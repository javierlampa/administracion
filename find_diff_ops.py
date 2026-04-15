import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

res_op = supabase.table('v_todas_las_op_report').select('id, op, estado, es_canje, fecha_orden').execute()
ops = {}
for r in res_op.data:
    val = r.get('fecha_orden') or ''
    if '2026' in str(val) and r.get('estado') not in ('Anulada', 'Baja'):
        ops[r['id']] = r

res_tv = supabase.table('tv').select('op_id, programa_nombre, importe_total, op_numero').in_('programa_nombre', ['Banner digital Zonda', 'Cobertura Municipal Telesol', 'NOTICIEROS, 2', 'NOTICIEROS, LOS 3', 'TLN']).execute()

records = []
for t in res_tv.data:
    if t['op_id'] in ops:
        op = ops[t['op_id']]
        records.append({
            'programa_nombre': str(t['programa_nombre']).strip(),
            'importe_total': float(t['importe_total'] or 0),
            'es_canje': op['es_canje'],
            'op': op['op']
        })

df_db = pd.DataFrame(records)

canjes = df_db[df_db['es_canje'] == True]
print(f"Suma de Canjes en la DB para estos programas: {canjes['importe_total'].sum():,.2f}")
print("Canjes detalle:")
print(canjes.groupby('programa_nombre')['importe_total'].sum())

# Mismatch de fechas en excel (SharePoint TV)
df_excel = pd.read_excel('csv/tv.xlsx')
df_excel['Total'] = pd.to_numeric(df_excel['Importe Total'], errors='coerce').fillna(0)

print("\nTotal en SharePoint (Bruto sin filtro de fechas de o.fecha_orden):")
ag = df_excel[df_excel['Programas.lookupValue'].isin([
    'Banner digital Zonda', 'Cobertura Municipal Telesol', 
    'NOTICIEROS, 2', 'NOTICIEROS, LOS 3', 'TLN'
])].groupby('Programas.lookupValue')['Total'].sum()
print(ag)
