-- =============================================================================
-- SleepTrack - Esquema DDL para Perfiles de Usuario (Supabase PostgreSQL)
-- Archivo: supabase/schema_perfiles_usuario.sql
-- Módulo: Autenticación y Gestión de Perfiles (RF01, RF02, RF10, RNF01, RNF02, RNF04)
-- =============================================================================

-- Habilitar extensión para UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 1. Tabla de Perfiles de Usuario (perfiles_usuario)
-- Vinculada directamente al usuario de Supabase Auth (auth.users).
-- Las contraseñas NUNCA se guardan aquí; son gestionadas por Supabase Auth (RNF01).
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.perfiles_usuario (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    ocupacion VARCHAR(100) NOT NULL,
    meta_sueno NUMERIC(4, 2) NOT NULL DEFAULT 8.0 CHECK (meta_sueno >= 1.0 AND meta_sueno <= 24.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Índices para optimización de consultas
CREATE INDEX IF NOT EXISTS idx_perfiles_usuario_email ON public.perfiles_usuario(email);

-- Trigger para actualización automática de updated_at
CREATE OR REPLACE FUNCTION public.set_current_timestamp_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_perfiles_usuario_updated_at ON public.perfiles_usuario;
CREATE TRIGGER trg_perfiles_usuario_updated_at
BEFORE UPDATE ON public.perfiles_usuario
FOR EACH ROW
EXECUTE FUNCTION public.set_current_timestamp_updated_at();

-- =============================================================================
-- 2. Configuración de Seguridad a Nivel de Fila (Row Level Security - RLS)
-- =============================================================================
ALTER TABLE public.perfiles_usuario ENABLE ROW LEVEL SECURITY;

-- Política de Consulta: Cada usuario autenticado solo puede leer su propio perfil
CREATE POLICY "Los usuarios pueden ver su propio perfil"
ON public.perfiles_usuario
FOR SELECT
TO authenticated
USING (auth.uid() = id);

-- Política de Inserción: Cada usuario autenticado solo puede crear su propio perfil
CREATE POLICY "Los usuarios pueden insertar su propio perfil"
ON public.perfiles_usuario
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = id);

-- Política de Actualización: Cada usuario autenticado solo puede actualizar su propio perfil
CREATE POLICY "Los usuarios pueden actualizar su propio perfil"
ON public.perfiles_usuario
FOR UPDATE
TO authenticated
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- Política de Eliminación: Cada usuario autenticado solo puede eliminar su propio perfil (RF10)
CREATE POLICY "Los usuarios pueden eliminar su propio perfil"
ON public.perfiles_usuario
FOR DELETE
TO authenticated
USING (auth.uid() = id);
