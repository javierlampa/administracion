import pandas as pd

try:
    df = pd.read_excel('csv/tv1.xlsx')
    # Buscar columna de canje (puede tener espacios)
    canje_col = next((c for c in df.columns if 'Canje' in c), None)
    
    if canje_col:
        print(f"Columna de canje encontrada: '{canje_col}'")
        # Filtrar por fecha si es posible
        df['Fecha'] = pd.to_datetime(df['Fecha de la Orden'], errors='coerce')
        mask = (df['Fecha'] >= '2026-01-01') & (df['Fecha'] <= '2026-04-14')
        df_2026 = df[mask]
        
        # Ojo: en Excel 'Canje' puede ser 'Sí', 'S', True, 1, etc.
        canjes = df_2026[df_2026[canje_col].astype(str).str.lower().isin(['sí', 'si', 's', 'true', '1', 'yes'])]
        
        print(f"Canjes encontrados en Excel (2026): {len(canjes)}")
        if len(canjes) > 0:
            importe_col = next((c for c in df.columns if 'Importe' in c), None)
            total_canje = canjes[importe_col].sum()
            print(f"SUMA CANJES EXCEL: {total_canje:,.2f}")
            for _, r in canjes.iterrows():
                print(f" - OP {r['OP']}: {r[importe_col]:,.2f}")
    else:
        print("No se encontró columna de Canje en el Excel.")

except Exception as e:
    print("Error:", e)
