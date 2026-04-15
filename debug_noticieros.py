import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("--- REVISANDO DIFERENCIAS EN NOTICIEROS, 2 ---")
try:
    res = supabase.table('tv').select('id, op_numero, programa_nombre, importe_total, op_id').ilike('programa_nombre', '%NOTICIEROS, 2%').execute()
    
    ops_ids = [r['op_id'] for r in res.data]
    res_ops = supabase.table('v_todas_las_op_report').select('id, op, es_canje, importe_total, estado').in_('id', ops_ids).execute()
    ops_map = {o['id']: o for o in res_ops.data}
    
    print(f"Total de registros encontrados en TV: {len(res.data)}")
    total_canje = 0
    for r in res.data:
        op = ops_map.get(r['op_id'], {})
        if op.get('es_canje'):
            total_canje += r['importe_total']
            print(f"CANJE: OP {r['op_numero']} | Importe: {r['importe_total']}")
    
    print(f"\nSUMA TOTAL DE CANJES EN NOTICIEROS, 2: {total_canje}")

except Exception as e:
    print("Error:", e)
