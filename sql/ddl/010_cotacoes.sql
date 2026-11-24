-- =====================================================================
-- SafraViva — 010: cotações (CEPEA, CBOT, dólar)
-- cotacao_diaria: um valor por dia e série (histórico); valor_rs_sc normaliza tudo para R$/saca 60 kg
-- cotacao_intradia: o último pregão em 15 min (bolsa) / 5 min (dólar)
-- cotacao_ultima: o preço mais recente de cada série de bolsa, com a hora do mercado
-- =====================================================================
CREATE TABLE IF NOT EXISTS raw.cotacao_diaria (
    serie         VARCHAR,     -- cepea_soja_parana, cbot_soja, dolar, dolar_ptax...
    cultura       VARCHAR,     -- soja, milho, trigo, dolar
    nome          VARCHAR,
    data          DATE,
    valor         DOUBLE,      -- na unidade original
    unidade       VARCHAR,     -- R$/sc, R$/t, US¢/bushel, R$/US$
    valor_usd     DOUBLE,
    valor_rs_sc   DOUBLE,      -- R$ por saca de 60 kg (nulo para o dólar)
    fonte         VARCHAR,
    carregado_em  TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.cotacao_intradia (
    serie         VARCHAR,
    ts            TIMESTAMP,   -- horário de Brasília
    valor         DOUBLE,
    carregado_em  TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.cotacao_ultima (
    serie                VARCHAR,
    cultura              VARCHAR,
    nome                 VARCHAR,
    simbolo              VARCHAR,
    preco                DOUBLE,
    fechamento_anterior  DOUBLE,
    variacao_pct         DOUBLE,
    horario_mercado      TIMESTAMP,
    unidade              VARCHAR,
    preco_rs_sc          DOUBLE,
    carregado_em         TIMESTAMP
);
