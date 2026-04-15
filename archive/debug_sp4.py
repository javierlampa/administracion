import os
import requests
from dotenv import load_dotenv

load_dotenv('.env')

TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SITE_NAME_SEARCH = "Sistema de Ventas"

import msal
def get_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    return app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])["access_token"]

def ds():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/columns"
    cols = requests.get(url, headers=headers).json()
    for col in cols.get('value', []):
        if col.get('name') == 'Nombre_x0020_del_x0020_Comercio':
            print("COMERCIO LOOKUP:", col.get('lookup'))
        elif 'Vendedor' in col.get('name', ''):
            print("VENDEDOR LOOKUP:", col.get('name'), col.get('lookup'))

ds()
