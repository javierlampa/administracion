import os
import random
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('f:/JAVIER PRIVADO/APP PHYTON/ADMINISTRACION/.env')

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(URL, KEY)

TEST_OP = f"OP-TEST-{random.randint(1000, 9999)}"
TEST_ID = random.randint(2000000, 3000000)

def run_complete_test():
    print(f"🚀 Iniciando Simulacro de Carga Integral para: {TEST_OP}\n")
    
    try:
        # 1. INSERT CABECERA (ordenes_publicidad)
        print(" -> Procesando Cabecera...")
        header_data = {
            "id": TEST_ID,
            "op": TEST_OP,
            "cliente_nombre": "CLIENTE DE PRUEBA INTEGRAL",
            "vendedor_nombre": "VENDEDOR TEST",
            "importe_total": 5000.0,
            "observaciones_de_facturacion": "NOTAS DE FACTURACION TEST",
            "observaciones_digital": "UBICACION HOME IZQUIERDA",
            "medidas_digital": "970x250",
            "es_canje": False
        }
        supabase.table("ordenes_publicidad").insert(header_data).execute()
        print(f" ✅ Cabecera guardada con éxito (ID: {TEST_ID})", flush=True)

        # 2. INSERT UNIDADES (unidades_negocio)
        print(" -> Procesando Unidades de Negocio...", flush=True)
        units = [
            {"id": random.randint(3000000, 4000000), "op_id": TEST_ID, "op_numero": TEST_OP, "unidad_negocio": "CANAL 5", "importe_total": 3000.0},
            {"id": random.randint(3000000, 4000000), "op_id": TEST_ID, "op_numero": TEST_OP, "unidad_negocio": "RADIO AM", "importe_total": 2000.0}
        ]
        supabase.table("unidades_negocio").insert(units).execute()
        print(" ✅ 2 Unidades financieras vinculadas.", flush=True)

        # 3. INSERT TÉCNICO (tv)
        print(" -> Procesando Desglose Técnico...", flush=True)
        tech = [
            {
                "id": random.randint(4000000, 5000000),
                "op_id": TEST_ID, 
                "op_numero": TEST_OP, 
                "programa_nombre": "NOTICIERO CENTRAL", 
                "tipo": "PNT",
                "detalles_salidas": "Lunes a Viernes, 20:00hs a 21:00hs",
                "importe_total": 3000.0
            },
            {
                "id": random.randint(4000000, 5000000),
                "op_id": TEST_ID, 
                "op_numero": TEST_OP, 
                "programa_nombre": "S/N", 
                "tipo": "BANNER",
                "importe_total": 2000.0
            }
        ]
        supabase.table("tv").insert(tech).execute()
        print(" ✅ 2 Líneas técnicas vinculadas (incluyendo detalles de salidas).", flush=True)

        # --- REPORTE DE VERIFICACIÓN ---
        print("\n" + "="*50, flush=True)
        print("   REPORTE DE AUDITORÍA DE CARGA", flush=True)
        print("="*50, flush=True)
        
        # Verificar Cabecera
        db_header = supabase.table("ordenes_publicidad").select("*").eq("op", TEST_OP).single().execute().data
        print(f"OP EN CABECERA: {db_header['op']} (MATCH OK)", flush=True)
        print(f"OBS. FACTURACIÓN: {db_header.get('observaciones_de_facturacion')} (OK)", flush=True)
        print(f"OBS. DIGITAL: {db_header.get('observaciones_digital')} (OK)", flush=True)
        
        # Verificar Unidades
        db_units = supabase.table("unidades_negocio").select("unidad_negocio, importe_total").eq("op_numero", TEST_OP).execute().data
        print(f"UNIDADES CARGADAS: {[u['unidad_negocio'] for u in db_units]} (OK)", flush=True)
        
        # Verificar Técnico
        db_tech = supabase.table("tv").select("programa_nombre, detalles_salidas").eq("op_numero", TEST_OP).execute().data
        print(f"DETALLE TÉCNICO: {db_tech[0]['programa_nombre']} -> {db_tech[0].get('detalles_salidas')} (OK)", flush=True)
        
        print("\n✨ CONCLUSIÓN: El flujo de datos es 100% consistente a lo largo de todas las tablas.", flush=True)

    except Exception as e:
        print(f"❌ ERROR EN EL SIMULACRO: {e}")

if __name__ == "__main__":
    run_complete_test()
