ALTER TABLE ordenes_publicidad ADD COLUMN IF NOT EXISTS dias_emision TEXT;
ALTER TABLE ordenes_publicidad ADD COLUMN IF NOT EXISTS cantidad_salidas INTEGER;
ALTER TABLE ordenes_publicidad ADD COLUMN IF NOT EXISTS observaciones_tecnicas TEXT;
