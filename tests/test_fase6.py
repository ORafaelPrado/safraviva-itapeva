"""Testes da Fase 6: balanço hídrico, central de alertas (deduplicação) e regras de confiabilidade."""

from datetime import date

import duckdb
import numpy as np
import pandas as pd
import pytest

from analytics import balanco_hidrico as bh
from app import notificacoes
from app.notificacoes import AlertaNovo, CanalSistema
from core import config

FASES_SOJA = pd.DataFrame({
    "fase": ["emergência", "vegetativo", "florescimento", "enchimento", "maturação"],
    "dia_inicio": [0, 16, 51, 81, 111], "dia_fim": [15, 50, 80, 110, 125],
})


def _clima(chuva_por_dia: float, eto: float = 5.0, inicio="2025-10-15", dias=140, seco_entre=None) -> pd.DataFrame:
    datas = pd.date_range(inicio, periods=dias, freq="D")
    chuva = np.full(dias, chuva_por_dia)
    if seco_entre:
        chuva[seco_entre[0]:seco_entre[1]] = 0
    return pd.DataFrame({"data": datas, "chuva_mm": chuva, "eto_mm": eto})


def test_sem_falta_de_agua_nao_ha_perda():
    sim = bh.simular(_clima(10.0), date(2025, 10, 15), "soja", FASES_SOJA, 100)
    assert sim.razao_produtividade == pytest.approx(1.0)
    assert (sim.diario["ks"] == 1).all()


def test_seca_no_florescimento_pesa_mais_que_no_vegetativo():
    # 30 dias sem chuva: no vegetativo (dias 16–45) × no florescimento/enchimento (dias 60–89)
    veg = bh.simular(_clima(6.0, seco_entre=(16, 46)), date(2025, 10, 15), "soja", FASES_SOJA, 100)
    flor = bh.simular(_clima(6.0, seco_entre=(60, 90)), date(2025, 10, 15), "soja", FASES_SOJA, 100)
    assert flor.razao_produtividade < veg.razao_produtividade < 1.0
    assert flor.por_fase.set_index("fase").loc["florescimento", "perda_pct"] > 0


def test_solo_que_segura_mais_agua_sofre_menos():
    arenoso = bh.simular(_clima(6.0, seco_entre=(60, 85)), date(2025, 10, 15), "soja", FASES_SOJA, bh.TAW_POR_AD["AD1"])
    argiloso = bh.simular(_clima(6.0, seco_entre=(60, 85)), date(2025, 10, 15), "soja", FASES_SOJA, bh.TAW_POR_AD["AD6"])
    assert argiloso.razao_produtividade > arenoso.razao_produtividade


def test_clima_incompleto_avisa():
    with pytest.raises(ValueError, match="Clima incompleto"):
        bh.simular(_clima(5.0, dias=30), date(2025, 10, 15), "soja", FASES_SOJA, 100)


def test_curva_de_kc_e_radiacao_plausiveis():
    kc = bh.kc_por_dia("soja", FASES_SOJA)
    assert kc[0] == pytest.approx(0.40) and kc[65] == pytest.approx(1.15) and kc[125] == pytest.approx(0.50)
    ra = bh.ra_extraterrestre(np.array([172, 355]))  # junho × dezembro em Itapeva
    assert 20 < ra[0] < 25 and 40 < ra[1] < 45


@pytest.fixture()
def con():
    conexao = duckdb.connect()
    for pasta in ("ddl", "transform"):
        for arquivo in sorted((config.DIR_SQL / pasta).glob("*.sql")):
            conexao.execute(arquivo.read_text(encoding="utf-8"))
    yield conexao
    conexao.close()


def test_central_deduplica_agrava_e_resolve(con):
    canal = CanalSistema()
    geada = AlertaNovo("geada|regiao", "geada", "atencao", "Risco de geada", "3 °C")
    assert canal.publicar(con, [geada], 1)["novos"] == 1
    assert canal.publicar(con, [geada], 1) == {"novos": 0, "atualizados": 1, "agravados": 0, "resolvidos": 0}
    id_, = con.execute("SELECT id FROM notif.alerta").fetchone()
    notificacoes.marcar_lidos(con, [id_])
    forte = AlertaNovo("geada|regiao", "geada", "critico", "Geada forte", "0,5 °C")
    assert canal.publicar(con, [forte], 1)["agravados"] == 1
    assert con.execute("SELECT lido_em IS NULL, nivel FROM notif.alerta").fetchone() == (True, "critico")
    assert canal.publicar(con, [], 1)["resolvidos"] == 1
    assert con.execute("SELECT count(*) FROM notif.vw_alertas_ativos").fetchone()[0] == 0


def test_estimativa_gera_alerta_so_quando_o_modelo_e_confiavel(con):
    estimativas = pd.DataFrame([
        {"plantio_id": 1, "rotulo": "Soja · T1", "meta_sc_ha": 60, "p10_sc_ha": 20, "p50_sc_ha": 30, "p90_sc_ha": 50,
         "ponto_equilibrio_sc_ha": 36, "usar_em_alertas": True},
        {"plantio_id": 2, "rotulo": "Soja · T2", "meta_sc_ha": 60, "p10_sc_ha": 40, "p50_sc_ha": 48, "p90_sc_ha": 60,
         "ponto_equilibrio_sc_ha": 36, "usar_em_alertas": True},
        {"plantio_id": 3, "rotulo": "Trigo · T3", "meta_sc_ha": 60, "p10_sc_ha": 10, "p50_sc_ha": 20, "p90_sc_ha": 30,
         "ponto_equilibrio_sc_ha": 50, "usar_em_alertas": False},
    ])
    alertas = {a.chave: a for a in notificacoes.gerar_alertas(con, None, estimativas) if a.tema == "estimativa"}
    # sem propriedade, só os alertas regionais: a estimativa depende da fazenda
    assert alertas == {}
    con.execute("INSERT INTO fazenda.propriedade (id, nome) VALUES (1, 'X')")
    alertas = {a.chave: a for a in notificacoes.gerar_alertas(con, 1, estimativas) if a.tema == "estimativa"}
    assert alertas["estimativa|plantio:1"].nivel == "critico"      # p50 abaixo do ponto de equilíbrio
    assert alertas["estimativa|plantio:2"].nivel == "atencao"      # 20% abaixo da meta
    assert "estimativa|plantio:3" not in alertas                    # trigo: modelo hídrico pouco confiável


def test_relatorio_de_uso_monta_o_funil():
    """Funil do passo 6: viu o veredito → clicou → agiu, e dias de uso por semana."""
    from datetime import datetime, timedelta

    import duckdb

    from app import eventos
    from scripts import relatorio_uso

    con = duckdb.connect()
    agora = datetime.now()
    linhas = [
        (agora, "s1", "ab_view", "inicio", "v=A", "celular"),
        (agora, "s1", "pagina_vista", "inicio", None, "celular"),
        (agora, "s1", "cta_click", "inicio", "agronomo|v=A", "celular"),
        (agora, "s1", "pagina_vista", "agronomo", None, "celular"),
        (agora, "s1", "pergunta_ia", "agronomo", "sugestao", "celular"),
        (agora - timedelta(days=1), "s2", "ab_view", "inicio", "v=B", "celular"),
        (agora - timedelta(days=1), "s2", "pagina_vista", "inicio", None, "celular"),
    ]
    eventos.gravar(con, linhas)
    r = relatorio_uso.resumo(relatorio_uso.sessoes(con, 30))
    assert r["sessoes"] == 2 and r["dias_com_uso"] == 2
    assert (r["viu_veredito_pct"], r["clicou_pct"], r["agiu_pct"]) == (100, 50, 50)
    assert r["por_versao"]["A"]["agiu"] == 1.0 and r["por_versao"]["B"]["clicou"] == 0.0
    assert relatorio_uso.resumo(relatorio_uso.sessoes(duckdb.connect(), 30)) == {"sessoes": 0}


def test_relatorio_conta_votos_e_uso_da_ia():
    from datetime import datetime

    import duckdb

    from app import eventos
    from core import config
    from scripts import relatorio_uso

    con = duckdb.connect()
    con.execute((config.DIR_SQL / "ddl" / "007_ai.sql").read_text(encoding="utf-8"))
    eventos.gravar(con, [(datetime.now(), "s1", "feedback_veredito", "inicio", "ajudou|v=A", "celular"),
                         (datetime.now(), "s2", "feedback_veredito", "inicio", "nao_ajudou|v=B", "celular")])
    con.execute("INSERT INTO ai.conversa (origem, pergunta, tokens_entrada, tokens_saida) VALUES ('chat', 'x', 900, 100)")
    assert relatorio_uso.extras(con, 7) == {"ajudou": 1, "nao_ajudou": 1, "perguntas_ia": 1, "tokens_ia": 1000}
