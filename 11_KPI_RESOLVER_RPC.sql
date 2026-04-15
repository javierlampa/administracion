-- ==============================================================================
-- FASE 4: OPTIMIZADOR DE RENDIMIENTO DASHBOARD (KPI RESOLVER RPC)
-- Objetivo: Evitar la descarga masiva de datos en el cliente y forzar que
-- Postgres calcule y consolide los agregados métricos en 1 ms.
-- ==============================================================================

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
    -- 1. Determinar Filtros de Fecha Anual
    IF p_year IS NOT NULL AND p_year != 'Todos los Años' THEN
        v_start_date := (p_year || '-01-01')::DATE;
        v_end_date := ((p_year::integer + 1)::text || '-01-01')::DATE;
    END IF;

    -- 2. Determinar Filtros Mensuales Nativos
    IF p_month IS NOT NULL AND p_month != 'Todos los Meses' THEN
        v_month_num := CASE p_month
            WHEN 'Enero' THEN 1 WHEN 'Febrero' THEN 2 WHEN 'Marzo' THEN 3
            WHEN 'Abril' THEN 4 WHEN 'Mayo' THEN 5 WHEN 'Junio' THEN 6
            WHEN 'Julio' THEN 7 WHEN 'Agosto' THEN 8 WHEN 'Septiembre' THEN 9
            WHEN 'Octubre' THEN 10 WHEN 'Noviembre' THEN 11 WHEN 'Diciembre' THEN 12
            ELSE NULL
        END;
    END IF;

    -- 3. Inyección Atómica a la Memoria del Motor (Calculo Veloz)
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

    -- 4. Extracción Liviana (Convertimos 30 Megabytes en sólo 1 Kilobyte de respuesta)
    RETURN jsonb_build_object(
        'total_facturado', ROUND(v_total_facturado),
        'total_paid', ROUND(v_total_facturado - v_total_saldo),
        'total_ops', v_total_ops,
        'balance', ROUND(v_total_saldo)
    );
END;
$$;

-- FIN.
