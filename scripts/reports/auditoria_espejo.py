import os, requests
from collections import defaultdict
from sharepoint_sync import get_token, get_items_incremental
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
token = get_token()
headers = {'Authorization': f'Bearer {token}'}
SITE_NAME_SEARCH = "Sistema de Ventas"
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def fetch_all_supabase(table, column):
    all_rows = []
    offset = 0
    while True:
        res = supabase.table(table).select(column).range(offset, offset + 999).execute()
        if not res.data:  break
        all_rows.extend(res.data)
        if len(res.data) < 1000: break
        offset += 1000
    return all_rows

config = [
    {"name": "Ordenes_Maestras", "sp_list": "Orden de Publicidad", "db_table": "ordenes_publicidad", "sp_col": "OP", "db_col": "op"},
    {"name": "Pagos", "sp_list": "Pagos", "db_table": "pagos", "sp_col": "OP", "db_col": "op_numero"},
    {"name": "TV", "sp_list": "TV", "db_table": "tv", "sp_col": "OP_TP", "db_col": "op_numero"},
    {"name": "Unidades_Negocio", "sp_list": "Unidad de Negocio", "db_table": "unidades_negocio", "sp_col": "OP_UNN", "db_col": "op_numero"},
]

report_lines = []
report_lines.append("========================================================")
report_lines.append("      REPORTE DE AUDITORÍA TOTAL: SHAREPOINT VS SUPABASE      ")
report_lines.append("========================================================\n")

print("🔍 Iniciando Auditoría profunda para TODAS las tablas...")

for c in config:
    print(f"\n  -> Procesando tabla: {c['name']}...")
    
    # SHAREPOINT
    url_sp = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{c['sp_list']}/items?expand=fields($select={c['sp_col']},{c['sp_col']}LookupId)&$top=999"
    items_sp = get_items_incremental(url_sp, headers)
    sp_counts = defaultdict(int)
    for item in items_sp:
        f = item['fields']
        # Extract OP carefully matching sharepoint_sync logic
        val = f.get(c['sp_col']) or f.get(c['sp_col']+"LookupId")
        if val:
            op_str = str(val).replace('.0','').strip()
            sp_counts[op_str] += 1

    total_sp = sum(sp_counts.values())
    print(f"     ✅ {total_sp} registros leídos en SharePoint.")

    # SUPABASE
    db_rows = fetch_all_supabase(c['db_table'], c['db_col'])
    db_counts = defaultdict(int)
    for r in db_rows:
        val = r.get(c['db_col'])
        if val:
            op_str = str(val).strip()
            db_counts[op_str] += 1
            
    total_db = sum(db_counts.values())
    print(f"     ✅ {total_db} registros leídos en Supabase.")

    # COMPARACION
    todas_ops = set(sp_counts.keys()).union(set(db_counts.keys()))
    diferencias = []
    
    for op in sorted(list(todas_ops)):
        cant_sp = sp_counts[op]
        cant_db = db_counts[op]
        if cant_sp != cant_db:
            diferencias.append((op, cant_sp, cant_db))

    report_lines.append(f"📊 Módulo: {c['name'].upper()}")
    report_lines.append(f"  • Total bruto en SharePoint: {total_sp} registros.")
    report_lines.append(f"  • Total bruto en Supabase  : {total_db} registros.")
    
    if len(diferencias) == 0:
        report_lines.append("  ✅ RESULTADO: ESPEJO PERFECTO (0 diferencias)\n")
    else:
        report_lines.append(f"  ⚠️ RESULTADO: Se encontraron discrepancias en {len(diferencias)} OPs distintas:")
        for (op, sp_c, db_c) in diferencias:
            if db_c == 0:
                report_lines.append(f"      - OP {op}: Está en SharePoint ({sp_c} items) pero NO está en Supabase.")
            elif sp_c == 0:
                report_lines.append(f"      - OP {op}: Está en Supabase ({db_c} items) pero NO está en SharePoint (Huérfano).")
            else:
                report_lines.append(f"      - OP {op}: Cantidad distinta -> SP tiene {sp_c}, DB tiene {db_c}.")
        report_lines.append("\n")

report_path = "DOCS/auditoria_diferencias.txt"
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

print(f"\n🏆 Auditoría finalizada en todas las tablas. Revisa {report_path}")
