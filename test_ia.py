import os
from dotenv import load_dotenv

load_dotenv()
clave = os.getenv("GEMINI_API_KEY")

if clave:
    print(f"¡Clave detectada! Longitud: {len(clave)}")
    print(f"Primeros 4 caracteres: {clave[:4]}")
else:
    print("ERROR: No se ha detectado ninguna clave en el archivo .env")