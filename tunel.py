from pyngrok import ngrok
import time

# Tu token va aquí, dentro de las comillas:
ngrok.set_auth_token(os.getenv("NGROK_AUTH_TOKEN"))
print("Iniciando túnel...")

try:
    public_url = ngrok.connect(8000)
    print("------------------------------------------------")
    print(f"TÚNEL ACTIVO EN: {public_url.public_url}")
    print("------------------------------------------------")
    
    while True:
        time.sleep(1)
except Exception as e:
    print(f"Error: {e}")