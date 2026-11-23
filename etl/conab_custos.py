"""ETL CONAB: custos de produção de referência (soja, milho verão e trigo).

Planilhas oficiais da CONAB, uma aba por localidade e ano, com o mesmo layout
("Custo de Produção - Resumo"). Usamos as praças mais parecidas com Itapeva:
* trigo: a própria Itapeva-SP (e Itaberá-SP), além de Ponta Grossa-PR;
* soja e milho verão: Ponta Grossa-PR (Campos Gerais, mesmo sistema de plantio direto
  e altitude parecida). A CONAB não tem praça de soja ou milho no Sudoeste Paulista.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd
import xlrd

from core import config
from core.db import substituir
from core.http import criar_sessao

log = logging.getLogger(__name__)

BASE = ("https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/custos-de-producao/"
        "arquivos-custo-de-producao/agricolas/")
PLANILHAS = {
    "soja": (BASE + "serie-historica-custos-soja-1997-a-2026.xls", ["Ponta Grossa-PR"]),
    "milho": (BASE + "milho/milho_1a_safra_serie_historica_1997-2026.xls/@@download/file", ["Ponta Grossa-PR"]),
    "trigo": (BASE + "seriehistoricacustostrigo1998a2025.xls", ["Itapeva-SP", "Itaber", "Ponta Grossa-PR"]),
}
DIR_CONAB = config.DIR_RAW / "conab"

# Número do item na planilha CONAB → categoria de custo do SafraViva (a mesma usada no caderno de campo).
CATEGORIA_ITEM = {
    "3.1": "maquinas", "3.2": "maquinas", "4": "servicos", "6": "mao_obra", "7": "mao_obra",
    "8": "semente", "9": "fertilizante", "10": "defensivo", "12.1": "outros", "12.2": "outros",
    "12.3": "outros", "13": "servicos", "14": "frete", "15": "outros", "16": "armazenagem",
    "17": "armazenagem", "18": "seguro", "19": "seguro", "20": "assistencia_tecnica", "21": "outros",
    "22": "outros", "23": "impostos", "24": "juros", "25": "depreciacao", "26": "depreciacao",
    "27": "depreciacao", "28": "manutencao", "29": "mao_obra", "30": "seguro", "31": "arrendamento",
    "32": "renda_fatores", "33": "renda_fatores",
}
TOTAIS = {
    "CUSTO VARI": "custo_variavel",
    "CUSTO OPERACIONAL": "custo_operacional",
    "CUSTO TOTAL": "custo_total",
}
RE_ITEM = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*-\s*(.+?)\s*:?\s*$")
MESES = {m: i for i, m in enumerate(
    ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
     "setembro", "outubro", "novembro", "dezembro"], start=1)}


def baixar(cultura: str, forcar: bool = False) -> Path:
    destino = DIR_CONAB / f"{cultura}.xls"
    if forcar or not destino.exists():
        url, _ = PLANILHAS[cultura]
        resp = criar_sessao().get(url, timeout=(10, 300))
        resp.raise_for_status()
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(resp.content)
    return destino


def _num(valor) -> float | None:
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def ler_aba(planilha: xlrd.sheet.Sheet) -> tuple[dict, list[dict]]:
    """Lê o cabeçalho (tecnologia, safra, mês de referência, produtividade) e as linhas de custo."""
    celula = lambda r, c=0: str(planilha.cell_value(r, c)).strip() if r < planilha.nrows else ""  # noqa: E731
    cabecalho = " | ".join(celula(r) for r in range(0, 6))
    mes = re.search(r"M.s/Ano:\s*([A-Za-zçÇ]+)/(\d{4})", cabecalho)
    prod = re.search(r"Produtividade M.dia:\s*([\d.,]+)\s*kg", cabecalho)
    meta = {
        "tecnologia": celula(1),
        "safra_texto": celula(2),
        "mes_referencia": (datetime(int(mes[2]), MESES.get(mes[1].lower(), 1), 1).date() if mes else None),
        "produtividade_kg_ha": _num(prod[1]) if prod else None,
    }
    linhas = []
    for r in range(planilha.nrows):
        rotulo = celula(r)
        por_ha, por_sc = _num(planilha.cell_value(r, 1)), _num(planilha.cell_value(r, 2)) if planilha.ncols > 2 else None
        if por_ha is None:
            continue
        total = next((v for k, v in TOTAIS.items() if rotulo.upper().startswith(k)), None)
        if total:
            linhas.append({"item": total, "descricao": rotulo, "categoria": total, "valor_ha": por_ha, "valor_sc": por_sc})
            continue
        achado = RE_ITEM.match(rotulo.replace("\t", " "))
        if achado and achado[1] in CATEGORIA_ITEM:
            linhas.append({"item": achado[1], "descricao": achado[2], "categoria": CATEGORIA_ITEM[achado[1]],
                           "valor_ha": por_ha, "valor_sc": por_sc})
    return meta, linhas


def ler_planilha(caminho: Path, cultura: str, praças: list[str]) -> pd.DataFrame:
    livro = xlrd.open_workbook(str(caminho), on_demand=True)
    registros = []
    for aba in livro.sheet_names():
        if not any(p in aba for p in praças) or aba.startswith("OGM"):
            continue
        meta, linhas = ler_aba(livro.sheet_by_name(aba))
        local = re.sub(r"-\d{4}(-\d{2})?$", "", aba)
        for linha in linhas:
            registros.append({"cultura": cultura, "aba": aba, "local": local, **meta, **linha})
    return pd.DataFrame(registros)


def executar(con: duckdb.DuckDBPyConnection, forcar: bool = False) -> dict[str, int]:
    partes = []
    for cultura, (_, praças) in PLANILHAS.items():
        df = ler_planilha(baixar(cultura, forcar), cultura, praças)
        log.info("CONAB %s: %d linhas de %d abas", cultura, len(df), df["aba"].nunique() if len(df) else 0)
        partes.append(df)
    df = pd.concat(partes, ignore_index=True)
    df["carregado_em"] = datetime.now()
    return {"conab_custo": substituir(con, "raw.conab_custo", df)}
