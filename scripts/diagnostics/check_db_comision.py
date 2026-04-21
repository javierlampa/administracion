import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("pagos").select("importe_comision, op_numero").neq("importe_comision", 0).limit(5).execute()
print("Records with non-zero commission:")
for r in res.data:
    print(r)
