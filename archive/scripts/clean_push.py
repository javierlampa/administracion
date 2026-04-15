import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Cargar archivos
df_u = pd.read_excel('csv/unn.xlsx')
df_e = pd.read_excel('csv/enero .xlsx')
df_f = pd.read_excel('csv/febrero.xlsx')

# Limpiar df_u
df_u['op'] = df_u['OP_UNN'].astype(str).str.split('.').str[0].str.strip()
df_u['un'] = df_u['Unidad de Negocio'].astype(str).str.strip()
df_u['val'] = pd.to_numeric(df_u['Importe Total'], errors='coerce')
df_u = df_u[['op', 'un', 'val']].dropna(subset=['val'])

# Limpiar df_e y df_f
for dfx in [df_e, df_f]:
    dfx['op'] = dfx['OP_UNN'].fillna(dfx['OP']).astype(str).str.split('.').str[0].str.strip()
    dfx['un'] = dfx['Unidad de negocio'].astype(str).str.strip()
    dfx['val'] = pd.to_numeric(dfx['UN Importe Total'].astype(str).str.replace(',','.'), errors='coerce')

df_e_clean = df_e[['op', 'un', 'val']].dropna(subset=['val'])
df_f_clean = df_f[['op', 'un', 'val']].dropna(subset=['val'])

# CONSOLIDAR: Priorizar energia y febrero, sino usar unn.xlsx
df_all = pd.concat([df_e_clean, df_f_clean, df_u])

# IMPORTANTE: Remover filas de df_u que ya están cubiertas por los archivos más específicos (Enero/Febrero)
# Usando op y unidad de negocio como clave única, manteniendo el primero (que es el de los archivos mensuales)
df_final = df_all.drop_duplicates(subset=['op', 'un'], keep='first')

# Sumar totales a ver si coinciden con PowerBI (Enero = $48.562k, Febrero = $58.524k o 59.665k)
# Como no tenemos mes aquí, dependemos del cruce con órdenes, pero solo mandamos lo limpio.
print(f"Total registros únicos listos para Supabase: {len(df_final)}")

# Insertar todos
print("Subiendo...")
for _, r in df_final.iterrows():
    try:
        if float(r['val']) > 0:
            payload = {
                'op_numero': r['op'],
                'unidad_negocio': r['un'],
                'importe_total': float(r['val'])
            }
            supabase.table('unidades_negocio').upsert(payload, on_conflict='op_id, unidad_negocio').execute()
    except Exception as e:
        pass

print("Carga lista y des-duplicada.")
