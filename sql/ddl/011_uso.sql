-- =====================================================================
-- SafraViva — 011: uso do painel (medição desde o começo)
-- Um registro por evento: página vista, versão do texto (A/B) e clique nas chamadas principais.
-- Sem dado pessoal: só a sessão (id aleatório), a página, a ação e o tipo de aparelho.
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS uso;

CREATE TABLE IF NOT EXISTS uso.evento (
    ts           TIMESTAMP NOT NULL,
    sessao       VARCHAR   NOT NULL,   -- uuid curto, gerado por sessão do navegador
    evento       VARCHAR   NOT NULL,   -- pagina_vista | ab_view | cta_click
    pagina       VARCHAR,
    detalhe      VARCHAR,              -- ex.: "agronomo|v=B"
    dispositivo  VARCHAR               -- celular | computador
);
