import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('SUPABASE_DB_URL')

sql = """
DROP VIEW IF EXISTS v_pagos_resumen CASCADE;

CREATE VIEW v_pagos_resumen AS
SELECT 
    o.id AS op_id,
    o.empresa,
    o.op,
    o.numero_factura,
    o.inicio_pauta,
    o.fin_pauta,
    o.fecha_orden,
    o.cliente_nombre,
    c.razon_social AS cliente_razon_social,
    o.vendedor_nombre,
    COALESCE(o.importe_total, 0) AS importe_total,
    COALESCE(p.total_pago, 0) AS total_pago,
    COALESCE(o.importe_total, 0) - COALESCE(p.total_pago, 0) AS saldo,
    CASE 
        WHEN (COALESCE(o.importe_total, 0) - COALESCE(p.total_pago, 0)) <= 0.01 THEN 'SALDADA'
        ELSE 'PENDIENTE'
    END AS estado_cuenta,
    p.ultima_fecha_pago
FROM ordenes_publicidad o
LEFT JOIN clientes c ON o.cliente_id = c.id
LEFT JOIN (
    SELECT op_id, SUM(importe_pago) AS total_pago, MAX(fecha_pago) AS ultima_fecha_pago
    FROM pagos
    GROUP BY op_id
) p ON o.id = p.op_id;

-- Ensure RLS is still configured
GRANT SELECT ON v_pagos_resumen TO authenticated, anon;

NOTIFY pgrst, 'reload schema';
"""

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    print("SUCCESS: v_pagos_resumen recreated successfully.")
except Exception as e:
    print(f"ERROR: {str(e)}")
