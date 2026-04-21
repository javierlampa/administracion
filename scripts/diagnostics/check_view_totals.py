import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("v_comisiones_report").select("importe_pago", count="exact").gte("fecha_pago", "2026-01-01").lte("fecha_pago", "2026-04-20").execute()
print(f"Count of records in view for 2026: {res.count}")
total = sum([r['importe_pago'] for r in res.data])
print(f"Total importe_pago in view: {total}")
