import sqlite3

def init_db():
    conn = sqlite3.connect('radar_inmobiliario.db')
    cursor = conn.cursor()
    # Guardamos el ID del anuncio, el precio detectado y el timestamp
    cursor.execute('''CREATE TABLE IF NOT EXISTS activos 
                      (id TEXT PRIMARY KEY, precio INTEGER, url TEXT, visto_el TIMESTAMP)''')
    conn.commit()
    conn.close()

def es_nuevo_o_cambio(anuncio_id, precio_actual):
    conn = sqlite3.connect('radar_inmobiliario.db')
    cursor = conn.cursor()
    cursor.execute("SELECT precio FROM activos WHERE id = ?", (anuncio_id,))
    row = cursor.fetchone()
    
    if row is None:
        # Es nuevo, lo guardamos
        cursor.execute("INSERT INTO activos VALUES (?, ?, ?, CURRENT_TIMESTAMP)", (anuncio_id, precio_actual, ""))
        conn.commit()
        conn.close()
        return "NUEVO"
    elif row[0] != precio_actual:
        # Ha cambiado el precio
        cursor.execute("UPDATE activos SET precio = ? WHERE id = ?", (precio_actual, anuncio_id))
        conn.commit()
        conn.close()
        return "CAMBIO_PRECIO"
    
    conn.close()
    return "IGNORAR"