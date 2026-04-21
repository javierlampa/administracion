import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

for op in ["102/0", "1330"]:
    res_op = supabase.table("v_pagos_resumen").select("op, importe_total, total_pago, saldo").eq("op", op).execute()
    print(f"Resumen OP={op}: {res_op.data}")
    
    res_pagos = supabase.table("pagos").select("*").eq("op_numero", op).execute()
    print(f"Pagos para OP={op}: {[p['importe_pago'] for p in res_pagos.data]}")
