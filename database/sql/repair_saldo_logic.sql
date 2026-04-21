-- 1. Intentar borrar la columna saldo de ordenes_publicidad por si quedó algún remanente (redundante)
ALTER TABLE IF EXISTS ordenes_publicidad DROP COLUMN IF EXISTS saldo;

-- 2. Función auxiliar optimizada para obtener el último saldo de la tabla de pagos
-- Esto toma la información DIRECTAMENTE de lo que SharePoint dice que es el saldo.
CREATE OR REPLACE FUNCTION get_current_op_saldo(p_op_numero TEXT, p_importe_total NUMERIC)
RETURNS NUMERIC AS $$
    SELECT COALESCE(
        (SELECT p.saldo FROM pagos p WHERE p.op_numero = p_op_numero ORDER BY p.fecha_pago DESC, p.id DESC LIMIT 1),
        p_importe_total
    );
$$ LANGUAGE sql STABLE;

-- 3. Actualizar v_todas_las_op_report para usar el saldo de la tabla PAGOS
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
    (SELECT string_agg(DISTINCT un.unidad_negocio, ', ') FROM unidades_negocio un WHERE un.op_id = o.id) AS unidad_negocio,
    -- USAMOS EL SALDO DE LA TABLA PAGOS (Info sincronizada de SP)
    get_current_op_saldo(o.op, o.importe_total) AS saldo_actual,
    COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_numero = o.op), 0) AS total_pagado,
    CASE
        WHEN o.activo = false THEN 'Baja'
        WHEN get_current_op_saldo(o.op, o.importe_total) <= 0.01 THEN 'Cobrada'
        ELSE 'Pendiente'
    END AS estado
FROM ordenes_publicidad o
LEFT JOIN clientes c ON o.cliente_id = c.id;

-- 4. Actualizar v_pagos_resumen para usar el mismo criterio
DROP VIEW IF EXISTS v_pagos_resumen CASCADE;
CREATE OR REPLACE VIEW v_pagos_resumen AS
SELECT
    o.id AS op_id,
    o.op,
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
    COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_numero = o.op), 0) AS total_pago,
    -- MISMO CRITERIO: Tomar saldo de la tabla PAGOS
    get_current_op_saldo(o.op, o.importe_total) AS saldo,
    (SELECT MAX(p.fecha_pago) FROM pagos p WHERE p.op_numero = o.op) AS ultima_fecha_pago,
    CASE
        WHEN get_current_op_saldo(o.op, o.importe_total) <= 0.01 THEN 'SALDADA'
        ELSE 'PENDIENTE'
    END AS estado_cuenta
FROM ordenes_publicidad o
LEFT JOIN clientes c ON o.cliente_id = c.id
WHERE o.activo = true OR o.activo IS NULL;
