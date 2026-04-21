import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def check():
    res = supabase.table('unidades_negocio').select('id').is_('unidad_negocio', 'null').execute()
    count = len(res.data or [])
    print(f"RESULTADO: Quedan {count} unidades sin asignar.")

if __name__ == "__main__":
    check()
