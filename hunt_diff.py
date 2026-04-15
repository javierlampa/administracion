import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

targets = {367500: 'Cobertura Municipal Telesol', 960000: 'NOTICIEROS, 2', 180000: 'NOTICIEROS, LOS 3', 96000: 'TLN'}

print("--- INVESTIGANDO ÓRDENES CON MONTOS DE DIFERENCIA ---")
try:
    for monto, programa in targets.items():
        res = supabase.table('tv').select('op_numero, importe_total, programa_nombre, op_id').eq('importe_total', monto).ilike('programa_nombre', f'%{programa}%').execute()
        if res.data:
            r = res.data[0]
            op = supabase.table('v_todas_las_op_report').select('op, estado, es_canje').eq('id', r['op_id']).single().execute()
            o = op.data
            print(f"DIFF FOUND: {programa} | OP: {o['op']} | Monto: {r['importe_total']:,.0f} | Estado: {o['estado']}")

except Exception as e:
    print("Error:", e)
