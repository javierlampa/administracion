import os, json, requests
from dotenv import load_dotenv

load_dotenv()
tenant_id = os.getenv("SP_TENANT_ID")
client_id = os.getenv("SP_CLIENT_ID")
secret = os.getenv("SP_CLIENT_SECRET")

import msal
app = msal.ConfidentialClientApplication(client_id, authority=f"https://login.microsoftonline.com/{tenant_id}", client_credential=secret)
result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
token = result["access_token"]
headers = {'Authorization': f'Bearer {token}'}
site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas", headers=headers).json()
site_id = site['value'][0]['id']

url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?$top=20&expand=fields"
resp = requests.get(url, headers=headers).json()

for i in resp['value']:
    f = i['fields']
    keys = {k: v for k, v in f.items() if "IVA" in k.upper()}
    if keys:
        print(f"ID {i['id']}: {keys}")
