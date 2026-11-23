"""Testes do Agrônomo Digital sem rede: um provedor roteirizado faz o papel do modelo."""

import json
from datetime import date, datetime, timedelta

import duckdb
import pytest

from ai import agente, ferramentas
from ai.agente import Agente, ChamadaFerramenta, RespostaModelo
from ai.ferramentas import Contexto
from app import gestao
from core import config


class ProvedorRoteiro:
    """Devolve respostas pré-definidas e guarda as mensagens que recebeu."""

    modelo = "roteiro"

    def __init__(self, respostas: list[RespostaModelo]):
        self.respostas = list(respostas)
        self.recebidas: list[list[dict]] = []

    def responder(self, mensagens, ferramentas_):
        self.recebidas.append(json.loads(json.dumps(mensagens, default=str)))
        return self.respostas.pop(0)


def chamar(nome, **args):
    return RespostaModelo(None, [ChamadaFerramenta(f"c_{nome}", nome, args)], 100, 10)


def final(texto):
    return RespostaModelo(texto, [], 50, 20)


@pytest.fixture()
def banco(tmp_path, monkeypatch):
    caminho = tmp_path / "agente.duckdb"
    monkeypatch.setattr(config, "CAMINHO_DB", caminho)
    hoje = date.today()
    with duckdb.connect(str(caminho)) as con:
        for pasta in ("ddl", "transform"):
            for arquivo in sorted((config.DIR_SQL / pasta).glob("*.sql")):
                con.execute(arquivo.read_text(encoding="utf-8"))
        emitida = datetime.now().replace(microsecond=0)
        for i in range(16):
            con.execute("INSERT INTO raw.previsao_diaria (emitida_em, lat, lon, data, chuva_mm, prob_chuva_pct, "
                        "temp_max_c, temp_min_c) VALUES (?, -24, -48.9, ?, ?, ?, 28, ?)",
                        [emitida, hoje + timedelta(days=i), 0.0 if i < 10 else 15.0, 10 if i < 10 else 80,
                         2.0 if i == 2 else 15.0])
        for h in range(48):
            con.execute("INSERT INTO raw.previsao_horaria (emitida_em, lat, lon, ts_local, temp_c, umid_pct, "
                        "chuva_mm, prob_chuva_pct, vento_kmh) VALUES (?, -24, -48.9, ?, 24, 60, 0, 5, 6)",
                        [emitida, datetime.combine(hoje, datetime.min.time()) + timedelta(hours=h)])
        pid = gestao.criar_propriedade(con, "Sítio Teste")
        tid = gestao.criar_talhao(con, pid, "Chapada", 100, "AD4")
        gestao.criar_plantio(con, tid, "soja", "verao", hoje - timedelta(days=60), produtividade_meta_sc_ha=60)
    return caminho, pid


def test_esquemas_coerentes():
    for nome, (funcao, esquema) in ferramentas.FERRAMENTAS.items():
        f = esquema["function"]
        assert f["name"] == nome
        assert set(f["parameters"]["required"]) <= set(f["parameters"]["properties"])
        assert callable(funcao)


def test_laco_executa_ferramenta_e_devolve_resultado_ao_modelo(banco):
    _, pid = banco
    provedor = ProvedorRoteiro([chamar("previsao_tempo", dias=3), final("Vai gear na quinta.")])
    r = Agente(provedor).perguntar("Vai gear?", Contexto(propriedade_id=pid))
    assert r.texto == "Vai gear na quinta."
    assert [f["nome"] for f in r.ferramentas_usadas] == ["previsao_tempo"]
    msg_ferramenta = provedor.recebidas[1][-1]
    assert msg_ferramenta["role"] == "tool" and "Open-Meteo" in msg_ferramenta["content"]
    assert "geada" in msg_ferramenta["content"].lower()           # alerta de geada (2 °C no 3º dia) chegou ao modelo
    assert r.tokens_entrada == 150 and r.tokens_saida == 30


def test_prompt_sistema_tem_data_e_propriedade(banco):
    _, pid = banco
    provedor = ProvedorRoteiro([final("ok")])
    Agente(provedor).perguntar("oi", Contexto(propriedade_id=pid), nome_propriedade="Sítio Teste")
    sistema = provedor.recebidas[0][0]["content"]
    assert date.today().strftime("%d/%m/%Y") in sistema and "Sítio Teste" in sistema
    assert "receituário agronômico" in sistema


def test_lavoura_em_florescimento_com_veranico_vira_alerta(banco):
    _, pid = banco
    r = ferramentas.executar("minhas_lavouras", {}, Contexto(propriedade_id=pid))
    lavoura = r["lavouras_plantadas"][0]
    assert lavoura["fase_estimada"] == "florescimento"
    assert lavoura["alerta_tempo"]["nivel"] == "Atenção alta"     # 10 dias secos previstos no florescimento


def test_lancamento_por_voz_so_grava_depois_de_confirmar(banco):
    caminho, pid = banco
    ctx = Contexto(propriedade_id=pid)
    provedor = ProvedorRoteiro([
        chamar("propor_lancamento", registro="operacao", talhao="chapada", data=date.today().isoformat(),
               tipo_operacao="pulverizacao", produto="fungicida", dose=0.5, unidade="L/ha", valor=3200,
               categoria="defensivo"),
        final("Preparei o lançamento — confira e toque em Confirmar."),
    ])
    r = Agente(provedor).perguntar("Passei fungicida na Chapada hoje, gastei 3200", ctx)
    assert len(r.pendentes) == 1 and "Pulverização" in r.pendentes[0]["resumo"]
    with duckdb.connect(str(caminho)) as con:
        assert con.execute("SELECT count(*) FROM fazenda.operacao").fetchone()[0] == 0   # nada gravado ainda
        agente.confirmar_pendente(con, r.pendentes[0])
        linha = con.execute("SELECT produto, dose, custo_total, categoria_custo FROM fazenda.operacao").fetchone()
    assert linha == ("fungicida", 0.5, 3200.0, "defensivo")


@pytest.mark.parametrize(("args", "erro"), [
    ({"registro": "operacao", "talhao": "Chapada", "data": "2099-01-01", "tipo_operacao": "plantio"}, "futuro"),
    ({"registro": "operacao", "talhao": "Fundão", "data": "2026-01-01", "tipo_operacao": "plantio"}, "Talhões cadastrados"),
    ({"registro": "despesa", "talhao": "Chapada", "data": "2026-01-01", "valor": 10}, "categoria"),
])
def test_lancamento_invalido_volta_erro_para_o_modelo(banco, args, erro):
    _, pid = banco
    ctx = Contexto(propriedade_id=pid)
    r = ferramentas.executar("propor_lancamento", args, ctx)
    assert erro in r["erro"] and ctx.pendentes == []


def test_ferramenta_desconhecida_e_argumento_invalido(banco):
    ctx = Contexto()
    assert "desconhecida" in ferramentas.executar("apagar_tudo", {}, ctx)["erro"]
    assert "inválidos" in ferramentas.executar("previsao_tempo", {"cidade": "x"}, ctx)["erro"]


def test_sem_fazenda_responde_com_erro_amigavel(banco):
    r = ferramentas.executar("resultado_safra", {}, Contexto(propriedade_id=None))
    assert "Nenhuma propriedade" in r["erro"]


def test_limite_de_rodadas(banco):
    provedor = ProvedorRoteiro([chamar("previsao_tempo")] * agente.MAX_RODADAS)
    r = Agente(provedor).perguntar("?", Contexto())
    assert "consultar dados demais" in r.texto and len(r.ferramentas_usadas) == agente.MAX_RODADAS


def test_pagina_sem_chave_orienta_o_usuario(monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    at = AppTest.from_file(str(config.RAIZ / "app" / "paginas" / "agronomo.py"), default_timeout=60)
    at.session_state["propriedade_id"] = None
    at.run()
    assert not at.exception
    assert any("OPENAI_API_KEY" in w.value for w in at.warning)


def test_estoque_considera_todas_as_safras(banco):
    caminho, pid = banco
    with duckdb.connect(str(caminho)) as con:
        tid = con.execute("SELECT id FROM fazenda.talhao LIMIT 1").fetchone()[0]
        trigo = gestao.criar_plantio(con, tid, "trigo", "inverno", date(2025, 4, 20), produtividade_meta_sc_ha=55)
        gestao.registrar_colheita(con, trigo, date(2025, 9, 20), sacas=5000)
        gestao.registrar_venda(con, pid, "trigo", "2024/25", date(2025, 10, 1), 2000, 78)
    r = ferramentas.executar("resultado_safra", {}, Contexto(propriedade_id=pid))  # safra padrão = a mais recente
    trigo_estoque = next(e for e in r["estoque_todas_as_safras"] if e["cultura"] == "trigo")
    assert trigo_estoque["sacas_em_estoque"] == 3000 and trigo_estoque["preco_referencia_sc"] == 80
