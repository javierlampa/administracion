"""
Borra directamente el registro fantasma id=103871 (sp_id=NULL, op=7605)
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Borrar todos los registros con sp_id = NULL (fantasmas pre-espejo)
res_count = supabase.table('pagos').select('id, op_numero', count='exact').is_('sp_id', 'null').execute()
print(f"Fantasmas con sp_id=NULL: {res_count.count}")
for r in res_count.data:
    print(f"  -> id={r['id']} | op={r['op_numero']}")

supabase.table('pagos').delete().is_('sp_id', 'null').execute()
print(f"✅ Borrados {res_count.count} registros fantasma sin sp_id.")

# Verificar la 7605 ahora
res = supabase.table('pagos').select('id, sp_id, op_numero').eq('op_numero', '7605').execute()
print(f"\n✅ OP 7605 ahora tiene {len(res.data)} registro(s): {res.data}")
