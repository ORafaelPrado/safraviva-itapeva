-- Pergunta: em que meses há risco de geada em Itapeva e com que frequência?
-- Fonte: estação A714 (2006→). Abrigo ≤ 3 °C ≈ geada na relva; ≤ 1 °C = geada forte provável.
WITH anos AS (
    SELECT count(DISTINCT year(data)) AS n
    FROM analytics.fato_clima_inmet_diario
    WHERE estacao = 'A714' AND temp_min_c IS NOT NULL
)
SELECT
    month(data)                                                                         AS mes,
    count(*) FILTER (WHERE temp_min_c <= 3)                                             AS dias_tmin_le3,
    count(*) FILTER (WHERE temp_min_c <= 1)                                             AS dias_tmin_le1,
    round(count(*) FILTER (WHERE temp_min_c <= 3) / any_value(anos.n), 2)               AS media_dias_por_ano,
    round(100.0 * count(DISTINCT year(data)) FILTER (WHERE temp_min_c <= 3) / any_value(anos.n)) AS pct_anos_com_evento,
    round(min(temp_min_c), 1)                                                           AS tmin_absoluta_c
FROM analytics.fato_clima_inmet_diario, anos
WHERE estacao = 'A714' AND temp_min_c IS NOT NULL
GROUP BY month(data)
HAVING count(*) FILTER (WHERE temp_min_c <= 5) > 0
ORDER BY mes;
