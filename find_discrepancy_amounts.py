import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def find():
    amounts = [709250, 789000, 79750]
    print(f"Buscando montos: {amounts}")
    
    # Buscamos en ordenes_publicidad
    res = supabase.table('ordenes_publicidad').select('op, importe_total, fecha_orden').execute()
    matches = [r for r in res.data if any(abs(float(r['importe_total'] or 0) - a) < 1 for a in amounts)]
    
    if matches:
        print("\n--- COINCIDENCIAS ENCONTRADAS ---")
        for m in matches:
            print(f"OP: {m['op']} | Monto: {m['importe_total']} | Fecha: {m['fecha_orden']}")
    else:
        print("\nNo se encontraron coincidencias exactas.")

if __name__ == "__main__":
    find()
