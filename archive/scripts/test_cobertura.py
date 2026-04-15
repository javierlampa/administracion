import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Traer ops validas
res_op = supabase.table('v_todas_las_op_report').select('id, op, estado, es_canje, fecha_orden').neq('estado', 'Anulada').neq('estado', 'Baja').execute()
ops = {r['id']: r for r in res_op.data if r.get('fecha_orden') and r.get('fecha_orden').startswith('2026')}

# Traer tv
res_tv = supabase.table('tv').select('op_id, programa_nombre, importe_total').execute()

records = []
for t in res_tv.data:
    if t['op_id'] in ops:
        prog = str(t['programa_nombre'] or '').strip()
        if 'Cobertura Municipal Telesol' in prog:
            op = ops[t['op_id']]
            records.append({
                'op_id': op['id'],
                'op': op['op'],
                'estado': op['estado'],
                'es_canje': op['es_canje'],
                'importe': float(t['importe_total'] or 0)
            })

df = pd.DataFrame(records)
print(f"Total Next.js (Bruto): {df['importe'].sum():,.2f}")

canjes = df[df['es_canje'] == True]
print(f"Suma Canjes: {canjes['importe'].sum():,.2f}")
print("Canjes:\n", canjes)

# Que ops contribuyen:
print("TOP Ops:\n", df.sort_values('importe', ascending=False).head(10))
