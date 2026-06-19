import asyncio
from playwright.async_api import async_playwright
from database import supabase

async def ejecutar_escaneo_radar_local():
    """Agente: Lee EXCLUSIVAMENTE lo que ya tienes abierto en la pestaña de Chrome."""
    async with async_playwright() as p:
        try:
            print("DEBUG: Conectando a tu sesión activa de Chrome...")
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            
            page = None
            for context in browser.contexts:
                for p_ in context.pages:
                    if "idealista.com" in p_.url:
                        page = p_
                        break
            
            if not page:
                print("ERROR: No tienes ninguna pestaña de idealista.com abierta.")
                return {"estado": "FALLO"}
            
            print(f"DEBUG: Leyendo pestaña: {page.url}")
            
            enlaces = await page.eval_on_selector_all(
                "a", 
                "elements => elements.filter(e => e.href.includes('/inmueble/')).map(e => e.href)"
            )
            
            unique_links = list(set(enlaces))
            
            if not unique_links:
                print("DEBUG: No se detectaron enlaces.")
            else:
                print(f"DEBUG: ÉXITO. Se han detectado {len(unique_links)} inmuebles.")
                
            return {"estado": "OK", "enlaces": unique_links} if unique_links else {"estado": "FALLO"}
            
        except Exception as e:
            print(f"Error al conectar: {e}")
            return {"estado": "FALLO"}

async def agente_radar_autonomo():
    """Escanea y filtra: Solo devuelve los inmuebles nuevos no registrados en Supabase."""
    resultado = await ejecutar_escaneo_radar_local()
    
    if resultado.get("estado") == "OK" and resultado.get("enlaces"):
        nuevos_inmuebles = []
        
        for url in resultado["enlaces"]:
            try:
                # Verificamos si existe antes de insertar para evitar errores de red innecesarios
                check = supabase.table("anuncios_vistos").select("url").eq("url", url).execute()
                
                if not check.data:
                    # No existe, lo insertamos
                    supabase.table("anuncios_vistos").insert({"url": url}).execute()
                    nuevos_inmuebles.append(url)
                    print(f"DEBUG: Nuevo inmueble registrado -> {url}")
                else:
                    # Ya existe, lo saltamos
                    continue
            except Exception as e:
                print(f"Error al procesar URL {url}: {e}")
                continue
        
        if nuevos_inmuebles:
            return {
                "encontrado": True,
                "target_id": None, 
                "datos": {
                    "url": nuevos_inmuebles[0],
                    "cantidad": len(nuevos_inmuebles),
                    "lista": nuevos_inmuebles[:5]
                }
            }
    
    return {"encontrado": False}