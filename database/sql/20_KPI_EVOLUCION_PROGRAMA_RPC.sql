-- ==============================================================================
-- 20_KPI_EVOLUCION_PROGRAMA_RPC.sql (VERSIÓN SIMPLIFICADA)
-- ==============================================================================

CREATE OR REPLACE FUNCTION get_evolucion_programa_metrics(
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL,
    p_empresa TEXT DEFAULT 'Todas',
    p_excluir_canjes BOOLEAN DEFAULT false
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
            t.id,
            COALESCE(NULLIF(TRIM(t.programa_nombre), ''), '(En blanco)') AS un,
            COALESCE(t.tipo, '(En blanco)') as tipo_pub,
            COALESCE(t.importe_total, 0) AS importe,
            COALESCE(t.segundos, 0) AS segundos,
            o.fecha_orden,
            EXTRACT(YEAR FROM o.fecha_orden) as anio,
            EXTRACT(MONTH FROM o.fecha_orden) as mes,
            to_char(o.fecha_orden, 'TMMonth') as mes_nombre,
            o.id as op_id
        FROM tv t
        JOIN ordenes_publicidad o ON t.op_id = o.id
        WHERE o.fecha_orden BETWEEN v_start AND v_end
          AND (o.es_canje = false OR p_excluir_canjes = false)
          AND (p_empresa = 'Todas' OR o.empresa = p_empresa)
          -- FILTRO DE PAUTA TV REAL
          AND t.programa_nombre NOT ILIKE '%digital%'
          AND t.programa_nombre NOT ILIKE '%papel%'
          -- Filtro de seguridad por si hay nulos
          AND t.id IS NOT NULL
    ),
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
            SELECT fecha, un, total FROM diario ORDER BY fecha ASC
        ) d
    ),
            mes_num,
            SUM(importe) as total,
            COUNT(DISTINCT op_id) as cantidad
        FROM base_ops
        GROUP BY 1, 2, 3
        ORDER BY 3 ASC
    ),
    matriz_segundos AS (
        SELECT 
            un,
            mes_nombre as mes,
            mes as mes_num,
            SUM(segundos) as total,
            COUNT(DISTINCT op_id) as cantidad
        FROM base_ops
        GROUP BY 1, 2, 3
        ORDER BY 3 ASC
    ),
    matriz_tipo AS (
        SELECT 
            tipo_pub as un,
            mes_nombre as mes,
            mes as mes_num,
            SUM(importe) as total,
            COUNT(DISTINCT op_id) as cantidad
        FROM base_ops
        GROUP BY 1, 2, 3
        ORDER BY 3 ASC
    ),
    base_digital AS (
        SELECT 
            'Digital ' || COALESCE(NULLIF(TRIM(t.programa_nombre), ''), o.empresa) || ' - ' || COALESCE(o.medidas_digital, '(Sin medida)') as un,
            EXTRACT(MONTH FROM o.fecha_orden) as mes_num,
            to_char(o.fecha_orden, 'TMMonth') as mes,
            SUM(COALESCE(t.importe_total, 0)) as total,
            COUNT(DISTINCT o.op) as cantidad
        FROM tv t
        JOIN ordenes_publicidad o ON t.op_numero = o.op
        WHERE o.fecha_orden BETWEEN v_start AND v_end
          AND (o.es_canje = false OR p_excluir_canjes = false)
          AND (p_empresa = 'Todas' OR o.empresa = p_empresa)
          AND NULLIF(TRIM(o.medidas_digital), '') IS NOT NULL
        GROUP BY 1, 2, 3
    ),
    pie_value AS (
        SELECT un as name, SUM(importe) as value 
        FROM base_ops 
        GROUP BY 1
    )

    SELECT json_build_object(
        'evolution', COALESCE((SELECT * FROM evolucion_json), '[]'::json),
        'matrixImporte', COALESCE((SELECT json_agg(row_to_json(m)) FROM matriz_importe m), '[]'::json),
        'matrixSegundos', COALESCE((SELECT json_agg(row_to_json(ms)) FROM matriz_segundos ms), '[]'::json),
        'matrixTipo', COALESCE((SELECT json_agg(row_to_json(mt)) FROM matriz_tipo mt), '[]'::json),
        'matrixDigital', COALESCE((SELECT json_agg(row_to_json(md)) FROM base_digital md), '[]'::json),
        'matrixPapel', '[]'::json,
        'pieValue', COALESCE((SELECT json_agg(row_to_json(pv)) FROM pie_value pv), '[]'::json)
    ) INTO result;

    RETURN result;
END;
$$;
