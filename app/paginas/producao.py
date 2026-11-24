"""Produção regional: Itapeva comparada com SP, PR e os vizinhos."""

import plotly.graph_objects as go
import streamlit as st

from app import dados, ui

st.title("Produção regional")
cultura = st.segmented_control("Cultura", ["soja", "milho", "trigo"], default="soja",
                               format_func=str.capitalize) or "soja"

# --- Itapeva × SP × PR ---------------------------------------------------------------
serie = dados.rendimento_comparado(cultura)
media5 = serie.set_index("ano").rolling(5, min_periods=3).mean().reset_index()
fig = go.Figure()
finais = []
for cor, local in zip(ui.SERIE, ["Itapeva", "São Paulo", "Paraná"]):
    fig.add_trace(go.Scatter(x=media5["ano"], y=media5[local], name=local, mode="lines",
                             line=dict(color=cor, width=2), hovertemplate=f"{local}: %{{y:.1f}} sc/ha<extra></extra>"))
    ultimo = media5.dropna(subset=[local]).iloc[-1]
    finais.append((ultimo.ano, ultimo[local], f"{ultimo[local]:.0f}", cor))
valores = media5[["Itapeva", "São Paulo", "Paraná"]].stack()
ui.rotulos_finais(fig, finais, (valores.min() * 0.95, valores.max() * 1.05))
fig.update_layout(hovermode="x unified")
fig.update_yaxes(ticksuffix=" sc")
fig.update_xaxes(range=[1990, media5["ano"].max() + 3])
ui.mostrar(ui.layout(fig, f"Rendimento de {cultura} (média móvel de 5 anos)", 340))

ult = media5.dropna(subset=["Itapeva", "São Paulo"]).iloc[-1]
col1, col2 = st.columns(2)
col1.metric("Itapeva (5 anos)", f"{ult['Itapeva']:.0f} sc/ha")
col2.metric("vs. média de SP", f"{100 * (ult['Itapeva'] / ult['São Paulo'] - 1):+.0f}%")
ui.fonte("IBGE, Produção Agrícola Municipal (tabela 1612). Anos com valor repetido pelo informante ficam de fora.")

# --- Ranking regional -------------------------------------------------------------------
st.subheader("Itapeva entre os vizinhos")
rank = dados.ranking_regional(cultura).sort_values("area_ha")
cores = [ui.SERIE[0] if m == "Itapeva" else ui.NEUTRO for m in rank["municipio"]]
fig = go.Figure(go.Bar(
    x=rank["area_ha"] / 1000, y=rank["municipio"], orientation="h", marker_color=cores,
    text=[f"{ui.num(a / 1000, 1)} mil ha · {s:.0f} sc/ha" if s == s else f"{ui.num(a / 1000, 1)} mil ha"
          for a, s in zip(rank["area_ha"], rank["sc_ha"])],
    textposition="outside", textfont=dict(color=ui.TEXTO, size=11), cliponaxis=False,
    hovertemplate="<b>%{y}</b><br>%{x:.1f} mil ha<extra></extra>",
))
fig.update_xaxes(showticklabels=False, range=[0, rank["area_ha"].max() / 1000 * 1.9])
fig.update_yaxes(showgrid=False)
ui.mostrar(ui.layout(fig, None, 60 + 30 * len(rank), legenda=False))
participacao = rank.loc[rank["municipio"] == "Itapeva", "area_ha"].sum() / rank["area_ha"].sum()
st.caption(f"Itapeva planta {100 * participacao:.0f}% da área de {cultura} dos 11 municípios da região.")

# --- Área em Itapeva --------------------------------------------------------------------
st.subheader("Como a área cresceu em Itapeva")
area = dados.area_itapeva().pivot(index="ano", columns="cultura", values="mil_ha")
fig = go.Figure()
for cor, c in zip(ui.SERIE, ["soja", "milho", "trigo"]):
    fig.add_trace(go.Scatter(x=area.index, y=area[c], name=c.capitalize(), mode="lines", line=dict(color=cor, width=2),
                             hovertemplate=f"{c.capitalize()}: %{{y:.1f}} mil ha<extra></extra>"))
fig.update_layout(hovermode="x unified")
fig.update_yaxes(ticksuffix=" mil ha")
ui.mostrar(ui.layout(fig, None, 300))
ui.fonte("IBGE/PAM, área colhida.")
