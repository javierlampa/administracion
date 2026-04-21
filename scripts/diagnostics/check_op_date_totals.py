import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Sumar pagos donde la OP asociada sea de 2026
res = supabase.table("v_comisiones_report").select("importe_pago, importe_comision").gte("fecha_orden", "2026-01-01").lte("fecha_orden", "2026-12-31").execute()
total_pago = sum([r['importe_pago'] for r in res.data])
total_com = sum([r['importe_comision'] for r in res.data])

print(f"Total Pago for OPs of 2026: {total_pago}")
print(f"Total Comision for OPs of 2026: {total_com}")
print(f"Count: {len(res.data)}")
