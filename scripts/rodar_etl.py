"""Orquestrador do ETL do SafraViva.

    python -m scripts.rodar_etl                    # tudo
    python -m scripts.rodar_etl --fontes previsao  # só a previsão (uso diário)
    python -m scripts.rodar_etl --so-transformar   # só reconstrói a camada analytics

Ordem: setup do banco → extratores (raw) → transformações SQL (analytics).
"""

from __future__ import annotations

import argparse
import logging
import time

from core import config
from core.db import conectar
from etl import conab_custos, cotacoes, ibge, inmet, nasa_power, open_meteo, zarc
from scripts import setup_db

# A ordem importa: o NASA POWER usa os centroides carregados pelo IBGE.
EXTRATORES = {
    "ibge": ibge.executar,
    "previsao": open_meteo.executar,
    "nasa": nasa_power.executar,
    "inmet": inmet.executar,
    "zarc": zarc.executar,
    "conab": conab_custos.executar,
    "cotacoes": cotacoes.executar,
}

log = logging.getLogger("etl")


def transformar(con) -> list[str]:
    """Executa sql/transform/*.sql em ordem alfabética (prefixo numérico)."""
    arquivos = sorted((config.DIR_SQL / "transform").glob("*.sql"))
    for arquivo in arquivos:
        con.execute(arquivo.read_text(encoding="utf-8"))
        log.info("transform %s", arquivo.name)
    return [a.name for a in arquivos]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fontes", default=",".join(EXTRATORES), help="lista separada por vírgula")
    parser.add_argument("--so-transformar", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    with conectar() as con:
        setup_db.aplicar_ddl(con)
        setup_db.sincronizar_dimensoes(con)
        if not args.so_transformar:
            for fonte in args.fontes.split(","):
                t0 = time.perf_counter()
                resultado = EXTRATORES[fonte.strip()](con)
                log.info("%s concluído em %.0fs: %s", fonte, time.perf_counter() - t0, resultado)
        transformar(con)


if __name__ == "__main__":
    main()
