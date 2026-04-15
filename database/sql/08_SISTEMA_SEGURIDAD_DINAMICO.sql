-- 08. SISTEMA DE SEGURIDAD DINÁMICO (ROLES Y PERMISOS RBAC)
-- Este script crea la infraestructura para gestionar usuarios, roles y permisos individuales.

-- 1. TABLA DE ROLES (DINÁMICA)
CREATE TABLE IF NOT EXISTS public.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. TABLA DE PERFILES (EXTENSIÓN DE AUTH.USERS)
CREATE TABLE IF NOT EXISTS public.perfiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nombre TEXT,
    apellido TEXT,
    username TEXT UNIQUE NOT NULL,
    numero_celular TEXT,
    role_id UUID REFERENCES public.roles(id) ON DELETE SET NULL,
    whatsapp_habilitado BOOLEAN DEFAULT FALSE,
    permisos JSONB DEFAULT '{
        "dashboard": false,
        "monitoreo": false,
        "todas_op": false,
        "cobranzas": false,
        "grilla_tecnica": false,
        "usuarios": false
    }'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Habilitar RLS en Perfiles
ALTER TABLE public.perfiles ENABLE ROW LEVEL SECURITY;

-- 3. FUNCIONES DE AYUDA (PERMISSION CHECK)
CREATE OR REPLACE FUNCTION public.has_permission(p_user_id UUID, p_module TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN COALESCE(
        (SELECT (permisos->>p_module)::BOOLEAN 
         FROM public.perfiles 
         WHERE id = p_user_id),
        FALSE
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. INSERTAR ROLES INICIALES
INSERT INTO public.roles (nombre, descripcion) VALUES
('ADMIN', 'Acceso total al sistema y gestión de usuarios'),
('ADMINISTRACION', 'Gestión operativa y contable'),
('GERENCIA', 'Visualización de reportes e indicadores')
ON CONFLICT (nombre) DO NOTHING;

-- 5. TRIGGER PARA AUTO-CREAR PERFIL AL REGISTRAR USUARIO
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.perfiles (id, username, nombre, apellido, role_id, permisos)
    VALUES (
        NEW.id, 
        COALESCE(NEW.raw_user_meta_data->>'username', SPLIT_PART(NEW.email, '@', 1)),
        NEW.raw_user_meta_data->>'nombre',
        NEW.raw_user_meta_data->>'apellido',
        (SELECT id FROM public.roles WHERE nombre = 'ADMIN' LIMIT 1), -- Por defecto Admin para el primero (ajustar luego)
        '{"dashboard": true, "monitoreo": true, "todas_op": true, "cobranzas": true, "grilla_tecnica": true, "usuarios": true}'::jsonb
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
