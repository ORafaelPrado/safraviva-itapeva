-- =====================================================================
-- analytics.janela_plantio — períodos contínuos de plantio com o mesmo risco ZARC
-- Técnica "gaps and islands": decêndios consecutivos com o mesmo risco
-- formam uma ilha (row_number por grupo − row_number geral = constante).
-- A ordenação usa o decêndio do ano-safra (julho = 1), para que janelas que
-- atravessam a virada do ano (milho 2ª safra: dez → mar) fiquem inteiras.
-- =====================================================================
CREATE OR REPLACE TABLE analytics.janela_plantio AS
WITH base AS (
    SELECT
        *,
        ((decendio - 19 + 36) % 36) + 1                  AS decendio_safra,
        -- decêndios de julho a dezembro caem no 1º ano da safra; jan–jun no 2º
        CASE WHEN decendio >= 19 THEN ano_safra_inicio ELSE ano_safra_inicio + 1 END AS ano_civil
    FROM analytics.fato_zarc
    WHERE indicado
),
ilhas AS (
    SELECT
        *,
        decendio_safra - row_number() OVER (
            PARTITION BY safra, codigo_ibge, nome_cultura, cod_ciclo, cod_solo, manejo, risco_pct
            ORDER BY decendio_safra
        )                                                AS ilha
    FROM base
),
agrupado AS (
    SELECT
        safra, codigo_ibge, municipio, nome_cultura, cod_ciclo, ciclo, cod_solo, solo, manejo,
        risco_pct,
        arg_min(decendio, decendio_safra)                AS dec_inicio,
        arg_min(ano_civil, decendio_safra)               AS ano_inicio,
        arg_max(decendio, decendio_safra)                AS dec_fim,
        arg_max(ano_civil, decendio_safra)               AS ano_fim,
        count(*)                                         AS n_decendios
    FROM ilhas
    GROUP BY safra, codigo_ibge, municipio, nome_cultura, cod_ciclo, ciclo, cod_solo, solo, manejo,
             risco_pct, ilha
)
SELECT
    * EXCLUDE (dec_inicio, ano_inicio, dec_fim, ano_fim),
    make_date(ano_inicio, (dec_inicio - 1) // 3 + 1, [1, 11, 21][(dec_inicio - 1) % 3 + 1]) AS data_inicio,
    CASE (dec_fim - 1) % 3
        WHEN 0 THEN make_date(ano_fim, (dec_fim - 1) // 3 + 1, 10)
        WHEN 1 THEN make_date(ano_fim, (dec_fim - 1) // 3 + 1, 20)
        ELSE last_day(make_date(ano_fim, (dec_fim - 1) // 3 + 1, 1))
    END                                                  AS data_fim,
    CASE risco_pct WHEN 20 THEN 'baixo' WHEN 30 THEN 'médio' WHEN 40 THEN 'alto' END AS nivel_risco
FROM agrupado;
