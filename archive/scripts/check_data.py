import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("SUPABASE_DB_URL")
if not db_url:
    print("Error: SUPABASE_DB_URL not found")
    exit(1)

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Check activo status
    cur.execute("SELECT COUNT(*), activo FROM ordenes_publicidad GROUP BY activo")
    print('Activo status:', cur.fetchall())
    
    # Check matches for today (ignoring activo)
    target_date = '2026-04-07'
    cur.execute(f"SELECT COUNT(*) FROM ordenes_publicidad WHERE inicio_pauta <= '{target_date}' AND fin_pauta >= '{target_date}'")
    print(f'Matches for {target_date} (ignoring activo):', cur.fetchone()[0])
    
    # Check matches for today (with activo=TRUE)
    cur.execute(f"SELECT COUNT(*) FROM ordenes_publicidad WHERE inicio_pauta <= '{target_date}' AND fin_pauta >= '{target_date}' AND activo = TRUE")
    print(f'Matches for {target_date} (with activo=TRUE):', cur.fetchone()[0])

    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
