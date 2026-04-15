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

def find_cols_v2():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/columns?$top=1000"
    cols = requests.get(url, headers=headers).json()
    
    targets = [
        "Medidas Digital",
        "Dia",
        "Mes"
    ]
    
    print("=== MAPPING FOUND V2 ===")
    for c in cols.get('value', []):
        disp = c['displayName']
        internal = c['name']
        for t in targets:
            if t.lower() in disp.lower():
                print(f"DISPLAY: {disp} | INTERNAL: {internal}")
                break

find_cols_v2()
