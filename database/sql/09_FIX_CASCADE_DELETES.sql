-- ==============================================================================
-- FASE 2: MIGRACIÓN DE INTEGRIDAD REFERENCIAL (CASCADA)
-- Objetivo: Limpiar fantasmas históricos y aplicar enlaces rígidos.
-- ==============================================================================

-- 0. LIMPIEZA DE DATOS CORRUPTOS (FANTASMAS)
-- El error 23503 indica que YA TIENES boletas flotando en tu base (ej. op_id = 172)
-- que perdieron a su OP Padre. Procedemos a purgarlas para sanear la base financiera.

DELETE FROM pagos WHERE op_id IS NOT NULL AND op_id NOT IN (SELECT id FROM ordenes_publicidad);
DELETE FROM tv WHERE op_id IS NOT NULL AND op_id NOT IN (SELECT id FROM ordenes_publicidad);
DELETE FROM unidades_negocio WHERE op_id IS NOT NULL AND op_id NOT IN (SELECT id FROM ordenes_publicidad);

-- 1. Destruimos los enlaces viejos
ALTER TABLE pagos DROP CONSTRAINT IF EXISTS pagos_op_id_fkey;
ALTER TABLE tv DROP CONSTRAINT IF EXISTS tv_op_id_fkey;
ALTER TABLE unidades_negocio DROP CONSTRAINT IF EXISTS unidades_negocio_op_id_fkey;

-- 2. Creamos los enlaces rígidos y estructurados (CASCADE)
ALTER TABLE pagos 
    ADD CONSTRAINT pagos_op_id_fkey 
    FOREIGN KEY (op_id) REFERENCES ordenes_publicidad(id) ON DELETE CASCADE;

ALTER TABLE tv 
    ADD CONSTRAINT tv_op_id_fkey 
    FOREIGN KEY (op_id) REFERENCES ordenes_publicidad(id) ON DELETE CASCADE;

ALTER TABLE unidades_negocio 
    ADD CONSTRAINT unidades_negocio_op_id_fkey 
    FOREIGN KEY (op_id) REFERENCES ordenes_publicidad(id) ON DELETE CASCADE;

-- FIN.
