import google.generativeai as genai
import os

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("API Key not found in environment")
else:
    genai.configure(api_key=api_key)
    print(f"Checking models with key: {api_key[:5]}...")
    try:
        models = genai.list_models()
        found = False
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
                found = True
        if not found:
            print("No models found supporting generateContent.")
    except Exception as e:
        print(f"Error listing models: {e}")
