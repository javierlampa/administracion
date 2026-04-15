import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("--- SUMA TV 2026 (SIN PENDIENTES) ---")
try:
    res = supabase.table('tv').select('importe_total, programa_nombre, v_todas_las_op_report!inner(fecha_orden, estado)').gte('v_todas_las_op_report.fecha_orden', '2026-01-01').lte('v_todas_las_op_report.fecha_orden', '2026-04-14').execute()
    
    total = 0
    valid_count = 0
    digital_sum = 0
    for r in res.data:
        status = r['v_todas_las_op_report']['estado']
        pn = r['programa_nombre'] or ''
        
        # Filtro de Estado
        if status in ('Anulada', 'Baja', 'Pendiente'):
            continue
            
        # Filtro de nombre (Digital)
        if 'digital' in pn.lower() or 'papel' in pn.lower():
            digital_sum += float(r['importe_total'] or 0)
            continue

        total += float(r['importe_total'] or 0)
        valid_count += 1
            
    print(f"Total Registros Válidos: {valid_count}")
    print(f"SUMA TOTAL FINAL: {total:,.2f}")
    print(f"Digital filtrado: {digital_sum:,.2f}")
    print("Objetivo PowerBI: 211,132,716.76")

except Exception as e:
    print("Error:", e)
