import os
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

# Configuración
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
    res = requests.post(url, data=data).json()
    return res['access_token']

def parse_num(val):
    if val is None or val == "": return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(',', '.')
        return float(val)
    except: return 0.0

def parse_int(val):
    if val is None or val == "": return 0
    try: return int(float(val))
    except: return 0

def get_changed_ops(site_id, headers, hours=24):
    """Busca qué OPs fueron modificadas recientemente en CUALQUIER lista de SharePoint"""
    since = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%SZ')
    print(f"🔍 [SCAN] Buscando cambios desde: {since}...")
    
    lists_to_check = [
        ("Orden de Publicidad", "OP"),
        ("TV", "OP_TP"),
        ("Unidad de Negocio", "OP_UNN"),
        ("Pagos", "OP")
    ]
    
    changed_ops = set()
    for list_name, op_field in lists_to_check:
        # Nota: expand=fields facilitá mucho el mapeo, pero $filter requiere HonorNonIndexedQueries
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_name}/items?expand=fields&$filter=fields/Modified ge '{since}'"
        res = requests.get(url, headers=headers).json()
        
        if 'value' in res:
            items = res['value']
            for item in items:
                op = str(item['fields'].get(op_field) or '').strip()
                if op: changed_ops.add(op)
        elif 'error' in res:
            print(f"⚠️ Error en lista {list_name}: {res['error'].get('message')}")
            
    return list(changed_ops)

def run_incremental_sync(hours=24):
    print(f"\n⚡ [SINCRONIZADOR DIA A DIA] Iniciando... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    token = get_token()
    headers = {'Authorization': f'Bearer {token}', 'Prefer': 'HonorNonIndexedQueriesWarningMayFail'}
    
    # 1. Obtener ID del sitio
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    if not res_site.get('value'): raise Exception("No se encontró el sitio de SharePoint")
    site_id = res_site['value'][0]['id']
    
    # 2. Identificar OPs afectadas
    ops_to_sync = get_changed_ops(site_id, headers, hours)
    if not ops_to_sync:
        print("✅ No se detectaron cambios en las últimas horas.")
        return

    print(f"📦 Se encontraron {len(ops_to_sync)} órdenes para actualizar: {ops_to_sync}")

    # 3. Cache de Maestros y Mappings (Para coherencia con Espejo Total)
    from sharepoint_sync import get_global_ops_map, smart_find_op_id
    db_maps = get_global_ops_map()
    
    def fetch_cat_mapping(sp_list, display_name_field="Title"):
        items = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{sp_list}/items?expand=fields", headers=headers).json().get('value', [])
        return {parse_int(i['fields'].get('id')): i['fields'].get(display_name_field) or i['fields'].get('Title') for i in items}

    print("  -> Refrescando catálogos...")
    programas_map = fetch_cat_mapping("Programas")
    vendedores_map = fetch_cat_mapping("Vendedores", "Nombre_Vendedor") # Ajustado según sharepoint_sync
    clientes_raw = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Clientes_1/items?expand=fields", headers=headers).json().get('value', [])
    clientes_map = {parse_int(i['fields'].get('id')): i['fields'].get('Nombre_x0020_Comercial') or i['fields'].get('Razon_x0020_Social') or i['fields'].get('Title') for i in clientes_raw}

    # 4. Sincronización Quirúrgica de cada OP
    for op_num in ops_to_sync:
        print(f"  -> Sincronizando OP #{op_num}")
        
        # --- A. MAESTRA (ordenes_publicidad) ---
        url_m = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items?expand=fields&$filter=fields/OP eq '{op_num}'"
        res_m = requests.get(url_m, headers=headers).json().get('value', [])
        if res_m:
            f = res_m[0]['fields']
            try:
                supabase.table("ordenes_publicidad").upsert({
                    'op': op_num,
                    'importe_total': parse_num(f.get('Total')), 
                    'fecha_orden': f.get('Fecha_x0020_de_x0020_la_x0020_Or'),
                    'cliente_nombre': clientes_map.get(parse_int(f.get('Nombre_x0020_del_x0020_ComercioLookupId'))),
                    'vendedor_nombre': vendedores_map.get(parse_int(f.get('VendedorLookupId'))),
                    'programa_nombre': f.get('Programa') or f.get('Programas') or f.get('Title'),
                    'empresa': str(f.get('Empresa') or ''),
                    'numero_factura': f.get('UnidaddeNegocio2'),
                    'esta_facturado': bool(f.get('EstaFacturado')),
                    'tipo_factura': f.get('EsFacturado'),
                    'inicio_pauta': f.get('Inicio_x0020_de_x0020_la_x0020_P'),
                    'fin_pauta': f.get('Fin_x0020_de_x0020_la_x0020_Paut'),
                    'es_canje': bool(f.get('EsCanjelaPublicidad')),
                    'venta_combo': bool(f.get('Venta_x0020_COMBO'))
                }, on_conflict="op").execute()
            except Exception as e:
                print(f"     ⚠️ Error al actualizar maestra OP {op_num}: {e}")

        # --- B. HIJAS (Lógica: Borrar por OP y re-insertar actual) ---
        # 1. TV
        supabase.table("tv").delete().eq('op_numero', op_num).execute()
        res_tv = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/TV/items?expand=fields&$filter=fields/OP_TP eq '{op_num}'", headers=headers).json().get('value', [])
        data_tv = [{
            'op_id': smart_find_op_id(op_num, db_maps),
            'op_numero': op_num,
            'programa_id': parse_int(f['fields'].get('ProgramasLookupId')),
            'programa_nombre': programas_map.get(parse_int(f['fields'].get('ProgramasLookupId'))) or str(f['fields'].get('Programa') or ''),
            'tipo': f['fields'].get('TipodePublicidad'),
            'importe_total': parse_num(f['fields'].get('ImporteTotal')),
            'iva': parse_num(f['fields'].get('IVA')),
            'importe_sin_iva': parse_num(f['fields'].get('ImporteSinSIVA')),
            'segundos': parse_int(f['fields'].get('SegundosdeTV')),
            'valor_segundo': parse_num(f['fields'].get('Valor_x0020_del_x0020_Segundo'))
        } for f in res_tv]
        if data_tv: supabase.table("tv").insert(data_tv).execute()

        # 2. UN
        supabase.table("unidades_negocio").delete().eq('op_numero', op_num).execute()
        res_un = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Unidad de Negocio/items?expand=fields&$filter=fields/OP_UNN eq '{op_num}'", headers=headers).json().get('value', [])
        data_un = [{
            'op_id': smart_find_op_id(op_num, db_maps),
            'op_numero': op_num,
            'unidad_negocio': str(f['fields'].get('Unidaddenegocio0') or '').strip(),
            'importe_total': parse_num(f['fields'].get('ImporteTotal')),
            'iva': str(f['fields'].get('IVA0') or '0').replace('IVA ', '').replace(',', '.').strip(),
            'importe_sin_iva': parse_num(f['fields'].get('ImportesinIVA')),
            'fecha_creacion': f['fields'].get('fecha_creacion_UN')
        } for f in res_un]
        if data_un: supabase.table("unidades_negocio").insert(data_un).execute()

        # 3. PAGOS
        supabase.table("pagos").delete().eq('op_numero', op_num).execute()
        res_p = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?expand=fields&$filter=fields/OP eq '{op_num}'", headers=headers).json().get('value', [])
        data_p = [{
            'op_id': smart_find_op_id(op_num, db_maps),
            'op_numero': op_num,
            'fecha_pago': f['fields'].get('FechadePago').split('T')[0] if f['fields'].get('FechadePago') else None,
            'importe_pago': parse_num(f['fields'].get('ImportePago')),
            'recibo_numero': str(f['fields'].get('ReciboNumero') or f['fields'].get('Recibo') or '').strip()
        } for f in res_p]
        if data_p: supabase.table("pagos").insert(data_p).execute()

    print(f"✨ [DONE] OP {op_num} sincronizada al 100%.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--hours', type=int, default=24, help='Horas hacia atrás para sincronizar (def: 24)')
    args = parser.parse_args()
    
    run_incremental_sync(hours=args.hours)
