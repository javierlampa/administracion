-- Script para eliminar restricciones de unicidad SOLO en la tabla TV
-- Esto permite que si SharePoint tiene múltiples renglones para la misma OP y Programa/Tipo en TV, todos pasen a la DB.

DO $$
DECLARE
    r RECORD;
BEGIN
    -- 1. Eliminar constraints UNIQUE de la tabla 'tv'
    FOR r IN (
        SELECT conname FROM pg_constraint 
        WHERE conrelid = 'tv'::regclass AND contype = 'u'
    ) LOOP
        EXECUTE 'ALTER TABLE tv DROP CONSTRAINT ' || r.conname;
    END LOOP;

    -- 2. Eliminar índices UNIQUE de la tabla 'tv' que no son la PK
    FOR r IN (
        SELECT indexname FROM pg_indexes 
        WHERE tablename = 'tv' 
        AND indexdef LIKE 'CREATE UNIQUE INDEX%'
        AND indexname NOT LIKE '%_pkey'
    ) LOOP
        EXECUTE 'DROP INDEX ' || r.indexname;
    END LOOP;
END $$;
