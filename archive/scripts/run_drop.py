import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

with open('drop_functions.sql', 'r') as f:
    sql = f.read()

try:
    # Intentar ejecutar el SQL a través de un RPC genérico si existe
    print("Ejecutando limpieza de funciones...")
    # Si tienes un rpc que ejecute SQL, úsalo. Si no, usaremos el archivo .sql manualmente si el usuario puede.
    # Por ahora intento rpc('get_raw_sql')
    supabase.rpc('get_raw_sql', {'sql_query': sql}).execute()
    print("Funciones eliminadas con éxito.")
except Exception as e:
    print("Error al ejecutar SQL:", e)
    print("Por favor, ejecuta el contenido de drop_functions.sql manualmente en el editor de Supabase si falla.")
