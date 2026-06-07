import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("API_KEY_GEMINI"))

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Modelo disponible: {m.name}")