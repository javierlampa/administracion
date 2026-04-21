import os, requests, time
from dotenv import load_dotenv
from sharepoint_sync import get_token, get_items_incremental, parse_int

load_dotenv()

token = get_token()
headers = {'Authorization': f'Bearer {token}'}
SITE_NAME_SEARCH = "Sistema de Ventas"
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

def run_cleanup_un(dry_run=True):
    print(f"\n{'[SIMULACIÓN]' if dry_run else '[EJECUCIÓN REAL]'} Iniciando limpieza de Unidades de Negocio huérfanas...")
    
    # 1. Cargar Maestras
    url_maestra = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items?expand=fields&$top=999"
    items_maestra = get_items_incremental(url_maestra, headers)
    ops_validas = {str(i['fields'].get('OP') or '').strip() for i in items_maestra if i['fields'].get('OP')}
    print(f"✅ Maestras: {len(ops_validas)} OPs válidas.")

    # 2. Cargar Unidades
    url_un = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Unidad de Negocio/items?expand=fields&$top=999"
    items_un = get_items_incremental(url_un, headers)
    
    huerfanas = []
    for i in items_un:
        op = str(i['fields'].get('OP_UNN') or '').strip()
        if op not in ops_validas:
            huerfanas.append({'id': i['id'], 'op': op, 'unidad': i['fields'].get('Unidaddenegocio0'), 'fecha': i['fields'].get('Created')})

    print(f"⚠️ TOTAL ENCONTRADAS PARA BORRAR: {len(huerfanas)}")
    
    if dry_run:
        print("\nPrimeras 20 huérfanas:")
        for h in huerfanas[:20]:
            print(f" - OP: {h['op']} | Unidad: {h['unidad']} | ID_SP: {h['id']}")
    else:
        # BORRADO REAL
        count = 0
        for h in huerfanas:
            requests.delete(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Unidad de Negocio/items/{h['id']}", headers=headers)
            count += 1
            if count % 10 == 0: print(f" Borradas {count}...")
        print(f"✅ FIN: {count} eliminadas.")

if __name__ == "__main__":
    # PROCEDIENDO AL BORRADO REAL SEGÚN OK DEL USUARIO
    run_cleanup_un(dry_run=False)
