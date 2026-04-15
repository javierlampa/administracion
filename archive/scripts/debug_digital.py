import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("--- BUSCANDO ÓRDENES DIGITALES 2026 ---")
try:
    # 1. Ver total digital
    res_digital = supabase.table('ordenes_publicidad').select('id', count='exact').not_.is_('medidas_digital', 'null').execute()
    print(f"TOTAL DIGITAL ORDERS: {res_digital.count}")

    # 2. Ver primeros 2 digitales
    res_sample = supabase.table('ordenes_publicidad').select('id, op, medidas_digital, fecha_orden').not_.is_('medidas_digital', 'null').limit(2).execute()
    import json
    print("SAMPLE DIGITAL:", json.dumps(res_sample.data, indent=2))

    # 3. Ver si estas IDs están en la vista de reportes
    if res_sample.data:
        ids = [r['id'] for r in res_sample.data]
        res_view = supabase.table('v_todas_las_op_report').select('id, estado').in_('id', ids).execute()
        print(f"\nEstado en v_todas_las_op_report para estas IDs: {res_view.data}")

except Exception as e:
    print("Error:", e)
