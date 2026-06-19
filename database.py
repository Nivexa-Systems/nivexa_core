import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Inicializamos el cliente
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def init_db():
    print("✅ Conectado a Supabase.")

def registrar_anuncio(url):
    """
    Intenta insertar la URL en 'anuncios_vistos'.
    Si la URL ya existe, la restricción 'Is Unique' de Supabase evitará el duplicado 
    y lanzará una excepción que capturamos.
    """
    try:
        supabase.table("anuncios_vistos").insert({"url": url}).execute()
        return True # Es nuevo y se guardó
    except Exception as e:
        # Si llega aquí es porque ya existe o hubo error
        return False # No es nuevo o falló la inserción

def es_nuevo(url):
    """
    Verifica si una URL ya ha sido vista.
    """
    response = supabase.table("anuncios_vistos").select("url").eq("url", url).execute()
    return len(response.data) == 0