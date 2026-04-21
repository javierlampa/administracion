import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("ordenes_publicidad").select("id, op").ilike("op", "4098%").execute()
print("OPs en Supabase que empiezan con 4098:")
for r in res.data:
    print(r)
