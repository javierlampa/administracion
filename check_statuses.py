import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("--- DISTRIBUCIÓN DE ESTADOS 2026 ---")
try:
    res = supabase.table('tv').select('importe_total, v_todas_las_op_report!inner(estado)').gte('v_todas_las_op_report.fecha_orden', '2026-01-01').lte('v_todas_las_op_report.fecha_orden', '2026-04-14').execute()
    
    status_map = {}
    for r in res.data:
        s = r['v_todas_las_op_report']['estado']
        imp = float(r['importe_total'] or 0)
        status_map[s] = status_map.get(s, 0) + imp
            
    for s, total in status_map.items():
        print(f"Estado {s:15} | Total: {total:15,.2f}")

except Exception as e:
    print("Error:", e)
