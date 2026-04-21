"""
Script para sincronizar la tabla pagos como un ESPEJO de SharePoint (Modo Upsert).
Uso: python limpiar_y_recargar_pagos.py
"""
import os, sys, requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Ahora sincronizamos todos los pagos desde el inicio usando el modo Espejo (Upsert por sp_id)
print("\n🔄 Iniciando Sincronización ESPEJO de Pagos desde SharePoint...")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importamos las funciones del sync principal
from sharepoint_sync import get_token, get_items_incremental, get_global_ops_map, parse_int, parse_num, smart_find_op_id, smart_find_op_numero
SITE_NAME_SEARCH = os.getenv("SP_SITE_NAME", "Sistema de Ventas")
token = get_token()
headers = {'Authorization': f'Bearer {token}'}
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

print("  -> Descargando Pagos de SharePoint...")
url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Pagos/items?expand=fields&$top=999"
items = get_items_incremental(url, headers)  # Sin filtro de fecha = todos
print(f"     ✅ {len(items)} pagos descargados de SharePoint.")

print("  -> Descargando mapa de Órdenes directamente desde SharePoint (para resolución de Lookups)...")
# Descargamos el mapa DIRECTAMENTE de SharePoint, no de Supabase.
# Esto garantiza que incluso OPs nuevas del mismo día puedan resolverse correctamente.
op_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Orden de Publicidad/items?expand=fields&$select=id,fields&$top=999"
op_items_raw = get_items_incremental(op_url, headers)
# Construimos el mapa: {sp_id_orden -> op_numero_texto} y {op_numero_texto -> sp_id_orden}
sp_op_map_id_to_text = {}
sp_op_map_text_to_id = {}
for oi in op_items_raw:
    of = oi.get('fields', {})
    sp_id_op = parse_int(of.get('id'))
    op_text = str(of.get('OP') or of.get('N_x00ba__x0020_Orden_x0020_de_') or '').strip()
    if sp_id_op and op_text:
        sp_op_map_id_to_text[sp_id_op] = op_text
        sp_op_map_text_to_id[op_text] = sp_id_op
print(f"     ✅ {len(sp_op_map_id_to_text)} Órdenes cargadas desde SharePoint. Iniciando Sincronización Espejo...")

total_success = []
total_errors = []
all_pagos = []

for i in items:
    f = i['fields']
    # ID de SharePoint (Este es EL ID del ítem en la lista)
    sp_id = parse_int(f.get('id'))
    
    op_val = str(f.get('OP') or '').strip()
    if not op_val:
        # El campo OP es un Lookup. Intentamos resolver el ID al texto usando el mapa de SharePoint.
        lookup_id = parse_int(f.get('OPLookupId'))
        if lookup_id and lookup_id in sp_op_map_id_to_text:
            op_val = sp_op_map_id_to_text[lookup_id]
        else:
            op_val = str(lookup_id or '').strip()

    # FILTRO CRÍTICO: Si no hay número de OP, este registro no sirve para comisiones (es basura o nota)
    if not op_val or op_val.lower() in ['none', 'nan', '']:
        continue

    # LÓGICA DE COMISIÓN (Espejo Estricto)
    com_pct = parse_num(f.get('comision') or f.get('Comision') or f.get('Comisi_x00f3_n'))
    com_imp = parse_num(f.get('Importe_x0020_Comision') or f.get('ImporteComision') or f.get('Importe_x0020_Comisi_x00f3_n'))
    
    # Si tenemos el importe directo de SP, lo usamos. 
    # Si el importe es 0 pero hay % de comisión, lo calculamos para mayor seguridad.
    pago_val = parse_num(f.get('ImportePago'))
    if com_imp == 0 and com_pct > 0 and pago_val > 0:
        com_imp = pago_val * (com_pct / 100)

    if op_val == "7191":
        print(f"DEBUG OP 7191: Pago={pago_val}, Com%={com_pct}, ComImp={com_imp}")

    all_pagos.append({
        'sp_id':         sp_id,
        'op_id':         sp_op_map_text_to_id.get(op_val),
        'op_numero':     op_val,
        'fecha_pago':    f.get('FechadePago').split('T')[0] if f.get('FechadePago') else None,
        'importe_pago':  pago_val,
        'recibo_numero': str(f.get('ReciboNumero') or f.get('Recibo') or '').strip(),
        'vendedor':      f.get('Vendedor'),
        'cliente':       f.get('Cliente'),
        'saldo':         parse_num(f.get('Saldo')),
        'medio_pago':    f.get('MediodePago') or f.get('Medio_x0020_de_x0020_Pago'),
        'total_sin_iva': parse_num(f.get('TotalSinIVA') or f.get('Total_x0020_sin_x0020_IVA') or f.get('ImportesinIVA') or f.get('TotalsinIVA') or f.get('Total_sin_IVA')),
        'iva':           parse_num(f.get('IVA') or f.get('iva') or f.get('Iva')),
        'comision':      com_pct,
        'importe_comision': com_imp,
        'esta_liquidado': bool(f.get('EstaLiquidado') or f.get('Liquidado')),
        'fecha_liquidacion': f.get('FechaLiquidacion').split('T')[0] if f.get('FechaLiquidacion') else None,
        'created':       f.get('Created'),
        'modified':      f.get('Modified'),
        'activo':        True
    })

# UPSERT en bloques de 200 (Modo Espejo)
chunk_size = 200
for idx in range(0, len(all_pagos), chunk_size):
    chunk = all_pagos[idx:idx+chunk_size]
    try:
        # Usamos upsert con on_conflict='sp_id' para que sea un espejo perfecto
        supabase.table("pagos").upsert(chunk, on_conflict='sp_id').execute()
        total_success.extend([{'lista': 'PAGOS', 'op': r['op_numero'], 'sp_id': r['sp_id']} for r in chunk])
        print(f"  -> Sincronizados {len(total_success)} de {len(all_pagos)}...")
    except Exception as e:
        # Si falla el bloque, de a uno para debug
        for data_item in chunk:
            try:
                supabase.table("pagos").upsert(data_item, on_conflict='sp_id').execute()
                total_success.append({'lista': 'PAGOS', 'op': data_item['op_numero'], 'sp_id': data_item['sp_id']})
            except Exception as e2:
                total_errors.append({'lista': 'PAGOS', 'sp_id': data_item['sp_id'], 'op': data_item['op_numero'], 'motivo': f"ERROR DB: {str(e2)}"})

print(f"\n✅ Sincronización Finalizada. Exitosos: {len(total_success)}, Errores: {len(total_errors)}")

# ELIMINACIÓN DE REGISTROS QUE YA NO EXISTEN O FUERON DESCARTADOS (ESPEJO REAL)
print("  -> Limpiando registros descartados o eliminados en SharePoint...")
# La lista de sp_id VÁLIDOS es la de los que acabamos de meter/actualizar
sp_ids_validos = [p['sp_id'] for p in all_pagos]

# Obtenemos todos los sp_id que tenemos en la DB usando paginación
sp_id_en_db = []
start = 0
while True:
    res_db = supabase.table('pagos').select('sp_id').range(start, start + 999).execute()
    if not res_db.data:
        break
    sp_id_en_db.extend([r['sp_id'] for r in res_db.data if r.get('sp_id')])
    if len(res_db.data) < 1000:
        break
    start += 1000
    
print(f"  -> Total registros detectados en DB: {len(sp_id_en_db)}")

ids_a_borrar = list(set(sp_id_en_db) - set(sp_ids_validos))

if ids_a_borrar:
    print(f"  -> Se encontraron {len(ids_a_borrar)} registros para purgar.")
    for i in range(0, len(ids_a_borrar), 200):
        batch = ids_a_borrar[i:i+200]
        supabase.table('pagos').delete().in_('sp_id', batch).execute()
    print(f"  ✅ Purga completada. Borrados {len(ids_a_borrar)} registros.")
else:
    print("  ✅ Todo limpio. No había registros para purgar.")

# Reportes
os.makedirs("DOCS", exist_ok=True)
with open("DOCS/sincronizacion_exitosa_pagos.txt", "w", encoding="utf-8") as fs:
    fs.write(f"REPORTE ESPEJO PAGOS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    for s in total_success[:100]: # Solo primeros 100 para no inflar el log
        fs.write(f"  • OP: {s['op']}  (SP_ID: {s['sp_id']})\n")

with open("DOCS/sincronizacion_errores_pagos.txt", "w", encoding="utf-8") as fe:
    fe.write(f"ERRORES EN ESPEJO PAGOS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    for e in total_errors:
        fe.write(f"OP: {e['op']} | SP_ID: {e['sp_id']} | Motivo: {e['motivo']}\n")

print(f"🕒 Finalizado: {datetime.now().strftime('%H:%M:%S')}")
