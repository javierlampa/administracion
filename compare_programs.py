import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

try:
    # 1. Programas en Excel
    df = pd.read_excel('csv/tv1.xlsx')
    excel_progs = set(df['Programas'].dropna().str.strip().unique())
    print(f"Total programas en Excel: {len(excel_progs)}")

    # 2. Programas en Supabase (TV en el rango)
    # Replicamos la lógica del SQL: JOIN con v_todas_las_op_report
    query = """
    SELECT t.programa_nombre, SUM(t.importe_total) as total
    FROM tv t
    JOIN v_todas_las_op_report o ON t.op_id = o.id
    WHERE o.fecha_orden >= '2026-01-01' AND o.fecha_orden <= '2026-04-14'
      AND o.estado NOT IN ('Anulada', 'Baja')
    GROUP BY 1
    """
    res = supabase.rpc('get_raw_sql', {'sql_query': query}).execute()
    # Si RPC no funciona, usamos table join manual
    if not res.data:
        res = supabase.table('tv').select('programa_nombre, importe_total, v_todas_las_op_report!inner(fecha_orden, estado)').gte('v_todas_las_op_report.fecha_orden', '2026-01-01').lte('v_todas_las_op_report.fecha_orden', '2026-04-14').execute()
        # Agrupar manualmente
        db_data = {}
        for r in res.data:
            pn = str(r['programa_nombre']).strip() if r['programa_nombre'] else '(En blanco)'
            db_data[pn] = db_data.get(pn, 0) + float(r['importe_total'] or 0)
    else:
        db_data = {str(r['programa_nombre']).strip(): float(r['total']) for r in res.data}

    print("\n--- COMPARACIÓN DE TOTALES POR PROGRAMA ---")
    portal_total_check = 0
    for prog, portal_sum in db_data.items():
        portal_total_check += portal_sum
        if prog not in excel_progs and prog != '(En blanco)':
            print(f" (!) Programa en Portal que NO está en Excel: '{prog}' | Suma: {portal_sum:,.2f}")
        
    print(f"\nTotal calculado en este script (Portal): {portal_total_check:,.2f}")

except Exception as e:
    print("Error:", e)
