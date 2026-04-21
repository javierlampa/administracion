import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def generate_report_2026():
    start_date = '2026-01-01'
    end_date = '2026-04-20'
    
    # 1. Traer todas las OPs del rango
    all_ops = []
    for i in range(0, 10000, 1000):
        res = supabase.table('ordenes_publicidad').select('op, importe_total, cliente_nombre, fecha_orden, es_canje')\
            .gte('fecha_orden', start_date).lte('fecha_orden', end_date).range(i, i + 999).execute()
        if not res.data: break
        all_ops.extend(res.data)
    
    # 2. Traer toda la tabla TV
    all_tv = []
    for i in range(0, 20000, 1000):
        res = supabase.table('tv').select('op_numero, importe_total').range(i, i + 999).execute()
        if not res.data: break
        all_tv.extend(res.data)
    
    tv_totals = {}
    for r in all_tv:
        op = str(r['op_numero']).strip()
        tv_totals[op] = tv_totals.get(op, 0) + (r['importe_total'] or 0)
    
    # Análisis Global
    map_ops = {str(r['op']).strip(): r for r in all_ops if r['op']}
    total_op_global = sum(r['importe_total'] or 0 for r in all_ops)
    total_tv_global = sum(tv_totals.get(op, 0) for op in map_ops.keys())
    
    print(f"🌍 TOTALES GLOBALES (EFECTIVO + CANJE):")
    print(f"   Maestra (OP): ${total_op_global:,.2f}")
    print(f"   Tabla TV:     ${total_tv_global:,.2f}")
    print(f"   DIFERENCIA:   ${total_op_global - total_tv_global:,.2f}")
    
    # Detectar discrepancias
    discrepancias = []
    for op_data in all_ops:
        op_num = str(op_data['op']).strip()
        monto_maestra = op_data['importe_total'] or 0
        monto_tv = tv_totals.get(op_num, 0)
        
        diff = monto_maestra - monto_tv
        if abs(diff) > 1.0: # Margen de $1 por redondeos
            discrepancias.append({
                'OP': op_num,
                'Cliente': op_data['cliente_nombre'],
                'Monto Maestra': monto_maestra,
                'Monto TV': monto_tv,
                'Faltan cargar en TV': diff,
                'Tipo': 'CANJE' if op_data['es_canje'] else 'EFECTIVO'
            })
            
    # Ordenar por el que más falta cargar
    discrepancias.sort(key=lambda x: abs(x['Faltan cargar en TV']), reverse=True)
    
    print(f"\nREPORT_START")
    print(f"| OP | Tipo | Cliente | Monto OP | Suma TV | DIFERENCIA |")
    print(f"| :--- | :--- | :--- | :--- | :--- | :--- |")
    for d in discrepancias:
        print(f"| {d['OP']} | {d['Tipo']} | {d['Cliente']} | ${d['Monto Maestra']:,.2f} | ${d['Monto TV']:,.2f} | **${d['Faltan cargar en TV']:,.2f}** |")
    print(f"REPORT_END")

if __name__ == "__main__":
    generate_report_2026()
