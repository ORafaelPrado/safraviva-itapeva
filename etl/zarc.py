"""ETL ZARC (MAPA): tábuas de risco climático de todas as safras publicadas.

Cada CSV é nacional e grande, e o servidor não aceita download parcial. Por isso
lemos em streaming, mantemos só as linhas dos municípios da região e guardamos
esse recorte em data/raw/zarc/ (as safras passadas ficam em cache).
"""

from __future__ import annotations

import csv
import io
import logging
import re
from datetime import datetime
from typing import Iterable, Iterator

import duckdb
import pandas as pd

from core import config
from core.db import substituir
from core.http import criar_sessao, get_json

log = logging.getLogger(__name__)

URL_PACOTE = "https://dados.agricultura.gov.br/api/3/action/package_show"
DATASET = "tabua-de-risco-zoneamento-agricola-de-risco-climatico"
DIR_ZARC = config.DIR_RAW / "zarc"
PADRAO_SAFRA = re.compile(r"Safra (\d{4})/(\d{4})")
DECENDIOS = [f"dec{i}" for i in range(1, 37)]
COLUNAS_RAW = [
    "safra", "nome_cultura", "safraini", "safrafin", "cod_cultura", "cod_ciclo", "cod_solo",
    "geocodigo", "uf", "municipio", "cod_clima", "nome_clima", "cod_outros_manejos",
    "nome_outros_manejos", "produtividade", "cod_nm", "cod_munic", "cod_meso", "cod_micro",
    "portaria", *DECENDIOS,
]


def listar_safras(sessao=None) -> dict[str, str]:
    """Devolve {'2026-2027': url_csv} para cada tábua de risco anual publicada."""
    recursos = get_json(URL_PACOTE, params={"id": DATASET}, sessao=sessao)["result"]["resources"]
    safras = {}
    for r in recursos:
        achado = PADRAO_SAFRA.search(r["name"])
        if achado and r["format"].upper() == "CSV":
            safras[f"{achado[1]}-{achado[2]}"] = r["url"]
    return dict(sorted(safras.items()))


def filtrar_linhas(linhas: Iterable[str], geocodigos: set[str]) -> Iterator[list[str]]:
    """Lê o CSV linha a linha e devolve o cabeçalho e as linhas dos municípios de interesse."""
    leitor = csv.reader(linhas, delimiter=";")
    cabecalho = [c.strip().lstrip("﻿") for c in next(leitor)]
    yield cabecalho
    idx = cabecalho.index("geocodigo")
    for linha in leitor:
        if len(linha) > idx and linha[idx] in geocodigos:
            yield linha


def baixar_safra(safra: str, url: str, geocodigos: set[str], forcar: bool, sessao) -> pd.DataFrame:
    cache = DIR_ZARC / f"{safra}.csv"
    if forcar or not cache.exists():
        log.info("ZARC: lendo tábua %s (arquivo nacional)", safra)
        with sessao.get(url, stream=True, timeout=(10, 900)) as resp:
            resp.raise_for_status()
            resp.raw.decode_content = True  # descompacta gzip/deflate do transporte
            texto = io.TextIOWrapper(resp.raw, encoding="utf-8-sig", errors="replace", newline="")
            linhas = list(filtrar_linhas(texto, geocodigos))
        cache.parent.mkdir(parents=True, exist_ok=True)
        with cache.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f, delimiter=";").writerows(linhas)
    return pd.read_csv(cache, sep=";", dtype=str, keep_default_na=False)


def normalizar(df: pd.DataFrame, safra: str) -> pd.DataFrame:
    """Padroniza nomes e tipos; decêndios viram inteiros (risco em %, 0 = não indicado)."""
    df = df.rename(columns=str.lower)
    for col in DECENDIOS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ("cod_ciclo", "cod_solo", "geocodigo", "cod_clima", "cod_outros_manejos", "safraini", "safrafin"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    df.insert(0, "safra", safra)
    # Safras antigas podem trazer colunas a mais/a menos: fica só o que a raw conhece.
    return df.reindex(columns=COLUNAS_RAW)


def executar(con: duckdb.DuckDBPyConnection, forcar_recentes: int = 2) -> dict[str, int]:
    """Carrega todas as safras; as `forcar_recentes` mais novas são sempre baixadas de novo."""
    sessao = criar_sessao()
    geocodigos = {str(m.codigo_ibge) for m in config.MUNICIPIOS}
    safras = listar_safras(sessao)
    recentes = set(list(safras)[-forcar_recentes:])
    total = 0
    for safra, url in safras.items():
        df = normalizar(baixar_safra(safra, url, geocodigos, safra in recentes, sessao), safra)
        df["carregado_em"] = datetime.now()
        total += substituir(con, "raw.zarc_tabua", df, onde="safra = ?", params=[safra])
        log.info("ZARC %s: %d linhas da região", safra, len(df))
    return {"zarc_tabua": total}
