"""ETL INMET BDMEP: série horária das estações automáticas da região (2006→).

O INMET publica um .zip anual (~90 MB) com todas as estações do país. Baixamos
em streaming, extraímos só as estações de interesse e apagamos o .zip.
Os anos fechados ficam em cache em data/raw/inmet/{ano}/; o ano corrente é
sempre baixado de novo, porque o INMET atualiza o pacote durante o ano.
"""

from __future__ import annotations

import io
import logging
import zipfile
from datetime import date, datetime
from pathlib import Path

import duckdb
import pandas as pd

from core import config
from core.db import substituir
from core.http import criar_sessao

log = logging.getLogger(__name__)

URL_ANO = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip"
DIR_INMET = config.DIR_RAW / "inmet"
ANO_INICIAL = 2006  # A714 entrou em operação em jul/2006

# As 19 colunas do CSV têm ordem fixa em todos os anos; só os nomes e os formatos
# de data/hora mudaram (2019+: "2025/01/01" e "0000 UTC"; antes: "2006-07-25" e "00:00").
COLUNAS = [
    "data", "hora", "chuva_mm", "pressao_mb", "pressao_max_mb", "pressao_min_mb",
    "radiacao_kj_m2", "temp_c", "orvalho_c", "temp_max_c", "temp_min_c",
    "orvalho_max_c", "orvalho_min_c", "umid_max_pct", "umid_min_pct", "umid_pct",
    "vento_dir_graus", "rajada_ms", "vento_ms",
]
VALOR_AUSENTE = -9999


def arquivo_local(ano: int, estacao: str) -> Path:
    return DIR_INMET / str(ano) / f"{estacao}.csv"


def baixar_ano(ano: int, estacoes: list[str], forcar: bool = False) -> list[Path]:
    """Baixa o pacote do ano e extrai os CSVs das estações. Devolve os arquivos disponíveis."""
    alvos = {e: arquivo_local(ano, e) for e in estacoes}
    if not forcar and all(p.exists() for p in alvos.values()):
        return list(alvos.values())

    log.info("INMET: baixando pacote %s", ano)
    resp = criar_sessao().get(URL_ANO.format(ano=ano), timeout=(10, 600))
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as pacote:
        for nome in pacote.namelist():
            for estacao, destino in alvos.items():
                if f"_{estacao}_" in nome.upper():
                    destino.parent.mkdir(parents=True, exist_ok=True)
                    destino.write_bytes(pacote.read(nome))
    return [p for p in alvos.values() if p.exists()]


def ler_csv(caminho: Path | io.BytesIO, estacao: str) -> pd.DataFrame:
    """Lê um CSV horário do BDMEP e devolve colunas padronizadas com timestamp UTC."""
    df = pd.read_csv(
        caminho,
        sep=";",
        decimal=",",
        encoding="latin-1",
        skiprows=8,
        header=0,
        usecols=range(len(COLUNAS)),
        names=COLUNAS,
        dtype={"data": str, "hora": str},
        na_values=[VALOR_AUSENTE, str(VALOR_AUSENTE), "-9999,0"],
    )
    hora = df["hora"].str.replace(r"\D", "", regex=True).str[:2]
    df.insert(
        0, "ts_utc", pd.to_datetime(df["data"].str.replace("/", "-") + " " + hora + ":00", format="%Y-%m-%d %H:%M")
    )
    df = df.drop(columns=["data", "hora"])
    numericas = df.columns.drop("ts_utc")
    df[numericas] = df[numericas].apply(pd.to_numeric, errors="coerce")
    df.insert(0, "estacao", estacao)
    return df


def executar(
    con: duckdb.DuckDBPyConnection, anos: range | None = None, estacoes: list[str] | None = None
) -> dict[str, int]:
    estacoes = estacoes or [e.codigo for e in config.ESTACOES_INMET]
    ano_atual = date.today().year
    anos = anos or range(ANO_INICIAL, ano_atual + 1)
    total = 0
    for ano in anos:
        try:
            arquivos = baixar_ano(ano, estacoes, forcar=(ano == ano_atual))
        except Exception as erro:  # noqa: BLE001 — um ano indisponível não derruba a carga
            log.warning("INMET %s indisponível: %s", ano, erro)
            continue
        for arquivo in arquivos:
            df = ler_csv(arquivo, arquivo.stem)
            df["carregado_em"] = datetime.now()
            total += substituir(
                con,
                "raw.inmet_horario",
                df,
                onde="estacao = ? AND year(ts_utc) = ?",
                params=[arquivo.stem, ano],
            )
        log.info("INMET %s: %d estações", ano, len(arquivos))
    return {"inmet_horario": total}
