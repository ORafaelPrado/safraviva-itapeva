-- =====================================================================
-- SafraViva — 012: ficha da fazenda (formulário do produtor)
-- Guarda as respostas como vieram (JSON) e aponta a propriedade criada a partir delas.
-- Fica só no banco privado (MotherDuck); nunca no repositório.
-- =====================================================================
CREATE TABLE IF NOT EXISTS fazenda.ficha (
    id              INTEGER PRIMARY KEY DEFAULT nextval('fazenda.seq_id'),
    enviada_em      TIMESTAMP DEFAULT current_timestamp,
    respostas       JSON NOT NULL,
    propriedade_id  INTEGER,            -- propriedade criada (NULL se só guardada para conferência)
    situacao        VARCHAR NOT NULL    -- aplicada | guardada
);
