import os
import psycopg2
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

user = "postgres.ehodsnqdspswuzzdsgoe"
pw = "dsP3026x&&&"
host = "aws-0-us-east-1.pooler.supabase.com"
port = "6543"
dbname = "postgres"

# Escapar password por si acaso
pw_escaped = urllib.parse.quote_plus(pw)
db_url = f"postgresql://{user}:{pw_escaped}@{host}:{port}/{dbname}"

print(f"Connecting to pooler...")
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    with open('database/sql/21_FIX_UNIQUE_CONSTRAINTS.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
        
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    print("SUCCESS: Unique constraints dropped for TV.")
except Exception as e:
    print(f"ERROR: {str(e)}")
