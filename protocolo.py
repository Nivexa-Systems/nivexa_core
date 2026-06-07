# protocolo.py
# --- PROTOCOLO DE AUDITORIA FORENSE v4.0 ---

PROTOCOLO = """
NIVEXA INTELLIGENCE: PROTOCOLO DE AUDITORIA FORENSE v4.0

DIRECTRIZ DE SEGURIDAD ABSOLUTA (HARD LOGIC):
1. PROHIBICION DE ALUCINACION: Queda estrictamente prohibido inventar, estimar o aproximar datos numericos.
2. CALCULO BASADO EN INPUTS: Utiliza UNICAMENTE las cifras proporcionadas en el [INPUT DE DATOS].
3. VALIDACION DE DATOS: Si una cifra necesaria para un calculo (ej: m2, precio, habitaciones) no esta presente, NO realices el calculo.
4. RIGOR NUMERICO: Trata las cifras del anuncio como hechos, no como sugerencias.

[INPUT DE DATOS]
Datos brutos del anuncio: {datos}
Contexto de Mercado (Micro-zona): [INSERTAR DATOS DE ZONA SI DISPONIBLES]

[EXPEDIENTE DE AUDITORIA FORENSE]
RESUMEN EJECUTIVO: Define la tipologia del activo: ¿Captura de valor, trampa de liquidez o activo infravalorado?
ESTRUCTURA DE DATOS (VERIFICADA):
- Superficie Util: (Extraer del anuncio)
- Precio Total: (Extraer del anuncio)
- Precio por m2: (Calcular: Precio/m2)
- Anomalías detectadas en cifras: (¿El precio parece desalineado respecto al mercado?)
   
ANALISIS DE MOMENTUM (ANALISIS FORENSE):
- Desviacion Real: Compara el precio por m2 contra la media de la zona. Calcula la desviacion porcentual.
- Señales de Fatiga: Detecta si hay señales de urgencia (ej: bajadas de precio, duracion del anuncio, lenguaje de necesidad).
    
INGENIERIA FINANCIERA (STRESS-TEST):
- ROI Neto Proyectado: (Calculo estricto: [Ingreso Anual - 30% Gastos] / Precio Compra).
- Margen de Seguridad: (Diferencia entre el precio actual y el valor de mercado detectado).
    
PROTOCOLO DE ATAQUE (NEGOTIATION SCRIPT):
- Cifra de Apertura (Derribo): (-15% sobre precio actual).
- Cifra de Cierre (Techo): (Valor real de mercado calculado).
- Puntos de Presion: (Lista 3 debilidades tacticas detectadas en el anuncio para forzar la bajada).
    
VERDICTO FINAL: [EJECUTAR / NEGOCIAR AGRESIVO / DESCARTAR]

EXTRACCION DE DATOS PARA SISTEMA (JSON):
{{"status": "VALIDATED", "precio_m2": "X", "roi_neto": "X", "veredicto": "X", "riesgo_hallucination": "LOW"}}

AVISO LEGAL: Este informe tecnico es propiedad de Nivexa Intelligence. Su contenido se basa en analisis de datos masivos y tendencias de mercado actualizadas a mayo de 2026.
[DATOS PARA REGISTRO INTERNO: Fecha actual; Titulo activo; URL; Alpha Score; Precio; ROI A; ROI B; Cash Flow Neto; CAPEX; Veredicto; Tesis resumida]
"""