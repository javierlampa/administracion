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
        # Reemplazar coma por punto si viene como string
        if isinstance(val, str):
            val = val.replace(',', '.')
        return float(val)
    except: return 0.0

def parse_int(val):
    if val is None or val == "": return 0
    try: return int(float(val))
    except: return 0

def get_items_incremental(base_url, headers):
    all_items = []
    next_url = base_url
    while next_url:
        res = requests.get(next_url, headers=headers).json()
        if 'value' in res: all_items.extend(res['value'])
        next_url = res.get('@odata.nextLink')
    return all_items

def get_global_ops_map():
    all_data = []
    step = 1000
    for i in range(0, 50000, step):
        res = supabase.table("ordenes_publicidad").select("id, op").range(i, i + step - 1).execute()
        if not res.data: break
        all_data.extend(res.data)
    
    op_to_id = {str(r['op']).strip(): r['id'] for r in all_data if r['op']}
    id_to_op = {r['id']: str(r['op']).strip() for r in all_data if r['op']}
    return op_to_id, id_to_op

def smart_find_op_id(sp_op_value, maps):
    op_to_id, _ = maps
    val_str = str(sp_op_value or '').strip()
    if val_str in op_to_id: return op_to_id[val_str]
    return None

def run_mirror_sync():
    print(f"\n🚀 [MIRROR SYNC] Iniciando... {datetime.now().strftime('%H:%M:%S')}")
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    # 1. Obtener ID del sitio
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    if not res_site.get('value'): raise Exception("No se encontró el sitio de SharePoint")
    site_id = res_site['value'][0]['id']
    
    # 2. Catálogos (Mirror)
    print("  -> Sincronizando Catálogos...")
    def sync_cat(sp_list, table, mapper):
        items = get_items_incremental(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{sp_list}/items?expand=fields", headers)
        data = [mapper(i['fields']) for i in items if i['fields'].get('id')]
        if data:
            for i in range(0, len(data), 100):
                supabase.table(table).upsert(data[i:i+100]).execute()
        return {parse_int(i['fields'].get('id')): i['fields'] for i in items}

    prog_raw = sync_cat("Programas", "programas", lambda f: {'id': parse_int(f.get('id')), 'title': f.get('Title')})
    programas_map = {k: v.get('Title') for k, v in prog_raw.items()}

    vend_raw = sync_cat("Vendedores", "vendedores", lambda f: {'id': parse_int(f.get('id')), 'nombre': f"{f.get('Nombre_Vendedor', '')} {f.get('Apellido', '')}".strip() or f.get('Title')})
    vendedores_map = {k: f"{v.get('Nombre_Vendedor', '')} {v.get('Apellido', '')}".strip() or v.get('Title') for k, v in vend_raw.items()}

    clie_raw = sync_cat("Clientes_1", "clientes", lambda f: {'id': parse_int(f.get('id')), 'nombre': f.get('Nombre_x0020_Comercial') or f.get('Razon_x0020_Social') or f.get('Title')})
    clientes_map = {k: v.get('Nombre_x0020_Comercial') or v.get('Razon_x0020_Social') or v.get('Title') for k, v in clie_raw.items()}

    # 3. Ordenes de Publicidad (MAESTRA)
    print("  -> Sincronizando Ordenes de Publicidad (MAESTRA)...")
    sp_ops = get_items_incremental(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items?expand=fields", headers)
    op_ids_sp = []
    ops_to_upsert = []
    
    for i in sp_ops:
        f = i['fields']
        op_num = str(f.get('OP')).strip() if f.get('OP') else None
        if not op_num: continue # Si no hay OP real, la salteamos
        
        op_ids_sp.append(op_num)
        ops_to_upsert.append({
            'op': op_num,
            'importe_total': parse_num(f.get('Total')), 
            'fecha_orden': f.get('Fecha_x0020_de_x0020_la_x0020_Or'),
            'cliente_nombre': clientes_map.get(parse_int(f.get('Nombre_x0020_del_x0020_ComercioLookupId'))),
            'vendedor_nombre': vendedores_map.get(parse_int(f.get('VendedorLookupId'))),
            'programa_nombre': f.get('Programa') or f.get('Programas') or f.get('Title'),
            'empresa': str(f.get('Empresa') or ''), 'numero_factura': f.get('UnidaddeNegocio2'),
            'esta_facturado': bool(f.get('EstaFacturado')), 'tipo_factura': f.get('EsFacturado'),
            'inicio_pauta': f.get('Inicio_x0020_de_x0020_la_x0020_P'), 'fin_pauta': f.get('Fin_x0020_de_x0020_la_x0020_Paut'),
            'es_canje': bool(f.get('EsCanjelaPublicidad')), 'venta_combo': bool(f.get('Venta_x0020_COMBO'))
        })

    if ops_to_upsert:
        print(f"  -> Procesando {len(ops_to_upsert)} órdenes...")
        # LÓGICA HIBRIDA: Bloques de 100, si falla, uno por uno
        for i in range(0, len(ops_to_upsert), 100):
            chunk = ops_to_upsert[i:i + 100]
            try:
                supabase.table("ordenes_publicidad").upsert(chunk, on_conflict="op").execute()
            except Exception:
                # Fallback quirúrgico para este bloque
                for item in chunk:
                    try:
                        supabase.table("ordenes_publicidad").upsert(item, on_conflict="op").execute()
                    except Exception as e:
                        print(f"     ⚠️ Error persistente en OP {item.get('op')}: {e}")

    # Limpieza: Borrar de la DB lo que ya NO está en SharePoint (basado en OP)
    res_db = supabase.table("ordenes_publicidad").select("op").execute()
    ops_db = [str(r['op']).strip() for r in res_db.data]
    to_del = list(set(ops_db) - set(op_ids_sp))
    if to_del:
        print(f"     🧹 Borrando {len(to_del)} órdenes obsoletas...")
        for i in range(0, len(to_del), 100):
            supabase.table("ordenes_publicidad").delete().in_("op", to_del[i:i+100]).execute()

    # Mapa de OPs actualizado
    db_maps = get_global_ops_map()

    # 4. Tablas Relacionadas (Modo Espejo Total: Limpiar e Insertar)
    rel_config = [
        ("TV", "tv", lambda f: {
            'op_id': smart_find_op_id(f.get('OP_TP'), db_maps),
            'op_numero': str(f.get('OP_TP') or '').strip(),
            'programa_id': parse_int(f.get('ProgramasLookupId')) or None,
            'programa_nombre': programas_map.get(parse_int(f.get('ProgramasLookupId'))) or str(f.get('Programa') or f.get('Title') or ''),
            'tipo': f.get('TipodePublicidad'), 
            'importe_total': parse_num(f.get('ImporteTotal')),
            'iva': parse_num(f.get('IVA')),
            'importe_sin_iva': parse_num(f.get('ImporteSinSIVA')),
            'segundos': parse_int(f.get('SegundosdeTV')), 
            'valor_segundo': parse_num(f.get('Valor_x0020_del_x0020_Segundo'))
        }),
        ("Unidad de Negocio", "unidades_negocio", lambda f: {
            'op_id': smart_find_op_id(f.get('OP_UNN'), db_maps),
            'op_numero': str(f.get('OP_UNN') or '').strip(),
            'unidad_negocio': str(f.get('Unidaddenegocio0') or '').strip(),
            'importe_total': parse_num(f.get('ImporteTotal')),
            'iva': str(f.get('IVA0') or '0').replace('IVA ', '').replace(',', '.').strip(),
            'importe_sin_iva': parse_num(f.get('ImportesinIVA')),
            'fecha_creacion': f.get('fecha_creacion_UN')
        }),
        ("Pagos", "pagos", lambda f: {
            'op_id': smart_find_op_id(str(f.get('OP')).strip() if f.get('OP') else str(parse_int(f.get('OPLookupId')) or '').strip(), db_maps),
            'op_numero': str(f.get('OP')).strip() if f.get('OP') else str(parse_int(f.get('OPLookupId')) or '').strip(),
            'fecha_pago': f.get('FechadePago').split('T')[0] if f.get('FechadePago') else None,
            'importe_pago': parse_num(f.get('ImportePago')), 'recibo_numero': str(f.get('ReciboNumero') or f.get('Recibo') or '').strip()
        })
    ]

    for sp_list, pg_table, mapper in rel_config:
        print(f"  -> Sincronizando {pg_table} (Espejo Total)...")
        # 1. Obtener todo de SharePoint
        items = get_items_incremental(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{sp_list}/items?expand=fields", headers)
        
        # Procesar y deduplicar por ID interno de SharePoint
        data = []
        seen_sp_ids = set()
        for i in items:
            f = i['fields']
            sp_id = f.get('id')
            mapped = mapper(f)
            
            if not mapped.get('op_numero'): continue
            
            # Debug para OP 6933
            if mapped.get('op_numero') == '6933':
                print(f"     [DEBUG 6933] Encontrado SP_ID: {sp_id}")

            if sp_id not in seen_sp_ids:
                seen_sp_ids.add(sp_id)
                data.append(mapped)
                
        print(f"     ✅ {len(data)} registros únicos (según SP ID) a insertar en {pg_table}.")
        
        if data:
            # 2. Borrar TODO en Supabase (Limpieza absoluta por lotes)
            print("     🧹 Limpiando tabla antes de insertar...")
            while True:
                res_ids = supabase.table(pg_table).select('id').limit(1000).execute()
                if not res_ids.data: 
                    break
                ids_to_del = [r['id'] for r in res_ids.data]
                supabase.table(pg_table).delete().in_('id', ids_to_del).execute()
            
            # 3. Insertar TODO de nuevo
            for i in range(0, len(data), 100):
                supabase.table(pg_table).insert(data[i:i+100]).execute()

    print(f"\n🏆 [FIN] Espejo completado.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--one-shot', action='store_true')
    args = parser.parse_args()
    while True:
        try: run_mirror_sync()
        except Exception as e: print(f"❌ Error: {e}")
        if args.one_shot: break
        time.sleep(3600)
