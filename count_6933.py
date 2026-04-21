import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def count_items():
    res_op = supabase.table('ordenes_publicidad').select('id, op').eq('op', '6933').execute()
    if not res_op.data:
        print("No se encontró la OP 6933")
        return
    op_id = res_op.data[0]['id']
    
    res_tv = supabase.table('tv').select('*').eq('op_id', op_id).execute()
    
    print(f"Total registros de tv para OP 6933: {len(res_tv.data)}")
    for t in res_tv.data:
        print(t)

if __name__ == "__main__":
    count_items()
