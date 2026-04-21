import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('SUPABASE_DB_URL')

def check_sums():
    # Nos conectamos directamente por SQL que es más rápido y certero
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    print("--- INFORME DE DISCREPANCIA (TV vs OP) ---")
    
    # query 1: OPs que tienen múltiples bloques de TV con el MISMO importe total que la OP
    query = """
    SELECT 
        o.op,
        o.importe_total AS op_total,
        COUNT(t.id) as cantidad_bloques,
        SUM(t.importe_total) as tv_sum,
        MAX(t.importe_total) as tv_max
    FROM ordenes_publicidad o
    JOIN tv t ON t.op_id = o.id
    WHERE o.fecha_orden BETWEEN '2026-01-01' AND '2026-04-18'
    GROUP BY o.op, o.importe_total
    HAVING SUM(t.importe_total) > o.importe_total
    ORDER BY (SUM(t.importe_total) - o.importe_total) DESC
    LIMIT 10;
    """
    cur.execute(query)
    rows = cur.fetchall()
    
    print("\nEjemplo de OPs donde la suma de TV es mayor al Total de OP:")
    print(f"{'OP':<10} | {'Total OP':<15} | {'Cant. Bloques':<15} | {'Suma TV':<15} | {'Max Importe TV':<15}")
    print("-" * 75)
    for r in rows:
        print(f"{r[0]:<10} | ${float(r[1]):<14,.2f} | {r[2]:<15} | ${float(r[3]):<14,.2f} | ${float(r[4]):<14,.2f}")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_sums()
