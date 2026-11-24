"""Testes das cotações: conversão de Chicago para R$/saca, preço de referência e ferramenta da IA."""

from datetime import date, datetime, timedelta

import duckdb
import pandas as pd
import pytest

from ai import ferramentas
from ai.ferramentas import Contexto
from core import config
from etl import cotacoes


@pytest.mark.parametrize(("cultura", "centavos", "dolar", "esperado"), [
    ("soja", 1238.25, 5.90, 12.3825 * 60 / 27.2155 * 5.90),   # ≈ R$ 161/sc
    ("milho", 450.75, 5.90, 4.5075 * 60 / 25.4012 * 5.90),    # bushel de milho é mais leve (25,4 kg)
])
def test_conversao_chicago_para_reais_por_saca(cultura, centavos, dolar, esperado):
    assert cotacoes.rs_por_saca_cbot(centavos, cultura, dolar) == pytest.approx(esperado)
    assert cotacoes.rs_por_saca_cbot(1238.25, "soja", 5.90) == pytest.approx(161.06, abs=0.05)


def test_converter_cbot_usa_o_dolar_do_dia_ou_anterior():
    diario = pd.DataFrame({
        "serie": ["dolar", "dolar", "cbot_soja", "cbot_soja"], "cultura": ["dolar", "dolar", "soja", "soja"],
        "nome": ["d", "d", "s", "s"], "data": [date(2026, 11, 20), date(2026, 11, 23), date(2026, 11, 22), date(2026, 11, 23)],
        "valor": [5.0, 6.0, 1000.0, 1000.0]})
    ultimos = pd.DataFrame({"serie": ["dolar", "cbot_soja"], "cultura": ["dolar", "soja"], "preco": [6.0, 1000.0]})
    saida, ult = cotacoes.converter_cbot(diario, ultimos)
    soja = saida[saida["serie"] == "cbot_soja"].set_index("data")["valor_rs_sc"]
    assert soja[date(2026, 11, 22)] == pytest.approx(cotacoes.rs_por_saca_cbot(1000, "soja", 5.0))  # sábado → dólar de sexta
    assert soja[date(2026, 11, 23)] == pytest.approx(cotacoes.rs_por_saca_cbot(1000, "soja", 6.0))
    assert ult.set_index("serie").loc["cbot_soja", "preco_rs_sc"] == pytest.approx(cotacoes.rs_por_saca_cbot(1000, "soja", 6.0))


@pytest.fixture()
def banco(tmp_path, monkeypatch):
    caminho = tmp_path / "cot.duckdb"
    monkeypatch.setattr(config, "CAMINHO_DB", caminho)
    with duckdb.connect(str(caminho)) as con:
        for arquivo in sorted((config.DIR_SQL / "ddl").glob("*.sql")):
            con.execute(arquivo.read_text(encoding="utf-8"))
        hoje = date.today()
        for i in range(400):
            d = hoje - timedelta(days=i)
            con.execute("INSERT INTO raw.cotacao_diaria (serie, cultura, nome, data, valor, unidade, valor_rs_sc, fonte) "
                        "VALUES ('cepea_soja_parana', 'soja', 'Soja CEPEA PR', ?, ?, 'R$/sc', ?, 'CEPEA')",
                        [d, 150 - i * 0.01, 150 - i * 0.01])
        con.execute("INSERT INTO raw.cotacao_ultima (serie, cultura, nome, preco, variacao_pct, horario_mercado, preco_rs_sc) "
                    "VALUES ('cbot_soja', 'soja', 'Soja CBOT', 1200, 0.5, ?, 158.0)", [datetime.now()])
    return caminho


def test_preco_de_referencia_automatico_respeita_o_digitado(banco):
    banco = duckdb.connect(str(banco))
    assert cotacoes.atualizar_preco_referencia(banco) == 1   # soja: fonte de partida → vira CEPEA
    assert banco.execute("SELECT preco_sc FROM fazenda.preco_referencia WHERE cultura = 'soja'").fetchone()[0] == 150
    banco.execute("UPDATE fazenda.preco_referencia SET preco_sc = 140, fonte = 'Cotação local' WHERE cultura = 'soja'")
    cotacoes.atualizar_preco_referencia(banco)
    assert banco.execute("SELECT preco_sc FROM fazenda.preco_referencia WHERE cultura = 'soja'").fetchone()[0] == 140


def test_ferramenta_de_cotacoes_para_a_ia(banco):
    r = ferramentas.executar("cotacoes", {"cultura": "soja", "dias": 30}, Contexto())
    cepea = next(x for x in r["ultimos_e_periodo"] if x["serie"] == "cepea_soja_parana")
    assert cepea["valor"] == pytest.approx(150.0) and cepea["unidade"] == "R$/sc 60 kg"
    assert cepea["variacao_periodo_pct"] == pytest.approx(100 * (150 / 149.7 - 1), abs=0.01)
    assert r["bolsa_agora"][0]["preco_rs_sc"] == pytest.approx(158.0)
    assert "não previsão" in r["nota_sazonalidade"]
    assert "erro" in ferramentas.executar("cotacoes", {"cultura": "cafe"}, Contexto())


def test_decomposicao_separa_chicago_do_dolar(tmp_path, monkeypatch):
    caminho = tmp_path / "dec.duckdb"
    monkeypatch.setattr(config, "CAMINHO_DB", caminho)
    with duckdb.connect(str(caminho)) as con:
        for arquivo in sorted((config.DIR_SQL / "ddl").glob("*.sql")):
            con.execute(arquivo.read_text(encoding="utf-8"))
        hoje = date.today()
        # Chicago parado em 1.000 ¢/bu; dólar de 5,00 para 5,50 (+10%) → em reais, +10%, culpa do dólar
        for d, dolar in [(hoje - timedelta(days=20), 5.0), (hoje, 5.5)]:
            con.execute("INSERT INTO raw.cotacao_diaria (serie, cultura, data, valor, valor_rs_sc) VALUES "
                        "('cbot_soja', 'soja', ?, 1000, ?)", [d, cotacoes.rs_por_saca_cbot(1000, "soja", dolar)])
    r = ferramentas.executar("cotacoes", {"cultura": "soja", "dias": 30}, Contexto())["decomposicao_chicago_x_dolar"]
    assert r["chicago_em_dolar_pct"] == pytest.approx(0.0) and r["dolar_pct"] == pytest.approx(10.0)
    assert "Quem mais pesou foi o dólar" in r["leitura"] and "+10,0%" in r["leitura"]
