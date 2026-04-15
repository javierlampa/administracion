ALTER TABLE public.perfiles ENABLE ROW LEVEL SECURITY;

-- Remove any existing policies to avoid conflicts
DROP POLICY IF EXISTS "Permitir SELECT a perfiles" ON public.perfiles;
DROP POLICY IF EXISTS "Permitir UPDATE a perfiles" ON public.perfiles;
DROP POLICY IF EXISTS "Permitir INSERT a perfiles" ON public.perfiles;
DROP POLICY IF EXISTS "Permitir DELETE a perfiles" ON public.perfiles;

-- Allow authenticated users to view profiles
CREATE POLICY "Permitir SELECT a perfiles"
ON public.perfiles FOR SELECT
USING (auth.role() = 'authenticated');

-- Allow authenticated users to insert profiles (needed for first-time creation from handle_new_user, though that runs with SECURITY DEFINER and bypasses RLS)
CREATE POLICY "Permitir INSERT a perfiles"
ON public.perfiles FOR INSERT
WITH CHECK (auth.role() = 'authenticated');

-- Allow authenticated users to update profiles (needed for the admin dashboard updates)
CREATE POLICY "Permitir UPDATE a perfiles"
ON public.perfiles FOR UPDATE
USING (auth.role() = 'authenticated')
WITH CHECK (auth.role() = 'authenticated');

-- Allow authenticated users to delete profiles
CREATE POLICY "Permitir DELETE a perfiles"
ON public.perfiles FOR DELETE
USING (auth.role() = 'authenticated');
