import os
import json
import requests
import pandas as pd
from datetime import datetime
from fastapi import FastAPI
from google.cloud import storage

app = FastAPI()

BUCKET_NAME = os.getenv("BUCKET_NAME")


def fetch_nbp_data():
    api_nbp = "https://api.nbp.pl/api/exchangerates/tables/A/"
    response = requests.get(api_nbp)
    response.raise_for_status()
    return response.json()


def save_to_gcs(data):
    if not BUCKET_NAME:
        print("Error: path BUCKET_NAME is not set")
        return None

    try:
        client = storage.Client()
        bucket = client.get_bucket(BUCKET_NAME)

        filename = f"rates_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"
        blob = bucket.blob(filename)

        blob.upload_from_string(
            data=json.dumps(data, indent=4),
            content_type='application/json'
        )
        return filename
    except Exception as e:
        print(f"Error during write to GCS: {e}")
        return None


@app.get("/")
def get_and_save_data():
    data = fetch_nbp_data()
    saved_file = save_to_gcs(data)

    return {
        "status": "success",
        "file_saved": saved_file,
        "data": data[0]['rates']
    }


@app.get("/table")
def get_formatted_table():
    data = fetch_nbp_data()
    rates = data[0]['rates']
    df = pd.DataFrame(rates)
    return df[['code', 'currency', 'mid']].to_dict(orient="records")