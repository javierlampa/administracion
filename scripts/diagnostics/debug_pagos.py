import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

pagos = []
offset = 0
limit = 1000
while True:
    res_pagos = supabase.table("pagos").select("importe_pago, op_numero, op_id").range(offset, offset + limit - 1).execute()
    if not res_pagos.data: break
    pagos.extend(res_pagos.data)
    if len(res_pagos.data) < limit: break
    offset += limit

v_pagos = []
offset = 0
while True:
    res_v = supabase.table("v_pagos_resumen").select("total_pago").range(offset, offset + limit - 1).execute()
    if not res_v.data: break
    v_pagos.extend(res_v.data)
    if len(res_v.data) < limit: break
    offset += limit

if v_pagos:
    print(f"Total pago en la vista v_pagos_resumen: {sum([p['total_pago'] or 0 for p in v_pagos])}")

total_pago = sum([p['importe_pago'] or 0 for p in pagos])
print(f"Suma total de caja (pagos directos): {total_pago}")
print(f"Total registros pagos: {len(pagos)}")

res_ops = []
offset = 0
while True:
    r = supabase.table("ordenes_publicidad").select("op").range(offset, offset + limit - 1).execute()
    if not r.data: break
    res_ops.extend(r.data)
    if len(r.data) < limit: break
    offset += limit

ops_in_db = {str(o['op']).strip() for o in res_ops}

orphans = [p for p in pagos if str(p['op_numero']).strip() not in ops_in_db]
orphans_suma = sum(p['importe_pago'] or 0 for p in orphans)
print(f"Pagos huérfanos (OP no existe en OP): {len(orphans)} registros, Suma: {orphans_suma}")

print("Muestra 5 pagos huerfanos:")
for o in orphans[:5]:
    print(f"OP_Numero={str(o['op_numero']).strip()} Importe={o['importe_pago']}")
