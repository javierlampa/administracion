import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path='f:\\JAVIER PRIVADO\\APP PHYTON\\ADMINISTRACION\\.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def audit_digital_programs():
    print(" Buscando pautas digitales mal cargadas...\n")
    
    # Traemos todas las OPs que tengan alguna medida digital
    res_ops = supabase.table('ordenes_publicidad').select('id, op, medidas_digital, cliente_nombre, fecha_orden').gte('fecha_orden', '2025-01-01').execute()
    
    ops_digitales = [o for o in res_ops.data if o.get('medidas_digital') and str(o.get('medidas_digital')).strip().upper() not in ('NONE', 'NULL', '')]
    ops_map = {str(o['op']): o for o in ops_digitales}
    
    if not ops_map:
        print("No se encontraron OPs con medidas_digital completado.")
        return

    # Buscamos estas OPs en TV
    ids_to_check = list(ops_map.keys())
    
    invalidas = []
    
    # Procesar en bloques para la API
    step = 500
    for i in range(0, len(ids_to_check), step):
        chunk = ids_to_check[i:i+step]
        res_tv = supabase.table('tv').select('op_numero, programa_nombre, tipo, importe_total').in_('op_numero', chunk).execute()
        
        for r in res_tv.data:
            prog_nombre = str(r['programa_nombre']).upper().strip()
            # Si NO dice explícitamente "DIARIO TELESOL" o "DIARIO ZONDA", lo marcamos como inválido / a revisar
            if "DIARIO TELESOL" not in prog_nombre and "DIARIO ZONDA" not in prog_nombre:
                op_obj = ops_map.get(r['op_numero'])
                invalidas.append({
                    'OP': r['op_numero'],
                    'Cliente': op_obj['cliente_nombre'],
                    'Medida': op_obj['medidas_digital'],
                    'Medio_Asignado': prog_nombre,
                    'Importe': r['importe_total']
                })

    if not invalidas:
        print("✅ TODAS las OPs con medidas digitales están correctamente asignadas a Diario Telesol o Diario Zonda.")
    else:
        print(f"⚠️ Encontramos {len(invalidas)} filas en TV que tienen medidas cargadas pero un medio incorrecto:\n")
        # Remover duplicados visuales si una misma OP tiene la misma falla varias veces
        vistas = set()
        for c in sorted(invalidas, key=lambda x: x['OP']):
            key = f"{c['OP']}-{c['Medio_Asignado']}"
            if key not in vistas:
                print(f"🔹 OP #{c['OP']} | Cliente: {c['Cliente']}")
                print(f"   Medida: {c['Medida']}")
                print(f"   Dice: '{c['Medio_Asignado']}' (Debería decir Diario Telesol o Diario Zonda)")
                print(f"   ---")
                vistas.add(key)

if __name__ == "__main__":
    audit_digital_programs()
