import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

user = "postgres.ehodsnqdspswuzzdsgoe"
password = "dsP3026x&&&"
host = "aws-0-us-east-1.pooler.supabase.com"
port = 6543
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
    
    with open("14_ADD_EMISSION_FIELDS.sql", "r", encoding="utf-8") as f:
        sql = f.read()
        
    cur.execute(sql)
    conn.commit()
    print("✅ SQL Migration applied successfully!")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Direct Connection Error: {e}")
