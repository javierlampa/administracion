-- 16. DAILY GRID REPORT RPC (VERSIÓN ROBUSTA - LIMPIEZA DE FORMATO)
-- Esta versión normaliza los números de OP durante el cruce para evitar "S/N".

DROP FUNCTION IF EXISTS get_daily_grid_report(DATE, TEXT);

CREATE OR REPLACE FUNCTION get_daily_grid_report(target_date DATE, p_business_unit TEXT DEFAULT NULL)
RETURNS TABLE (
    op_id INTEGER,
    op_number TEXT,
    cliente_nombre TEXT,
    programa_nombre TEXT,
    tipo_publicidad TEXT,
    segundos INTEGER,
    observaciones_tecnicas TEXT,
    unidades TEXT,
    status TEXT,
    cantidad_salidas INTEGER
) AS $$
DECLARE
    v_dia_semana TEXT;
BEGIN
    v_dia_semana := CASE EXTRACT(ISODOW FROM target_date)
        WHEN 1 THEN 'Lunes'
        WHEN 2 THEN 'Martes'
        WHEN 3 THEN 'Miércoles'
        WHEN 4 THEN 'Jueves'
        WHEN 5 THEN 'Viernes'
        WHEN 6 THEN 'Sábado'
        WHEN 7 THEN 'Domingo'
    END;

    RETURN QUERY
    WITH normalized_ops AS (
        SELECT 
            op.*,
            TRIM(REPLACE(op.op, '.0', '')) as op_norm
        FROM ordenes_publicidad op
    ),
    filtered_ops AS (
        SELECT DISTINCT n.id
        FROM normalized_ops n
        LEFT JOIN unidades_negocio un ON n.op_norm = TRIM(REPLACE(un.op_numero, '.0', ''))
        WHERE 
            (
                (n.inicio_pauta <= target_date AND n.fin_pauta >= target_date)
                OR n.fin_pauta = (target_date - 1) 
            )
            AND (n.activo = TRUE OR n.activo IS NULL)
            AND (p_business_unit IS NULL OR p_business_unit = 'Todas' OR un.unidad_negocio = p_business_unit)
            AND (
                n.dias_emision IS NULL 
                OR TRIM(n.dias_emision) = '' 
                OR n.dias_emision ILIKE '%' || v_dia_semana || '%'
            )
            AND NOT EXISTS (
                SELECT 1 
                FROM tv 
                WHERE TRIM(REPLACE(tv.op_numero, '.0', '')) = n.op_norm 
                AND UPPER(tv.tipo) LIKE 'PROGRAMA%'
            )
    )
    SELECT 
        op.id::INTEGER as op_id,
        op.op::TEXT as op_number,
        op.cliente_nombre::TEXT,
        COALESCE(NULLIF(tv.programa_nombre, ''), 'S/N')::TEXT as programa_nombre,
        COALESCE(tv.tipo, 'S/D')::TEXT as tipo_publicidad,
        COALESCE(tv.segundos, 0)::INTEGER as segundos,
        op.observaciones_tecnicas::TEXT,
        COALESCE(STRING_AGG(DISTINCT un.unidad_negocio, ', '), 'SIN UNIDAD')::TEXT as unidades,
        (CASE 
            WHEN op.inicio_pauta = target_date THEN 'ALTA'
            WHEN op.fin_pauta = target_date THEN 'BAJA'
            WHEN op.fin_pauta = (target_date - 1) THEN 'CADUCADA'
            ELSE 'VIGENTE'
        END)::TEXT as status,
        op.cantidad_salidas::INTEGER as cantidad_salidas
    FROM normalized_ops op
    JOIN filtered_ops f ON op.id = f.id
    LEFT JOIN tv ON op.op_norm = TRIM(REPLACE(tv.op_numero, '.0', '')) AND UPPER(TRIM(tv.tipo)) NOT LIKE 'PROGRAMA%'
    LEFT JOIN unidades_negocio un ON op.op_norm = TRIM(REPLACE(un.op_numero, '.0', ''))
    GROUP BY op.id, op.op, op.cliente_nombre, tv.id, tv.programa_nombre, tv.tipo, tv.segundos, op.observaciones_tecnicas, op.inicio_pauta, op.fin_pauta, op.cantidad_salidas
    ORDER BY programa_nombre, op.cliente_nombre;
END;
$$ LANGUAGE plpgsql;
