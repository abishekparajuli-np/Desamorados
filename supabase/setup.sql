-- ============================================================
-- SewaSathi - PostGIS Vector Tiles Setup for Supabase
-- Run these SQL commands in order in your Supabase SQL editor
-- ============================================================

-- 1. Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS "postgis" WITH SCHEMA "extensions";

-- 2. Add geometry column to providers table
ALTER TABLE public.providers 
ADD COLUMN IF NOT EXISTS wkb_geometry geometry(Point, 4326);

-- 3. Populate geometry from existing latitude/longitude columns
UPDATE public.providers 
SET wkb_geometry = ST_SetSRID(ST_MakePoint(
  (SELECT longitude FROM public.users WHERE public.users.id = public.providers.user_id),
  (SELECT latitude FROM public.users WHERE public.users.id = public.providers.user_id)
), 4326)
WHERE wkb_geometry IS NULL
AND EXISTS (
  SELECT 1 FROM public.users 
  WHERE public.users.id = public.providers.user_id 
  AND public.users.latitude IS NOT NULL 
  AND public.users.longitude IS NOT NULL
);

-- 4. Create spatial index for Web Mercator (3857) - optimal for tile rendering
CREATE INDEX IF NOT EXISTS providers_webmercator 
ON public.providers 
USING gist (st_transform(wkb_geometry, 3857)) 
WHERE wkb_geometry IS NOT NULL;

-- 5. Enable Row Level Security on providers table
ALTER TABLE public.providers ENABLE ROW LEVEL SECURITY;

-- 6. Create RLS policy for public read access (allows querying via MVT tiles)
CREATE POLICY "Enable read access for all users" 
ON public.providers 
FOR SELECT 
USING (true);

-- 7. MVT (Mapbox Vector Tiles) function - streams providers as vector tiles
-- Call: SELECT mvt(z, x, y) where z = zoom level, x = tile column, y = tile row
CREATE OR REPLACE FUNCTION public.mvt(z integer, x integer, y integer)
RETURNS bytea
LANGUAGE plpgsql
IMMUTABLE STRICT PARALLEL SAFE
AS $$
DECLARE
  result bytea;
BEGIN
  WITH bounds AS (
    SELECT ST_TileEnvelope(z, x, y) AS geom
  ),
  providers_in_tile AS (
    SELECT
      p.id,
      p.user_id,
      u.name,
      u.city,
      u.latitude,
      u.longitude,
      u.is_female,
      p.rating,
      p.trust_score,
      p.is_available,
      p.hourly_rate,
      CASE WHEN z >= 12 THEN p.bio ELSE NULL END AS bio,
      ST_AsMVTGeom(
        ST_Transform(p.wkb_geometry, 3857),
        bounds.geom,
        4096,
        64,
        true
      ) AS geom
    FROM public.providers p
    INNER JOIN public.users u ON p.user_id = u.id
    CROSS JOIN bounds
    WHERE ST_Intersects(
      ST_Transform(p.wkb_geometry, 3857),
      bounds.geom
    )
    AND p.is_available = true
  )
  SELECT ST_AsMVT(providers_in_tile.*, 'providers', 4096, 'geom')
  INTO result
  FROM providers_in_tile;

  RETURN COALESCE(result, '\x00'::bytea);
END;
$$;

-- 8. Grant execute permission on mvt function to anonymous users
GRANT EXECUTE ON FUNCTION public.mvt(integer, integer, integer) TO anon, authenticated;

-- 9. Add helpful comment
COMMENT ON FUNCTION public.mvt IS 'Streams provider locations as Mapbox Vector Tiles for use with MapLibre GL JS';
