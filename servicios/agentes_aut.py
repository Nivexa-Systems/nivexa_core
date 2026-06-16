import asyncio
from scanner import ejecutar_escaneo_radar
from calculadora import auditar_inversion
from database import supabase
 
async def agente_radar_autonomo():
    """
    Agente autónomo: Escanea, filtra según criterios de usuario 
    y reporta solo oportunidades validadas.
    """
    # 1. Definir URL de escaneo (o traerla de Supabase)
    url_target = "https://www.idealista.com/venta-viviendas/madrid/con-precio-hasta_300000/" 
    
    # 2. Ejecutar escaneo (bloqueante, por eso usamos run_in_executor)
    loop = asyncio.get_running_loop()
    resultado = await loop.run_in_executor(None, ejecutar_escaneo_radar, url_target)
    
    if resultado.get("estado") == "NUEVO":
        # 3. Filtrado Inteligente (Aquí aplicas tu lógica de negocio)
        precio = float(resultado.get("precio", 0))
        
        # Consultamos filtros de los usuarios registrados
        filtros = supabase.table("config_filtros").select("*").execute()
        
        for config in filtros.data:
            # Lógica de "Chollo": ¿El precio está en presupuesto?
            if precio <= config.get("precio_max", 0):
                # Aquí podrías añadir lógica adicional como:
                # if calcular_roi_estimado(resultado) >= config.get("roi_min_objetivo"):
                
                return {
                    "encontrado": True,
                    "target_id": config.get("telegram_id"),
                    "datos": resultado
                }
    
    return {"encontrado": False}
