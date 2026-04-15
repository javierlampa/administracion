import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('f:/JAVIER PRIVADO/APP PHYTON/ADMINISTRACION/.env')

# Supabase URL structure might be configured differently, checking if SUPABASE_DB_URL is present
db_url = os.getenv('SUPABASE_DB_URL')
if not db_url:
    print("SUPABASE_DB_URL not found in .env")
    exit(1)

with open('f:/JAVIER PRIVADO/APP PHYTON/ADMINISTRACION/20_KPI_EVOLUCION_PROGRAMA_RPC.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()
cur.execute(sql)
cur.close()
conn.close()
print("SQL Executed successfully!")
