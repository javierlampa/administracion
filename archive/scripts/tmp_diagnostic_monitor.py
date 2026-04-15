import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("SUPABASE_DB_URL")

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    target_date = '2026-04-07'
    print(f"--- Diagnostic Report for {target_date} ---")
    
    # 1. Total OPs active in dates
    query1 = f"""
        SELECT COUNT(*) 
        FROM ordenes_publicidad 
        WHERE inicio_pauta <= '{target_date}' AND fin_pauta >= '{target_date}'
    """
    cur.execute(query1)
    total_active = cur.fetchone()[0]
    print(f"Total OPs active in dates (ignoring everything else): {total_active}")
    
    # 2. Total OPs active in dates AND (activo is true or null)
    query2 = f"""
        SELECT COUNT(*) 
        FROM ordenes_publicidad 
        WHERE inicio_pauta <= '{target_date}' AND fin_pauta >= '{target_date}'
        AND (activo = TRUE OR activo IS NULL)
    """
    cur.execute(query2)
    active_with_flag = cur.fetchone()[0]
    print(f"Total OPs active in dates AND (activo is true or null): {active_with_flag}")

    # 3. Join with unidades_negocio
    query3 = f"""
        SELECT COUNT(DISTINCT op.id)
        FROM ordenes_publicidad op
        LEFT JOIN unidades_negocio un ON op.id = un.op_id
        WHERE op.inicio_pauta <= '{target_date}' AND op.fin_pauta >= '{target_date}'
    """
    cur.execute(query3)
    total_with_join = cur.fetchone()[0]
    print(f"Total OPs with join (should match total_active): {total_with_join}")

    # 4. Filtered by 'CANAL TELESOL'
    query4 = f"""
        SELECT COUNT(DISTINCT op.id)
        FROM ordenes_publicidad op
        JOIN unidades_negocio un ON op.id = un.op_id
        WHERE op.inicio_pauta <= '{target_date}' AND op.fin_pauta >= '{target_date}'
        AND un.unidad_negocio = 'CANAL TELESOL'
    """
    cur.execute(query4)
    telesol_active = cur.fetchone()[0]
    print(f"OPs with explicitly assigned 'CANAL TELESOL': {telesol_active}")

    # 5. OPs without ANY unit assigned
    query5 = f"""
        SELECT COUNT(*)
        FROM ordenes_publicidad op
        WHERE inicio_pauta <= '{target_date}' AND fin_pauta >= '{target_date}'
        AND NOT EXISTS (SELECT 1 FROM unidades_negocio un WHERE un.op_id = op.id)
    """
    cur.execute(query5)
    no_unit_active = cur.fetchone()[0]
    print(f"OPs with NO units assigned: {no_unit_active}")

    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
