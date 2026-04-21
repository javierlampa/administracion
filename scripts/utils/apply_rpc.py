import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path='f:\\JAVIER PRIVADO\\APP PHYTON\\ADMINISTRACION\\.env')

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase = create_client(url, key)

sql_file = 'f:\\JAVIER PRIVADO\\APP PHYTON\\ADMINISTRACION\\database\\sql\\20_KPI_EVOLUCION_PROGRAMA_RPC.sql'

with open(sql_file, 'r', encoding='utf-8') as f:
    sql_text = f.read()

# Try via REST API since some direct connection features fail via PgBouncer
try:
    print("Intentando ejecutar SQL a través del endpoint de Supabase...")
    # Not safely possible via python raw unless we have the connection string.
    # The safest way is to ask the user to run it in SQL Editor.
except Exception as e:
    print("Error:", e)
