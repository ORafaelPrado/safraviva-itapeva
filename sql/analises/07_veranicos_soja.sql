-- Pergunta: com que frequência a soja de Itapeva enfrenta veranico no florescimento/enchimento?
-- Veranico relevante = ≥ 10 dias seguidos sem chuva ≥ 1 mm (severo ≥ 15).
SELECT
    (ano_pam - 1)::VARCHAR || '/' || right(ano_pam::VARCHAR, 2)                          AS safra,
    max(max_veranico_dias) FILTER (WHERE fase = 'florescimento')                          AS veranico_flor_dias,
    max(max_veranico_dias) FILTER (WHERE fase = 'enchimento')                             AS veranico_ench_dias,
    round(sum(chuva_mm)    FILTER (WHERE fase IN ('florescimento', 'enchimento')))        AS chuva_flor_ench_mm,
    round(sum(balanco_mm)  FILTER (WHERE fase IN ('florescimento', 'enchimento')))        AS balanco_mm,
    CASE WHEN max(max_veranico_dias) FILTER (WHERE fase IN ('florescimento', 'enchimento')) >= 15 THEN 'severo'
         WHEN max(max_veranico_dias) FILTER (WHERE fase IN ('florescimento', 'enchimento')) >= 10 THEN 'moderado'
         ELSE '-' END                                                                     AS classificacao
FROM analytics.indices_fase
WHERE serie = 'itapeva' AND cultura = 'soja'
  AND ano_pam BETWEEN 2007 AND year(current_date)
  AND cobertura >= 0.9
GROUP BY ano_pam
ORDER BY ano_pam;
