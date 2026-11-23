-- =====================================================================
-- SafraViva — 004: calendário fenológico de referência para Itapeva
-- Datas típicas da região, derivadas das janelas de risco baixo do ZARC
-- (soja Grupo II, plantio de out–nov; milho verão de set–out; trigo de abr–mai)
-- e da duração de ciclo das cultivares. É uma aproximação regional, não a
-- data de uma lavoura específica: troque pelas datas reais da fazenda na Fase 4.
--
-- ano_offset é relativo ao ano da PAM (ano da colheita):
--   soja e milho verão: plantio no ano anterior (−1), colheita no ano da PAM (0);
--   trigo: tudo no ano da PAM.
-- =====================================================================
CREATE OR REPLACE TABLE analytics.dim_fase_fenologica (
    cultura          VARCHAR,
    ordem            INTEGER,
    fase             VARCHAR,
    ini_mes          INTEGER, ini_dia INTEGER, ini_offset INTEGER,
    fim_mes          INTEGER, fim_dia INTEGER, fim_offset INTEGER,
    descricao        VARCHAR,
    PRIMARY KEY (cultura, fase)
);

INSERT INTO analytics.dim_fase_fenologica VALUES
    ('soja',  1, 'semeadura',     10, 15, -1, 11, 30, -1, 'Semeadura e emergência (VE): exige solo úmido'),
    ('soja',  2, 'vegetativo',    12,  1, -1, 12, 31, -1, 'Crescimento vegetativo (V3–Vn)'),
    ('soja',  3, 'florescimento',  1,  1,  0,  1, 31,  0, 'Florescimento e formação de vagens (R1–R4): fase mais sensível à seca e ao calor'),
    ('soja',  4, 'enchimento',     2,  1,  0,  3, 10,  0, 'Enchimento de grãos (R5–R6): define peso de grão'),
    ('soja',  5, 'colheita',       3, 11,  0,  4, 30,  0, 'Maturação e colheita (R7–R8): chuva excessiva atrasa e deprecia'),
    ('milho', 1, 'semeadura',      9, 15, -1, 10, 31, -1, 'Semeadura e emergência do milho verão'),
    ('milho', 2, 'vegetativo',    11,  1, -1, 12, 15, -1, 'Crescimento vegetativo (V4–VT)'),
    ('milho', 3, 'florescimento', 12, 16, -1,  1, 20,  0, 'Pendoamento e espigamento (VT–R1): fase crítica para água'),
    ('milho', 4, 'enchimento',     1, 21,  0,  2, 28,  0, 'Enchimento de grãos (R2–R5)'),
    ('milho', 5, 'colheita',       3,  1,  0,  4, 30,  0, 'Maturação e colheita'),
    ('trigo', 1, 'semeadura',      4,  1,  0,  5, 31,  0, 'Semeadura e emergência'),
    ('trigo', 2, 'perfilhamento',  6,  1,  0,  7, 15,  0, 'Perfilhamento e alongamento'),
    ('trigo', 3, 'florescimento',  7, 16,  0,  8, 31,  0, 'Espigamento e florescimento: geada aqui esteriliza a espiga'),
    ('trigo', 4, 'enchimento',     9,  1,  0,  9, 30,  0, 'Enchimento de grãos'),
    ('trigo', 5, 'colheita',      10,  1,  0, 11, 15,  0, 'Maturação e colheita: chuva causa germinação na espiga');
