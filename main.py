import asyncio, threading, uvicorn, os
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

# Servicios modulares
from servicios.gestor_pagos import app_web
from servicios.motor_ia import inicializar_motor
from servicios.agentes_aut import agente_radar_autonomo

# Tus nuevos módulos de lógica (migrados)
from handlers import setup_handlers, tarea_radar_puente
from database import init_db

load_dotenv()
init_db()
inicializar_motor()

async def main():
    app = ApplicationBuilder().token(os.getenv("TOKEN_TELEGRAM")).build()
    
    # Carga todos los comandos y conversaciones desde el archivo externo
    setup_handlers(app)
    
    # Scheduler Maestro
    scheduler = AsyncIOScheduler()
    scheduler.add_job(tarea_radar_puente, 'interval', hours=2, kwargs={'bot': app.bot})
    scheduler.start()
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Future()

if __name__ == '__main__':
    threading.Thread(target=lambda: uvicorn.run(app_web, port=8000), daemon=True).start()
    asyncio.run(main())
