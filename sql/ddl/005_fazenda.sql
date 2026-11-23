-- =====================================================================
-- SafraViva — 005: gestão da propriedade (schema fazenda) + custos CONAB (raw)
--
-- propriedade ─┬─ talhao ─── plantio ─┬─ operacao (caderno de campo, com custo opcional)
--              │                      ├─ colheita
--              │                      └─ ocorrencia
--              ├─ custo (despesas fora das operações: arrendamento, seguro, assistência...)
--              └─ venda
-- preco_referencia: preço da saca para estimar receita enquanto não há venda.
-- Toda linha de demonstração pertence a uma propriedade com demo = TRUE.
-- =====================================================================

CREATE TABLE IF NOT EXISTS raw.conab_custo (
    cultura              VARCHAR,
    aba                  VARCHAR,
    local                VARCHAR,
    tecnologia           VARCHAR,
    safra_texto          VARCHAR,
    mes_referencia       DATE,
    produtividade_kg_ha  DOUBLE,
    item                 VARCHAR,
    descricao            VARCHAR,
    categoria            VARCHAR,
    valor_ha             DOUBLE,
    valor_sc             DOUBLE,
    carregado_em         TIMESTAMP
);

-- Criada vazia aqui para as views de gestão poderem referenciá-la; preenchida por sql/transform/060.
CREATE TABLE IF NOT EXISTS analytics.custo_referencia (
    cultura VARCHAR, local VARCHAR, aba VARCHAR, mes_referencia DATE,
    produtividade_sc_ha DOUBLE, categoria VARCHAR, valor_ha DOUBLE
);

CREATE SEQUENCE IF NOT EXISTS fazenda.seq_id START 1;

CREATE TABLE IF NOT EXISTS fazenda.propriedade (
    id               INTEGER PRIMARY KEY DEFAULT nextval('fazenda.seq_id'),
    nome             VARCHAR NOT NULL,
    municipio_ibge   INTEGER NOT NULL DEFAULT 3522406,
    lat              DOUBLE,
    lon              DOUBLE,
    demo             BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em        TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS fazenda.talhao (
    id               INTEGER PRIMARY KEY DEFAULT nextval('fazenda.seq_id'),
    propriedade_id   INTEGER NOT NULL REFERENCES fazenda.propriedade (id),
    nome             VARCHAR NOT NULL,
    area_ha          DOUBLE NOT NULL CHECK (area_ha > 0),
    solo_ad          VARCHAR CHECK (solo_ad IN ('AD1', 'AD2', 'AD3', 'AD4', 'AD5', 'AD6')),
    observacao       VARCHAR,
    ativo            BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS fazenda.plantio (
    id                       INTEGER PRIMARY KEY DEFAULT nextval('fazenda.seq_id'),
    talhao_id                INTEGER NOT NULL REFERENCES fazenda.talhao (id),
    safra                    VARCHAR NOT NULL,           -- ex.: 2026/27 (ano-safra jul→jun)
    temporada                VARCHAR NOT NULL CHECK (temporada IN ('verao', 'safrinha', 'inverno')),
    cultura                  VARCHAR NOT NULL,           -- slug de analytics.dim_cultura
    cultivar                 VARCHAR,
    grupo_ciclo              VARCHAR,                    -- Grupo I / II / III (ZARC)
    data_plantio             DATE,
    area_ha                  DOUBLE CHECK (area_ha > 0), -- se nulo, usa a área do talhão
    populacao_plantas_ha     DOUBLE,
    espacamento_cm           DOUBLE,
    produtividade_meta_sc_ha DOUBLE,
    status                   VARCHAR NOT NULL DEFAULT 'planejado'
                             CHECK (status IN ('planejado', 'plantado', 'colhido', 'perdido')),
    observacao               VARCHAR
);

-- Caderno de campo: toda operação feita na lavoura. O custo é opcional (ex.: aplicação com produto já pago).
CREATE TABLE IF NOT EXISTS fazenda.operacao (
    id               INTEGER PRIMARY KEY DEFAULT nextval('fazenda.seq_id'),
    plantio_id       INTEGER NOT NULL REFERENCES fazenda.plantio (id),
    data             DATE NOT NULL,
    tipo             VARCHAR NOT NULL CHECK (tipo IN ('preparo', 'plantio', 'adubacao', 'pulverizacao',
                                                     'colheita', 'transporte', 'outro')),
    produto          VARCHAR,
    dose             DOUBLE,
    unidade          VARCHAR,                            -- L/ha, kg/ha, sc/ha...
    area_ha          DOUBLE,
    custo_total      DOUBLE CHECK (custo_total >= 0),
    categoria_custo  VARCHAR,
    observacao       VARCHAR
);

-- Despesas fora do caderno de campo. Com plantio_id: custo direto do plantio.
-- Sem plantio_id: custo da propriedade na safra, rateado por área entre os plantios da safra.
CREATE TABLE IF NOT EXISTS fazenda.custo (
    id               INTEGER PRIMARY KEY DEFAULT nextval('fazenda.seq_id'),
    propriedade_id   INTEGER NOT NULL REFERENCES fazenda.propriedade (id),
    plantio_id       INTEGER REFERENCES fazenda.plantio (id),
    safra            VARCHAR NOT NULL,
    data             DATE NOT NULL,
    categoria        VARCHAR NOT NULL,
    descricao        VARCHAR,
    valor            DOUBLE NOT NULL CHECK (valor >= 0)
);

CREATE TABLE IF NOT EXISTS fazenda.colheita (
    id               INTEGER PRIMARY KEY DEFAULT nextval('fazenda.seq_id'),
    plantio_id       INTEGER NOT NULL REFERENCES fazenda.plantio (id),
    data             DATE NOT NULL,
    area_colhida_ha  DOUBLE,
    sacas            DOUBLE NOT NULL CHECK (sacas >= 0),  -- sacas de 60 kg, já descontadas umidade e impureza
    umidade_pct      DOUBLE,
    impureza_pct     DOUBLE,
    observacao       VARCHAR
);

CREATE TABLE IF NOT EXISTS fazenda.venda (
    id               INTEGER PRIMARY KEY DEFAULT nextval('fazenda.seq_id'),
    propriedade_id   INTEGER NOT NULL REFERENCES fazenda.propriedade (id),
    cultura          VARCHAR NOT NULL,
    safra            VARCHAR NOT NULL,
    data             DATE NOT NULL,
    sacas            DOUBLE NOT NULL CHECK (sacas > 0),
    preco_sc         DOUBLE NOT NULL CHECK (preco_sc > 0),
    comprador        VARCHAR,
    observacao       VARCHAR
);

CREATE TABLE IF NOT EXISTS fazenda.ocorrencia (
    id               INTEGER PRIMARY KEY DEFAULT nextval('fazenda.seq_id'),
    plantio_id       INTEGER NOT NULL REFERENCES fazenda.plantio (id),
    data             DATE NOT NULL,
    tipo             VARCHAR NOT NULL CHECK (tipo IN ('praga', 'doenca', 'daninha', 'geada', 'granizo',
                                                     'seca', 'excesso_chuva', 'outro')),
    severidade       INTEGER CHECK (severidade BETWEEN 1 AND 3),  -- 1 leve, 2 moderada, 3 severa
    descricao        VARCHAR
);

CREATE TABLE IF NOT EXISTS fazenda.preco_referencia (
    cultura          VARCHAR PRIMARY KEY,
    preco_sc         DOUBLE NOT NULL,
    data             DATE NOT NULL,
    fonte            VARCHAR NOT NULL
);

-- Preços de partida (pesquisados em 03/11/2026). Editáveis no painel; não sobrescreve o que o usuário mudou.
INSERT OR IGNORE INTO fazenda.preco_referencia VALUES
    ('soja',  152.22, DATE '2026-10-30', 'Cepea/Esalq, indicador Paraná'),
    ('milho',  54.00, DATE '2026-10-21', 'Média de cooperativas/CONAB ao produtor no PR (R$ 52–55,50)'),
    ('trigo',  80.00, DATE '2026-10-26', 'Deral/SEAB atacado PR (R$ 79,31) e Copagril balcão (R$ 80,00)');

-- Duração aproximada das fases por cultura, em dias após o plantio (ciclo médio, Grupo II).
-- Usada para estimar a fase atual de cada lavoura e cruzar com os alertas do tempo.
CREATE OR REPLACE TABLE analytics.dim_fase_duracao (
    cultura      VARCHAR,
    temporada    VARCHAR,
    ordem        INTEGER,
    fase         VARCHAR,
    dia_inicio   INTEGER,
    dia_fim      INTEGER,
    sensivel_a   VARCHAR     -- o que mais prejudica nessa fase
);
INSERT INTO analytics.dim_fase_duracao VALUES
    ('soja',  'verao',    1, 'emergência',     0,  15, 'falta de chuva (falha de estande)'),
    ('soja',  'verao',    2, 'vegetativo',    16,  50, 'veranico prolongado'),
    ('soja',  'verao',    3, 'florescimento', 51,  80, 'veranico e calor ≥ 32 °C'),
    ('soja',  'verao',    4, 'enchimento',    81, 110, 'veranico'),
    ('soja',  'verao',    5, 'maturação',    111, 125, 'chuva na colheita'),
    ('milho', 'verao',    1, 'emergência',     0,  15, 'falta de chuva'),
    ('milho', 'verao',    2, 'vegetativo',    16,  65, 'veranico prolongado'),
    ('milho', 'verao',    3, 'florescimento', 66,  90, 'veranico e calor'),
    ('milho', 'verao',    4, 'enchimento',    91, 125, 'veranico'),
    ('milho', 'verao',    5, 'maturação',    126, 150, 'chuva na colheita'),
    ('milho', 'safrinha', 1, 'emergência',     0,  15, 'falta de chuva'),
    ('milho', 'safrinha', 2, 'vegetativo',    16,  60, 'veranico'),
    ('milho', 'safrinha', 3, 'florescimento', 61,  85, 'veranico e geada'),
    ('milho', 'safrinha', 4, 'enchimento',    86, 120, 'geada'),
    ('milho', 'safrinha', 5, 'maturação',    121, 140, 'chuva na colheita'),
    ('trigo', 'inverno',  1, 'emergência',     0,  15, 'falta de chuva'),
    ('trigo', 'inverno',  2, 'perfilhamento', 16,  55, 'geada forte'),
    ('trigo', 'inverno',  3, 'florescimento', 56,  85, 'geada e chuva (doenças)'),
    ('trigo', 'inverno',  4, 'enchimento',    86, 110, 'geada'),
    ('trigo', 'inverno',  5, 'maturação',    111, 125, 'chuva na colheita (germinação na espiga)'),
    ('feijao','verao',    1, 'emergência',     0,  12, 'falta de chuva'),
    ('feijao','verao',    2, 'vegetativo',    13,  35, 'veranico'),
    ('feijao','verao',    3, 'florescimento', 36,  55, 'veranico e calor'),
    ('feijao','verao',    4, 'enchimento',    56,  75, 'veranico'),
    ('feijao','verao',    5, 'maturação',     76,  90, 'chuva na colheita');
