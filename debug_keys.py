import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("tv").select("op_numero, programa_nombre, tipo").limit(5).execute()
print("Estructura en DB:")
for r in res.data:
    key = (str(r.get('op_numero') or '').strip(), str(r.get('programa_nombre') or '').strip(), str(r.get('tipo') or '').strip())
    print(f"DB Key: {key}")

# Ver una OP especifica que el reporte dice que falta
op_target = "5011"
res2 = supabase.table("tv").select("*").eq("op_numero", op_target).execute()
print(f"\nBuscando OP {op_target} en DB:")
print(res2.data)
