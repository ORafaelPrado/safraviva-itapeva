-- Pergunta: o clima de Itapeva mudou desde os anos 1980?
-- Fonte: NASA POWER no centroide de Itapeva (série longa e homogênea).
-- Verão da safra = out–mar; inverno = jun–ago.
WITH d AS (
    SELECT
        t.ano_safra_inicio,
        (t.ano_safra_inicio // 10) * 10                     AS decada,
        c.chuva_mm, c.temp_max_c, c.temp_min_c,
        month(c.data) IN (10, 11, 12, 1, 2, 3)              AS verao,
        month(c.data) IN (6, 7, 8)                          AS inverno
    FROM analytics.clima_diario c
    JOIN analytics.dim_tempo t USING (data)
    WHERE c.serie = 'nasa' AND c.codigo_ibge = 3522406
      AND t.ano_safra_inicio BETWEEN 1981 AND 2024
),
por_safra AS (
    SELECT
        decada, ano_safra_inicio,
        sum(chuva_mm)   FILTER (WHERE verao)                AS chuva_verao_mm,
        avg(temp_max_c) FILTER (WHERE verao)                AS tmax_verao_c,
        count(*) FILTER (WHERE verao AND temp_max_c >= 32)  AS dias_calor_verao,
        avg(temp_min_c) FILTER (WHERE inverno)              AS tmin_inverno_c,
        count(*) FILTER (WHERE inverno AND temp_min_c <= 3) AS dias_frio_inverno
    FROM d
    GROUP BY ALL
)
SELECT
    decada::VARCHAR || 's'                  AS decada,
    count(*)                                AS safras,
    round(avg(chuva_verao_mm))              AS chuva_verao_mm,
    round(avg(tmax_verao_c), 1)             AS tmax_verao_c,
    round(avg(dias_calor_verao), 1)         AS dias_ge32_verao,
    round(avg(tmin_inverno_c), 1)           AS tmin_inverno_c,
    round(avg(dias_frio_inverno), 1)        AS dias_le3_inverno
FROM por_safra
GROUP BY por_safra.decada
ORDER BY por_safra.decada;
