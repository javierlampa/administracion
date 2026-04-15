import psycopg2
import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

project_ref = "ehodsnqdspswuzzdsgoe"
user = "postgres"
password_raw = "dsP3026x&&&"
password = urllib.parse.quote_plus(password_raw)

# Try direct database port 5432 on db.[project_ref].supabase.co
host = f"db.{project_ref}.supabase.co"
port = "5432"
dbname = "postgres"

db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

try:
    print(f"Connecting to {host}:{port} directly...")
    conn = psycopg2.connect(db_url, connect_timeout=15)
    cur = conn.cursor()
    
    with open("17_RLS_PERFILES.sql", "r", encoding="utf-8") as f:
        sql = f.read()
        
    cur.execute(sql)
    conn.commit()
    print("✅ RLS policies applied successfully!")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Direct Connection Error: {e}")
