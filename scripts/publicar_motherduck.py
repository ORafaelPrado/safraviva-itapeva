"""Envia o banco local para o MotherDuck (DuckDB na nuvem), para o painel online e a rotina do GitHub Actions.

    python -m scripts.publicar_motherduck              # cria o banco na nuvem (recusa se já existir)
    python -m scripts.publicar_motherduck --substituir # SOBRESCREVE o da nuvem com o local (cuidado!)
    python -m scripts.publicar_motherduck --baixar     # traz uma cópia da nuvem para data/backup_nuvem.duckdb

Precisa de MOTHERDUCK_TOKEN no .env. Depois da publicação, o banco da NUVEM passa a ser o oficial
(os lançamentos feitos no painel online ficam lá). Por isso, sobrescrever exige --substituir.
"""

from __future__ import annotations

import argparse
import os
import sys

import duckdb

from core import config


def main() -> None:
    parser = argparse.ArgumentParser()
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--substituir", action="store_true")
    grupo.add_argument("--baixar", action="store_true")
    args = parser.parse_args()

    if not os.getenv("MOTHERDUCK_TOKEN"):
        sys.exit("Falta MOTHERDUCK_TOKEN no arquivo .env (crie em app.motherduck.com → Settings → Access tokens).")
    banco = os.getenv("MOTHERDUCK_BANCO", "safraviva")
    nuvem = duckdb.connect("md:")
    existentes = {r[0] for r in nuvem.execute("SELECT database_name FROM duckdb_databases()").fetchall()}

    if args.baixar:
        destino = config.DIR_DADOS / "backup_nuvem.duckdb"
        destino.unlink(missing_ok=True)
        nuvem.execute(f"ATTACH '{destino.as_posix()}' AS backup")
        nuvem.execute(f"COPY FROM DATABASE {banco} TO backup")
        print(f"Cópia da nuvem salva em {destino}")
        return

    if banco in existentes and not args.substituir:
        sys.exit(f"O banco '{banco}' já existe no MotherDuck e pode ter lançamentos feitos online. "
                 "Use --baixar para fazer backup ou --substituir se tiver certeza.")
    if banco in existentes:
        nuvem.execute(f"DROP DATABASE {banco}")
    publicar(nuvem, banco, config.CAMINHO_DB.as_posix())


# Tabelas com chave estrangeira, na ordem pai → filho (o resto não tem dependência).
ORDEM_FK = ["fazenda.propriedade", "fazenda.talhao", "fazenda.plantio", "fazenda.operacao", "fazenda.custo",
            "fazenda.colheita", "fazenda.venda", "fazenda.ocorrencia"]
# Sequências e as tabelas cujo maior id elas precisam ultrapassar.
SEQUENCIAS = {"fazenda.seq_id": ORDEM_FK, "ai.seq_conversa": ["ai.conversa"], "notif.seq_alerta": ["notif.alerta"]}


def publicar(nuvem: duckdb.DuckDBPyConnection, banco: str, arquivo_local: str) -> None:
    """Cria o banco na nuvem com o mesmo DDL do projeto e copia os dados respeitando as chaves.

    (O `CREATE DATABASE ... FROM` do MotherDuck copia as tabelas fora de ordem e viola as FKs.)
    """
    from scripts import rodar_etl

    nuvem.execute(f"CREATE DATABASE {banco}")
    nuvem.execute(f"ATTACH '{arquivo_local}' AS loc (READ_ONLY)")
    nuvem.execute(f"USE {banco}")

    # 1) esquemas e sequências começando depois do maior id local (para não colidir com ids copiados)
    for esquema in ("raw", "staging", "analytics", "fazenda", "ai", "notif"):
        nuvem.execute(f"CREATE SCHEMA IF NOT EXISTS {esquema}")
    for seq, tabelas in SEQUENCIAS.items():
        maior = max((nuvem.execute(f"SELECT coalesce(max(id), 0) FROM loc.{t}").fetchone()[0] for t in tabelas), default=0)
        nuvem.execute(f"CREATE SEQUENCE IF NOT EXISTS {seq} START {maior + 1}")

    # 2) estrutura: o mesmo DDL do projeto (tabelas, chaves, views)
    for arquivo in sorted((config.DIR_SQL / "ddl").glob("*.sql")):
        nuvem.execute(arquivo.read_text(encoding="utf-8"))

    # 3) dados: tabelas com FK na ordem pai → filho; as demais em qualquer ordem
    locais = [f"{s}.{t}" for s, t in nuvem.execute(
        "SELECT table_schema, table_name FROM information_schema.tables "
        "WHERE table_catalog = 'loc' AND table_type = 'BASE TABLE'").fetchall()]
    na_nuvem = {f"{s}.{t}" for s, t in nuvem.execute(
        f"SELECT table_schema, table_name FROM information_schema.tables "
        f"WHERE table_catalog = '{banco}' AND table_type = 'BASE TABLE'").fetchall()}
    ordem = [t for t in ORDEM_FK if t in locais] + sorted(t for t in locais if t not in ORDEM_FK)
    for tabela in reversed(ordem):  # limpa o que o DDL já populou (filhos antes dos pais)
        if tabela in na_nuvem:
            nuvem.execute(f"DELETE FROM {tabela}")
    for tabela in ordem:
        if tabela in na_nuvem:
            nuvem.execute(f"INSERT INTO {tabela} BY NAME SELECT * FROM loc.{tabela}")
        else:
            nuvem.execute(f"CREATE TABLE {tabela} AS SELECT * FROM loc.{tabela}")
        n = nuvem.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0]
        print(f"  {tabela:<40} {n:>9} linhas")
    nuvem.execute("DETACH loc")

    # 4) camada analytics e views recalculadas na nuvem
    rodar_etl.transformar(nuvem)
    total = nuvem.execute(f"SELECT count(*) FROM information_schema.tables WHERE table_catalog = '{banco}'").fetchone()[0]
    print(f"Banco local publicado em md:{banco} ({total} tabelas e views).")


if __name__ == "__main__":
    main()
