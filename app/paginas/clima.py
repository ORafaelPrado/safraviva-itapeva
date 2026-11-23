"""Previsão do tempo detalhada: 16 dias, janela de pulverização hora a hora e chuva do último ano."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import alertas, dados, ui

st.title("🌦️ Previsão do tempo")
diaria, horaria = dados.previsao_diaria(), dados.previsao_horaria()
if diaria.empty:
    st.warning("Sem previsão no banco. Atualize na tela inicial.")
    st.stop()

rotulo_dia = diaria["data"].map(alertas.dia_curto)

# --- Chuva -------------------------------------------------------------------
fig = go.Figure(go.Bar(
    x=diaria["data"], y=diaria["chuva_mm"], marker_color=ui.SERIE[0], marker_line_width=0,
    customdata=list(zip(rotulo_dia, diaria["prob_chuva_pct"].fillna(0))),
    hovertemplate="<b>%{customdata[0]}</b><br>Chuva: %{y:.0f} mm<br>Chance: %{customdata[1]:.0f}%<extra></extra>",
))
fig.update_xaxes(tickformat="%d/%m", dtick=86400000 * 3)
fig.update_yaxes(ticksuffix=" mm")
ui.mostrar(ui.layout(fig, f"Chuva prevista: {diaria['chuva_mm'].sum():.0f} mm em 16 dias", 300, legenda=False))

# --- Temperatura ---------------------------------------------------------------
fig = go.Figure()
fig.add_trace(go.Scatter(x=diaria["data"], y=diaria["temp_max_c"], name="Máxima", mode="lines+markers",
                         line=dict(color=ui.SERIE[1], width=2), marker=dict(size=8, line=dict(color="white", width=2)),
                         hovertemplate="Máx: %{y:.0f} °C<extra></extra>"))
fig.add_trace(go.Scatter(x=diaria["data"], y=diaria["temp_min_c"], name="Mínima", mode="lines+markers",
                         line=dict(color=ui.SERIE[0], width=2), marker=dict(size=8, line=dict(color="white", width=2)),
                         hovertemplate="Mín: %{y:.0f} °C<extra></extra>"))
fig.add_hline(y=alertas.GEADA_ATENCAO_C, line=dict(color=ui.STATUS["critico"], dash="dot", width=1),
              annotation_text="3 °C: risco de geada", annotation_position="bottom left",
              annotation_font=dict(size=11, color=ui.TEXTO))
fig.add_hline(y=alertas.CALOR_TMAX_C, line=dict(color=ui.STATUS["atencao"], dash="dot", width=1),
              annotation_text="32 °C: calor que derruba flor", annotation_position="top left",
              annotation_font=dict(size=11, color=ui.TEXTO))
fig.update_xaxes(tickformat="%d/%m", dtick=86400000 * 3)
fig.update_yaxes(ticksuffix="°", range=[min(0, diaria["temp_min_c"].min() - 2), max(36, diaria["temp_max_c"].max() + 2)])
fig.update_layout(hovermode="x unified")
ui.mostrar(ui.layout(fig, "Temperatura mínima e máxima", 320))
ui.fonte("Open-Meteo, previsão para o centro de Itapeva.")

# --- Pulverização hora a hora --------------------------------------------------------
st.subheader("Quando pulverizar")
st.caption("Hora boa: vento entre 3 e 10 km/h, Delta T entre 2 e 8 °C, chance de chuva abaixo de 30% e menos de 30 °C.")
h = alertas.horas_pulverizacao(horaria)
h = h[h["ts_local"].dt.hour.between(6, 20)]
h["dia"] = h["ts_local"].dt.normalize()
h["hora"] = h["ts_local"].dt.hour
dias = sorted(h["dia"].unique())[:5]
h = h[h["dia"].isin(dias)]
grade = h.pivot(index="dia", columns="hora", values="boa").astype(float)
motivo = h.pivot(index="dia", columns="hora", values="motivo").fillna("já passou")
detalhe = h.pivot(index="dia", columns="hora", values="vento_kmh")
fig = go.Figure(go.Heatmap(
    z=grade.values, x=[f"{c:02d}h" for c in grade.columns], y=[alertas.dia_curto(d) for d in grade.index],
    colorscale=[[0, "#e9e8e4"], [1, ui.STATUS["ok"]]], zmin=0, zmax=1, showscale=False, xgap=2, ygap=2,
    customdata=list(zip(motivo.values.tolist(), detalhe.round(0).values.tolist())),
    text=[["✓" if v == 1 else "" for v in linha] for linha in grade.values], texttemplate="%{text}",
    textfont=dict(color="white", size=12),
    hovertemplate="<b>%{y} %{x}</b><br>%{customdata[0]}<br>vento %{customdata[1]} km/h<extra></extra>",
))
fig.update_yaxes(autorange="reversed", showgrid=False)
rotulos_hora = [f"{c:02d}h" for c in grade.columns]
fig.update_xaxes(tickangle=0, tickmode="array", tickvals=rotulos_hora[::3], side="top")
ui.mostrar(ui.layout(fig, "Verde com ✓ = hora boa para aplicar", 60 + 44 * len(dias), legenda=False))
ui.cartao(alertas.alerta_pulverizacao(horaria), "Pulverização")

# --- Chuva dos últimos 12 meses -------------------------------------------------------
st.subheader("Chuva do último ano × normal")
mensal = dados.chuva_mensal_vs_normal()
if not mensal.empty:
    mensal["rotulo"] = pd.to_datetime(mensal["mes"]).dt.strftime("%b/%y")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=mensal["rotulo"], y=mensal["normal_mm"], name="Normal 1991–2020", marker_color=ui.NEUTRO,
                         hovertemplate="Normal: %{y:.0f} mm<extra></extra>"))
    fig.add_trace(go.Bar(x=mensal["rotulo"], y=mensal["chuva_mm"], name="Choveu", marker_color=ui.SERIE[0],
                         hovertemplate="Choveu: %{y:.0f} mm<extra></extra>"))
    fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08, hovermode="x unified")
    fig.update_yaxes(ticksuffix=" mm")
    ui.mostrar(ui.layout(fig, None, 300))
    total, normal = mensal["chuva_mm"].sum(), mensal["normal_mm"].sum()
    st.caption(f"Últimos 12 meses: {total:.0f} mm ({100 * (total / normal - 1):+.0f}% em relação à normal de {normal:.0f} mm).")
    ui.fonte("INMET estação A714 Itapeva (falhas preenchidas com NASA POWER calibrada).")
