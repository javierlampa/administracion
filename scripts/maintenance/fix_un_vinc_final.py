import os
from dotenv import load_dotenv
from supabase import create_client

def final_fix_links():
    load_dotenv()
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    
    print("🚀 Iniciando REPARACIÓN DEFINITIVA de Vínculos (ID -> OP)...")
    
    # 1. Obtenemos el mapa de ID de SharePoint -> Número de OP Real
    res_ops = supabase.table('ordenes_publicidad').select('id, op').execute()
    # id_to_op = {str(7328): "6405", ...}
    id_to_op = {str(item['id']): str(item['op']).strip() for item in res_ops.data or []}
    
    # 2. Obtenemos todas las unidades de negocio
    res_un = supabase.table('unidades_negocio').select('id, op_numero').execute()
    all_un = res_un.data or []
    
    count = 0
    for un in all_un:
        op_actual = str(un['op_numero']).strip()
        
        # Si el número que tiene es en realidad un ID de SharePoint, lo cambiamos por la OP Real
        if op_actual in id_to_op:
            op_real = id_to_op[op_actual]
            
            supabase.table('unidades_negocio').update({
                'op_numero': op_real
            }).eq('id', un['id']).execute()
            
            count += 1

    print(f"\n🏆 ¡REPARACIÓN COMPLETADA!")
    print(f"Se corrigieron {count} unidades de negocio.")
    print("Ahora en el reporte deberías ver todo agrupado por la OP real.")

if __name__ == "__main__":
    final_fix_links()
