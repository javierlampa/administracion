import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Conexión DIRECTA (Bypassing the Pooler 6543)
# Host: db.[ProjectID].supabase.co
# Port: 5432
# User: postgres (just postgres for direct connection)
# Password: dsP3026x&&&

def apply_sql(filename):
    try:
        print(f"Applying {filename} via DIRECT Connection (Port 5432)...")
        conn = psycopg2.connect(
            user="postgres",
            password="dsP3026x&&&",
            host="db.ehodsnqdspswuzzdsgoe.supabase.co",
            port=5432,
            dbname="postgres",
            connect_timeout=15
        )
        cur = conn.cursor()
        with open(filename, "r", encoding="utf-8") as f:
            sql = f.read()
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ {filename} applied.")
        return True
    except Exception as e:
        print(f"❌ Error in {filename}: {e}")
        return False

if __name__ == "__main__":
    r1 = apply_sql("18_REFIX_VIEW_REPORT.sql")
    r2 = apply_sql("12_KPI_EVOLUCION_TC_RPC.sql")
    if r1 and r2:
        print("🎉 All fixes applied successfully!")
