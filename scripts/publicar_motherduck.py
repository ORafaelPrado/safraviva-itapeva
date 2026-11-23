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
    local = config.CAMINHO_DB.as_posix()
    if banco in existentes:
        nuvem.execute(f"DROP DATABASE {banco}")
    nuvem.execute(f"CREATE DATABASE {banco} FROM '{local}'")
    tabelas = nuvem.execute(f"SELECT count(*) FROM {banco}.information_schema.tables").fetchone()[0]
    print(f"Banco local publicado em md:{banco} ({tabelas} tabelas e views).")


if __name__ == "__main__":
    main()
