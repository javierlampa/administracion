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
    res = requests.post(url, data={
        'client_id': client_id,
        'scope': 'https://graph.microsoft.com/.default',
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }).json()
    return res['access_token']

def scan_lists():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    lists_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists"
    res = requests.get(lists_url, headers=headers).json()
    
    print("--- LISTAS DISPONIBLES EN SHAREPOINT ---")
    for s_list in res.get('value', []):
        name = s_list.get('name')
        if any(kw in name.lower() for kw in ['banner', 'digital', 'venta', 'tipo']):
            print(f"- {name}")

if __name__ == "__main__":
    scan_lists()
