-- =====================================================================
-- Clima diário consolidado
--  1. analytics.fato_clima_inmet_diario — horário da estação agregado ao dia
--     LOCAL (UTC-3); só vale o dia que tem ≥ 20 h válidas da variável.
--  2. analytics.fato_clima_nasa_diario — grade NASA POWER por município.
--  A série de Itapeva (A714 + NASA calibrada) é montada em 022.
-- =====================================================================
CREATE OR REPLACE TABLE analytics.fato_clima_inmet_diario AS
WITH h AS (
    SELECT *, CAST(ts_utc - INTERVAL 3 HOUR AS DATE) AS data
    FROM raw.inmet_horario
)
SELECT
    estacao,
    data,
    count(temp_c)                                                         AS horas_validas,
    CASE WHEN count(chuva_mm)   >= 20 THEN sum(chuva_mm)            END   AS chuva_mm,
    CASE WHEN count(temp_max_c) >= 20 THEN max(temp_max_c)          END   AS temp_max_c,
    CASE WHEN count(temp_min_c) >= 20 THEN min(temp_min_c)          END   AS temp_min_c,
    CASE WHEN count(temp_c)     >= 20 THEN avg(temp_c)              END   AS temp_c,
    CASE WHEN count(umid_pct)   >= 20 THEN avg(umid_pct)            END   AS umid_pct,
    CASE WHEN count(umid_min_pct) >= 20 THEN min(umid_min_pct)      END   AS umid_min_pct,
    CASE WHEN count(vento_ms)   >= 20 THEN avg(vento_ms)            END   AS vento_ms,
    max(rajada_ms)                                                        AS rajada_max_ms,
    CASE WHEN count(temp_c)     >= 20
         THEN sum(greatest(radiacao_kj_m2, 0)) / 1000.0              END  AS radiacao_mj_m2
FROM h
GROUP BY estacao, data;

CREATE OR REPLACE TABLE analytics.fato_clima_nasa_diario AS
SELECT
    codigo_ibge,
    CAST(data AS DATE)          AS data,
    chuva_mm,
    temp_max_c,
    temp_min_c,
    temp_c,
    umid_pct,
    vento_2m_ms,
    radiacao_mj_m2
FROM raw.nasa_power_diario;
