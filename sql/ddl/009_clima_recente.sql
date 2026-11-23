-- =====================================================================
-- SafraViva — 009: clima dos últimos dias (Open-Meteo, past_days)
-- Fecha o buraco entre o último dia observado (NASA POWER tem alguns dias de atraso;
-- o pacote do INMET é mensal) e o início da previsão, no balanço hídrico das lavouras.
-- =====================================================================
CREATE TABLE IF NOT EXISTS raw.clima_recente_diario (
    data          DATE,
    chuva_mm      DOUBLE,
    et0_mm        DOUBLE,
    temp_max_c    DOUBLE,
    temp_min_c    DOUBLE,
    carregado_em  TIMESTAMP
);
