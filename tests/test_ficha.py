"""Ficha da fazenda (formulário do produtor): conversões, validação e criação da fazenda real."""

import json
from datetime import date

import duckdb
import pytest

from app import ficha
from core import config


@pytest.fixture()
def con():
    conexao = duckdb.connect()
    for arquivo in sorted((config.DIR_SQL / "ddl").glob("*.sql")):
        conexao.execute(arquivo.read_text(encoding="utf-8"))
    yield conexao
    conexao.close()


def _respostas(**fazenda):
    return {
        "fazenda": {"nome": "Sítio Teste", "coordenadas": "-23.98, -48.87", "unidade_area": "alqueire", **fazenda},
        "talhoes": [
            {"nome": "Chapada", "area": 10, "terra": "argilosa_profunda", "lavoura": "soja",
             "data_plantio": "2026-10-20", "cultivar": "BRS 1003", "ciclo": "medio", "meta_sc_ha": 65},
            {"nome": "Baixada", "area": 4, "terra": "nao_sei", "lavoura": "milho", "data_plantio": None,
             "cultivar": "", "ciclo": "nao_sei", "meta_sc_ha": None},
            {"nome": "Fundo", "area": 2, "terra": "arenosa", "lavoura": "nada"},
            {"nome": "", "area": None},  # talhão a mais deixado em branco
        ],
        "whatsapp": "",
    }


def test_coordenadas_do_google_maps():
    assert ficha.ler_coordenadas("-23.982145, -48.876543") == (-23.982145, -48.876543)
    assert ficha.ler_coordenadas("  ") is None
    with pytest.raises(ValueError):
        ficha.ler_coordenadas("23.98, 48.87")  # fora do Brasil (sem o sinal de menos)
    with pytest.raises(ValueError):
        ficha.ler_coordenadas("perto da igreja")


def test_validacao_fala_a_lingua_do_produtor():
    assert ficha.validar(_respostas()) == []
    r = _respostas(nome=" ")
    r["talhoes"] = [{"nome": "Sede", "area": None}, {"nome": "sede", "area": 3}]
    erros = " ".join(ficha.validar(r))
    assert "nome da fazenda" in erros and "falta a **área**" in erros and "dois talhões" in erros


def test_ficha_cria_a_fazenda_real_convertendo_unidades(con):
    res = ficha.salvar(con, _respostas())
    assert res["situacao"] == "aplicada"
    pid = res["propriedade_id"]
    assert con.execute("SELECT nome, demo, lat FROM fazenda.propriedade WHERE id = ?", [pid]).fetchone() == \
        ("Sítio Teste", False, -23.98)
    talhoes = con.execute("SELECT nome, area_ha, solo_ad FROM fazenda.talhao ORDER BY nome").fetchall()
    assert talhoes == [("Baixada", 9.68, None), ("Chapada", 24.2, "AD5"), ("Fundo", 4.84, "AD2")]  # alqueire → ha
    plantios = con.execute("""SELECT t.nome, p.cultura, p.status, p.grupo_ciclo, p.safra FROM fazenda.plantio p
                              JOIN fazenda.talhao t ON t.id = p.talhao_id ORDER BY t.nome""").fetchall()
    assert plantios[0][:3] == ("Baixada", "milho", "planejado")            # sem data: planejado
    assert plantios[1] == ("Chapada", "soja", "plantado", "Grupo II", "2026/27")
    assert len(plantios) == 2                                                # "nada plantado" não vira lavoura
    guardada = json.loads(con.execute("SELECT respostas FROM fazenda.ficha").fetchone()[0])
    assert guardada["talhoes"][0]["cultivar"] == "BRS 1003"


def test_ficha_repetida_nao_duplica_e_nao_perde_as_respostas(con):
    ficha.salvar(con, _respostas())
    res = ficha.salvar(con, _respostas())
    assert res["situacao"] == "guardada" and "Já existe" in res["aviso"]
    assert con.execute("SELECT count(*) FROM fazenda.propriedade").fetchone()[0] == 1
    assert con.execute("SELECT count(*) FROM fazenda.ficha").fetchone()[0] == 2
