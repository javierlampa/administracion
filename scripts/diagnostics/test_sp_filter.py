import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def get_token():
    tenant_id = os.getenv("SP_TENANT_ID")
    client_id = os.getenv("SP_CLIENT_ID")
    client_secret = os.getenv("SP_CLIENT_SECRET")
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        'client_id': client_id,
        'scope': 'https://graph.microsoft.com/.default',
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    res = requests.post(url, data=data).json()
    return res['access_token']

def test_filter():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}', 'Prefer': 'HonorNonIndexedQueriesWarningMayFail'}
    
    SITE_NAME_SEARCH = "SistemadeVentas2"
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    # Modified in the last 2 hours
    since = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
    print(f"Buscando cambios desde: {since}")
    
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items?expand=fields&$filter=fields/Modified ge '{since}'"
    res = requests.get(url, headers=headers).json()
    
    if 'error' in res:
        print("Error en filtro:", res['error'])
    else:
        items = res.get('value', [])
        print(f"Encontrados {len(items)} cambios.")
        for i in items:
            print(f" - OP: {i['fields'].get('OP')} | Modificado: {i['fields'].get('Modified')}")

if __name__ == "__main__":
    test_filter()
