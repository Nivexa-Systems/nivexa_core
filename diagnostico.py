import requests
import os

api_key = os.getenv("API_KEY_GEMINI")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

response = requests.get(url)
print(f"Código de respuesta: {response.status_code}")
print(response.json())