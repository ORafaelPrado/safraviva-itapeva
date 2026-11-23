-- =====================================================================
-- SafraViva — 008: central de alertas (notificações)
-- Um alerta por chave (tema + alvo). Enquanto a situação continua, a mesma linha
-- é atualizada; se piora, volta a "não lido"; quando passa, é marcada como resolvida.
-- As colunas enviado_* são para os canais externos (WhatsApp, numa fase futura).
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS notif;
CREATE SEQUENCE IF NOT EXISTS notif.seq_alerta START 1;

CREATE TABLE IF NOT EXISTS notif.alerta (
    id               INTEGER PRIMARY KEY DEFAULT nextval('notif.seq_alerta'),
    chave            VARCHAR NOT NULL,          -- ex.: geada|regiao ; lavoura|plantio:42 ; estimativa|plantio:42
    propriedade_id   INTEGER,
    plantio_id       INTEGER,
    tema             VARCHAR NOT NULL,          -- geada, veranico, calor, chuva, lavoura, plantio, estimativa
    nivel            VARCHAR NOT NULL CHECK (nivel IN ('critico', 'atencao', 'info')),
    titulo           VARCHAR NOT NULL,
    detalhe          VARCHAR,
    criado_em        TIMESTAMP NOT NULL DEFAULT current_timestamp,
    atualizado_em    TIMESTAMP NOT NULL DEFAULT current_timestamp,
    resolvido_em     TIMESTAMP,                 -- preenchido quando a situação deixa de existir
    lido_em          TIMESTAMP,
    enviado_whatsapp_em TIMESTAMP
);

CREATE OR REPLACE VIEW notif.vw_alertas_ativos AS
SELECT *,
       lido_em IS NULL                                            AS novo,
       CASE nivel WHEN 'critico' THEN 1 WHEN 'atencao' THEN 2 ELSE 3 END AS prioridade
FROM notif.alerta
WHERE resolvido_em IS NULL;
