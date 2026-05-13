import os
import requests
import logging
from solver import save_to_gcs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_historical_data(days=255):
    """
    Pobiera ostatnie N tabel (dni roboczych) z API NBP. 
    Z dokumentacji wynika ze max to 255.
    """
    api_url = f"https://api.nbp.pl/api/exchangerates/tables/A/last/{days}/"
    logger.info(f"Pobieram dane historyczne z ostatnich {days} tabel...")
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()

def main():
    if not os.getenv("BUCKET_NAME"):
        logger.error("Please set BUCKET_NAME before running the historical load script.")
        return

    try:
        tables = fetch_historical_data()
        logger.info(f"Udalo sie pobrac {len(tables)} tabel.")

        success_count = 0
        for table in tables:
            filename = save_to_gcs(table)
            if filename:
                success_count += 1
                logger.info(f"Zapisano {table['effectiveDate']} -> {filename}")
            else:
                logger.error(f"Nie udalo sie zapisać danych dla {table['effectiveDate']}")

        logger.info(f"Koniec. Zapisano {success_count}/{len(tables)} plikow w Storage.")
    except Exception as e:
        logger.error(f"Blad podczas ladowania historii: {e}", exc_info=True)

if __name__ == "__main__":
    main()
