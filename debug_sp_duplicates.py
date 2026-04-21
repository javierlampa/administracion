import os, requests
from dotenv import load_dotenv
from sharepoint_sync import get_token, get_items_incremental, parse_int

load_dotenv()
token = get_token()
headers = {'Authorization': f'Bearer {token}'}
SITE_NAME_SEARCH = "Sistema de Ventas"
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

# Lista de OPs sospechosas de ser duplicados reales o clones
ops_to_check = ["36085", "36125", "5693-06", "6864"]

url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/TV/items?expand=fields"
items = get_items_incremental(url, headers)

print(f"Analizando {len(items)} registros de TV en SharePoint...\n")

for op in ops_to_check:
    print(f"--- Datos para OP {op} ---")
    found = [i['fields'] for i in items if str(i['fields'].get('OP_TP')).strip() == op]
    for idx, f in enumerate(found):
        print(f"Registro {idx+1}:")
        print(f"  ID SP    : {f.get('id')}")
        print(f"  Programa : {f.get('Programa')} / {f.get('Title')}")
        print(f"  Tipo     : {f.get('TipodePublicidad')}")
        print(f"  Total    : {f.get('ImporteTotal')}")
        print(f"  Segundos : {f.get('SegundosdeTV')}")
        print(f"  Created  : {f.get('Created')}")
        print("-" * 30)
    if not found:
        print("No se encontró en SharePoint.")
    print("\n")
