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
    return app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])["access_token"]

def check():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items?expand=fields&$top=500"
    r = requests.get(url, headers=headers).json()
    
    found = 0
    for i in r.get('value', []):
        f = i['fields']
        m = f.get('MedidasDigital') or f.get('MedidasoespaciosenDigital')
        if m:
            print(f"ID: {f.get('id')} | OP: {f.get('OP')} | MEDIDA: {m}")
            found += 1
            if found >= 5: break
    if found == 0:
        print("No se encontro ninguna con medidas digital en las primeras 500")

check()
