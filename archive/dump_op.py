import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('.env')
s = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

p = s.table("pagos").select("*").gte("fecha_pago", "2025-09-01").lte("fecha_pago", "2025-12-31").execute()

count = 0
for pago in p.data:
    op_v = str(pago.get('op_valor', '')).strip()
    if not op_v: continue
    ops = s.table("ordenes_publicidad").select("*").eq("op", op_v).execute()
    if ops.data:
        fo = ops.data[0].get('fecha_orden', '')
        if fo and fo >= "2025-12-01" and fo <= "2025-12-31":
            print(f"Match: Pago de {op_v}, fecha_orden OP: {fo}")
            count += 1
    if count > 5: break
if count == 0:
    print("NO SE ENCONTRÓ NINGÚN MATCH.")
