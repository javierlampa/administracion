import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def check_6933():
    print("--- OPs con 6933 ---")
    res_op = supabase.table('ordenes_publicidad').select('id, op, importe_total').eq('op', '6933').execute()
    for o in res_op.data:
        print(f"ID: {o['id']} | OP: {o['op']} | Importe Total: {o['importe_total']}")
        
    print("\n--- Keys from tv table ---")
    single_tv = supabase.table('tv').select('*').limit(1).execute()
    if single_tv.data:
         print(single_tv.data[0].keys())
         
    print("\n--- Bloques de TV donde op_id coincide con el de la OP ---")
    if res_op.data:
        op_id = res_op.data[0]['id']
        res_tv2 = supabase.table('tv').select('*').eq('op_id', op_id).execute()
        for t in res_tv2.data:
             print(f"TV ID: {t.get('id')} | Prog: {t.get('programa_nombre')} | Importe: {t.get('importe_total')} | Seg: {t.get('segundos')}")

if __name__ == "__main__":
    check_6933()
