import os
from dotenv import load_dotenv
from supabase import create_client

def run_fix():
    load_dotenv()
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    
    # Buscar pagos sin vincular
    res = supabase.table('pagos').select('id, op_numero').is_('op_id', 'null').execute()
    orphans = res.data or []
    print(f"Reparando {len(orphans)} pagos huérfanos...")
    
    for p in orphans:
        op_num = p['op_numero']
        if not op_num: continue
        
        # Buscar la OP
        op_res = supabase.table('ordenes_publicidad').select('id').eq('op', op_num).execute()
        if op_res.data:
            op_id = op_res.data[0]['id']
            supabase.table('pagos').update({'op_id': op_id}).eq('id', p['id']).execute()
            print(f"Vínculo OK: Pago {p['id']} -> OP {op_num}")
            
    print("Proceso terminado.")

if __name__ == "__main__":
    run_fix()
