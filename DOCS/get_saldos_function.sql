-- Función que devuelve el saldo REAL del último pago por cada OP (Vinculado por Texto)
-- Usa DISTINCT ON para traer solo el pago más reciente (id mayor) por el número de OP (op_valor)
-- Esto es 100% confiable: el saldo ya está calculado en el momento de registrar el pago en SharePoint/Sync

CREATE OR REPLACE FUNCTION get_saldos_por_op()
RETURNS TABLE (op_numero_pago TEXT, saldo_final NUMERIC)
LANGUAGE sql STABLE
AS $$
  SELECT DISTINCT ON (op_valor)
    op_valor as op_numero_pago,
    saldo AS saldo_final
  FROM pagos
  WHERE op_valor IS NOT NULL AND op_valor <> ''
  ORDER BY op_valor, id DESC;
$$;

-- Verificar que funciona
-- SELECT * FROM get_saldos_por_op() LIMIT 10;
