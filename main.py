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
Settings.embed_model = JinaEmbedding(
    api_key=os.getenv("JINA_API_KEY"),
    model="jina-embeddings-v3",
    task="text-matching",
)

# ===== ENV =====
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
assert BOT_TOKEN, "TELEGRAM_BOT_TOKEN belum diset di Railway environment variables"
assert GROQ_API_KEY, "GROQ_API_KEY belum diset di Railway environment variables"
assert os.getenv("JINA_API_KEY"), "JINA_API_KEY belum diset di Railway environment variables"

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
        # Fallback OpenAI-compatible endpoint
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
    # Create storage directory if it doesn't exist
    PERSIST_ROOT.mkdir(parents=True, exist_ok=True)
    
    if not PERSIST_ROOT.exists():
        raise RuntimeError("Folder 'storage/' tidak bisa dibuat. Cek permission Railway.")
    
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
        print("⚠️  Tidak ada index yang tersedia. Bot akan build index saat runtime.")
        return False
    
    print("✅ Retrievers loaded:", sorted(retrievers.keys()))
    return True

# Load retrievers with error handling
try:
    load_retrievers()
except Exception as e:
    print(f"❌ Error loading retrievers: {e}")
    print("Bot akan tetap berjalan tapi tidak bisa menjawab pertanyaan sampai index tersedia.")

# Function to build index at runtime if needed
def build_index_if_needed():
    if retrievers:
        return True
    
    print("🔨 Building index at runtime...")
    try:
        # Import build_index functions
        from build_index import build_one, CATEGORIES as BUILD_CATEGORIES
        
        success_count = 0
        for cat, path in BUILD_CATEGORIES.items():
            if build_one(cat, path, PERSIST_ROOT):
                success_count += 1
        
        if success_count > 0:
            # Reload retrievers
            load_retrievers()
            print(f"✅ Index berhasil dibangun untuk {success_count} kategori")
            return True
        else:
            print("❌ Tidak ada index yang berhasil dibangun")
            return False
    except Exception as e:
        print(f"❌ Error building index at runtime: {e}")
        return False

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
    # Check if retrievers are available, if not try to build them
    if not retrievers:
        await update.message.reply_text("⏳ Bot sedang mempersiapkan index, tunggu sebentar...")
        
        if build_index_if_needed():
            await update.message.reply_text("✅ Index siap! Silakan tanya pertanyaanmu.")
        else:
            await update.message.reply_text(
                "❌ Bot sedang dalam maintenance. Index tidak bisa dibangun. Coba lagi nanti."
            )
            return
    
    q_raw = update.message.text or ""
    loading = await update.message.reply_text("⏳ Lagi nyari jawabannya...")

    try:
        cat_from_prefix, q = detect_category_and_query(q_raw)
        selected_cat = context.user_data.get("selected_cat")
        cat = cat_from_prefix if cat_from_prefix is not None else selected_cat

        if cat and cat not in retrievers:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=loading.message_id,
                text=f"Kategori '{cat}' belum ter-index. Jalankan build_index.py untuk folder itu dulu."
            )
            return

        retrieved_nodes = []
        if cat:
            retrieved_nodes.extend(retrievers[cat].retrieve(q))
        else:
            for r in retrievers.values():
                retrieved_nodes.extend(r.retrieve(q))

        if reranker and retrieved_nodes:
            try:
                retrieved_nodes = reranker.postprocess_nodes(retrieved_nodes, query=q)
            except Exception:
                pass

        contexts = [n.node.text for n in retrieved_nodes]
        context_text = "\n\n---\n\n".join(contexts[:12])

        if not context_text.strip():
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=loading.message_id,
                text="🙇‍♂️ Maaf, belum ketemu di basis data. Coba spesifikkan pertanyaan atau cek index."
            )
            return

        source_note = f"(Sumber: {collect_sources(retrieved_nodes)})"
        mode_note = f"[Mode: {('Semua' if not cat else cat)}]"

        prompt = (
            "Jawablah pertanyaan hanya dengan memanfaatkan KONTEN berikut. "
            "Jika jawaban persis tidak ada, gunakan informasi paling relevan dari KONTEN untuk memberi penjelasan ringkas. "
            "Jika sama sekali tidak relevan, tulis: 'Informasi tidak ditemukan di basis data.'\n\n"
            f"--- KONTEN ---\n{context_text}\n\n"
            f"--- PERTANYAAN ---\n{q}\n\n"
            "--- PETUNJUK ---\n"
            "- Utamakan fakta dari KONTEN.\n"
            "- Jika tidak ada fakta langsung, boleh simpulkan singkat dari potongan yang terkait.\n"
            "- Jika benar-benar kosong, tulis: 'Informasi tidak ditemukan di basis data.'\n"
        )

        resp = await Settings.llm.acomplete(prompt)
        answer = (getattr(resp, 'text', None) or str(resp)).strip()

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=loading.message_id,
            text=f"🧠 {answer}\n\n{source_note}\n{mode_note}"
        )

        keyboard_fb = InlineKeyboardMarkup([[  # feedback
            InlineKeyboardButton("1", callback_data=f"fb|1|{q_raw}"),
            InlineKeyboardButton("2", callback_data=f"fb|2|{q_raw}"),
            InlineKeyboardButton("3", callback_data=f"fb|3|{q_raw}"),
            InlineKeyboardButton("4", callback_data=f"fb|4|{q_raw}"),
            InlineKeyboardButton("5", callback_data=f"fb|5|{q_raw}")
        ]])
        await update.message.reply_text("Nilai jawaban ini (1=buruk, 5=bagus):", reply_markup=keyboard_fb)

        keyboard_next = InlineKeyboardMarkup([  # tanya lagi?
            [InlineKeyboardButton("Tanya lagi 🔄", callback_data="NEXT|again")],
            [InlineKeyboardButton("Selesai ✅", callback_data="NEXT|done")]
        ])
        await update.message.reply_text("Apakah masih ingin bertanya?", reply_markup=keyboard_next)

    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=loading.message_id,
            text=f"❌ Error saat memproses: {e}"
        )

# ===== Next step callback =====
async def next_step_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        _, action = q.data.split("|", 1)
    except Exception:
        await q.edit_message_text("Pilihan tidak dikenal.")
        return

    if action == "again":
        await q.edit_message_text("Pilih kategori baru:", reply_markup=category_keyboard())
    else:
        tips = (
            "Terima kasih sudah menggunakan bot ini 👋\n\n"
        )
        await q.edit_message_text(tips)

# ===== Feedback CSV =====
async def feedback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        _, score, question = q.data.split("|", 2)
    except Exception:
        await q.edit_message_text("⚠️ Format feedback tidak valid.")
        return

    user = q.from_user
    row = {"user_id": user.id, "username": user.username or "",
           "score": score, "question": question, "timestamp": datetime.now().isoformat()}

    try:
        with open("feedback_log.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(row)
        await q.edit_message_text(f"✅ Terima kasih! Feedback {score}/5 terekam.")
    except Exception as e:
        await q.edit_message_text(f"⚠️ Feedback tidak bisa disimpan: {e}")

# ===== Run bot =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CallbackQueryHandler(pick_category_callback, pattern=r"^CAT\|"))
    app.add_handler(CallbackQueryHandler(next_step_callback, pattern=r"^NEXT\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(feedback_callback, pattern=r"^fb\|"))
    print("🤖 Bot aktif. Gunakan /start untuk memilih kategori.")
    print(f"📊 Retrievers tersedia: {sorted(retrievers.keys())}")
    app.run_polling()

if __name__ == "__main__":
    main()
