#!/usr/bin/env python3
"""
Test Gemini API Environment and Connection
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_api():
    """Test Gemini API setup and connection"""
    
    print("🔧 TESTING GEMINI API ENVIRONMENT")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"GEMINI_API_KEY: {'SET' if api_key else 'NOT SET'}")
    
    if not api_key:
        print("❌ No API key found. Please set GEMINI_API_KEY in .env file")
        return False
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file exists")
        with open('.env', 'r') as f:
            content = f.read()
            if 'GEMINI_API_KEY' in content:
                print("✅ GEMINI_API_KEY found in .env file")
            else:
                print("❌ GEMINI_API_KEY not found in .env file")
    else:
        print("❌ .env file does not exist")
        return False
    
    # Test import
    try:
        import google.generativeai as genai
        print("✅ google-generativeai imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import google-generativeai: {e}")
        return False
    
    # Test API initialization
    try:
        genai.configure(api_key=api_key)
        print("✅ API key configured successfully")
    except Exception as e:
        print(f"❌ Failed to configure API key: {e}")
        return False
    
    # Test model initialization
    try:
        # Try different model names
        model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        model = None
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                print(f"✅ Model '{model_name}' initialized successfully")
                break
            except Exception as e:
                print(f"⚠️  Model '{model_name}' failed: {e}")
                continue
        
        if not model:
            print("❌ All model names failed")
            return False
            
    except Exception as e:
        print(f"❌ Failed to initialize model: {e}")
        return False
    
    # Test API call
    try:
        print("🧪 Testing API call...")
        response = model.generate_content("Hello, are you working?")
        print(f"✅ API call successful: {response.text[:100]}...")
        return True
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_api()
    if success:
        print("\n🎉 GEMINI API TEST PASSED!")
    else:
        print("\n💥 GEMINI API TEST FAILED!")
