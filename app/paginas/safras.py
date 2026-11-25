"""Clima e safras: o que o histórico ensina sobre safras boas e ruins em Itapeva."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app import dados, ui

ui.titulo("Clima e safras", "Quais safras foram boas ou ruins em Itapeva, e o clima de cada uma.")
cultura = st.segmented_control("Cultura", ["soja", "milho", "trigo"], default="soja",
                               format_func=str.capitalize, key="cultura_safras") or "soja"

# --- Safra boa × ruim -------------------------------------------------------------------
d = dados.desvios_safra(cultura).dropna(subset=["desvio_pct"])
lim = 45
paleta = ["#184f95", "#6da7ec", "#f0efec", "#f08a85", "#b8312f"]


def cor(desvio: float, suspeito: bool) -> str:
    if suspeito:
        return ui.NEUTRO
    t = (np.clip(-desvio, -lim, lim) + lim) / (2 * lim)  # 0 = muito acima, 1 = muito abaixo
    return paleta[min(int(t * len(paleta)), len(paleta) - 1)]


hover = [
    f"<b>{r.ano}</b>: {r.rendimento_sc_ha:.0f} sc/ha ({r.desvio_pct:+.0f}%)"
    + (" · valor suspeito (repetido)" if r.suspeito_repeticao else "")
    + (f"<br>Balanço hídrico no florescimento: {r.balanco_flor_mm:+.0f} mm" if r.balanco_flor_mm == r.balanco_flor_mm else "")
    + (f"<br>Dias ≥ 32 °C no florescimento: {r.dias_calor_flor:.0f}" if r.dias_calor_flor == r.dias_calor_flor else "")
    + (f"<br>Dias ≤ 3 °C no florescimento: {r.dias_frio_flor:.0f}" if cultura == "trigo" and r.dias_frio_flor == r.dias_frio_flor else "")
    + (f"<br>Maior veranico: {r.veranico_dias:.0f} dias" if r.veranico_dias == r.veranico_dias else "")
    + (f"<br>Chuva na colheita: {r.chuva_colheita_mm:.0f} mm" if r.chuva_colheita_mm == r.chuva_colheita_mm else "")
    for r in d.itertuples()
]
fig = go.Figure(go.Bar(x=d["ano"], y=d["desvio_pct"], marker_color=[cor(v, s) for v, s in zip(d["desvio_pct"], d["suspeito_repeticao"])],
                       hovertext=hover, hoverinfo="text"))
fig.add_hline(y=0, line=dict(color=ui.TEXTO_2, width=1))
fig.update_yaxes(ticksuffix="%")
ui.mostrar(ui.layout(fig, f"{cultura.capitalize()}: safra × média dos 5 anos", 340, legenda=False))
st.caption("Azul = safra acima do esperado; vermelho = abaixo. Toque numa barra para ver o clima daquela safra. "
           "Cinza = número oficial suspeito (repetido do ano anterior).")

licoes = {
    "soja": "**2024 (−28%)**: 13 dias acima de 32 °C e falta de água no florescimento (janeiro). "
            "**2011**: 73% da área não foi colhida, sem sinal climático na estação; causa não identificada.",
    "milho": "**2011 (−67%)**: queda forte junto com a soja, sem sinal climático claro. Nos demais anos, o milho responde à água no enchimento.",
    "trigo": "**1994 e 2000**: geada no florescimento (−1,7 °C e −1,5 °C). **2019**: 33 dias sem chuva no florescimento. "
             "**2009**: 285 mm na colheita (grão germinando na espiga).",
}
st.info(licoes[cultura])

# --- Geada ------------------------------------------------------------------------------
st.subheader("Quando gela em Itapeva")
geada = dados.geada_por_mes()
meses = {5: "mai", 6: "jun", 7: "jul", 8: "ago", 9: "set"}
fig = go.Figure(go.Bar(
    x=geada["mes"].map(meses), y=geada["pct_anos_com_evento"], marker_color=ui.SERIE[0],
    text=[f"{v:.0f}%" for v in geada["pct_anos_com_evento"]], textposition="outside", textfont=dict(color=ui.TEXTO),
    customdata=geada["tmin_absoluta_c"], cliponaxis=False,
    hovertemplate="%{x}: %{y:.0f}% dos anos<br>mínima absoluta %{customdata:.1f} °C<extra></extra>",
))
fig.update_yaxes(ticksuffix="%", range=[0, max(25, geada["pct_anos_com_evento"].max() * 1.3)])
ui.mostrar(ui.layout(fig, "Anos com pelo menos 1 dia ≤ 3 °C", 280, legenda=False))
st.caption("Junho e julho concentram o risco, que coincide com o florescimento do trigo semeado em abril e maio. "
           "Cada dia a mais de frio nessa fase custou ~5% de produtividade na região.")
ui.fonte("INMET, estação A714 Itapeva, 2006–2026.")

# --- Calor --------------------------------------------------------------------------------
st.subheader("O verão está ficando mais quente")
tend = dados.tendencia_climatica()
fig = go.Figure(go.Bar(
    x=tend["decada"], y=tend["dias_ge32_verao"], marker_color=ui.SERIE[1],
    text=[f"{v:.0f} dias" for v in tend["dias_ge32_verao"]], textposition="outside", textfont=dict(color=ui.TEXTO),
    customdata=tend["chuva_verao_mm"], cliponaxis=False,
    hovertemplate="%{x}: %{y:.0f} dias ≥ 32 °C<br>chuva out–mar: %{customdata:.0f} mm<extra></extra>",
))
fig.update_yaxes(range=[0, tend["dias_ge32_verao"].max() * 1.25])
ui.mostrar(ui.layout(fig, "Dias com máxima ≥ 32 °C entre outubro e março", 280, legenda=False))
st.caption("Os anos 2020 têm só 5 safras (inclui o El Niño de 2023/24): é um sinal a acompanhar, não uma certeza.")
ui.fonte("NASA POWER, centroide de Itapeva, 1981–2025.")
