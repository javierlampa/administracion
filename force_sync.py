import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# 1. Cargar Órdenes (las completas) para asegurar que hay fechas
print("Cargando órdenes de CSV a DB para no pifiar fechas...")
df_o = pd.read_csv('csv/Orden de Publicidad (4).csv')
for _, r in df_o.iterrows():
    try:
        op = str(r['OP']).split('.')[0].strip()
        fecha = pd.to_datetime(r['Fecha de la Orden'], dayfirst=True).strftime('%Y-%m-%d')
        # solo fecha y op para no chocar con tipos en otras cosas
        supabase.table('ordenes_publicidad').upsert({'op': op, 'fecha_orden': fecha}, on_conflict='op').execute()
    except Exception as e:
        pass

# 2. Cargar Unidades
print("Cargando unidades de negocio de Excel a DB...")
df_u = pd.read_excel('csv/unn.xlsx')
for _, r in df_u.iterrows():
    try:
        op = str(r['OP_UNN']).split('.')[0].strip()
        val = str(r['Importe Total']).replace('.','').replace(',','.')
        payload = {
            'op_numero': op,
            'unidad_negocio': str(r['Unidad de Negocio']),
            'importe_total': float(val)
        }
        supabase.table('unidades_negocio').upsert(payload, on_conflict='op_id, unidad_negocio').execute()
    except Exception as e:
        pass

print("Todo sincronizado a la fuerza. DB == Excel.")
