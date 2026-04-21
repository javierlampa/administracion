import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def audit_un_links():
    # 1. Traer una muestra de Órdenes Maestras
    res_ops = supabase.table('ordenes_publicidad').select('id, op').limit(1000).execute()
    op_map = {str(r['op']).strip(): r['id'] for r in res_ops.data}
    
    # 2. Traer una muestra de Unidades de Negocio
    res_un = supabase.table('unidades_negocio').select('op_numero, op_id').limit(1000).execute()
    
    print(f"Auditando vínculos de UN...")
    total = len(res_un.data)
    huerfanas = 0
    
    for row in res_un.data:
        op_num = str(row['op_numero'] or '').strip()
        if row['op_id'] is None:
            huerfanas += 1
            # Ver si el número de OP existe en nuestro mapa (con o sin decimales)
            match = op_map.get(op_num)
            if not match:
                # Probar si el número en UN es algo tipo "7191.0" y en la Maestra es "7191"
                try:
                    clean_num = str(int(float(op_num)))
                    match = op_map.get(clean_num)
                except: pass
            
            if match:
                if huerfanas <= 5:
                    print(f"  ❌ OP {op_num} no tiene link pero EXISTE en Maestra como ID {match}. (Falla el formato)")
            else:
                if huerfanas <= 5:
                    print(f"  ❓ OP {op_num} no existe en la muestra de 1000 Maestras.")

    print(f"\nResumen: {huerfanas}/{total} unidades en la muestra están huérfanas.")

if __name__ == "__main__":
    audit_un_links()
