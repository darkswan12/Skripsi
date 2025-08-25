import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from typing import Union, List

# Load environment variables
load_dotenv()

# Check if we're in deployment mode
IS_DEPLOYMENT = (
    os.getenv("RAILWAY_ENVIRONMENT") or 
    os.getenv("RAILWAY_SERVICE_NAME") or
    os.getenv("RAILWAY_PROJECT_ID") or
    os.getenv("PORT") or
    os.getenv("DYNO") or  # Heroku
    os.getenv("VERCEL") or  # Vercel
    os.getenv("FLY_APP_NAME") or  # Fly.io
    os.getenv("RENDER") or  # Render
    os.getenv("DETA_SPACE_APP") or  # Deta Space
    os.getenv("FLY_APP_NAME") or  # Fly.io
    os.getenv("KUBERNETES_SERVICE_HOST") or  # Kubernetes
    os.getenv("AWS_EXECUTION_ENV") or  # AWS Lambda
    os.getenv("GOOGLE_CLOUD_PROJECT") or  # Google Cloud
    os.getenv("AZURE_FUNCTIONS_ENVIRONMENT")  # Azure Functions
)

print(f"🚀 Build mode: {'Deployment' if IS_DEPLOYMENT else 'Local'}")
if IS_DEPLOYMENT:
    print(f"🌐 Deployment platform detected: {os.getenv('RAILWAY_ENVIRONMENT', 'Railway')}")

# ===== Embedding via Jina AI (multilingual, gratis) =====
try:
    from llama_index.core import Settings
    from llama_index.embeddings.jinaai import JinaEmbedding
    import numpy as np
    
    # Custom Jina Embedding class to fix dimension issues
    Settings.embed_model = JinaEmbedding(
    api_key=jina_key,
    model="jina-embeddings-v3",
    task="text-matching",
)

    # Check if JINA_API_KEY is available
    # ambil API key dari environment
    jina_key = os.getenv("JINA_API_KEY")

    if not jina_key:
        print("⚠️  JINA_API_KEY tidak tersedia, skip embedding setup")
        Settings.embed_model = None
    else:
        print("✅ JINA_API_KEY tersedia, setup embedding...")
        Settings.embed_model = JinaEmbedding(
            api_key=jina_key,
            model="jina-embeddings-v3",
            task="text-matching",
        )
        print("✅ Jina Embedding initialized")
except ImportError as e:
    print(f"⚠️  Error importing llama_index: {e}")
    print("Index building akan di-skip")
    exit(0)

# ===== Inti indexing =====
try:
    from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
    from llama_index.core.node_parser import SentenceSplitter
except ImportError as e:
    print(f"⚠️  Error importing llama_index components: {e}")
    print("Index building akan di-skip")
    exit(0)

DATA_DIR = Path("data")
PERSIST_ROOT = Path("storage")

# Sesuaikan dengan struktur folder data kamu
CATEGORIES = {
    "character": DATA_DIR / "character",
    "factions":  DATA_DIR / "factions",
    "items":     DATA_DIR / "items",
    "maps":      DATA_DIR / "maps",
    "npc":       DATA_DIR / "npc",
    "timeline":  DATA_DIR / "timeline",
}

# Pecah dokumen agar retrieval akurat
parser = SentenceSplitter(chunk_size=512, chunk_overlap=100)

def build_one(category: str, src_dir: Path, persist_root: Path):
    if not src_dir.exists():
        print(f"⚠️  Lewati '{category}': folder {src_dir} tidak ada")
        return False
    
    md_files = sorted(str(p) for p in src_dir.glob("*.md"))
    if not md_files:
        print(f"⚠️  Lewati '{category}': tidak ada .md di {src_dir}")
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
    print("🔍 Checking data directory...")
    if not DATA_DIR.exists():
        print(f"❌ Data directory '{DATA_DIR}' tidak ada")
        if IS_DEPLOYMENT:
            print("💡 Dalam deployment, ini normal. Index akan dibangun saat runtime.")
            return
        else:
            print("💡 Pastikan folder 'data/' ada dan berisi markdown files")
            return
    
    print(f"✅ Data directory ditemukan: {DATA_DIR}")
    
    # Create storage directory
    PERSIST_ROOT.mkdir(parents=True, exist_ok=True)
    print(f"📁 Storage directory: {PERSIST_ROOT}")
    
    success_count = 0
    total_categories = len(CATEGORIES)
    
    for cat, path in CATEGORIES.items():
        print(f"\n--- Processing {cat} ---")
        if build_one(cat, path, PERSIST_ROOT):
            success_count += 1
    
    print(f"\n📊 Hasil build: {success_count}/{total_categories} kategori berhasil")
    
    if success_count == 0:
        print("⚠️  Tidak ada index yang berhasil dibangun")
        if IS_DEPLOYMENT:
            print("💡 Dalam deployment, ini bisa normal. Bot akan build index saat runtime.")
        else:
            print("💡 Cek error di atas dan pastikan semua dependencies terinstall")
    else:
        print("✅ Beberapa index berhasil dibangun dan tersimpan di folder 'storage/'")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if IS_DEPLOYMENT:
            print("💡 Dalam deployment, ini bisa normal. Bot akan handle error ini.")
        exit(1)
