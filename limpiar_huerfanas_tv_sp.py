import os, requests
from dotenv import load_dotenv
from sharepoint_sync import get_token, get_items_incremental

load_dotenv()

token = get_token()
headers = {'Authorization': f'Bearer {token}'}
SITE_NAME_SEARCH = "Sistema de Ventas"
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

def cleanup_tv_huerfanas():
    print("🔄 Iniciando limpieza de TV en SharePoint...")
    
    # Maestras
    url_m = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items?expand=fields&$top=999"
    items_m = get_items_incremental(url_m, headers)
    ops_validas = {str(i['fields'].get('OP') or '').strip() for i in items_m if i['fields'].get('OP')}
    
    # TV
    url_tv = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/TV/items?expand=fields&$top=999"
    items_tv = get_items_incremental(url_tv, headers)
    
    huerfanas = []
    for i in items_tv:
        op = str(i['fields'].get('OP_TP') or '').strip()
        if op not in ops_validas:
            huerfanas.append({'id': i['id'], 'op': op})

    print(f"⚠️  Borrando {len(huerfanas)} huérfanas de TV...")
    count = 0
    for h in huerfanas:
        requests.delete(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/TV/items/{h['id']}", headers=headers)
        count += 1
        if count % 20 == 0: print(f"  -> Borradas {count}...")
    
    print(f"✅ FINALIZADO: {count} eliminadas de la lista de TV.")

if __name__ == "__main__":
    cleanup_tv_huerfanas()
