"""Janela de plantio: risco climático do ZARC por data de semeadura."""

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import alertas, dados, ui

ui.titulo("Janela de plantio", "Quando plantar com menos risco, pelo zoneamento oficial do Ministério da Agricultura (ZARC) para Itapeva.")
solo, ciclo = ui.referencia()
st.caption(
    f"Zoneamento Agrícola de Risco Climático (MAPA) para Itapeva · solo **{solo}** · cultivar **{ciclo}** · sequeiro. "
    "Troque o solo e o ciclo no menu lateral."
)

janelas = dados.janelas_plantio(solo, ciclo)
principais = ["Soja", "Milho 1ª Safra", "Milho 2ª Safra", "Feijão", "Feijão 2ª Safra", "Trigo", "Aveia", "Cevada Grãos"]
disponiveis = [c for c in principais if c in set(janelas["nome_cultura"])]
escolhidas = st.multiselect("Culturas", disponiveis, default=[c for c in ["Soja", "Milho 2ª Safra", "Trigo"] if c in disponiveis])

if not escolhidas:
    st.info("Escolha ao menos uma cultura.")
    st.stop()

hoje = pd.Timestamp(date.today())
inicio_eixo, fim_eixo = hoje - pd.DateOffset(months=1), hoje + pd.DateOffset(months=11)


def janelas_no_horizonte(cultura: str) -> tuple[pd.DataFrame, bool]:
    """Janelas da cultura; se a safra publicada já passou, projeta para o próximo ano (MAPA ainda não publicou)."""
    j = janelas[janelas["nome_cultura"] == cultura].copy()
    projetada = False
    while not j.empty and j["data_fim"].max() < hoje:
        j["data_inicio"] += pd.DateOffset(years=1)
        j["data_fim"] += pd.DateOffset(years=1)
        projetada = True
    return j, projetada


fig = go.Figure()
rotulos_y = []
for cultura in escolhidas:
    j, projetada = janelas_no_horizonte(cultura)
    rotulo = f"{cultura}*" if projetada else cultura
    rotulos_y.append(rotulo)
    for r in j.itertuples():
        fim = r.data_fim + pd.Timedelta(days=1)
        fig.add_trace(go.Bar(
            y=[rotulo], x=[(fim - r.data_inicio).total_seconds() * 1000], base=[r.data_inicio], orientation="h",
            marker=dict(color=ui.RISCO[r.nivel_risco], line=dict(color=ui.SUPERFICIE, width=2),
                        pattern=dict(shape="/" if projetada else "", fillmode="overlay", fgcolor="rgba(255,255,255,0.6)", size=7, solidity=0.3)),
            showlegend=False,
            hovertemplate=(f"<b>{cultura}</b>{' (projeção)' if projetada else ''}<br>"
                           f"{r.data_inicio:%d/%m/%Y} a {r.data_fim:%d/%m/%Y}<br>"
                           f"Risco {r.nivel_risco}: {r.risco_pct}% de chance de perda<extra></extra>"),
        ))
for ordem, (nivel, pct) in enumerate((("baixo", 20), ("médio", 30), ("alto", 40))):
    # entradas só de legenda (barra de largura zero numa categoria existente), em ordem fixa
    fig.add_trace(go.Bar(y=[rotulos_y[0]], x=[0], base=[hoje], orientation="h", marker_color=ui.RISCO[nivel],
                         name=f"risco {nivel} ({pct}%)", legendrank=ordem, hoverinfo="skip"))
fig.add_vline(x=hoje, line=dict(color=ui.TEXTO, width=1, dash="dash"))
fig.add_annotation(x=hoje, y=1, yref="paper", yanchor="bottom", text="hoje", showarrow=False,
                   font=dict(size=11, color=ui.TEXTO))
fig.update_xaxes(type="date", tickformat="%b/%y", showgrid=True, gridcolor=ui.GRADE, range=[inicio_eixo, fim_eixo])
fig.update_yaxes(autorange="reversed", showgrid=False, categoryorder="array", categoryarray=rotulos_y)
fig.update_layout(barmode="overlay", bargap=0.35)
ui.layout(fig, "Risco por data de semeadura", 150 + 60 * len(escolhidas))
fig.update_layout(legend=dict(orientation="h", y=-0.15, yanchor="top", x=0, xanchor="left"))  # legenda embaixo
ui.mostrar(fig)
st.caption("Fora das barras, o ZARC não indica o plantio. Seguro rural e Proagro exigem plantio dentro da janela."
           + (" \\* Hachurado = projeção pela safra anterior (o MAPA ainda não publicou a nova portaria)."
              if any(r.endswith("*") for r in rotulos_y) else ""))

st.subheader("Situação hoje")
for cultura in escolhidas:
    ui.cartao(alertas.situacao_plantio(janelas, cultura, date.today()), "Plantio")

with st.expander("Como ler: o que são AD1 a AD6 e os grupos de ciclo"):
    st.markdown(
        """
- **AD = água disponível no solo.** **AD1** é solo arenoso e raso, que seca rápido. **AD6** é solo argiloso e profundo, que segura muita água.
  Os latossolos argilosos das áreas de grãos de Itapeva ficam, em geral, entre **AD4 e AD6**, e as manchas arenosas mais perto de **AD1–AD2**.
  Quem define a classe do talhão é a análise de textura do solo.
- **Grupo I, II e III** são o ciclo da cultivar: **I = precoce**, **III = tardio**. A janela muda com o ciclo, porque muda a data do florescimento.
- **Risco 20 / 30 / 40%** é a chance de a lavoura perder produtividade por clima (seca, geada, chuva na colheita) plantando naquela data.
"""
    )
ui.fonte("MAPA, Tábua de Risco ZARC (safra mais recente publicada para cada cultura).")
