import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

try:
    # 1. Excel Maestro 2026
    df = pd.read_excel('csv/tvtodas.xlsx')
    df['Fecha'] = pd.to_datetime(df['Fecha de la Orden'], errors='coerce')
    mask = (df['Fecha'] >= '2026-01-01') & (df['Fecha'] <= '2026-04-14')
    df_excel = df[mask].copy()
    df_excel['OP'] = df_excel['OP_TP'].astype(str).str.split('.').str[0].str.strip()
    excel_sums = df_excel.groupby('OP')['Importe Total'].sum().to_dict()

    # 2. Supabase 2026
    db_data = []
    limit = 1000
    offset = 0
    while True:
        res = supabase.table('tv').select('op_numero, importe_total, v_todas_las_op_report!inner(fecha_orden)').gte('v_todas_las_op_report.fecha_orden', '2026-01-01').lte('v_todas_las_op_report.fecha_orden', '2026-04-14').range(offset, offset + limit - 1).execute()
        if not res.data: break
        db_data.extend(res.data)
        offset += limit
    
    db_df = pd.DataFrame([{'OP': str(r['op_numero']).strip(), 'Importe': float(r['importe_total'] or 0)} for r in db_data])
    db_sums = db_df.groupby('OP')['Importe'].sum().to_dict()

    print(f"OPs en Excel: {len(excel_sums)} | OPs en DB: {len(db_sums)}")
    
    print("\n--- DIFERENCIAS DE IMPORTES POR OP (2026) ---")
    diff_total = 0
    all_ops = set(excel_sums.keys()) | set(db_sums.keys())
    for op in sorted(all_ops):
        e = excel_sums.get(op, 0)
        d = db_sums.get(op, 0)
        if abs(d - e) > 1:
            print(f"OP {op:10} | Excel: {e:12,.2f} | DB: {d:12,.2f} | DIFF: {d-e:12,.2f}")
            diff_total += (d - e)
            
    print(f"\nSuma total de diferencias: {diff_total:,.2f}")

except Exception as e:
    print("Error:", e)
