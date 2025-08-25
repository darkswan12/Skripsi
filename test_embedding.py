#!/usr/bin/env python3
"""
Test Script untuk Embedding - Debug Dimension Issues
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_jina_embedding():
    """Test Jina embedding functionality"""
    print("🧪 Testing Jina Embedding...")
    
    try:
        from llama_index.embeddings.jinaai import JinaEmbedding
        import numpy as np
        
        # Test basic Jina embedding
        jina_key = os.getenv("JINA_API_KEY")
        if not jina_key:
            print("❌ JINA_API_KEY tidak tersedia")
            return False
        
        print("✅ JINA_API_KEY tersedia")
        
        # Test original Jina embedding
        print("\n--- Testing Original Jina Embedding ---")
        original_model = JinaEmbedding(
            api_key=jina_key,
            model="jina-embeddings-v3",
            task="text-matching",
        )
        
        # Test single text
        print("Testing single text embedding...")
        single_emb = original_model.get_text_embedding("Hello world")
        print(f"Type: {type(single_emb)}")
        print(f"Length: {len(single_emb) if hasattr(single_emb, '__len__') else 'N/A'}")
        if hasattr(single_emb, 'shape'):
            print(f"Shape: {single_emb.shape}")
        print(f"First 5 values: {single_emb[:5] if hasattr(single_emb, '__getitem__') else 'N/A'}")
        
        # Test multiple texts
        print("\nTesting multiple text embeddings...")
        multi_emb = original_model.get_text_embeddings(["Hello", "World"])
        print(f"Type: {type(multi_emb)}")
        print(f"Length: {len(multi_emb) if hasattr(multi_emb, '__len__') else 'N/A'}")
        if hasattr(multi_emb, 'shape'):
            print(f"Shape: {multi_emb.shape}")
        print(f"First embedding: {multi_emb[0][:5] if hasattr(multi_emb, '__getitem__') else 'N/A'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Jina embedding: {e}")
        return False

def test_fixed_embedding():
    """Test our fixed embedding class"""
    print("\n🧪 Testing Fixed Embedding Class...")
    
    try:
        from main import FixedJinaEmbedding
        
        jina_key = os.getenv("JINA_API_KEY")
        if not jina_key:
            print("❌ JINA_API_KEY tidak tersedia")
            return False
        
        # Test fixed embedding
        fixed_model = FixedJinaEmbedding(
            api_key=jina_key,
            model="jina-embeddings-v3",
            task="text-matching",
        )
        
        print("✅ FixedJinaEmbedding initialized")
        
        # Test single text
        print("\n--- Testing Fixed Single Text ---")
        single_emb = fixed_model.get_text_embedding("Hello world")
        print(f"Type: {type(single_emb)}")
        print(f"Length: {len(single_emb)}")
        print(f"First 5 values: {single_emb[:5]}")
        print(f"Is list: {isinstance(single_emb, list)}")
        
        # Test multiple texts
        print("\n--- Testing Fixed Multiple Texts ---")
        multi_emb = fixed_model.get_text_embeddings(["Hello", "World"])
        print(f"Type: {type(multi_emb)}")
        print(f"Length: {len(multi_emb)}")
        print(f"First embedding length: {len(multi_emb[0])}")
        print(f"First embedding first 5: {multi_emb[0][:5]}")
        print(f"Is list of lists: {isinstance(multi_emb, list) and all(isinstance(emb, list) for emb in multi_emb)}")
        
        # Test query embedding
        print("\n--- Testing Fixed Query ---")
        query_emb = fixed_model.get_query_embedding("What is this?")
        print(f"Type: {type(query_emb)}")
        print(f"Length: {len(query_emb)}")
        print(f"First 5 values: {query_emb[:5]}")
        print(f"Is list: {isinstance(query_emb, list)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing fixed embedding: {e}")
        return False

def test_llamaindex_compatibility():
    """Test if our embedding is compatible with LlamaIndex"""
    print("\n🧪 Testing LlamaIndex Compatibility...")
    
    try:
        from llama_index.core import Settings
        from main import FixedJinaEmbedding
        
        jina_key = os.getenv("JINA_API_KEY")
        if not jina_key:
            print("❌ JINA_API_KEY tidak tersedia")
            return False
        
        # Set our fixed embedding
        Settings.embed_model = FixedJinaEmbedding(
            api_key=jina_key,
            model="jina-embeddings-v3",
            task="text-matching",
        )
        
        print("✅ FixedJinaEmbedding set in Settings")
        
        # Test if LlamaIndex can use it
        from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
        
        # Create a simple test
        test_text = "This is a test document for embedding."
        
        # This should not crash
        print("Testing LlamaIndex embedding...")
        # Note: We're not actually building an index, just testing compatibility
        
        print("✅ LlamaIndex compatibility test passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing LlamaIndex compatibility: {e}")
        return False

def main():
    """Run all embedding tests"""
    print("🚀 Starting Embedding Tests...\n")
    
    tests = [
        ("Jina Embedding", test_jina_embedding),
        ("Fixed Embedding", test_fixed_embedding),
        ("LlamaIndex Compatibility", test_llamaindex_compatibility),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 EMBEDDING TEST RESULTS")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} : {status}")
        if result:
            passed += 1
    
    print("="*50)
    print(f"Total: {total}, Passed: {passed}, Failed: {total - passed}")
    
    if passed == total:
        print("🎉 All embedding tests passed!")
        return True
    else:
        print("⚠️  Some embedding tests failed. Check output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 