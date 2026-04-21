import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

res = supabase.table('pagos').select('sp_id').limit(10000).execute()
ids = [r['sp_id'] for r in res.data if r.get('sp_id')]
print(f"Total IDs en DB: {len(ids)}")
print(f"¿ID 7256 está en la DB? {7256 in ids}")
