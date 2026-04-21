import os, requests
from dotenv import load_dotenv
from supabase import create_client
from sharepoint_sync import get_token, get_items_incremental, parse_int

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
token = get_token()
headers = {'Authorization': f'Bearer {token}'}
SITE_NAME_SEARCH = "Sistema de Ventas"
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

def get_diagnostico(sp_list, db_table, sp_op_field, key_fields_db):
    print(f"\n🔍 Analizando {sp_list}...")
    
    # 1. Obtener de Supabase (Lo que sí pasó) con paginación
    db_keys = set()
    offset = 0
    batch_size = 1000
    sel = "op_numero, programa_nombre, tipo" if db_table == "tv" else "op_numero, unidad_negocio"
    
    while True:
        res = supabase.table(db_table).select(sel).range(offset, offset + batch_size - 1).execute()
        if not res.data:
            break
        for r in res.data:
            if db_table == "tv":
                op_db = str(r.get('op_numero') or '').strip()
                pr_db = str(r.get('programa_nombre') or '').strip()
                tp_db = str(r.get('tipo') or '').strip()
                db_keys.add( (op_db, pr_db, tp_db) )
            else:
                op_db = str(r.get('op_numero') or '').strip()
                un_db = str(r.get('unidad_negocio') or '').strip()
                db_keys.add( (op_db, un_db) )
        if len(res.data) < batch_size:
            break
        offset += batch_size
    
    # 2. Obtener de SharePoint (El origen)
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{sp_list}/items?expand=fields&$top=999"
    items_sp = get_items_incremental(url, headers)
    
    excluidos = []
    vistos_en_sp = set() # Para detectar duplicados dentro del mismo SP

    # Pre-cargar programas para comparar peras con peras
    prog_raw = get_items_incremental(f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/Programas/items?expand=fields", headers)
    prog_map = {parse_int(i['fields'].get('id')): i['fields'].get('Title') for i in prog_raw}

    for i in items_sp:
        f = i['fields']
        op = str(f.get(sp_op_field) or '').strip()
        fecha = f.get('Created', 'Desconocida')[:10]
        
        if not op:
            excluidos.append({"op": "(VACÍA)", "fecha": fecha, "motivo": "Sin OP en SharePoint", "extra": f"ID SharePoint: {f.get('id')}"})
            continue
            
        if db_table == "tv":
            # Usar la misma lógica que el mapper original
            p_id = parse_int(f.get('ProgramasLookupId'))
            programa = str(prog_map.get(p_id) or f.get('Programa') or f.get('Title') or '').strip()
            tipo = str(f.get('TipodePublicidad') or '').strip()
            key = (op, programa, tipo)
            info_extra = f"Prog: {programa} | Tipo: {tipo}"
        else:
            un = str(f.get('Unidaddenegocio0') or '').strip()
            key = (op, un)
            info_extra = f"Unidad: {un}"

        if key in vistos_en_sp:
            excluidos.append({"op": op, "fecha": fecha, "motivo": "REGISTRO DUPLICADO", "extra": info_extra})
        else:
            vistos_en_sp.add(key)
            if key not in db_keys:
                 excluidos.append({"op": op, "fecha": fecha, "motivo": "FALTANTE REAL", "extra": info_extra})

    return excluidos

# Generar reporte
repo_tv = get_diagnostico("TV", "tv", "OP_TP", ["op_numero", "programa_nombre", "tipo"])
repo_un = get_diagnostico("Unidad de Negocio", "unidades_negocio", "OP_UNN", ["op_numero", "unidad_negocio"])

with open("DOCS/reporte_excluidos_detalle.txt", "w", encoding="utf-8") as f:
    f.write("REPORTE DETALLADO DE REGISTROS QUE NO PASARON (ESPEJO)\n")
    f.write("====================================================\n\n")
    
    f.write(f"--- TABLA TV ({len(repo_tv)} excluidos) ---\n")
    for e in repo_tv:
        f.write(f"OP: {e['op']} | Fecha: {e['fecha']} | Motivo: {e['motivo']} | Detalle: {e['extra']}\n")
    
    f.write(f"\n--- TABLA UNIDADES DE NEGOCIO ({len(repo_un)} excluidos) ---\n")
    for e in repo_un:
        f.write(f"OP: {e['op']} | Fecha: {e['fecha']} | Motivo: {e['motivo']} | Detalle: {e['extra']}\n")

print(f"\n✅ Reporte generado en DOCS/reporte_excluidos_detalle.txt")
