import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path='f:\\JAVIER PRIVADO\\APP PHYTON\\ADMINISTRACION\\.env')
# Reemplazar 6543 por 5432 para conexión directa
db_url = os.getenv('SUPABASE_DB_URL')
if not db_url:
    print("Error: SUPABASE_DB_URL no encontrado en .env")
    exit(1)

# Asegurarnos de usar 5432 y desactivar pgbouncer param
db_url = db_url.replace(':6543', ':5432').replace('?pgbouncer=true', '')

sql_file = 'f:\\JAVIER PRIVADO\\APP PHYTON\\ADMINISTRACION\\database\\sql\\20_KPI_EVOLUCION_PROGRAMA_RPC.sql'
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_text = f.read()

try:
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(sql_text)
    print("✅ RPC Actualizado correctamente en Supabase!")
    conn.close()
except Exception as e:
    print("Error al aplicar SQL:", e)
