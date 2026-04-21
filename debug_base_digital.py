import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path='f:\\JAVIER PRIVADO\\APP PHYTON\\ADMINISTRACION\\.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def get_base_digital_2026():
    print(" Buscando TODO lo digital en tv para 2026...\n")
    # Join manual para replicar `base_digital`
    res_ops = supabase.table('ordenes_publicidad').select('id, op, empresa, medidas_digital, cliente_nombre, fecha_orden').gte('fecha_orden', '2026-01-01').lte('fecha_orden', '2026-12-31').execute()
    
    ops_map = {str(o['op']): o for o in res_ops.data}
    ids_to_check = list(ops_map.keys())
    
    print(f"Total OPs en 2026: {len(ids_to_check)}")
    
    found = []
    
    step = 500
    for i in range(0, len(ids_to_check), step):
        chunk = ids_to_check[i:i+step]
        res_tv = supabase.table('tv').select('op_numero, programa_nombre, tipo, importe_total').in_('op_numero', chunk).execute()
        
        for r in res_tv.data:
            prog = str(r['programa_nombre']).strip().upper()
            tipo = str(r['tipo']).strip().upper()
            op_obj = ops_map.get(r['op_numero'])
            
            medida = str(op_obj.get('medidas_digital', '')).strip().casefold()
            
            # The SQL condition:
            # (t.tipo ILIKE '%DIGITAL%' OR t.tipo ILIKE '%BANNER%' OR o.medidas_digital IS NOT NULL)
            
            if 'digital' in tipo or 'banner' in tipo or (medida and medida not in ('none', 'null', '')):
                found.append({
                    'OP': r['op_numero'],
                    'Fecha': op_obj['fecha_orden'],
                    'Programa': r['programa_nombre'],
                    'Tipo': r['tipo'],
                    'Medida': op_obj['medidas_digital'],
                    'Importe': r['importe_total']
                })

    for f in found:
        if 'COBERTURA' in str(f['Programa']).upper() or 'ROTATIVO' in str(f['Programa']).upper() or 'REDES' in str(f['Programa']).upper():
             print(f"OP: {f['OP']} | Prog: {f['Programa']} | Tipo: {f['Tipo']} | Medida: {f['Medida']} | Importe: {f['Importe']} | Fecha: {f['Fecha']}")

if __name__ == "__main__":
    get_base_digital_2026()
