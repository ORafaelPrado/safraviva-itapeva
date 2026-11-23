-- =====================================================================
-- analytics.fato_producao — PAM em formato largo (uma linha por local × cultura × ano)
-- Inclui métricas derivadas com window functions: variação anual, média
-- móvel de 5 anos e desvio em relação à tendência (base para "ano de quebra").
-- suspeito_repeticao: o rendimento é idêntico ao do ano anterior e a produção
-- varia menos de 0,1%, sinal de que o informante repetiu o número (ver docs/fontes.md).
-- =====================================================================
CREATE OR REPLACE TABLE analytics.fato_producao AS
WITH largo AS (
    SELECT
        p.nivel,
        p.codigo_local,
        p.nome_local,
        c.slug                                                   AS cultura,
        p.ano,
        max(p.valor) FILTER (WHERE p.variavel_codigo = 109)      AS area_plantada_ha,
        max(p.valor) FILTER (WHERE p.variavel_codigo = 216)      AS area_colhida_ha,
        max(p.valor) FILTER (WHERE p.variavel_codigo = 214)      AS producao_t,
        max(p.valor) FILTER (WHERE p.variavel_codigo = 112)      AS rendimento_kg_ha,
        max(p.valor) FILTER (WHERE p.variavel_codigo = 215)      AS valor_mil_reais
    FROM raw.sidra_pam p
    JOIN analytics.dim_cultura c ON c.codigo_sidra = p.cultura_codigo
    GROUP BY ALL
)
SELECT
    *,
    rendimento_kg_ha / 60.0                                       AS rendimento_sc_ha,
    CASE WHEN area_plantada_ha > 0
         THEN 1 - area_colhida_ha / area_plantada_ha END          AS perda_area_pct,
    rendimento_kg_ha / nullif(lag(rendimento_kg_ha) OVER w, 0) - 1 AS var_rendimento_aa,
    avg(rendimento_kg_ha) OVER (w ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING) AS media_movel_5a_kg_ha,
    rendimento_kg_ha
        / nullif(avg(rendimento_kg_ha) OVER (w ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING), 0)
        - 1                                                       AS desvio_vs_media_5a,
    coalesce(
        rendimento_kg_ha = lag(rendimento_kg_ha) OVER w
        AND abs(producao_t / nullif(lag(producao_t) OVER w, 0) - 1) < 0.001,
        FALSE
    )                                                             AS suspeito_repeticao
FROM largo
WINDOW w AS (PARTITION BY nivel, codigo_local, cultura ORDER BY ano);
