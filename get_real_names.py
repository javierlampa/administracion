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

def find_technical_names():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    # Traer items (con paginación para no errar)
    print(f"🚀 Buscando la OP 6048-11 en SharePoint...")
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Unidad de Negocio/items?expand=fields"
    found = False
    while url and not found:
        res = requests.get(url, headers=headers).json()
        for item in res['value']:
            f = item['fields']
            vals = str(f.values())
            if '6048-11' in vals:
                print("\n✅ ¡LA ENCONTRÉ! Estos son los campos reales:")
                import json
                print(json.dumps(f, indent=2))
                found = True
                break
        url = res.get('@odata.nextLink')

if __name__ == "__main__":
    find_technical_names()
