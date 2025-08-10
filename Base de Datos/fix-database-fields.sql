-- Script para arreglar campos de texto largos en la tabla de películas
-- Ejecutar en PostgreSQL para expandir los límites de caracteres


-- Aumentar el tamaño de belong_to_collection (actualmente 255 caracteres)
ALTER TABLE peliculas 
ALTER COLUMN belong_to_collection TYPE CHARACTER VARYING(1000);

-- Aumentar el tamaño de original_title (actualmente sin límite específico, pero por si acaso)
ALTER TABLE peliculas 
ALTER COLUMN original_title TYPE CHARACTER VARYING(500);

-- Aumentar el tamaño de tagline (actualmente sin límite específico, pero por si acaso)
ALTER TABLE peliculas 
ALTER COLUMN tagline TYPE CHARACTER VARYING(1000);

-- Asegurar que otros campos de texto tengan suficiente espacio
ALTER TABLE peliculas 
ALTER COLUMN production_companies TYPE TEXT;

ALTER TABLE peliculas 
ALTER COLUMN production_countries TYPE TEXT;

ALTER TABLE peliculas 
ALTER COLUMN spoken_languages TYPE TEXT;

-- Verificar los cambios
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'peliculas' 
AND table_schema = 'public'
ORDER BY column_name;
