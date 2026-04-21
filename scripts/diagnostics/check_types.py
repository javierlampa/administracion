import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("v_comisiones_report").select("esta_liquidado, importe_comision").limit(10).execute()
for r in res.data:
    print(f"Liquidado: {r['esta_liquidado']} (type: {type(r['esta_liquidado'])}), Comision: {r['importe_comision']} (type: {type(r['importe_comision'])})")
