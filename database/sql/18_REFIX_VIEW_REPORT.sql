-- ==============================================================================
-- 18_REFIX_VIEW_REPORT.sql
-- Re-definición de la vista maestra para reportes y dashboard.
-- Incluye 'clasificacion' y cálculo dinámico de saldos.
-- ==============================================================================

DROP VIEW IF EXISTS v_todas_las_op_report CASCADE;

CREATE OR REPLACE VIEW v_todas_las_op_report AS
SELECT 
    o.id,
    o.op,
    o.empresa,
    o.programa_nombre,
    o.fecha_orden,
    o.importe_total,
    o.cliente_nombre AS cliente_nombre_comercial,
    c.razon_social AS cliente_razon_social,
    o.vendedor_nombre,
    o.esta_facturado,
    o.numero_factura,
    o.fecha_factura,
    o.inicio_pauta,
    o.fin_pauta,
    o.anio,
    o.es_canje,
    o.clasificacion,
    o.tipo_factura,
    -- Agregación de unidades de negocio (UN)
    (
        SELECT string_agg(DISTINCT un.unidad_negocio, ', ')
        FROM unidades_negocio un
        WHERE un.op_id = o.id
    ) AS unidad_negocio,
    -- Cálculo dinámico de saldo
    (
        COALESCE(o.importe_total, 0) - 
        COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_id = o.id), 0)
    ) AS saldo_actual,
    -- Campo 'estado' para compatibilidad con KPIs
    CASE 
        WHEN o.activo = false THEN 'Baja'
        WHEN (COALESCE(o.importe_total, 0) - COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_id = o.id), 0)) <= 0.01 THEN 'Cobrada'
        ELSE 'Pendiente'
    END AS estado
FROM ordenes_publicidad o
LEFT JOIN clientes c ON o.cliente_id = c.id;

-- También nos aseguramos de que la función de KPI esté actualizada si hace falta
-- pero el problema principal era la vista.

COMMENT ON VIEW v_todas_las_op_report IS 'Vista maestra que consolida OP, Clientes, Vendedores y cálculos financieros.';
