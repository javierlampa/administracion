import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Intentamos insertar dos registros que mi script cree que son unicos pero la DB cree que son duplicados
# Probamos con 4098 y algo mas si es que hay sospechas
# O simplemente probamos insertar uno y luego otro con mismo op_id y unidad pero diferente op_numero

d1 = {'op_id': 777, 'op_numero': '4098', 'unidad_negocio': 'Canal Telesol', 'importe_total': 100}
d2 = {'op_id': 777, 'op_numero': '4098-DIFFERENT', 'unidad_negocio': 'Canal Telesol', 'importe_total': 200}

print("Insertando 4098...")
try:
    supabase.table("unidades_negocio").insert(d1).execute()
    print("✅ 4098 insertada.")
except Exception as e:
    print(f"❌ Error 1: {e}")

print("Insertando 4098-DIFFERENT (Mismo op_id 777, misma unidad)...")
try:
    supabase.table("unidades_negocio").insert(d2).execute()
    print("✅ 4098-DIFFERENT insertada.")
except Exception as e:
    print(f"❌ Error 2: {e}")

# Limpiar
supabase.table("unidades_negocio").delete().eq("op_id", 777).execute()
print("Limpieza hecha.")
