#!/usr/bin/env python3
import google.generativeai as genai
import json

# Load your API Key
try:
    with open("config/generator_config.json") as f:
        config = json.load(f)
    with open(config['GEMINI_KEYS_FILE']) as f:
        api_key = f.readline().strip()
    
    genai.configure(api_key=api_key)
    
    print(f"🔑 Using Key: {api_key[:5]}... (verified)")
    print("\n📋 AVAILABLE GEMINI MODELS:")
    print("=" * 40)
    
    count = 0
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ {m.name}")
            count += 1
            
    if count == 0:
        print("❌ No models found! Check your API key permissions.")
        
except Exception as e:
    print(f"❌ Error: {e}")