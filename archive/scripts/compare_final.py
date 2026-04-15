import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Traer ops validas
res_op = supabase.table('v_todas_las_op_report').select('id, op, estado, es_canje, fecha_orden, empresa').execute()
ops = {}
for r in res_op.data:
    val = r.get('fecha_orden') or ''
    if '2026' in str(val) and r.get('estado') not in ('Anulada', 'Baja'):
        ops[r['id']] = r

res_tv = supabase.table('tv').select('op_id, programa_nombre, importe_total, op_numero').execute()

records = []
for t in res_tv.data:
    if t['op_id'] in ops:
        op = ops[t['op_id']]
        prog = str(t['programa_nombre'] or '').strip()
        if not prog: prog = '(En blanco)'
        records.append({
            'op': op['op'],
            'op_numero_tv': t.get('op_numero'),
            'programa': prog,
            'importe_db': float(t['importe_total'] or 0.0),
            'empresa': op['empresa'],
            'es_canje': op['es_canje']
        })

if not records:
    print("NO SE ENCONTRARON RECORDS EN LA DB PARA 2026!")
    sys.exit(0)

df_db = pd.DataFrame(records)

df_csv = pd.read_excel('csv/tv.xlsx')
df_csv['Total'] = pd.to_numeric(df_csv['Importe Total'], errors='coerce').fillna(0)
df_csv['programa'] = df_csv['Programas.lookupValue'].fillna('(En blanco)').astype(str).str.strip()

print(f"Total Next.js DB (Todas las empresas): {df_db['importe_db'].sum():,.2f}")
print(f"Total Excel csv/tv.xlsx: {df_csv['Total'].sum():,.2f}")

# Simular comportamiento PowerBI excluyendo canjes
db_sin_canjes = df_db[df_db['es_canje'] == False]
print(f"Total Next.js SIN Canjes: {db_sin_canjes['importe_db'].sum():,.2f}")

# Comparar Cobertura Municipal Telesol
cob_db = df_db[df_db['programa'] == 'Cobertura Municipal Telesol']
cob_csv = df_csv[df_csv['programa'] == 'Cobertura Municipal Telesol']

print(f"Cobertura Municipal Telesol DB (con canjes): {cob_db['importe_db'].sum():,.2f}")
print(f"Cobertura Municipal Telesol DB (sin canjes): {cob_db[cob_db['es_canje'] == False]['importe_db'].sum():,.2f}")
print(f"Cobertura Municipal Telesol Excel: {cob_csv['Total'].sum():,.2f}")
