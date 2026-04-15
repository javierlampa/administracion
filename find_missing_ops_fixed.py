import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# ALL 2026 ops
res_op = supabase.table('v_todas_las_op_report').select('id, op, estado, es_canje, fecha_orden, empresa').gte('fecha_orden', '2026-01-01').limit(10000).execute()
ops = {r['id']: r for r in res_op.data if r['estado'] not in ('Anulada', 'Baja')}

# ALL tv records
res_tv = supabase.table('tv').select('op_id, programa_nombre, importe_total, op_numero').limit(10000).execute()

records = []
for t in res_tv.data:
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
        ops_sum = prog_df.groupby('op')['importe'].sum().reset_index().sort_values('importe', ascending=False)
        print(ops_sum.to_string(index=False))
