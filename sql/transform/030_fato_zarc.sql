-- =====================================================================
-- analytics.fato_zarc — tábua de risco em formato longo (uma linha por decêndio)
-- risco_pct: 20, 30 ou 40 = risco de perda indicado pelo ZARC; 0 = plantio não indicado.
-- Os códigos vêm do dicionário oficial do MAPA (docs/fontes.md).
-- =====================================================================
CREATE OR REPLACE TABLE analytics.fato_zarc AS
WITH longo AS (
    UNPIVOT raw.zarc_tabua
    ON COLUMNS('^dec[0-9]+$')
    INTO NAME coluna VALUE risco_pct
)
SELECT
    safra,
    safraini                                        AS ano_safra_inicio,
    geocodigo                                       AS codigo_ibge,
    municipio,
    nome_cultura,
    cod_ciclo,
    CASE cod_ciclo WHEN 13 THEN 'Perene' WHEN 19 THEN 'Semiperene'
         WHEN 20 THEN 'Grupo I' WHEN 21 THEN 'Grupo II' WHEN 22 THEN 'Grupo III'
         WHEN 24 THEN 'Grupo IV' WHEN 25 THEN 'Grupo V' WHEN 26 THEN 'Grupo VI'
    END                                             AS ciclo,
    cod_solo,
    CASE cod_solo WHEN 1 THEN 'Arenoso' WHEN 2 THEN 'Textura média' WHEN 3 THEN 'Argiloso'
         ELSE 'AD' || (cod_solo - 10)::VARCHAR
    END                                             AS solo,
    nome_outros_manejos                             AS manejo,
    nome_clima                                      AS clima,
    portaria,
    CAST(replace(coluna, 'dec', '') AS INTEGER)     AS decendio,
    risco_pct,
    risco_pct > 0                                   AS indicado
FROM longo;
