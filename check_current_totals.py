import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def check_totals():
    # PowerBI Totals (from image)
    pbi = {
        '2026-01': 48611467.06,
        '2026-02': 60209292.04,
        '2026-03': 73925020.59,
        '2026-04': 53964864.47
    }
    
    report_content = "--- COMPARACIÓN PORTAL VS POWERBI ---\n"
    for month, pbi_val in pbi.items():
        year, m = month.split('-')
        next_m = int(m) + 1
        next_y = int(year)
        if next_m > 12:
            next_m = 1
            next_y += 1
        
        limit_start = f"{month}-01"
        limit_end = f"{next_y}-{next_m:02d}-01"
        
        res = supabase.table('ordenes_publicidad').select('importe_total').filter('fecha_orden', 'gte', limit_start).filter('fecha_orden', 'lt', limit_end).execute()
        db_val = sum(float(r['importe_total'] or 0) for r in res.data)
        diff = db_val - pbi_val
        status = "✅ OK" if abs(diff) < 1 else f"❌ DIFF: {diff:+,.2f}"
        line = f"{month} | Portal: {db_val:15,.2f} | PBI: {pbi_val:15,.2f} | {status}\n"
        print(line, end="")
        report_content += line
    
    with open("DOCS/comparativa_pbi.txt", "w", encoding="utf-8") as f:
        f.write(report_content)

if __name__ == "__main__":
    check_totals()
