-- Pergunta: como área e produtividade de soja, milho e trigo evoluíram em Itapeva, década a década?
-- Técnicas: CTE, agregação por faixa temporal, LAG sobre a década anterior.
WITH decadas AS (
    SELECT
        cultura,
        (ano // 10) * 10                         AS decada,
        avg(area_colhida_ha)                     AS area_media_ha,
        avg(rendimento_sc_ha)                    AS rendimento_medio_sc_ha
    FROM analytics.fato_producao
    WHERE nivel = 'municipio' AND codigo_local = 3522406
      AND cultura IN ('soja', 'milho', 'trigo')
      AND NOT suspeito_repeticao
    GROUP BY ALL
)
SELECT
    cultura,
    decada::VARCHAR || 's'                                                         AS decada,
    round(area_media_ha)                                                           AS area_media_ha,
    round(rendimento_medio_sc_ha, 1)                                               AS rendimento_sc_ha,
    round(100 * (rendimento_medio_sc_ha / lag(rendimento_medio_sc_ha) OVER w - 1)) AS ganho_rend_vs_decada_ant_pct
FROM decadas
WINDOW w AS (PARTITION BY cultura ORDER BY decada)
ORDER BY cultura, decadas.decada;
