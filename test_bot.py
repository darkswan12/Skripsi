#!/usr/bin/env python3
"""
Automated Testing Script untuk Bot Telegram Marvel
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test environment variables dan dependencies"""
    print("🔍 Testing Environment...")
    
    # Check environment variables
    required_vars = ["TELEGRAM_BOT_TOKEN", "GROQ_API_KEY", "JINA_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    print("✅ Environment variables OK")
    
    # Check data directory
    data_dir = Path("data")
    if not data_dir.exists():
        print("❌ Data directory tidak ada")
        return False
    
    print("✅ Data directory OK")
    
    # Check storage directory
    storage_dir = Path("storage")
    if not storage_dir.exists():
        print("⚠️  Storage directory tidak ada, akan dibuat saat runtime")
    else:
        print("✅ Storage directory OK")
    
    return True

def test_dependencies():
    """Test Python dependencies"""
    print("\n📦 Testing Dependencies...")
    
    try:
        import telegram
        print("✅ python-telegram-bot OK")
    except ImportError:
        print("❌ python-telegram-bot tidak terinstall")
        return False
    
    try:
        import llama_index
        print("✅ llama-index OK")
    except ImportError:
        print("❌ llama-index tidak terinstall")
        return False
    
    try:
        from llama_index.llms.groq import Groq
        print("✅ llama-index-llms-groq OK")
    except ImportError:
        print("❌ llama-index-llms-groq tidak terinstall")
        return False
    
    try:
        from llama_index.embeddings.jinaai import JinaEmbedding
        print("✅ llama-index-embeddings-jinaai OK")
    except ImportError:
        print("❌ llama-index-embeddings-jinaai tidak terinstall")
        return False
    
    return True

def test_data_files():
    """Test data files dan struktur"""
    print("\n📁 Testing Data Files...")
    
    data_dir = Path("data")
    categories = ["character", "factions", "items", "maps", "npc", "timeline"]
    
    total_files = 0
    for cat in categories:
        cat_dir = data_dir / cat
        if cat_dir.exists():
            md_files = list(cat_dir.glob("*.md"))
            print(f"✅ {cat}: {len(md_files)} files")
            total_files += len(md_files)
        else:
            print(f"❌ {cat}: folder tidak ada")
    
    print(f"📊 Total markdown files: {total_files}")
    return total_files > 0

def test_build_index():
    """Test build_index.py"""
    print("\n🔨 Testing Build Index...")
    
    try:
        # Import build_index functions
        from build_index import main as build_main
        
        # Run build process
        print("Building index...")
        build_main()
        
        # Check if storage was created
        storage_dir = Path("storage")
        if storage_dir.exists():
            categories = ["character", "factions", "items", "maps", "npc", "timeline"]
            built_categories = []
            
            for cat in categories:
                cat_dir = storage_dir / cat
                if cat_dir.exists():
                    built_categories.append(cat)
            
            print(f"✅ Index built for {len(built_categories)} categories: {built_categories}")
            return True
        else:
            print("❌ Storage directory tidak dibuat")
            return False
            
    except Exception as e:
        print(f"❌ Error building index: {e}")
        return False

def test_bot_initialization():
    """Test bot initialization"""
    print("\n🤖 Testing Bot Initialization...")
    
    try:
        # Import main functions
        from main import init_llm, load_retrievers
        
        # Test LLM initialization
        print("Testing LLM...")
        llm = init_llm()
        print("✅ LLM initialized OK")
        
        # Test retrievers loading
        print("Testing retrievers...")
        success = load_retrievers()
        if success:
            print("✅ Retrievers loaded OK")
        else:
            print("⚠️  Retrievers not loaded (will be built at runtime)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing bot: {e}")
        return False

def run_all_tests():
    """Run semua tests"""
    print("🚀 Starting Bot Tests...\n")
    
    tests = [
        ("Environment", test_environment),
        ("Dependencies", test_dependencies),
        ("Data Files", test_data_files),
        ("Build Index", test_build_index),
        ("Bot Initialization", test_bot_initialization),
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
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1
    
    print("="*50)
    print(f"Total: {total}, Passed: {passed}, Failed: {total - passed}")
    
    if passed == total:
        print("🎉 All tests passed! Bot siap untuk deploy.")
        return True
    else:
        print("⚠️  Some tests failed. Fix issues before deploying.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 