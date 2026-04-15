import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

try:
    print("Analizando Canjes en tvtodas.xlsx...")
    df = pd.read_excel('csv/tvtodas.xlsx')
    
    # Necesitamos las fechas de las órdenes para filtrar 2026
    # Como el Excel no tiene fecha, usamos las OPs del Portal que sabemos son 2026
    res = supabase.table('v_todas_las_op_report').select('op').gte('fecha_orden', '2026-01-01').lte('fecha_orden', '2026-04-14').execute()
    ops_2026 = set(str(r['op']).strip() for r in res.data)
    
    df['OP'] = df['OP_TP'].astype(str).str.split('.').str[0].str.strip()
    df_2026 = df[df['OP'].isin(ops_2026)].copy()
    
    # Buscar columna Canje (con espacio al final según vimos antes)
    canje_col = next((c for c in df.columns if 'Canje' in c), 'Canje ')
    importe_col = next((c for c in df.columns if 'Importe' in c), 'Importe Total')
    
    # Ver valores posibles en columna Canje
    print(f"Valores en columna '{canje_col}':", df_2026[canje_col].unique())
    
    canjes = df_2026[df_2026[canje_col].astype(str).str.lower().isin(['sí', 'si', 's', 'true', '1'])]
    total_canje = canjes[importe_col].sum()
    
    print(f"\nCanjes encontrados en 2026: {len(canjes)}")
    print(f"SUMA TOTAL CANJES: {total_canje:,.2f}")
    
    print(f"\nDiferencia que buscamos: 1,933,500.00")
    
    if len(canjes) > 0:
        print("\nEjemplos de Canjes:")
        for _, r in canjes.head(10).iterrows():
            print(f" - OP {r['OP']} | Importe: {r[importe_col]:,.2f}")

except Exception as e:
    print("Error:", e)
