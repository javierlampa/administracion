CREATE OR REPLACE VIEW v_reporte_programas AS
SELECT 
    t.id as tv_id,
    COALESCE(op.op, SPLIT_PART(t.op_ref, '.', 1)) as op_numero,
    op.fecha_orden,
    t.programa_nombre,
    c.nombre_comercial as cliente_nombre,
    c.razon_social as cliente_razon_social,
    op.vendedor_nombre,
    op.inicio_pauta,
    op.fin_pauta,
    op.tipo_factura,
    op.esta_facturado,
    op.fecha_factura,
    op.numero_factura,
    op.es_canje,
    t.segundos as segundos_tv_radio,
    t.importe_total as importe_fila_tv,
    op.importe_total as op_importe_total,
    op.empresa
FROM public.tv t
LEFT JOIN public.ordenes_publicidad op ON SPLIT_PART(t.op_ref, '.', 1) = op.op
LEFT JOIN public.clientes c ON op.cliente_id = c.id;
