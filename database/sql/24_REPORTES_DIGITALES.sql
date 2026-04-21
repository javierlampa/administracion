-- 1. Vista Agrupada (Resumen Ideal para ver cuántos y cuánta plata)
CREATE OR REPLACE VIEW v_digital_agrupado AS
SELECT 
    COUNT(t.id) as cantidad_pautas,
    COALESCE(op.medidas_digital, 'Sin Especificar') as medidas_digital,
    COALESCE(t.programa_nombre, 'Medio No Asignado') as medio,
    COALESCE(t.tipo, 'Banner Digital') as tipo_publicidad,
    SUM(t.importe_total) as importe_total_recaudado
FROM public.tv t
LEFT JOIN public.ordenes_publicidad op ON t.op_numero = op.op
WHERE (t.tipo ILIKE '%DIGITAL%' OR t.tipo ILIKE '%BANNER%' OR op.medidas_digital IS NOT NULL)
  AND t.importe_total > 0
GROUP BY 
    COALESCE(op.medidas_digital, 'Sin Especificar'),
    COALESCE(t.programa_nombre, 'Medio No Asignado'),
    COALESCE(t.tipo, 'Banner Digital')
ORDER BY 
    importe_total_recaudado DESC;

-- 2. Vista de Detalle (Ideal para la tabla principal si querés ver a qué OP corresponde cada uno)
CREATE OR REPLACE VIEW v_digital_detalle AS
SELECT 
    t.id as tv_id,
    COALESCE(op.op, t.op_numero) as op_numero,
    op.fecha_orden,
    t.programa_nombre as medio,
    t.tipo as tipo_publicidad,
    op.medidas_digital,
    c.nombre_comercial as cliente_nombre,
    c.razon_social as cliente_razon_social,
    op.vendedor_nombre,
    t.importe_total as importe_pauta,
    op.importe_total as importe_op_maestra
FROM public.tv t
LEFT JOIN public.ordenes_publicidad op ON t.op_numero = op.op
LEFT JOIN public.clientes c ON op.cliente_id = c.id
WHERE (t.tipo ILIKE '%DIGITAL%' OR t.tipo ILIKE '%BANNER%' OR op.medidas_digital IS NOT NULL);
