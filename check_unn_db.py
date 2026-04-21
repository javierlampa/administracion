import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv('SUPABASE_DB_URL')

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Ver constraints
    cur.execute("""
        SELECT conname, pg_get_constraintdef(oid) 
        FROM pg_constraint 
        WHERE conrelid = 'unidades_negocio'::regclass;
    """)
    print("Constraints en unidades_negocio:")
    for row in cur.fetchall():
        print(f" - {row[0]}: {row[1]}")
    
    # Ver indices unicos
    cur.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'unidades_negocio' AND indexdef LIKE '%UNIQUE%';
    """)
    print("\nIndices UNICOS en unidades_negocio:")
    for row in cur.fetchall():
        print(f" - {row[0]}: {row[1]}")

    cur.close()
    conn.close()
except Exception as e:
    print(f"ERROR: {str(e)}")
