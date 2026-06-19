import requests
from bs4 import BeautifulSoup

def extraer_datos_inmueble(url):
    """Extrae datos clave del anuncio para alimentar el motor forense."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extraemos info básica
    precio = soup.find("span", {"class": "price"}).text if soup.find("span", {"class": "price"}) else "No det."
    m2 = soup.find("span", {"class": "item-detail"}).text if soup.find("span", {"class": "item-detail"}) else "No det."
    ubicacion = soup.find("span", {"class": "main-info__title-main"}).text if soup.find("span", {"class": "main-info__title-main"}) else "Madrid"
    
    return {
        "precio": precio,
        "m2": m2,
        "ubicacion": ubicacion,
        "url": url
    }