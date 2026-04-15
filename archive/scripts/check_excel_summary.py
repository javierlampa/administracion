import pandas as pd

try:
    df = pd.read_excel('csv/tv1.xlsx')
    print("--- RESUMEN DEL EXCEL ---")
    print(f"Columnas: {df.columns.tolist()}")
    print(f"Total registros: {len(df)}")
    
    # Detectar importe
    importe_col = next((c for c in df.columns if 'Importe' in c), None)
    if importe_col:
        print(f"SUM:{df[importe_col].sum()}")
    
    print(f"COLS:{df.columns.tolist()}")
    print(f"ROWS:{len(df)}")

except Exception as e:
    print("Error al leer Excel:", e)
