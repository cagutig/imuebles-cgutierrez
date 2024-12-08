import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL base del portal
BASE_URL = "https://www.arrendamientossantafe.com/propiedades/"

# Función para extraer propiedades de una página
def scrape_properties_from_page(page_url):
    """Extrae información de propiedades desde una página específica."""
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Contenedor de propiedades
    properties_container = soup.find("div", class_="row mt-4 properties-to-display")
    if not properties_container:
        return []

    properties = []
    for property_card in properties_container.find_all("div", class_="property-card"):
        try:
            # URL de la propiedad
            property_link = property_card.find("a")["href"]
            full_property_url = f"https://www.arrendamientossantafe.com{property_link}"

            # URL de la imagen
            img_style = property_card.find("div", class_="img-preview")["style"]
            img_url = img_style.split("url(")[-1].split(")")[0].replace('"', '')

            # Agregar la información a la lista
            properties.append({
                "URL Propiedad": full_property_url,
                "URL Imagen": img_url,
            })
        except Exception as e:
            print(f"Error al procesar una propiedad: {e}")
    return properties

# Función principal de scraping
def scrape_urls():
    """Realiza el scraping de todas las páginas y guarda las URLs en un archivo CSV."""
    business_types = [
        {"tipo": "Venta", "url_param": "Venta"},
        {"tipo": "Arrendamiento", "url_param": "Arrendar"}
    ]

    all_properties = []
    for business in business_types:
        tipo = business["tipo"]
        url_param = business["url_param"]
        page_number = 1
        previous_urls = set()

        while True:
            page_url = f"{BASE_URL}?page={page_number}&&bussines_type={url_param}"
            print(f"Scraping página {page_number} para {tipo}: {page_url}")
            properties = scrape_properties_from_page(page_url)

            # Verificar si la página actual tiene las mismas propiedades que la anterior
            current_urls = {prop["URL Propiedad"] for prop in properties}
            if current_urls == previous_urls or not properties:
                print(f"Página {page_number} es igual a la anterior o no tiene propiedades. Fin del scraping.")
                break

            # Agregar tipo de negocio y propiedades a la lista principal
            for prop in properties:
                prop["Tipo"] = tipo
            all_properties.extend(properties)
            previous_urls = current_urls
            page_number += 1

    # Crear el DataFrame inicial con las URLs, las imágenes y el tipo de propiedad
    df_urls = pd.DataFrame(all_properties)

    # Agregar columna de índice
    df_urls.insert(0, "Índice Propiedad", range(1, len(df_urls) + 1))

    # Guardar el DataFrame en un archivo CSV
    df_urls.to_csv("urls_propiedades_paginas.csv", index=False, encoding="utf-8")
    print("Scraping completado. Datos guardados en urls_propiedades_paginas.csv")

    # Mostrar resumen
    print(f"Total de propiedades extraídas: {len(df_urls)}")


