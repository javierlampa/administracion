-- ==============================================================================
-- 19_KPI_EVOLUCION_UN_RPC.sql
-- Genera métricas de evolución por Unidad de Negocio (UN)
-- ==============================================================================

CREATE OR REPLACE FUNCTION get_evolucion_un_metrics(
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL,
    p_empresa TEXT DEFAULT 'Todas'
)
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
    result json;
    v_start DATE := COALESCE(p_start_date, date_trunc('year', CURRENT_DATE)::DATE);
    v_end DATE := COALESCE(p_end_date, CURRENT_DATE);
BEGIN
    WITH base_ops AS (
        SELECT 
            id,
            COALESCE(unidad_negocio, 'SIN ASIGNAR') AS un,
            COALESCE(importe_total, 0) AS importe,
            fecha_orden,
            EXTRACT(YEAR FROM fecha_orden) as anio,
            EXTRACT(MONTH FROM fecha_orden) as mes,
            to_char(fecha_orden, 'TMMonth') as mes_nombre
        FROM v_todas_las_op_report
        WHERE estado IS DISTINCT FROM 'Anulada'
          AND estado IS DISTINCT FROM 'Baja'
          AND fecha_orden BETWEEN v_start AND v_end
          AND (p_empresa = 'Todas' OR empresa = p_empresa)
    ),
    -- Evolución diaria para el gráfico de líneas
    diario AS (
        SELECT 
            fecha_orden::text as fecha,
            un,
            SUM(importe) AS total
        FROM base_ops
        GROUP BY 1, 2
    ),
    evolucion_json AS (
        SELECT json_agg(row_to_json(d)) FROM (
            -- Aquí pivotamos dinámicamente o devolvemos filas para que el frontend procese
            -- Para simplicidad y flexibilidad, devolvemos los puntos diarios y el front los agrupa
            SELECT fecha, un, total FROM diario ORDER BY fecha ASC
        ) d
    ),
    -- Datos para la matriz (Mes vs UN)
    matriz AS (
        SELECT 
            un,
            mes_nombre as mes,
            mes as mes_num,
            SUM(importe) as total
        FROM base_ops
        GROUP BY 1, 2, 3
        ORDER BY 3 ASC
    ),
    -- Totales para Pie Charts
    pie_value AS (
        SELECT un as name, SUM(importe) as value 
        FROM base_ops 
        GROUP BY 1
    ),
    pie_count AS (
        SELECT un as name, COUNT(id) as value 
        FROM base_ops 
        GROUP BY 1
    )
    SELECT json_build_object(
        'evolution', COALESCE((SELECT * FROM evolucion_json), '[]'::json),
        'matrix', COALESCE((SELECT json_agg(row_to_json(m)) FROM matriz m), '[]'::json),
        'pieValue', COALESCE((SELECT json_agg(row_to_json(pv)) FROM pie_value pv), '[]'::json),
        'pieCount', COALESCE((SELECT json_agg(row_to_json(pc)) FROM pie_count pc), '[]'::json)
    ) INTO result;

    RETURN result;
END;
$$;
