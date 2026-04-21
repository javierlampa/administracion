import os
from dotenv import load_dotenv
from supabase import create_client
import requests

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# 1. Get SB keys
res = supabase.table("tv").select("op_numero, programa_nombre, tipo").execute()
sb_keys = set()
for r in res.data:
    sb_keys.add((str(r['op_numero'] or '').strip(), str(r['programa_nombre'] or '').strip(), str(r['tipo'] or '').strip()))
print(f"Supabase has {len(sb_keys)} unique business keys.")

# 2. Get SP keys
from sharepoint_sync import get_token, get_items_incremental, parse_int
token = get_token()
headers = {'Authorization': f'Bearer {token}'}
SITE_NAME_SEARCH = "Sistema de Ventas"
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

# Programas map
prog_raw = get_items_incremental(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Programas/items?expand=fields", headers)
prog_map = {parse_int(i['fields'].get('id')): i['fields'].get('Title') for i in prog_raw}

url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/TV/items?expand=fields&$top=999"
items_sp = get_items_incremental(url, headers)

sp_keys = []
for i in items_sp:
    f = i['fields']
    op = str(f.get('OP_TP') or '').strip()
    p_id = parse_int(f.get('ProgramasLookupId'))
    prog = str(prog_map.get(p_id) or f.get('Programa') or f.get('Title') or '').strip()
    tipo = str(f.get('TipodePublicidad') or '').strip()
    sp_keys.append((op, prog, tipo))

print(f"SharePoint has {len(items_sp)} total records.")
unique_sp_keys = set(sp_keys)
print(f"SharePoint has {len(unique_sp_keys)} unique business keys.")

intersection = unique_sp_keys.intersection(sb_keys)
print(f"Overlap: {len(intersection)} keys match perfectly.")

missing = unique_sp_keys - sb_keys
print(f"Keys in SP but not in SB: {len(missing)}")

if missing:
    print("\nExample of missing keys (top 5):")
    for m in list(missing)[:5]:
        print(m)
