import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Buscar pagos IDs que aparezcan más de una vez en la vista
res = supabase.table("v_comisiones_report").select("pago_id").execute()
ids = [r['pago_id'] for r in res.data]
from collections import Counter
c = Counter(ids)
dupes = {item: count for item, count in c.items() if count > 1}

if dupes:
    pago_id = list(dupes.keys())[0]
    print(f"Pago ID {pago_id} is duplicated {dupes[pago_id]} times in view.")
    
    # Ver por qué
    # Traer el pago
    p = supabase.table("pagos").select("*").eq("id", pago_id).execute().data[0]
    print(f"Pago op_numero: {p['op_numero']}")
    
    # Traer las OPs que matchean
    ops = supabase.table("ordenes_publicidad").select("*").eq("op", p['op_numero']).execute().data
    print(f"Number of OPs matching '{p['op_numero']}': {len(ops)}")
    for o in ops:
        print(f"  OP ID: {o['id']}, Name: {o.get('op')}")
else:
    print("No repeated pago_id found in view.")
