# 🚨 Troubleshooting Guide - Bot Telegram Marvel

## ❌ Error: "shapes (1024,) and (1,) not aligned: 1024 (dim 0) != 1 (dim 0)"

### 🔍 **Penyebab Error:**
Ini adalah error klasik dari **Jina Embeddings** dimana:
- Model mengembalikan vector dengan shape `(1024,)` (1D array)
- Tapi sistem expect shape `(1, 1024)` (2D array)
- Operasi dot product/matrix multiplication gagal karena dimensi tidak cocok

## ❌ Error: "list object has no attribute ndim"

### 🔍 **Penyebab Error:**
Jina Embeddings return **list** bukan **numpy array**:
- `super()._get_query_embedding()` return `[0.1, 0.2, ..., 0.9]` (list)
- Kode coba akses `.ndim` yang hanya ada di numpy array
- Error: `list object has no attribute ndim`

### ✅ **Solusi yang Sudah Diterapkan:**

#### 1. **Custom Embedding Class dengan Type Conversion**
```python
class FixedJinaEmbedding(JinaEmbedding):
    def _get_query_embedding(self, query: str) -> np.ndarray:
        embedding = super()._get_query_embedding(query)
        # Fix 1: Convert list to numpy array
        if isinstance(embedding, list):
            embedding = np.array(embedding)
        # Fix 2: Ensure 2D array: (1, 1024) instead of (1024,)
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        return embedding
```

#### 2. **Double Fix untuk Semua Methods**
- **Fix 1:** `list` → `numpy array` conversion
- **Fix 2:** `(1024,)` → `(1, 1024)` dimension reshape

#### 3. **Robust Error Handling**
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
git commit -m "Fix Jina embedding list to numpy array conversion and dimension mismatch"
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
4. **Expected:** Bot jawab tanpa error dimension atau list

### **Test 2: Category Prefix**
1. Langsung tanya: "character: Siapa Spider-Man?"
2. **Expected:** Bot jawab tanpa error dimension atau list

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

### **Option 3: Debug Embedding Type**
```python
# Debug: cek tipe dan shape embedding
embedding = model.get_embedding("test")
print(f"Type: {type(embedding)}")
print(f"Content: {embedding[:5]}...")  # First 5 values
if hasattr(embedding, 'shape'):
    print(f"Shape: {embedding.shape}")
```

## 📊 **Expected Behavior Setelah Fix:**

✅ **Bot start tanpa error dimension**  
✅ **Bot start tanpa error list.ndim**  
✅ **Embedding vectors dengan shape yang benar**  
✅ **Retrieval berfungsi normal**  
✅ **Bot bisa jawab pertanyaan Marvel**  
✅ **Feedback system berfungsi**  

## 🎯 **Success Criteria:**

- ❌ **Sebelum:** `shapes (1024,) and (1,) not aligned`
- ❌ **Sebelum:** `list object has no attribute ndim`
- ✅ **Sesudah:** `✅ Jina Embedding initialized with dimension fix`

## 🔍 **Root Cause Analysis:**

1. **Jina Embeddings v3** return `list` bukan `numpy array`
2. **LlamaIndex** expect `numpy array` dengan shape tertentu
3. **Type mismatch** menyebabkan error `list.ndim`
4. **Dimension mismatch** menyebabkan error shape alignment

---

**Note:** Fix ini sudah diterapkan di `main.py` dan `build_index.py`. Deploy ulang ke Railway untuk apply fix! 🚀 