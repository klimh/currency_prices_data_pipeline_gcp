import requests
#import json
# from tabulate import tabulate
import pandas as pd

api_nbp = "https://api.nbp.pl/api/exchangerates/tables/A/"

response = requests.get(api_nbp).json()

df = pd.DataFrame(response[0]['rates'])
df = df[['code','currency','mid']]

print(df.to_string(index=False))

# rates = response[0]['rates']
# print(tabulate(rates, headers = "keys", tablefmt = "github"))

#print(json.dumps(nbp_data, indent=4, sort_keys=True))