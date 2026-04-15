import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SITE_NAME_SEARCH = "Sistema de Ventas"

def get_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return result["access_token"]

token = get_token()
headers = {'Authorization': f'Bearer {token}'}

# Get Site ID
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

# Get items to find OP 179
url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden%20de%20Publicidad/items?expand=fields&$filter=fields/OP eq '179'"
resp = requests.get(url, headers=headers).json()

if 'value' in resp and len(resp['value']) > 0:
    fields = resp['value'][0]['fields']
    print(f"\n--- INSPECTING FIELDS FOR OP 179 ---")
    for k, v in sorted(fields.items()):
        print(f"{k}: {v}")
else:
    print("OP 179 not found in the first batch, searching without filter...")
    url_all = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden%20de%20Publicidad/items?expand=fields&$top=100"
    resp_all = requests.get(url_all, headers=headers).json()
    for item in resp_all['value']:
        if str(item['fields'].get('OP')) == '179':
             for k, v in sorted(item['fields'].items()):
                print(f"{k}: {v}")
             break

    print("No items found")
