import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

s = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

all_data = []
offset = 0
limit = 1000
while True:
    res = s.table('pagos').select('importe_pago').range(offset, offset + limit - 1).execute()
    if not res.data: break
    all_data.extend(res.data)
    if len(res.data) < limit: break
    offset += limit

total = sum(float(d['importe_pago'] or 0) for d in all_data)
print(f"Total Sum in Supabase: ${total:,.2f}")
print(f"Count: {len(all_data)}")
