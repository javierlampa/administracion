import os
import requests
import msal
import time
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime
import math

load_dotenv()

# Configuración
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
TENANT_ID = os.getenv("SP_TENANT_ID")
CLIENT_ID = os.getenv("SP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SITE_NAME_SEARCH = "Sistema de Ventas"

supabase = create_client(URL, KEY)

def parse_int(val):
    if val is None or str(val).strip() == '': return None
    try: return int(float(str(val).strip()))
    except: return None

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
    return (
        {str(i['op']).strip(): i['id'] for i in all_data},
        {i['id']: i['id'] for i in all_data}
    )

def smart_find_op_id(op_text, db_maps):
    if not op_text: return None
    op_text = str(op_text).strip()
    map_str, map_id = db_maps
    if op_text in map_str: return map_str[op_text]
    try:
        val_int = int(float(op_text))
        if val_int in map_id: return map_id[val_int]
    except: pass
    root = op_text.split('-')[0].split('/')[0].split(' ')[0].strip()
    if root in map_str: return map_str[root]
    return None

def run_full_sync_tv():
    print(f"\n🚀 [FULL SYNC TV] Iniciando barrido total para TV... {datetime.now().strftime('%H:%M:%S')}")
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']

    # Cargar catálogos
    print("  -> Refrescando catálogos de Programas...")
    prog_raw = get_items_full(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Programas/items?expand=fields", headers)
    programas_map = {parse_int(i['fields'].get('id')): i['fields'].get('Title') for i in prog_raw}

    # Ubicar lista TV
    res_list = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists?select=id,displayName", headers=headers).json()
    list_tv_id = next(l['id'] for l in res_list['value'] if l['displayName'] == 'TV')
    
    print("  -> Descargando todos los ítems de TV desde SharePoint...")
    sp_items = get_items_full(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_tv_id}/items?expand=fields", headers)
    
    db_maps = get_global_ops_map()
    
    records = []
    print(f"  -> Mapeando y procesando {len(sp_items)} registros (sumando duplicados legítimos por nombre de programa)...")
    
    # Agrupar por (op_id, programa)
    merged = {}
    
    for item in sp_items:
        f = item['fields']
        op_id = smart_find_op_id(f.get('OP_TP'), db_maps)
        
        programa_nombre = programas_map.get(parse_int(f.get('ProgramasLookupId'))) or str(f.get('Programa') or f.get('Title') or '')
        tipo = f.get('TipodePublicidad')
        
        k = (op_id, programa_nombre, tipo)
        
        # Ojo que el SharePoint graph devuelve id como string, lo parseamos a int para persistir si lo necesitas, pero acá usamos deduplicación acumulativa nativa como en UN.
        if k not in merged:
            merged[k] = {
                'id': parse_int(f.get('id')), # Mantenemos uno arbitrario si se fusionan
                'op_id': op_id,
                'op_numero': str(f.get('OP_TP') or '').strip(),
                'programa_id': parse_int(f.get('ProgramasLookupId')),
                'programa_nombre': programa_nombre,
                'tipo': tipo, 
                'importe_total': parse_num(f.get('ImporteTotal')),
                'segundos': parse_int(f.get('SegundosdeTV')) or 0,
                'valor_segundo': parse_num(f.get('Valor_x0020_del_x0020_Segundo')),
                'iva': parse_num(f.get('IVA')),
                'importe_sin_iva': parse_num(f.get('ImportesinIVA')),
                'created': f.get('Created'), 
                'modified': f.get('Modified')
            }
        else:
            merged[k]['importe_total'] += parse_num(f.get('ImporteTotal'))
            merged[k]['segundos'] += (parse_int(f.get('SegundosdeTV')) or 0)
            merged[k]['importe_sin_iva'] += parse_num(f.get('ImportesinIVA'))
            merged[k]['iva'] += parse_num(f.get('IVA'))

    records = list(merged.values())
    print(f"  -> Registros en DB luego de purga y agrupación acumulativa: {len(records)}.")
    
    print("  -> Vaciando la tabla TV en Supabase en bloques pesados...")
    # Limpiamos todo
    while True:
        res = supabase.table('tv').delete().neq('id', 0).execute()
        if not res.data or len(res.data) == 0:
            break
            
    print("  -> Insertando registros limpios en DB...")
    batch_size = 500
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            supabase.table("tv").upsert(batch).execute()
            print(f"     ✅ Lote insertado: {min(i + batch_size, len(records))} / {len(records)}")
        except Exception as e:
            print(f"  [!] Error en lote {i}: {str(e)}")

    print(f"✅ [FULL SYNC TV] ¡Sincronización Total de TV finalizada! {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    run_full_sync_tv()
