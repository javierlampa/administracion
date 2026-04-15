import os
import pandas as pd
from dotenv import load_dotenv
import psycopg2

load_dotenv()
conn = psycopg2.connect(os.getenv('SUPABASE_DB_URL'))

query = """
    WITH base_ops AS (
        SELECT 
            COALESCE(NULLIF(TRIM(t.programa_nombre), ''), '(En blanco)') AS un,
            COALESCE(t.importe_total, 0) AS importe
        FROM v_todas_las_op_report o
        JOIN tv t ON t.op_id = o.id
        WHERE o.estado IS DISTINCT FROM 'Anulada'
          AND o.estado IS DISTINCT FROM 'Baja'
          AND o.fecha_orden BETWEEN '2026-01-01' AND '2026-04-14'
          AND o.empresa = 'Telesol'
    )
    SELECT un as programa_nombre, SUM(importe) as total FROM base_ops GROUP BY un
"""
df_db = pd.read_sql_query(query, conn)
conn.close()

df_csv = pd.read_excel('csv/tv.xlsx')
print("Columnas del Excel:", df_csv.columns.tolist())

# Asumimos que tiene "Programas." y "Suma de Importe Total"
# O similar, iteramos primeras filas
print(df_csv.head(5))

# Asegúrate de limpiar los nombres
if 'Suma de Importe Total' in df_csv.columns and 'Programas.' in df_csv.columns:
    df_csv = df_csv.rename(columns={'Programas.': 'programa_nombre', 'Suma de Importe Total': 'total'})
    
    # Merge y comparar
    merged = pd.merge(df_db, df_csv, on='programa_nombre', suffixes=('_DB', '_Excel'), how='outer')
    merged['total_DB'] = merged['total_DB'].fillna(0)
    merged['total_Excel'] = merged['total_Excel'].fillna(0)
    merged['diff'] = merged['total_DB'] - merged['total_Excel']
    
    differences = merged[abs(merged['diff']) > 1].sort_values('diff', ascending=False)
    
    print("\n--- DIFERENCIAS (DB vs EXCEL) ---")
    print(f"Total DB: {df_db['total'].sum():,.2f}")
    print(f"Total Excel: {df_csv['total'].sum():,.2f}")
    print(differences.to_string())
else:
    print("Las columnas no coinciden con lo esperado. Usa los nombres de arriba.")
