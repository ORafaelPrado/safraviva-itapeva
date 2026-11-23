-- =====================================================================
-- analytics.calibracao_nasa_a714 — viés mensal NASA POWER × estação A714
-- Só entram dias em que as duas fontes são válidas. O viés de temperatura
-- (A714 − NASA) é somado à NASA nos dias sem estação. A chuva não é corrigida
-- (a razão do total é ~1), mas a razão fica registrada para auditoria.
-- =====================================================================
CREATE OR REPLACE TABLE analytics.calibracao_nasa_a714 AS
SELECT
    month(i.data)                                         AS mes,
    count(*)                                              AS dias_pareados,
    avg(i.temp_min_c - n.temp_min_c)                      AS vies_tmin_c,
    avg(i.temp_max_c - n.temp_max_c)                      AS vies_tmax_c,
    avg(i.temp_c     - n.temp_c)                          AS vies_tmed_c,
    corr(i.temp_min_c, n.temp_min_c)                      AS corr_tmin,
    corr(i.chuva_mm,   n.chuva_mm)                        AS corr_chuva_diaria,
    sum(i.chuva_mm) / nullif(sum(n.chuva_mm), 0)          AS razao_chuva
FROM analytics.fato_clima_inmet_diario i
JOIN analytics.fato_clima_nasa_diario n
  ON n.data = i.data AND n.codigo_ibge = 3522406
WHERE i.estacao = 'A714'
  AND i.temp_min_c IS NOT NULL AND i.temp_max_c IS NOT NULL
  AND i.temp_c IS NOT NULL AND i.chuva_mm IS NOT NULL
GROUP BY month(i.data);
