import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

try:
    print("Extrayendo datos de TV...")
    db_data = []
    limit = 1000
    offset = 0
    while True:
        res = supabase.table('tv').select('op_numero, importe_total, programa_nombre, v_todas_las_op_report!inner(fecha_orden, estado)').gte('v_todas_las_op_report.fecha_orden', '2026-01-01').lte('v_todas_las_op_report.fecha_orden', '2026-04-14').range(offset, offset + limit - 1).execute()
        if not res.data: break
        db_data.extend(res.data)
        offset += limit
    
    rows = []
    for r in db_data:
        if r['v_todas_las_op_report']['estado'] in ('Anulada', 'Baja'): continue
        pn = r['programa_nombre'] or ''
        if 'digital' in pn.lower() or 'papel' in pn.lower(): continue

        rows.append({
            'OP': r['op_numero'],
            'Programa': pn,
            'Importe Total': float(r['importe_total'] or 0),
            'Fecha Orden': r['v_todas_las_op_report']['fecha_orden'],
            'Estado': r['v_todas_las_op_report']['estado']
        })

    df = pd.DataFrame(rows)
    df = df.sort_values(by='OP')
    df.to_excel('csv/revision_portal_2026.xlsx', index=False)
    
    print(f"\n¡Listo! Archivo creado: csv/revision_portal_2026.xlsx")
    print(f"Total registros: {len(df)}")
    print(f"Suma Total: {df['Importe Total'].sum():,.2f}")

except Exception as e:
    print("Error:", e)
