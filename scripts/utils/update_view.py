import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

sql = """
DROP VIEW IF EXISTS v_comisiones_report CASCADE;

CREATE OR REPLACE VIEW v_comisiones_report AS
SELECT 
    p.id AS pago_id,
    p.op_numero AS op,
    o.numero_factura,
    p.vendedor,
    o.cliente_nombre AS cliente_nombre_comercial,
    c.razon_social AS cliente_razon_social,
    o.fecha_orden,
    p.fecha_pago,
    p.importe_pago,
    p.total_sin_iva,
    p.comision,
    p.importe_comision,
    p.esta_liquidado,
    p.fecha_liquidacion,
    o.empresa AS empresa_op,
    o.importe_total AS importe_orden
FROM pagos p
LEFT JOIN ordenes_publicidad o ON (p.op_numero = o.op)
LEFT JOIN clientes c ON o.cliente_id = c.id;
"""

# Usamos RPC para ejecutar SQL si existe, o informamos
try:
    res = supabase.rpc("exec_sql", {"sql_query": sql}).execute()
    print("View updated successfully.")
except Exception as e:
    print(f"Error updating view: {e}")
    print("Please run the SQL manually in Supabase SQL Editor if exec_sql is not available.")
