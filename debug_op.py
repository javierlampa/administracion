import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def debug_op():
    print("\nDetalle Real de bloques de TV en la base de datos:")
    print(f"{'OP':<6} | {'Total de la OP':<15} | {'Programa (TV)':<30} | {'Importe en TV':<15} | {'Segs':<5} | {'Valor Seg'}")
    print("-" * 100)
    
    # Query manual de dos OPs que fallaban
    targets = ['6933', '6791']
    
    for t_op in targets:
        # Traer total de OP
        res_op = supabase.table('ordenes_publicidad').select('id, op, importe_total').eq('op', t_op).execute()
        if not res_op.data: continue
        
        op_data = res_op.data[0]
        op_id = op_data['id']
        op_total = float(op_data['importe_total'] or 0)
        
        # Traer sus bloques de TV
        res_tv = supabase.table('tv').select('programa_nombre, importe_total, segundos, valor_segundo').eq('op_id', op_id).execute()
        
        for t in res_tv.data:
            tv_importe = float(t['importe_total'] or 0)
            print(f"{op_data['op']:<6} | ${op_total:<14,.2f} | {str(t['programa_nombre'])[:28]:<30} | ${tv_importe:<14,.2f} | {t.get('segundos') or 0:<5} | ${float(t.get('valor_segundo') or 0):.2f}")

if __name__ == "__main__":
    debug_op()
