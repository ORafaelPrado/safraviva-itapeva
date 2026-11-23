-- Pergunta: quando dá para pulverizar nos próximos dias?
-- Hora boa = vento 3–10 km/h, Delta T 2–8 °C, probabilidade de chuva < 30% e temperatura < 30 °C, entre 6h e 20h.
WITH horas AS (
    SELECT
        *,
        hour(ts_local) BETWEEN 6 AND 20
        AND vento_kmh BETWEEN 3 AND 10
        AND delta_t_c BETWEEN 2 AND 8
        AND coalesce(prob_chuva_pct, 0) < 30
        AND temp_c < 30                                     AS boa
    FROM analytics.vw_previsao_horaria_atual
)
SELECT
    strftime(CAST(ts_local AS DATE), '%d/%m %a')                                    AS dia,
    count(*) FILTER (WHERE boa)                                                     AS horas_boas,
    string_agg(strftime(ts_local, '%Hh'), ' ' ORDER BY ts_local) FILTER (WHERE boa) AS horarios,
    round(max(prob_chuva_pct))                                                      AS prob_chuva_max_pct,
    round(max(vento_kmh))                                                           AS vento_max_kmh
FROM horas
WHERE ts_local >= current_localtimestamp()   -- só horas que ainda não passaram
GROUP BY CAST(ts_local AS DATE)
ORDER BY CAST(ts_local AS DATE)
LIMIT 7;
