import os
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SITE_NAME_SEARCH = "SistemadeVentas2"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_token():
    tenant_id = os.getenv("SP_TENANT_ID")
    client_id = os.getenv("SP_CLIENT_ID")
    client_secret = os.getenv("SP_CLIENT_SECRET")
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {'client_id': client_id, 'scope': 'https://graph.microsoft.com/.default', 'client_secret': client_secret, 'grant_type': 'client_credentials'}
    return requests.post(url, data=data).json()['access_token']

def find_specifics():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    print("🚀 Analizando 30/2 y 6926-03 en SharePoint...")
    items_sp = []
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Unidad de Negocio/items?expand=fields"
    while url:
        res = requests.get(url, headers=headers).json()
        items_sp.extend(res['value'])
        url = res.get('@odata.nextLink')

    targets = ["30/2", "6926-03"]
    for item in items_sp:
        f = item['fields']
        op = str(f.get('OP_UNN') or f.get('OP_x002d_UNN') or '').strip()
        if op.endswith('.0'): op = op[:-2]
        
        if op in targets:
            print(f"✅ Encontrada en SP: OP {op} | Unidad: {f.get('Unidad_x0020_de_x0020_Negocio')} | Importe: {f.get('Importe_x0020_Total_x0020_con_x002')}")
            # Ver si tiene link en Supabase
            res_sb = supabase.table('ordenes_publicidad').select('id').eq('op', op).execute()
            if res_sb.data:
                print(f"   -> Link en Supabase EXISTE (ID {res_sb.data[0]['id']})")
            else:
                print(f"   -> ❌ Link en Supabase NO EXISTE. No hay orden maestra para esta OP.")

if __name__ == "__main__":
    find_specifics()
