"""Estimativa de safra: balanço hídrico de cada lavoura + anos análogos para o que ainda vai acontecer."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analytics.balanco_hidrico import CONFIABILIDADE, TAW_POR_AD
from app import dados, ui

st.title("🌾 Estimativa de safra")
pid = ui.propriedade_atual()
if pid is None:
    st.info("Cadastre a propriedade e os plantios para ver a estimativa.")
    st.stop()
ui.aviso_demo(bool(dados.propriedades().set_index("id").loc[pid, "demo"]))

with st.spinner("Simulando a água no solo de cada lavoura..."):
    lista, tabela = dados.estimativas(pid)
if not lista:
    st.info("Nenhuma lavoura plantada com data de plantio e meta de produtividade.")
    st.stop()

st.caption("Para cada lavoura, o SafraViva acompanha a água no solo dia a dia desde o plantio: chuva que entrou "
           "menos o que a planta consumiu. Quando falta água, a produtividade cai, mais forte no florescimento e no "
           "enchimento de grãos (método FAO). Para o resto do ciclo, que ainda não aconteceu, simula o clima de cada "
           "ano desde 1991 e mostra a **faixa provável**.")

rotulos = {e.plantio_id: e.rotulo for e in lista}
escolha = st.segmented_control("Lavoura", list(rotulos), format_func=rotulos.get, default=lista[0].plantio_id) \
    or lista[0].plantio_id
e = next(x for x in lista if x.plantio_id == escolha)
linha = tabela.set_index("plantio_id").loc[escolha]
cultura = linha["cultura"]
nivel_conf, _, texto_conf = CONFIABILIDADE.get(cultura, ("não avaliada", False, ""))

# --- Números principais ---------------------------------------------------------------------------
c1, c2 = st.columns(2)
c1.metric("Produtividade provável", f"{ui.num(e.p50_sc_ha, 0)} sc/ha", help="Mediana dos cenários (p50).")
c2.metric("Faixa provável", f"{ui.num(e.p10_sc_ha, 0)} a {ui.num(e.p90_sc_ha, 0)} sc/ha",
          help="De um ano ruim (p10) a um ano bom (p90) para o restante do ciclo.")
c3, c4 = st.columns(2)
c3.metric("Meta", f"{ui.num(e.meta_sc_ha, 0)} sc/ha")
pe = linha["ponto_equilibrio_sc_ha"]
c4.metric("Ponto de equilíbrio", f"{ui.num(pe, 1)} sc/ha" if pe == pe else "–")
perda = linha["perda_ate_hoje_pct"]
st.markdown(f"**Perda por falta de água até hoje:** {ui.num(perda, 0)}%"
            + (" (sem estresse até agora)" if perda < 0.5 else "") + f" · **Confiabilidade:** {nivel_conf}")
st.caption(texto_conf)

# --- Distribuição dos cenários --------------------------------------------------------------------------
cen = e.cenarios.sort_values("sc_ha")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=cen["sc_ha"], y=np.zeros(len(cen)) + np.random.default_rng(1).uniform(-0.3, 0.3, len(cen)), mode="markers",
    marker=dict(color=ui.SERIE[0], size=10, opacity=0.75, line=dict(color="white", width=1.5)),
    customdata=cen["ano"], hovertemplate="Se o resto do ciclo repetir %{customdata}: %{x:.0f} sc/ha<extra></extra>",
    showlegend=False))
for valor, nome, cor in [(pe, "ponto de equilíbrio", ui.STATUS["critico"]), (e.meta_sc_ha, "meta", ui.TEXTO_2)]:
    if valor == valor:
        fig.add_vline(x=valor, line=dict(color=cor, width=1.5, dash="dash"))
        fig.add_annotation(x=valor, y=-0.46, text=nome, showarrow=False, xanchor="right", yanchor="bottom", xshift=-4,
                           font=dict(size=11, color=ui.TEXTO), bgcolor=ui.SUPERFICIE)
fig.update_yaxes(visible=False, range=[-0.5, 0.5])
fig.update_xaxes(ticksuffix=" sc", range=[0, max(e.meta_sc_ha, pe if pe == pe else 0) * 1.1], showgrid=True, gridcolor=ui.GRADE)
ui.mostrar(ui.layout(fig, f"Um ponto por ano análogo ({e.anos_analogos} cenários)", 200, legenda=False))

# --- Água no solo ao longo do ciclo (cenário mediano) --------------------------------------------------------------
diario = e.simulacao_mediana.diario
hoje = pd.Timestamp.today().normalize()
fim_prev = hoje + pd.Timedelta(days=e.dias_previstos)
fig = go.Figure()
for nome, filtro, cor in [("observado", diario["data"] < hoje, ui.SERIE[0]),
                          ("previsão 16 dias", (diario["data"] >= hoje) & (diario["data"] <= fim_prev), ui.SERIE[1]),
                          ("cenário (ano típico)", diario["data"] > fim_prev, ui.NEUTRO)]:
    trecho = diario[filtro]
    if not trecho.empty:
        fig.add_trace(go.Scatter(x=trecho["data"], y=trecho["armazenamento_pct"], name=nome, mode="lines",
                                 line=dict(color=cor, width=2.5), hovertemplate="%{x|%d/%m}: %{y:.0f}% da água disponível<extra></extra>"))
fig.add_hline(y=50, line=dict(color=ui.STATUS["atencao"], dash="dot", width=1),
              annotation_text="abaixo de 50%: a planta começa a sofrer", annotation_position="bottom left",
              annotation_font=dict(size=11, color=ui.TEXTO))
solo = dados.plantios(pid).set_index("id").loc[escolha, "solo_ad"] or "AD4"
fig.update_yaxes(range=[0, 105], ticksuffix="%")
fig.update_xaxes(tickformat="%d/%m")
ui.layout(fig, "Água disponível no solo (cenário mediano)", 320)
fig.update_layout(legend=dict(orientation="h", y=-0.15, yanchor="top", x=0, xanchor="left"))
ui.mostrar(fig)
st.caption(f"Solo {solo}: cerca de {ui.num(TAW_POR_AD.get(solo, 100))} mm de água disponível na zona das raízes "
           "(aproximação pela classe do ZARC; a análise de solo do talhão refina esse número).")

# --- Por fase -----------------------------------------------------------------------------------------------
fases = e.simulacao_mediana.por_fase.assign(atendido=lambda d: 100 * d["razao_eta_etc"])
st.dataframe(
    fases[["fase", "etc_mm", "eta_mm", "atendido", "ky", "perda_pct"]], hide_index=True, use_container_width=True,
    column_config={
        "fase": "Fase", "etc_mm": st.column_config.NumberColumn("Precisava (mm)", format="%.0f"),
        "eta_mm": st.column_config.NumberColumn("Teve (mm)", format="%.0f"),
        "atendido": st.column_config.ProgressColumn("Água atendida", format="%.0f%%", min_value=0, max_value=100),
        "ky": st.column_config.NumberColumn("Sensibilidade (Ky)", format="%.1f"),
        "perda_pct": st.column_config.NumberColumn("Perda (%)", format="%.1f"),
    },
)
st.caption(f"Clima usado: {e.dias_observados} dias observados, {e.dias_previstos} de previsão e {e.dias_cenario} de "
           f"cenário (anos 1991 em diante)." + (f" {e.dias_media_historica} dias sem dado recente foram preenchidos "
                                               "com a média histórica." if e.dias_media_historica else ""))
ui.fonte("Balanço hídrico FAO-56 com Ky da FAO-33; estação A714 + NASA POWER + Open-Meteo. Considera só a água: "
         "doenças, pragas, geada e nutrição não entram. Validação em docs/backtest_balanco.md.")
