import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res_op = supabase.table("ordenes_publicidad").select("id, op").or_("op.eq.102/0,op.eq.1330").execute()
print("OPs found in DB:")
for r in res_op.data:
    print(r)

for r in res_op.data:
    op_id = r['id']
    res_pago = supabase.table("pagos").select("op_numero, importe_pago").eq("op_numero", str(op_id)).execute()
    print(f"Pagos with op_numero={op_id}: {res_pago.data}")
