"""Health check das fontes de dados do SafraViva.

Faz uma chamada real e pequena a cada fonte e confere se a resposta tem o
conteúdo esperado para Itapeva. Rode sempre que um ETL falhar:

    python -m scripts.validar_fontes
"""

from __future__ import annotations

import sys
import time
from datetime import date, timedelta
from typing import Callable

from core import config
from core.http import TIMEOUT_PADRAO, criar_sessao, get_json

SESSAO = criar_sessao()
LAT, LON = config.FAZENDA_LAT, config.FAZENDA_LON


def checar_ibge_localidades() -> str:
    dados = get_json("https://servicodados.ibge.gov.br/api/v1/localidades/estados/SP/municipios", sessao=SESSAO)
    codigos = {m["id"] for m in dados}
    faltando = [m.nome for m in config.MUNICIPIOS if m.codigo_ibge not in codigos]
    assert not faltando, f"códigos IBGE não encontrados: {faltando}"
    return f"{len(config.MUNICIPIOS)} municípios da região conferidos"


def checar_sidra_pam() -> str:
    url = (
        f"https://apisidra.ibge.gov.br/values/t/1612/n6/{config.CODIGO_ITAPEVA}"
        "/v/112/p/all/c81/2713/h/n"
    )
    serie = get_json(url, sessao=SESSAO)
    assert len(serie) > 40, "série histórica curta demais"
    ini, fim = serie[0], serie[-1]
    return f"soja Itapeva {ini['D3N']}–{fim['D3N']} ({len(serie)} anos); último rendimento {fim['V']} kg/ha"


def checar_inmet_catalogo() -> str:
    estacoes = get_json("https://apitempo.inmet.gov.br/estacoes/T", sessao=SESSAO)
    a714 = next(e for e in estacoes if e["CD_ESTACAO"] == "A714")
    assert a714["CD_SITUACAO"] == "Operante", f"A714 em situação {a714['CD_SITUACAO']}"
    return f"A714 {a714['DC_NOME']} operante desde {a714['DT_INICIO_OPERACAO'][:10]}"


def checar_inmet_bdmep() -> str:
    ano = date.today().year - 1
    resp = SESSAO.head(
        f"https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip", timeout=TIMEOUT_PADRAO
    )
    resp.raise_for_status()
    mb = int(resp.headers.get("Content-Length", 0)) / 1e6
    return f"pacote anual {ano}.zip disponível ({mb:.0f} MB, todas as estações)"


def checar_nasa_power() -> str:
    fim = date.today() - timedelta(days=10)
    ini = fim - timedelta(days=4)
    dados = get_json(
        "https://power.larc.nasa.gov/api/temporal/daily/point",
        params={
            "parameters": "PRECTOTCORR,T2M_MAX,T2M_MIN",
            "community": "AG",
            "latitude": LAT,
            "longitude": LON,
            "start": ini.strftime("%Y%m%d"),
            "end": fim.strftime("%Y%m%d"),
            "format": "JSON",
        },
        sessao=SESSAO,
    )
    chuva = dados["properties"]["parameter"]["PRECTOTCORR"]
    return f"{len(chuva)} dias retornados; chuva {sum(v for v in chuva.values() if v >= 0):.1f} mm"


def checar_open_meteo_previsao() -> str:
    dados = get_json(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": LAT,
            "longitude": LON,
            "daily": "precipitation_sum,temperature_2m_min",
            "timezone": config.FUSO,
            "forecast_days": 16,
        },
        sessao=SESSAO,
    )
    d = dados["daily"]
    return (
        f"16 dias: chuva prevista {sum(x or 0 for x in d['precipitation_sum']):.0f} mm, "
        f"mínima {min(x for x in d['temperature_2m_min'] if x is not None):.1f} °C"
    )


def checar_open_meteo_historico() -> str:
    # Geada de 30/06/2021, que atingiu o milho safrinha do Sudoeste Paulista.
    dados = get_json(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": LAT,
            "longitude": LON,
            "start_date": "2021-06-28",
            "end_date": "2021-07-02",
            "daily": "temperature_2m_min",
            "timezone": config.FUSO,
        },
        sessao=SESSAO,
    )
    return f"mínima na onda de frio de jun/2021: {min(dados['daily']['temperature_2m_min'])} °C"


def checar_zarc() -> str:
    dados = get_json(
        "https://dados.agricultura.gov.br/api/3/action/package_show",
        params={"id": "tabua-de-risco-zoneamento-agricola-de-risco-climatico"},
        sessao=SESSAO,
    )
    safras = [r["name"] for r in dados["result"]["resources"] if "Safra 20" in r["name"]]
    return f"{len(safras)} tábuas de risco; mais recente: {sorted(safras)[-1]}"


def checar_cepea() -> str:
    resp = SESSAO.get("https://www.cepea.org.br/br/indicador/soja.aspx", timeout=TIMEOUT_PADRAO)
    resp.raise_for_status()
    assert "soja" in resp.text.lower()
    return f"página do indicador acessível ({len(resp.content) // 1000} kB); exige raspagem/planilha"


CHECAGENS: dict[str, Callable[[], str]] = {
    "IBGE Localidades": checar_ibge_localidades,
    "IBGE SIDRA / PAM": checar_sidra_pam,
    "INMET catálogo": checar_inmet_catalogo,
    "INMET BDMEP (zip)": checar_inmet_bdmep,
    "NASA POWER": checar_nasa_power,
    "Open-Meteo previsão": checar_open_meteo_previsao,
    "Open-Meteo histórico": checar_open_meteo_historico,
    "MAPA ZARC": checar_zarc,
    "CEPEA": checar_cepea,
}


def main() -> int:
    falhas = 0
    print(f"{'FONTE':<22} {'OK':<3} {'TEMPO':>6}  DETALHE")
    for nome, checar in CHECAGENS.items():
        t0 = time.perf_counter()
        try:
            detalhe, ok = checar(), "✔"
        except Exception as erro:  # noqa: BLE001 — health check reporta qualquer falha
            detalhe, ok = f"{type(erro).__name__}: {erro}"[:140], "✘"
            falhas += 1
        print(f"{nome:<22} {ok:<3} {time.perf_counter() - t0:5.1f}s  {detalhe}")
    print(f"\n{len(CHECAGENS) - falhas}/{len(CHECAGENS)} fontes OK")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
