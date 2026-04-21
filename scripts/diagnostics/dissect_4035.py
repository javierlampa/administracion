import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def dissect_4035():
    # 1. Ver en Maestra
    res_m = supabase.table('ordenes_publicidad').select('id, op').eq('op', '4035').execute()
    if res_m.data:
        op_m = res_m.data[0]['op']
        print(f"Maestra (ID {res_m.data[0]['id']}): '{op_m}' | Tipo: {type(op_m)} | Hex: {op_m.encode().hex() if isinstance(op_m, str) else 'N/A'}")
    else:
        print("❌ No encontré la OP 4035 en la Maestra por coincidencia exacta.")

    # 2. Ver en Unidad de Negocio
    res_un = supabase.table('unidades_negocio').select('id, op_numero').eq('op_numero', '4035').execute()
    if res_un.data:
        op_un = res_un.data[0]['op_numero']
        print(f"Unidad (ID {res_un.data[0]['id']}): '{op_un}' | Tipo: {type(op_un)} | Hex: {op_un.encode().hex() if isinstance(op_un, str) else 'N/A'}")
    else:
        print("❌ No encontré la OP 4035 en Unidades por coincidencia exacta.")

if __name__ == "__main__":
    dissect_4035()
