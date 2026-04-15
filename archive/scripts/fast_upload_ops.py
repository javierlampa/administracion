import pandas as pd
from supabase import create_client
import os
import math
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("Sincronizando tabla maestra de orden_publicidad desde CSV local...")
df_o = pd.read_csv('csv/Orden de Publicidad (4).csv')

records = []
for _, r in df_o.iterrows():
    try:
        op = str(r['OP']).split('.')[0].strip()
        if op == 'nan' or not op: continue
        
        fecha = pd.to_datetime(r['Fecha de la Orden'], dayfirst=True, errors='coerce')
        if pd.isna(fecha): continue
        
        importe = str(r['Importe Total']).replace('.', '').replace(',', '.')
        try:
            val = float(importe)
            if math.isnan(val): val = 0.0
        except:
            val = 0.0
            
        records.append({
            'op': op,
            'fecha_orden': fecha.strftime('%Y-%m-%d'),
            'importe_total': val,
            'empresa': str(r['Empresa']) if pd.notna(r['Empresa']) else 'Todas'
        })
    except Exception as e:
        pass

print(f"Total OPs en CSV listas para upload: {len(records)}")

batch_size = 500
for i in range(0, len(records), batch_size):
    batch = records[i:i + batch_size]
    try:
        supabase.table('ordenes_publicidad').upsert(batch, on_conflict='op').execute()
        print(f"Insertados {min(i + batch_size, len(records))}")
    except Exception as e:
        print("Error lote:", e)

print("Carga de base Maestra completada.")
