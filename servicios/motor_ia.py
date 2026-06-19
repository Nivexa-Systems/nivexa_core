import os
import time
import requests
from ddgs import DDGS
from protocolo import PROTOCOLO

def inicializar_motor():
    if not os.getenv("API_KEY_GEMINI"):
        raise ValueError("API_KEY_GEMINI no encontrada.")

def investigar_mercado(datos_inmueble):
    """Investigación autónoma: Busca el precio de mercado para el activo."""
    try:
        # Extraemos ubicación o por defecto Madrid
        ubicacion = datos_inmueble.get("ubicacion", "Madrid")
        query = f"precio medio m2 alquiler y venta {ubicacion} junio 2026 idealista"
        
        with DDGS() as ddgs:
            resultados = list(ddgs.text(query, max_results=3))
            return str(resultados)
    except Exception as e:
        return f"Datos de mercado no disponibles temporalmente: {e}"

def generar_informe_forense(datos_inmueble):
    """Motor forense con Inteligencia Competitiva integrada."""
    api_key = os.getenv("API_KEY_GEMINI")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    if not datos_inmueble:
        return "⚠️ Error: No se recibieron datos del activo."

    # 1. Investigación en tiempo real
    contexto_mercado = investigar_mercado(datos_inmueble)
    
    # 2. Prompt optimizado para razonamiento y estimación
    prompt_final = f"""
    {PROTOCOLO}
    
    DATOS DEL INMUEBLE A AUDITAR: 
    {datos_inmueble}
    
    INTELIGENCIA COMPETITIVA (Datos de mercado en tiempo real):
    {contexto_mercado}
    
    INSTRUCCIÓN DE PROCESAMIENTO:
    Como CIO, tu misión es auditar el activo. Si faltan datos en el anuncio proporcionado, 
    NO utilices "DATO NO VERIFICABLE" de forma generalizada. 
    RAZONAMIENTO: Utiliza la "INTELIGENCIA COMPETITIVA" y tu conocimiento para inferir 
    valores de mercado razonables. Marca estas inferencias como [ESTIMACIÓN].
    Solo si el riesgo es catastrófico o la información es nula, aplica el "Derecho a Veto".
    Tu objetivo es proporcionar un análisis financiero que permita al inversor tomar una decisión.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt_final}]}],
        "generationConfig": {"temperature": 0.3}
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"⚠️ Error técnico en la auditoría (HTTP {response.status_code})"
            
    except Exception as e:
        return f"⚠️ Fallo de conexión forense: {e}"