import os
import requests
from dotenv import load_dotenv
import msal

load_dotenv('.env')

TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SITE_NAME_SEARCH = "Sistema de Ventas"

def get_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    return app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])["access_token"]

def dmp():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    # Columnas TOTALES
    url_cols = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/columns?$top=1000"
    rcols = requests.get(url_cols, headers=headers).json()
    print("=== TODAS LAS COLUMNAS DE ORDEN DE PUBLICIDAD ===")
    for c in rcols.get('value', []):
        print(f"Name: {c['name']} | Display: {c['displayName']}")
    
    # Unidades de Negocio
    url_un = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Unidad de Negocio/items?expand=fields&$top=5"
    run = requests.get(url_un, headers=headers).json()
    print("\n=== UNIDADES NEGOCIO SAMPLE FIELDS ===")
    if 'value' in run:
        for item in run['value']:
            fields = item['fields']
            if fields:
                print(f"Item ID: {fields.get('id')}")
                for k, v in fields.items():
                    print(f"  {k}: {v}")
                break

dmp()
