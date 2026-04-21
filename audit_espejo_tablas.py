"""
AUDITORÍA ESPEJO: Compara OP por OP entre SharePoint y Supabase para cada tabla.
Genera un reporte en DOCS/audit_espejo_<fecha>.txt

Tablas auditadas:
  SP: Orden de Publicidad  -> Supabase: ordenes_publicidad  (campo: OP / op)
  SP: Pagos                -> Supabase: pagos               (campo: OP / op_numero)
  SP: TV                   -> Supabase: tv                  (campo: OP_TP / op_numero)
  SP: Unidad de Negocio    -> Supabase: unidades_negocio    (campo: OP_UNN / op_numero)
"""
import os, requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from sharepoint_sync import get_token, get_items_incremental, parse_int

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
SITE_NAME_SEARCH = os.getenv("SP_SITE_NAME", "Sistema de Ventas")

token = get_token()
headers = {'Authorization': f'Bearer {token}'}
res_site = requests.get(f"https://graph.microsoft.com/v1.0/sites?search={SITE_NAME_SEARCH}", headers=headers).json()
site_id = res_site['value'][0]['id']

def get_sp_ops(list_name, op_field, fallback_lookup_field=None):
    """Descarga todos los items de una lista SP y devuelve el set de OPs."""
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{requests.utils.quote(list_name)}/items?expand=fields&$top=999"
    items = get_items_incremental(url, headers)
    ops = set()
    for i in items:
        val = str(i['fields'].get(op_field) or '').strip()
        # Si el campo principal está vacío, intentar con el campo Lookup de fallback
        if (not val or val.lower() in ('none', 'nan', '')) and fallback_lookup_field:
            val = str(i['fields'].get(fallback_lookup_field) or '').strip()
        if val and val.lower() not in ('none', 'nan', ''):
            ops.add(val)
    return ops, len(items)

def get_db_ops(table, op_field):
    """Descarga todos los op_numero de una tabla Supabase (con paginación)."""
    ops = set()
    start = 0
    while True:
        res = supabase.table(table).select(op_field).range(start, start + 999).execute()
        if not res.data:
            break
        for r in res.data:
            val = str(r.get(op_field) or '').strip()
            if val and val.lower() not in ('none', 'nan', ''):
                ops.add(val)
        if len(res.data) < 1000:
            break
        start += 1000
    return ops

TABLES = [
    # (Nombre visual, Lista SP, campo SP, fallback_lookup, Tabla DB, campo DB, usar sp_id?)
    ("Orden de Publicidad", "Orden de Publicidad", "OP",      None,           "ordenes_publicidad", "op",        False),
    ("Pagos",               "Pagos",               "OP",      "OPLookupId",   "pagos",              "op_numero", True),  # Lookup → comparar por sp_id
    ("TV",                  "TV",                  "OP_TP",   None,           "tv",                 "op_numero", False),
    ("Unidad de Negocio",   "Unidad de Negocio",   "OP_UNN",  None,           "unidades_negocio",   "op_numero", False),
]

lines = []
lines.append("=" * 70)
lines.append(f"  AUDITORÍA ESPEJO SHAREPOINT ↔ SUPABASE")
lines.append(f"  Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append("=" * 70)

total_discrepancias = 0

for (nombre, sp_list, sp_field, sp_fallback, db_table, db_field, use_sp_id) in TABLES:
    print(f"\n🔍 Auditando '{nombre}'...")

    if use_sp_id:
        # Para Pagos: comparar por sp_id (ID del ítem en SharePoint) vs sp_id en Supabase
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{requests.utils.quote(sp_list)}/items?expand=fields&$top=999"
        items = get_items_incremental(url, headers)
        sp_ids_en_sp = set(str(parse_int(i['fields'].get('id'))) for i in items if i['fields'].get('id'))
        sp_total_items = len(items)

        db_sp_ids = set()
        start = 0
        while True:
            res = supabase.table(db_table).select('sp_id').range(start, start + 999).execute()
            if not res.data: break
            for r in res.data:
                if r.get('sp_id'): db_sp_ids.add(str(r['sp_id']))
            if len(res.data) < 1000: break
            start += 1000

        solo_en_sp = sorted(sp_ids_en_sp - db_sp_ids)
        solo_en_db = sorted(db_sp_ids - sp_ids_en_sp)
        en_ambos = len(sp_ids_en_sp & db_sp_ids)
        label_sp = f"SP item IDs únicos: {len(sp_ids_en_sp)}"
        label_db = f"Supabase sp_ids únicos: {len(db_sp_ids)}"
        nota = "  ℹ️  Comparación por sp_id (Pagos usa campo Lookup, no texto)"
    else:
        sp_ops, sp_total_items = get_sp_ops(sp_list, sp_field, fallback_lookup_field=sp_fallback)
        db_ops = get_db_ops(db_table, db_field)
        solo_en_sp = sorted(sp_ops - db_ops)
        solo_en_db = sorted(db_ops - sp_ops)
        en_ambos = len(sp_ops & db_ops)
        label_sp = f"SharePoint: {len(sp_ops)} OPs únicas"
        label_db = f"Supabase: {len(db_ops)} OPs únicas"
        nota = None

    estado = "✅ ESPEJO PERFECTO" if not solo_en_sp and not solo_en_db else "⚠️  DISCREPANCIAS"
    total_discrepancias += len(solo_en_sp) + len(solo_en_db)

    lines.append(f"\n{'─' * 70}")
    lines.append(f"  TABLA: {nombre}")
    lines.append(f"  {label_sp} ({sp_total_items} items totales en SP)")
    lines.append(f"  {label_db}")
    lines.append(f"  En ambos: {en_ambos} | Estado: {estado}")
    if nota:
        lines.append(nota)

    if solo_en_sp:
        lines.append(f"\n  ❌ FALTAN en Supabase ({len(solo_en_sp)}):")
        for op in solo_en_sp[:50]:
            lines.append(f"     - {op}")
        if len(solo_en_sp) > 50:
            lines.append(f"     ... y {len(solo_en_sp) - 50} más")

    if solo_en_db:
        lines.append(f"\n  ⚠️  Solo en Supabase / no en SP ({len(solo_en_db)}):")
        for op in solo_en_db[:50]:
            lines.append(f"     - {op}")
        if len(solo_en_db) > 50:
            lines.append(f"     ... y {len(solo_en_db) - 50} más")


lines.append(f"\n{'=' * 70}")
lines.append(f"  RESUMEN FINAL: {'✅ SIN DISCREPANCIAS' if total_discrepancias == 0 else f'⚠️  {total_discrepancias} OPs con discrepancias'}")
lines.append("=" * 70)

report = "\n".join(lines)
print(report)

os.makedirs("DOCS", exist_ok=True)
out_file = f"DOCS/audit_espejo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
with open(out_file, "w", encoding="utf-8") as f:
    f.write(report)

print(f"\n📄 Reporte guardado en: {out_file}")
