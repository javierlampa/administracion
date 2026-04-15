import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

try:
    res = supabase.rpc('get_evolucion_programa_metrics', {
        'p_start_date': '2026-01-01',
        'p_end_date': '2026-12-31',
        'p_empresa': 'Todas'
    }).execute()
    print("SUCCESS")
except Exception as e:
    print("ERROR:", repr(e))
