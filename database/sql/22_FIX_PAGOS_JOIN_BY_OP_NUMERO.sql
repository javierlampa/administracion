-- ==============================================================================
-- 22_FIX_PAGOS_JOIN_BY_OP_NUMERO.sql
-- Corrige las vistas para que el JOIN con pagos use op_numero en lugar de op_id.
-- Esto garantiza que TODOS los pagos se vinculen correctamente,
-- independientemente de si tienen op_id NULL o no.
-- ==============================================================================

-- 1. ACTUALIZAR v_todas_las_op_report
--    Cambia el JOIN con pagos de op_id a op_numero

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
    -- Unidades de negocio (por op_id, que es confiable para UN)
    (
        SELECT string_agg(DISTINCT un.unidad_negocio, ', ')
        FROM unidades_negocio un
        WHERE un.op_id = o.id
    ) AS unidad_negocio,
    -- Saldo calculado por op_numero (JOIN confiable para pagos)
    (
        COALESCE(o.importe_total, 0) -
        COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_numero = o.op), 0)
    ) AS saldo_actual,
    -- Total pagado por op_numero
    COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_numero = o.op), 0) AS total_pagado,
    -- Estado de la cuenta
    CASE
        WHEN o.activo = false THEN 'Baja'
        WHEN (COALESCE(o.importe_total, 0) - COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_numero = o.op), 0)) <= 0.01 THEN 'Cobrada'
        ELSE 'Pendiente'
    END AS estado
FROM ordenes_publicidad o
LEFT JOIN clientes c ON o.cliente_id = c.id;

COMMENT ON VIEW v_todas_las_op_report IS 'Vista maestra OP. JOIN pagos por op_numero para incluir todos los pagos.';


-- 2. CREAR/RECREAR v_pagos_resumen para la página Pagos y Saldos

DROP VIEW IF EXISTS v_pagos_resumen CASCADE;

CREATE OR REPLACE VIEW v_pagos_resumen AS
SELECT
    o.id            AS op_id,
    o.op            AS op,
    o.empresa,
    o.cliente_nombre,
    c.razon_social,
    o.vendedor_nombre,
    o.numero_factura,
    o.esta_facturado,
    o.fecha_orden,
    o.inicio_pauta,
    o.fin_pauta,
    o.importe_total,
    -- Total cobrado por op_numero
    COALESCE(
        (SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_numero = o.op),
        0
    ) AS total_pago,
    -- Saldo por op_numero
    COALESCE(o.importe_total, 0) - COALESCE(
        (SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_numero = o.op),
        0
    ) AS saldo,
    -- Última fecha de pago
    (SELECT MAX(p.fecha_pago) FROM pagos p WHERE p.op_numero = o.op) AS ultima_fecha_pago,
    -- Estado de cuenta
    CASE
        WHEN (
            COALESCE(o.importe_total, 0) -
            COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_numero = o.op), 0)
        ) <= 0.01 THEN 'SALDADA'
        ELSE 'PENDIENTE'
    END AS estado_cuenta
FROM ordenes_publicidad o
LEFT JOIN clientes c ON o.cliente_id = c.id
WHERE o.activo = true OR o.activo IS NULL;

COMMENT ON VIEW v_pagos_resumen IS 'Vista de pagos y saldos. JOIN por op_numero para incluir todos los pagos correctamente.';
