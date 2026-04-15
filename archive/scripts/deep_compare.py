import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

try:
    # 1. Leer Excel Maestro (TV completas de SharePoint)
    print("Leyendo tvtodas.xlsx...")
    df_master = pd.read_excel('csv/tvtodas.xlsx')
    # Limpiar OPs y montos
    # El usuario dice que se llama OP_TP
    df_master['OP'] = df_master['OP_TP'].astype(str).str.split('.').str[0].str.strip()
    # Buscar el nombre de la columna de importe si no es exacto
    importe_col = next((c for c in df_master.columns if 'Importe' in c), 'Importe Total')
    df_master['Importe Total'] = df_master[importe_col].fillna(0).astype(float)
    
    master_dict = {} # (OP, Importe) -> Count
    for _, row in df_master.iterrows():
        key = (row['OP'], round(row['Importe Total'], 2))
        master_dict[key] = master_dict.get(key, 0) + 1
    
    print(f"Total registros en Excel Maestro: {len(df_master)}")

    # 2. Leer Supabase (Tabla TV completa)
    print("Leyendo tabla TV de Supabase...")
    db_data = []
    limit = 1000
    offset = 0
    while True:
        res = supabase.table('tv').select('op_numero, importe_total, programa_nombre').range(offset, offset + limit - 1).execute()
        if not res.data:
            break
        db_data.extend(res.data)
        offset += limit
    print(f"Total registros en Supabase: {len(db_data)}")

    # 3. Comparar
    print("\n--- REGISTROS EN SUPABASE QUE NO ESTÁN EN EL EXCEL ---")
    count_missing = 0
    total_missing_money = 0
    
    # Hacemos una copia del dict para ir restando y ver qué sobra
    temp_master = master_dict.copy()
    
    for row in db_data:
        op = str(row['op_numero']).strip()
        imp = round(float(row['importe_total'] or 0), 2)
        key = (op, imp)
        
        if temp_master.get(key, 0) > 0:
            temp_master[key] -= 1
        else:
            # Este registro sobra en Supabase
            count_missing += 1
            total_missing_money += imp
            if count_missing <= 20: # Limitar el log
                print(f" (!) SOBRA EN DB: OP {op} | Monto: {imp:,.2f} | Programa: {row['programa_nombre']}")
    
    print(f"\nTotal registros sobrantes en la DB: {count_missing}")
    print(f"SUMA TOTAL QUE SOBRA: {total_missing_money:,.2f}")

except Exception as e:
    print("Error:", e)
