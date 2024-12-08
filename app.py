import logging
from src.scraping_urls import scrape_urls
from src.scraping_details import scrape_details

def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Iniciando el proceso de scraping...")

    try:
        # Paso 1: Scraping de URLs
        logging.info("Extrayendo URLs de propiedades...")
        scrape_urls()

        # Paso 2: Scraping de detalles
        logging.info("Extrayendo detalles de propiedades...")
        scrape_details()

        logging.info("Proceso completado exitosamente.")
    except Exception as e:
        logging.error(f"Error durante el proceso de scraping: {e}")

if __name__ == "__main__":
    main()

