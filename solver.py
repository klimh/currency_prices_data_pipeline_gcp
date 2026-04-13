import requests
import json
from tabulate import tabulate
import pandas as pd

api_nbp = "https://api.nbp.pl/api/exchangerates/tables/A/"

response = requests.get(api_nbp)
nbp_data = response.json()

rates = nbp_data[0]['rates']

print(tabulate(rates, headers = "keys", tablefmt = "rounded_grid"))

#print(json.dumps(nbp_data, indent=4, sort_keys=True))