import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()
TENANT_ID = os.getenv('SP_TENANT_ID')
CLIENT_ID = os.getenv('SP_CLIENT_ID')
CLIENT_SECRET = os.getenv('SP_CLIENT_SECRET')

def get_token():
    auth_url = f'https://login.microsoftonline.com/{TENANT_ID}'
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    return app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])['access_token']

def get_items(url, headers):
    all_items=[]
    current_url=url 
    while current_url:
        resp = requests.get(current_url, headers=headers)
        if resp.status_code == 429:
            import time
            time.sleep(5)
            continue
        res = resp.json()
        if 'value' in res:
            all_items.extend(res['value'])
        current_url = res.get('@odata.nextLink')
    return all_items

def main():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    site = requests.get('https://graph.microsoft.com/v1.0/sites?search=Sistema de Ventas', headers=headers).json()['value'][0]['id']
    lists = requests.get(f'https://graph.microsoft.com/v1.0/sites/{site}/lists?select=id,displayName', headers=headers).json()['value']
    un_id = next(l['id'] for l in lists if l['displayName'] == 'Unidad de Negocio')
    
    print('Descargando items de SharePoint...')
    sp_units = get_items(f'https://graph.microsoft.com/v1.0/sites/{site}/lists/{un_id}/items?expand=fields', headers)
    
    seen = {}
    dups = set()
    for item in sp_units:
        f = item['fields']
        op_num = str(f.get('OP_UNN', '')).strip()
        un = f.get('Unidaddenegocio0')
        k = (op_num, un)
        if k in seen:
            dups.add(k)
        else:
            seen[k] = True
            
    print(f'Encontradas {len(dups)} omas duplicadas:')
    for item in sp_units:
        f = item['fields']
        op_num = str(f.get('OP_UNN', '')).strip()
        un = f.get('Unidaddenegocio0')
        k = (op_num, un)
        if k in dups:
            print(f"ID: {item['id']} | OP: {op_num} | UN: {un} | ImporteTotal: {f.get('ImporteTotal')} | OP_ID_SP: {f.get('id', 'N/A')}")
            
if __name__ == '__main__':
    main()
