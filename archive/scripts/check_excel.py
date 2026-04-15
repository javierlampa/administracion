import pandas as pd

df = pd.read_excel('csv/tv.xlsx')
print(df.head())

# Limpiar columnas
df['Importe Total'] = pd.to_numeric(df['Importe Total'], errors='coerce').fillna(0)

grouped = df.groupby('Programas.lookupValue', dropna=False)['Importe Total'].sum().reset_index()
grouped = grouped.sort_values('Programas.lookupValue').reset_index(drop=True)

print("--- EXCEL GROUPED ---")
print(grouped)
print("TOTAL:", grouped['Importe Total'].sum())
