import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Buscar la OP 4098
res = supabase.table("ordenes_publicidad").select("id, op").eq("op", "4098").execute()
print(f"Buscando OP '4098' en DB: {res.data}")

# Buscar el ID 777
res2 = supabase.table("ordenes_publicidad").select("id, op").eq("id", 777).execute()
print(f"Buscando ID 777 en DB: {res2.data}")
