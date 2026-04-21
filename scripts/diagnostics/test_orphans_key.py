import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Intentar insertar dos huerfanos con misma unidad
d1 = {'op_id': None, 'op_numero': 'H1', 'unidad_negocio': 'Canal Telesol', 'importe_total': 100}
d2 = {'op_id': None, 'op_numero': 'H2', 'unidad_negocio': 'Canal Telesol', 'importe_total': 200}

print("Insertando Huerfano 1...")
try:
    supabase.table("unidades_negocio").insert(d1).execute()
    print("✅ H1 insertada.")
except Exception as e:
    print(f"❌ Error H1: {e}")

print("Insertando Huerfano 2 (Mismo op_id None, misma unidad)...")
try:
    supabase.table("unidades_negocio").insert(d2).execute()
    print("✅ H2 insertada.")
except Exception as e:
    print(f"❌ Error H2: {e}")

# Limpiar
supabase.table("unidades_negocio").delete().is_("op_id", "null").execute()
print("Limpieza hecha.")
