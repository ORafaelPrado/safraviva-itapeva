-- Pergunta: Itapeva produz mais por hectare que SP e PR? A vantagem é estável?
-- Técnicas: pivot condicional, média móvel de 5 anos (window frame), QUALIFY.
WITH serie AS (
    SELECT
        cultura, ano,
        max(rendimento_sc_ha) FILTER (WHERE nivel = 'municipio' AND codigo_local = 3522406 AND NOT suspeito_repeticao) AS itapeva,
        max(rendimento_sc_ha) FILTER (WHERE nivel = 'uf' AND codigo_local = 35)                                     AS sp,
        max(rendimento_sc_ha) FILTER (WHERE nivel = 'uf' AND codigo_local = 41)                                     AS pr
    FROM analytics.fato_producao
    WHERE cultura IN ('soja', 'milho', 'trigo')
    GROUP BY ALL
)
SELECT
    cultura,
    ano,
    round(avg(itapeva) OVER w, 1)                           AS itapeva_mm5,
    round(avg(sp)      OVER w, 1)                           AS sp_mm5,
    round(avg(pr)      OVER w, 1)                           AS pr_mm5,
    round(100 * (avg(itapeva) OVER w / avg(sp) OVER w - 1)) AS vantagem_vs_sp_pct
FROM serie
WINDOW w AS (PARTITION BY cultura ORDER BY ano ROWS BETWEEN 4 PRECEDING AND CURRENT ROW)
QUALIFY ano IN (1990, 2000, 2010, 2015, 2020, 2025)
ORDER BY cultura, ano;
