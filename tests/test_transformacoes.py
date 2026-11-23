"""Testes das transformações SQL da camada analytics (banco em memória)."""

from datetime import date

import duckdb
import pytest

from core import config


def _executar(con, pasta: str, nomes: list[str] | None = None) -> None:
    for arquivo in sorted((config.DIR_SQL / pasta).glob("*.sql")):
        if nomes is None or arquivo.name in nomes:
            con.execute(arquivo.read_text(encoding="utf-8"))


@pytest.fixture()
def con():
    conexao = duckdb.connect()
    _executar(conexao, "ddl")
    yield conexao
    conexao.close()


def test_janela_plantio_atravessa_virada_do_ano(con):
    # Milho 2ª safra: 21/dez e 1/jan com risco 20%, 11/jan com 30%, resto não indicado.
    decs = {f"dec{i}": 0 for i in range(1, 37)}
    decs.update(dec36=20, dec1=20, dec2=30)
    colunas = ", ".join(decs)
    valores = ", ".join(str(v) for v in decs.values())
    con.execute(
        f"""INSERT INTO raw.zarc_tabua (safra, nome_cultura, safraini, safrafin, cod_ciclo, cod_solo,
                geocodigo, municipio, nome_outros_manejos, {colunas})
            VALUES ('2026-2027', 'Milho 2ª Safra', 2026, 2027, 21, 14, 3522406, 'Itapeva', 'Sequeiro', {valores})"""
    )
    _executar(con, "transform", ["030_fato_zarc.sql", "031_janelas_plantio.sql"])
    janelas = con.execute(
        "SELECT nivel_risco, data_inicio, data_fim, solo, ciclo FROM analytics.janela_plantio ORDER BY data_inicio"
    ).fetchall()
    assert janelas == [
        ("baixo", date(2026, 12, 21), date(2027, 1, 10), "AD4", "Grupo II"),
        ("médio", date(2027, 1, 11), date(2027, 1, 20), "AD4", "Grupo II"),
    ]


def test_fato_producao_derivadas(con):
    _executar(con, "ddl")
    con.execute(
        """INSERT INTO analytics.dim_cultura VALUES ('soja', 'Soja', 2713, 'verao');
           INSERT INTO raw.sidra_pam (nivel, codigo_local, nome_local, variavel_codigo, ano, cultura_codigo, valor)
           VALUES ('municipio', 3522406, 'Itapeva', 112, 2024, 2713, 3000),
                  ('municipio', 3522406, 'Itapeva', 112, 2025, 2713, 2400),
                  ('municipio', 3522406, 'Itapeva', 109, 2025, 2713, 100),
                  ('municipio', 3522406, 'Itapeva', 216, 2025, 2713, 90);"""
    )
    _executar(con, "transform", ["010_fato_producao.sql"])
    linha = con.execute(
        "SELECT rendimento_sc_ha, var_rendimento_aa, perda_area_pct, desvio_vs_media_5a "
        "FROM analytics.fato_producao WHERE ano = 2025"
    ).fetchone()
    assert linha == pytest.approx((40.0, -0.2, 0.1, -0.2))


def test_flag_repeticao_pam(con):
    con.execute(
        """INSERT INTO analytics.dim_cultura VALUES ('soja', 'Soja', 2713, 'verao');
           INSERT INTO raw.sidra_pam (nivel, codigo_local, nome_local, variavel_codigo, ano, cultura_codigo, valor) VALUES
             ('municipio', 1, 'A', 112, 2024, 2713, 2949), ('municipio', 1, 'A', 214, 2024, 2713, 241819),
             ('municipio', 1, 'A', 112, 2025, 2713, 2949), ('municipio', 1, 'A', 214, 2025, 2713, 241814),
             ('municipio', 2, 'B', 112, 2024, 2713, 2949), ('municipio', 2, 'B', 214, 2024, 2713, 200000),
             ('municipio', 2, 'B', 112, 2025, 2713, 2949), ('municipio', 2, 'B', 214, 2025, 2713, 230000);"""
    )
    _executar(con, "transform", ["010_fato_producao.sql"])
    flags = con.execute(
        "SELECT nome_local, suspeito_repeticao FROM analytics.fato_producao WHERE ano = 2025 ORDER BY 1"
    ).fetchall()
    # A repete rendimento e produção (suspeito); B repete o rendimento, mas a produção mudou 15% (área mudou).
    assert flags == [("A", True), ("B", False)]


def test_indices_fase_veranico_e_balanco(con):
    # Florescimento da soja 2025 = 1 a 31/jan/2025. Chuva só nos dias 1, 2 e 20 → maior veranico = 17 dias (3 a 19).
    con.execute(
        """CREATE TABLE analytics.clima_diario AS
           SELECT 'itapeva' AS serie, 3522406 AS codigo_ibge, d::DATE AS data,
                  CASE WHEN day(d) IN (1, 2, 20) THEN 30.0 ELSE 0.0 END AS chuva_mm,
                  33.0 AS temp_max_c, 18.0 AS temp_min_c, 25.0 AS temp_c, 20.0 AS radiacao_mj_m2
           FROM range(DATE '2025-01-01', DATE '2025-02-01', INTERVAL 1 DAY) t(d)"""
    )
    _executar(con, "transform", ["024_indices_fase.sql"])
    linha = con.execute(
        """SELECT cobertura, chuva_mm, dias_chuva, max_veranico_dias, dias_tmax_ge32, gdd, eto_mm, balanco_mm
           FROM analytics.indices_fase WHERE cultura = 'soja' AND ano_pam = 2025 AND fase = 'florescimento'"""
    ).fetchone()
    eto_dia = 0.0135 * (25 + 17.8) * 20 / 2.45
    assert linha == pytest.approx((1.0, 90.0, 3, 17, 31, 31 * 15.0, 31 * eto_dia, 90 - 31 * eto_dia))


def test_delta_t_faixa_plausivel(con):
    con.execute(
        """INSERT INTO raw.previsao_horaria (emitida_em, ts_local, temp_c, umid_pct)
           VALUES (TIMESTAMP '2026-10-15 06:00', TIMESTAMP '2026-10-16 09:00', 25, 60)"""
    )
    _executar(con, "transform", ["040_previsao.sql"])
    delta_t = con.execute("SELECT delta_t_c FROM analytics.vw_previsao_horaria_atual").fetchone()[0]
    # Bulbo úmido a 25 °C e 60% UR ≈ 19,5 °C → Delta T ≈ 5,5 °C (dentro da faixa boa para pulverizar)
    assert delta_t == pytest.approx(5.5, abs=0.3)
