-- =====================================================================
-- SafraViva — 006: indicadores de gestão (views, sempre atualizadas)
-- Técnicas: CTE, UNION ALL, rateio proporcional com SUM() OVER, COALESCE de
-- preço realizado × preço de referência, ponto de equilíbrio.
-- =====================================================================

-- Plantio com talhão e propriedade; área efetiva = área do plantio ou, se vazia, a do talhão.
CREATE OR REPLACE VIEW fazenda.vw_plantio AS
SELECT
    p.*,
    coalesce(p.area_ha, t.area_ha)  AS area_efetiva_ha,
    t.nome                          AS talhao,
    t.solo_ad,
    t.propriedade_id,
    pr.nome                         AS propriedade,
    pr.demo
FROM fazenda.plantio p
JOIN fazenda.talhao t       ON t.id = p.talhao_id
JOIN fazenda.propriedade pr ON pr.id = t.propriedade_id;

-- Todos os custos de cada plantio, por categoria: diretos (operações + despesas do plantio)
-- e rateados (despesas da propriedade na safra, divididas pela área de cada plantio).
CREATE OR REPLACE VIEW fazenda.vw_custo_plantio AS
WITH diretos AS (
    SELECT plantio_id, coalesce(categoria_custo, 'outros') AS categoria, custo_total AS valor, 'operação' AS origem
    FROM fazenda.operacao WHERE coalesce(custo_total, 0) > 0
    UNION ALL
    SELECT plantio_id, categoria, valor, 'despesa do plantio'
    FROM fazenda.custo WHERE plantio_id IS NOT NULL
),
rateados AS (
    SELECT
        p.id AS plantio_id,
        c.categoria,
        c.valor * p.area_efetiva_ha / sum(p.area_efetiva_ha) OVER (PARTITION BY c.id) AS valor,
        'rateio da propriedade' AS origem
    FROM fazenda.custo c
    JOIN fazenda.vw_plantio p
      ON p.propriedade_id = c.propriedade_id AND p.safra = c.safra AND p.status <> 'planejado'
    WHERE c.plantio_id IS NULL
)
SELECT plantio_id, categoria, origem, sum(valor) AS valor
FROM (SELECT * FROM diretos UNION ALL SELECT * FROM rateados)
GROUP BY ALL;

-- Resultado econômico de cada plantio.
CREATE OR REPLACE VIEW fazenda.vw_resultado_plantio AS
WITH custos AS (
    SELECT plantio_id, sum(valor) AS custo_total FROM fazenda.vw_custo_plantio GROUP BY plantio_id
),
colhido AS (
    SELECT plantio_id, sum(sacas) AS sacas, sum(area_colhida_ha) AS area_colhida_ha, max(data) AS data_colheita
    FROM fazenda.colheita GROUP BY plantio_id
),
preco_vendas AS (
    SELECT propriedade_id, cultura, safra, sum(sacas * preco_sc) / sum(sacas) AS preco_medio, sum(sacas) AS sacas_vendidas
    FROM fazenda.venda GROUP BY ALL
),
referencia AS (
    -- custo CONAB por ha sem arrendamento e sem custo de oportunidade (terra e capital próprios)
    SELECT cultura, sum(valor_ha) AS custo_ref_ha
    FROM analytics.custo_referencia
    WHERE categoria NOT IN ('custo_variavel', 'custo_operacional', 'custo_total', 'renda_fatores', 'arrendamento')
    GROUP BY cultura
)
SELECT
    p.id AS plantio_id, p.propriedade_id, p.propriedade, p.demo, p.talhao, p.solo_ad, p.safra, p.temporada,
    p.cultura, p.cultivar, p.grupo_ciclo, p.data_plantio, p.status,
    p.area_efetiva_ha                                                   AS area_ha,
    coalesce(c.custo_total, 0)                                          AS custo_total,
    coalesce(c.custo_total, 0) / p.area_efetiva_ha                      AS custo_ha,
    h.sacas,
    h.data_colheita,
    h.sacas / coalesce(h.area_colhida_ha, p.area_efetiva_ha)            AS produtividade_sc_ha,
    p.produtividade_meta_sc_ha,
    coalesce(v.preco_medio, r.preco_sc)                                 AS preco_sc,
    CASE WHEN v.preco_medio IS NOT NULL THEN 'vendas' ELSE 'referência: ' || r.fonte END AS origem_preco,
    -- receita: colheita real × preço; antes de colher, estimada pela meta de produtividade
    CASE WHEN h.sacas IS NOT NULL THEN h.sacas
         ELSE p.produtividade_meta_sc_ha * p.area_efetiva_ha END        AS sacas_para_receita,
    h.sacas IS NULL                                                     AS receita_estimada,
    coalesce(h.sacas, p.produtividade_meta_sc_ha * p.area_efetiva_ha)
        * coalesce(v.preco_medio, r.preco_sc)                           AS receita,
    coalesce(h.sacas, p.produtividade_meta_sc_ha * p.area_efetiva_ha)
        * coalesce(v.preco_medio, r.preco_sc) - coalesce(c.custo_total, 0) AS margem,
    -- lavoura em andamento: custo previsto = maior entre o já lançado e a referência CONAB
    CASE WHEN p.status IN ('colhido', 'perdido') THEN coalesce(c.custo_total, 0)
         ELSE greatest(coalesce(c.custo_total, 0), coalesce(ref.custo_ref_ha, 0) * p.area_efetiva_ha) END AS custo_previsto,
    ref.custo_ref_ha,
    coalesce(h.sacas, p.produtividade_meta_sc_ha * p.area_efetiva_ha) * coalesce(v.preco_medio, r.preco_sc)
        - CASE WHEN p.status IN ('colhido', 'perdido') THEN coalesce(c.custo_total, 0)
               ELSE greatest(coalesce(c.custo_total, 0), coalesce(ref.custo_ref_ha, 0) * p.area_efetiva_ha) END
                                                                        AS margem_prevista,
    coalesce(c.custo_total, 0) / nullif(h.sacas, 0)                     AS custo_por_saca,
    -- quantas sacas por hectare pagam o custo (previsto, nas lavouras em andamento)
    CASE WHEN p.status IN ('colhido', 'perdido') THEN coalesce(c.custo_total, 0)
         ELSE greatest(coalesce(c.custo_total, 0), coalesce(ref.custo_ref_ha, 0) * p.area_efetiva_ha) END
        / p.area_efetiva_ha / coalesce(v.preco_medio, r.preco_sc)      AS ponto_equilibrio_sc_ha
FROM fazenda.vw_plantio p
LEFT JOIN custos c        ON c.plantio_id = p.id
LEFT JOIN colhido h       ON h.plantio_id = p.id
LEFT JOIN preco_vendas v  ON v.propriedade_id = p.propriedade_id AND v.cultura = p.cultura AND v.safra = p.safra
LEFT JOIN fazenda.preco_referencia r ON r.cultura = p.cultura
LEFT JOIN referencia ref ON ref.cultura = p.cultura;

-- Fase atual de cada lavoura plantada (dias após o plantio × duração típica das fases).
CREATE OR REPLACE VIEW fazenda.vw_estadio_atual AS
WITH ativos AS (
    -- "hoje" no horário de Brasília, mesmo em servidor UTC (GitHub Actions, Streamlit Cloud): D028
    SELECT *, date_diff('day', data_plantio, (current_timestamp AT TIME ZONE 'America/Sao_Paulo')::DATE) AS dias_apos_plantio
    FROM fazenda.vw_plantio
    WHERE status = 'plantado' AND data_plantio IS NOT NULL
)
SELECT
    a.id AS plantio_id, a.propriedade_id, a.demo, a.talhao, a.solo_ad, a.cultura, a.temporada, a.cultivar,
    a.data_plantio, a.dias_apos_plantio, a.area_efetiva_ha AS area_ha,
    coalesce(f.fase, CASE WHEN a.dias_apos_plantio > fim.ultimo_dia THEN 'pronta para colher' END) AS fase,
    f.sensivel_a,
    fim.ultimo_dia - a.dias_apos_plantio                       AS dias_para_colheita
FROM ativos a
LEFT JOIN analytics.dim_fase_duracao f
       ON f.cultura = a.cultura AND f.temporada = a.temporada
      AND a.dias_apos_plantio BETWEEN f.dia_inicio AND f.dia_fim
LEFT JOIN (SELECT cultura, temporada, max(dia_fim) AS ultimo_dia FROM analytics.dim_fase_duracao GROUP BY ALL) fim
       ON fim.cultura = a.cultura AND fim.temporada = a.temporada;
