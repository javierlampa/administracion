import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

try:
    print("1. Cargando Excel Maestro (tvtodas.xlsx)...")
    df_excel = pd.read_excel('csv/tvtodas.xlsx')
    # Columnas: OP_TP, Importe Total
    df_excel['OP'] = df_excel['OP_TP'].astype(str).str.split('.').str[0].str.strip()
    # Agrupar Excel por OP para comparar totales por orden
    excel_sums = df_excel.groupby('OP')['Importe Total'].sum().to_dict()

    print("2. Cargando Datos de Supabase (Uniendo TV con Órdenes para obtener fechas)...")
    db_data = []
    limit = 1000
    offset = 0
    while True:
        # Traemos la pauta unida a su orden para tener la fecha oficial
        res = supabase.table('tv').select('op_numero, importe_total, v_todas_las_op_report!inner(fecha_orden, estado)').gte('v_todas_las_op_report.fecha_orden', '2026-01-01').lte('v_todas_las_op_report.fecha_orden', '2026-04-14').range(offset, offset + limit - 1).execute()
        if not res.data: break
        db_data.extend(res.data)
        offset += limit
    
    # Agrupar DB por OP
    db_sums = {}
    for r in db_data:
        if r['v_todas_las_op_report']['estado'] in ('Anulada', 'Baja'): continue
        op = str(r['op_numero']).strip()
        db_sums[op] = db_sums.get(op, 0) + float(r['importe_total'] or 0)

    print("\n--- DIFERENCIAS ENCONTRADAS (SOLO OPs DE 2026) ---")
    diff_total = 0
    # Comparamos solo las OPs que el portal detecta en el rango 2026
    for op in sorted(db_sums.keys()):
        e = excel_sums.get(op, 0)
        d = db_sums.get(op, 0)
        if abs(d - e) > 1:
            print(f"OP {op:15} | Excel: {e:12,.2f} | Portal: {d:12,.2f} | DIFF: {d-e:12,.2f}")
            diff_total += (d - e)

    print(f"\nSUMA TOTAL DE DIFERENCIAS: {diff_total:,.2f}")
    print("Diferencia que buscamos: ~1,933,500.00")

except Exception as e:
    print("Error:", e)
