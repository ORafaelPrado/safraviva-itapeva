-- =====================================================================
-- Previsão vigente (último retrato emitido) — base do "Clima Agora" e dos alertas.
-- =====================================================================
CREATE OR REPLACE VIEW analytics.vw_previsao_diaria_atual AS
SELECT *
FROM raw.previsao_diaria
WHERE emitida_em = (SELECT max(emitida_em) FROM raw.previsao_diaria);

CREATE OR REPLACE VIEW analytics.vw_previsao_horaria_atual AS
SELECT
    *,
    -- Delta T = temperatura do ar − temperatura de bulbo úmido (Stull, 2011).
    -- Faixa ideal para pulverização: 2 a 8 °C.
    temp_c - (
        temp_c * atan(0.151977 * sqrt(umid_pct + 8.313659))
        + atan(temp_c + umid_pct) - atan(umid_pct - 1.676331)
        + 0.00391838 * pow(umid_pct, 1.5) * atan(0.023101 * umid_pct)
        - 4.686035
    )                                                       AS delta_t_c
FROM raw.previsao_horaria
WHERE emitida_em = (SELECT max(emitida_em) FROM raw.previsao_horaria);
