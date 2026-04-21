import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def check_op_blocks(op_num):
    print(f"--- REVISIÓN BLOQUES TV PARA OP {op_num} ---")
    res_op = supabase.table('ordenes_publicidad').select('importe_total').eq('op', op_num).execute()
    if res_op.data:
        print(f"Master OP Total: ${res_op.data[0]['importe_total']:,.2f}")
    
    res_tv = supabase.table('tv').select('*').eq('op_numero', op_num).execute()
    print(f"Encontrados {len(res_tv.data)} bloques en TV:")
    for t in res_tv.data:
        print(f"  - Programa: {t['programa_nombre']} | Importe: ${t['importe_total']:,.2f}")

if __name__ == "__main__":
    check_op_blocks('7556')
    print("\n")
    check_op_blocks('7116-01-26')
