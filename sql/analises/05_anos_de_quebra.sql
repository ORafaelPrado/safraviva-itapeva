-- Pergunta: quais safras quebraram em Itapeva e o que o clima mostra na fase crítica?
-- Quebra = rendimento ≥ 15% abaixo da média dos 5 anos anteriores.
-- Técnicas: JOIN fato × índices, pivot por fase com FILTER.
WITH quebras AS (
    SELECT cultura, ano, rendimento_sc_ha, desvio_vs_media_5a
    FROM analytics.fato_producao
    WHERE nivel = 'municipio' AND codigo_local = 3522406
      AND cultura IN ('soja', 'milho', 'trigo')
      AND desvio_vs_media_5a <= -0.15
      AND ano >= 1983 AND NOT suspeito_repeticao
)
SELECT
    q.cultura,
    q.ano,
    round(q.rendimento_sc_ha, 1)                                                     AS sc_ha,
    round(100 * q.desvio_vs_media_5a)                                                AS desvio_pct,
    round(max(i.chuva_mm)    FILTER (WHERE i.fase = 'florescimento'))                AS chuva_flor_mm,
    round(max(i.balanco_mm)  FILTER (WHERE i.fase = 'florescimento'))                AS balanco_flor_mm,
    max(i.max_veranico_dias) FILTER (WHERE i.fase IN ('florescimento', 'enchimento')) AS veranico_max_dias,
    max(i.dias_tmax_ge32)    FILTER (WHERE i.fase = 'florescimento')                 AS dias_calor_flor,
    round(min(i.tmin_min), 1)                                                        AS tmin_ciclo_c,
    round(max(i.chuva_mm)    FILTER (WHERE i.fase = 'colheita'))                     AS chuva_colheita_mm
FROM quebras q
LEFT JOIN analytics.indices_fase i
       ON i.cultura = q.cultura AND i.ano_pam = q.ano
      AND i.codigo_ibge = 3522406 AND i.serie = 'itapeva'
GROUP BY ALL
ORDER BY q.cultura, q.ano;
