import os, requests
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

url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?$top=999&expand=fields"
all_items = []
while url:
    resp = requests.get(url, headers=headers).json()
    if 'value' in resp: all_items.extend(resp['value'])
    url = resp.get('@odata.nextLink')

for i in all_items:
    f = i['fields']
    if '102/0' in str(f) or '1330' in str(f):
        print(f"FOUND MATCH SP_ID {i['id']}: ")
        for key, val in f.items():
            if val is not None and ('102/0' in str(val) or '1330' in str(val)):
                print(f"   {key}: {val}")
