"""ETL Open-Meteo: previsão de 16 dias (diária e horária) para a fazenda de referência.

Cada execução guarda um "retrato" da previsão com a data de emissão. Assim
depois dá para medir o quanto a previsão acertou em Itapeva.
"""

from __future__ import annotations

import logging
from datetime import date, datetime

import duckdb
import pandas as pd

from core import config
from core.db import substituir
from core.http import get_json

log = logging.getLogger(__name__)

URL = "https://api.open-meteo.com/v1/forecast"

DIARIAS = {
    "precipitation_sum": "chuva_mm",
    "precipitation_probability_max": "prob_chuva_pct",
    "temperature_2m_max": "temp_max_c",
    "temperature_2m_min": "temp_min_c",
    "relative_humidity_2m_mean": "umid_pct",
    "wind_speed_10m_max": "vento_max_kmh",
    "wind_gusts_10m_max": "rajada_max_kmh",
    "et0_fao_evapotranspiration": "et0_mm",
    "shortwave_radiation_sum": "radiacao_mj_m2",
}
HORARIAS = {
    "temperature_2m": "temp_c",
    "relative_humidity_2m": "umid_pct",
    "dew_point_2m": "orvalho_c",
    "precipitation": "chuva_mm",
    "precipitation_probability": "prob_chuva_pct",
    "wind_speed_10m": "vento_kmh",
    "wind_gusts_10m": "rajada_kmh",
    "soil_temperature_0cm": "temp_solo_c",
}


def baixar(lat: float, lon: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    dados = get_json(
        URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join(DIARIAS),
            "hourly": ",".join(HORARIAS),
            "timezone": config.FUSO,
            "forecast_days": 16,
        },
    )
    diaria = pd.DataFrame(dados["daily"]).rename(columns={"time": "data", **DIARIAS})
    diaria["data"] = pd.to_datetime(diaria["data"]).dt.date
    horaria = pd.DataFrame(dados["hourly"]).rename(columns={"time": "ts_local", **HORARIAS})
    horaria["ts_local"] = pd.to_datetime(horaria["ts_local"])
    return diaria, horaria


RECENTES = {"precipitation_sum": "chuva_mm", "et0_fao_evapotranspiration": "et0_mm",
            "temperature_2m_max": "temp_max_c", "temperature_2m_min": "temp_min_c"}
DIAS_RECENTES = 45


def baixar_recente(lat: float, lon: float) -> pd.DataFrame:
    """Clima dos últimos dias (modelo Open-Meteo). Cobre o atraso da NASA POWER e do pacote do INMET
    no balanço hídrico das lavouras: sem isso, ficaria um buraco entre o último observado e a previsão."""
    dados = get_json(URL, params={"latitude": lat, "longitude": lon, "daily": ",".join(RECENTES),
                                  "timezone": config.FUSO, "past_days": DIAS_RECENTES, "forecast_days": 1})
    df = pd.DataFrame(dados["daily"]).rename(columns={"time": "data", **RECENTES})
    df["data"] = pd.to_datetime(df["data"]).dt.date
    return df[df["data"] < date.today()]


def executar(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    lat, lon = config.FAZENDA_LAT, config.FAZENDA_LON
    recente = baixar_recente(lat, lon)
    recente["carregado_em"] = datetime.now().replace(microsecond=0)
    substituir(con, "raw.clima_recente_diario", recente, "data >= ?", [recente["data"].min()])
    diaria, horaria = baixar(lat, lon)
    emitida_em = datetime.now().replace(microsecond=0)
    for df in (diaria, horaria):
        df.insert(0, "emitida_em", emitida_em)
        df.insert(1, "lat", lat)
        df.insert(2, "lon", lon)
    # Um retrato por dia: rodar de novo no mesmo dia substitui o anterior.
    filtro, params = "CAST(emitida_em AS DATE) = ? AND lat = ? AND lon = ?", [date.today(), lat, lon]
    return {
        "previsao_diaria": substituir(con, "raw.previsao_diaria", diaria, filtro, params),
        "previsao_horaria": substituir(con, "raw.previsao_horaria", horaria, filtro, params),
    }
