"""
Diagnóstico de la OP 7605: compara SharePoint vs Supabase
"""
import os, requests
from dotenv import load_dotenv
from supabase import create_client
from sharepoint_sync import get_token, get_items_incremental

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
SITE_NAME_SEARCH = os.getenv("SP_SITE_NAME", "Sistema de Ventas")

token = get_token()
headers = {'Authorization': f'Bearer {token}'}
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

# 1. Lo que hay en Supabase
print("=== SUPABASE: registros con op_numero = '7605' ===")
res = supabase.table('pagos').select('id, sp_id, op_numero, fecha_pago, importe_pago, comision, importe_comision').eq('op_numero', '7605').execute()
for r in res.data:
    print(r)

print(f"\nTotal en Supabase: {len(res.data)}")

# 2. Lo que hay en SharePoint (búsqueda por OP)
print("\n=== SHAREPOINT: items con OP = '7605' ===")
url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?expand=fields&$filter=fields/OP eq '7605'&$top=50"
items = get_items_incremental(url, headers)
for i in items:
    f = i['fields']
    print(f"  SP_ID={f.get('id')} | OP={f.get('OP')} | OPLookupId={f.get('OPLookupId')} | Importe={f.get('ImportePago')} | Fecha={f.get('FechadePago','')[:10]}")

print(f"\nTotal en SharePoint (búsqueda por OP='7605'): {len(items)}")

# 3. Buscar también por OPLookupId por si el campo es un Lookup
print("\n=== SUPABASE: todos los sp_id que tienen op_numero = '7605' ===")
sp_ids = [r['sp_id'] for r in res.data]
print(f"sp_ids en DB: {sp_ids}")
for sp_id in sp_ids:
    url2 = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items/{sp_id}?expand=fields"
    resp = requests.get(url2, headers=headers).json()
    if 'fields' in resp:
        f = resp['fields']
        print(f"  SP item {sp_id}: OP={f.get('OP')} | OPLookupId={f.get('OPLookupId')} | Importe={f.get('ImportePago')} | Fecha={f.get('FechadePago','')[:10]}")
    else:
        print(f"  SP item {sp_id}: NO ENCONTRADO EN SHAREPOINT -> {resp.get('error', {}).get('message')}")
