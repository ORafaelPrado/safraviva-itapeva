-- =====================================================================
-- analytics.indices_fase — índices agroclimáticos por safra e fase fenológica
-- Grão: serie × município × cultura × ano da PAM × fase.
--
--   chuva_mm, dias_chuva ........ chuva acumulada e dias com chuva ≥ 1 mm
--   max_veranico_dias ........... maior sequência de dias secos (< 1 mm)
--   eto_mm ...................... evapotranspiração de referência (Hargreaves com radiação:
--                                 ETo = 0,0135 · (Tméd + 17,8) · Rs / 2,45)
--   balanco_mm .................. chuva − ETo (negativo = déficit hídrico)
--   gdd ......................... graus-dia acima de 10 °C
--   dias_tmax_ge32 .............. dias com calor ≥ 32 °C (abortamento de flores)
--   dias_tmin_le3 / tmin_min .... risco de geada (abrigo ≤ 3 °C ≈ geada na relva)
--   cobertura ................... fração dos dias com dado válido (usar ≥ 0,9)
-- =====================================================================
CREATE OR REPLACE TABLE analytics.indices_fase AS
WITH anos AS (
    SELECT unnest(range(1982, year(current_date) + 1)) AS ano_pam
),
periodos AS (
    SELECT
        f.cultura, f.ordem, f.fase, a.ano_pam,
        make_date(a.ano_pam + f.ini_offset, f.ini_mes, f.ini_dia) AS inicio,
        make_date(a.ano_pam + f.fim_offset, f.fim_mes, f.fim_dia) AS fim
    FROM analytics.dim_fase_fenologica f
    CROSS JOIN anos a
),
dias AS (
    SELECT
        p.cultura, p.ordem, p.fase, p.ano_pam, p.inicio, p.fim,
        c.serie, c.codigo_ibge, c.data, c.chuva_mm, c.temp_max_c, c.temp_min_c,
        coalesce(c.temp_c, (c.temp_max_c + c.temp_min_c) / 2)     AS tmed,
        c.radiacao_mj_m2,
        (c.chuva_mm < 1)::INTEGER                                  AS seco
    FROM periodos p
    JOIN analytics.clima_diario c
      ON c.data BETWEEN p.inicio AND p.fim
),
ilhas_secas AS (
    -- gaps and islands: dias secos consecutivos têm a mesma diferença de row_numbers
    SELECT
        *,
        row_number() OVER w_todos - row_number() OVER w_seco      AS ilha
    FROM dias
    WINDOW
        w_todos AS (PARTITION BY serie, codigo_ibge, cultura, ano_pam, fase ORDER BY data),
        w_seco  AS (PARTITION BY serie, codigo_ibge, cultura, ano_pam, fase, seco ORDER BY data)
),
veranicos AS (
    SELECT serie, codigo_ibge, cultura, ano_pam, fase, max(n) AS max_veranico_dias
    FROM (
        SELECT serie, codigo_ibge, cultura, ano_pam, fase, ilha, count(*) AS n
        FROM ilhas_secas
        WHERE seco = 1
        GROUP BY ALL
    )
    GROUP BY ALL
)
SELECT
    d.serie,
    d.codigo_ibge,
    d.cultura,
    d.ano_pam,
    d.ordem,
    d.fase,
    min(d.inicio)                                                  AS inicio,
    min(d.fim)                                                     AS fim,
    count(d.chuva_mm) / (date_diff('day', min(d.inicio), min(d.fim)) + 1.0) AS cobertura,
    sum(d.chuva_mm)                                                AS chuva_mm,
    count(*) FILTER (WHERE d.chuva_mm >= 1)                        AS dias_chuva,
    coalesce(v.max_veranico_dias, 0)                               AS max_veranico_dias,
    sum(0.0135 * (d.tmed + 17.8) * d.radiacao_mj_m2 / 2.45)        AS eto_mm,
    sum(d.chuva_mm) - sum(0.0135 * (d.tmed + 17.8) * d.radiacao_mj_m2 / 2.45) AS balanco_mm,
    sum(greatest(d.tmed - 10, 0))                                  AS gdd,
    count(*) FILTER (WHERE d.temp_max_c >= 32)                     AS dias_tmax_ge32,
    count(*) FILTER (WHERE d.temp_min_c <= 3)                      AS dias_tmin_le3,
    min(d.temp_min_c)                                              AS tmin_min,
    avg(d.tmed)                                                    AS tmed_c
FROM dias d
LEFT JOIN veranicos v USING (serie, codigo_ibge, cultura, ano_pam, fase)
GROUP BY d.serie, d.codigo_ibge, d.cultura, d.ano_pam, d.ordem, d.fase, v.max_veranico_dias;
