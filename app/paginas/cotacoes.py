"""Cotações: soja, milho, trigo e dólar, com histórico, bolsa ao vivo e perguntas à IA."""

import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import dados, ui

ui.titulo("Cotações", "Quanto está a saca hoje e se o preço mexeu por causa de Chicago ou do dólar.")
st.caption("**CEPEA/ESALQ:** preço do físico no Brasil, uma vez por dia (sai à tarde). **Chicago (CBOT):** bolsa ao vivo, "
           "com ~15 min de atraso, convertida para R$/saca. A conversão não inclui o prêmio de porto, o frete nem os impostos. "
           "**Dólar:** comercial ao vivo e PTAX do Banco Central.")

CULTURAS = {
    "soja": {"nome": "Soja", "cepea": ["cepea_soja_parana", "cepea_soja_paranagua"], "cbot": "cbot_soja"},
    "milho": {"nome": "Milho", "cepea": ["cepea_milho"], "cbot": "cbot_milho"},
    "trigo": {"nome": "Trigo", "cepea": ["cepea_trigo_parana"], "cbot": "cbot_trigo"},
}
CURTO = {"cepea_soja_parana": "CEPEA Paraná", "cepea_soja_paranagua": "CEPEA Paranaguá", "cepea_milho": "CEPEA Campinas",
         "cepea_trigo_parana": "CEPEA Paraná", "cbot_soja": "Chicago", "cbot_milho": "Chicago", "cbot_trigo": "Chicago"}


def _var(v) -> str | None:
    return None if v is None or v != v else f"{v:+.2f}%".replace(".", ",")


@st.fragment(run_every="5m")
def painel_ao_vivo() -> None:
    falha = dados.cotacoes_atualizar_se_preciso()
    if falha:
        st.toast(f"Não deu para atualizar as cotações: {falha}", icon=":material/warning:")
    resumo = dados.cotacao_resumo().set_index("serie")
    bolsa = dados.cotacao_bolsa().set_index("serie")
    if resumo.empty:
        st.info("Ainda sem cotações carregadas.")
        return
    for chave, c in CULTURAS.items():
        st.markdown(f"**{c['nome']}** · R$ por saca de 60 kg")
        cols = st.columns(len(c["cepea"]) + 1)
        for col, serie in zip(cols, c["cepea"]):
            if serie in resumo.index:
                r = resumo.loc[serie]
                col.metric(f"{CURTO[serie]} ({pd.Timestamp(r['data']):%d/%m})", ui.reais(r["valor"], 2), _var(r["variacao_pct"]))
        if c["cbot"] in bolsa.index:
            b = bolsa.loc[c["cbot"]]
            cols[-1].metric(f"Chicago ({pd.Timestamp(b['horario_mercado']):%d/%m %Hh%M})", ui.reais(b["preco_rs_sc"], 2),
                            _var(b["variacao_pct"]), help=f"{ui.num(b['preco'], 2)} US¢/bushel")
    d1, d2 = st.columns(2)
    if "dolar" in bolsa.index:
        b = bolsa.loc["dolar"]
        d1.metric(f"Dólar comercial ({pd.Timestamp(b['horario_mercado']):%Hh%M})", ui.reais(b["preco"], 4), _var(b["variacao_pct"]))
    if "dolar_ptax" in resumo.index:
        r = resumo.loc["dolar_ptax"]
        d2.metric(f"Dólar PTAX ({pd.Timestamp(r['data']):%d/%m})", ui.reais(r["valor"], 4), _var(r["variacao_pct"]))
    ui.ao_vivo(f"atualiza sozinho a cada 5 minutos · última às {pd.Timestamp.now():%Hh%M}")


painel_ao_vivo()

# --- Detalhe por cultura ------------------------------------------------------------------------------------
st.divider()
chave = st.segmented_control("Detalhe", list(CULTURAS), format_func=lambda k: CULTURAS[k]["nome"], default="soja") or "soja"
c = CULTURAS[chave]
periodos = {"1 mês": 31, "6 meses": 183, "1 ano": 366, "5 anos": 1827, "20 anos": 7305}
periodo = st.segmented_control("Período", list(periodos), default="1 ano") or "1 ano"
desde = (pd.Timestamp.today() - pd.Timedelta(days=periodos[periodo])).date().isoformat()
hist = dados.cotacao_historico(tuple(c["cepea"] + [c["cbot"]]), desde)
fig = go.Figure()
for cor, serie in zip(ui.SERIE, c["cepea"] + [c["cbot"]]):
    h = hist[hist["serie"] == serie]
    if not h.empty:
        fig.add_trace(go.Scatter(x=h["data"], y=h["valor"], name=CURTO[serie], mode="lines", line=dict(color=cor, width=2),
                                 hovertemplate=f"{CURTO[serie]}: R$ %{{y:.2f}}<extra></extra>"))
fig.update_layout(hovermode="x unified")
fig.update_yaxes(tickprefix="R$ ")
ui.mostrar(ui.layout(fig, f"{c['nome']}: R$ por saca ({periodo})", 320))
if periodos[periodo] > 760:
    st.caption("Chicago convertido para R$ só a partir de 2 anos atrás (histórico do dólar carregado).")

# Pregão de hoje em Chicago
intradia = dados.cotacao_intradia(c["cbot"])
if not intradia.empty:
    fig = go.Figure(go.Scatter(x=intradia["ts"], y=intradia["valor"], mode="lines", line=dict(color=ui.SERIE[0], width=2),
                               hovertemplate="%{x|%Hh%M}: %{y:.2f} US¢/bushel<extra></extra>"))
    fig.update_xaxes(tickformat="%Hh")
    ui.mostrar(ui.layout(fig, "Chicago hoje (US¢/bushel, horário de Brasília)", 220, legenda=False))

# Sazonalidade
saz = dados.cotacao_sazonalidade(c["cepea"][0])
if not saz.empty:
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    cores = ["#184f95" if v >= 0 else "#b8312f" for v in saz["desvio_pct"]]
    fig = go.Figure(go.Bar(x=[meses[m - 1] for m in saz["mes"]], y=saz["desvio_pct"], marker_color=cores,
                           text=[f"{v:+.1f}%".replace(".", ",") for v in saz["desvio_pct"]], textposition="outside",
                           textfont=dict(color=ui.TEXTO, size=10), cliponaxis=False,
                           hovertemplate="%{x}: %{y:+.1f}% em relação à média do ano<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=ui.TEXTO_2, width=1))
    fig.update_yaxes(ticksuffix="%", range=[min(saz["desvio_pct"].min() * 1.4, -1), max(saz["desvio_pct"].max() * 1.4, 1)])
    ui.mostrar(ui.layout(fig, f"Sazonalidade · {CURTO[c['cepea'][0]]} (últimos 10 anos)", 260, legenda=False))
    st.caption("Quanto o preço de cada mês costuma ficar acima (azul) ou abaixo (vermelho) da média do próprio ano. "
               "É padrão do passado, não previsão.")

# Fazenda
pid = ui.propriedade_atual()
if pid is not None:
    r = dados.resultado(pid)
    r = r[(r["cultura"] == chave) & r["sacas"].notna()]
    resumo = dados.cotacao_resumo().set_index("serie")
    if not r.empty and c["cepea"][0] in resumo.index:
        safra = r["safra"].max()
        rs = r[r["safra"] == safra]
        custo_sc = rs["custo_total"].sum() / rs["sacas"].sum()
        preco = resumo.loc[c["cepea"][0], "valor"]
        vendas = dados.vendas(pid)
        vendidas = vendas[(vendas["cultura"] == chave) & (vendas["safra"] == safra)]["sacas"].sum()
        estoque = max(rs["sacas"].sum() - vendidas, 0)
        st.subheader("Para a sua fazenda")
        ui.aviso_demo(bool(dados.propriedades().set_index("id").loc[pid, "demo"]))
        f1, f2 = st.columns(2)
        f1.metric(f"Custo por saca (safra {safra})", ui.reais(custo_sc, 2))
        f2.metric("Preço de hoje − custo", ui.reais(preco - custo_sc, 2), f"{100 * (preco / custo_sc - 1):+.0f}%".replace(".", ","))
        if estoque >= 10:  # sobras de arredondamento não são estoque
            st.markdown(f"**Estoque:** {ui.num(estoque)} sc · ao preço de hoje ({CURTO[c['cepea'][0]]}) = **{ui.reais(estoque * preco)}**")

ui.fonte("CEPEA/ESALQ (CC BY-NC 4.0, uso não comercial com crédito); CBOT e dólar comercial via Yahoo Finance (atraso ~15 min, "
         "fonte não oficial); PTAX: Banco Central do Brasil.")

# --- Pergunte à IA --------------------------------------------------------------------------------------------
st.divider()
st.subheader("Pergunte sobre as cotações")
if not os.getenv("OPENAI_API_KEY"):
    st.info("A pergunta à IA está desligada neste computador: falta a chave da IA (veja a tela Agrônomo Digital).")
else:
    from ai.agente import Agente, ProvedorOpenAI
    from ai.ferramentas import Contexto
    from ai.registro import registrar

    st.session_state.setdefault("chat_cotacoes", [])
    for m in st.session_state["chat_cotacoes"]:
        with st.chat_message(m["role"], avatar="🧑‍🌾" if m["role"] == "user" else "🌱"):
            st.markdown(m["content"])
    sugestoes = [f"Como está o preço da {c['nome'].lower()} hoje?",
                 f"Em que meses a {c['nome'].lower()} costuma pagar melhor?",
                 "Quanto o dólar mexeu no preço da soja este mês?",
                 "Meu estoque cobre o custo ao preço de hoje?"]
    pergunta = None
    if not st.session_state["chat_cotacoes"]:
        cols = st.columns(2)
        for i, s in enumerate(sugestoes):
            if cols[i % 2].button(s, key=f"sug_cot_{i}", width="stretch"):
                pergunta = s
    pergunta = st.chat_input("Ex.: a soja subiu por causa de Chicago ou do dólar?", key="entrada_cotacoes") or pergunta
    if pergunta:
        st.session_state["chat_cotacoes"].append({"role": "user", "content": pergunta})
        with st.spinner("Consultando as cotações..."):
            try:
                historico = st.session_state["chat_cotacoes"][:-1][-8:]
                resultado = Agente(ProvedorOpenAI()).perguntar(pergunta, Contexto(propriedade_id=pid), historico)
                st.session_state["chat_cotacoes"].append({"role": "assistant", "content": resultado.texto})
                dados.gravar(registrar, pergunta, resultado, pid, "cotacoes")
            except Exception as erro:  # noqa: BLE001
                st.session_state["chat_cotacoes"].pop()
                st.error("O agrônomo não conseguiu responder agora. Tente de novo em 1 minuto.")
                st.caption(f"Detalhe técnico: {erro}")
        st.rerun()
