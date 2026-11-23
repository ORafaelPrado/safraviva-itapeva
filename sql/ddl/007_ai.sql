-- =====================================================================
-- SafraViva — 007: registro do Agrônomo Digital
-- Cada pergunta respondida fica gravada (pergunta, resposta, ferramentas usadas,
-- tokens e tempo) para avaliar a qualidade e acompanhar o custo da API.
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS ai;
CREATE SEQUENCE IF NOT EXISTS ai.seq_conversa START 1;

CREATE TABLE IF NOT EXISTS ai.conversa (
    id               INTEGER PRIMARY KEY DEFAULT nextval('ai.seq_conversa'),
    ts               TIMESTAMP DEFAULT current_timestamp,
    propriedade_id   INTEGER,
    origem           VARCHAR,          -- chat | resumo_semanal | avaliacao
    pergunta         VARCHAR,
    resposta         VARCHAR,
    ferramentas      VARCHAR,          -- JSON [{nome, argumentos, erro}]
    modelo           VARCHAR,
    tokens_entrada   INTEGER,
    tokens_saida     INTEGER,
    segundos         DOUBLE
);
