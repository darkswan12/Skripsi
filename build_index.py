import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

# ===== Load environment =====
load_dotenv()

from llama_index.core import Settings
from llama_index.embeddings.jinaai import JinaEmbedding
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

# ===== Config =====
DATA_DIR = Path("data")
PERSIST_ROOT = Path("storage")

CATEGORIES = {
    "character": DATA_DIR / "character",
    "factions":  DATA_DIR / "factions",
    "items":     DATA_DIR / "items",
    "maps":      DATA_DIR / "maps",
    "npc":       DATA_DIR / "npc",
    "timeline":  DATA_DIR / "timeline",
}

# ===== Setup embedding =====
jina_key = os.getenv("JINA_API_KEY")
if not jina_key:
    print("⚠️  JINA_API_KEY tidak tersedia, index tidak akan dibangun")
    Settings.embed_model = None
else:
    print("✅ JINA_API_KEY ditemukan, inisialisasi embedding...")
    Settings.embed_model = JinaEmbedding(
        api_key=jina_key,
        model="jina-embeddings-v3",
        task="text-matching",
    )
    print("✅ Jina Embedding initialized")

# ===== Parser =====
parser = SentenceSplitter(chunk_size=512, chunk_overlap=100)

def build_one(category: str, src_dir: Path, persist_root: Path):
    """Bangun index untuk satu kategori"""
    if not src_dir.exists():
        print(f"⚠️  Lewati '{category}': folder {src_dir} tidak ada")
        return False

    md_files = sorted(str(p) for p in src_dir.glob("*.md"))
    if not md_files:
        print(f"⚠️  Lewati '{category}': tidak ada file .md di {src_dir}")
        return False

    persist_dir = persist_root / category
    if persist_dir.exists():
        shutil.rmtree(persist_dir)

    try:
        print(f"📥 [{category}] Baca {len(md_files)} file markdown...")
        docs = SimpleDirectoryReader(input_files=md_files, filename_as_id=True).load_data()

        print(f"🔨 [{category}] Susun nodes & bangun index...")
        nodes = parser.get_nodes_from_documents(docs)
        index = VectorStoreIndex(nodes)

        print(f"💾 [{category}] Simpan index ke {persist_dir} ...")
        index.storage_context.persist(persist_dir=str(persist_dir))
        return True
    except Exception as e:
        print(f"❌ Error building index '{category}': {e}")
        return False

def main():
    if not DATA_DIR.exists():
        print(f"❌ Folder data '{DATA_DIR}' tidak ditemukan")
        return

    PERSIST_ROOT.mkdir(parents=True, exist_ok=True)

    success_count = 0
    for cat, path in CATEGORIES.items():
        print(f"\n--- Processing {cat} ---")
        if build_one(cat, path, PERSIST_ROOT):
            success_count += 1

    print(f"\n📊 Hasil build: {success_count}/{len(CATEGORIES)} kategori berhasil")
    if success_count > 0:
        print("✅ Index siap digunakan")
    else:
        print("⚠️  Tidak ada index yang berhasil dibangun")

if __name__ == "__main__":
    main()
