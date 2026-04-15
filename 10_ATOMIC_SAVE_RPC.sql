-- ==============================================================================
-- FASE 3: TRANSACCIÓN ATÓMICA DE ÓRDENES (RPC POSTGRES)
-- Objetivo: Prevenir corrupción de datos al guardar o editar, empaquetando
-- "maestro y detalle" en una sola operación inquebrantable desde la nube.
-- ==============================================================================

CREATE OR REPLACE FUNCTION save_op_atomic(
    p_op_data JSONB,
    p_units_data JSONB,
    p_tech_data JSONB,
    p_edit_mode BOOLEAN,
    p_edit_id INTEGER DEFAULT NULL
) RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_op_id INTEGER;
    v_op_numero TEXT;
BEGIN
    -- 1. RAMIFICACIÓN MAESTRA: Actualiza o Inserta la Cabecera (OP)
    IF p_edit_mode AND p_edit_id IS NOT NULL THEN
        -- Actualización de OP Existente
        UPDATE ordenes_publicidad SET 
            op = p_op_data->>'op',
            numero_factura = p_op_data->>'numero_factura',
            tipo_factura = p_op_data->>'tipo_factura',
            empresa = p_op_data->>'empresa',
            clasificacion = p_op_data->>'clasificacion',
            fecha_orden = (p_op_data->>'fecha_orden')::date,
            cliente_id = (p_op_data->>'cliente_id')::integer,
            vendedor_nombre = p_op_data->>'vendedor_nombre',
            cliente_nombre = p_op_data->>'cliente_nombre',
            inicio_pauta = (p_op_data->>'inicio_pauta')::date,
            fin_pauta = (p_op_data->>'fin_pauta')::date,
            venta_combo = (p_op_data->>'venta_combo')::boolean,
            esta_facturado = (p_op_data->>'esta_facturado')::boolean,
            es_canje = (p_op_data->>'es_canje')::boolean,
            importe_total = (p_op_data->>'importe_total')::numeric,
            iva = (p_op_data->>'iva')::numeric,
            importe_sin_iva = (p_op_data->>'importe_sin_iva')::numeric,
            medidas_digital = p_op_data->>'medidas_digital',
            observaciones_de_facturacion = p_op_data->>'observaciones_de_facturacion',
            observaciones_digital = p_op_data->>'observaciones_digital',
            dias_emision = p_op_data->>'dias_emision',
            cantidad_salidas = (p_op_data->>'cantidad_salidas')::integer,
            observaciones_tecnicas = p_op_data->>'observaciones_tecnicas',
            modified = current_timestamp
        WHERE id = p_edit_id;
        
        v_op_id := p_edit_id;
        v_op_numero := p_op_data->>'op';

        -- Dado que es edición, purgamos los dependientes antiguos de forma atómica para reemplazarlos
        DELETE FROM unidades_negocio WHERE op_id = v_op_id;
        DELETE FROM tv WHERE op_id = v_op_id;
    ELSE
        -- Creación de Inserción Nueva
        INSERT INTO ordenes_publicidad (
            op, numero_factura, tipo_factura, empresa, clasificacion, fecha_orden,
            cliente_id, vendedor_nombre, cliente_nombre, inicio_pauta, fin_pauta,
            venta_combo, esta_facturado, es_canje, importe_total, iva, importe_sin_iva,
            medidas_digital, observaciones_de_facturacion, observaciones_digital,
            dias_emision, cantidad_salidas, observaciones_tecnicas
        ) VALUES (
            p_op_data->>'op', p_op_data->>'numero_factura', p_op_data->>'tipo_factura', p_op_data->>'empresa', p_op_data->>'clasificacion', (p_op_data->>'fecha_orden')::date,
            (p_op_data->>'cliente_id')::integer, p_op_data->>'vendedor_nombre', p_op_data->>'cliente_nombre', (p_op_data->>'inicio_pauta')::date, (p_op_data->>'fin_pauta')::date,
            (p_op_data->>'venta_combo')::boolean, (p_op_data->>'esta_facturado')::boolean, (p_op_data->>'es_canje')::boolean, (p_op_data->>'importe_total')::numeric, (p_op_data->>'iva')::numeric, (p_op_data->>'importe_sin_iva')::numeric,
            p_op_data->>'medidas_digital', p_op_data->>'observaciones_de_facturacion', p_op_data->>'observaciones_digital',
            p_op_data->>'dias_emision', (p_op_data->>'cantidad_salidas')::integer, p_op_data->>'observaciones_tecnicas'
        ) RETURNING id, op INTO v_op_id, v_op_numero;
    END IF;

    -- 2. INSERCIÓN DE BLOQUES FINANCIEROS (Unidades de Negocio)
    IF p_units_data IS NOT NULL AND jsonb_array_length(p_units_data) > 0 THEN
        INSERT INTO unidades_negocio (op_id, op_numero, unidad_negocio, importe_total, importe_sin_iva, iva)
        SELECT 
            v_op_id, v_op_numero, 
            el->>'unidad_negocio', 
            (el->>'importe_total')::numeric, 
            (el->>'importe_sin_iva')::numeric, 
            (el->>'iva')::numeric
        FROM jsonb_array_elements(p_units_data) AS el;
    END IF;

    -- 3. INSERCIÓN DE SALIDAS TÉCNICAS (TV / Radio)
    IF p_tech_data IS NOT NULL AND jsonb_array_length(p_tech_data) > 0 THEN
        INSERT INTO tv (op_id, op_numero, programa_id, programa_nombre, tipo, segundos, valor_segundo, importe_total, iva, importe_sin_iva, detalles_salidas)
        SELECT 
            v_op_id, v_op_numero, 
            NULLIF(el->>'programa_id', '')::integer, 
            el->>'programa_nombre', 
            el->>'tipo', 
            NULLIF(el->>'segundos', '')::numeric, 
            NULLIF(el->>'valor_segundo', '')::numeric, 
            (el->>'importe_total')::numeric, 
            (el->>'iva')::numeric, 
            (el->>'importe_sin_iva')::numeric, 
            el->>'detalles_salidas'
        FROM jsonb_array_elements(p_tech_data) AS el;
    END IF;

    -- 4. RETORNO DE CÓDIGO FINAL DE ÉXITO
    RETURN jsonb_build_object('success', true, 'op_id', v_op_id);

    -- Si algo falló antes, Postgres cancela la transacción de forma "rollback" automáticamente sin guardar nada roto.
END;
$$;
