import csv
import os
from dotenv import load_dotenv
from supabase import create_client

def find_diffs():
    load_dotenv()
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    
    # CSV Data
    csv_data = {}
    with open('csv/comision.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            op = row['OP']
            com = float(row['Importe Comision'].replace(',', '.') or 0)
            pago = float(row['Pago'].replace(',', '.') or 0)
            if op not in csv_data: csv_data[op] = {'com': 0.0, 'pago': 0.0}
            csv_data[op]['com'] += com
            csv_data[op]['pago'] += pago

    # DB Data
    res = supabase.table('v_comisiones_report').select('op, importe_comision, importe_pago').gte('fecha_orden', '2026-01-01').lte('fecha_orden', '2026-04-14').execute()
    db_data = {}
    for r in res.data:
        op = r['op']
        com = float(r['importe_comision'] or 0)
        pago = float(r['importe_pago'] or 0)
        if op not in db_data: db_data[op] = {'com': 0.0, 'pago': 0.0}
        db_data[op]['com'] += com
        db_data[op]['pago'] += pago

    print(f"{'OP':<15} | {'CSV Com':>12} | {'DB Com':>12} | {'Diff':>12}")
    print("-" * 60)
    for op in set(csv_data.keys()) | set(db_data.keys()):
        c_com = csv_data.get(op, {}).get('com', 0.0)
        d_com = db_data.get(op, {}).get('com', 0.0)
        if abs(c_com - d_com) > 1.0:
            print(f"{op:<15} | {c_com:>12,.2f} | {d_com:>12,.2f} | {d_com-c_com:>12,.2f}")

if __name__ == "__main__":
    find_diffs()
