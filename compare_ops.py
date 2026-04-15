import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

try:
    # 1. Leer OPs del Excel
    df = pd.read_excel('csv/tv1.xlsx')
    excel_ops = set(df['OP'].astype(str).str.split('.').str[0].str.strip().unique())
    print(f"Total OPs únicas en Excel: {len(excel_ops)}")

    # 2. Leer OPs de Supabase (rango 01-01 a 14-04)
    res = supabase.table('v_todas_las_op_report').select('op, importe_total, programa_nombre').gte('fecha_orden', '2026-01-01').lte('fecha_orden', '2026-04-14').execute()
    
    sobrantes = []
    total_sobrante = 0
    for r in res.data:
        op_str = str(r['op']).strip()
        if op_str not in excel_ops:
            sobrantes.append(r)
            total_sobrante += float(r['importe_total'] or 0)
    
    print(f"OPs en Portal que NO están en Excel: {len(sobrantes)}")
    if sobrantes:
        print("\nLista de órdenes sobrantes en el Portal:")
        # Mostrar las primeras 20 para no saturar
        for s in sobrantes[:20]:
            print(f" - OP {s['op']} | Programa: {s['programa_nombre']} | Importe: {s['importe_total']:,.2f}")
        
        print(f"\nSUMA TOTAL SOBRANTE: {total_sobrante:,.2f}")
        print(f"Diferencia que buscábamos: 1,603,500.00")

except Exception as e:
    print("Error:", e)
