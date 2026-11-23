"""Cria/atualiza o banco DuckDB do SafraViva.

    python -m scripts.setup_db

Executa os scripts de sql/ddl/ em ordem e sincroniza as dimensões com
core/config.py. Idempotente.
"""

from __future__ import annotations

import duckdb

from core import config
from core.db import conectar


def aplicar_ddl(con: duckdb.DuckDBPyConnection) -> list[str]:
    arquivos = sorted((config.DIR_SQL / "ddl").glob("*.sql"))
    for arquivo in arquivos:
        con.execute(arquivo.read_text(encoding="utf-8"))
    return [a.name for a in arquivos]


def sincronizar_dimensoes(con: duckdb.DuckDBPyConnection) -> None:
    con.executemany(
        "INSERT INTO analytics.dim_municipio (codigo_ibge, nome, microrregiao, foco) "
        "VALUES (?, ?, ?, ?) ON CONFLICT (codigo_ibge) DO UPDATE "
        "SET nome = excluded.nome, microrregiao = excluded.microrregiao, foco = excluded.foco",
        [(m.codigo_ibge, m.nome, m.microrregiao, m.foco) for m in config.MUNICIPIOS],
    )
    con.executemany(
        "INSERT INTO analytics.dim_cultura VALUES (?, ?, ?, ?) ON CONFLICT (slug) DO UPDATE "
        "SET nome = excluded.nome, codigo_sidra = excluded.codigo_sidra, estacao = excluded.estacao",
        [(c.slug, c.nome, c.codigo_sidra, c.estacao) for c in config.CULTURAS],
    )
    con.executemany(
        "INSERT OR REPLACE INTO analytics.dim_estacao VALUES (?, ?, ?, ?, ?, ?)",
        [
            (e.codigo, e.nome, e.lat, e.lon, e.altitude_m, e.distancia_itapeva_km)
            for e in config.ESTACOES_INMET
        ],
    )


def main() -> None:
    with conectar() as con:
        aplicados = aplicar_ddl(con)
        sincronizar_dimensoes(con)
        resumo = con.execute(
            """
            SELECT 'dim_municipio', count(*) FROM analytics.dim_municipio
            UNION ALL SELECT 'dim_cultura', count(*) FROM analytics.dim_cultura
            UNION ALL SELECT 'dim_estacao', count(*) FROM analytics.dim_estacao
            UNION ALL SELECT 'dim_tempo', count(*) FROM analytics.dim_tempo
            """
        ).fetchall()
    print(f"Banco: {config.CAMINHO_DB}")
    print(f"DDL aplicada: {', '.join(aplicados)}")
    for tabela, linhas in resumo:
        print(f"  {tabela:<14} {linhas:>6} linhas")


if __name__ == "__main__":
    main()
