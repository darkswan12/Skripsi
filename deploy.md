# 🚀 Deployment Guide untuk Railway

## Persiapan Sebelum Deploy

1. **Pastikan semua file sudah ada:**
   - `main.py` ✅
   - `build_index.py` ✅
   - `requirements.txt` ✅
   - `nixpacks.toml` ✅
   - `railway.json` ✅
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
  2. Jalankan `build_index.py` untuk build index
  3. Start bot dengan `python main.py`

### 5. Monitor Deployment
- Cek tab "Deployments" untuk status build
- Cek tab "Logs" untuk melihat output bot
- Pastikan tidak ada error

## Troubleshooting

### Bot tidak bisa start
- Cek environment variables sudah benar
- Cek logs untuk error message
- Pastikan semua dependencies terinstall

### Index tidak bisa di-load
- Cek folder `storage/` sudah terbuat
- Cek permission Railway untuk write file
- Cek logs build_index.py

### Bot tidak merespon
- Cek Telegram Bot Token sudah benar
- Cek bot sudah di-start di Telegram
- Cek Railway service status

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
- **Backup:** Backup folder `storage/` jika perlu

---

**Note:** Bot ini menggunakan Groq LLM dan Jina AI embeddings. Pastikan API keys masih valid dan ada quota yang cukup. 