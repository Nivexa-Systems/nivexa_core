from fastapi import FastAPI, Request, HTTPException
from telegram import Bot
from supabase import create_client
import hmac
import hashlib
import os
import json
import logging

# Configuración de logs para auditoría
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NivexaPagos")

# Inicialización
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

app_web = FastAPI()

@app_web.post("/webhook")
async def webhook_handler(request: Request):
    """
    Endpoint robusto para LemonSqueezy. 
    Procesa suscripciones y notifica al usuario en Telegram.
    """
    payload = await request.body()
    signature = request.headers.get("x-signature")
    
    # 1. Blindaje: Verificación de firma
    if not WEBHOOK_SECRET:
        logger.error("WEBHOOK_SECRET no configurado")
        raise HTTPException(status_code=500, detail="Configuración interna faltante")

    digest = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature or "", digest):
        logger.warning("Intento de webhook con firma inválida")
        raise HTTPException(status_code=403, detail="Firma de pago inválida")
    
    # 2. Procesamiento
    data = json.loads(payload)
    event_name = data.get('meta', {}).get('event_name') # Es útil saber si es 'order_created', 'subscription_created', etc.
    attributes = data.get('data', {}).get('attributes', {})
    email_pago = attributes.get('user_email')
    plan = attributes.get('product_name')

    logger.info(f"Procesando pago: {plan} para {email_pago}")

    if email_pago and plan:
        # 3. Actualización de estado en base de datos
        # Usamos update, pero nos aseguramos de que el email exista
        resultado = supabase.table("usuarios").update({"estado": plan}).eq("email", email_pago).execute()
        
        if resultado.data:
            usuario = resultado.data[0]
            tg_id = usuario.get("telegram_id")
            if tg_id:
                try:
                    bot = Bot(token=TOKEN_TELEGRAM)
                    await bot.send_message(
                        chat_id=tg_id, 
                        text=f"🎉 **¡Pago recibido con éxito!**\n\nTu suscripción a {plan} ya está activa.\nYa tienes acceso total al ecosistema Nivexa. ¡A cazar oportunidades!"
                    )
                    logger.info(f"Notificación enviada a {tg_id}")
                except Exception as e:
                    logger.error(f"Error enviando notificación Telegram: {e}")
            return {"status": "ok", "message": "Procesado y notificado"}
        else:
            logger.warning(f"Pago recibido para {email_pago}, pero el usuario no está en la base de datos.")
            return {"status": "error", "message": "Usuario no encontrado"}
                    
    return {"status": "error", "message": "Datos incompletos en el payload"}