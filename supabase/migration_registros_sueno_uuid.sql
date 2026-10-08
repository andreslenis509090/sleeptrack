-- =============================================================================
-- SleepTrack - Migración SQL: Unificación de id_usuario a UUID
-- Archivo: supabase/migration_registros_sueno_uuid.sql
-- =============================================================================
-- Este script adapta la tabla registros_sueno para utilizar UUID como id_usuario,
-- referenciando auth.users(id) y manteniendo la regla RN01 (usuario + fecha único).
-- =============================================================================

-- 1. Si la tabla registros_sueno ya existe con id_usuario BIGINT:
-- Nota: Si hay datos existentes con IDs numéricos, deben limpiarse o mapearse previamente.
ALTER TABLE public.registros_sueno
    DROP CONSTRAINT IF EXISTS uq_registros_sueno_usuario_fecha,
    DROP CONSTRAINT IF EXISTS registros_sueno_id_usuario_fkey;

-- 2. Modificar el tipo de columna a UUID
ALTER TABLE public.registros_sueno
    ALTER COLUMN id_usuario TYPE UUID USING id_usuario::text::uuid;

-- 3. Vincular clave foránea a auth.users con borrado en cascada (RF10)
ALTER TABLE public.registros_sueno
    ADD CONSTRAINT fk_registros_sueno_usuario
    FOREIGN KEY (id_usuario) REFERENCES auth.users(id) ON DELETE CASCADE;

-- 4. Recrear restricción única RN01: 1 registro por usuario por fecha
ALTER TABLE public.registros_sueno
    ADD CONSTRAINT uq_registros_sueno_usuario_fecha
    UNIQUE (id_usuario, fecha);

-- 5. Habilitar RLS en registros_sueno
ALTER TABLE public.registros_sueno ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Usuarios acceden a sus propios registros de sueno" ON public.registros_sueno;
CREATE POLICY "Usuarios acceden a sus propios registros de sueno"
ON public.registros_sueno
FOR ALL
TO authenticated
USING (auth.uid() = id_usuario)
WITH CHECK (auth.uid() = id_usuario);
