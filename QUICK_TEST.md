# 🚀 Quick Test Guide - Bot Telegram Marvel

## ⚡ Testing dalam 5 Menit

### 1. **Setup Cepat**
```bash
# Install dependencies
pip install -r requirements.txt

# Buat file .env
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env
echo "GROQ_API_KEY=your_groq_key_here" >> .env
echo "JINA_API_KEY=your_jina_key_here" >> .env
```

### 2. **Test Otomatis**
```bash
# Run automated tests
python test_bot.py
```

### 3. **Test Manual**
```bash
# Build index
python build_index.py

# Start bot
python main.py
```

## 🧪 Test Cases Sederhana

### **Test 1: Basic Functionality**
1. Kirim `/start` ke bot
2. Expected: Keyboard kategori muncul

### **Test 2: Character Question**
1. Pilih "Character"
2. Tanya: "Siapa Iron Man?"
3. Expected: Jawaban tentang Iron Man

### **Test 3: Category Prefix**
1. Langsung tanya: "character: Siapa Spider-Man?"
2. Expected: Jawaban tentang Spider-Man

### **Test 4: All Categories**
1. Pilih "🔎 Semua Kategori"
2. Tanya: "Apa itu Avengers?"
3. Expected: Jawaban dari berbagai sumber

## 📱 Testing di Telegram

### **Step 1: Start Bot**
- Cari bot kamu di Telegram
- Kirim `/start`

### **Step 2: Test Kategori**
- Pilih salah satu kategori
- Tanya pertanyaan sederhana

### **Step 3: Test Feedback**
- Beri rating 1-5 setelah bot jawab
- Cek `feedback_log.csv` untuk konfirmasi

## 🔍 Expected Results

### **Console Output:**
```
✅ Retrievers loaded: ['character', 'factions', 'items', 'maps', 'npc', 'timeline']
🤖 Bot aktif. Gunakan /start untuk memilih kategori.
```

### **Telegram Bot:**
- Merespon `/start` dengan keyboard
- Bisa jawab pertanyaan Marvel
- Memberikan feedback options
- Menyimpan feedback ke CSV

## ❌ Common Issues & Fixes

### **Bot tidak merespon:**
- Cek Telegram Bot Token
- Cek bot sudah di-start
- Cek console untuk errors

### **"No module named X":**
```bash
pip install -r requirements.txt
```

### **"Environment variables not set":**
- Pastikan file `.env` ada
- Format: `KEY=value` (tanpa spasi)

### **Index tidak tersedia:**
```bash
python build_index.py
```

## 🎯 Success Criteria

✅ **Bot start tanpa error**
✅ **Keyboard kategori muncul**
✅ **Bisa jawab pertanyaan Marvel**
✅ **Feedback system berfungsi**
✅ **Index tersimpan di folder storage/**

---

**Jika semua test passed → Bot siap deploy ke Railway! 🚀** 