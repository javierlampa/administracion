import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(URL, KEY)

ops_to_check = [
    "1058-1", "1058-2", "1058-3", "1167", "1198", "1198-12",
    "1315-05", "1580-05"
]

print(f"--- ANALISIS DE DATOS FALTANTES ---")

for op in ops_to_check:
    print(f"\nBusqueda de OP: {op}")
    # 1. Buscar en ordenes_publicidad
    r_op = supabase.table("ordenes_publicidad").select("*").eq("op", op).execute()
    if r_op.data:
        print(f"  [FOUND IN OP TABLE] ID: {r_op.data[0]['id']}, Fecha: {r_op.data[0]['fecha_orden']}")
    else:
        print(f"  [NOT FOUND IN OP TABLE] ❌")

    # 2. Buscar en pagos
    r_pago = supabase.table("pagos").select("*").eq("op_valor", op).execute()
    if r_pago.data:
        print(f"  [FOUND IN PAGOS TABLE] Count: {len(r_pago.data)}")
        for p in r_pago.data:
            print(f"    - Pago ID: {p['id']}, op_id linked: {p['op_id']}, Importe: {p['importe_pago']}")
    else:
        print(f"  [NOT FOUND IN PAGOS TABLE] ❌")

# 3. Contar totales
print(f"\n--- TOTALES EN BASE DE DATOS ---")
ops_count = supabase.table("ordenes_publicidad").select("id", count="exact").execute().count
pagos_count = supabase.table("pagos").select("id", count="exact").execute().count
print(f"Total OPs: {ops_count}")
print(f"Total Pagos: {pagos_count}")

# 4. Chequear OPs huerfanas en Pagos
huerfanas = supabase.table("pagos").select("id, op_valor").is_("op_id", "null").order("op_valor").execute()
if huerfanas.data:
    print(f"\nPagos huerfanos (sin op_id): {len(huerfanas.data)}")
    for h in huerfanas.data[:10]:
        print(f"  - Pago {h['id']} -> OP Texto: {h['op_valor']}")
