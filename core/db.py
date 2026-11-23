"""Acesso ao banco DuckDB e utilitários de carga.

Onde fica o banco:
* sem MOTHERDUCK_TOKEN (computador de casa, testes): arquivo local `data/safraviva.duckdb`;
* com MOTHERDUCK_TOKEN (painel online e GitHub Actions): banco `md:<MOTHERDUCK_BANCO>` no MotherDuck,
  o mesmo DuckDB, na nuvem. Assim o painel online e a rotina diária leem e gravam no mesmo lugar.
"""

from __future__ import annotations

import os

import duckdb
import pandas as pd

from core import config


def destino() -> str:
    """Descrição curta de onde está o banco (para logs e para a tela)."""
    return f"MotherDuck (md:{_banco_nuvem()})" if os.getenv("MOTHERDUCK_TOKEN") else str(config.CAMINHO_DB)


def _banco_nuvem() -> str:
    return os.getenv("MOTHERDUCK_BANCO", "safraviva")


def conectar(leitura: bool = False) -> duckdb.DuckDBPyConnection:
    """Abre o banco. `leitura=True` no arquivo local abre somente-leitura (não trava o ETL)."""
    if os.getenv("MOTHERDUCK_TOKEN"):
        return duckdb.connect(f"md:{_banco_nuvem()}")  # o token é lido da variável de ambiente
    config.CAMINHO_DB.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(config.CAMINHO_DB), read_only=leitura)


def substituir(
    con: duckdb.DuckDBPyConnection,
    tabela: str,
    df: pd.DataFrame,
    onde: str | None = None,
    params: list | None = None,
) -> int:
    """Carga idempotente: apaga o recorte `onde` (ou a tabela toda) e insere `df`.

    A tabela é criada na primeira carga com o esquema do DataFrame.
    """
    con.register("_carga", df)
    try:
        con.execute(f"CREATE TABLE IF NOT EXISTS {tabela} AS SELECT * FROM _carga LIMIT 0")
        con.execute(f"DELETE FROM {tabela}" + (f" WHERE {onde}" if onde else ""), params or [])
        con.execute(f"INSERT INTO {tabela} BY NAME SELECT * FROM _carga")
    finally:
        con.unregister("_carga")
    return len(df)
