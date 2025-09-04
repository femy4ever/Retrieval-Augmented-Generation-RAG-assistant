"""
Debug script to check all dependencies and setup
Run this before running the main app
"""

import sys
import os
from dotenv import load_dotenv

def check_environment():
    """Check environment setup"""
    print("🔍 Checking environment setup...")
    
    # Load .env file
    load_dotenv()
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print(f"✅ GEMINI_API_KEY found (length: {len(api_key)})")
    else:
        print("❌ GEMINI_API_KEY not found in .env file")
        return False
    
    return True

def check_dependencies():
    """Check all required packages"""
    print("\n🔍 Checking dependencies...")
    
    required_packages = [
        "chainlit",
        "chromadb", 
        "google.generativeai",
        "PyPDF2",
        "python_dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "python_dotenv":
                import dotenv
                print(f"✅ {package}")
            elif package == "google.generativeai":
                import google.generativeai as genai
                print(f"✅ {package}")
            else:
                __import__(package)
                print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_langchain():
    """Check LangChain separately as it's optional"""
    print("\n🔍 Checking LangChain...")
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        print("✅ LangChain text_splitter available")
        return True
    except ImportError:
        print("⚠️ LangChain not available - will use fallback splitter")
        return False

def test_google_api():
    """Test Google API connection"""
    print("\n🔍 Testing Google API connection...")
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ No API key available")
            return False
            
        genai.configure(api_key=api_key)
        
        # Test embedding
        result = genai.embed_content(
            model="models/embedding-001",
            content="test",
            task_type="retrieval_document"
        )
        
        if result and "embedding" in result:
            print("✅ Google API working correctly")
            return True
        else:
            print("❌ Google API test failed")
            return False
            
    except Exception as e:
        print(f"❌ Google API error: {e}")
        return False

def main():
    """Run all checks"""
    print("🚀 RAG Application Setup Check")
    print("=" * 40)
    
    all_good = True
    
    # Run checks
    all_good &= check_environment()
    all_good &= check_dependencies()
    check_langchain()  # Optional
    all_good &= test_google_api()
    
    print("\n" + "=" * 40)
    if all_good:
        print("🎉 All checks passed! You can run the app with:")
        print("   chainlit run app.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\n💡 Quick fixes:")
        print("   1. pip install -r requirements.txt")
        print("   2. Create .env file with GEMINI_API_KEY=your_key_here")
        print("   3. Get API key from: https://makersuite.google.com/app/apikey")

if __name__ == "__main__":
    main()