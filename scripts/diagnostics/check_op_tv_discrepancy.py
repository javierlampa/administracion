import os
from dotenv import load_dotenv
from supabase import create_client
from collections import defaultdict

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def run_check():
    print("Obteniendo datos de OPs de 2026...")
    # Filtro de fecha: 2026-01-01 a 2026-04-18
    res_op = supabase.table('ordenes_publicidad').select('id, op, importe_total, fecha_orden, es_canje').gte('fecha_orden', '2026-01-01').lte('fecha_orden', '2026-04-18').execute()
    
    ops = {}
    total_ops_amount = 0
    for r in res_op.data:
        monto = float(r['importe_total'] or 0)
        ops[r['id']] = {  # Usamos el id numérico de supabse como key
            'op': r['op'],
            'importe_total': monto,
            'fecha_orden': r['fecha_orden'],
            'es_canje': r.get('es_canje', False)
        }
        total_ops_amount += monto
        
    print(f"Total OPs en rango: {len(ops)}")
    print(f"Suma total de OPs: {total_ops_amount:,.2f}")
    
    print("\nObteniendo datos de la tabla TV (todas las páginas)...")
    tv_data = []
    # Usamos paginación para traer todos
    start = 0
    step = 900
    while True:
        res = supabase.table('tv').select('op_id, importe_total, segundos').range(start, start + step).execute()
        if not res.data:
            break
        tv_data.extend(res.data)
        start += step + 1
    
    print(f"Bloques TV obtenidos: {len(tv_data)}")
    
    tv_per_op = defaultdict(list)
    for t in tv_data:
        if t.get('op_id'):
            tv_per_op[t['op_id']].append(float(t.get('importe_total') or 0))
        
    total_tv_in_range_mapped = 0
    discrepancies = []
    ops_with_tv = 0
    
    for op_id, t_list in tv_per_op.items():
        if op_id in ops:
            ops_with_tv += 1
            tv_sum = sum(t_list)
            total_tv_in_range_mapped += tv_sum
            op_total = ops[op_id]['importe_total']
            
            # Tolerancia de 0.1 para decimales
            if tv_sum > op_total + 1:
                discrepancies.append({
                    'op': ops[op_id]['op'],
                    'fecha': ops[op_id]['fecha_orden'],
                    'op_total': op_total,
                    'tv_sum': tv_sum,
                    'diff': tv_sum - op_total,
                    'es_canje': ops[op_id]['es_canje']
                })
                
    print(f"\nResumen Analítico:")
    print(f"Total OPs que tienen bloques de TV: {ops_with_tv}")
    print(f"Suma de bloques de TV para esas OPs: {total_tv_in_range_mapped:,.2f}")
    print(f"Diferencia Global (TV - OPs): {total_tv_in_range_mapped - total_ops_amount:,.2f}")
    
    if discrepancies:
        print(f"\n--- ATENCIÓN: OPs donde TV > OP Total ({len(discrepancies)} casos) ---")
        discrepancies.sort(key=lambda x: x['diff'], reverse=True)
        for i, d in enumerate(discrepancies):
            if i < 20: # Mostramos top 20
                print(f"OP: {d['op']} | Fecha: {d['fecha']} | OP Total: {d['op_total']:,.2f} | Cant. TV: ? | TV Suma: {d['tv_sum']:,.2f} | Exceso: {d['diff']:,.2f} | Canje: {'Sí' if d['es_canje'] else 'No'}")
        if len(discrepancies) > 20:
             print(f"... y {len(discrepancies) - 20} casos más.")
    else:
        print("\n¡Excelente! Ninguna OP tiene bloques de TV cuya suma supere el total de la OP.")
        
    # Verificar bloques de TV huérfanos (que apuntan a OPs fuera de rango o que no existen)
    tv_no_mapped = sum(sum(t_list) for op_id, t_list in tv_per_op.items() if op_id not in ops)
    print(f"\nSuma de TV huérfano o fuera del rango de fechas buscado: {tv_no_mapped:,.2f}")

if __name__ == "__main__":
    run_check()
