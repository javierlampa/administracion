-- ==============================================================================
-- 12_KPI_EVOLUCION_TC_RPC.sql (VERSION POWERBI PARITY - DATESMTD)
-- Replicando la lógica de PowerBI: Puntos diarios acumulados por mes.
-- ==============================================================================

CREATE OR REPLACE FUNCTION get_evolucion_tc_metrics()
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
    result json;
BEGIN
    WITH base_ops AS (
        SELECT 
            id,
            COALESCE(clasificacion, 'SIN CLASIFICAR') AS clasificacion,
            COALESCE(importe_total, 0) AS importe,
            fecha_orden,
            EXTRACT(YEAR FROM fecha_orden) as anio,
            EXTRACT(MONTH FROM fecha_orden) as mes
        FROM v_todas_las_op_report
        WHERE estado IS DISTINCT FROM 'Anulada'
          AND estado IS DISTINCT FROM 'Baja'
          AND fecha_orden IS NOT NULL
          AND EXTRACT(YEAR FROM fecha_orden) = EXTRACT(YEAR FROM CURRENT_DATE)
    ),
    -- Calculamos los totales diarios para el gráfico de líneas (Evolución)
    diario AS (
        SELECT 
            fecha_orden as fecha,
            clasificacion,
            SUM(importe) AS venta_dia
        FROM base_ops
        GROUP BY 1, 2
    ),
    -- PIVOT de los datos para el chart
    evolucion_diaria AS (
        SELECT 
            fecha::text as fecha,
            SUM(CASE WHEN clasificacion = 'INSTITUCIONAL' THEN venta_dia ELSE 0 END) AS "INSTITUCIONAL",
            SUM(CASE WHEN clasificacion = 'MUNICIPIOS' THEN venta_dia ELSE 0 END) AS "MUNICIPIOS",
            SUM(CASE WHEN clasificacion = 'PRIVADOS NACION' THEN venta_dia ELSE 0 END) AS "PRIVADOS NACION",
            SUM(CASE WHEN clasificacion = 'PRIVADOS SJ' THEN venta_dia ELSE 0 END) AS "PRIVADOS SJ"
        FROM diario
        GROUP BY 1
        ORDER BY 1 ASC
    )
    SELECT json_build_object(
        'evolution', COALESCE((SELECT json_agg(row_to_json(ed)) FROM evolucion_diaria ed), '[]'::json),
        'pieValue', COALESCE((SELECT json_agg(row_to_json(tm)) FROM (SELECT clasificacion as name, SUM(importe) as value FROM base_ops GROUP BY 1) tm), '[]'::json),
        'pieCount', COALESCE((SELECT json_agg(row_to_json(tc)) FROM (SELECT clasificacion as name, COUNT(id) as value FROM base_ops GROUP BY 1) tc), '[]'::json)
    ) INTO result;

    RETURN result;
END;
$$;
