# 🚨 Troubleshooting Guide - Bot Telegram Marvel

## ❌ Error: "shapes (1024,) and (1,) not aligned: 1024 (dim 0) != 1 (dim 0)"

### 🔍 **Penyebab Error:**
Ini adalah error klasik dari **Jina Embeddings** dimana:
- Model mengembalikan vector dengan shape `(1024,)` (1D array)
- Tapi sistem expect shape `(1, 1024)` (2D array)
- Operasi dot product/matrix multiplication gagal karena dimensi tidak cocok

### ✅ **Solusi yang Sudah Diterapkan:**

#### 1. **Custom Embedding Class**
```python
class FixedJinaEmbedding(JinaEmbedding):
    def _get_query_embedding(self, query: str) -> np.ndarray:
        embedding = super()._get_query_embedding(query)
        # Fix: (1024,) → (1, 1024)
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        return embedding
```

#### 2. **Dimension Fix di Semua Methods**
- `_get_query_embedding()` - untuk query user
- `_get_text_embedding()` - untuk single text
- `_get_text_embeddings()` - untuk multiple texts

#### 3. **Error Handling**
```python
try:
    Settings.embed_model = FixedJinaEmbedding(...)
    print("✅ Jina Embedding initialized with dimension fix")
except Exception as e:
    print(f"⚠️  Error: {e}")
    Settings.embed_model = None  # Fallback
```

### 🚀 **Cara Deploy Setelah Fix:**

#### **Step 1: Push Perubahan**
```bash
git add .
git commit -m "Fix Jina embedding dimension mismatch error"
git push origin main
```

#### **Step 2: Deploy di Railway**
- Railway akan otomatis rebuild dengan fix baru
- Expected output:
```
🚀 Bot mode: Deployment
🌐 Platform: Railway
🔑 Environment variables loaded: True
✅ Jina Embedding initialized with dimension fix
✅ Retrievers loaded: ['character', 'factions', 'items', 'maps', 'npc', 'timeline']
🤖 Bot aktif. Gunakan /start untuk memilih kategori.
```

## 🧪 **Test Setelah Fix:**

### **Test 1: Basic Question**
1. Kirim `/start` ke bot
2. Pilih kategori "Character"
3. Tanya: "Siapa Iron Man?"
4. **Expected:** Bot jawab tanpa error dimension

### **Test 2: Category Prefix**
1. Langsung tanya: "character: Siapa Spider-Man?"
2. **Expected:** Bot jawab tanpa error dimension

### **Test 3: All Categories**
1. Pilih "🔎 Semua Kategori"
2. Tanya: "Apa itu Avengers?"
3. **Expected:** Bot jawab dari berbagai sumber tanpa error

## 🔧 **Jika Masih Error:**

### **Option 1: Check Logs**
```bash
# Di Railway, cek tab "Logs"
# Cari error message yang lebih spesifik
```

### **Option 2: Fallback Embedding**
Jika Jina masih bermasalah, bot akan gunakan default embedding:
```python
Settings.embed_model = None  # Default embedding
```

### **Option 3: Manual Dimension Check**
```python
# Debug: cek shape embedding
embedding = model.get_embedding("test")
print(f"Shape: {embedding.shape}")
print(f"Type: {type(embedding)}")
```

## 📊 **Expected Behavior Setelah Fix:**

✅ **Bot start tanpa error dimension**  
✅ **Embedding vectors dengan shape yang benar**  
✅ **Retrieval berfungsi normal**  
✅ **Bot bisa jawab pertanyaan Marvel**  
✅ **Feedback system berfungsi**  

## 🎯 **Success Criteria:**

- ❌ **Sebelum:** `shapes (1024,) and (1,) not aligned`
- ✅ **Sesudah:** `✅ Jina Embedding initialized with dimension fix`

---

**Note:** Fix ini sudah diterapkan di `main.py` dan `build_index.py`. Deploy ulang ke Railway untuk apply fix! 🚀 