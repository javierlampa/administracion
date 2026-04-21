"""
Arregla el pago sp_id=7257 que quedó guardado como op_numero='7542'
pero en realidad corresponde a la OP '7191' de SharePoint.
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Primero verificamos el estado actual
res = supabase.table('pagos').select('id, sp_id, op_numero, comision, importe_comision').eq('sp_id', 7257).execute()
print(f"Estado actual: {res.data}")

# Actualizamos op_numero de '7542' a '7191'
res_update = supabase.table('pagos').update({'op_numero': '7191'}).eq('sp_id', 7257).execute()
print(f"Actualizado: {res_update.data}")

# Verificamos
res_check = supabase.table('pagos').select('id, sp_id, op_numero, comision, importe_comision').eq('sp_id', 7257).execute()
print(f"Resultado final: {res_check.data}")
