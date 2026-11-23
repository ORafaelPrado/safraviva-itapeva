"""ETL IBGE: geografia dos municípios e Produção Agrícola Municipal (PAM/SIDRA 1612).

Níveis carregados: municípios da região, SP, PR (estado vizinho, para comparação) e Brasil.
"""

from __future__ import annotations

import logging
from datetime import datetime

import duckdb
import pandas as pd

from core import config
from core.db import substituir
from core.http import criar_sessao, get_json

log = logging.getLogger(__name__)

URL_MALHAS = "https://servicodados.ibge.gov.br/api/v3/malhas/municipios/{codigo}/metadados"
URL_SIDRA = "https://apisidra.ibge.gov.br/values/t/1612/{nivel}/v/{variavel}/p/all/c81/{culturas}"

# Recortes territoriais no formato da API SIDRA.
NIVEIS = {
    "municipio": "n6/" + ",".join(str(m.codigo_ibge) for m in config.MUNICIPIOS),
    "uf": "n3/35,41",  # São Paulo e Paraná
    "brasil": "n1/all",
}

# Convenções do SIDRA: "-" é zero absoluto; "..", "..." e "X" são ausência de dado.
SIDRA_ZERO = {"-"}
SIDRA_NULO = {"..", "...", "X", ""}


def valor_sidra(bruto: str) -> float | None:
    """Converte o valor textual do SIDRA em número respeitando as convenções do IBGE."""
    bruto = (bruto or "").strip()
    if bruto in SIDRA_ZERO:
        return 0.0
    if bruto in SIDRA_NULO:
        return None
    return float(bruto)


def parse_sidra(resposta: list[dict], nivel: str) -> pd.DataFrame:
    """Transforma a resposta JSON do SIDRA (1ª linha = cabeçalho) em DataFrame tipado."""
    cabecalho, linhas = resposta[0], resposta[1:]
    chave = {texto: cod for cod, texto in cabecalho.items()}

    def campo(prefixo: str) -> str:
        return next(cod for texto, cod in chave.items() if texto.startswith(prefixo))

    k_local = campo("Município (Código)" if nivel == "municipio" else "Unidade da Federação (Código)" if nivel == "uf" else "Brasil (Código)")
    k_nome = k_local.replace("C", "N")
    k_var, k_ano = campo("Variável (Código)"), campo("Ano (Código)")
    k_cult = campo("Produto das lavouras")

    return pd.DataFrame(
        {
            "nivel": nivel,
            "codigo_local": [int(r[k_local]) for r in linhas],
            "nome_local": [r[k_nome] for r in linhas],
            "variavel_codigo": [int(r[k_var]) for r in linhas],
            "ano": [int(r[k_ano]) for r in linhas],
            "cultura_codigo": [int(r[k_cult]) for r in linhas],
            "valor_bruto": [r["V"] for r in linhas],
            "valor": [valor_sidra(r["V"]) for r in linhas],
        }
    )


def carregar_geografia(con: duckdb.DuckDBPyConnection) -> int:
    """Preenche centroide e área de cada município a partir da API de malhas do IBGE."""
    sessao = criar_sessao()
    for m in config.MUNICIPIOS:
        meta = get_json(URL_MALHAS.format(codigo=m.codigo_ibge), sessao=sessao)[0]
        con.execute(
            "UPDATE analytics.dim_municipio SET lat = ?, lon = ?, area_km2 = ? WHERE codigo_ibge = ?",
            [
                meta["centroide"]["latitude"],
                meta["centroide"]["longitude"],
                float(meta["area"]["dimensao"]),
                m.codigo_ibge,
            ],
        )
    return len(config.MUNICIPIOS)


def carregar_pam(con: duckdb.DuckDBPyConnection) -> int:
    """Baixa a série completa da PAM (1974→) e substitui raw.sidra_pam."""
    sessao = criar_sessao()
    culturas = ",".join(str(c.codigo_sidra) for c in config.CULTURAS)
    partes = []
    for nivel, recorte in NIVEIS.items():
        for variavel in config.SIDRA_VARIAVEIS:
            url = URL_SIDRA.format(nivel=recorte, variavel=variavel, culturas=culturas)
            partes.append(parse_sidra(get_json(url, sessao=sessao), nivel))
            log.info("SIDRA %s v%s: %d linhas", nivel, variavel, len(partes[-1]))
    df = pd.concat(partes, ignore_index=True)
    df["carregado_em"] = datetime.now()
    return substituir(con, "raw.sidra_pam", df)


def executar(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    return {"municipios_geo": carregar_geografia(con), "sidra_pam": carregar_pam(con)}
