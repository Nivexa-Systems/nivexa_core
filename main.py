import asyncio, threading, uvicorn, os, trafilatura
from dotenv import load_dotenv

# 1. Carga inmediata y obligatoria de variables
load_dotenv()

from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Servicios modulares
from servicios.gestor_pagos import app_web
from servicios.motor_ia import inicializar_motor, generar_informe_forense
from servicios.agentes_aut import agente_radar_autonomo

# Lógica migrada
from handlers import setup_handlers, tarea_radar_puente
from database import init_db

# Inicialización del sistema
init_db()
inicializar_motor()

# --- NUEVA TAREA AUTOMÁTICA CON IA ---
async def tarea_radar_automatica(app):
    """Función que ejecuta el radar, filtra y audita los nuevos inmuebles con IA."""
    print("🕒 Radar automático despertando...")
    res = await agente_radar_autonomo()
    
    if res and res.get("encontrado"):
        chat_id = os.getenv("MI_ID_ADMIN")
        if not chat_id: return
        
        for url in res['datos']['lista']:
            try:
                # 1. Extraer contenido
                downloaded = trafilatura.fetch_url(url)
                contenido = trafilatura.extract(downloaded) if downloaded else url
                
                # 2. Auditar con el motor forense
                informe = generar_informe_forense({"contenido": contenido, "url": url, "ubicacion": "Marbella"})
                
                # 3. Enviar informe al Admin
                await app.bot.send_message(
                    chat_id=chat_id, 
                    text=f"🚀 **¡NUEVA OPORTUNIDAD DETECTADA!**\n\n{url}\n\n🔍 **INFORME FORENSE:**\n{informe}"
                )
            except Exception as e:
                print(f"Error procesando {url} con IA: {e}")
                # Si falla la IA, enviamos al menos el enlace para no perder la pista
                await app.bot.send_message(chat_id=chat_id, text=f"🚀 Nueva oportunidad (sin informe): {url}")

async def main():
    token = os.getenv("TOKEN_TELEGRAM")
    if not token:
        print("ERROR: TOKEN_TELEGRAM no encontrado en .env")
        return

    app = ApplicationBuilder().token(token).build()
    
    # Carga todos los comandos y conversaciones
    setup_handlers(app)
    
    # Scheduler Maestro
    scheduler = AsyncIOScheduler()
    
    # Mantenemos tu tarea puente y añadimos la nueva automática cada 60 min
    scheduler.add_job(tarea_radar_puente, 'interval', hours=2, kwargs={'bot': app.bot})
    scheduler.add_job(tarea_radar_automatica, 'interval', minutes=60, kwargs={'app': app})
    scheduler.start()
    
    # Secuencia de inicio robusta
    await app.initialize()
    await app.start()
    print("🚀 Bot Nivexa conectado a Telegram...")
    
    await app.updater.start_polling()
    print("👂 Bot escuchando actualizaciones...")
    
    # Mantenemos el bot vivo esperando eventos
    await asyncio.Event().wait()

if __name__ == '__main__':
    # Lanzamiento paralelo del servidor de pagos y el bot
    threading.Thread(target=lambda: uvicorn.run(app_web, host="0.0.0.0", port=8000), daemon=True).start()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot detenido por el usuario.")