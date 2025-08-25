# 🧪 Testing Bot Telegram - Local

## Persiapan Testing Local

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Setup Environment Variables**
Buat file `.env` di root folder:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
JINA_API_KEY=your_jina_api_key_here
```

### 3. **Build Index Terlebih Dahulu**
```bash
python build_index.py
```

### 4. **Test Bot**
```bash
python main.py
```

## Expected Output
```
🚀 Build mode: Local
🔍 Checking data directory...
✅ Data directory ditemukan: data
📁 Storage directory: storage

--- Processing character ---
📥 [character] Baca 40 file markdown...
🔨 [character] Susun nodes & bangun index...
💾 [character] Simpan index ke storage/character ...

--- Processing factions ---
📥 [factions] Baca 7 file markdown...
🔨 [factions] Susun nodes & bangun index...
💾 [factions] Simpan index ke storage/factions ...

📊 Hasil build: 6/6 kategori berhasil
✅ Semua index berhasil dibangun dan tersimpan di folder 'storage/'

✅ Retrievers loaded: ['character', 'factions', 'items', 'maps', 'npc', 'timeline']
🤖 Bot aktif. Gunakan /start untuk memilih kategori.
📊 Retrievers tersedia: ['character', 'factions', 'items', 'maps', 'npc', 'timeline']
```

## Test Cases

### ✅ **Test 1: Start Command**
- Kirim `/start` ke bot
- Expected: Bot reply dengan keyboard kategori

### ✅ **Test 2: Category Selection**
- Pilih salah satu kategori (misal: Character)
- Expected: Bot reply "Mode: 🗂 Character"

### ✅ **Test 3: Basic Question**
- Tanya: "Siapa Iron Man?"
- Expected: Bot jawab dengan informasi Iron Man

### ✅ **Test 4: Category Prefix**
- Tanya: "character: Siapa Spider-Man?"
- Expected: Bot jawab dengan info Spider-Man

### ✅ **Test 5: All Categories**
- Pilih "🔎 Semua Kategori"
- Tanya: "Apa itu Avengers?"
- Expected: Bot jawab dengan info dari berbagai kategori

### ✅ **Test 6: Feedback System**
- Setelah bot jawab, beri rating 1-5
- Expected: Feedback tersimpan di `feedback_log.csv`

## Troubleshooting Local

### ❌ "No module named 'llama_index'"
**Solution:**
```bash
pip install llama-index
```

### ❌ "JINA_API_KEY belum diset"
**Solution:**
- Pastikan file `.env` ada
- Pastikan format: `JINA_API_KEY=your_key_here`

### ❌ "Folder 'storage/' tidak ada"
**Solution:**
```bash
python build_index.py
```

### ❌ Bot tidak merespon
**Solution:**
- Cek Telegram Bot Token sudah benar
- Cek bot sudah di-start di Telegram
- Cek console untuk error messages

## Performance Testing

### 📊 **Test Response Time**
- Measure waktu dari kirim pertanyaan sampai dapat jawaban
- Expected: < 10 detik untuk pertanyaan sederhana

### 📊 **Test Memory Usage**
- Monitor memory usage saat bot running
- Expected: < 500MB untuk bot dengan index

### 📊 **Test Concurrent Users**
- Test dengan multiple users (jika ada)
- Expected: Bot handle multiple requests

## Security Testing

### 🔒 **Test Input Validation**
- Kirim input aneh: `"'; DROP TABLE users; --"`
- Expected: Bot handle dengan graceful error

### 🔒 **Test File Access**
- Cek apakah bot bisa akses file di luar folder data
- Expected: Bot hanya akses folder yang diizinkan

## Data Validation

### 📋 **Test Index Quality**
- Tanya pertanyaan spesifik untuk setiap kategori
- Expected: Jawaban relevan dan akurat

### 📋 **Test Source Attribution**
- Cek apakah bot mention sumber file
- Expected: Bot mention file sumber (misal: iron_man.md)

---

**Note:** Testing local penting untuk memastikan bot berfungsi sebelum deploy ke Railway! 