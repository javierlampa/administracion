import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("ordenes_publicidad").select("id, op").eq("id", 5893).execute()
print(f"ID 5893 en DB: {res.data}")
