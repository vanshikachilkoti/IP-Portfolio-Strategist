import os
from dotenv import load_dotenv
import requests

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
print(f"🔑 API Key: {GOOGLE_API_KEY[:20]}...")

# List of model names to try
model_names = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-1.5-pro",
    "gemini-1.5-pro-001",
    "gemini-1.5-pro-002",
    "gemini-pro",
    "gemini-pro-vision",
    "gemini-1.0-pro",
    "gemini-1.0-pro-001",
    "gemini-flash-1.5",
    "gemini-2.0-flash-exp",
]

print("\n🧪 Testing different model names...\n")

for model_name in model_names:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    
    headers = {"Content-Type": "application/json"}
    params = {"key": GOOGLE_API_KEY}
    data = {"contents": [{"parts": [{"text": "Hi"}]}]}
    
    try:
        response = requests.post(url, json=data, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            text = result['candidates'][0]['content']['parts'][0]['text']
            print(f"✅ {model_name}: SUCCESS")
            print(f"   Response: {text[:50]}...")
            print(f"   👉 USE THIS MODEL: {model_name}\n")
            break
        else:
            print(f"❌ {model_name}: Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ {model_name}: Error - {str(e)[:50]}")

print("\n" + "="*60)
print("If none worked, let's try listing available models...")
print("="*60 + "\n")

# Try to list models
list_url = "https://generativelanguage.googleapis.com/v1beta/models"
try:
    response = requests.get(list_url, params={"key": GOOGLE_API_KEY})
    if response.status_code == 200:
        models = response.json()
        print("📋 Available models:")
        for model in models.get('models', []):
            name = model.get('name', '').replace('models/', '')
            methods = model.get('supportedGenerationMethods', [])
            if 'generateContent' in methods:
                print(f"  ✅ {name}")
    else:
        print(f"Could not list models: {response.status_code}")
except Exception as e:
    print(f"Error listing models: {e}")