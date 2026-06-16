from fastapi import FastAPI, Request, HTTPException
from telegram import Bot
from supabase import create_client
import hmac
import hashlib
import os
import json

# Inicializamos el cliente de Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

app_web = FastAPI()

@app_web.post("/webhook")
async def webhook_handler(request: Request):
    """
    Endpoint profesional para recibir notificaciones de pagos.
    Verifica la integridad de la firma y procesa el acceso del usuario.
    """
    payload = await request.body()
    signature = request.headers.get("x-signature")
    
    # 1. Blindaje: Verificación de firma obligatoria
    digest = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature or "", digest):
        raise HTTPException(status_code=403, detail="Firma de pago inválida")
    
    # 2. Procesamiento de datos
    data = json.loads(payload)
    attributes = data.get('data', {}).get('attributes', {})
    email_pago = attributes.get('user_email')
    plan = attributes.get('product_name')

    if email_pago:
        # 3. Actualización de estado en base de datos
        resultado = supabase.table("usuarios").update({"estado": plan}).eq("email", email_pago).execute()
        
        # 4. Notificación al usuario (si está registrado)
        if resultado.data:
            usuario = resultado.data[0]
            tg_id = usuario.get("telegram_id")
            if tg_id:
                try:
                    bot = Bot(token=TOKEN_TELEGRAM)
                    await bot.send_message(
                        chat_id=tg_id, 
                        text=f"🎉 ¡Bienvenido al {plan}! Tu acceso ya está activo en el ecosistema Nivexa."
                    )
                except Exception as e:
                    print(f"Error enviando notificación post-pago: {e}")
                    
    return {"status": "ok", "message": "Procesado correctamente"}
