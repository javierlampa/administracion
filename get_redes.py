import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path='f:\\JAVIER PRIVADO\\APP PHYTON\\ADMINISTRACION\\.env')
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

raw = sb.table('tv').select('op_numero, programa_nombre').execute()
for r in raw.data:
    p = str(r['programa_nombre']).upper()
    if 'REDES' in p:
        print("REDES-> OP:", r['op_numero'])
        
