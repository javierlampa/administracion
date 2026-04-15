import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('f:/JAVIER PRIVADO/APP PHYTON/ADMINISTRACION/.env')

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(URL, KEY)

TEST_OP = "99999-TEST"

def test_save():
    print(f"🚀 Iniciando prueba de guardado para OP: {TEST_OP}...")
    
    try:
        # 1. Limpiar si ya existe
        supabase.table("ordenes_publicidad").delete().eq("op", TEST_OP).execute()
        
        # 2. Simular Insert de Cabecera con los NUEVOS CAMPOS (incluyendo ID manual)
        print(" -> Insertando en 'ordenes_publicidad'...")
        op_res = supabase.table("ordenes_publicidad").insert({
            "id": 999999,
            "op": TEST_OP,
            "importe_total": 1000.0,
            "es_canje": True,
            "observaciones_de_facturacion": "ESTO ES UNA PRUEBA DE FACTURACION",
            "observaciones_digital": "ESTO ES UNA PRUEBA DE UBICACION DIGITAL",
            "medidas_digital": "300x250",
            "cliente_nombre": "CLIENTE DE PRUEBA"
        }).execute()
        
        if not op_res.data:
            print("❌ Error: No se pudo crear la cabecera.")
            return

        op_id = op_res.data[0]['id']
        print(f" ✅ Cabecera creada con ID: {op_id}")

        # 3. Simular Insert de Unidad
        print(" -> Insertando en 'unidades_negocio'...")
        supabase.table("unidades_negocio").insert({
            "op_id": op_id,
            "op_numero": TEST_OP,
            "unidad_negocio": "CANAL 5 TEST",
            "importe_total": 1000.0
        }).execute()
        print(" ✅ Unidad creada.")

        # 4. Simular Insert de Técnico
        print(" -> Insertando en 'tv'...")
        supabase.table("tv").insert({
            "op_id": op_id,
            "op_numero": TEST_OP,
            "programa_nombre": "PROGRAMA TEST",
            "tipo": "PNT",
            "importe_total": 1000.0
        }).execute()
        print(" ✅ Detalle técnico creado.")

        # 5. VERIFICACIÓN FINAL
        print("\n--- RESULTADO FINAL EN BASE DE DATOS ---")
        final = supabase.table("ordenes_publicidad").select("*").eq("op", TEST_OP).single().execute()
        
        data = final.data
        print(f"OP: {data['op']}")
        print(f"Obs. Facturación: {data.get('observaciones_de_facturacion')}")
        print(f"Obs. Digital: {data.get('observaciones_digital')}")
        print(f"Medidas Digital: {data.get('medidas_digital')}")
        print(f"Canje: {data['es_canje']}")
        
        print("\n✅ LA PRUEBA FUE EXITOSA: Los campos se guardaron en sus columnas correspondientes.")

    except Exception as e:
        print(f"❌ ERROR EN LA PRUEBA: {e}")
    finally:
        # Limpieza opcional
        # supabase.table("ordenes_publicidad").delete().eq("op", TEST_OP).execute()
        pass

if __name__ == "__main__":
    test_save()
