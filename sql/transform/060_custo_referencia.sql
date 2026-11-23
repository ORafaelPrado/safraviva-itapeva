-- =====================================================================
-- analytics.custo_referencia — custo CONAB mais recente por cultura, na praça mais
-- parecida com Itapeva (trigo: a própria Itapeva; soja/milho: Ponta Grossa-PR).
-- Uma linha por cultura × categoria, em R$/ha, para comparar com o custo da fazenda.
-- =====================================================================
CREATE OR REPLACE TABLE analytics.custo_referencia AS
WITH preferencia AS (
    SELECT *,
           CASE WHEN cultura = 'trigo' AND local = 'Itapeva-SP' THEN 1
                WHEN local = 'Ponta Grossa-PR' THEN 2 ELSE 3 END AS prioridade
    FROM raw.conab_custo
),
mais_recente AS (
    SELECT cultura, arg_min(aba, (prioridade, -epoch(mes_referencia))) AS aba
    FROM preferencia
    GROUP BY cultura
)
SELECT
    c.cultura,
    c.local,
    c.aba,
    c.mes_referencia,
    c.produtividade_kg_ha / 60.0     AS produtividade_sc_ha,
    c.categoria,
    sum(c.valor_ha)                  AS valor_ha
FROM raw.conab_custo c
JOIN mais_recente m USING (cultura, aba)
GROUP BY ALL;
