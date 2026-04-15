import pandas as pd
import numpy as np

# Cargar archivos
df_app = pd.read_excel('DOCS/app.xlsx')
df_pbi = pd.read_excel('DOCS/powerbi.xlsx')

print("=== COMPARACIÓN BÁSICA ===")
print(f"APP:   {df_app.shape[0]} filas, {df_app.shape[1]} columnas")
print(f"PBI:   {df_pbi.shape[0]} filas, {df_pbi.shape[1]} columnas")
print()

print("=== COLUMNAS APP ===")
print(df_app.columns.tolist())
print("\n=== COLUMNAS PBI ===")
print(df_pbi.columns.tolist())
print()

# Tomamos una muestra de cómo se ve el primer registro en cada uno
print("=== EJEMPLO APP (Fila 1) ===")
print(df_app.head(1).to_dict(orient='records')[0])
print("\n=== EJEMPLO PBI (Fila 1) ===")
print(df_pbi.head(1).to_dict(orient='records')[0])
