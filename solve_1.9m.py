import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("--- BUSCANDO DIFERENCIA DE 1,933,500 ---")
try:
    # 1. Órdenes totales de la tabla principal (rango 01-01 a 14-04)
    res_ord = supabase.table('ordenes_publicidad').select('id, op, importe_total, empresa').gte('fecha_orden', '2026-01-01').lte('fecha_orden', '2026-04-14').execute()
    
    # 2. Órdenes que tienen pauta en la tabla TV
    res_tv = supabase.table('tv').select('op_id').execute()
    tv_ids = set(r['op_id'] for r in res_tv.data)
    
    extra_sum = 0
    print("\nÓrdenes que están en el Portal pero NO tienen pauta de TV (y por eso no saldrían en tu Excel):")
    for o in res_ord.data:
        if o['id'] not in tv_ids:
            extra_sum += float(o['importe_total'] or 0)
            print(f" - OP {o['op']} | Empresa: {o['empresa']} | Importe: {o['importe_total']:,.2f}")
            
    print(f"\nSUMA DE ESTAS ÓRDENES: {extra_sum:,.2f}")
    print(f"Diferencia buscada: 1,933,500.00")

except Exception as e:
    print("Error:", e)
