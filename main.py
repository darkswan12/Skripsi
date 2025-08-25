import os
import csv
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CallbackQueryHandler,
    CommandHandler, filters, ContextTypes
)

# ===== LlamaIndex: Jina Embedding (harus sama dengan yang dipakai saat build) =====
from llama_index.core import Settings, StorageContext, load_index_from_storage
from llama_index.embeddings.jinaai import JinaEmbedding

load_dotenv()

# Gunakan JinaEmbedding langsung (tanpa subclass)
Settings.embed_model = JinaEmbedding(
    api_key=os.getenv("JINA_API_KEY"),
    model="jina-embeddings-v3",
    task="text-matching",
)
print("✅ Jina Embedding initialized")

# ===== ENV =====
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")

# Validate environment variables
assert BOT_TOKEN, "❌ TELEGRAM_BOT_TOKEN belum diset"
assert GROQ_API_KEY, "❌ GROQ_API_KEY belum diset"
assert JINA_API_KEY, "❌ JINA_API_KEY belum diset"

# ===== LLM Groq =====
PREFERRED_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-8b-instant"]
MAX_TOKENS = 1024

def init_llm():
    model_to_use = PREFERRED_MODELS[0]
    try:
        from llama_index.llms.groq import Groq
        return Groq(api_key=GROQ_API_KEY, model=model_to_use,
                    temperature=0.2, max_tokens=MAX_TOKENS, request_timeout=60.0)
    except Exception:
        from llama_index.llms.openai_like import OpenAILike
        return OpenAILike(api_base="https://api.groq.com/openai/v1",
                          api_key=GROQ_API_KEY, model=model_to_use,
                          temperature=0.2, max_tokens=MAX_TOKENS, timeout=60.0)

Settings.llm = init_llm()

# (Opsional) Reranker dimatikan biar ringan
reranker = None

# ===== Index loader =====
PERSIST_ROOT = Path("storage")
CATEGORIES = ["character", "factions", "items", "maps", "npc", "timeline"]
retrievers = {}

def load_retrievers():
    PERSIST_ROOT.mkdir(parents=True, exist_ok=True)
    for cat in CATEGORIES:
        cat_dir = PERSIST_ROOT / cat
        if not cat_dir.exists():
            print(f"⚠️  Index '{cat}' tidak ada, dilewati.")
            continue
        try:
            sc = StorageContext.from_defaults(persist_dir=str(cat_dir))
            index = load_index_from_storage(sc)
            retrievers[cat] = index.as_retriever(similarity_top_k=8)
        except Exception as e:
            print(f"⚠️  Error loading index '{cat}': {e}")
            continue
    if not retrievers:
        print("⚠️  Tidak ada index yang tersedia.")
        return False
    print("✅ Retrievers loaded:", sorted(retrievers.keys()))
    return True

try:
    load_retrievers()
except Exception as e:
    print(f"❌ Error loading retrievers: {e}")

# ===== Aliases & helper =====
ALIASES = {
    "character": ["character", "karakter"],
    "factions":  ["faction", "factions", "tim", "team", "faksi"],
    "items":     ["item", "items", "artefak", "artifact", "barang"],
    "maps":      ["maps", "map", "peta", "lokasi", "area"],
    "npc":       ["npc"],
    "timeline":  ["timeline", "linimasa", "alur", "sejarah"],
}

def detect_category_and_query(text: str):
    raw = (text or "").strip()
    if ":" in raw:
        prefix, rest = raw.split(":", 1)
        prefix = prefix.lower().strip()
        rest = rest.strip()
        for cat, keys in ALIASES.items():
            if prefix in keys:
                return cat, rest
    return None, raw

def collect_sources(nodes, max_files=5):
    files = []
    for n in nodes:
        meta = getattr(n, "node", n).metadata if hasattr(n, "node") else {}
        fname = (meta.get("file_name") or meta.get("filename") or meta.get("id"))
        if fname and fname not in files:
            files.append(fname)
        if len(files) >= max_files:
            break
    return ", ".join(files) if files else "dataset"

# ===== UI =====
def category_keyboard():
    rows = [
        [
            InlineKeyboardButton("Character", callback_data="CAT|character"),
            InlineKeyboardButton("Factions", callback_data="CAT|factions"),
        ],
        [
            InlineKeyboardButton("Items", callback_data="CAT|items"),
            InlineKeyboardButton("Maps", callback_data="CAT|maps"),
        ],
        [
            InlineKeyboardButton("NPC", callback_data="CAT|npc"),
            InlineKeyboardButton("Timeline", callback_data="CAT|timeline"),
        ],
        [InlineKeyboardButton("🔎 Semua Kategori", callback_data="CAT|all")],
    ]
    return InlineKeyboardMarkup(rows)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("selected_cat", None)
    await update.message.reply_text(
        "Pilih kategori yang ingin kamu tanyakan:",
        reply_markup=category_keyboard()
    )

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("selected_cat", None)
    await update.message.reply_text("Kategori direset. Ketik /start untuk pilih lagi.")

async def pick_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        _, cat = q.data.split("|", 1)
    except Exception:
        await q.edit_message_text("Pilihan tidak dikenal. /start lagi ya.")
        return
    if cat == "all":
        context.user_data["selected_cat"] = None
        await q.edit_message_text("Mode: 🔎 semua kategori.\nTulis pertanyaanmu:")
        return
    if cat not in retrievers:
        await q.edit_message_text(
            f"Kategori '{cat}' belum ter-index. Jalankan build_index.py untuk folder itu dulu."
        )
        return
    context.user_data["selected_cat"] = cat
    await q.edit_message_text(f"Mode: 🗂 {cat.capitalize()}\nSilakan ketik pertanyaanmu…")

# ===== Q&A handler =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_raw = update.message.text or ""
    loading = await update.message.reply_text("⏳ Lagi nyari jawabannya...")

    try:
        cat_from_prefix, q = detect_category_and_query(q_raw)
        selected_cat = context.user_data.get("selected_cat")
        cat = cat_from_prefix if cat_from_prefix is not None else selected_cat

        retrieved_nodes = []
        if cat:
            retrieved_nodes.extend(retrievers[cat].retrieve(q))
        else:
            for r in retrievers.values():
                retrieved_nodes.extend(r.retrieve(q))

        contexts = [n.node.text for n in retrieved_nodes]
        context_text = "\n\n---\n\n".join(contexts[:12])

        if not context_text.strip():
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=loading.message_id,
                text="🙇‍♂️ Maaf, belum ketemu di basis data."
            )
            return

        prompt = (
            "Jawablah pertanyaan hanya dengan memanfaatkan KONTEN berikut.\n\n"
            f"--- KONTEN ---\n{context_text}\n\n"
            f"--- PERTANYAAN ---\n{q}\n"
        )

        resp = await Settings.llm.acomplete(prompt)
        answer = (getattr(resp, 'text', None) or str(resp)).strip()

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=loading.message_id,
            text=f"🧠 {answer}"
        )

    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=loading.message_id,
            text=f"❌ Error saat memproses: {e}"
        )

# ===== Run bot =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CallbackQueryHandler(pick_category_callback, pattern=r"^CAT\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot aktif. Gunakan /start untuk memilih kategori.")
    app.run_polling()

if __name__ == "__main__":
    main()
