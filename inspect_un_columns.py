import os
import requests
from dotenv import load_dotenv

load_dotenv()
SITE_NAME_SEARCH = "SistemadeVentas2"

def get_token():
    tenant_id = os.getenv("SP_TENANT_ID")
    client_id = os.getenv("SP_CLIENT_ID")
    client_secret = os.getenv("SP_CLIENT_SECRET")
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {'client_id': client_id, 'scope': 'https://graph.microsoft.com/.default', 'client_secret': client_secret, 'grant_type': 'client_credentials'}
    return requests.post(url, data=data).json()['access_token']

def inspect_columns():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    # Obtener ID del sitio
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    # Obtener la lista "Unidad de Negocio"
    res_lists = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists", headers=headers).json()
    un_list = [l for l in res_lists['value'] if l['displayName'] == 'Unidad de Negocio'][0]
    list_id = un_list['id']
    
    # Obtener Columnas
    print(f"🚀 Inspeccionando columnas de la lista 'Unidad de Negocio'...")
    res_cols = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/columns", headers=headers).json()
    
    for col in res_cols['value']:
        print(f"👉 Display: {col['displayName']} | Name: {col['name']}")

if __name__ == "__main__":
    inspect_columns()
