import os
import requests
import msal
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SITE_NAME_SEARCH = "Sistema de Ventas"

supabase = create_client(URL, KEY)

def get_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return result["access_token"]

def get_all_items(url, headers):
    all_items = []
    while url:
        resp = requests.get(url, headers=headers)
        res = resp.json()
        if 'value' in res: all_items.extend(res['value'])
        url = res.get('@odata.nextLink')
    return all_items

def get_global_ops_map():
    all_data = []
    offset = 0
    limit = 1000
    while True:
        res = supabase.table("ordenes_publicidad").select("id, op").range(offset, offset + limit - 1).execute()
        if not res.data: break
        all_data.extend(res.data)
        if len(res.data) < limit: break
        offset += limit
    return {str(i['op']).strip(): i['id'] for i in all_data}

print("Iniciando diagnostico de huerfanos...")
token = get_token()
headers = {'Authorization': f'Bearer {token}'}

res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

db_ops_map = get_global_ops_map()
valid_op_ids = set(db_ops_map.values())

print("\n--- UNIDADES DE NEGOCIO ---")
unItems = get_all_items(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Unidad de Negocio/items?expand=fields&$top=5000", headers)
orphans_un = []
for i in unItems:
    f = i['fields']
    op_num = str(f.get('OP_UNN') or '').strip()
    op_id = db_ops_map.get(op_num)
    if op_id not in valid_op_ids:
        orphans_un.append((op_num, f.get('Unidaddenegocio0'), f.get('ImporteTotal')))

print(f"Total huerfanos: {len(orphans_un)}")
for o in orphans_un[:15]:
    print(o)

print("\n--- PAGOS ---")
pagItems = get_all_items(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?expand=fields&$top=5000", headers)
orphans_pag = []
for i in pagItems:
    f = i['fields']
    op_id_sp = f.get('OPLookupId')
    op_num = str(f.get('OP') or '').strip()
    op_id = op_id_sp or db_ops_map.get(op_num)
    if op_id not in valid_op_ids:
        orphans_pag.append((op_id, op_num, f.get('ImportePago')))

print(f"Total huerfanos: {len(orphans_pag)}")
for o in orphans_pag[:15]:
    print(o)

