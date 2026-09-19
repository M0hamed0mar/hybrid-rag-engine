"""
Test script for Google Gemini API
Lists available models and tests a simple query
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("❌ ERROR: GOOGLE_API_KEY not found in .env file")
    print("Please add: GOOGLE_API_KEY=your_key_here")
    exit(1)

# Configure Gemini
genai.configure(api_key=API_KEY)

print("=" * 60)
print("🤖 Google Gemini API Test")
print("=" * 60)

# ============================================
# 1. List all available models
# ============================================
print("\n📋 1. Listing all available models:\n")

try:
    models = genai.list_models()
    
    gemini_models = []
    for model in models:
        if "gemini" in model.name:
            gemini_models.append(model.name)
            print(f"   ✅ {model.name}")
    
    if not gemini_models:
        print("   ❌ No Gemini models found!")
        
except Exception as e:
    print(f"   ❌ Error listing models: {e}")

# ============================================
# 2. Test each model
# ============================================
print("\n" + "=" * 60)
print("🧪 2. Testing models with a simple question:")
print("   Question: 'What is 2+2? Answer in one word.'")
print("=" * 60)

# Models to test (in order of preference)
models_to_test = [
    "models/gemini-1.5-flash",
    "models/gemini-1.5-pro", 
    "models/gemini-1.0-pro",
    "models/gemini-1.0-pro-vision-latest",
]

test_query = "What is 2+2? Answer in one word only."

for model_name in models_to_test:
    print(f"\n📌 Testing: {model_name}")
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(test_query)
        
        answer = response.text.strip()
        print(f"   ✅ SUCCESS!")
        print(f"   📝 Answer: {answer}")
        
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            print(f"   ❌ Model not found")
        elif "not supported" in error_msg.lower():
            print(f"   ❌ Model exists but generateContent not supported")
        else:
            print(f"   ❌ Error: {error_msg[:100]}")

# ============================================
# 3. Test with working model (if found)
# ============================================
print("\n" + "=" * 60)
print("💬 3. Interactive test with working model")
print("=" * 60)

# Find a working model
working_model = None
for model_name in models_to_test:
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'OK' if you can hear me")
        if response.text:
            working_model = model_name
            break
    except:
        continue

if working_model:
    print(f"\n✅ Working model found: {working_model}")
    print("\n💬 Ask a question (type 'quit' to exit):\n")
    
    model = genai.GenerativeModel(working_model)
    
    while True:
        user_input = input("❓ You: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        try:
            response = model.generate_content(user_input)
            print(f"🤖 AI: {response.text}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")
else:
    print("\n❌ No working Gemini model found!")
    print("   Please check your API key or internet connection.")

# ============================================
# 4. Summary
# ============================================
print("\n" + "=" * 60)
print("📊 4. Summary")
print("=" * 60)

print(f"""
API Key Status: {'✅ Valid key found' if API_KEY else '❌ No key'}
Key value: {API_KEY[:20]}...{API_KEY[-10:] if len(API_KEY) > 30 else ''}

Recommended model for settings.py:
   LLM_MODEL = "gemini-1.5-flash"

If that doesn't work, try:
   LLM_MODEL = "gemini-1.0-pro"
""")

print("=" * 60)