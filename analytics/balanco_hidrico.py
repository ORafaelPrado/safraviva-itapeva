"""Balanço hídrico da cultura e estimativa de produtividade (FAO-56 + FAO-33).

Para cada dia desde o plantio:
    ETc = Kc(fase) × ETo
    Ks  = 1 se a falta de água no solo (Dr) ≤ RAW, senão (TAW − Dr) / (TAW − RAW)   [FAO-56, eq. 84]
    ETa = Ks × ETc
    Dr  = limitado a [0, TAW] de Dr − chuva + ETa       (o excesso de chuva drena)
Por fase:  1 − Ya/Ym = Ky × (1 − ΣETa / ΣETc)                                 [FAO-33]
Produtividade = meta × Π (1 − Ky_f × (1 − ETa_f / ETc_f))  (fases combinadas multiplicativamente)

O clima vem de três fontes, nesta ordem:
1. observado: série de Itapeva (estação A714 + NASA POWER calibrada), até o último dia disponível;
2. previsão: Open-Meteo, 16 dias (ETo FAO Penman-Monteith do próprio Open-Meteo);
3. o restante do ciclo: **anos análogos**. O resto da safra é simulado com o clima de cada ano desde
   1991, o que gera uma distribuição. Daí saem os percentis p10 (ano ruim), p50 (provável) e p90 (ano bom).

Simplificações (documentadas em docs/decisoes.md): raiz e TAW constantes; solo começa na capacidade de
campo no plantio; chuva efetiva = chuva; sem irrigação; considera só a água, sem doença, geada, praga ou
nutrição. Ou seja, mede o **risco hídrico**, não prevê tudo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

import duckdb
import numpy as np
import pandas as pd

from core import config

# Água disponível total na zona de raízes (mm) por classe do ZARC. Aproximação: AD1 = solo arenoso e raso,
# AD6 = argiloso profundo. Ajustar com a análise de solo do talhão quando houver.
TAW_POR_AD = {"AD1": 40.0, "AD2": 60.0, "AD3": 80.0, "AD4": 100.0, "AD5": 120.0, "AD6": 140.0}
P_DEPLECAO = 0.5  # fração da água que a planta tira sem estresse (FAO-56, tab. 22: soja 0,5; milho 0,55; trigo 0,55)

# Kc inicial, médio e final (FAO-56, tabela 12)
KC = {"soja": (0.40, 1.15, 0.50), "milho": (0.30, 1.20, 0.60), "trigo": (0.40, 1.15, 0.40),
      "feijao": (0.40, 1.15, 0.35)}
# Ky por grupo de fase (FAO-33, tabela 24)
KY = {
    "soja": {"vegetativo": 0.2, "florescimento": 0.8, "enchimento": 1.0, "maturacao": 0.1},
    "milho": {"vegetativo": 0.4, "florescimento": 1.5, "enchimento": 0.5, "maturacao": 0.2},
    "trigo": {"vegetativo": 0.2, "florescimento": 0.6, "enchimento": 0.5, "maturacao": 0.1},
    "feijao": {"vegetativo": 0.2, "florescimento": 1.1, "enchimento": 0.75, "maturacao": 0.2},
}
GRUPO_FASE = {"emergência": "vegetativo", "vegetativo": "vegetativo", "perfilhamento": "vegetativo",
              "florescimento": "florescimento", "enchimento": "enchimento", "maturação": "maturacao"}
ANO_ANALOGO_INICIAL = 1991

# Quanto a estimativa merece confiança, pelo backtest (docs/backtest_balanco.md, 23/11/2026).
# usar_em_alertas = False: a estimativa aparece com o aviso, mas não gera alerta de produtividade.
CONFIABILIDADE = {
    "soja": ("moderada", True, "No backtest de Itapeva, o modelo acompanhou as safras boas e ruins de soja "
                               "(r = 0,32) e marcou 2 das 3 quebras do IBGE entre os 25% piores anos."),
    "milho": ("baixa a moderada", True, "No backtest regional do milho verão, r = 0,21: indica o risco hídrico, "
                                        "mas erra com frequência."),
    "feijao": ("não avaliada", False, "Sem backtest para o feijão: use como indicação do estresse hídrico."),
    "trigo": ("baixa", False, "O trigo quebra mais por geada e chuva na colheita do que por falta de água "
                              "(r ≈ 0 no backtest). Para o trigo, valem os alertas de geada e de chuva."),
}
LAT_ITAPEVA = -23.98


# ----------------------------------------------------------------------------------------------
# Clima
# ----------------------------------------------------------------------------------------------

def ra_extraterrestre(dia_do_ano: np.ndarray, lat_graus: float = LAT_ITAPEVA) -> np.ndarray:
    """Radiação extraterrestre Ra (MJ/m²/dia), FAO-56 eq. 21."""
    phi = math.radians(lat_graus)
    dr = 1 + 0.033 * np.cos(2 * np.pi * dia_do_ano / 365)
    delta = 0.409 * np.sin(2 * np.pi * dia_do_ano / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    return 24 * 60 / np.pi * 0.0820 * dr * (ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws))


def eto_diaria(df: pd.DataFrame) -> pd.Series:
    """ETo (mm/dia): Hargreaves com radiação medida quando houver; senão Hargreaves-Samani (só temperatura)."""
    tmed = df["temp_c"].fillna((df["temp_max_c"] + df["temp_min_c"]) / 2)
    com_rad = 0.0135 * (tmed + 17.8) * df["radiacao_mj_m2"] / 2.45
    ra = ra_extraterrestre(pd.to_datetime(df["data"]).dt.dayofyear.to_numpy())
    amplitude = (df["temp_max_c"] - df["temp_min_c"]).clip(lower=0)
    so_temp = 0.0023 * (tmed + 17.8) * np.sqrt(amplitude) * ra * 0.408
    return com_rad.fillna(so_temp).clip(lower=0)


def clima_observado(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    df = con.execute("""SELECT data, chuva_mm, temp_c, temp_max_c, temp_min_c, radiacao_mj_m2
                        FROM analytics.fato_clima_itapeva ORDER BY data""").df()
    df["data"] = pd.to_datetime(df["data"])
    df["eto_mm"] = eto_diaria(df)
    df["chuva_mm"] = df["chuva_mm"].fillna(0)
    return df.dropna(subset=["eto_mm"])[["data", "chuva_mm", "eto_mm"]]


def clima_recente(con: duckdb.DuckDBPyConnection, depois_de: pd.Timestamp) -> pd.DataFrame:
    """Últimos dias modelados pelo Open-Meteo (cobre o atraso da série observada)."""
    df = con.execute("SELECT data, chuva_mm, et0_mm AS eto_mm FROM raw.clima_recente_diario ORDER BY data").df()
    df["data"] = pd.to_datetime(df["data"])
    return df[df["data"] > depois_de].fillna({"chuva_mm": 0}).dropna(subset=["eto_mm"])


def climatologia(observado: pd.DataFrame, datas: pd.DatetimeIndex) -> pd.DataFrame:
    """Média 1991–hoje do mesmo dia do ano: último recurso para buracos no passado recente."""
    base = observado[observado["data"].dt.year >= ANO_ANALOGO_INICIAL].copy()
    base["doy"] = base["data"].dt.dayofyear.clip(upper=365)
    media = base.groupby("doy")[["chuva_mm", "eto_mm"]].mean()
    doy = datas.dayofyear.to_numpy().clip(max=365)
    return pd.DataFrame({"data": datas, "chuva_mm": media["chuva_mm"].reindex(doy).to_numpy(),
                         "eto_mm": media["eto_mm"].reindex(doy).to_numpy()})


def clima_previsto(con: duckdb.DuckDBPyConnection, depois_de: pd.Timestamp) -> pd.DataFrame:
    df = con.execute("SELECT data, chuva_mm, et0_mm AS eto_mm FROM analytics.vw_previsao_diaria_atual ORDER BY data").df()
    df["data"] = pd.to_datetime(df["data"])
    return df[df["data"] > depois_de].fillna({"chuva_mm": 0})


# ----------------------------------------------------------------------------------------------
# Fases e coeficientes
# ----------------------------------------------------------------------------------------------

def fases(con: duckdb.DuckDBPyConnection, cultura: str, temporada: str) -> pd.DataFrame:
    return con.execute("""SELECT fase, dia_inicio, dia_fim FROM analytics.dim_fase_duracao
                          WHERE cultura = ? AND temporada = ? ORDER BY ordem""", [cultura, temporada]).df()


def kc_por_dia(cultura: str, tabela_fases: pd.DataFrame) -> np.ndarray:
    """Curva de Kc dia a dia: inicial na emergência, sobe no vegetativo, plateau no florescimento/enchimento,
    desce na maturação (FAO-56, fig. 25)."""
    kc_ini, kc_med, kc_fim = KC[cultura]
    duracao = int(tabela_fases["dia_fim"].max()) + 1
    kc = np.full(duracao, kc_med)
    for f in tabela_fases.itertuples():
        dias = np.arange(int(f.dia_inicio), int(f.dia_fim) + 1)
        frac = (dias - f.dia_inicio) / max(f.dia_fim - f.dia_inicio, 1)
        grupo = GRUPO_FASE[f.fase]
        if f.fase == "emergência":
            kc[dias] = kc_ini
        elif grupo == "vegetativo":
            kc[dias] = kc_ini + (kc_med - kc_ini) * frac
        elif grupo == "maturacao":
            kc[dias] = kc_med + (kc_fim - kc_med) * frac
    return kc


# ----------------------------------------------------------------------------------------------
# Simulação
# ----------------------------------------------------------------------------------------------

@dataclass
class Simulacao:
    razao_produtividade: float       # Ya / Ym
    por_fase: pd.DataFrame           # fase, etc_mm, eta_mm, razao_eta_etc, ky, perda_pct
    diario: pd.DataFrame             # data, chuva_mm, etc_mm, eta_mm, armazenamento_pct, ks


def simular(clima: pd.DataFrame, plantio: date, cultura: str, tabela_fases: pd.DataFrame,
            taw_mm: float) -> Simulacao:
    """Roda o balanço do plantio até o fim do ciclo. `clima` precisa cobrir todos os dias do ciclo."""
    kc = kc_por_dia(cultura, tabela_fases)
    datas = pd.date_range(pd.Timestamp(plantio), periods=len(kc), freq="D")
    c = clima.set_index("data").reindex(datas)
    if c[["chuva_mm", "eto_mm"]].isna().any().any():
        faltando = c.index[c["eto_mm"].isna()]
        raise ValueError(f"Clima incompleto: faltam {len(faltando)} dias (ex.: {faltando[0]:%d/%m/%Y}).")
    raw = P_DEPLECAO * taw_mm
    dr, linhas = 0.0, []
    for i, (dia, chuva, eto) in enumerate(zip(datas, c["chuva_mm"].to_numpy(), c["eto_mm"].to_numpy())):
        etc = kc[i] * eto
        ks = 1.0 if dr <= raw else max(0.0, (taw_mm - dr) / (taw_mm - raw))
        eta = ks * etc
        dr = min(taw_mm, max(0.0, dr - chuva + eta))
        linhas.append((dia, chuva, etc, eta, 100 * (1 - dr / taw_mm), ks, i))
    diario = pd.DataFrame(linhas, columns=["data", "chuva_mm", "etc_mm", "eta_mm", "armazenamento_pct", "ks", "dia"])
    grupos = []
    for f in tabela_fases.itertuples():
        trecho = diario[(diario["dia"] >= f.dia_inicio) & (diario["dia"] <= f.dia_fim)]
        grupos.append((GRUPO_FASE[f.fase], f.fase, trecho["etc_mm"].sum(), trecho["eta_mm"].sum()))
    por_fase = pd.DataFrame(grupos, columns=["grupo", "fase", "etc_mm", "eta_mm"])
    agregado = por_fase.groupby("grupo", sort=False)[["etc_mm", "eta_mm"]].sum()
    razao = 1.0
    perdas = {}
    for grupo, linha in agregado.iterrows():
        relativo = linha["eta_mm"] / linha["etc_mm"] if linha["etc_mm"] > 0 else 1.0
        perda = KY[cultura][grupo] * (1 - relativo)
        perdas[grupo] = perda
        razao *= max(0.0, 1 - perda)
    por_fase["razao_eta_etc"] = por_fase["eta_mm"] / por_fase["etc_mm"]
    por_fase["ky"] = por_fase["grupo"].map(KY[cultura])
    por_fase["perda_pct"] = 100 * por_fase["grupo"].map(perdas)
    return Simulacao(razao, por_fase, diario)


def clima_analogo(observado: pd.DataFrame, ano: int, inicio: pd.Timestamp, fim: pd.Timestamp) -> pd.DataFrame:
    """Clima de [inicio, fim] copiado do mesmo dia/mês do `ano` análogo (29/02 vira 28/02)."""
    datas = pd.date_range(inicio, fim, freq="D")
    deslocamento = ano - inicio.year
    origem = [(d.replace(day=28) if (d.month == 2 and d.day == 29) else d) + pd.DateOffset(years=deslocamento) for d in datas]
    base = observado.set_index("data").reindex(pd.DatetimeIndex(origem))
    return pd.DataFrame({"data": datas, "chuva_mm": base["chuva_mm"].to_numpy(), "eto_mm": base["eto_mm"].to_numpy()})


@dataclass
class Estimativa:
    plantio_id: int
    rotulo: str
    meta_sc_ha: float
    p10_sc_ha: float
    p50_sc_ha: float
    p90_sc_ha: float
    razao_ate_hoje: float            # perda já "garantida" pelo que aconteceu até agora
    dias_observados: int
    dias_previstos: int
    dias_media_historica: int        # buraco no passado preenchido com a média (dado recente faltando)
    dias_cenario: int
    anos_analogos: int
    simulacao_mediana: Simulacao
    cenarios: pd.DataFrame           # ano, razao, sc_ha


def estimar(con: duckdb.DuckDBPyConnection, plantio_id: int, rotulo: str, cultura: str, temporada: str,
            data_plantio: date, solo_ad: str | None, meta_sc_ha: float, hoje: date | None = None) -> Estimativa:
    hoje = pd.Timestamp(hoje or date.today())
    tabela = fases(con, cultura, temporada)
    if tabela.empty or cultura not in KC:
        raise ValueError(f"Sem coeficientes para {cultura}/{temporada}.")
    taw = TAW_POR_AD.get(solo_ad or "AD4", TAW_POR_AD["AD4"])
    inicio = pd.Timestamp(data_plantio)
    fim = inicio + timedelta(days=int(tabela["dia_fim"].max()))

    obs = clima_observado(con)
    obs_ciclo = obs[(obs["data"] >= inicio) & (obs["data"] <= min(fim, hoje))]
    ultimo = obs_ciclo["data"].max() if not obs_ciclo.empty else inicio - timedelta(days=1)
    rec = clima_recente(con, ultimo)
    rec = rec[(rec["data"] >= inicio) & (rec["data"] <= min(fim, hoje))]
    if not rec.empty:
        ultimo = rec["data"].max()
    prev = clima_previsto(con, ultimo)
    prev = prev[prev["data"] <= fim]
    conhecido = pd.concat([obs_ciclo, rec, prev], ignore_index=True).drop_duplicates("data")
    # Buraco no passado (dado recente ainda não carregado): média histórica do dia, sinalizada no resultado
    buraco = pd.date_range(inicio, min(fim, hoje - timedelta(days=1)), freq="D").difference(pd.DatetimeIndex(conhecido["data"]))
    if len(buraco):
        conhecido = pd.concat([conhecido, climatologia(obs, buraco)], ignore_index=True).sort_values("data")

    ano_final = int(obs["data"].max().year) - 1
    cenarios, sims = [], {}
    for ano in range(ANO_ANALOGO_INICIAL, ano_final + 1):
        dias_faltando = pd.date_range(inicio, fim, freq="D").difference(pd.DatetimeIndex(conhecido["data"]))
        if len(dias_faltando):
            analogo = clima_analogo(obs, ano, dias_faltando.min(), dias_faltando.max())
            analogo = analogo[analogo["data"].isin(dias_faltando)]
            serie = pd.concat([conhecido, analogo], ignore_index=True)
        else:
            serie = conhecido
        try:
            sim = simular(serie, inicio.date(), cultura, tabela, taw)
        except ValueError:
            continue  # ano análogo sem dado completo
        cenarios.append((ano, sim.razao_produtividade))
        sims[ano] = sim
        if not len(dias_faltando):
            break  # ciclo todo conhecido: um cenário basta
    if not cenarios:
        raise ValueError("Sem clima suficiente para simular.")
    tab = pd.DataFrame(cenarios, columns=["ano", "razao"]).assign(sc_ha=lambda d: d["razao"] * meta_sc_ha)
    p10, p50, p90 = np.percentile(tab["sc_ha"], [10, 50, 90])
    ano_mediano = tab.iloc[(tab["sc_ha"] - p50).abs().argsort().iloc[0]]["ano"]

    # Perda já acumulada até hoje: simula o que passou e trata o futuro como sem falta de água
    passado = conhecido[conhecido["data"] <= hoje]
    futuro_sem_estresse = pd.DataFrame({"data": pd.date_range(max(passado["data"].max() + timedelta(days=1), inicio)
                                                              if not passado.empty else inicio, fim, freq="D")})
    futuro_sem_estresse["chuva_mm"], futuro_sem_estresse["eto_mm"] = 50.0, 0.0
    razao_hoje = simular(pd.concat([passado, futuro_sem_estresse], ignore_index=True), inicio.date(), cultura,
                         tabela, taw).razao_produtividade

    return Estimativa(
        plantio_id=plantio_id, rotulo=rotulo, meta_sc_ha=meta_sc_ha,
        p10_sc_ha=float(p10), p50_sc_ha=float(p50), p90_sc_ha=float(p90), razao_ate_hoje=float(razao_hoje),
        dias_observados=len(obs_ciclo) + len(rec), dias_previstos=len(prev), dias_media_historica=len(buraco),
        dias_cenario=int(max(0, (fim - inicio).days + 1 - len(conhecido))),
        anos_analogos=len(tab), simulacao_mediana=sims[int(ano_mediano)], cenarios=tab,
    )


def estimar_propriedade(con: duckdb.DuckDBPyConnection, propriedade_id: int, hoje: date | None = None) -> list[Estimativa]:
    """Estimativa para cada lavoura plantada (status 'plantado') da propriedade."""
    plantios = con.execute("""
        SELECT p.id, p.talhao, p.cultura, p.temporada, p.data_plantio, p.solo_ad,
               coalesce(p.produtividade_meta_sc_ha, r.produtividade_sc_ha) AS meta
        FROM fazenda.vw_plantio p
        LEFT JOIN (SELECT DISTINCT cultura, produtividade_sc_ha FROM analytics.custo_referencia) r USING (cultura)
        WHERE p.propriedade_id = ? AND p.status = 'plantado' AND p.data_plantio IS NOT NULL""", [propriedade_id]).df()
    saida = []
    for p in plantios.itertuples():
        if p.cultura not in KC or not p.meta:
            continue
        rotulo = f"{p.cultura.capitalize()} · {p.talhao}"
        try:
            saida.append(estimar(con, int(p.id), rotulo, p.cultura, p.temporada, pd.Timestamp(p.data_plantio).date(),
                                 p.solo_ad, float(p.meta), hoje))
        except ValueError:
            continue
    return saida


def tabela_estimativas(estimativas: list[Estimativa], con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Resumo para alertas e telas, com o ponto de equilíbrio previsto de cada plantio."""
    if not estimativas:
        return pd.DataFrame()
    pe = con.execute("SELECT plantio_id, ponto_equilibrio_sc_ha FROM fazenda.vw_resultado_plantio").df().set_index("plantio_id")
    return pd.DataFrame([{
        "plantio_id": e.plantio_id, "rotulo": e.rotulo, "meta_sc_ha": e.meta_sc_ha,
        "p10_sc_ha": e.p10_sc_ha, "p50_sc_ha": e.p50_sc_ha, "p90_sc_ha": e.p90_sc_ha,
        "perda_ate_hoje_pct": 100 * (1 - e.razao_ate_hoje),
        "ponto_equilibrio_sc_ha": float(pe["ponto_equilibrio_sc_ha"].get(e.plantio_id, np.nan)),
        "cultura": e.rotulo.split(" · ")[0].lower().replace("feijão", "feijao"),
        "confiabilidade": CONFIABILIDADE.get(e.rotulo.split(" · ")[0].lower(), ("não avaliada", False, ""))[0],
        "usar_em_alertas": CONFIABILIDADE.get(e.rotulo.split(" · ")[0].lower(), ("", False, ""))[1],
        "anos_analogos": e.anos_analogos, "dias_observados": e.dias_observados, "dias_previstos": e.dias_previstos,
        "dias_media_historica": e.dias_media_historica,
        "dias_cenario": e.dias_cenario,
    } for e in estimativas])
