-- Pergunta: quanto a NASA POWER erra em relação à estação de Itapeva, mês a mês?
SELECT
    mes,
    dias_pareados,
    round(vies_tmin_c, 2)        AS vies_tmin_c,
    round(vies_tmax_c, 2)        AS vies_tmax_c,
    round(corr_tmin, 2)          AS corr_tmin,
    round(corr_chuva_diaria, 2)  AS corr_chuva_diaria,
    round(razao_chuva, 2)        AS razao_chuva
FROM analytics.calibracao_nasa_a714
ORDER BY mes;
