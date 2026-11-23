"""Atualização dos dados, das estimativas de safra e da central de alertas.

* Painel: ao abrir, se a previsão tiver mais de 6 h, roda a versão rápida (previsão + alertas, ~5 s).
* Rotina diária (scripts/rotina_diaria.py): versão completa (previsão, NASA, transformações, alertas,
  e às segundas o resumo semanal).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import duckdb

from analytics import balanco_hidrico
from app import notificacoes

log = logging.getLogger(__name__)
IDADE_MAXIMA_PREVISAO = timedelta(hours=6)


def previsao_velha(con: duckdb.DuckDBPyConnection) -> bool:
    emitida = con.execute("SELECT max(emitida_em) FROM raw.previsao_diaria").fetchone()[0]
    return emitida is None or datetime.now() - emitida > IDADE_MAXIMA_PREVISAO


def atualizar_alertas(con: duckdb.DuckDBPyConnection) -> dict:
    """Estimativas de safra + alertas para a região e para cada propriedade."""
    resumo = {"estimativas": 0}
    propriedades = [r[0] for r in con.execute("SELECT id FROM fazenda.propriedade").fetchall()]
    if not propriedades:
        resumo["regiao"] = notificacoes.atualizar_central(con, None)
    for pid in propriedades:
        estimativas = balanco_hidrico.estimar_propriedade(con, pid)
        resumo["estimativas"] += len(estimativas)
        resumo[f"propriedade_{pid}"] = notificacoes.atualizar_central(
            con, pid, balanco_hidrico.tabela_estimativas(estimativas, con))
    return resumo


def atualizar(con: duckdb.DuckDBPyConnection, fontes: tuple[str, ...] = ("previsao",),
              transformar: bool = False) -> dict:
    from etl import inmet, nasa_power, open_meteo
    from scripts import rodar_etl, setup_db

    setup_db.aplicar_ddl(con)
    extratores = {"previsao": open_meteo.executar, "nasa": nasa_power.executar,
                  "inmet": lambda c: inmet.executar(c, anos=range(datetime.now().year, datetime.now().year + 1))}
    resumo = {}
    for fonte in fontes:
        try:
            resumo[fonte] = extratores[fonte](con)
        except Exception as erro:  # noqa: BLE001 — uma fonte fora do ar não impede o resto
            log.warning("Fonte %s falhou: %s", fonte, erro)
            resumo[fonte] = f"falhou: {erro}"
    if transformar:
        rodar_etl.transformar(con)
    resumo["alertas"] = atualizar_alertas(con)
    return resumo
