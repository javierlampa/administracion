-- 15. BACKFILL DE DÍAS DE EMISIÓN
-- Este script actualizará TODAS las órdenes vigentes o históricas 
-- en la base de datos para que asuman que salen todos los días.

UPDATE ordenes_publicidad
SET dias_emision = 'Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo'
WHERE dias_emision IS NULL OR TRIM(dias_emision) = '';

-- Una vez ejecutado, ninguna orden quedará huérfana de días, 
-- y podrás editarlas manualmente desde la UI para des-marcarlas.
