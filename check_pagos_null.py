import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Contar pagos con op_id NULL
res_null = supabase.table("pagos").select("id", count="exact").is_("op_id", "null").execute()
print(f"Pagos con op_id NULL (sin vincular): {res_null.count}")

# Contar pagos con op_id OK
res_ok = supabase.table("pagos").select("id", count="exact").not_.is_("op_id", "null").execute()
print(f"Pagos con op_id OK (vinculados): {res_ok.count}")

# Suma de importe_pago de los NULL
res_monto = supabase.table("pagos").select("importe_pago").is_("op_id", "null").execute()
total_perdido = sum(r.get("importe_pago") or 0 for r in res_monto.data)
print(f"Monto total de pagos SIN vincular: ${total_perdido:,.2f}")
