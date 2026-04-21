import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def get_exact_counts():
    tables = ['ordenes_publicidad', 'tv', 'unidades_negocio', 'pagos']
    print("--- CONTEO EXACTO EN LA BASE DE DATOS (No Estimado) ---")
    for t in tables:
        # Pidiendo count='exact' le decimos a Postgres que escanee la tabla completa
        res = supabase.table(t).select('id', count='exact').limit(1).execute()
        print(f"Tabla '{t}': {res.count} registros reales.")

if __name__ == '__main__':
    get_exact_counts()
