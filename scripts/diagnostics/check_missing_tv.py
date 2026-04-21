import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def audit_discrepancy_global_2026():
    start_date = '2026-01-01'
    end_date = '2026-04-18'
    
    print(f"--- AUDITORÍA GLOBAL (Periodo {start_date} al {end_date}) ---")
    
    # 1. Maestras
    all_ops_master = []
    step = 1000
    for i in range(0, 10000, step):
        res_ops = supabase.table('ordenes_publicidad').select('op, importe_total, cliente_nombre, fecha_orden, es_canje')\
            .gte('fecha_orden', start_date).lte('fecha_orden', end_date).range(i, i + step - 1).execute()
        if not res_ops.data: break
        all_ops_master.extend(res_ops.data)
    
    # 2. TV
    all_tv = []
    for i in range(0, 20000, step):
        res_tv = supabase.table('tv').select('op_numero, importe_total').range(i, i + step - 1).execute()
        if not res_tv.data: break
        all_tv.extend(res_tv.data)
    
    tv_totals_by_op = {}
    for r in all_tv:
        op = str(r['op_numero']).strip()
        tv_totals_by_op[op] = tv_totals_by_op.get(op, 0) + (r['importe_total'] or 0)
    
    # Análisis Global (Suma de OPs vs Suma de sus registros en TV)
    map_ops = {str(r['op']).strip(): r for r in all_ops_master if r['op']}
    
    total_op_global = sum(r['importe_total'] or 0 for r in all_ops_master)
    total_tv_global = sum(tv_totals_by_op.get(op, 0) for op in map_ops.keys())
    
    print(f"\n🌍 TOTALES GLOBALES (EFECTIVO + CANJE):")
    print(f"   Maestra (OP): ${total_op_global:,.2f}")
    print(f"   Tabla TV:     ${total_tv_global:,.2f}")
    print(f"   DIFERENCIA:   ${total_op_global - total_tv_global:,.2f}")

    # Identificar las OPs con diferencias
    print("\n🔍 DETALLE DE LAS DIFERENCIAS MÁS GRANDES:")
    diferencias = []
    for op, data in map_ops.items():
        monto_op = data['importe_total'] or 0
        monto_tv = tv_totals_by_op.get(op, 0)
        diff = monto_op - monto_tv
        if abs(diff) > 0.01:
            diferencias.append({
                'op': op,
                'cliente': data['cliente_nombre'],
                'monto_op': monto_op,
                'monto_tv': monto_tv,
                'diff': diff,
                'es_canje': data['es_canje']
            })

    for d in sorted(diferencias, key=lambda x: abs(x['diff']), reverse=True)[:15]:
        tipo = "[CANJE]" if d['es_canje'] else "[EFECTIVO]"
        print(f"   {tipo} OP: {d['op']} | Diff: ${d['diff']:,.2f} | {d['cliente']}")

if __name__ == "__main__":
    audit_discrepancy_global_2026()
