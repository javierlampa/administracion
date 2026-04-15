import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(URL, KEY)

# Intentar obtener la definición de la vista
query = """
SELECT view_definition 
FROM information_schema.views 
WHERE table_name = 'v_todas_las_op_report';
"""

try:
    # Usamos una query directa si es posible via SQL Editor o similar, 
    # pero desde la API solo podemos llamar a RPCs.
    # Si no tenemos un RPC, intentaremos leerla como una tabla 
    # para al menos ver sus columnas.
    res = supabase.table('v_todas_las_op_report').select('*').limit(1).execute()
    print("Columnas encontradas:", res.data[0].keys() if res.data else "Vista vacía")
except Exception as e:
    print(f"Error al leer la vista: {e}")
