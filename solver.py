import os
import logging
import json
import requests
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, HTTPException
from google.cloud import storage
from google.cloud import logging as cloud_logging
from google.cloud import bigquery

try:
    logging_client = cloud_logging.Client()
    logging_client.setup_logging()
except Exception:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

app = FastAPI()

BUCKET_NAME = os.getenv("BUCKET_NAME")
PROJECT_ID = os.getenv("PROJECT_ID")


def fetch_nbp_data():
    api_nbp = "https://api.nbp.pl/api/exchangerates/tables/A/"
    response = requests.get(api_nbp)
    response.raise_for_status()
    return response.json()

#print(fetch_nbp_data()[0])

def save_to_gcs(data):
    if not BUCKET_NAME:
        logger.error("path BUCKET_NAME is not set")
        return None

    try:
        client = storage.Client()
        bucket = client.get_bucket(BUCKET_NAME)

        filename = f"rates_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"
        blob = bucket.blob(filename)

        json_line = json.dumps(data)

        blob.upload_from_string(
            data=json_line,
            content_type='application/json'
        )
        return filename
    except Exception as e:
        logger.error(f"Error during write to GCS: {e}", exc_info=True)
        return None


@app.get("/")
def get_and_save_data():
    try:
        data = fetch_nbp_data()[0]
        saved_file = save_to_gcs(data)
        
        if not saved_file:
            raise Exception("Failed to save data to GCS bucket")

        logger.info(f"Successfully downloaded and saved NBP data to {saved_file}")
        return {
            "status": "success",
            "file_saved": saved_file,
            "data": data['rates']
        }
    except Exception as e:
        logger.error("Failed to process get_and_save_data request", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/table")
def get_formatted_table():
    try:
        data = fetch_nbp_data()[0]
        rates = data['rates']
        df = pd.DataFrame(rates)
        return df[['code', 'currency', 'mid']].to_dict(orient="records")
    except Exception as e:
        logger.error("Failed to format table data", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to parse external data")

@app.get("/health")
def health_check():
    """
    Endpoint that checks if the application is alive (used for load balancing, cloud run healthchecks)
    """
    return {"status": "healthy", "service": "nbp-pipeline"}

@app.get("/analyze")
def analyze_data():
    """
    Shows 'Production & Data Engineering Thinking'.
    The application uses BigQuery to query its own Data Lake.
    It takes for example 5 currencies with the highest exchange rate to show the analysis
    """
    if not PROJECT_ID:
        logger.error("PROJECT_ID environment variable is missing for BQ connection")
        raise HTTPException(status_code=500, detail="Missing PROJECT_ID")

    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Query in BQ that unpacks (UNNEST) the nested(zagniezdzona) structure 'rates' from the JSON file
        query = f"""
        SELECT rate.code, rate.currency, rate.mid
        FROM `{PROJECT_ID}.nbp_analytics.exchange_rates_raw` t,
        UNNEST(t.rates) as rate
        ORDER BY rate.mid DESC
        LIMIT 5
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        top_currencies = []
        for row in results:
            top_currencies.append({
                "code": row.code,
                "currency": row.currency,
                "mid": row.mid
            })
            
        logger.info("Successfully fetched analyzed data from BigQuery")
        return {"top_5_currencies": top_currencies}
        
    except Exception as e:
        logger.error("Error querying BigQuery in /analyze endpoint", exc_info=True)
        raise HTTPException(status_code=500, detail="Can't fetch from Data Warehouse")