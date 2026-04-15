import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# SUPABASE_DB_URL=postgresql://postgres.ehodsnqdspswuzzdsgoe:dsP3026x&&&@aws-0-us-east-1.pooler.supabase.com:6543/postgres
# Direct connection string
user = "postgres"
password = "dsP3026x&&&"
host = "db.ehodsnqdspswuzzdsgoe.supabase.co"
port = 5432
dbname = "postgres"

try:
    print(f"Connecting to {host}:{port} as {user}...")
    conn = psycopg2.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        dbname=dbname,
        connect_timeout=15
    )
    cur = conn.cursor()
    
    with open("16_DAILY_GRID_RPC.sql", "r", encoding="utf-8") as f:
        sql = f.read()
        
    cur.execute(sql)
    conn.commit()
    print("✅ SQL Monitoring Function applied successfully via Direct Connection!")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Direct Connection Error: {e}")
