import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def test():
    try:
        # Intentar insertar un cliente de prueba
        res = supabase.table('clientes').upsert({'id': 999999, 'nombre_cliente': 'CLIENTE TEST'}).execute()
        print("✅ Upsert exitoso en 'clientes'")
    except Exception as e:
        print(f"❌ Falló upsert en 'clientes': {e}")

if __name__ == "__main__":
    test()
