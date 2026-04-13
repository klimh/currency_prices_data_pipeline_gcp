import requests
from fastapi import FastAPI
#import json
# from tabulate import tabulate
import pandas as pd

app = FastAPI()

def fetch_nbp_data():
    api_nbp = "https://api.nbp.pl/api/exchangerates/tables/A/"
    response = requests.get(api_nbp)
    return response.json()[0]['rates']
@app.get("/")
def get_rates():
    rates = fetch_nbp_data()
    return {"status": "success", "data": rates}

@app.get("/table")
def get_formatted_table():
    rates = fetch_nbp_data()
    df = pd.DataFrame(rates)
    return df[['code', 'currency', 'mid']].to_dict(orient="records")

# rates = response[0]['rates']
# print(tabulate(rates, headers = "keys", tablefmt = "github"))

#print(json.dumps(nbp_data, indent=4, sort_keys=True))