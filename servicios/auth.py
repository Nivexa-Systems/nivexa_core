from database import supabase

def verificar_acceso(telegram_id):
    """
    Devuelve un diccionario con el acceso del usuario.
    { "es_vip": bool, "limite_informes": int, "estado": str }
    """
    response = supabase.table("usuarios").select("estado").eq("telegram_id", telegram_id).execute()
    
    if not response.data:
        return {"es_vip": False, "estado": "pendiente"}
    
    estado = response.data[0].get("estado", "pendiente")
    
    # Definimos los estados VIP
    vip_levels = ["[NIVEL 3] Nivexa Quantum Executive", "Nivel 2", "Nivel 3", "Nivel 2 (Pro)"]
    
    return {
        "es_vip": estado in vip_levels,
        "estado": estado
    }