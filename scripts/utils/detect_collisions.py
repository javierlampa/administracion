import os, requests
from dotenv import load_dotenv
from sharepoint_sync import get_token, get_items_incremental, parse_int, parse_num, smart_find_op_id, get_global_ops_map

load_dotenv()
token = get_token()
headers = {'Authorization': f'Bearer {token}'}
SITE_NAME_SEARCH = "Sistema de Ventas"
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

db_maps = get_global_ops_map()

print("Analizando UN en SharePoint para buscar duplicados de DB...")
url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Unidad de Negocio/items?expand=fields"
items = get_items_incremental(url, headers)

seen_keys = {}
for i in items:
    f = i['fields']
    op_val = str(f.get('OP_UNN') or '').strip()
    op_id = smart_find_op_id(op_val, db_maps)
    unit = f.get('Unidaddenegocio0')
    
    key = (op_id, unit)
    if key in seen_keys:
        print(f"COLISION DETECTADA:")
        print(f"  OP 1: {seen_keys[key]} (Key: {key})")
        print(f"  OP 2: {op_val} (Key: {key})")
        print("-" * 20)
    else:
        seen_keys[key] = op_val
