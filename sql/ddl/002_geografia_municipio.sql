-- SafraViva — 002: centroide e área dos municípios (preenchidos pelo etl/ibge.py)
ALTER TABLE analytics.dim_municipio ADD COLUMN IF NOT EXISTS lat DOUBLE;
ALTER TABLE analytics.dim_municipio ADD COLUMN IF NOT EXISTS lon DOUBLE;
ALTER TABLE analytics.dim_municipio ADD COLUMN IF NOT EXISTS area_km2 DOUBLE;
