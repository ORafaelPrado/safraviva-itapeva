"""Testes da gestão da propriedade: gravação, rateio de custos, resultado e fase da lavoura."""

from datetime import date, timedelta

import duckdb
import pytest

from app import gestao
from core import config


@pytest.fixture()
def con():
    conexao = duckdb.connect()
    for arquivo in sorted((config.DIR_SQL / "ddl").glob("*.sql")):
        conexao.execute(arquivo.read_text(encoding="utf-8"))
    yield conexao
    conexao.close()


@pytest.fixture()
def fazenda(con):
    pid = gestao.criar_propriedade(con, "Teste", demo=True)
    t1 = gestao.criar_talhao(con, pid, "T1", 100, "AD4")
    t2 = gestao.criar_talhao(con, pid, "T2", 50, "AD2")
    return pid, t1, t2


@pytest.mark.parametrize(("d", "esperado"), [(date(2026, 10, 15), "2026/27"), (date(2026, 4, 20), "2025/26"),
                                             (date(2026, 7, 1), "2026/27"), (date(2027, 6, 30), "2026/27")])
def test_safra_de(d, esperado):
    assert gestao.safra_de(d) == esperado


def test_validacoes(con, fazenda):
    pid, t1, _ = fazenda
    with pytest.raises(ValueError):
        gestao.criar_talhao(con, pid, "X", 10, "AD9")
    with pytest.raises(ValueError):
        gestao.criar_plantio(con, t1, "cafe", "verao", date(2026, 10, 1))
    plantio = gestao.criar_plantio(con, t1, "soja", "verao", date(2026, 10, 1))
    with pytest.raises(ValueError):
        gestao.registrar_operacao(con, plantio, date(2026, 10, 1), "pulverizacao", custo_total=100)  # sem categoria


def test_status_muda_com_plantio_e_colheita(con, fazenda):
    _, t1, _ = fazenda
    futuro = date.today() + timedelta(days=20)
    plantio = gestao.criar_plantio(con, t1, "soja", "verao", futuro)
    assert con.execute("SELECT status FROM fazenda.plantio WHERE id = ?", [plantio]).fetchone()[0] == "planejado"
    gestao.registrar_operacao(con, plantio, date.today(), "plantio")
    assert con.execute("SELECT status FROM fazenda.plantio WHERE id = ?", [plantio]).fetchone()[0] == "plantado"
    gestao.registrar_colheita(con, plantio, date.today(), sacas=6000)
    assert con.execute("SELECT status FROM fazenda.plantio WHERE id = ?", [plantio]).fetchone()[0] == "colhido"


def test_resultado_com_rateio_venda_e_ponto_de_equilibrio(con, fazenda):
    pid, t1, t2 = fazenda
    p1 = gestao.criar_plantio(con, t1, "soja", "verao", date(2025, 10, 15), produtividade_meta_sc_ha=60)
    p2 = gestao.criar_plantio(con, t2, "soja", "verao", date(2025, 10, 20), produtividade_meta_sc_ha=60)
    gestao.registrar_operacao(con, p1, date(2025, 10, 15), "plantio", custo_total=300_000, categoria_custo="semente")
    gestao.registrar_custo(con, pid, date(2025, 12, 1), "assistencia_tecnica", 15_000, safra="2025/26")  # rateado 100:50
    gestao.registrar_colheita(con, p1, date(2026, 3, 1), sacas=6000)
    gestao.registrar_venda(con, pid, "soja", "2025/26", date(2026, 3, 10), 3000, 120)
    gestao.registrar_venda(con, pid, "soja", "2025/26", date(2026, 5, 10), 3000, 140)

    r = con.execute("SELECT * FROM fazenda.vw_resultado_plantio ORDER BY talhao").df().set_index("talhao")
    assert r.loc["T1", "custo_total"] == pytest.approx(310_000)          # 300 mil + 2/3 de 15 mil
    assert r.loc["T2", "custo_total"] == pytest.approx(5_000)            # 1/3 do rateio
    assert r.loc["T1", "produtividade_sc_ha"] == pytest.approx(60)
    assert r.loc["T1", "preco_sc"] == pytest.approx(130)                 # média ponderada das vendas
    assert r.loc["T1", "receita"] == pytest.approx(6000 * 130)
    assert r.loc["T1", "custo_por_saca"] == pytest.approx(310_000 / 6000)
    assert r.loc["T1", "ponto_equilibrio_sc_ha"] == pytest.approx(3100 / 130)
    assert bool(r.loc["T2", "receita_estimada"])                         # ainda não colhido: usa a meta


def test_preco_de_referencia_quando_nao_ha_venda(con, fazenda):
    _, t1, _ = fazenda
    gestao.criar_plantio(con, t1, "trigo", "inverno", date(2026, 4, 20), produtividade_meta_sc_ha=55)
    r = con.execute("SELECT preco_sc, origem_preco FROM fazenda.vw_resultado_plantio").fetchone()
    assert r[0] == pytest.approx(80.0) and r[1].startswith("referência")


def test_fase_atual_da_lavoura(con, fazenda):
    _, t1, _ = fazenda
    gestao.criar_plantio(con, t1, "soja", "verao", date.today() - timedelta(days=60))
    fase, dias = con.execute("SELECT fase, dias_apos_plantio FROM fazenda.vw_estadio_atual").fetchone()
    assert (fase, dias) == ("florescimento", 60)


def test_remover_demonstracao_apaga_tudo(con, fazenda):
    pid, t1, _ = fazenda
    p = gestao.criar_plantio(con, t1, "soja", "verao", date(2025, 10, 15))
    gestao.registrar_operacao(con, p, date(2025, 10, 15), "plantio", custo_total=10, categoria_custo="semente")
    gestao.registrar_custo(con, pid, date(2025, 11, 1), "seguro", 5)
    gestao.registrar_colheita(con, p, date(2026, 3, 1), 100)
    gestao.registrar_ocorrencia(con, p, date(2026, 1, 10), "seca", 2)
    gestao.registrar_venda(con, pid, "soja", "2025/26", date(2026, 3, 5), 100, 120)
    assert gestao.remover_demonstracao(con) == 1
    for tabela in ("propriedade", "talhao", "plantio", "operacao", "custo", "colheita", "venda", "ocorrencia"):
        assert con.execute(f"SELECT count(*) FROM fazenda.{tabela}").fetchone()[0] == 0
