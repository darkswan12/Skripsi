# 🚀 Deployment Guide untuk Railway

## Persiapan Sebelum Deploy

1. **Pastikan semua file sudah ada:**
   - `main.py` ✅
   - `build_index.py` ✅
   - `requirements.txt` ✅
   - `nixpacks.toml` ✅
   - `railway.toml` ✅
   - `Dockerfile` ✅ (alternatif)
   - Folder `data/` dengan semua markdown files ✅

2. **Siapkan 3 API Keys yang diperlukan:**
   - `TELEGRAM_BOT_TOKEN` - dari @BotFather
   - `GROQ_API_KEY` - dari Groq.com
   - `JINA_API_KEY` - dari Jina AI

## Langkah Deployment di Railway

### 1. Login ke Railway
- Buka [railway.app](https://railway.app)
- Login dengan GitHub account

### 2. Buat Project Baru
- Klik "New Project"
- Pilih "Deploy from GitHub repo"
- Pilih repository yang berisi bot ini

### 3. Set Environment Variables
Setelah project dibuat, buka tab "Variables" dan tambahkan:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
JINA_API_KEY=your_jina_api_key_here
```

### 4. Deploy
- Railway akan otomatis detect Python project
- Build process akan:
  1. Install dependencies dari `requirements.txt`
  2. Start bot dengan `python main.py`
  3. Bot akan build index otomatis saat runtime

### 5. Monitor Deployment
- Cek tab "Deployments" untuk status build
- Cek tab "Logs" untuk melihat output bot
- Pastikan tidak ada error

## Troubleshooting

### ❌ Docker Build Failed Error
Jika muncul error seperti ini:
```
✕ [stage-0 6/10] RUN pip install -r requirements.txt
process did not complete successfully: exit code: 1
```

**Solusi:**
1. **Gunakan konfigurasi baru:** `railway.toml` + `nixpacks.toml`
2. **Hapus file lama:** `railway.json` dan `Procfile` (jika ada)
3. **Restart deployment** di Railway
4. **Cek logs** untuk detail error

### ❌ Build Index Failed Error
Jika muncul error seperti ini:
```
✕ [7/7] RUN python build_index.py
process did not complete successfully: exit code: 1
```

**Solusi:**
1. **Konfigurasi sudah diperbaiki** - bot akan build index otomatis saat runtime
2. **Tidak perlu manual build** - biarkan bot handle sendiri
3. **Cek environment variables** sudah benar

### Bot tidak bisa start
- Cek environment variables sudah benar
- Cek logs untuk error message
- Pastikan semua dependencies terinstall

### Index tidak bisa di-load
- Bot akan otomatis build index saat pertama kali digunakan
- Tunggu beberapa saat saat bot mempersiapkan index
- Cek logs untuk progress building

### Bot tidak merespon
- Cek Telegram Bot Token sudah benar
- Cek bot sudah di-start di Telegram
- Cek Railway service status

## Alternative Deployment Methods

### Method 1: Nixpacks (Recommended)
- Gunakan `railway.toml` + `nixpacks.toml`
- Lebih stabil untuk Python projects
- Automatic dependency resolution
- **Index building otomatis saat runtime**

### Method 2: Dockerfile
- Gunakan `Dockerfile` yang sudah disediakan
- Set Railway builder ke "Dockerfile"
- Lebih predictable build process

## Fitur Bot Setelah Deploy

✅ **Kategori yang tersedia:**
- Character (karakter Marvel)
- Factions (tim/kelompok)
- Items (artefak/barang)
- Maps (lokasi/area)
- NPC (non-player characters)
- Timeline (alur cerita)

✅ **Cara pakai:**
1. Start bot dengan `/start`
2. Pilih kategori
3. Tanya pertanyaan
4. Beri feedback 1-5
5. Tanya lagi atau selesai

## Monitoring & Maintenance

- **Logs:** Cek Railway logs secara berkala
- **Feedback:** Review `feedback_log.csv` untuk improvement
- **Updates:** Update dependencies jika diperlukan
- **Index:** Bot akan otomatis rebuild index jika diperlukan

## Common Issues & Solutions

### Issue: "No module named 'llama_index'"
**Solution:** Pastikan `requirements.txt` sudah benar dan Railway menggunakan Python 3.9

### Issue: "Permission denied" saat build index
**Solution:** Bot akan handle ini otomatis saat runtime

### Issue: Bot stuck di "loading" state
**Solution:** Bot sedang build index, tunggu beberapa saat

### Issue: Index tidak tersedia
**Solution:** Bot akan otomatis build index saat pertama kali digunakan

---

**Note:** Bot ini menggunakan Groq LLM dan Jina AI embeddings. Pastikan API keys masih valid dan ada quota yang cukup.

**Keunggulan baru:** Bot sekarang akan otomatis build index saat runtime, jadi tidak perlu manual build lagi! 