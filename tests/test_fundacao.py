"""Testes da Fase 0: configuração e banco (sem rede)."""

from datetime import date

import duckdb
import pytest

from core import config
from scripts import setup_db


@pytest.fixture()
def con(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CAMINHO_DB", tmp_path / "teste.duckdb")
    with setup_db.conectar() as conexao:
        setup_db.aplicar_ddl(conexao)
        setup_db.sincronizar_dimensoes(conexao)
        yield conexao


def test_config_sem_duplicatas():
    assert len({m.codigo_ibge for m in config.MUNICIPIOS}) == len(config.MUNICIPIOS)
    assert len({c.codigo_sidra for c in config.CULTURAS}) == len(config.CULTURAS)
    assert [m.codigo_ibge for m in config.MUNICIPIOS if m.foco] == [config.CODIGO_ITAPEVA]


@pytest.mark.parametrize(
    ("dia", "ano_safra", "decendio"),
    [
        (date(2026, 10, 15), "2026/27", 29),
        (date(2027, 6, 30), "2026/27", 18),
        (date(2026, 7, 1), "2026/27", 19),
        (date(2026, 1, 10), "2025/26", 1),
        (date(2026, 12, 31), "2026/27", 36),
    ],
)
def test_dim_tempo_ano_safra_e_decendio(con, dia, ano_safra, decendio):
    linha = con.execute(
        "SELECT ano_safra, decendio FROM analytics.dim_tempo WHERE data = ?", [dia]
    ).fetchone()
    assert linha == (ano_safra, decendio)


def test_setup_idempotente(con):
    setup_db.aplicar_ddl(con)
    setup_db.sincronizar_dimensoes(con)
    assert con.execute("SELECT count(*) FROM analytics.dim_municipio").fetchone()[0] == len(config.MUNICIPIOS)


def test_schemas_criados(con):
    schemas = {r[0] for r in con.execute("SELECT schema_name FROM information_schema.schemata").fetchall()}
    assert {"raw", "staging", "analytics", "fazenda"} <= schemas
