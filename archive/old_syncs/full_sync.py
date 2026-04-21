import os
import requests
import msal
import time
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Configuración
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SITE_NAME_SEARCH = "Sistema de Ventas"

supabase = create_client(URL, KEY)

import math

def parse_num(val):
    if val is None or str(val).strip() == '': return 0.0
    try:
        if isinstance(val, (int, float)):
            num = float(val)
        else:
            s_val = str(val).strip().replace('.', '').replace(',', '.')
            num = float(s_val)
        if math.isnan(num): return 0.0
        return num
    except:
        return 0.0

def get_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return result["access_token"]

def get_items_full(url, headers):
    all_items = []
    current_url = url
    while current_url:
        resp = requests.get(current_url, headers=headers)
        if resp.status_code == 429:
            time.sleep(5); continue
        res = resp.json()
        if 'value' in res: all_items.extend(res['value'])
        current_url = res.get('@odata.nextLink')
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

def run_full_sync():
    print(f"\n🚀 [FULL SYNC] Iniciando barrido total... {datetime.now().strftime('%H:%M:%S')}")
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']

    # 1. Traer todas las Unidades de Negocio de SharePoint
    res_list_un = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists?select=id,displayName", headers=headers).json()
    list_un_id = next(l['id'] for l in res_list_un['value'] if l['displayName'] == 'Unidad de Negocio')
    
    print("  -> Descargando todas las Unidades de Negocio...")
    sp_units = get_items_full(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_un_id}/items?expand=fields", headers)
    
    # 2. Mapear OPs en DB
    db_map = get_global_ops_map()
    
    # 3. Sincronizar
    print(f"  -> Procesando {len(sp_units)} registros...")
    batch_size = 500
    records = []
    
    for item in sp_units:
        f = item['fields']
        op_num = str(f.get('OP_UNN', '')).strip()
        op_id = db_map.get(op_num)
        
        payload = {
            "op_id": op_id,
            "op_numero": op_num,
            "unidad_negocio": f.get('Unidaddenegocio0'),
            "importe_total": parse_num(f.get('ImporteTotal')),
            "iva": parse_num(f.get('IVA0')),
            "importe_sin_iva": parse_num(f.get('ImportesinIVA'))
        }
        records.append(payload)

    print(f"  -> Preparados {len(records)} registros. Deduplicando fallas de SharePoint...")
    merged = {}
    for r in records:
        k = (r['op_numero'], r['unidad_negocio'])
        if k not in merged:
            merged[k] = r
        else:
            # Si SharePoint tiene 2 filas para la misma OP y misma Unidad de Negocio, las sumamos
            merged[k]['importe_total'] += r.get('importe_total', 0.0)
            merged[k]['importe_sin_iva'] += r.get('importe_sin_iva', 0.0)
    records = list(merged.values())
    print(f"  -> Registros únicos finales: {len(records)} listos para DB...")
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            supabase.table("unidades_negocio").upsert(batch, on_conflict="op_id, unidad_negocio").execute()
            print(f"  -> Lote completado: {min(i + batch_size, len(records))} / {len(records)}")
        except Exception as e:
            print(f"  [!] Error en lote {i}: {str(e)}")

    print(f"✅ [FULL SYNC] ¡Finalizado con éxito! {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    run_full_sync()
