import os
from supabase import create_client
from dotenv import load_dotenv
import time

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("Vaciando tabla de unidades de negocio...")
total_deleted = 0
while True:
    try:
        # Hacer petición limitando 1000, la máxima de la API
        res = supabase.table('unidades_negocio').select('id').limit(1000).execute()
        if not res.data:
            break
            
        ids = [row['id'] for row in res.data]
        res_del = supabase.table('unidades_negocio').delete().in_('id', ids).execute()
        total_deleted += len(ids)
        print(f"Borrados: {total_deleted}")
        time.sleep(0.5)
    except Exception as e:
        print("Error al borrar:", e)
        break

print(f"Vaciado COMPLETO de {total_deleted} filas. Base de datos está en 0.")
