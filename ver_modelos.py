import google.generativeai as genai
import os

# Asegúrate de tener cargada tu API_KEY_GEMINI
api_key = os.getenv("API_KEY_GEMINI")
genai.configure(api_key=api_key)

print("--- MODELOS DISPONIBLES EN TU CUENTA ---")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Modelo: {m.name}")