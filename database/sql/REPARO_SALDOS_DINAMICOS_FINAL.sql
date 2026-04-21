-- ==============================================================================
-- REPARO_SALDOS_DINAMICOS_FINAL.sql
-- Objetivo: Implementar el cálculo de saldos basado en "Total Orden - Suma de Pagos"
-- Esto garantiza que OPs sin pagos muestren su deuda total y que los borrados 
-- de pagos se reflejen al instante.
-- ==============================================================================

-- 1. Actualizar la Vista Maestra de OPs
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
    -- CÁLCULO DINÁMICO DE TOTAL PAGADO
    COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_id = o.id), 0) AS total_pagado,
    -- CÁLCULO DINÁMICO DE SALDO ACTUAL (La Verdad Absoluta)
    (
        COALESCE(o.importe_total, 0) - 
        COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_id = o.id), 0)
    ) AS saldo_actual,
    -- Campo 'estado' basado en el saldo real
    CASE 
        WHEN o.activo = false THEN 'Baja'
        WHEN (COALESCE(o.importe_total, 0) - COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_id = o.id), 0)) <= 0.01 THEN 'Cobrada'
        ELSE 'Pendiente'
    END AS estado
FROM ordenes_publicidad o
LEFT JOIN clientes c ON o.cliente_id = c.id;

-- 2. Actualizar la Vista de Pagos y Resumen
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
    -- Suma real de pagos
    COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_id = o.id), 0) AS total_pago,
    -- Saldo real calculado
    (COALESCE(o.importe_total, 0) - COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_id = o.id), 0)) AS saldo,
    (SELECT MAX(p.fecha_pago) FROM pagos p WHERE p.op_id = o.id) AS ultima_fecha_pago,
    CASE
        WHEN (COALESCE(o.importe_total, 0) - COALESCE((SELECT SUM(p.importe_pago) FROM pagos p WHERE p.op_id = o.id), 0)) <= 0.01 THEN 'SALDADA'
        ELSE 'PENDIENTE'
    END AS estado_cuenta
FROM ordenes_publicidad o
LEFT JOIN clientes c ON o.cliente_id = c.id
WHERE o.activo = true OR o.activo IS NULL;

-- 3. Actualizar la Función de KPIs para el Dashboard
CREATE OR REPLACE FUNCTION fetch_sum_kpis(
    p_year TEXT DEFAULT NULL,
    p_month TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_total_facturado NUMERIC;
    v_total_saldo NUMERIC;
    v_total_ops INTEGER;
    v_start_date DATE;
    v_end_date DATE;
    v_month_num INTEGER := NULL;
BEGIN
    -- Determinar Filtros de Fecha Anual
    IF p_year IS NOT NULL AND p_year != 'Todos los Años' THEN
        v_start_date := (p_year || '-01-01')::DATE;
        v_end_date := ((p_year::integer + 1)::text || '-01-01')::DATE;
    END IF;

    -- Determinar Filtros Mensuales
    IF p_month IS NOT NULL AND p_month != 'Todos los Meses' THEN
        v_month_num := CASE p_month
            WHEN 'Enero' THEN 1 WHEN 'Febrero' THEN 2 WHEN 'Marzo' THEN 3
            WHEN 'Abril' THEN 4 WHEN 'Mayo' THEN 5 WHEN 'Junio' THEN 6
            WHEN 'Julio' THEN 7 WHEN 'Agosto' THEN 8 WHEN 'Septiembre' THEN 9
            WHEN 'Octubre' THEN 10 WHEN 'Noviembre' THEN 11 WHEN 'Diciembre' THEN 12
            ELSE NULL
        END;
    END IF;

    -- Cálculo de Agregados usando la vista con saldos dinámicos
    SELECT 
        COALESCE(SUM(importe_total), 0),
        COALESCE(SUM(saldo_actual), 0),
        COUNT(*)
    INTO 
        v_total_facturado, v_total_saldo, v_total_ops
    FROM v_todas_las_op_report
    WHERE 
        (v_start_date IS NULL OR fecha_orden >= v_start_date) AND
        (v_start_date IS NULL OR fecha_orden < v_end_date) AND
        (v_month_num IS NULL OR EXTRACT(MONTH FROM fecha_orden) = v_month_num);

    RETURN jsonb_build_object(
        'total_facturado', ROUND(v_total_facturado),
        'total_paid', ROUND(v_total_facturado - v_total_saldo),
        'total_ops', v_total_ops,
        'balance', ROUND(v_total_saldo)
    );
END;
$$;
