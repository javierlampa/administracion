import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# ALL 2026 ops in range
res_op = supabase.table('v_todas_las_op_report').select('id, op, estado, es_canje, fecha_orden, empresa').gte('fecha_orden', '2026-01-01').lte('fecha_orden', '2026-04-14').limit(10000).execute()
ops = {r['id']: r for r in res_op.data if r['estado'] not in ('Anulada', 'Baja')}

print(f"Total OPs en rango: {len(ops)}")

# Fetch TV records in batches
all_tv = []
offset = 0
limit = 1000
while True:
    res_tv = supabase.table('tv').select('op_id, programa_nombre, importe_total, op_numero').range(offset, offset + limit - 1).execute()
    if not res_tv.data:
        break
    all_tv.extend(res_tv.data)
    if len(res_tv.data) < limit:
        break
    offset += limit

print(f"Total TV records: {len(all_tv)}")

records = []
for t in all_tv:
    if t['op_id'] in ops:
        op = ops[t['op_id']]
        records.append({
            'programa': str(t['programa_nombre']).strip(),
            'op': op['op'],
            'fecha': op['fecha_orden'],
            'importe': float(t['importe_total'] or 0),
            'es_canje': op['es_canje'],
            'empresa': op['empresa']
        })

df = pd.DataFrame(records)

diff_progs = ['Banner digital Zonda', 'Cobertura Municipal Telesol', 'NOTICIEROS, 2', 'NOTICIEROS, LOS 3', 'TLN']

print("\n--- DETALLE DE OPS PARA ESTOS PROGRAMAS ---")
for p in diff_progs:
    prog_df = df[df['programa'] == p]
    print(f"\n[{p}] Total: {prog_df['importe'].sum():,.2f}")
    if not prog_df.empty:
        # Sumar por OP_ID para evitar colisiones de numeros de OP
        ops_sum = prog_df.groupby('op')['importe'].sum().reset_index().sort_values('importe', ascending=False)
        print(ops_sum.to_string(index=False))
