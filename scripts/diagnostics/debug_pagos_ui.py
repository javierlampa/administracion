import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("v_pagos_resumen").select("total_pago, op, fecha_orden").gte("fecha_orden", "2026-01-01").lte("fecha_orden", "2026-04-15").execute()

if res.data:
    total = sum([p['total_pago'] or 0 for p in res.data])
    print(f"Total Ingresos Reales para OPs de 2026: {total}")
    print(f"Count: {len(res.data)}")
else:
    print("No data")
