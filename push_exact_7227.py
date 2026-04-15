import os
from supabase import create_client
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("Vaciando tabla de unidades_negocio...")
deleted = 0
while True:
    res = supabase.table('unidades_negocio').select('id').limit(1000).execute()
    if not res.data: break
    ids = [r['id'] for r in res.data]
    supabase.table('unidades_negocio').delete().in_('id', ids).execute()
    deleted += len(ids)

print(f"Limpieza lista. Borrados {deleted} registros.")

print("Cargando exactamente los registros de unn.xlsx...")
df_u = pd.read_excel('csv/unn.xlsx')

records = []
for idx, r in df_u.iterrows():
    val_str = str(r['Importe Total']).replace(',','.')
    try:
        val = float(val_str)
    except:
        val = 0.0

    op = str(r['OP_UNN']).split('.')[0].strip()
    un = str(r['Unidad de Negocio']).strip()
    
    # Queremos EXACTAMENTE el mismo número de filas que tiene el Excel si la OP tiene valor
    records.append({
        'op_numero': op,
        'unidad_negocio': un,
        'importe_total': val
    })

print(f"Total a inyectar directo (Sin deduplicar): {len(records)}")

batch_size = 500
for i in range(0, len(records), batch_size):
    batch = records[i:i + batch_size]
    # Insert simple en lote, no upsert para forzar la inyeccion pura de las 7227
    supabase.table('unidades_negocio').insert(batch).execute()
    print(f"Progreso: {min(i + batch_size, len(records))} / {len(records)}")

print("Tabla restaurada al calco exacto de SharePoint (7227).")
