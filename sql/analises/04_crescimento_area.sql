-- Pergunta: onde e quanto a soja, o milho e o trigo cresceram em área desde 2000?
-- Técnicas: CAGR = (fim / início)^(1/n) − 1, FILTER por ano.
WITH extremos AS (
    SELECT
        nome_local, cultura,
        max(area_colhida_ha) FILTER (WHERE ano = 2000) AS area_2000,
        max(area_colhida_ha) FILTER (WHERE ano = 2025) AS area_2025
    FROM analytics.fato_producao
    WHERE nivel = 'municipio' AND cultura IN ('soja', 'milho', 'trigo')
    GROUP BY ALL
)
SELECT
    cultura,
    nome_local,
    area_2000::INTEGER                                                       AS area_2000_ha,
    area_2025::INTEGER                                                       AS area_2025_ha,
    CASE WHEN area_2000 > 0
         THEN round(100 * (pow(area_2025 / area_2000, 1 / 25.0) - 1), 1) END AS cagr_pct_aa
FROM extremos
WHERE coalesce(area_2025, 0) >= 1000
ORDER BY cultura, area_2025 DESC;
