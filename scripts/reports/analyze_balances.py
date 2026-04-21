import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def analyze():
    # 1. Traer OPs
    res_ops = supabase.table('ordenes_publicidad').select('op, importe_total').execute()
    # 2. Traer Pagos
    res_pagos = supabase.table('pagos').select('op_numero, importe_pago').execute()

    def get_root(op):
        if not op: return ""
        return op.split('-')[0].strip()

    op_totals = {}
    for o in res_ops.data:
        r = get_root(o['op'])
        op_totals[r] = op_totals.get(r, 0) + float(o['importe_total'] or 0)

    pago_totals = {}
    for p in res_pagos.data:
        r = get_root(p['op_numero'])
        pago_totals[r] = pago_totals.get(r, 0) + float(p['importe_pago'] or 0)

    roots = set(op_totals.keys()) | set(pago_totals.keys())
    
    # 3. Calcular con agrupamiento por raíz
    total_balance_grouped = sum(max(0, op_totals.get(r, 0) - pago_totals.get(r, 0)) for r in roots)
    
    # 4. Calcular con el saldo de SharePoint (pagos.saldo)
    res_saldos = supabase.table('pagos').select('op_numero, saldo').order('id', desc=True).execute()
    latest_saldos = {}
    for s in res_saldos.data:
        if s['op_numero'] not in latest_saldos:
            latest_saldos[s['op_numero']] = float(s['saldo'] or 0)
    total_balance_sp = sum(latest_saldos.values())

    print(f"--- ANÁLISIS DE ESTRUCTURA ---")
    print(f"Total Balance (Grouped by Root): ${total_balance_grouped:,.2f}")
    print(f"Total Balance (SharePoint direct): ${total_balance_sp:,.2f}")
    print(f"Total Sales: ${sum(op_totals.values()):,.2f}")

if __name__ == "__main__":
    analyze()
