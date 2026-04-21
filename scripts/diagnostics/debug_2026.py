import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path='f:\\JAVIER PRIVADO\\APP PHYTON\\ADMINISTRACION\\.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def debug_2026():
    print(" Buscando en 2026...\n")
    
    res_ops = supabase.table('ordenes_publicidad').select('id, op, medidas_digital, cliente_nombre, fecha_orden').gte('fecha_orden', '2026-01-01').execute()
    ops_map = {str(o['op']): o for o in res_ops.data}
    ids_to_check = list(ops_map.keys())
    
    step = 500
    for i in range(0, len(ids_to_check), step):
        chunk = ids_to_check[i:i+step]
        res_tv = supabase.table('tv').select('op_numero, programa_nombre, tipo, importe_total').in_('op_numero', chunk).execute()
        
        for r in res_tv.data:
            prog = str(r['programa_nombre']).strip().upper()
            op_obj = ops_map.get(r['op_numero'])
            if not op_obj: continue
            
            medida = str(op_obj.get('medidas_digital', '')).strip().upper()
            
            # Chequear REDES
            if prog == 'REDES':
                print(f"OP REDES: {r['op_numero']} | Medida: {medida} | Fecha: {op_obj['fecha_orden']} | Cliente: {op_obj['cliente_nombre']}")
                
            # Chequear ROTATIVO ZONDA 300x250
            if prog == 'ROTATIVO ZONDA':
                print(f"OP ROTATIVO ZONDA: {r['op_numero']} | Medida: {medida} | Fecha: {op_obj['fecha_orden']} | Cliente: {op_obj['cliente_nombre']}")
                
            # Chequear DIARIO TELESOL - (Sin medida)
            if prog == 'DIARIO TELESOL' and ('NONE' in medida or 'NULL' in medida or not medida):
                if r['tipo'] and ('DIGITAL' in str(r['tipo']).upper() or 'BANNER' in str(r['tipo']).upper()):
                    print(f"OP DIARIO TELESOL SIN MEDIDA (TIPO DIGITAL): {r['op_numero']} | Fecha: {op_obj['fecha_orden']} | Cliente: {op_obj['cliente_nombre']}")

if __name__ == "__main__":
    debug_2026()
