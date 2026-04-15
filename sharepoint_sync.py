import os
import requests
import msal
import time
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta

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
    if isinstance(val, (int, float)): return float(val)
    s_val = str(val).strip().replace(',', '.')
    try: return float(s_val)
    except: return 0.0

def get_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=auth_url, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return result["access_token"]

def get_items_incremental(url, headers, modified_since=None):
    all_items = []
    # SharePoint Graph API filter for modified date
    # Note: Using fields/Modified requires Prefer: HonorNonIndexedQueriesWarningMayFail if column is not indexed
    # but for typical lists it works with expand=fields
    if modified_since:
        url += f"&$filter=fields/Modified ge '{modified_since}'"
    
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
    # Siempre cargamos el mapa para poder vincular hijos nuevos a padres existentes
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

def run_incremental_sync(hours_back=3):
    # Calculamos el timestamp para la sincronización incremental
    # Usamos una ventana de 'hours_back' para asegurar que capturamos cambios recientes inclusive si hubo un fallo corto
    last_sync_utc = (datetime.utcnow() - timedelta(hours=hours_back)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"\n🚀 [INCREMENTAL SYNC] Iniciando... {datetime.now().strftime('%H:%M:%S')}")
    print(f"  -> Buscando cambios desde: {last_sync_utc}")
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    # Obtenemos el ID del sitio
    res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
    site_id = res_site['value'][0]['id']
    
    last_sync_str = last_sync_utc

    # 2. Cargar catálogos (siempre necesarios para nombres)
    # Estos son pequeños, no pasa nada si se cargan completos
    print("  -> Refrescando catálogos...")
    prog_raw = get_items_incremental(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Programas/items?expand=fields", headers)
    programas_map = {parse_int(i['fields'].get('id')): i['fields'].get('Title') for i in prog_raw}
    
    vend_raw = get_items_incremental(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Vendedores/items?expand=fields", headers)
    vendedores_map = {parse_int(i['fields'].get('id')): f"{i['fields'].get('Nombre_Vendedor', '')} {i['fields'].get('Apellido', '')}".strip() or i['fields'].get('Title') for i in vend_raw}

    clie_raw = get_items_incremental(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Clientes_1/items?expand=fields", headers)
    clientes_map = {parse_int(i['fields'].get('id')): i['fields'].get('Nombre_x0020_Comercial') or i['fields'].get('Razon_x0020_Social') or i['fields'].get('Title') for i in clie_raw}

    # 3. Sincronizar Ordenes (Maestra)
    print("  -> Sincronizando Ordenes de Publicidad...")
    url_ops = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items?expand=fields&$top=999"
    items_ops = get_items_incremental(url_ops, headers, last_sync_str)
    
    if items_ops:
        ops_data = []
        for i in items_ops:
            f = i['fields']
            ops_data.append({
                'id': parse_int(f.get('id')), 
                'op': str(f.get('OP')).strip() if f.get('OP') and str(f.get('OP')).strip() != '' else f"S/N-{f.get('id')}",
                'importe_total': parse_num(f.get('Total')), 
                'fecha_orden': f.get('Fecha_x0020_de_x0020_la_x0020_Or'),
                'cliente_id': parse_int(f.get('Nombre_x0020_del_x0020_ComercioLookupId')),
                'cliente_nombre': clientes_map.get(parse_int(f.get('Nombre_x0020_del_x0020_ComercioLookupId'))),
                'vendedor_id': parse_int(f.get('VendedorLookupId')),
                'vendedor_nombre': vendedores_map.get(parse_int(f.get('VendedorLookupId'))),
                'programa_nombre': f.get('Programa') or f.get('Programas') or f.get('Title'),
                'empresa': str(f.get('Empresa') or ''), 
                'numero_factura': f.get('UnidaddeNegocio2'),
                'esta_facturado': bool(f.get('EstaFacturado')), 
                'tipo_factura': f.get('EsFacturado'),
                'inicio_pauta': f.get('Inicio_x0020_de_x0020_la_x0020_P'), 
                'fin_pauta': f.get('Fin_x0020_de_x0020_la_x0020_Paut'),
                'clasificacion': f.get('ClasificacionClientes'),
                'medidas_digital': f.get('MedidasDigital'),
                'es_canje': bool(f.get('EsCanjelaPublicidad'))
            })
        for i in range(0, len(ops_data), 100):
            supabase.table("ordenes_publicidad").upsert(ops_data[i:i+100]).execute()
        print(f"     ✅ {len(ops_data)} órdenes actualizadas.")
    else:
        print("     ✅ Sin cambios en órdenes.")

    # Recargamos mapa de OPs por si hubo nuevas
    db_maps = get_global_ops_map()

    # 4. Sincronizar Relacionados (TV, UN, Pagos)
    rel_config = [
        ("TV", "tv", lambda f: {
            'id': parse_int(f.get('id')),
            'op_id': smart_find_op_id(f.get('OP_TP'), db_maps),
            'op_numero': str(f.get('OP_TP') or '').strip(),
            'programa_id': parse_int(f.get('ProgramasLookupId')),
            'programa_nombre': programas_map.get(parse_int(f.get('ProgramasLookupId'))) or str(f.get('Programa') or f.get('Title') or ''),
            'tipo': f.get('TipodePublicidad'), 
            'importe_total': parse_num(f.get('ImporteTotal')),
            'segundos': parse_int(f.get('SegundosdeTV')),
            'valor_segundo': parse_num(f.get('Valor_x0020_del_x0020_Segundo')),
            'iva': parse_num(f.get('IVA')),
            'importe_sin_iva': parse_num(f.get('ImportesinIVA')),
            'created': f.get('Created'), 'modified': f.get('Modified')
        }),
        ("Unidad de Negocio", "unidades_negocio", lambda f: {
            'id': parse_int(f.get('id')), 
            'op_id': smart_find_op_id(f.get('OP_UNN'), db_maps),
            'op_numero': str(f.get('OP_UNN') or '').strip(),
            'unidad_negocio': f.get('Unidaddenegocio0'),
            'importe_total': parse_num(f.get('ImporteTotal')),
            'importe_sin_iva': parse_num(f.get('ImportesinIVA')),
            'iva': parse_num(f.get('IVA')),
            'created': f.get('Created'), 'modified': f.get('Modified')
        }),
        ("Pagos", "pagos", lambda f: {
            'id': parse_int(f.get('id')),
            'op_id': smart_find_op_id(f.get('OP'), db_maps) or smart_find_op_id(str(parse_int(f.get('OPLookupId')) or ''), db_maps),
            'op_numero': str(f.get('OP') or '').strip(),
            'fecha_pago': f.get('FechadePago').split('T')[0] if f.get('FechadePago') else None, 
            'importe_pago': parse_num(f.get('ImportePago')), 
            'recibo_numero': str(f.get('ReciboNumero') or f.get('Recibo') or '').strip(),
            'vendedor': f.get('Vendedor'), 'cliente': f.get('Cliente'),
            'saldo': parse_num(f.get('Saldo')),
            'medio_pago': f.get('MediodePago') or f.get('Medio_x0020_de_x0020_Pago'),
            'created': f.get('Created'), 'modified': f.get('Modified')
        })
    ]

    total_orphans = []
    for sp_list, pg_table, mapper in rel_config:
        print(f"  -> Sincronizando {pg_table}...", end="", flush=True)
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{sp_list}/items?expand=fields&$top=999"
        items = get_items_incremental(url, headers, last_sync_str)
        
        data_to_upsert = []
        if items:
            for i in items:
                f = i['fields']
                op_val = f.get('OP_TP') or f.get('OP_UNN') or f.get('OP') or f.get('OPLookupId')
                op_id = smart_find_op_id(op_val, db_maps)
                
                if op_id:
                    data_to_upsert.append(mapper(f))
                else:
                    total_orphans.append({
                        'lista': sp_list,
                        'sp_id': f.get('id'),
                        'op_no_encontrada': str(op_val).strip()
                    })

            if data_to_upsert:
                for j in range(0, len(data_to_upsert), 100):
                    supabase.table(pg_table).upsert(data_to_upsert[j:j+100]).execute()
                print(f" ✅ {len(data_to_upsert)} items.")
            else:
                print(" ✅ OK (Sin cambios o todo huérfano).")
        else:
            print(" ✅ OK (Sin cambios).")

    # Generar reporte de huérfanos si existen
    report_path = "DOCS/reporte_huerfanos.txt"
    if total_orphans:
        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write(f"REPORTE DE ITEMS HUÉRFANOS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            rf.write("="*60 + "\n")
            rf.write("Estos items se saltearon porque no se encontró su OP en la base de datos:\n\n")
            for o in total_orphans:
                rf.write(f"Lista: {o['lista']} | SP_ID: {o['sp_id']} | OP buscada: {o['op_no_encontrada']}\n")
        print(f"\n⚠️ Se encontraron {len(total_orphans)} huérfanos. Reporte generado en {report_path}")
    else:
        if os.path.exists(report_path):
            os.remove(report_path) # Limpiar reporte si ya no hay huérfanos
        print("\n✨ Limpio: No se encontraron huérfanos.")

    print(f"\n🏆 [FINALIZADO] Sincronización incremental exitosa. {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    while True:
        try:
            # Sincronizamos cambios de las últimas 12 horas por seguridad cada vez que corre
            run_incremental_sync(hours_back=12)
            print(f"\n🏆 [FINALIZADO] Sincronización exitosa. Próxima ejecución en 1 hora.")
        except Exception as e:
            print(f"\n❌ [ERROR] Falló la sincronización: {e}")
            print("  -> Reintentando en 1 hora...")
        
        # Esperar 1 hora
        time.sleep(3600)
