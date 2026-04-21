import os
import requests
from dotenv import load_dotenv

load_dotenv()

def find_duplicates_un():
    tenant_id = os.getenv("SP_TENANT_ID")
    client_id = os.getenv("SP_CLIENT_ID")
    client_secret = os.getenv("SP_CLIENT_SECRET")
    
    # Token
    url_token = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        'client_id': client_id,
        'scope': 'https://graph.microsoft.com/.default',
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    token = requests.post(url_token, data=data).json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Site ID
    res_site = requests.get("https://graph.microsoft.com/v1.0/sites?search=SistemadeVentas2", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    # Obtener todo de Unidades de Negocio
    url_un = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Unidad de Negocio/items?expand=fields"
    print("Escaneando duplicados en Unidad de Negocio...")
    
    seen = {} # (op, unidad) -> id_sp
    duplicates = []
    
    next_url = url_un
    while next_url:
        res = requests.get(next_url, headers=headers).json()
        items = res.get('value', [])
        for i in items:
            f = i['fields']
            op = str(f.get('OP_UNN') or '').strip()
            unidad = str(f.get('Unidaddenegocio0') or '').strip()
            if not op or not unidad: continue
            
            key = (op, unidad)
            if key in seen:
                duplicates.append({
                    'op': op,
                    'unidad': unidad,
                    'id_original': seen[key],
                    'id_duplicado': f.get('id')
                })
            else:
                seen[key] = f.get('id')
        next_url = res.get('@odata.nextLink')

    if not duplicates:
        print("✅ No se encontraron duplicados exactos (OP + Unidad) en SharePoint.")
    else:
        print(f"❌ Se encontraron {len(duplicates)} duplicados:")
        for d in duplicates:
            print(f"   - OP {d['op']} | Unidad: {d['unidad']} (IDs SP: {d['id_original']} y {d['id_duplicado']})")

if __name__ == "__main__":
    find_duplicates_un()
