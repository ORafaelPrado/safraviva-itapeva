-- Pergunta: que variável climática, em que fase, mais explica a produtividade na região?
-- Painel: 11 municípios × safras desde 1990 (NASA POWER, série comparável entre municípios).
-- O rendimento é medido como desvio da média móvel de 5 anos, para tirar a tendência tecnológica.
WITH painel AS (
    SELECT
        p.cultura, i.fase, i.ordem,
        p.desvio_vs_media_5a                              AS y,
        i.chuva_mm, i.balanco_mm, i.max_veranico_dias,
        i.dias_tmax_ge32, i.dias_tmin_le3, i.tmed_c
    FROM analytics.fato_producao p
    JOIN analytics.indices_fase i
      ON i.cultura = p.cultura AND i.ano_pam = p.ano
     AND i.codigo_ibge = p.codigo_local AND i.serie = 'nasa'
    WHERE p.nivel = 'municipio' AND p.ano >= 1990
      AND p.cultura IN ('soja', 'milho', 'trigo')
      AND p.desvio_vs_media_5a IS NOT NULL
      AND NOT p.suspeito_repeticao
      AND p.area_colhida_ha >= 500
)
SELECT
    cultura, fase,
    count(*)                                   AS n,
    round(corr(y, chuva_mm), 2)                AS r_chuva,
    round(corr(y, balanco_mm), 2)              AS r_balanco,
    round(corr(y, max_veranico_dias), 2)       AS r_veranico,
    round(corr(y, dias_tmax_ge32), 2)          AS r_calor,
    round(corr(y, dias_tmin_le3), 2)           AS r_frio,
    round(corr(y, tmed_c), 2)                  AS r_tmed
FROM painel
GROUP BY cultura, fase, ordem
ORDER BY cultura, ordem;
