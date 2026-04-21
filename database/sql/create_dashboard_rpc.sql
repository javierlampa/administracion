-- ==============================================================================
-- RPC: get_dashboard_metrics (VERSION V10 - POWERBI PARITY / DATESYTD)
-- Implementa la lógica de PowerBI: Sumar solo hasta el día de hoy.
-- ==============================================================================

CREATE OR REPLACE FUNCTION get_dashboard_metrics(
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL,
    p_empresa TEXT DEFAULT 'Todas'
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_start_date DATE;
    v_end_date DATE;
    v_today DATE := CURRENT_DATE;
    v_monthly_summary JSONB;
    v_annual_summary JSONB;
    v_units_distribution JSONB;
    v_company_distribution JSONB;
    v_daily_sales JSONB;
    v_kpis JSONB;
BEGIN
    -- 1. DETERMINAR EL RANGO (DATESMTD / DATESYTD LOGIC)
    v_start_date := COALESCE(p_start_date, (EXTRACT(YEAR FROM v_today) || '-01-01')::DATE);
    v_end_date := COALESCE(p_end_date, v_today);

    -- 2. RESUMEN MENSUAL (Hasta hoy para el mes actual)
    WITH monthly_raw AS (
        SELECT 
            EXTRACT(YEAR FROM fecha_orden) as anio_num,
            EXTRACT(MONTH FROM fecha_orden) as mes_num,
            empresa,
            SUM(importe_total) as venta_mes
        FROM v_todas_las_op_report
        WHERE fecha_orden >= v_start_date AND fecha_orden <= v_end_date
          AND (p_empresa = 'Todas' OR empresa = p_empresa)
        GROUP BY 1, 2, 3
    ),
    monthly_pivoted AS (
        SELECT 
            anio_num, mes_num,
            SUM(CASE WHEN empresa = 'ANDINA SA' THEN venta_mes ELSE 0 END) as venta_andina,
            SUM(CASE WHEN empresa = 'CONTENIDOS SA' THEN venta_mes ELSE 0 END) as venta_contenidos,
            SUM(venta_mes) as venta_total
        FROM monthly_raw
        GROUP BY 1, 2
    ),
    monthly_formatted AS (
        SELECT 
            anio_num, mes_num,
            CASE mes_num
                WHEN 1 THEN 'ene' WHEN 2 THEN 'feb' WHEN 3 THEN 'mar'
                WHEN 4 THEN 'abr' WHEN 5 THEN 'may' WHEN 6 THEN 'jun'
                WHEN 7 THEN 'jul' WHEN 8 THEN 'ago' WHEN 9 THEN 'sep'
                WHEN 10 THEN 'oct' WHEN 11 THEN 'nov' WHEN 12 THEN 'dic'
            END as mes_nombre,
            venta_andina,
            venta_contenidos,
            venta_total,
            SUM(venta_total) OVER (ORDER BY anio_num, mes_num) as acumulado
        FROM monthly_pivoted
    )
    SELECT jsonb_agg(jsonb_build_object(
        'mes', (mes_nombre || ' ' || anio_num),
        'andina', ROUND(venta_andina, 2),
        'contenidos', ROUND(venta_contenidos, 2),
        'venta', ROUND(venta_total, 2),
        'acumulado', ROUND(acumulado, 2)
    )) INTO v_monthly_summary FROM (SELECT * FROM monthly_formatted ORDER BY anio_num, mes_num) sub;

    -- 3. RESUMEN ANUAL (LÓGICA DATESYTD: Solo hasta hoy para el año actual)
    WITH annual_raw AS (
        SELECT 
            EXTRACT(YEAR FROM fecha_orden)::text as anio,
            SUM(CASE 
                WHEN EXTRACT(YEAR FROM fecha_orden) = EXTRACT(YEAR FROM v_today) 
                THEN (CASE WHEN fecha_orden <= v_today THEN importe_total ELSE 0 END)
                ELSE importe_total 
            END) as venta_total
        FROM v_todas_las_op_report
        WHERE (p_empresa = 'Todas' OR empresa = p_empresa)
          AND fecha_orden IS NOT NULL
        GROUP BY 1
    )
    SELECT jsonb_agg(jsonb_build_object(
        'anio', anio,
        'venta', ROUND(venta_total, 2)
    )) INTO v_annual_summary FROM (SELECT * FROM annual_raw WHERE venta_total > 0 ORDER BY anio DESC) sub;

    -- 4. DISTRIBUCIONES
    WITH units_raw AS (
        SELECT unidad_negocio, SUM(importe_total) as val
        FROM v_todas_las_op_report
        WHERE fecha_orden >= v_start_date AND fecha_orden <= v_end_date AND (p_empresa = 'Todas' OR empresa = p_empresa)
        GROUP BY 1
    )
    SELECT jsonb_agg(jsonb_build_object('name', unidad_negocio, 'value', ROUND(val, 2)))
    INTO v_units_distribution FROM (SELECT * FROM units_raw ORDER BY val DESC) sub;

    WITH company_raw AS (
        SELECT empresa, SUM(importe_total) as val
        FROM v_todas_las_op_report
        WHERE fecha_orden >= v_start_date AND fecha_orden <= v_end_date AND (p_empresa = 'Todas' OR empresa = p_empresa)
        GROUP BY 1
    )
    SELECT jsonb_agg(jsonb_build_object('name', empresa, 'value', ROUND(val, 2)))
    INTO v_company_distribution FROM (SELECT * FROM company_raw ORDER BY val DESC) sub;

    -- 5. VENTAS DIARIAS (ACUMULADO MENSUAL)
    WITH date_series AS (
        SELECT generate_series(v_start_date::timestamp, v_end_date::timestamp, '1 day'::interval)::date as d
    ),
    daily_raw AS (
        SELECT fecha_orden as f, SUM(importe_total) as v
        FROM v_todas_las_op_report
        WHERE fecha_orden >= v_start_date AND fecha_orden <= v_end_date
          AND (p_empresa = 'Todas' OR empresa = p_empresa)
        GROUP BY 1
    ),
    densified AS (
        SELECT 
            ds.d as fecha,
            COALESCE(dr.v, 0) as venta_dia,
            EXTRACT(MONTH FROM ds.d) as mes,
            EXTRACT(YEAR FROM ds.d) as anio
        FROM date_series ds
        LEFT JOIN daily_raw dr ON ds.d = dr.f
    ),
    accumulated AS (
        SELECT 
            fecha,
            SUM(venta_dia) OVER (PARTITION BY anio, mes ORDER BY fecha) as v_accum,
            mes,
            anio
        FROM densified
    )
    SELECT jsonb_agg(jsonb_build_object(
        'fecha', fecha,
        'venta', ROUND(v_accum, 2),
        'label', CASE mes
            WHEN 1 THEN 'ene' WHEN 2 THEN 'feb' WHEN 3 THEN 'mar'
            WHEN 4 THEN 'abr' WHEN 5 THEN 'may' WHEN 6 THEN 'jun'
            WHEN 7 THEN 'jul' WHEN 8 THEN 'ago' WHEN 9 THEN 'sep'
            WHEN 10 THEN 'oct' WHEN 11 THEN 'nov' WHEN 12 THEN 'dic'
        END || ' ' || anio
    )) INTO v_daily_sales FROM (SELECT * FROM accumulated ORDER BY fecha) sub;

    -- 6. KPIs (POWERBI PARITY)
    SELECT jsonb_build_object(
        'total_ops', COUNT(*),
        'ventas_mes', ROUND(SUM(CASE 
            WHEN EXTRACT(MONTH FROM fecha_orden) = EXTRACT(MONTH FROM v_today) 
             AND EXTRACT(YEAR FROM fecha_orden) = EXTRACT(YEAR FROM v_today) 
             AND fecha_orden <= v_today
            THEN importe_total ELSE 0 END), 2),
        'venta_anual', ROUND(SUM(CASE 
            WHEN EXTRACT(YEAR FROM fecha_orden) = EXTRACT(YEAR FROM v_today) 
             AND fecha_orden <= v_today
            THEN importe_total ELSE 0 END), 2),
        'start_date', v_start_date,
        'end_date', v_end_date
    ) INTO v_kpis FROM v_todas_las_op_report 
    WHERE fecha_orden >= v_start_date AND fecha_orden <= v_end_date AND (p_empresa = 'Todas' OR empresa = p_empresa);

    RETURN jsonb_build_object(
        'monthly_summary', COALESCE(v_monthly_summary, '[]'::jsonb),
        'annual_summary', COALESCE(v_annual_summary, '[]'::jsonb),
        'units_distribution', COALESCE(v_units_distribution, '[]'::jsonb),
        'company_distribution', COALESCE(v_company_distribution, '[]'::jsonb),
        'daily_sales', COALESCE(v_daily_sales, '[]'::jsonb),
        'kpis', v_kpis
    );
END;
$$;
