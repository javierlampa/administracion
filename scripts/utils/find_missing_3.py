import os
import requests
from dotenv import load_dotenv
from supabase import create_client

# Script AUTÓNOMO para comparar SharePoint vs Supabase
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
    data = {
        'client_id': client_id,
        'scope': 'https://graph.microsoft.com/.default',
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    return requests.post(url, data=data).json()['access_token']

def get_items(base_url, headers):
    all_items = []
    next_url = base_url
    while next_url:
        res = requests.get(next_url, headers=headers).json()
        if 'value' in res: all_items.extend(res['value'])
        next_url = res.get('@odata.nextLink')
    return all_items

def find_missing_3():
    print(f"🚀 Iniciando búsqueda de los 3 registros perdidos...")
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    # Obtener ID del sitio
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    # 1. Traer todo de SharePoint (Unidad de Negocio)
    print("  -> Descargando de SharePoint...")
    items_sp = get_items(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Unidad de Negocio/items?expand=fields", headers)
    
    # 2. Traer todo de Supabase
    print("  -> Descargando de Supabase...")
    items_sb = []
    for i in range(0, 10000, 1000):
        res = supabase.table('unidades_negocio').select('op_numero, unidad_negocio, importe_total').range(i, i+999).execute()
        if not res.data: break
        items_sb.extend(res.data)

    print(f"📊 Totales -> SharePoint: {len(items_sp)} | Supabase: {len(items_sb)}")

    # Set de comparación
    sb_keys = set()
    for r in items_sb:
        imp = round(float(r['importe_total'] or 0), 2)
        sb_keys.add((str(r['op_numero']).strip(), str(r['unidad_negocio']).strip(), imp))

    missing = []
    seen_in_sp = {} # Para detectar duplicados en SP
    
    for item in items_sp:
        f = item['fields']
        op = str(f.get('OP_UNN') or f.get('OP_x002d_UNN') or '').strip()
        if op.endswith('.0'): op = op[:-2]
        un = str(f.get('Unidad_x0020_de_x0020_Negocio') or '').strip()
        imp = round(float(f.get('Importe_x0020_Total_x0020_con_x002') or 0), 2)
        
        key = (op, un, imp)
        if key not in sb_keys:
            missing.append({'id': f.get('id'), 'op': op, 'un': un, 'imp': imp})
        
        seen_in_sp[key] = seen_in_sp.get(key, 0) + 1

    # Reporte
    if missing:
        print(f"\n❌ Se encontraron {len(missing)} registros en SharePoint que NO están en Supabase:")
        for m in missing:
            print(f"   - ID SP {m['id']} | OP: {m['op']} | Unidad: {m['un']} | Importe: ${m['imp']:,.2f}")
    
    # Detectar duplicados en SharePoint
    sp_dupes = {k: v for k, v in seen_in_sp.items() if v > 1}
    if sp_dupes:
        print(f"\n⚠️ Se encontraron {sum(sp_dupes.values()) - len(sp_dupes)} duplicados en SharePoint (mismo OP, UN e Importe):")
        for k, v in sp_dupes.items():
            print(f"   - OP {k[0]} | Unidad: {k[1]} | Importe: ${k[2]:,.2f} (Aparece {v} veces)")

if __name__ == "__main__":
    find_missing_3()
