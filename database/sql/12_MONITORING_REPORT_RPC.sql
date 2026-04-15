-- 12. MONITORING REPORT RPC (VERSIÓN ROBUSTA - LIMPIEZA DE FORMATO)
-- Esta versión normaliza los números de OP durante el cruce para evitar "S/N" por formatos distintos.

DROP FUNCTION IF EXISTS get_monitoring_report(DATE, TEXT);

CREATE OR REPLACE FUNCTION get_monitoring_report(target_date DATE, p_business_unit TEXT DEFAULT NULL)
RETURNS TABLE (
    op_id INTEGER,
    op_number TEXT,
    cliente_nombre TEXT,
    programa_nombre TEXT,
    tipo_publicidad TEXT,
    inicio_pauta DATE,
    fin_pauta DATE,
    empresa TEXT,
    status TEXT,
    unidades TEXT,
    importe_total NUMERIC
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
        -- Seleccionamos y normalizamos los números de OP
        SELECT 
            op.*,
            TRIM(REPLACE(op.op, '.0', '')) as op_norm
        FROM ordenes_publicidad op
    ),
    filtered_ops AS (
        SELECT DISTINCT n.op_norm
        FROM normalized_ops n
        LEFT JOIN unidades_negocio un ON n.op_norm = TRIM(REPLACE(un.op_numero, '.0', ''))
        WHERE 
            n.inicio_pauta <= target_date 
            AND n.fin_pauta >= (target_date - 3)
            AND (n.activo = TRUE OR n.activo IS NULL)
            AND (p_business_unit IS NULL OR p_business_unit = 'Todas' OR un.unidad_negocio = p_business_unit)
            AND (
                n.dias_emision IS NULL 
                OR TRIM(n.dias_emision) = '' 
                OR n.dias_emision ILIKE '%' || v_dia_semana || '%'
            )
    )
    SELECT 
        op.id as op_id,
        op.op as op_number,
        op.cliente_nombre,
        COALESCE(NULLIF(tv.programa_nombre, ''), 'S/N') as programa_nombre,
        COALESCE(tv.tipo, 'S/D') as tipo_publicidad,
        op.inicio_pauta,
        op.fin_pauta,
        op.empresa,
        CASE 
            WHEN op.inicio_pauta = target_date THEN 'ALTA'
            WHEN op.fin_pauta = target_date THEN 'BAJA'
            WHEN op.inicio_pauta < target_date AND op.fin_pauta > target_date THEN 'VIGENTE'
            WHEN op.fin_pauta < target_date AND op.fin_pauta >= (target_date - 3) THEN 'CADUCADA'
            ELSE 'OTRO'
        END as status,
        COALESCE(STRING_AGG(DISTINCT un.unidad_negocio, ', '), 'SIN UNIDAD') as unidades,
        op.importe_total
    FROM normalized_ops op
    JOIN filtered_ops f ON op.op_norm = f.op_norm
    LEFT JOIN tv ON op.op_norm = TRIM(REPLACE(tv.op_numero, '.0', '')) AND UPPER(TRIM(tv.tipo)) NOT LIKE 'PROGRAMA%'
    LEFT JOIN unidades_negocio un ON op.op_norm = TRIM(REPLACE(un.op_numero, '.0', ''))
    GROUP BY op.id, op.op, op.cliente_nombre, tv.id, tv.programa_nombre, tv.tipo, op.inicio_pauta, op.fin_pauta, op.empresa, op.importe_total
    ORDER BY op.op, tv.id;
END;
$$ LANGUAGE plpgsql;
