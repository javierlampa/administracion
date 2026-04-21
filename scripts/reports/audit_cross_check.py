import os, requests
from dotenv import load_dotenv
from supabase import create_client
from sharepoint_sync import get_token

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
SITE_NAME_SEARCH = os.getenv("SP_SITE_NAME", "Sistema de Ventas")

def audit():
    print("🔍 Iniciando Auditoría Cruzada (SharePoint vs Portal)...")
    
    # 1. Contar en SharePoint
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?$top=1000"
    sp_count = 0
    while url:
        resp = requests.get(url, headers=headers).json()
        items = resp.get('value', [])
        sp_count += len(items)
        url = resp.get('@odata.nextLink')
    
    print(f"📊 SharePoint (Total filas): {sp_count}")

    # 2. Contar en Supabase
    res_db = supabase.table('pagos').select('id', count='exact').execute()
    db_count = res_db.count
    print(f"📊 Portal (Total filas): {db_count}")

    if sp_count == db_count:
        print("\n✅ ¡COINCIDENCIA TOTAL! No falta ni una fila.")
    else:
        diff = sp_count - db_count
        print(f"\n⚠️ DISCREPANCIA DETECTADA: Faltan {diff} registros en el Portal.")
        print("Esto se debe probablemente a registros sin número de OP en SharePoint.")

if __name__ == "__main__":
    audit()
