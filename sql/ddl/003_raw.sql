-- =====================================================================
-- SafraViva — 003: tabelas da camada raw (como chegam das fontes)
-- Os extratores em etl/ inserem por nome de coluna (INSERT ... BY NAME).
-- =====================================================================

-- IBGE SIDRA 1612 — formato longo, uma linha por local × variável × ano × cultura
CREATE TABLE IF NOT EXISTS raw.sidra_pam (
    nivel            VARCHAR,   -- municipio | uf | brasil
    codigo_local     BIGINT,
    nome_local       VARCHAR,
    variavel_codigo  INTEGER,   -- 109, 216, 214, 112, 215 (ver core/config.py)
    ano              INTEGER,
    cultura_codigo   INTEGER,   -- classificação 81
    valor_bruto      VARCHAR,   -- texto original ("-", "..", "X" ...)
    valor            DOUBLE,
    carregado_em     TIMESTAMP
);

-- INMET BDMEP — horário, em UTC
CREATE TABLE IF NOT EXISTS raw.inmet_horario (
    estacao          VARCHAR,
    ts_utc           TIMESTAMP,
    chuva_mm         DOUBLE,
    pressao_mb       DOUBLE,
    pressao_max_mb   DOUBLE,
    pressao_min_mb   DOUBLE,
    radiacao_kj_m2   DOUBLE,
    temp_c           DOUBLE,
    orvalho_c        DOUBLE,
    temp_max_c       DOUBLE,
    temp_min_c       DOUBLE,
    orvalho_max_c    DOUBLE,
    orvalho_min_c    DOUBLE,
    umid_max_pct     DOUBLE,
    umid_min_pct     DOUBLE,
    umid_pct         DOUBLE,
    vento_dir_graus  DOUBLE,
    rajada_ms        DOUBLE,
    vento_ms         DOUBLE,
    carregado_em     TIMESTAMP
);

-- NASA POWER — diário no centroide de cada município
CREATE TABLE IF NOT EXISTS raw.nasa_power_diario (
    codigo_ibge      INTEGER,
    data             DATE,
    chuva_mm         DOUBLE,
    temp_c           DOUBLE,
    temp_max_c       DOUBLE,
    temp_min_c       DOUBLE,
    umid_pct         DOUBLE,
    vento_2m_ms      DOUBLE,
    radiacao_mj_m2   DOUBLE,
    carregado_em     TIMESTAMP
);

-- Open-Meteo — um retrato da previsão por dia de emissão
CREATE TABLE IF NOT EXISTS raw.previsao_diaria (
    emitida_em       TIMESTAMP,
    lat              DOUBLE,
    lon              DOUBLE,
    data             DATE,
    chuva_mm         DOUBLE,
    prob_chuva_pct   DOUBLE,
    temp_max_c       DOUBLE,
    temp_min_c       DOUBLE,
    umid_pct         DOUBLE,
    vento_max_kmh    DOUBLE,
    rajada_max_kmh   DOUBLE,
    et0_mm           DOUBLE,
    radiacao_mj_m2   DOUBLE
);

CREATE TABLE IF NOT EXISTS raw.previsao_horaria (
    emitida_em       TIMESTAMP,
    lat              DOUBLE,
    lon              DOUBLE,
    ts_local         TIMESTAMP,
    temp_c           DOUBLE,
    umid_pct         DOUBLE,
    orvalho_c        DOUBLE,
    chuva_mm         DOUBLE,
    prob_chuva_pct   DOUBLE,
    vento_kmh        DOUBLE,
    rajada_kmh       DOUBLE,
    temp_solo_c      DOUBLE
);

-- MAPA ZARC — tábua de risco (recorte da região); decN = risco % no decêndio N, 0 = não indicado
CREATE TABLE IF NOT EXISTS raw.zarc_tabua (
    safra                VARCHAR,   -- ex.: 2026-2027
    nome_cultura         VARCHAR,
    safraini             INTEGER,
    safrafin             INTEGER,
    cod_cultura          VARCHAR,
    cod_ciclo            INTEGER,
    cod_solo             INTEGER,
    geocodigo            INTEGER,
    uf                   VARCHAR,
    municipio            VARCHAR,
    cod_clima            INTEGER,
    nome_clima           VARCHAR,
    cod_outros_manejos   INTEGER,
    nome_outros_manejos  VARCHAR,
    produtividade        VARCHAR,
    cod_nm               VARCHAR,
    cod_munic            VARCHAR,
    cod_meso             VARCHAR,
    cod_micro            VARCHAR,
    portaria             VARCHAR,
    dec1  INTEGER,
    dec2  INTEGER,
    dec3  INTEGER,
    dec4  INTEGER,
    dec5  INTEGER,
    dec6  INTEGER,
    dec7  INTEGER,
    dec8  INTEGER,
    dec9  INTEGER,
    dec10 INTEGER,
    dec11 INTEGER,
    dec12 INTEGER,
    dec13 INTEGER,
    dec14 INTEGER,
    dec15 INTEGER,
    dec16 INTEGER,
    dec17 INTEGER,
    dec18 INTEGER,
    dec19 INTEGER,
    dec20 INTEGER,
    dec21 INTEGER,
    dec22 INTEGER,
    dec23 INTEGER,
    dec24 INTEGER,
    dec25 INTEGER,
    dec26 INTEGER,
    dec27 INTEGER,
    dec28 INTEGER,
    dec29 INTEGER,
    dec30 INTEGER,
    dec31 INTEGER,
    dec32 INTEGER,
    dec33 INTEGER,
    dec34 INTEGER,
    dec35 INTEGER,
    dec36 INTEGER,
    carregado_em         TIMESTAMP
);
