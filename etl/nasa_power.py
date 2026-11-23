"""ETL NASA POWER: clima diário desde 1981 no centroide de cada município.

Complementa a A714 (que começa em 2006), permitindo cruzar o clima com a PAM em
séries longas e para os municípios vizinhos que não têm estação.
"""

from __future__ import annotations

import logging
from datetime import date, datetime

import duckdb
import pandas as pd

from core.db import substituir
from core.http import criar_sessao, get_json

log = logging.getLogger(__name__)

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
INICIO = date(1981, 1, 1)
PARAMETROS = {
    "PRECTOTCORR": "chuva_mm",
    "T2M": "temp_c",
    "T2M_MAX": "temp_max_c",
    "T2M_MIN": "temp_min_c",
    "RH2M": "umid_pct",
    "WS2M": "vento_2m_ms",
    "ALLSKY_SFC_SW_DWN": "radiacao_mj_m2",
}
VALOR_AUSENTE = -999


def baixar_ponto(lat: float, lon: float, inicio: date, fim: date, sessao=None) -> pd.DataFrame:
    dados = get_json(
        URL,
        params={
            "parameters": ",".join(PARAMETROS),
            "community": "AG",
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "start": inicio.strftime("%Y%m%d"),
            "end": fim.strftime("%Y%m%d"),
            "format": "JSON",
        },
        sessao=sessao,
    )
    serie = dados["properties"]["parameter"]
    df = pd.DataFrame({PARAMETROS[p]: valores for p, valores in serie.items()})
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df = df.mask(df <= VALOR_AUSENTE)
    return df.rename_axis("data").reset_index()


def executar(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    municipios = con.execute(
        "SELECT codigo_ibge, nome, lat, lon FROM analytics.dim_municipio WHERE lat IS NOT NULL"
    ).fetchall()
    if not municipios:
        raise RuntimeError("Centroides ausentes: rode o ETL do IBGE antes do NASA POWER.")
    sessao, total = criar_sessao(), 0
    for codigo, nome, lat, lon in municipios:
        df = baixar_ponto(lat, lon, INICIO, date.today(), sessao)
        df.insert(0, "codigo_ibge", codigo)
        df["carregado_em"] = datetime.now()
        total += substituir(con, "raw.nasa_power_diario", df, onde="codigo_ibge = ?", params=[codigo])
        log.info("NASA POWER %s: %d dias", nome, len(df))
    return {"nasa_power_diario": total}
