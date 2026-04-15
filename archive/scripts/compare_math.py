import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

try:
    # 1. Excel
    df = pd.read_excel('csv/tv1.xlsx')
    df['Fecha'] = pd.to_datetime(df['Fecha de la Orden'], errors='coerce')
    mask = (df['Fecha'] >= '2026-01-01') & (df['Fecha'] <= '2026-04-14')
    df_2026 = df[mask]
    
    excel_totals = df_2026.groupby('Programas')['Importe Total'].sum().to_dict()

    # 2. Portal
    res = supabase.table('tv').select('programa_nombre, importe_total, v_todas_las_op_report!inner(fecha_orden, estado)').gte('v_todas_las_op_report.fecha_orden', '2026-01-01').lte('v_todas_las_op_report.fecha_orden', '2026-04-14').execute()
    
    db_totals = {}
    for r in res.data:
        if r['v_todas_las_op_report']['estado'] in ('Anulada', 'Baja'): continue
        pn = str(r['programa_nombre']).strip() if r['programa_nombre'] else '(En blanco)'
        db_totals[pn] = db_totals.get(pn, 0) + float(r['importe_total'] or 0)

    print("PROGRAMAS CON DIFERENCIAS:")
    all_progs = set(excel_totals.keys()) | set(db_totals.keys())
    for p in sorted(all_progs):
        e = excel_totals.get(p, 0)
        d = db_totals.get(p, 0)
        diff = d - e
        if abs(diff) > 1:
            print(f"> {p}")
            print(f"  Excel: {e:,.2f}")
            print(f"  Portal: {d:,.2f}")
            print(f"  DIFF: {diff:,.2f}")

except Exception as e:
    print("Error:", e)
