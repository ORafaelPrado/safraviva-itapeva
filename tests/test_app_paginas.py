"""Testes de interface do painel com o AppTest do Streamlit (sem navegador).

* Fumaça: cada página roda sem exceção sobre o banco real (pulado se o banco não existir).
* Gravação: preenche e envia o formulário de operação num banco temporário e confere o banco.
"""

from datetime import date

import duckdb
import pytest
from streamlit.testing.v1 import AppTest

from app import gestao
from core import config

PAGINAS = config.RAIZ / "app" / "paginas"


def _app(pagina: str, propriedade_id=None) -> AppTest:
    at = AppTest.from_file(str(PAGINAS / pagina), default_timeout=60)
    at.session_state["propriedade_id"] = propriedade_id
    return at


@pytest.fixture()
def banco_temporario(tmp_path, monkeypatch):
    """Banco novo com o DDL completo e uma propriedade com um plantio aberto."""
    caminho = tmp_path / "app.duckdb"
    monkeypatch.setattr(config, "CAMINHO_DB", caminho)
    with duckdb.connect(str(caminho)) as con:
        for pasta in ("ddl", "transform"):  # transformações sobre tabelas raw vazias: estrutura completa
            for arquivo in sorted((config.DIR_SQL / pasta).glob("*.sql")):
                con.execute(arquivo.read_text(encoding="utf-8"))
        pid = gestao.criar_propriedade(con, "Teste")
        tid = gestao.criar_talhao(con, pid, "T1", 50, "AD4")
        plantio = gestao.criar_plantio(con, tid, "soja", "verao", date(2026, 10, 10), status="plantado",
                                       produtividade_meta_sc_ha=60)
    import streamlit as st

    st.cache_data.clear()
    yield caminho, pid, plantio
    st.cache_data.clear()


def test_lancar_operacao_grava_no_banco(banco_temporario):
    caminho, pid, plantio = banco_temporario
    at = _app("lancar.py", pid).run()
    assert not at.exception
    at.text_input[0].set_value("Fungicida X")          # Produto / máquina (primeiro campo de texto da aba Operação)
    custo = next(n for n in at.number_input if n.label == "Custo total (R$)")
    custo.set_value(1500.0)
    next(b for b in at.button if b.label == "Salvar operação").click()
    at.run()
    assert not at.exception
    assert any("salva" in s.value for s in at.success)
    with duckdb.connect(str(caminho), read_only=True) as con:
        linha = con.execute("SELECT plantio_id, produto, custo_total, categoria_custo FROM fazenda.operacao").fetchone()
    assert linha == (plantio, "Fungicida X", 1500.0, "defensivo")  # tipo padrão "preparo" → categoria defensivo


def test_resultados_renderiza_com_plantio_aberto(banco_temporario):
    _, pid, _ = banco_temporario
    at = _app("fazenda.py", pid).run()
    assert not at.exception
    assert any("Margem prevista" in m.label for m in at.metric)


@pytest.mark.skipif(not config.CAMINHO_DB.exists(), reason="banco real ainda não carregado")
@pytest.mark.parametrize("pagina", ["inicio.py", "clima.py", "plantio.py", "producao.py", "safras.py",
                                    "fazenda.py", "lancar.py", "caderno.py", "ficha.py", "alertas.py", "estimativa.py", "cotacoes.py", "agronomo.py"])
def test_paginas_rodam_sem_erro_no_banco_real(pagina):
    with duckdb.connect(str(config.CAMINHO_DB), read_only=True) as con:
        props = con.execute("SELECT id FROM fazenda.propriedade ORDER BY demo, id LIMIT 1").fetchall()
    at = _app(pagina, props[0][0] if props else None).run()
    assert not at.exception, at.exception


def test_senha_protege_o_painel_online(monkeypatch):
    monkeypatch.setenv("APP_SENHA", "milho2026")
    at = AppTest.from_file(str(config.RAIZ / "app" / "main.py"), default_timeout=60).run()
    assert not at.exception
    assert [t.label for t in at.text_input] == ["Senha"]          # só a tela de senha aparece
    at.text_input[0].set_value("errada")
    at.button[0].click().run()
    assert any("incorreta" in e.value for e in at.error)
    at.text_input[0].set_value("milho2026")
    at.button[0].click().run()
    assert at.session_state["_acesso_liberado"] is True


def test_inicio_mostra_veredito_e_versao_do_link(banco_temporario):
    """Primeira dobra: a versão do texto pode ser forçada pelo link (?v=B) e vira evento ab_view na fila."""
    _, pid, _ = banco_temporario
    at = _app("inicio.py", pid)
    at.query_params["v"] = "b"
    at.run()
    assert not at.exception
    assert at.session_state["_versao_heroi"] == "B"
    fila = at.session_state["_eventos_pendentes"] if "_eventos_pendentes" in at.session_state else []
    # sem previsão no banco temporário não há veredito, então não há ab_view; com previsão, há exatamente um
    assert all(e[2] == "ab_view" and e[4] == "v=B" for e in fila)


def test_eventos_gravam_no_banco(banco_temporario):
    from datetime import datetime

    from app import eventos

    caminho, _, _ = banco_temporario
    with duckdb.connect(str(caminho)) as con:
        n = eventos.gravar(con, [(datetime(2026, 11, 24, 7), "abc", "cta_click", "inicio", "agronomo|v=A", "celular")])
        assert n == 1
        assert con.execute("SELECT evento, detalhe FROM uso.evento").fetchall() == [("cta_click", "agronomo|v=A")]


def test_ficha_da_fazenda_preenchida_e_enviada(banco_temporario):
    """O produtor preenche a ficha no celular e a fazenda real aparece no banco."""
    caminho, pid, _ = banco_temporario
    at = _app("ficha.py", pid).run()
    assert not at.exception
    campo = {t.label: t for t in at.text_input}
    campo["Nome da fazenda ou do sítio"].set_value("Sítio do Pai")
    next(t for t in at.text_input if t.key == "t0_nome").set_value("Chapada")
    next(n for n in at.number_input if n.key == "t0_area").set_value(12.0)
    next(b for b in at.button if b.label == "Enviar ficha").click()
    at.run()
    assert not at.exception
    assert at.session_state["_ficha_ok"]["situacao"] == "aplicada"
    with duckdb.connect(str(caminho), read_only=True) as con:
        assert con.execute("SELECT count(*) FROM fazenda.propriedade WHERE nome = 'Sítio do Pai' AND NOT demo").fetchone()[0] == 1
        assert con.execute("SELECT area_ha FROM fazenda.talhao WHERE nome = 'Chapada'").fetchone()[0] == 12.0
