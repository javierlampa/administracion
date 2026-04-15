-- ==============================================================================
-- FASE 3: OPTIMIZACIÓN AVANZADA DE BÚSQUEDAS (Trigram)
-- Objetivo: Acelerar búsquedas parciales (LIKE %text%) en grandes volúmenes.
-- IMPORTANTE: "pg_trgm" rompe el texto en sílabas, logrando que Postgres
-- busque mil veces más rápido al teclear una empresa en el frontend.
-- ==============================================================================

-- 1. Habilitar la súper-extensión de fragmentación silábica de Postgres
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Índices para Módulo OP (Mantenimiento Vistas)
CREATE INDEX IF NOT EXISTS idx_op_cliente_nombre_trgm ON ordenes_publicidad USING gin (cliente_nombre gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_op_vendedor_nombre_trgm ON ordenes_publicidad USING gin (vendedor_nombre gin_trgm_ops);

-- 3. Índices para Maestros
CREATE INDEX IF NOT EXISTS idx_clientes_nombre_trgm ON clientes USING gin (nombre gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_vendedores_nombre_trgm ON vendedores USING gin (nombre gin_trgm_ops);

-- 4. Índices para Facturación Secundaria
CREATE INDEX IF NOT EXISTS idx_unidades_empresa_trgm ON unidades_negocio USING gin (unidad_negocio gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_tv_programa_nombre_trgm ON tv USING gin (programa_nombre gin_trgm_ops);

-- FIN.
