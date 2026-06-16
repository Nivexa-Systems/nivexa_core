import random
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from googlesearch import search
from database import es_nuevo_o_cambio  # Ya está aquí, es perfecto

def obtener_datos_mercado(zona):
    query = f"precio medio m2 vivienda {zona} 2026"
    try:
        resultados = list(search(query, num_results=2))
        return f"Datos de mercado real: {', '.join(resultados)}"
    except Exception:
        return "Referencia de mercado no disponible."

def ejecutar_escaneo_radar(url, zona=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            "--no-sandbox", 
            "--disable-blink-features=AutomationControlled",
            "--disable-extensions"
        ])
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(random.randint(1500, 3000))
            
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            texto = soup.get_text(separator=' ', strip=True)
            
            # Limpieza y extracción
            precio_raw = re.search(r'(\d[\d\.]*)\s*(?:€|EUR)', texto, re.IGNORECASE)
            m2_raw = re.search(r'(\d+)\s*(?:m²|metros|m2)', texto, re.IGNORECASE)
            
            datos = {
                "precio": precio_raw.group(1).replace('.', '') if precio_raw else "0",
                "m2": m2_raw.group(1) if m2_raw else "0",
                "mercado": obtener_datos_mercado(zona if zona else "zona del inmueble"),
                "url": url,
                "texto_resumen": texto[:1500]
            }

            # --- INTEGRACIÓN DE LA BASE DE DATOS ---
            if datos.get("precio") and datos.get("precio") != "0":
                anuncio_id = url.split('/')[-1] 
                estado = es_nuevo_o_cambio(anuncio_id, int(datos["precio"]))
                datos["estado"] = estado
            # ---------------------------------------
            
            return datos
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            browser.close()