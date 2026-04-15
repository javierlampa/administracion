import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")

def get_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return result["access_token"]

token = get_token()
headers = {'Authorization': f'Bearer {token}'}

# Buscar el Site ID primero
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas", headers=headers).json()
site_id = res_site['value'][0]['id']

# Buscar la lista
res_list = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists?select=id,displayName", headers=headers).json()
list_id = next(l['id'] for l in res_list['value'] if l['displayName'] == 'Orden de Publicidad')

# Listar todas las columnas (columnas de sitio / lista)
res_cols = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/columns", headers=headers).json()
print("--- COLUMNAS DE LA LISTA EN SHAREPOINT ---")
for col in res_cols['value']:
    if 'Canje' in col['displayName']:
        print(f"- {col['displayName']} (Internal: {col['name']})")
