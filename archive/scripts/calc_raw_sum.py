import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("--- SUMA NETA TV 2026 (01-01 a 14-04) ---")
try:
    res = supabase.table('tv').select('importe_total, v_todas_las_op_report!inner(fecha_orden, estado)').gte('v_todas_las_op_report.fecha_orden', '2026-01-01').lte('v_todas_las_op_report.fecha_orden', '2026-04-14').execute()
    
    total = 0
    valid_count = 0
    for r in res.data:
        if r['v_todas_las_op_report']['estado'] not in ('Anulada', 'Baja'):
            total += float(r['importe_total'] or 0)
            valid_count += 1
            
    print(f"Total Registros: {valid_count}")
    print(f"SUMA TOTAL: {total:,.2f}")
    print("Objetivo PowerBI: 211,132,716.76")

except Exception as e:
    print("Error:", e)
