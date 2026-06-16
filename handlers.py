# handlers.py
import requests
import trafilatura
import os
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from database import supabase
from servicios.motor_ia import generar_informe_forense
from servicios.agentes_aut import agente_radar_autonomo

# Estados de conversación
ESPERANDO_EMAIL = 1

async def enviar_mensaje_largo(update, texto):
    limite = 4000
    for i in range(0, len(texto), limite):
        await update.message.reply_text(texto[i:i + limite])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenido a Nivexa. Escribe tu email para registrarte:")
    return ESPERANDO_EMAIL

async def registrar_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    supabase.table("usuarios").upsert({
        "telegram_id": telegram_id, "username": update.effective_user.username, 
        "email": update.message.text, "estado": "pendiente"
    }).execute()
    await update.message.reply_text("✅ Registrado. Usa /pagar para elegir tu plan.")
    return ConversationHandler.END

async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Elige nivel:\n\n🔹 [NIVEL 2] 99€: https://nivexasystems-pro.lemonsqueezy.com/checkout/buy/aa55b531-0ccb-441d-bb37-8085ab33c9b7\n"
        "🔸 [NIVEL 3] 499€: https://nivexasystems-pro.lemonsqueezy.com/checkout/buy/2e7db4a1-8b15-45c7-8bda-8c687bf44d90",
        parse_mode='Markdown'
    )

async def auditar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if "idealista.com" not in user_text:
        await update.message.reply_text("⚠️ Por favor, envíame un enlace válido de idealista.com.")
        return
    
    await update.message.reply_text("🔍 Analizando activo mediante motor forense...")
    
    # Lógica de extracción (Blindaje)
    data_to_analyze = user_text
    try:
        downloaded = trafilatura.fetch_url(user_text)
        if downloaded:
            data_to_analyze = trafilatura.extract(downloaded) or user_text
    except Exception as e:
        print(f"Error en scraping: {e}")
    
    # Llamada al servicio modular de IA
    informe = generar_informe_forense(data_to_analyze)
    await enviar_mensaje_largo(update, informe)

def setup_handlers(app):
    conv_registro = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ESPERANDO_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_email)]},
        fallbacks=[]
    )
    app.add_handler(conv_registro)
    app.add_handler(CommandHandler("pagar", pagar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auditar))

async def tarea_radar_puente(bot):
    resultado = await agente_radar_autonomo()
    if resultado.get("encontrado"):
        await bot.send_message(
            chat_id=resultado["target_id"], 
            text=f"🚀 ¡Nueva oportunidad detectada!\nURL: {resultado['datos']['url']}"
        )