import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path='f:\\JAVIER PRIVADO\\APP PHYTON\\ADMINISTRACION\\.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def find_invalid_digital_2025_2026():
    print(" Buscando pautas digitales mal cargadas en 2025 y 2026...\n")
    
    # 1. Traemos OPs de 2025 y 2026 con array de datos
    res_ops = supabase.table('ordenes_publicidad').select('id, op, medidas_digital, cliente_nombre, fecha_orden').gte('fecha_orden', '2025-01-01').lte('fecha_orden', '2026-12-31').execute()
    
    # Filtramos en Python los que tengan medidas_digital valido
    ops_digitales = []
    for o in res_ops.data:
        md = o.get('medidas_digital')
        if md and str(md).strip().upper() not in ('NONE', 'NULL', ''):
            ops_digitales.append(o)
            
    if not ops_digitales:
        print("No se encontraron OPs con medidas_digital en 2025/2026.")
        return
        
    ops_map = {str(o['op']): o for o in ops_digitales}
    ids_to_check = list(ops_map.keys())
    
    invalidas = []
    
    step = 500
    for i in range(0, len(ids_to_check), step):
        chunk = ids_to_check[i:i+step]
        res_tv = supabase.table('tv').select('op_numero, programa_nombre, tipo, importe_total').in_('op_numero', chunk).execute()
        
        for r in res_tv.data:
            prog = str(r['programa_nombre']).upper().strip()
            # Si NO es exactamente DIARIO TELESOL o DIARIO ZONDA
            if prog not in ("DIARIO TELESOL", "DIARIO ZONDA"):
                op_obj = ops_map.get(r['op_numero'])
                invalidas.append({
                    'OP': r['op_numero'],
                    'Fecha': op_obj['fecha_orden'],
                    'Cliente': op_obj['cliente_nombre'],
                    'Medida': op_obj['medidas_digital'],
                    'Medio_Asignado': prog
                })

    if not invalidas:
        print("✅ TODAS las OPs digitales de 2025 y 2026 dicen exclusivamente 'Diario Telesol' o 'Diario Zonda'.")
    else:
        print(f"⚠️ Encontramos {len(invalidas)} items mal asignados en TV (2025-2026):\n")
        vistas = set()
        for c in sorted(invalidas, key=lambda x: x['Fecha']):
            key = f"{c['OP']}-{c['Medio_Asignado']}"
            if key not in vistas:
                print(f"🔹 OP #{c['OP']} | Fecha: {c['Fecha']} | Cliente: {c['Cliente']}")
                print(f"   Medida  : {c['Medida']}")
                print(f"   Programa en TV : '{c['Medio_Asignado']}' (<< ESTO ESTÁ MAL)")
                print("-" * 50)
                vistas.add(key)

if __name__ == "__main__":
    find_invalid_digital_2025_2026()
