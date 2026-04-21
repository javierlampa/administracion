import os, requests
from dotenv import load_dotenv
from sharepoint_sync import get_token

load_dotenv()
token = get_token()
headers = {'Authorization': f'Bearer {token}'}
SITE_NAME_SEARCH = "Sistema de Ventas"
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

# Traer solo los primeros 3 registros para ver los campos
url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?expand=fields&$top=3"
resp = requests.get(url, headers=headers).json()

for item in resp.get('value', []):
    print("CAMPOS DEL ITEM:")
    for k, v in item['fields'].items():
        print(f"  {k}: {v}")
    print("---")
