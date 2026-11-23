-- =====================================================================
-- 1. analytics.fato_clima_itapeva — melhor série possível para Itapeva:
--    A714 quando o dia é válido; NASA POWER com viés mensal corrigido nos demais.
-- 2. analytics.clima_diario — tabela única consumida pelos índices:
--    serie = 'nasa'     → NASA bruta em todos os municípios (comparável entre eles, 1981→)
--    serie = 'itapeva'  → série 1 acima (mais fiel a Itapeva)
-- =====================================================================
CREATE OR REPLACE TABLE analytics.fato_clima_itapeva AS
SELECT
    n.data,
    coalesce(i.chuva_mm, n.chuva_mm)                                  AS chuva_mm,
    coalesce(i.temp_max_c, n.temp_max_c + coalesce(c.vies_tmax_c, 0)) AS temp_max_c,
    coalesce(i.temp_min_c, n.temp_min_c + coalesce(c.vies_tmin_c, 0)) AS temp_min_c,
    coalesce(i.temp_c,     n.temp_c     + coalesce(c.vies_tmed_c, 0)) AS temp_c,
    coalesce(i.umid_pct, n.umid_pct)                                  AS umid_pct,
    coalesce(i.radiacao_mj_m2, n.radiacao_mj_m2)                      AS radiacao_mj_m2,
    CASE WHEN i.chuva_mm IS NOT NULL AND i.temp_min_c IS NOT NULL THEN 'INMET A714'
         WHEN i.data IS NOT NULL THEN 'misto'
         ELSE 'NASA POWER calibrada' END                              AS fonte,
    -- leituras originais lado a lado, para auditoria
    i.chuva_mm   AS chuva_inmet_mm,  n.chuva_mm   AS chuva_nasa_mm,
    i.temp_min_c AS tmin_inmet_c,    n.temp_min_c AS tmin_nasa_c
FROM analytics.fato_clima_nasa_diario n
LEFT JOIN analytics.fato_clima_inmet_diario i
       ON i.data = n.data AND i.estacao = 'A714'
LEFT JOIN analytics.calibracao_nasa_a714 c
       ON c.mes = month(n.data)
WHERE n.codigo_ibge = 3522406;

CREATE OR REPLACE TABLE analytics.clima_diario AS
SELECT 'nasa' AS serie, codigo_ibge, data, chuva_mm, temp_max_c, temp_min_c, temp_c, radiacao_mj_m2
FROM analytics.fato_clima_nasa_diario
UNION ALL
SELECT 'itapeva', 3522406, data, chuva_mm, temp_max_c, temp_min_c, temp_c, radiacao_mj_m2
FROM analytics.fato_clima_itapeva;
