import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(URL, KEY)

print(f"Llamando a get_evolucion_tc_metrics via RPC...")
try:
    res = supabase.rpc('get_evolucion_tc_metrics').execute()
    print("Respuesta:", res.data)
except Exception as e:
    print(f"Error RPC: {e}")
