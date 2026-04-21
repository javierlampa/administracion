import os, requests, time
from dotenv import load_dotenv
from supabase import create_client
from sharepoint_sync import get_token, get_items_incremental, parse_int, parse_num, smart_find_op_id, get_global_ops_map

load_dotenv()

# Configuración de clientes
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
token = get_token()
headers = {'Authorization': f'Bearer {token}'}
SITE_NAME_SEARCH = "Sistema de Ventas"
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

print("=========================================================")
print("  INICIANDO ESPEJADO TOTAL: TV y UNIDADES DE NEGOCIO")
print("=========================================================\n")

# 1. Cargar catálogos
print("🔄 Cargando catálogos...")
prog_raw = get_items_incremental(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Programas/items?expand=fields", headers)
programas_map = {parse_int(i['fields'].get('id')): i['fields'].get('Title') for i in prog_raw}
db_maps = get_global_ops_map()

total_errors = []
total_success = []

def truncate_and_fill(sp_list, pg_table, sp_op_field, mapper):
    print(f"\n🗑️  Borrando todos los registros de la tabla {pg_table}...")
    try:
        supabase.table(pg_table).delete().neq("id", 0).execute()
        print(f"✅ Tabla {pg_table} vaciada con éxito.")
    except Exception as e:
        print(f"⚠️ Error al intentar vaciar la tabla: {e}")
        pass

    print(f"🔄 Descargando TODOS los registros de {sp_list} desde SharePoint...")
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{sp_list}/items?expand=fields&$top=999"
    items = get_items_incremental(url, headers)
    
    if not items:
        print("⚠️ No se encontraron elementos en SharePoint para esta tabla.")
        return

    print(f"  -> Encontrados {len(items)} registros. Insertando en Supabase en bloques limpios...")
    
    count_success = 0
    ops_data = []

    for i in items:
        f = i['fields']
        op_val = str(f.get(sp_op_field) or '').strip()
        # Fallback al LookupId en caso de que vacio (por las dudas)
        if not op_val and f.get(f"{sp_op_field}LookupId"):
            op_val = str(f.get(f"{sp_op_field}LookupId")).strip()

        if not op_val:
            total_errors.append({
                'lista': pg_table.upper(), 'sp_id': f.get('id'),
                'op': '(vacío)', 'motivo': f"Campo {sp_op_field} vacío en SharePoint"
            })
            continue

        try:
            ops_data.append(mapper(f, op_val))
        except Exception as e:
            total_errors.append({
                'lista': pg_table.upper(), 'sp_id': f.get('id'),
                'op': op_val, 'motivo': f"Error al parsear fila: {str(e)}"
            })
    # --- GESTIÓN DE DUPLICADOS DIFERENCIAL ---
    if pg_table == "unidades_negocio":
        # Usamos op_numero + unidad para detectar duplicados REALES (misma OP cargada 2 veces)
        # No usamos op_id porque si son huérfanas (op_id=None), se pisarían entre ellas.
        unique_keys = set()
        deduped_data = []
        for item in ops_data:
            # Clave de duplicados basada en el TEXTO de la OP, no en el ID
            key = (item.get("op_numero"), item.get("unidad_negocio"))
            
            if key not in unique_keys:
                unique_keys.add(key)
                deduped_data.append(item)
            else:
                total_errors.append({
                    'lista': pg_table.upper(), 'sp_id': item.get('sp_id_raw'),
                    'op': item.get('op_numero'), 'motivo': "DUPLICADO EN SHAREPOINT (Ya existe este renglón)"
                })
        ops_data = deduped_data
    # Para TV, pasan todos 1:1

    # Antes de insertar, identificar HUÉRFANOS para el reporte final
    for item in ops_data:
        if item.get("op_id") is None:
            total_errors.append({
                'lista': pg_table.upper(), 'sp_id': item.get('sp_id_raw'),
                'op': item.get('op_numero'), 'motivo': "HUÉRFANA (No existe en Orden de Publicidad Maestra)"
            })
            # Nota: El registro se intentará insertar igual si la DB lo permite (op_id nullable),
            # o fallará en el bloque lento si es NOT NULL.
    
    # Inserción SUPERSÓNICA en bloques (Chunks)
    count_success = 0
    chunk_size = 500
    for i in range(0, len(ops_data), chunk_size):
        chunk = ops_data[i:i+chunk_size]
        # Limpiar campo temporal antes de insertar en DB
        for item in chunk:
            if 'sp_id_raw' in item: del item['sp_id_raw']
            
        try:
            supabase.table(pg_table).insert(chunk).execute()
            count_success += len(chunk)
            print(f"     -> Subidos {count_success} de {len(ops_data)}...")
        except Exception as e:
            print(f"⚠️ Error bloque, insertando lento el bloque: {str(e)[:50]}")
            for item in chunk:
                try:
                    supabase.table(pg_table).insert(item).execute()
                    count_success += 1
                except Exception as ex:
                    total_errors.append({
                        'lista': pg_table.upper(), 'sp_id': '',
                        'op': item.get('op_numero', 'N/A'), 'motivo': f"ERROR DB: {str(ex)}"
                    })

    print(f"     ✅ {count_success} registros espejados en {pg_table}. (Ver {len(items) - count_success} excluidos en reporte)")

# TV Mapper
def mapper_tv(f, op_val):
    return {
        'sp_id_raw':       f.get('id'), # Para log
        'op_id':           smart_find_op_id(op_val, db_maps),
        'op_numero':       op_val,
        'programa_id':     parse_int(f.get('ProgramasLookupId')),
        'programa_nombre': programas_map.get(parse_int(f.get('ProgramasLookupId'))) or str(f.get('Programa') or f.get('Title') or ''),
        'tipo':            f.get('TipodePublicidad'),
        'importe_total':   parse_num(f.get('ImporteTotal')),
        'segundos':        parse_int(f.get('SegundosdeTV')),
        'valor_segundo':   parse_num(f.get('Valor_x0020_del_x0020_Segundo')),
        'iva':             parse_num(f.get('IVA')),
        'importe_sin_iva': parse_num(f.get('ImportesinIVA')),
        'created':         f.get('Created'),
        'modified':        f.get('Modified')
    }

# UNIDADES Mapper
def mapper_unn(f, op_val):
    return {
        'sp_id_raw':      f.get('id'), # Para log
        'op_id':          smart_find_op_id(op_val, db_maps),
        'op_numero':      op_val,
        'unidad_negocio': f.get('Unidaddenegocio0'),
        'importe_total':  parse_num(f.get('ImporteTotal')),
        'importe_sin_iva':parse_num(f.get('ImportesinIVA')),
        'iva':            parse_num(f.get('IVA')),
        'created':        f.get('Created'),
        'modified':       f.get('Modified')
    }

# Ejecutar proceso para AMBAS tablas para asegurar integridad total 1:1
truncate_and_fill("TV", "tv", "OP_TP", mapper_tv)
truncate_and_fill("Unidad de Negocio", "unidades_negocio", "OP_UNN", mapper_unn)

# Guardar reportes
with open("DOCS/espejado_errores_resto.txt", "w", encoding="utf-8") as fe:
    fe.write(f"REPORTE DE ERRORES/EXCLUIDOS - ESPEJADO TOTAL\n")
    fe.write("="*65 + "\n")
    for e in total_errors:
        fe.write(f"Lista : {e['lista']} | OP: {e['op']} | SP_ID: {e['sp_id']} | ERROR: {e['motivo']}\n")

print(f"\n📂 Finalizado. Ver DOCS/espejado_errores_resto.txt para items salteados por falta de OP")
