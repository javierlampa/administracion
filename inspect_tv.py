import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Conectar via direct postgres para inspeccionar tabla
db_url = os.getenv("DATABASE_URL") # Asumo que existe esta var o usaré los componentes
if not db_url:
    # Construir desde componentes si no existe
    # postgres://[user]:[password]@[host]:[port]/[dbname]
    pass

# Mejor usar psycopg2 con los datos directos
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cur = conn.cursor()

print("Inspeccionando tabla 'tv':")
cur.execute("""
    SELECT
        conname as constraint_name,
        pg_get_constraintdef(c.oid) as constraint_definition
    FROM pg_constraint c
    JOIN pg_class t ON c.conrelid = t.oid
    WHERE t.relname = 'tv';
""")
for row in cur.fetchall():
    print(f"Constraint: {row[0]} | Def: {row[1]}")

cur.execute("SELECT count(*) FROM tv")
print(f"Total registros: {cur.fetchone()[0]}")

cur.close()
conn.close()
