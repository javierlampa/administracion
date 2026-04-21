-- ==============================================================================
-- 23_FIX_COMISIONES_VIEW.sql
-- Recrea la vista de comisiones con todos los campos necesarios.
-- ==============================================================================

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

COMMENT ON VIEW v_comisiones_report IS 'Vista detallada de comisiones por pago. Join por op_numero para consistencia.';
