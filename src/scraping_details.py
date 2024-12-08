import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import time
import re
import os


def get_lat_lon_from_script(soup):
    """Extrae la latitud y longitud desde el script del HTML."""
    try:
        script_tag = soup.find("script", string=lambda t: t and "latitude" in t)
        if script_tag:
            script_content = script_tag.string
            lat_match = re.search(r"latitude\s*=\s*([\d.-]+);", script_content)
            lon_match = re.search(r"longitude\s*=\s*([\d.-]+);", script_content)
            if lat_match and lon_match:
                latitude = float(lat_match.group(1))
                longitude = float(lon_match.group(1))
                return latitude, longitude
    except Exception as e:
        print(f"Error al extraer latitud y longitud: {e}")
    return None, None


def geocode_location(latitude, longitude):
    """Realiza la geocodificación inversa para obtener dirección, ciudad y barrio."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        params = {
            'format': 'json',
            'lat': latitude,
            'lon': longitude,
            'zoom': 18,
            'addressdetails': 1
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        address = data.get("address", {})
        return {
            "Dirección": address.get("road", ""),
            "Ciudad": address.get("city", address.get("town", address.get("village", ""))),
            "Barrio": address.get("suburb", address.get("neighbourhood", ""))
        }
    except Exception as e:
        print(f"Error en la geocodificación: {e}")
        return {"Dirección": None, "Ciudad": None, "Barrio": None}


def scrape_property_details(url, img_url):
    """Extrae los detalles de una propiedad específica a partir de su URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        property_data = {
            "URL Propiedad": url,
            "URL Imagen": img_url,
        }

        property_data["Fecha de Consulta"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Extraer información general
        fields = [
            ("Referencia", "li.list-group-item.property-code span.second"),
            ("Estrato", "li.list-group-item.estrato span.second"),
            ("Sector", "li.list-group-item.sector span.second"),
            ("Precio", "li.list-group-item.precio span.second"),
            ("Área", "li.list-group-item.area span.second"),
        ]
        for key, selector in fields:
            element = soup.select_one(selector)
            property_data[key] = element.text.strip() if element else None

        # Tipo de Piso
        tipo_piso = soup.find("div", class_="text-left titulo", string="Tipo de Piso")
        if tipo_piso:
            tipo_piso_value = tipo_piso.find_next("span", class_="attr-name text")
            property_data['Tipo de Piso'] = tipo_piso_value.text.strip() if tipo_piso_value else None

        # Cocina
        cocina = soup.find("div", class_="text-left titulo", string="Cocina")
        if cocina:
            cocina_value = cocina.find_next("span", class_="attr-name text")
            property_data['Cocina'] = cocina_value.text.strip() if cocina_value else None

        # Zona de Ropa
        zona_ropa = soup.find("div", class_="attr-name titulo", string="Zona de ropa")
        if zona_ropa:
            zona_ropa_value = zona_ropa.find_next("span", class_="attr-value text")
            property_data['Zona de Ropa'] = zona_ropa_value.text.strip() if zona_ropa_value else None

        # Garaje
        garaje = soup.find("div", class_="attr-name titulo", string="Garaje")
        if garaje:
            garaje_value = garaje.find_next("span", class_="attr-value text")
            property_data['Garaje'] = garaje_value.text.strip() if garaje_value else None

        # Información adicional del inmueble
        informacion_adicional = soup.find("div", class_="titulo-informacion")
        if informacion_adicional and "Información adicional del inmueble" in informacion_adicional.text:
            descripcion = informacion_adicional.find_next_sibling("div", class_="text-informacion")
            property_data['Información adicional'] = descripcion.text.strip() if descripcion else "No especificada"
        else:
            property_data['Información adicional'] = "No especificada"

        # Coordenadas de latitud y longitud
        lat, lon = get_lat_lon_from_script(soup)
        property_data['Latitud'] = lat
        property_data['Longitud'] = lon

        # Geocodificación inversa
        if lat and lon:
            geocoded_data = geocode_location(lat, lon)
            property_data.update(geocoded_data)

        # Contactos y redes sociales
        contact_info = {}
        phone_tag = soup.find("a", href=lambda href: href and href.startswith("tel:"))
        contact_info["Teléfono"] = phone_tag["href"].replace("tel:", "") if phone_tag else None
        whatsapp_tag = soup.find("a", href=lambda href: href and "web.whatsapp.com/send" in href)
        contact_info["WhatsApp"] = whatsapp_tag["href"] if whatsapp_tag else None
        facebook_tag = soup.find("a", href=lambda href: href and "facebook.com" in href)
        contact_info["Facebook"] = facebook_tag["href"] if facebook_tag else None
        instagram_tag = soup.find("a", href=lambda href: href and "instagram.com" in href)
        contact_info["Instagram"] = instagram_tag["href"] if instagram_tag else None

        property_data.update(contact_info)
        return property_data
    except Exception as e:
        print(f"Error al procesar {url}: {e}")
        return None


def scrape_details():
    """Carga las URLs y extrae los detalles de cada propiedad, manteniendo un histórico."""
    try:
        # Cargar las URLs del archivo generado en el bloque 1
        df_urls = pd.read_csv("urls_propiedades_paginas.csv")
        df_urls = df_urls.head(5)  # Limitar a 5 filas para pruebas (puedes quitarlo)

        detailed_properties = []
        for _, row in df_urls.iterrows():
            print(f"Scraping detalles de {row['URL Propiedad']} ({row['Tipo']})")
            details = scrape_property_details(row["URL Propiedad"], row["URL Imagen"])
            if details:
                details["Tipo"] = row["Tipo"]
                detailed_properties.append(details)
            time.sleep(1)  # Respetar un intervalo entre solicitudes

        # Crear el DataFrame con los nuevos detalles
        df_details = pd.DataFrame(detailed_properties)

        # Verificar si ya existe el archivo histórico
        if os.path.exists("detalles_propiedades_completo.csv"):
            # Cargar el archivo histórico existente
            df_historico = pd.read_csv("detalles_propiedades_completo.csv")

            # Concatenar el histórico con los nuevos detalles
            df_historico_actualizado = pd.concat([df_historico, df_details])

            # Eliminar duplicados basados en "URL Propiedad"
            df_historico_actualizado = df_historico_actualizado.drop_duplicates(subset=["URL Propiedad"], keep="last")

            # Guardar el histórico actualizado
            df_historico_actualizado.to_csv("detalles_propiedades_completo.csv", index=False, encoding="utf-8-sig")
            print("Histórico actualizado. Datos guardados en detalles_propiedades_completo.csv")
        else:
            # Si no existe un histórico, guardar los nuevos detalles como inicial
            df_details.to_csv("detalles_propiedades_completo.csv", index=False, encoding="utf-8-sig")
            print("Histórico creado. Datos guardados en detalles_propiedades_completo.csv")
    except Exception as e:
        print(f"Error al procesar las propiedades: {e}")
