import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv('SUPABASE_DB_URL')

try:
    with open('20_KPI_EVOLUCION_PROGRAMA_RPC.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    print("SUCCESS: SQL applied successfully to Supabase.")
except Exception as e:
    print(f"ERROR: {str(e)}")
