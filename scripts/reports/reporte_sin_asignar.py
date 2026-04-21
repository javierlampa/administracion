import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def show_unnamed():
    res = supabase.table('unidades_negocio').select('op_numero, importe_total, unidad_negocio').is_('unidad_negocio', 'null').execute()
    data = res.data or []
    
    print("\n--- UNIDADES SIN ASIGNAR (Falta nombre en SharePoint) ---")
    total_importe = 0
    for r in data:
        print(f"- OP: {r['op_numero']:<15} | Importe: ${float(r['importe_total']):,.2f}")
        total_importe += float(r['importe_total'])
    
    print(f"\nTOTAL 'SIN ASIGNAR': ${total_importe:,.2f}")
    print(f"Cantidad de registros afectados: {len(data)}")

if __name__ == "__main__":
    show_unnamed()
