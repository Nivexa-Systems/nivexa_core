import os
from dotenv import load_dotenv
from supabase import create_client
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import urllib.parse

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def obtener_enlaces_busqueda(url_busqueda):
    try:
        api_key = os.getenv("SCRAPE_DO_TOKEN")
        if not api_key:
            print("ERROR: SCRAPE_DO_TOKEN no configurada en .env")
            return []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Simulamos ser un iPhone 13
            iphone = p.devices['iPhone 13']
            context = browser.new_context(**iphone)
            page = context.new_page()
            
            # Navegación usando el modo super=true
            url_codificada = urllib.parse.quote(url_busqueda)
            proxy_url = f"http://api.scrape.do?token={api_key}&url={url_codificada}&render=true&super=true"
            
            print(f"DEBUG: Navegando como iPhone 13: {url_busqueda}")
            page.goto(proxy_url, timeout=90000)
            
            html = page.content()
            
            # --- LA "CHIVATA" ---
            print(f"DEBUG: Las primeras 200 letras del HTML recibido son: {html[:200]}")
            
            with open("debug_idealista.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            browser.close()
            
            soup = BeautifulSoup(html, 'html.parser')
            enlaces_encontrados = soup.select('a.item-link')
            print(f"DEBUG: Enlaces detectados: {len(enlaces_encontrados)}")
            
            return ["https://www.idealista.com" + a.get('href') for a in enlaces_encontrados if a.get('href', '').startswith('/inmueble/')]
    except Exception as e:
        print(f"Error en scanner: {e}")
        return []

def es_nuevo(url):
    respuesta = supabase.table("anuncios_vistos").select("url").eq("url", url).execute()
    return len(respuesta.data) == 0

def registrar_anuncio(url):
    try:
        supabase.table("anuncios_vistos").insert({"url": url}).execute()
    except Exception as e:
        print(f"Error al registrar anuncio: {e}")

def ejecutar_escaneo_radar(url_busqueda):
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
    print("--- Consultando zonas configuradas en Supabase ---")
    try:
        respuesta = supabase.table("config_filtros").select("*").eq("activo", True).execute()
        if not respuesta.data:
            print("⚠️ No se encontraron zonas activas en Supabase.")
            return

        for config in respuesta.data:
            url = config.get('url_busqueda')
            if url:
                ejecutar_escaneo_radar(url)
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")

if __name__ == "__main__":
    ejecutar_escaneo_nacional()