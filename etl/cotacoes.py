"""ETL de cotações: CEPEA (físico, diário), CBOT (bolsa de Chicago, intradiário) e dólar.

Fontes e o que cada uma é:
* CEPEA/ESALQ, preço do físico no Brasil, um valor por dia útil (publicado à tarde). Séries completas
  em planilha desde 2006. Licença CC BY-NC 4.0: uso não comercial, citando o Cepea.
* CBOT, contratos futuros de Chicago (soja ZS, milho ZC, trigo ZW), em centavos de dólar por bushel,
  com ~10–15 min de atraso, via endpoint público do Yahoo Finance (não oficial: pode mudar sem aviso).
* Dólar: comercial ao vivo (Yahoo, BRL=X) e PTAX oficial do Banco Central (API Olinda).

O que é "tempo real" aqui: a bolsa e o dólar se mexem durante o dia; o CEPEA é diário.
A conversão CBOT → R$/saca não inclui prêmio de porto, frete nem impostos ("paridade Chicago").
"""

from __future__ import annotations

import io
import logging
import re
from datetime import date, datetime, timedelta

import duckdb
import pandas as pd
import xlrd

from core.db import substituir
from core.http import TIMEOUT_PADRAO, criar_sessao, get_json

log = logging.getLogger(__name__)

URL_CEPEA = "https://www.cepea.org.br/br/indicador/series/{produto}.aspx?id={id}"
URL_YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{simbolo}"
URL_PTAX = ("https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
            "CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)")

KG_POR_BUSHEL = {"soja": 27.2155, "milho": 25.4012, "trigo": 27.2155}

# serie: (produto CEPEA na URL, id, cultura, nome, unidade original)
SERIES_CEPEA = {
    "cepea_soja_paranagua": ("soja", 92, "soja", "Soja CEPEA/ESALQ · Paranaguá (porto)", "R$/sc"),
    "cepea_soja_parana": ("soja", 12, "soja", "Soja CEPEA/ESALQ · Paraná", "R$/sc"),
    "cepea_milho": ("milho", 77, "milho", "Milho ESALQ/B3 · Campinas", "R$/sc"),
    "cepea_trigo_parana": ("trigo", 178, "trigo", "Trigo CEPEA/ESALQ · Paraná", "R$/t"),
}
# serie: (símbolo Yahoo, cultura, nome)
SERIES_BOLSA = {
    "cbot_soja": ("ZS=F", "soja", "Soja CBOT (Chicago)"),
    "cbot_milho": ("ZC=F", "milho", "Milho CBOT (Chicago)"),
    "cbot_trigo": ("ZW=F", "trigo", "Trigo CBOT (Chicago)"),
    "dolar": ("BRL=X", "dolar", "Dólar comercial"),
}
# Qual série CEPEA vira o preço de referência da fazenda (quando ele não foi digitado à mão)
REFERENCIA_FAZENDA = {"soja": "cepea_soja_parana", "milho": "cepea_milho", "trigo": "cepea_trigo_parana"}


def rs_por_saca_cbot(centavos_por_bushel: float, cultura: str, dolar: float) -> float:
    """Contrato de Chicago (US¢/bushel) → R$ por saca de 60 kg, sem prêmio, frete ou impostos."""
    return centavos_por_bushel / 100 * (60 / KG_POR_BUSHEL[cultura]) * dolar


# ----------------------------------------------------------------------------------------------
# CEPEA
# ----------------------------------------------------------------------------------------------

def ler_planilha_cepea(conteudo: bytes, unidade: str) -> pd.DataFrame:
    """Planilha de série do CEPEA → data, valor (unidade original), valor_usd, valor_rs_sc."""
    livro = xlrd.open_workbook(file_contents=conteudo, ignore_workbook_corruption=True)
    folha = livro.sheet_by_index(0)
    linhas = []
    for r in range(folha.nrows):
        texto = str(folha.cell_value(r, 0)).strip()
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", texto):
            continue
        valor = folha.cell_value(r, 1)
        usd = folha.cell_value(r, 2) if folha.ncols > 2 else None
        if isinstance(valor, (int, float)):
            linhas.append((datetime.strptime(texto, "%d/%m/%Y").date(), float(valor),
                           float(usd) if isinstance(usd, (int, float)) else None))
    df = pd.DataFrame(linhas, columns=["data", "valor", "valor_usd"])
    df["valor_rs_sc"] = df["valor"] * 60 / 1000 if unidade == "R$/t" else df["valor"]
    return df


def baixar_cepea(sessao=None) -> pd.DataFrame:
    sessao = sessao or criar_sessao()
    partes = []
    for serie, (produto, id_, cultura, nome, unidade) in SERIES_CEPEA.items():
        resp = sessao.get(URL_CEPEA.format(produto=produto, id=id_), timeout=TIMEOUT_PADRAO)
        resp.raise_for_status()
        df = ler_planilha_cepea(resp.content, unidade)
        df.insert(0, "serie", serie)
        df.insert(1, "cultura", cultura)
        df["nome"], df["unidade"], df["fonte"] = nome, unidade, "CEPEA/ESALQ (CC BY-NC 4.0)"
        partes.append(df)
        log.info("CEPEA %s: %d dias (%s → %s)", serie, len(df), df["data"].min(), df["data"].max())
    return pd.concat(partes, ignore_index=True)


# ----------------------------------------------------------------------------------------------
# Bolsa (CBOT) e dólar
# ----------------------------------------------------------------------------------------------

def _yahoo(simbolo: str, intervalo: str, periodo: str, sessao=None) -> dict:
    dados = get_json(URL_YAHOO.format(simbolo=simbolo), params={"interval": intervalo, "range": periodo},
                     sessao=sessao)
    return dados["chart"]["result"][0]


def _serie_yahoo(bruto: dict) -> pd.DataFrame:
    df = pd.DataFrame({"ts": pd.to_datetime(bruto.get("timestamp", []), unit="s", utc=True),
                       "valor": bruto["indicators"]["quote"][0]["close"]}).dropna()
    df["ts"] = df["ts"].dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)
    return df


def baixar_bolsa(sessao=None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(diário 2 anos, intradiário do último pregão, último preço) para CBOT e dólar."""
    sessao = sessao or criar_sessao()
    diarios, intradia, ultimos = [], [], []
    for serie, (simbolo, cultura, nome) in SERIES_BOLSA.items():
        d = _yahoo(simbolo, "1d", "2y", sessao)
        df = _serie_yahoo(d).assign(data=lambda x: x["ts"].dt.date).drop_duplicates("data", keep="last")
        df = df.assign(serie=serie, cultura=cultura, nome=nome)
        diarios.append(df[["serie", "cultura", "nome", "data", "valor"]])
        i = _yahoo(simbolo, "15m" if serie != "dolar" else "5m", "1d", sessao)
        intradia.append(_serie_yahoo(i).assign(serie=serie))
        meta = i["meta"]
        anterior = meta.get("chartPreviousClose") or meta.get("previousClose")
        ultimos.append({
            "serie": serie, "cultura": cultura, "nome": nome, "simbolo": simbolo,
            "preco": meta["regularMarketPrice"], "fechamento_anterior": anterior,
            "variacao_pct": (meta["regularMarketPrice"] / anterior - 1) * 100 if anterior else None,
            "horario_mercado": pd.Timestamp(meta["regularMarketTime"], unit="s", tz="UTC")
            .tz_convert("America/Sao_Paulo").tz_localize(None),
            "unidade": "R$/US$" if serie == "dolar" else "US¢/bushel",
        })
    return pd.concat(diarios, ignore_index=True), pd.concat(intradia, ignore_index=True), pd.DataFrame(ultimos)


def baixar_ptax(dias: int = 760, sessao=None) -> pd.DataFrame:
    fim, inicio = date.today(), date.today() - timedelta(days=dias)
    dados = get_json(URL_PTAX + f"?@dataInicial='{inicio:%m-%d-%Y}'&@dataFinalCotacao='{fim:%m-%d-%Y}'&$format=json",
                     sessao=sessao)
    df = pd.DataFrame(dados["value"])
    df["data"] = pd.to_datetime(df["dataHoraCotacao"]).dt.date
    return df.groupby("data", as_index=False)["cotacaoVenda"].last().rename(columns={"cotacaoVenda": "valor"})


def converter_cbot(diario: pd.DataFrame, ultimos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Acrescenta R$/saca às séries CBOT usando o dólar do mesmo dia (ou o último anterior)."""
    dolar = diario[diario["serie"] == "dolar"][["data", "valor"]].rename(columns={"valor": "dolar"})
    dolar = dolar.assign(dia=pd.to_datetime(dolar["data"])).drop(columns="data").sort_values("dia")
    saida = []
    for serie, g in diario.groupby("serie"):
        g = g.sort_values("data").copy()
        if serie == "dolar":
            g["valor_rs_sc"], g["unidade"] = None, "R$/US$"
        else:
            g = pd.merge_asof(g.assign(dia=pd.to_datetime(g["data"])), dolar, on="dia").drop(columns="dia")
            g["valor_rs_sc"] = [rs_por_saca_cbot(v, c, d) for v, c, d in zip(g["valor"], g["cultura"], g["dolar"])]
            g["unidade"] = "US¢/bushel"
            g = g.drop(columns=["dolar"])
        saida.append(g)
    diario = pd.concat(saida, ignore_index=True)
    dolar_agora = float(ultimos.loc[ultimos["serie"] == "dolar", "preco"].iloc[0])
    ultimos = ultimos.copy()
    ultimos["preco_rs_sc"] = [None if s == "dolar" else rs_por_saca_cbot(p, c, dolar_agora)
                              for s, p, c in zip(ultimos["serie"], ultimos["preco"], ultimos["cultura"])]
    return diario, ultimos


# ----------------------------------------------------------------------------------------------
# Carga
# ----------------------------------------------------------------------------------------------

def atualizar_preco_referencia(con: duckdb.DuckDBPyConnection) -> int:
    """Preço de referência da fazenda = último CEPEA, a menos que o produtor tenha digitado o seu.

    Só substitui preços cuja fonte é automática (Cepea) ou uma das referências de partida do projeto.
    """
    atualizados = 0
    for cultura, serie in REFERENCIA_FAZENDA.items():
        ultimo = con.execute("""SELECT data, valor_rs_sc, nome FROM raw.cotacao_diaria
                                WHERE serie = ? ORDER BY data DESC LIMIT 1""", [serie]).fetchone()
        if not ultimo:
            continue
        atual = con.execute("SELECT fonte FROM fazenda.preco_referencia WHERE cultura = ?", [cultura]).fetchone()
        automatico = atual is None or atual[0].startswith(("Cepea", "Média de cooperativas", "Deral"))
        if automatico:
            con.execute("INSERT OR REPLACE INTO fazenda.preco_referencia VALUES (?, ?, ?, ?)",
                        [cultura, round(ultimo[1], 2), ultimo[0], f"Cepea/Esalq: {ultimo[2]} (automático)"])
            atualizados += 1
    return atualizados


def executar_rapido(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Só bolsa e dólar (intradiário + último preço): para atualizar a tela a cada 15 min."""
    sessao = criar_sessao()
    diario, intradia, ultimos = baixar_bolsa(sessao)
    diario, ultimos = converter_cbot(diario, ultimos)
    agora = datetime.now().replace(microsecond=0)
    for df in (diario, intradia, ultimos):
        df["carregado_em"] = agora
    diario["fonte"] = "CBOT/Yahoo Finance (atraso ~15 min)"
    return {
        "bolsa_diario": substituir(con, "raw.cotacao_diaria", diario, "serie IN (SELECT unnest(?))",
                                   [list(SERIES_BOLSA)]),
        "bolsa_intradia": substituir(con, "raw.cotacao_intradia", intradia),
        "bolsa_ultimo": substituir(con, "raw.cotacao_ultima", ultimos),
    }


def executar(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Carga completa: CEPEA (séries desde 2006), PTAX, bolsa e dólar; atualiza o preço de referência."""
    sessao = criar_sessao()
    cepea = baixar_cepea(sessao)
    cepea["carregado_em"] = datetime.now().replace(microsecond=0)
    resumo = {"cepea": substituir(con, "raw.cotacao_diaria", cepea, "serie IN (SELECT unnest(?))",
                                  [list(SERIES_CEPEA)])}
    ptax = baixar_ptax(sessao=sessao).assign(serie="dolar_ptax", cultura="dolar", nome="Dólar PTAX (Banco Central)",
                                             unidade="R$/US$", fonte="Banco Central (PTAX venda)",
                                             carregado_em=datetime.now().replace(microsecond=0))
    resumo["ptax"] = substituir(con, "raw.cotacao_diaria", ptax, "serie = 'dolar_ptax'")
    resumo.update(executar_rapido(con))
    resumo["preco_referencia"] = atualizar_preco_referencia(con)
    return resumo
