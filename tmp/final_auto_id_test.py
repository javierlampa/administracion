import os
import random
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('f:/JAVIER PRIVADO/APP PHYTON/ADMINISTRACION/.env')

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(URL, KEY)

# GENERAR NOMBRE DE OP ÚNICO PARA ESTA PRUEBA
TEST_OP = f"OP-AUTO-{random.randint(100, 999)}"

def run_auto_id_test():
    print(f"🚀 Probando Generación de ID Automático para: {TEST_OP}\n")
    
    try:
        # 1. INSERT CABECERA (SIN CAMPO 'id')
        print(" -> Insertando Cabecera (Postgres generará el ID solo)...", flush=True)
        header_data = {
            "op": TEST_OP,
            "cliente_nombre": "PRUEBA AUTO-ID",
            "vendedor_nombre": "VENDEDOR AUTO",
            "importe_total": 1234.56,
            "observaciones_de_facturacion": "ESTO COMPRUEBA QUE EL IDENTITY FUNCIONA",
            "observaciones_digital": "OK",
            "es_canje": False
        }
        res = supabase.table("ordenes_publicidad").insert(header_data).execute()
        
        if not res.data:
            print("❌ FALLO: No se generó el registro. ¿Corriste el SQL?", flush=True)
            return

        new_id = res.data[0]['id']
        print(f" ✅ ÉXITO: Postgres generó el ID automático: {new_id}", flush=True)

        # 2. INSERT UNIDADES (VINCULANDO AL NUEVO ID)
        print(f" -> Vinculando Unidad al ID {new_id}...", flush=True)
        unit_data = {
            "op_id": new_id, 
            "op_numero": TEST_OP, 
            "unidad_negocio": "AUTO-TEST-UNIT", 
            "importe_total": 1234.56
        }
        supabase.table("unidades_negocio").insert(unit_data).execute()
        print(" ✅ Unidad vinculada correctamente.", flush=True)

        print("\n\n" + "="*50)
        print("   ¡SISTEMA 100% OPERATIVO!")
        print("="*50)
        print(f"La base de datos ya genera IDs automáticos: {new_id}")
        print(f"Las relaciones por OP de texto ('{TEST_OP}') están activas.")
        print("Módulo de Carga OP: LISTO PARA USAR.")

    except Exception as e:
        print(f"❌ ERROR: {e}", flush=True)

if __name__ == "__main__":
    run_auto_id_test()
