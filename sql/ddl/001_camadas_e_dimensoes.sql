-- =====================================================================
-- SafraViva — 001: camadas e dimensões
-- raw       → dado bruto como veio da fonte (append, com data de carga)
-- staging   → dado limpo e tipado
-- analytics → modelo estrela consumido por painéis, IA e ML
-- fazenda   → dados privados da propriedade (Fase 4)
-- Script idempotente: pode rodar quantas vezes quiser.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS fazenda;

-- ---------------------------------------------------------------------
-- Dimensões (populadas a partir de core/config.py pelo scripts/setup_db.py)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.dim_municipio (
    codigo_ibge   INTEGER PRIMARY KEY,
    nome          VARCHAR NOT NULL,
    microrregiao  VARCHAR NOT NULL,
    uf            VARCHAR NOT NULL DEFAULT 'SP',
    foco          BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS analytics.dim_cultura (
    slug          VARCHAR PRIMARY KEY,
    nome          VARCHAR NOT NULL,
    codigo_sidra  INTEGER NOT NULL UNIQUE,
    estacao       VARCHAR NOT NULL CHECK (estacao IN ('verao', 'inverno'))
);

CREATE TABLE IF NOT EXISTS analytics.dim_estacao (
    codigo                 VARCHAR PRIMARY KEY,
    nome                   VARCHAR NOT NULL,
    lat                    DOUBLE NOT NULL,
    lon                    DOUBLE NOT NULL,
    altitude_m             DOUBLE,
    distancia_itapeva_km   INTEGER
);

-- Calendário diário 1970–2035.
-- Ano-safra vai de julho a junho: 15/10/2026 pertence à safra 2026/27.
-- Decêndio 1–36 segue o padrão do ZARC (3 por mês: dias 1–10, 11–20, 21–fim).
CREATE OR REPLACE TABLE analytics.dim_tempo AS
SELECT
    d::DATE                                                       AS data,
    year(d)                                                       AS ano,
    month(d)                                                      AS mes,
    day(d)                                                        AS dia,
    dayofyear(d)                                                  AS dia_do_ano,
    CASE WHEN month(d) >= 7 THEN year(d) ELSE year(d) - 1 END     AS ano_safra_inicio,
    CASE WHEN month(d) >= 7
         THEN year(d)::VARCHAR || '/' || right((year(d) + 1)::VARCHAR, 2)
         ELSE (year(d) - 1)::VARCHAR || '/' || right(year(d)::VARCHAR, 2)
    END                                                           AS ano_safra,
    (month(d) - 1) * 3 + CASE WHEN day(d) <= 10 THEN 1
                              WHEN day(d) <= 20 THEN 2
                              ELSE 3 END                          AS decendio,
    CASE WHEN month(d) IN (12, 1, 2) THEN 'verao'
         WHEN month(d) IN (3, 4, 5)  THEN 'outono'
         WHEN month(d) IN (6, 7, 8)  THEN 'inverno'
         ELSE 'primavera' END                                     AS estacao_ano
FROM range(DATE '1970-01-01', DATE '2036-01-01', INTERVAL 1 DAY) AS t(d);
