import os
from whatsapp_bot import generar_reporte_pdf
import base64

def test():
    print("Iniciando prueba de generacion de PDF...")
    try:
        # Intentar generar para CAFE AMERICA
        print("Llamando a generar_reporte_pdf('CAFE AMERICA')...")
        result = generar_reporte_pdf("CAFE AMERICA")
        
        if not result:
            print("ERROR: El resultado es nulo")
            return

        if result.startswith("Error"):
            print(f"ERROR devuelto por el bot: {result}")
            return

        if len(result) < 100:
            print(f"AVISO: El resultado es muy corto, podria no ser un PDF valido: {result}")
            
        try:
            # Intentar decodificar
            pdf_bytes = base64.b64decode(result)
            # Guardar localmente
            with open("test_reporte.pdf", "wb") as f:
                f.write(pdf_bytes)
            print(f"EXITO: PDF generado exitosamente en 'test_reporte.pdf' ({len(pdf_bytes)} bytes)")
        except Exception as b64err:
            print(f"ERROR al decodificar base64: {b64err}")
            print(f"Primeros 100 caracteres del resultado: {result[:100]}")
        
    except Exception as e:
        print(f"ERROR FATAL en la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
