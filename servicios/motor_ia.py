import google.generativeai as genai
import os
from protocolo import PROTOCOLO

def inicializar_motor():
    """Configura la API de Gemini al arrancar el sistema."""
    api_key = os.getenv("API_KEY_GEMINI")
    if not api_key:
        raise ValueError("API_KEY_GEMINI no encontrada en las variables de entorno.")
    genai.configure(api_key=api_key)

def generar_informe_forense(datos_inmueble):
    """
    Función pura: Recibe datos, devuelve el informe.
    """
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    # Ajuste de seguridad: Si los datos llegan vacíos, no gastamos tokens ni fallamos.
    if not datos_inmueble:
        return "⚠️ Error: No se recibieron datos del inmueble para analizar."

    prompt_final = f"{PROTOCOLO}\n\nDATOS DEL INMUEBLE: {datos_inmueble}\n\nGENERAR INFORME:"
    
    try:
        response = model.generate_content(prompt_final, generation_config={"temperature": 0.0})
        return response.text
    except Exception as e:
        return f"⚠️ Error en la generación del informe: {str(e)}"
