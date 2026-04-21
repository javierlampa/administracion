import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def debug_op_link():
    res_ops = supabase.table('ordenes_publicidad').select('op').limit(5).execute()
    print("Muestra OP (Maestra):", [r['op'] for r in res_ops.data])
    
    res_tv = supabase.table('tv').select('op_numero').limit(5).execute()
    print("Muestra op_numero (TV):", [r['op_numero'] for r in res_tv.data])

if __name__ == "__main__":
    debug_op_link()
