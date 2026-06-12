import json
import hmac
import hashlib
import threading
import uvicorn
import requests
import trafilatura
import google.generativeai as genai
import asyncio
import os
from fastapi import FastAPI, Request, HTTPException
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.request import HTTPXRequest
from protocolo import PROTOCOLO
from supabase import create_client, Client
from calculadora import auditar_inversion
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scanner import ejecutar_escaneo_radar 

# --- INICIALIZACIÓN ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
genai.configure(api_key=os.getenv("API_KEY_GEMINI"))

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
model = genai.GenerativeModel("models/gemini-3.5-flash")

# --- ESTADOS PARA CONVERSACIÓN --- 
ESPERANDO_EMAIL = 1
CONFIG_PRECIO = 2
CONFIG_ROI = 3
CONFIG_ZONAS = 4

# --- FUNCIÓN PARA MENSAJES LARGOS ---
async def enviar_mensaje_largo(update, texto):
    limite = 4000
    if len(texto) <= limite:
        await update.message.reply_text(texto)
    else:
        for i in range(0, len(texto), limite):
            await update.message.reply_text(texto[i:i + limite])

# --- WEBHOOK BLINDADO ---
app_web = FastAPI()

@app_web.post("/webhook")
async def webhook_handler(request: Request):
    payload = await request.body()
    signature = request.headers.get("x-signature")
    digest = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(signature, digest):
        raise HTTPException(status_code=403, detail="Firma inválida")
    
    data = json.loads(payload)
    attributes = data.get('data', {}).get('attributes', {})
    email_pago = attributes.get('user_email')
    plan = attributes.get('product_name')

    if email_pago:
        resultado = supabase.table("usuarios").update({"estado": plan}).eq("email", email_pago).execute()
        if resultado.data:
            usuario = resultado.data[0]
            tg_id = usuario.get("telegram_id")
            if tg_id:
                bot = Bot(token=TOKEN_TELEGRAM)
                await bot.send_message(chat_id=tg_id, text=f"🎉 ¡Bienvenido al {plan}! Tu acceso ya está activo.")
    return {"status": "ok"}

# --- FUNCIONES TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenido a Nivexa. Por favor, escribe tu email para registrarte:")
    return ESPERANDO_EMAIL

async def registrar_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    telegram_id = update.effective_user.id
    username = update.effective_user.username
    
    supabase.table("usuarios").upsert({
        "telegram_id": telegram_id, 
        "username": username, 
        "email": email, 
        "estado": "pendiente"
    }).execute()
    
    await update.message.reply_text(f"✅ Registrado con éxito: {email}. Ahora puedes usar /pagar para elegir tu plan.")
    return ConversationHandler.END

async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    enlace_99 = "https://nivexasystems-pro.lemonsqueezy.com/checkout/buy/aa55b531-0ccb-441d-bb37-8085ab33c9b7"
    enlace_499 = "https://nivexasystems-pro.lemonsqueezy.com/checkout/buy/2e7db4a1-8b15-45c7-8bda-8c687bf44d90"
    
    mensaje = (
        "Elige tu nivel de auditoría:\n\n"
        f"🔹 [[NIVEL 2] Nivexa Professional - 99€]({enlace_99})\n\n"
        f"🔸 [[NIVEL 3] Nivexa Quantum Executive - 499€]({enlace_499})"
    )
    await update.message.reply_text(mensaje, parse_mode='Markdown')
    
async def auditar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    data_to_analyze = user_text
    tg_id = update.effective_user.id
    estado_extraccion = "FALLO"
    error_log = None
    
    if "idealista.com" in user_text:
        await update.message.reply_text("🔍 Analizando activo mediante motor forense...")
        exito = False
        try:
            scrape_token = os.getenv("SCRAPE_DO_TOKEN")
            proxy_url = f"http://api.scrape.do?token={scrape_token}&url={user_text}"
            response = requests.get(proxy_url, timeout=20)
            if response.status_code == 200:
                data_to_analyze = response.text
                exito = True
        except Exception as e:
            error_log = str(e)
            print(f"Scrape.do falló: {e}")

        if not exito:
            downloaded = trafilatura.fetch_url(user_text)
            if downloaded:
                extracted = trafilatura.extract(downloaded)
                if extracted:
                    data_to_analyze = extracted
                    exito = True
                else:
                    error_log = "Trafilatura no pudo extraer contenido."
            else:
                error_log = "No se pudo acceder a la URL."
        
        if exito: estado_extraccion = "EXITO"
        
        try:
            supabase.table("auditorias_logs").insert({
                "telegram_id": tg_id,
                "url_inmueble": user_text,
                "estado_extraccion": estado_extraccion,
                "error_log": error_log
            }).execute()
        except: pass
    
    try:
        prompt_extraccion = f"Analiza: {data_to_analyze[:3000]}. Extrae PRECIO, ALQUILER, METROS. Responde solo formato: PRECIO,ALQUILER,METROS. Si no hay dato pon 0."
        respuesta_ia = model.generate_content(prompt_extraccion).text.strip()
        
        def a_numero(val):
            try: return float(val.strip())
            except: return 0.0

        numeros = respuesta_ia.split(',')
        p, a, m = a_numero(numeros[0]), a_numero(numeros[1]), a_numero(numeros[2])
        
        # LLAMADA PROTEGIDA A CALCULADORA
        metricas = auditar_inversion(p, a, m)
        datos_auditados_str = ""
        
        if metricas is not None:
            try:
                supabase.table("historico_auditorias").insert({
                    "telegram_id": tg_id,
                    "precio": p,
                    "alquiler": a,
                    "metro": m,
                    "roi_calculado": metricas.get('Rentabilidad_Neta_Pct', 0),
                    "url_inmueble": user_text
                }).execute()
            except: pass
            datos_auditados_str = f"\n\nDATOS FINANCIEROS AUDITADOS: {metricas}"
        
        prompt_final = PROTOCOLO.format(datos=data_to_analyze) + datos_auditados_str
        response = model.generate_content(prompt_final)
        
    except Exception as e:
        print(f"Error en motor forense: {e}")
        response = model.generate_content(PROTOCOLO.format(datos=data_to_analyze))
    
    await enviar_mensaje_largo(update, response.text)

# --- FUNCIONES DE CONFIGURACIÓN ---
async def iniciar_configuracion(update, context):
    await update.message.reply_text("💰 Dime tu presupuesto máximo de inversión (ej. 200000):")
    return CONFIG_PRECIO

async def set_precio(update, context):
    context.user_data['precio'] = int(update.message.text)
    await update.message.reply_text("📈 ¿Cuál es tu ROI mínimo objetivo? (ej. 6.5):")
    return CONFIG_ROI

async def set_roi(update, context):
    context.user_data['roi'] = float(update.message.text)
    await update.message.reply_text("📍 ¿En qué provincias quieres buscar? (separadas por coma, ej. Madrid, Valencia):")
    return CONFIG_ZONAS

async def guardar_configuracion(update, context):
    zonas = [z.strip() for z in update.message.text.split(',')]
    tg_id = update.effective_user.id
    
    supabase.table("config_filtros").upsert({
        "telegram_id": tg_id,
        "precio_max": context.user_data['precio'],
        "roi_min_objetivo": context.user_data['roi'],
        "zonas_interes": zonas
    }).execute()
    
    await update.message.reply_text("✅ ¡Configuración guardada! Ahora el radar Nivexa está listo para buscar chollos.")
    return ConversationHandler.END

# --- LANZAMIENTO ---
async def main():
    request_config = HTTPXRequest(connection_pool_size=8, read_timeout=30.0, write_timeout=30.0, connect_timeout=30.0)
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).request(request_config).build()
    
    conv_registro = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ESPERANDO_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_email)]},
        fallbacks=[]
    )
    
    conv_config = ConversationHandler(
        entry_points=[CommandHandler("configurar", iniciar_configuracion)],
        states={
            CONFIG_PRECIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_precio)],
            CONFIG_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_roi)],
            CONFIG_ZONAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_configuracion)],
        },
        fallbacks=[]
    )
    
    app.add_handler(conv_registro)
    app.add_handler(conv_config)
    app.add_handler(CommandHandler("pagar", pagar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auditar))
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(ejecutar_escaneo_radar, 'interval', hours=2, args=["TU_URL_DE_BUSQUEDA_AQUI"])
    scheduler.start()
    
    print("🚀 Sistema Nivexa Business Core activo.")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == '__main__':
    def run_server():
        uvicorn.run(app_web, host="0.0.0.0", port=8000)
    
    threading.Thread(target=run_server, daemon=True).start()
    asyncio.run(main())