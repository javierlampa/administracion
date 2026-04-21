import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# From .env: postgresql://postgres.ehodsnqdspswuzzdsgoe:dsP3026x&&&@aws-0-us-east-1.pooler.supabase.com:6543/postgres
user = "postgres.ehodsnqdspswuzzdsgoe"
password = "dsP3026x&&&"
host = "aws-0-us-east-1.pooler.supabase.com"
port = "6543"
dbname = "postgres"

SQL_FILE = "database/sql/repair_saldo_logic.sql"

def apply_sql():
    try:
        # Construct DSN manually to avoid URL parsing issues
        dsn = f"host={host} port={port} dbname={dbname} user={user} password={password}"
        print(f"Connecting to database...")
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print(f"Executing SQL...")
        cur.execute(sql)
        conn.commit()
        
        print("✅ SQL applied successfully!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error applying SQL: {e}")

if __name__ == "__main__":
    apply_sql()
