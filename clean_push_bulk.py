import pandas as pd
from supabase import create_client
import os
import math
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

df_u = pd.read_excel('csv/unn.xlsx')
df_e = pd.read_excel('csv/enero .xlsx')
df_f = pd.read_excel('csv/febrero.xlsx')

df_u['op'] = df_u['OP_UNN'].astype(str).str.split('.').str[0].str.strip()
df_u['un'] = df_u['Unidad de Negocio'].astype(str).str.strip()
df_u['val'] = pd.to_numeric(df_u['Importe Total'], errors='coerce')
df_u = df_u[['op', 'un', 'val']].dropna(subset=['val'])

for dfx in [df_e, df_f]:
    dfx['op'] = dfx['OP_UNN'].fillna(dfx['OP']).astype(str).str.split('.').str[0].str.strip()
    dfx['un'] = dfx['Unidad de negocio'].astype(str).str.strip()
    dfx['val'] = pd.to_numeric(dfx['UN Importe Total'].astype(str).str.replace(',','.'), errors='coerce')

df_e_clean = df_e[['op', 'un', 'val']].dropna(subset=['val'])
df_f_clean = df_f[['op', 'un', 'val']].dropna(subset=['val'])

df_all = pd.concat([df_e_clean, df_f_clean, df_u])
df_final = df_all.drop_duplicates(subset=['op', 'un'], keep='first')

records = []
for _, r in df_final.iterrows():
    if pd.notna(r['val']) and float(r['val']) > 0 and str(r['un']).lower() != 'nan':
        records.append({
            'op_numero': str(r['op']),
            'unidad_negocio': str(r['un']),
            'importe_total': float(r['val'])
        })

print(f"Total registros únicos listos y limpios: {len(records)}")

batch_size = 500
for i in range(0, len(records), batch_size):
    batch = records[i:i + batch_size]
    try:
        supabase.table('unidades_negocio').upsert(batch, on_conflict='op_id, unidad_negocio').execute()
        print(f"Lote insertado: {min(i + batch_size, len(records))} / {len(records)}")
    except Exception as e:
        print(f"Error en batch {i}: {e}")

print("Terminado.")
