import trafilatura
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from database import supabase
from servicios.motor_ia import generar_informe_forense
from servicios.agentes_aut import agente_radar_autonomo
from config import ADMIN_IDS

# --- ESTADOS Y FUNCIONES AUXILIARES ---
ESPERANDO_EMAIL = 1

async def enviar_mensaje_largo(update, texto):
    limite = 4000
    for i in range(0, len(texto), limite):
        await update.message.reply_text(texto[i:i + limite])

# --- COMANDOS Y CONVERSACIONES ---
async def start(update, context):
    await update.message.reply_text("Bienvenido a Nivexa. Escribe tu email para registrarte:")
    return ESPERANDO_EMAIL

async def registrar_email(update, context):
    telegram_id = update.effective_user.id
    supabase.table("usuarios").upsert({
        "telegram_id": telegram_id, "username": update.effective_user.username, 
        "email": update.message.text, "estado": "pendiente"
    }).execute()
    await update.message.reply_text("✅ Registrado. Usa /pagar para elegir tu plan.")
    return ConversationHandler.END

async def pagar(update, context):
    mensaje = (
        "💎 **ELIGE TU NIVEL DE AUDITORÍA**\n\n"
        "🔹 `NIVEL 2 - 99€`: https://nivexasystems-pro.lemonsqueezy.com/checkout/buy/aa55b531-0ccb-441d-bb37-8085ab33c9b7\n\n"
        "🔸 `NIVEL 3 - 499€`: https://nivexasystems-pro.lemonsqueezy.com/checkout/buy/2e7db4a1-8b15-45c7-8bda-8c687bf44d90"
    )
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def check(update, context):
    if update.effective_user.id not in ADMIN_IDS: return 
    if not context.args: return await update.message.reply_text("Uso: /check email@ejemplo.com")
    email = context.args[0]
    usuario = supabase.table("usuarios").select("*").eq("email", email).execute()
    if usuario.data:
        data = usuario.data[0]
        await update.message.reply_text(f"👤 USUARIO: {data['username']}\n📊 ESTADO: {data['estado']}")
    else:
        await update.message.reply_text("❌ Usuario no encontrado.")

async def setvip(update, context):
    if update.effective_user.id not in ADMIN_IDS or len(context.args) < 2: return
    email, nivel = context.args[0], " ".join(context.args[1:])
    resultado = supabase.table("usuarios").update({"estado": nivel}).eq("email", email).execute()
    if resultado.data: await update.message.reply_text(f"✅ Usuario {email} actualizado a: {nivel}")

# --- RADAR DE PRUEBA (TEST DE CORTOCIRCUITO) ---
async def probar_radar(update, context):
    await update.message.reply_text("🔍 Radar activado: Escaneando Idealista...")
    res = await agente_radar_autonomo()
    
    if res and res.get("encontrado"):
        datos = res.get("datos", {})
        cantidad = datos.get("cantidad", 0)
        # Formateamos la lista de enlaces encontrados
        lista_enlaces = "\n".join(datos.get("lista", []))
        mensaje = f"🚀 ¡Éxito! He detectado {cantidad} inmuebles.\n\nAquí tienes los primeros:\n\n{lista_enlaces}"
        await update.message.reply_text(mensaje)
    else:
        await update.message.reply_text("❌ No encontré anuncios. Revisa la terminal para ver si hay un error de bloqueo.")

# --- AUDITORÍA FORENSE (EL CORAZÓN) ---
async def auditar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id
    
    if len(user_text) < 100:
        await update.message.reply_text("⚠️ Por favor, envíame el texto del anuncio completo o un enlace de Idealista para poder realizar la auditoría.")
        return
    
    usuario_db = supabase.table("usuarios").select("estado").eq("telegram_id", user_id).execute()
    estado = usuario_db.data[0]['estado'] if usuario_db.data else "pendiente"
    es_vip = estado in ["[NIVEL 3] Nivexa Quantum Executive", "Nivel 2", "Nivel 3", "Nivexa Professional"] 
    
    msg = await update.message.reply_text("🔍 [NIVEXA] Procesando activos y calculando viabilidad...")
    
    contenido = user_text
    if "idealista.com" in user_text:
        try:
            downloaded = trafilatura.fetch_url(user_text)
            if downloaded:
                contenido = trafilatura.extract(downloaded) or user_text
        except Exception as e:
            print(f"Error scraping: {e}")
    
    data_to_analyze = {"contenido": contenido, "ubicacion": "Marbella"}
    
    informe, intentos = None, 0
    max_intentos = 3 if es_vip else 1 

    while intentos < max_intentos:
        try:
            resultado = generar_informe_forense(data_to_analyze)
            informe = str(resultado)
            if any(p in informe for p in ["Quota", "429", "Error"]): raise Exception("Saturado")
            break 
        except:
            intentos += 1
            if not es_vip: break

    if not informe or "⚠️" in informe:
        await msg.edit_text("⚠️ CAPACIDAD FORENSE OCUPADA. El motor está procesando alta carga.")
        return

    if es_vip:
        await msg.delete()
        await enviar_mensaje_largo(update, informe)
    else:
        resumen = informe.split("---")[0].replace("*", "").replace("`", "")
        await msg.edit_text(
            f"💎 **PREVIEW GRATUITA**\n\n{resumen[:800]}...\n\n⚠️ **INFORME BLOQUEADO**\n/pagar para desbloquear.",
            parse_mode='Markdown'
        )

# --- SETUP Y TAREA ---
def setup_handlers(app):
    conv = ConversationHandler(entry_points=[CommandHandler("start", start)], 
                               states={ESPERANDO_EMAIL: [MessageHandler(filters.TEXT, registrar_email)]}, fallbacks=[])
    app.add_handler(conv)
    app.add_handler(CommandHandler("pagar", pagar))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("setvip", setvip))
    app.add_handler(CommandHandler("probar_radar", probar_radar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auditar))

async def tarea_radar_puente(bot):
    res = await agente_radar_autonomo()
    if res and res.get("encontrado"): 
        await bot.send_message(chat_id=res["target_id"], text=f"🚀 ¡Nueva oportunidad!\n{res['datos']['url']}")