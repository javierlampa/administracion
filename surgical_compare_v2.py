import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# 1. CARGAR EXCEL
print("--- CARGANDO EXCEL ---")
df_excel = pd.read_excel('csv/tv.xlsx')
df_excel['Importe Total'] = pd.to_numeric(df_excel['Importe Total'], errors='coerce').fillna(0)
df_excel['OP_Limpia'] = df_excel['OP'].astype(str).str.strip().str.upper()
ex_grouped = df_excel.groupby(['OP_Limpia', 'Programas.lookupValue'])['Importe Total'].sum().reset_index()

# 2. CARGAR BASE DE DATOS
print("--- CARGANDO DB ---")
res_op = supabase.table('v_todas_las_op_report').select('id, op, estado, fecha_orden').gte('fecha_orden', '2026-01-01').lte('fecha_orden', '2026-04-14').execute()
ops = {r['id']: r for r in res_op.data if r['estado'] not in ('Anulada', 'Baja')}

all_tv = []
offset = 0
limit = 1000
while True:
    res_tv = supabase.table('tv').select('op_id, programa_nombre, importe_total').range(offset, offset + limit - 1).execute()
    if not res_tv.data: break
    all_tv.extend(res_tv.data)
    if len(res_tv.data) < limit: break
    offset += limit

db_records = []
for t in all_tv:
    if t['op_id'] in ops:
        op_info = ops[t['op_id']]
        db_records.append({
            'OP_Limpia': str(op_info['op']).strip().upper(),
            'programa': str(t['programa_nombre']).strip(),
            'importe': float(t['importe_total'] or 0)
        })

df_db = pd.DataFrame(db_records)
# Fix Grouping Column name
if not df_db.empty:
    db_grouped = df_db.groupby(['OP_Limpia', 'programa'])['importe'].sum().reset_index()
else:
    db_grouped = pd.DataFrame(columns=['OP_Limpia', 'programa', 'importe'])

# 3. MERGE
merged = pd.merge(
    db_grouped, 
    ex_grouped, 
    left_on=['OP_Limpia', 'programa'], 
    right_on=['OP_Limpia', 'Programas.lookupValue'], 
    how='outer'
)

merged['importe'] = merged['importe'].fillna(0)
merged['Importe Total'] = merged['Importe Total'].fillna(0)
merged['diff'] = merged['importe'] - merged['Importe Total']

# Solo mostrar diferencias grandes
diferencias = merged[abs(merged['diff']) > 1].sort_values('diff', ascending=False)

print(f"\nTOTAL DB: {df_db['importe'].sum() if not df_db.empty else 0:,.2f}")
print(f"TOTAL EXCEL: {df_excel['Importe Total'].sum():,.2f}")

print("\n--- OPS QUE SOBRAN EN DB (Están en DB pero no en el Excel filtrado) ---")
print(diferencias[diferencias['diff'] > 0][['OP_Limpia', 'programa', 'importe', 'Importe Total', 'diff']].to_string(index=False))

print("\n--- OPS QUE FALTAN EN DB (Están en Excel pero no en mi DB filtrada) ---")
print(diferencias[diferencias['diff'] < 0][['OP_Limpia', 'programa', 'importe', 'Importe Total', 'diff']].to_string(index=False))
