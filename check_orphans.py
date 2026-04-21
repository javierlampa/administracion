import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

op_num = "4040-3"
res = supabase.table("ordenes_publicidad").select("id, op").eq("op", op_num).execute()
print(f"Buscando OP '{op_num}' en ordenes_publicidad:")
print(res.data)

# Si no la encuentra por exacto, buscar por el prefijo 4040
res2 = supabase.table("ordenes_publicidad").select("id, op").ilike("op", "4040%").execute()
print(f"\nBuscando OPs que empiecen con '4040':")
print(res2.data)
