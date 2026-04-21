import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

dummy = {
    'op_numero': 'TEST_DUP',
    'programa_nombre': 'TEST_PROG',
    'tipo': 'TEST_TIPO',
    'importe_total': 100
}

# Insertar el primero
print("Insertando primero...")
supabase.table("tv").insert(dummy).execute()

# Insertar el segundo (identico)
print("Insertando segundo (identico)...")
try:
    res = supabase.table("tv").insert(dummy).execute()
    print("✅ SEGUNDO INSERTADO (No hay constraint única)")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Limpiar
supabase.table("tv").delete().eq("op_numero", "TEST_DUP").execute()
