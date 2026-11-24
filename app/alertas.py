"""Regras de alerta do SafraViva: funções puras sobre a previsão e o ZARC.

Cada função recebe DataFrames simples e devolve um `Alerta`. Não há Streamlit
aqui, então as regras são testáveis (tests/test_alertas.py) e reaproveitáveis
pelo Agrônomo Digital (Fase 5) e pelos avisos no celular (Fase 6).

Limiares e fontes:
* Geada: Tmín ≤ 3 °C no abrigo ≈ geada na relva; ≤ 1 °C = geada forte provável (docs/insights.md, insight 5).
* Pulverização: vento 3–10 km/h, Delta T 2–8 °C, chuva < 30% de probabilidade e T < 30 °C (boas práticas de aplicação).
* Veranico: ≥ 7 dias seguidos sem chuva ≥ 1 mm prevista; ≥ 10 dias = severo (insight 4: soja sente no florescimento/enchimento).
* Calor: ≥ 3 dias com máxima ≥ 32 °C (abortamento de flores da soja).
* Chuva forte: dia com ≥ 40 mm previstos (erosão, atraso de operações).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

GEADA_ATENCAO_C = 3.0
GEADA_FORTE_C = 1.0
VERANICO_ATENCAO_DIAS = 7
VERANICO_SEVERO_DIAS = 10
SECO_CHUVA_MM = 1.0
SECO_PROB_MAX = 40
CALOR_TMAX_C = 32.0
CALOR_DIAS = 3
CHUVA_FORTE_MM = 40.0

DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]

# nível → (rótulo, ícone). O ícone acompanha sempre o texto: a cor nunca carrega o significado sozinha.
NIVEIS = {
    "critico": ("Atenção alta", "🔴"),
    "atencao": ("Atenção", "🟡"),
    "ok": ("Tranquilo", "🟢"),
    "info": ("Informação", "🔵"),
}


@dataclass(frozen=True)
class Alerta:
    tema: str
    nivel: str  # critico | atencao | ok | info
    titulo: str
    detalhe: str

    @property
    def icone(self) -> str:
        return NIVEIS[self.nivel][1]

    @property
    def rotulo(self) -> str:
        return NIVEIS[self.nivel][0]


def _br(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def dia_curto(d) -> str:
    d = pd.Timestamp(d)
    return f"{DIAS_SEMANA[d.weekday()]} {d:%d/%m}"


def alerta_geada(diaria: pd.DataFrame) -> Alerta:
    """diaria: colunas data, temp_min_c."""
    frio = diaria[diaria["temp_min_c"] <= GEADA_ATENCAO_C]
    if frio.empty:
        minimo = diaria.loc[diaria["temp_min_c"].idxmin()]
        return Alerta("geada", "ok", "Sem risco de geada",
                      f"Menor mínima prevista: {minimo.temp_min_c:.0f} °C ({dia_curto(minimo.data)}).")
    pior = frio.loc[frio["temp_min_c"].idxmin()]
    dias = ", ".join(dia_curto(d) for d in frio["data"])
    if pior.temp_min_c <= GEADA_FORTE_C:
        return Alerta("geada", "critico", f"Geada forte provável em {dia_curto(pior.data)}",
                      f"Mínima de {_br(pior.temp_min_c)} °C. Dias frios: {dias}. Trigo em florescimento é o mais sensível.")
    return Alerta("geada", "atencao", f"Risco de geada em {dia_curto(pior.data)}",
                  f"Mínima de {_br(pior.temp_min_c)} °C no abrigo, o que pode gear na baixada. Dias frios: {dias}.")


def maior_sequencia_seca(diaria: pd.DataFrame) -> tuple[int, object]:
    """Maior sequência de dias secos (chuva < 1 mm e probabilidade < 40%). Devolve (dias, data de início)."""
    seco = (diaria["chuva_mm"].fillna(0) < SECO_CHUVA_MM) & (diaria["prob_chuva_pct"].fillna(0) < SECO_PROB_MAX)
    melhor, inicio_melhor, atual, inicio = 0, None, 0, None
    for d, s in zip(diaria["data"], seco):
        if s:
            inicio = d if atual == 0 else inicio
            atual += 1
            if atual > melhor:
                melhor, inicio_melhor = atual, inicio
        else:
            atual = 0
    return melhor, inicio_melhor


def alerta_veranico(diaria: pd.DataFrame) -> Alerta:
    dias, inicio = maior_sequencia_seca(diaria)
    total = diaria["chuva_mm"].fillna(0).sum()
    if dias >= VERANICO_SEVERO_DIAS:
        return Alerta("veranico", "critico", f"{dias} dias seguidos sem chuva a partir de {dia_curto(inicio)}",
                      f"Veranico longo previsto. Soja em florescimento/enchimento perde produtividade. Chuva total em 16 dias: {total:.0f} mm.")
    if dias >= VERANICO_ATENCAO_DIAS:
        return Alerta("veranico", "atencao", f"{dias} dias secos seguidos a partir de {dia_curto(inicio)}",
                      f"Fique de olho na umidade do solo. Chuva total em 16 dias: {total:.0f} mm.")
    return Alerta("veranico", "ok", "Chuva bem distribuída",
                  f"Maior sequência seca prevista: {dias} dias. Chuva total em 16 dias: {total:.0f} mm.")


def alerta_calor(diaria: pd.DataFrame) -> Alerta:
    quentes = diaria[diaria["temp_max_c"] >= CALOR_TMAX_C]
    if len(quentes) >= CALOR_DIAS:
        pico = quentes.loc[quentes["temp_max_c"].idxmax()]
        return Alerta("calor", "atencao", f"{len(quentes)} dias com máxima ≥ {CALOR_TMAX_C:.0f} °C",
                      f"Pico de {pico.temp_max_c:.0f} °C em {dia_curto(pico.data)}. Calor no florescimento da soja derruba vagens.")
    return Alerta("calor", "ok", "Sem onda de calor",
                  f"Máxima prevista: {diaria['temp_max_c'].max():.0f} °C.")


def alerta_chuva_forte(diaria: pd.DataFrame) -> Alerta:
    fortes = diaria[diaria["chuva_mm"] >= CHUVA_FORTE_MM]
    if fortes.empty:
        prox7 = diaria.head(7)["chuva_mm"].fillna(0).sum()
        return Alerta("chuva", "info", f"{prox7:.0f} mm previstos em 7 dias",
                      "Nenhum dia com chuva forte (≥ 40 mm).")
    dias = ", ".join(f"{dia_curto(r.data)} ({r.chuva_mm:.0f} mm)" for r in fortes.itertuples())
    return Alerta("chuva", "atencao", "Chuva forte prevista", f"{dias}. Evite operações e adubação a lanço antes da chuva.")


def horas_pulverizacao(horaria: pd.DataFrame, agora: pd.Timestamp | None = None) -> pd.DataFrame:
    """Marca cada hora futura como boa ou não para pulverizar. horaria: ts_local, vento_kmh, delta_t_c, prob_chuva_pct, temp_c."""
    agora = agora if agora is not None else pd.Timestamp.now()
    h = horaria[horaria["ts_local"] >= agora.floor("h")].copy()
    h["boa"] = (
        h["ts_local"].dt.hour.between(6, 20)
        & h["vento_kmh"].between(3, 10)
        & h["delta_t_c"].between(2, 8)
        & (h["prob_chuva_pct"].fillna(0) < 30)
        & (h["temp_c"] < 30)
    )
    h["motivo"] = ""
    h.loc[~h["vento_kmh"].between(3, 10), "motivo"] = "vento"
    h.loc[h["delta_t_c"] > 8, "motivo"] = "ar seco/quente (deriva e evaporação)"
    h.loc[h["delta_t_c"] < 2, "motivo"] = "ar úmido demais (escorrimento)"
    h.loc[h["prob_chuva_pct"].fillna(0) >= 30, "motivo"] = "chuva"
    h.loc[h["boa"], "motivo"] = "boa"
    return h


def alerta_pulverizacao(horaria: pd.DataFrame, agora: pd.Timestamp | None = None) -> Alerta:
    h = horas_pulverizacao(horaria, agora)
    h["dia"] = h["ts_local"].dt.normalize()
    por_dia = h.groupby("dia").agg(horas=("boa", "sum")).reset_index()
    proximos = por_dia.head(4)
    if proximos["horas"].sum() == 0:
        return Alerta("pulverizacao", "atencao", "Sem janela boa para pulverizar nos próximos dias",
                      "Vento, chuva ou ar seco fora da faixa ideal. Veja o detalhe hora a hora.")
    melhor = proximos.loc[proximos["horas"].idxmax()]
    horas = h[(h["dia"] == melhor.dia) & h["boa"]]["ts_local"].dt.hour
    return Alerta("pulverizacao", "ok", f"Melhor dia para pulverizar: {dia_curto(melhor.dia)}",
                  f"{int(melhor.horas)} horas boas, entre {horas.min():02d}h e {horas.max() + 1:02d}h (vento, Delta T e chuva na faixa).")


def situacao_plantio(janelas: pd.DataFrame, cultura: str, hoje: date) -> Alerta:
    """janelas: linhas de analytics.janela_plantio já filtradas para município, solo, ciclo e manejo de referência."""
    j = janelas[janelas["nome_cultura"] == cultura].sort_values("data_inicio")
    if j.empty:
        return Alerta("plantio", "info", f"{cultura}: sem zoneamento", "O ZARC não traz janela para esta combinação.")
    hoje = pd.Timestamp(hoje)
    agora = j[(j["data_inicio"] <= hoje) & (j["data_fim"] >= hoje)]
    if not agora.empty:
        r = agora.iloc[0]
        baixo = j[(j["nivel_risco"] == "baixo") & (j["data_fim"] >= hoje)]
        if r.nivel_risco == "baixo":
            return Alerta("plantio", "ok", f"{cultura}: época boa de plantio",
                          f"Risco climático baixo (20%) até {pd.Timestamp(r.data_fim):%d/%m}.")
        complemento = (f" O risco baixo começa em {pd.Timestamp(baixo.iloc[0].data_inicio):%d/%m}."
                       if not baixo.empty and pd.Timestamp(baixo.iloc[0].data_inicio) > hoje else "")
        return Alerta("plantio", "atencao", f"{cultura}: plantio com risco {r.nivel_risco}",
                      f"Risco de {r.risco_pct}% até {pd.Timestamp(r.data_fim):%d/%m}.{complemento}")
    futuras = j[j["data_inicio"] > hoje]
    if not futuras.empty:
        prox = futuras.iloc[0]
        return Alerta("plantio", "info", f"{cultura}: fora da época",
                      f"A janela abre em {pd.Timestamp(prox.data_inicio):%d/%m} (risco {prox.nivel_risco}).")
    # Todas as janelas publicadas já passaram (o MAPA publica a portaria da cultura perto da época).
    # Projeta a janela de risco baixo do último ZARC para o próximo ano.
    baixo = j[j["nivel_risco"] == "baixo"]
    if baixo.empty:
        return Alerta("plantio", "info", f"{cultura}: janela encerrada nesta safra", "Plantio não indicado pelo ZARC.")
    inicio, fim = pd.Timestamp(baixo.iloc[0].data_inicio), pd.Timestamp(baixo.iloc[-1].data_fim)
    while inicio <= hoje:
        inicio, fim = inicio + pd.DateOffset(years=1), fim + pd.DateOffset(years=1)
    return Alerta("plantio", "info", f"{cultura}: fora da época",
                  f"Próxima janela de risco baixo deve ir de {inicio:%d/%m} a {fim:%d/%m}, pelo ZARC anterior "
                  "(o MAPA ainda não publicou o da próxima safra).")


FASES_SECA = {"emergência", "florescimento", "enchimento"}
FASES_CALOR = {"florescimento"}
FASES_GEADA = {"perfilhamento", "florescimento", "enchimento"}
FASES_COLHEITA = {"maturação", "pronta para colher"}
NOMES_CULTURA = {"soja": "Soja", "milho": "Milho", "trigo": "Trigo", "feijao": "Feijão", "aveia": "Aveia",
                 "cevada": "Cevada", "sorgo": "Sorgo"}


def alerta_lavoura(talhao: str, cultura: str, fase: str | None, dias_apos_plantio: int,
                   diaria: pd.DataFrame) -> Alerta:
    """Cruza a fase atual de uma lavoura com a previsão: o mesmo tempo pesa diferente em cada fase.

    Ex.: 8 dias secos não preocupam na maturação, mas preocupam no florescimento da soja;
    3 °C é irrelevante no vegetativo da soja, mas pode esterilizar o trigo no florescimento.
    """
    nome = f"{NOMES_CULTURA.get(cultura, cultura)} · {talhao}"
    fase = fase or "fase desconhecida"
    contexto = f"{fase.capitalize()}, {dias_apos_plantio} dias após o plantio."
    if diaria.empty:
        return Alerta("lavoura", "info", nome, contexto)

    seco, inicio = maior_sequencia_seca(diaria)
    frio = diaria[diaria["temp_min_c"] <= GEADA_ATENCAO_C]
    quentes = diaria[diaria["temp_max_c"] >= CALOR_TMAX_C]
    chuva_7d = diaria.head(7)["chuva_mm"].fillna(0).sum()

    if fase in FASES_GEADA and not frio.empty and cultura in ("trigo", "milho", "aveia", "cevada"):
        pior = frio.loc[frio["temp_min_c"].idxmin()]
        nivel = "critico" if fase == "florescimento" or pior.temp_min_c <= GEADA_FORTE_C else "atencao"
        return Alerta("lavoura", nivel, f"{nome}: risco de geada no {fase}",
                      f"{contexto} Mínima de {_br(pior.temp_min_c)} °C em {dia_curto(pior.data)}.")
    if fase in FASES_SECA and seco >= VERANICO_ATENCAO_DIAS:
        nivel = "critico" if seco >= VERANICO_SEVERO_DIAS and fase != "emergência" else "atencao"
        efeito = "pode falhar o estande" if fase == "emergência" else "a lavoura sente a falta de água nesta fase"
        return Alerta("lavoura", nivel, f"{nome}: {seco} dias sem chuva a partir de {dia_curto(inicio)}",
                      f"{contexto} Fase sensível: {efeito}.")
    if fase in FASES_CALOR and len(quentes) >= CALOR_DIAS:
        return Alerta("lavoura", "atencao", f"{nome}: calor no florescimento",
                      f"{contexto} {len(quentes)} dias com máxima ≥ {CALOR_TMAX_C:.0f} °C: risco de abortar flores.")
    if fase in FASES_COLHEITA and chuva_7d >= 30:
        return Alerta("lavoura", "atencao", f"{nome}: chuva na colheita",
                      f"{contexto} {chuva_7d:.0f} mm previstos em 7 dias: colha nas janelas secas para não perder qualidade.")
    if fase == "pronta para colher":
        return Alerta("lavoura", "info", f"{nome}: pronta para colher", f"{contexto} Tempo firme nos próximos dias.")
    return Alerta("lavoura", "ok", f"{nome}: sem risco do tempo para a fase", contexto)


# ----------------------------------------------------------------------------------------
# Veredito do dia: a frase da primeira dobra da tela "Hoje na lavoura"
# ----------------------------------------------------------------------------------------
CHUVA_DIA_PARADO_MM = 10.0  # chuva no dia que, na prática, tira a operação da lavoura
HORA_VIRADA = 18  # a partir das 18h o veredito passa a falar de amanhã


@dataclass(frozen=True)
class Veredito:
    nivel: str  # critico | atencao | ok | info
    resposta: str  # resposta curta à pergunta "dá para entrar na lavoura?"
    frase: str  # o veredito em uma linha (título)
    apoio: str  # o porquê, ou o alerta de atenção mais importante
    quando: str  # "hoje" | "amanhã"

    @property
    def icone(self) -> str:
        return NIVEIS[self.nivel][1]

    @property
    def rotulo(self) -> str:
        return ROTULOS_VEREDITO[self.nivel]


ROTULOS_VEREDITO = {"ok": "Tudo certo", "atencao": "Atenção", "critico": "Atenção alta", "info": "Com restrição"}


def veredito_do_dia(diaria: pd.DataFrame, horaria: pd.DataFrame, agora: pd.Timestamp | None = None) -> Veredito:
    """Uma frase com a decisão do dia, por ordem de importância:

    1. alerta grave (geada forte, veranico severo) → "Cuidado";
    2. chuva ≥ 10 mm no dia → "Não";
    3. há horas boas para pulverizar → "Sim, das Xh às Yh";
    4. senão → dá para trabalhar, mas não para pulverizar (com o melhor dia).
    A partir das 18h, fala de amanhã.
    """
    agora = agora if agora is not None else pd.Timestamp.now()
    alvo = agora.normalize() + pd.Timedelta(days=1 if agora.hour >= HORA_VIRADA else 0)
    quando = "amanhã" if alvo > agora.normalize() else "hoje"

    clima = [alerta_geada(diaria), alerta_veranico(diaria), alerta_calor(diaria), alerta_chuva_forte(diaria)]
    grave = next((a for a in clima if a.nivel == "critico"), None)
    atencao = next((a for a in clima if a.nivel == "atencao"), None)
    if grave is not None:
        return Veredito("critico", "Cuidado", grave.titulo, grave.detalhe, quando)

    dia = diaria[pd.to_datetime(diaria["data"]).dt.normalize() == alvo]
    chuva = float(dia["chuva_mm"].fillna(0).iloc[0]) if not dia.empty else 0.0
    if chuva >= CHUVA_DIA_PARADO_MM:
        return Veredito("atencao", "Não", f"Dia de chuva {quando}: {chuva:.0f} mm previstos",
                        "Bom para planejar. Evite pulverizar e adubar a lanço.", quando)

    extra = f" Atenção: {atencao.titulo.lower()}." if atencao is not None else ""
    h = horas_pulverizacao(horaria, agora)
    boas = h[(h["ts_local"].dt.normalize() == alvo) & h["boa"]]["ts_local"].dt.hour
    if not boas.empty:
        return Veredito("atencao" if atencao is not None else "ok", "Sim",
                        f"Dá para pulverizar {quando}, das {boas.min()}h às {boas.max() + 1}h",
                        ("Vento, Delta T e chuva na faixa certa." + extra).strip(), quando)

    pulv = alerta_pulverizacao(horaria, agora)
    porque = f"{pulv.titulo}." if pulv.nivel == "ok" else pulv.detalhe
    return Veredito("atencao" if atencao is not None else "info", "Em parte",
                    f"Dá para trabalhar {quando}, mas não para pulverizar", (porque + extra).strip(), quando)
