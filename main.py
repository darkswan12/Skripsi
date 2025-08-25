import os
import csv
import threading
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from flask import Flask, send_file, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CallbackQueryHandler,
    CommandHandler, filters, ContextTypes
)

# ==== Flask dashboard ====
dashboard_app = Flask(__name__)
FEEDBACK_FILE = "feedback_log.csv"

@dashboard_app.route("/")
def home():
    return """
    <h1>Bot Dashboard</h1>
    <ul>
        <li><a href='/status'>Status Bot</a></li>
        <li><a href='/categories'>Daftar Kategori Index</a></li>
        <li><a href='/feedback'>Lihat Feedback (JSON)</a></li>
        <li><a href='/download-feedback'>Download feedback_log.csv</a></li>
    </ul>
    """

@dashboard_app.route("/status")
def status():
    return jsonify({
        "status": "running",
        "telegram_bot": os.getenv("TELEGRAM_BOT_TOKEN") is not None,
        "groq_api": os.getenv("GROQ_API_KEY") is not None,
        "jina_api": os.getenv("JINA_API_KEY") is not None
    })

@dashboard_app.route("/categories")
def categories_status():
    return jsonify({
        "loaded_categories": sorted(list(retrievers.keys())),
        "expected_categories": CATEGORIES
    })

@dashboard_app.route("/feedback")
def feedback_json():
    if not os.path.exists(FEEDBACK_FILE):
        return jsonify({"error": "feedback_log.csv belum ada"}), 404
    data = []
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")
        for line in f:
            values = line.strip().split(",")
            row = dict(zip(header, values))
            data.append(row)
    return jsonify(data)

@dashboard_app.route("/download-feedback")
def download_feedback():
    if not os.path.exists(FEEDBACK_FILE):
        return "⚠️ File feedback_log.csv belum ada", 404
    return send_file(FEEDBACK_FILE, as_attachment=True)


# ==== Telegram Bot ====
from llama_index.core import Settings, StorageContext, load_index_from_storage
from llama_index.embeddings.jinaai import JinaEmbedding

load_dotenv(override=False)
Settings.embed_model = JinaEmbedding(
    api_key=os.getenv("JINA_API_KEY"),
    model="jina-embeddings-v3",
    task="text-matching",
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")
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

# ===== Index loader =====
PERSIST_ROOT = Path("storage")
CATEGORIES = ["character", "factions", "items", "maps", "npc", "timeline"]
retrievers = {}

def load_retrievers():
    for cat in CATEGORIES:
        cat_dir = PERSIST_ROOT / cat
        if not cat_dir.exists():
            print(f"⚠️ Index '{cat}' tidak ada, dilewati.")
            continue
        sc = StorageContext.from_defaults(persist_dir=str(cat_dir))
        index = load_index_from_storage(sc)
        retrievers[cat] = index.as_retriever(similarity_top_k=8)
    print("✅ Retrievers loaded:", sorted(retrievers.keys()))

try:
    load_retrievers()
except Exception as e:
    print(f"❌ Error load retrievers: {e}")

# ===== Aliases & helper =====
ALIASES = {
    "character": ["character", "karakter"],
    "factions": ["faction", "factions", "tim", "team", "faksi"],
    "items": ["item", "items", "artefak", "artifact", "barang"],
    "maps": ["maps", "map", "peta", "lokasi", "area"],
    "npc": ["npc"],
    "timeline": ["timeline", "linimasa", "alur", "sejarah"],
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

# ===== Bot handlers =====
def category_keyboard():
    rows = [
        [InlineKeyboardButton("Character", callback_data="CAT|character"),
         InlineKeyboardButton("Factions", callback_data="CAT|factions")],
        [InlineKeyboardButton("Items", callback_data="CAT|items"),
         InlineKeyboardButton("Maps", callback_data="CAT|maps")],
        [InlineKeyboardButton("NPC", callback_data="CAT|npc"),
         InlineKeyboardButton("Timeline", callback_data="CAT|timeline")],
        [InlineKeyboardButton("🔎 Semua Kategori", callback_data="CAT|all")],
    ]
    return InlineKeyboardMarkup(rows)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("selected_cat", None)
    await update.message.reply_text("Pilih kategori yang ingin kamu tanyakan:",
                                    reply_markup=category_keyboard())

async def pick_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        _, cat = q.data.split("|", 1)
    except Exception:
        await q.edit_message_text("Pilihan tidak dikenal.")
        return
    if cat == "all":
        context.user_data["selected_cat"] = None
        await q.edit_message_text("Mode: 🔎 semua kategori.\nTulis pertanyaanmu:")
        return
    if cat not in retrievers:
        await q.edit_message_text(f"Kategori '{cat}' belum ter-index.")
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
            await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                                message_id=loading.message_id,
                                                text="🙇‍♂️ Maaf, belum ketemu di basis data.")
            return

        prompt = (f"Jawablah pertanyaan hanya dengan memanfaatkan KONTEN berikut.\n\n"
                  f"--- KONTEN ---\n{context_text}\n\n--- PERTANYAAN ---\n{q}\n")
        resp = await Settings.llm.acomplete(prompt)
        answer = (getattr(resp, 'text', None) or str(resp)).strip()

        source_note = f"(Sumber: {collect_sources(retrieved_nodes)})"
        mode_note = f"[Mode: {('Semua' if not cat else cat)}]"
        final_text = f"🧠 {answer}\n\n{source_note}\n{mode_note}"

        await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                            message_id=loading.message_id,
                                            text=final_text)

        # Feedback 1–5
        keyboard_fb = InlineKeyboardMarkup([[
            InlineKeyboardButton("1", callback_data=f"fb|1|{q_raw}"),
            InlineKeyboardButton("2", callback_data=f"fb|2|{q_raw}"),
            InlineKeyboardButton("3", callback_data=f"fb|3|{q_raw}"),
            InlineKeyboardButton("4", callback_data=f"fb|4|{q_raw}"),
            InlineKeyboardButton("5", callback_data=f"fb|5|{q_raw}")
        ]])
        await update.message.reply_text("Nilai jawaban ini (1=buruk, 5=bagus):",
                                        reply_markup=keyboard_fb)

        # Next step
        keyboard_next = InlineKeyboardMarkup([
            [InlineKeyboardButton("Tanya lagi 🔄", callback_data="NEXT|again")],
            [InlineKeyboardButton("Selesai ✅", callback_data="NEXT|done")]
        ])
        await update.message.reply_text("Apakah masih ingin bertanya?", reply_markup=keyboard_next)

    except Exception as e:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                            message_id=loading.message_id,
                                            text=f"❌ Error: {e}")

# ===== Feedback callback =====
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
           "score": score, "question": question,
           "timestamp": datetime.now().isoformat()}
    with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(row)
    await q.edit_message_text(f"✅ Terima kasih! Feedback {score}/5 terekam.")

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
        await q.edit_message_text("Terima kasih sudah menggunakan bot ini 👋")

# ===== Run both bot + dashboard =====
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(pick_category_callback, pattern=r"^CAT\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(feedback_callback, pattern=r"^fb\|"))
    app.add_handler(CallbackQueryHandler(next_step_callback, pattern=r"^NEXT\|"))
    print("🤖 Bot aktif. Gunakan /start untuk memilih kategori.")
    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 8000))
    print(f"🌐 Dashboard running on port {port}")
    dashboard_app.run(host="0.0.0.0", port=port)
