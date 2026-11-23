-- Pergunta: qual o peso de Itapeva na região e como ela se posiciona em área e produtividade?
-- Técnicas: RANK, participação com SUM() OVER, média de 5 anos (2021–2025).
WITH base AS (
    SELECT
        nome_local, cultura,
        avg(area_colhida_ha)  FILTER (WHERE ano BETWEEN 2021 AND 2025)                            AS area_5a,
        avg(rendimento_sc_ha) FILTER (WHERE ano BETWEEN 2021 AND 2025 AND NOT suspeito_repeticao) AS rend_5a
    FROM analytics.fato_producao
    WHERE nivel = 'municipio' AND cultura IN ('soja', 'milho', 'trigo')
    GROUP BY ALL
)
SELECT
    cultura,
    nome_local,
    round(area_5a)                                                      AS area_media_ha,
    round(100 * area_5a / sum(area_5a) OVER (PARTITION BY cultura), 1)  AS participacao_regiao_pct,
    rank() OVER (PARTITION BY cultura ORDER BY area_5a DESC NULLS LAST) AS rank_area,
    round(rend_5a, 1)                                                   AS rendimento_sc_ha,
    rank() OVER (PARTITION BY cultura ORDER BY rend_5a DESC NULLS LAST) AS rank_rendimento
FROM base
WHERE area_5a > 0
ORDER BY cultura, rank_area;
