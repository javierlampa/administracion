import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.rpc('get_evolucion_tc_metrics', {
    'p_start_date': '2026-01-01',
    'p_end_date': '2026-01-31',
    'p_empresa': 'Todas'
}).execute()

if res.data:
    print("Datos RAW de la Matriz:")
    for item in res.data.get('matrix', []):
        print(item)
else:
    print("No hay datos.")
