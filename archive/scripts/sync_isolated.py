import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

archivos = ['csv/enero .xlsx', 'csv/febrero.xlsx']
insertados_un = 0
insertados_op = 0

for arc in archivos:
    print(f"Procesando {arc}...")
    df = pd.read_excel(arc)
    
    # Rellenar valores vacíos inteligentemente
    df['OP'] = df['OP'].astype(str).str.strip()
    df['OP_UN'] = df['OP_UNN'].fillna(df['OP']).astype(str).str.strip()
    
    for _, r in df.iterrows():
        try:
            op_limpio = str(r['OP_UN']).split('.')[0].strip()
            op_base = str(r['OP']).split('.')[0].strip()
            
            val = float(str(r['UN Importe Total']).replace(',','.'))
            un_nombre = str(r['Unidad de negocio']).strip()
            
            # --- 1. Sincronizar Orden Maestra (para que haya fecha) ---
            try:
                fecha = pd.to_datetime(r['Fecha de la Orden'], dayfirst=True).strftime('%Y-%m-%d')
            except:
                fecha = None
                
            if op_base and op_base != 'nan' and fecha:
                supabase.table('ordenes_publicidad').upsert({
                    'op': op_base, 
                    'fecha_orden': fecha,
                    'empresa': 'Todas' # Fallback
                }, on_conflict='op').execute()
                insertados_op += 1
            
            # --- 2. Sincronizar Unidad de Negocio (Desglose) ---
            if op_limpio and op_limpio != 'nan' and val > 0:
                payload = {
                    'op_numero': op_base,  # IMPORTANTE: Vincular con la base para que el JOIN funcione
                    'unidad_negocio': un_nombre,
                    'importe_total': val
                }
                supabase.table('unidades_negocio').upsert(payload, on_conflict='op_id, unidad_negocio').execute()
                insertados_un += 1
                
        except Exception as e:
            pass

print(f"Hecho. Modificadas {insertados_op} OPs y {insertados_un} UNs.")
