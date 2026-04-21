import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cur = conn.cursor()

print("Inspeccionando tabla 'unidades_negocio':")
cur.execute("""
    SELECT
        conname as constraint_name,
        pg_get_constraintdef(c.oid) as constraint_definition
    FROM pg_constraint c
    JOIN pg_class t ON c.conrelid = t.oid
    WHERE t.relname = 'unidades_negocio';
""")
for row in cur.fetchall():
    print(f"Constraint: {row[0]} | Def: {row[1]}")

cur.close()
conn.close()
