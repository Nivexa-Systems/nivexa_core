import re

# --- MOTOR DE CÁLCULO FORENSE ---

TABLA_ZONAS = {
    "premium": {"comunidad_m2": 1.5, "ibi_pct": 0.006},
    "estandar": {"comunidad_m2": 1.0, "ibi_pct": 0.004},
    "economica": {"comunidad_m2": 0.6, "ibi_pct": 0.003}
}

def limpiar_numero(valor):
    """Limpia strings como '2.100.000 €' y los convierte en float puro."""
    if isinstance(valor, (int, float)):
        return float(valor)
    if not valor:
        return 0.0
    # Elimina todo excepto números y puntos decimales
    # Si el valor tiene puntos de miles y comas de decimales, lo normaliza
    texto = str(valor).replace('.', '').replace(',', '.')
    solo_numeros = re.sub(r'[^\d.]', '', texto)
    try:
        return float(solo_numeros)
    except ValueError:
        return 0.0

def auditar_inversion(precio_raw, alquiler_raw, metros_raw, tipo_zona="estandar"):
    # 1. Limpieza de datos (El puente entre la IA y el motor)
    precio = limpiar_numero(precio_raw)
    alquiler = limpiar_numero(alquiler_raw)
    metros = limpiar_numero(metros_raw)
    
    # 2. Validación estricta
    if not (precio > 0 and alquiler > 0 and metros > 0):
        return None 
    
    # 3. Parámetros según zona
    params = TABLA_ZONAS.get(tipo_zona, TABLA_ZONAS["estandar"])
    
    # 4. Inversión Total (Precio + 10% gastos adquisición)
    gastos_adquisicion = precio * 0.10
    inversion_total = precio + gastos_adquisicion
    
    # 5. Gastos Anuales
    ingresos_brutos = alquiler * 12
    comunidad = (metros * params["comunidad_m2"]) * 12
    ibi = precio * params["ibi_pct"]
    mantenimiento = precio * 0.01
    gestion = ingresos_brutos * 0.10
    seguro = ingresos_brutos * 0.04
    
    gastos_anuales = comunidad + ibi + mantenimiento + gestion + seguro
    
    # 6. Métricas Financieras
    cash_flow_neto = ingresos_brutos - gastos_anuales
    rentabilidad = (cash_flow_neto / inversion_total) * 100
    
    # Semáforo de riesgo
    if rentabilidad >= 6.0: calificacion = "VERDE (Excelente)"
    elif rentabilidad >= 4.0: calificacion = "AMARILLO (Mercado)"
    else: calificacion = "ROJO (Riesgo/Bajo retorno)"
    
    return {
        "Inversion_Total": round(inversion_total, 2),
        "Cash_Flow_Neto_Anual": round(cash_flow_neto, 2),
        "Rentabilidad_Neta_Pct": round(rentabilidad, 2),
        "Calificacion": calificacion,
        "Zona": tipo_zona
    }