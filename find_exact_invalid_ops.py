import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path='f:\\JAVIER PRIVADO\\APP PHYTON\\ADMINISTRACION\\.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def find_exact_erroneous():
    print("Buscando OPs exactas...")
    res_ops = supabase.table('ordenes_publicidad').select('id, op, medidas_digital, cliente_nombre, fecha_orden').execute()
    
    ops_digitales = [o for o in res_ops.data if o.get('medidas_digital')]
    ops_map = {str(o['op']): o for o in ops_digitales}
    
    ids_to_check = list(ops_map.keys())
    
    cobertura_zonda = []
    rotativo_zonda = []
    
    step = 500
    for i in range(0, len(ids_to_check), step):
        chunk = ids_to_check[i:i+step]
        res_tv = supabase.table('tv').select('op_numero, programa_nombre, tipo, importe_total').in_('op_numero', chunk).execute()
        
        for r in res_tv.data:
            prog = str(r['programa_nombre']).strip().upper()
            op_obj = ops_map.get(r['op_numero'])
            if not op_obj: continue
            
            medida = str(op_obj.get('medidas_digital', '')).strip().upper()
            
            if '300 X 250 DESKTOP' in medida:
                if prog == 'COBERTURA MUNICIPAL ZONDA':
                    cobertura_zonda.append((r['op_numero'], op_obj['fecha_orden'], op_obj['cliente_nombre']))
                elif prog == 'ROTATIVO ZONDA':
                    rotativo_zonda.append((r['op_numero'], op_obj['fecha_orden'], op_obj['cliente_nombre']))

    print("\n[COBERTURA MUNICIPAL ZONDA - 300 x 250 Desktop]")
    for x in sorted(list(set(cobertura_zonda))):
        print(f"OP #{x[0]} (Fecha: {x[1]} | Cliente: {x[2]})")
        
    print("\n[ROTATIVO ZONDA - 300 x 250 Desktop]")
    for x in sorted(list(set(rotativo_zonda))):
        print(f"OP #{x[0]} (Fecha: {x[1]} | Cliente: {x[2]})")

if __name__ == "__main__":
    find_exact_erroneous()
