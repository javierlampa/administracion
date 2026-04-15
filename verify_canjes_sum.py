import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("--- VERIFICANDO SUMA DE CANJES (01-01-2026 al 14-04-2026) ---")
try:
    # 1. Traer todas las órdenes de TV que son CANJE
    res = supabase.table('v_todas_las_op_report').select('id, es_canje, importe_total, op').eq('es_canje', True).gte('fecha_orden', '2026-01-01').lte('fecha_orden', '2026-04-14').execute()
    
    total_canje = 0
    print(f"Canjes encontrados: {len(res.data)}")
    for r in res.data:
        monto = float(r['importe_total'] or 0)
        total_canje += monto
        print(f" - OP {r['op']}: {monto:,.2f}")
    
    print(f"\nSUMA TOTAL CANJES: {total_canje:,.2f}")
    
    # 2. Verificar diferencia exacta
    target_diff = 1603500
    if abs(total_canje - target_diff) < 1:
        print("\n¡COINCIDENCIA EXACTA! La diferencia son los Canjes.")
    else:
        print(f"\nNo coincide exactamente. Diferencia buscada: {target_diff:,.2f}, Encontrado: {total_canje:,.2f}")

except Exception as e:
    print("Error:", e)
