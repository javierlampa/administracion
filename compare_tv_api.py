import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client
import sys

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Fetch from TV table
res = supabase.table('v_todas_las_op_report').select('id, estado, empresa').in_('estado', ['Activa', 'Facturada', 'Cobrada', 'Morosa']).execute()
valid_ops = {row['id']: row for row in res.data}

res_tv = supabase.table('tv').select('op_id, programa_nombre, importe_total, importe_sin_iva').execute()

records = []
for t in res_tv.data:
    op_id = t.get('op_id')
    if op_id in valid_ops:
        op = valid_ops[op_id]
        if op.get('empresa') == 'Telesol' or True: # Not filtering by empresa yet to find the discrepancies universally
            name = str(t.get('programa_nombre') or '').strip()
            if not name: name = '(En blanco)'
            importe = float(t.get('importe_total') or 0)
            records.append({'programa_nombre': name, 'importe_total': importe, 'op_id': op_id, 'estado': op.get('estado'), 'empresa': op.get('empresa')})

df_db = pd.DataFrame(records)
# Only telesol?
df_db_telesol = df_db[df_db['empresa'] == 'Telesol']

grouped_db = df_db_telesol.groupby('programa_nombre')['importe_total'].sum().reset_index()

try:
    df_csv = pd.read_excel('csv/tv.xlsx')
except Exception as e:
    print("Error reading Excel:", e)
    sys.exit(1)

# Asumiremos columnas comunes de Excel
for col in df_csv.columns:
    if 'Programas.' in col or 'programa' in col.lower():
        prog_col = col
    if 'Suma' in col or 'total' in col.lower():
        tot_col = col

df_csv = df_csv.rename(columns={prog_col: 'programa_nombre', tot_col: 'total_Excel'})

merged = pd.merge(grouped_db, df_csv, on='programa_nombre', how='outer').fillna(0)
merged['diff'] = merged['importe_total'] - merged['total_Excel']

print(f"--- DB Total: {merged['importe_total'].sum():,.2f}")
print(f"--- Excel Total: {merged['total_Excel'].sum():,.2f}")

diffs = merged[abs(merged['diff']) > 1].sort_values('diff', ascending=False)
print("Diferencias:")
print(diffs)
