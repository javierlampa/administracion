-- Desactivar temporalmente RLS (o añadir políticas de borrado) para que el Portal Web pueda borrar en cascada
ALTER TABLE ordenes_publicidad DISABLE ROW LEVEL SECURITY;
ALTER TABLE unidades_negocio DISABLE ROW LEVEL SECURITY;
ALTER TABLE tv DISABLE ROW LEVEL SECURITY;
ALTER TABLE pagos DISABLE ROW LEVEL SECURITY;

-- Si alguna vez habilitaste políticas explícitamente, esto asegura que el anon key (la web) pueda operar
GRANT ALL ON ordenes_publicidad TO anon, authenticated;
GRANT ALL ON unidades_negocio TO anon, authenticated;
GRANT ALL ON tv TO anon, authenticated;
GRANT ALL ON pagos TO anon, authenticated;
