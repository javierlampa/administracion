import csv
import os
from dotenv import load_dotenv
from supabase import create_client

def compare():
    # 1. PARSE CSV
    csv_path = 'csv/comision.csv'
    csv_stats = {'orden': 0.0, 'pago': 0.0, 'comision': 0.0, 'liquidado': 0.0, 'pendiente': 0.0}
    unique_ops_csv = {}
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        print(f"DEBUG: CSV Headers detected: {reader.fieldnames}")
        for row in reader:
            op = row['OP']
            imp_orden = float(row['Importe '].replace(',', '.') or 0)
            pago = float(row['Pago'].replace(',', '.') or 0)
            com = float(row['Importe Comision'].replace(',', '.') or 0)
            liq = row['Liquidado'] == 'SI'
            
            unique_ops_csv[op] = imp_orden
            csv_stats['pago'] += pago
            csv_stats['comision'] += com
            if liq:
                csv_stats['liquidado'] += com
            else:
                csv_stats['pendiente'] += com
    
    csv_stats['orden'] = sum(unique_ops_csv.values())

    # 2. FETCH DB
    load_dotenv()
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    
    # Rango 2026-01-01 -> 2026-04-14 (as per user's range)
    res = supabase.table('v_comisiones_report').select('*').gte('fecha_orden', '2026-01-01').lte('fecha_orden', '2026-04-14').execute()
    
    db_stats = {'orden': 0.0, 'pago': 0.0, 'comision': 0.0, 'liquidado': 0.0, 'pendiente': 0.0}
    unique_ops_db = {}
    
    for r in res.data:
        op = r['op']
        imp_orden = float(r['importe_orden'] or 0)
        pago = float(r['importe_pago'] or 0)
        com = float(r['importe_comision'] or 0)
        liq = bool(r['esta_liquidado'])
        
        unique_ops_db[op] = imp_orden
        db_stats['pago'] += pago
        db_stats['comision'] += com
        if liq:
            db_stats['liquidado'] += com
        else:
            db_stats['pendiente'] += com
            
    db_stats['orden'] = sum(unique_ops_db.values())

    print("\n--- COMPARACIÓN REPORTE COMISIONES 2026 ---")
    print(f"{'Métrica':<25} | {'CSV (Excel/SP)':>15} | {'Portal (DB)':>15} | {'Diferencia':>15}")
    print("-" * 75)
    for k in ['orden', 'pago', 'comision', 'liquidado', 'pendiente']:
        diff = db_stats[k] - csv_stats[k]
        print(f"{k.capitalize():<25} | {csv_stats[k]:>15,.2f} | {db_stats[k]:>15,.2f} | {diff:>15,.2f}")

    print("\nDetalle de discrepancias:")
    # OPs en CSV pero no en DB
    missing_in_db = set(unique_ops_csv.keys()) - set(unique_ops_db.keys())
    if missing_in_db:
        print(f"  - OPs en CSV pero no en DB ({len(missing_in_db)}): {list(missing_in_db)[:10]}...")
    
    # OPs en DB pero no en CSV
    extra_in_db = set(unique_ops_db.keys()) - set(unique_ops_csv.keys())
    if extra_in_db:
        print(f"  - OPs en DB pero no en CSV ({len(extra_in_db)}): {list(extra_in_db)[:10]}...")

if __name__ == "__main__":
    compare()
