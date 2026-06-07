import os
from dotenv import load_dotenv
from supabase import create_client
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Cargar las variables desde el archivo .env
load_dotenv()

# Inicializar cliente Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def obtener_enlaces_busqueda(url_busqueda):
    try:
        with sync_playwright() as p:
            # Lanzamos el navegador con argumentos que ocultan la automatización
            browser = p.chromium.launch(headless=True, args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars"
            ])
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                viewport={'width': 390, 'height': 844}
            )
            
            page = context.new_page()
            # Ocultamos la propiedad navigator.webdriver
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print(f"DEBUG: Navegando (Modo Móvil): {url_busqueda}")
            page.goto(url_busqueda, wait_until="networkidle", timeout=60000)
            
            html = page.content()
            browser.close()
            
            soup = BeautifulSoup(html, 'html.parser')
            enlaces_encontrados = soup.select('.item-info a.item-link')
            print(f"DEBUG: Enlaces detectados: {len(enlaces_encontrados)}")
            
            return ["https://www.idealista.com" + a.get('href') for a in enlaces_encontrados if a.get('href', '').startswith('/inmueble/')]
    except Exception as e:
        print(f"Error en scanner: {e}")
        return []

def es_nuevo(url):
    """Consulta si la URL ya existe en Supabase."""
    respuesta = supabase.table("anuncios_vistos").select("url").eq("url", url).execute()
    return len(respuesta.data) == 0

def registrar_anuncio(url):
    """Guarda la URL en Supabase."""
    try:
        supabase.table("anuncios_vistos").insert({"url": url}).execute()
    except Exception as e:
        print(f"Error al registrar anuncio: {e}")

def ejecutar_escaneo_radar(url_busqueda):
    """Orquesta el proceso de escaneo, filtrado y registro."""
    print(f"--- Iniciando escaneo en: {url_busqueda} ---")
    enlaces = obtener_enlaces_busqueda(url_busqueda)
    
    if not enlaces:
        print("⚠️ No se pudieron obtener enlaces.")
    else:
        for link in enlaces:
            if es_nuevo(link):
                print(f"✅ Nuevo: {link}")
                registrar_anuncio(link)
            else:
                print(f"⚪ Anuncio ya registrado: {link}")
    print("--- Escaneo finalizado ---")

def ejecutar_escaneo_nacional():
    """Consulta Supabase y escanea todas las zonas activas."""
    print("--- Consultando zonas configuradas en Supabase ---")
    try:
        respuesta = supabase.table("config_filtros").select("*").eq("activo", True).execute()
        print(f"DEBUG: Configuración encontrada: {respuesta.data}")
        
        if not respuesta.data:
            print("⚠️ No se encontraron zonas activas en Supabase.")
            return

        for config in respuesta.data:
            url = config.get('url_busqueda')
            if url:
                ejecutar_escaneo_radar(url)
            else:
                print("⚠️ Configuración encontrada pero sin URL.")
                
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")

if __name__ == "__main__":
    ejecutar_escaneo_nacional()
