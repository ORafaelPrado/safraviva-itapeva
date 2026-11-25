"""Agrônomo Digital: conversa com a IA, que responde com os dados do SafraViva."""

import os

import streamlit as st

from ai.agente import Agente, ProvedorOpenAI, confirmar_pendente
from ai.ferramentas import Contexto
from ai.registro import registrar
from app import dados, eventos, ui

ui.titulo("Agrônomo Digital", "Pergunte como perguntaria ao agrônomo. Ele consulta os dados do SafraViva e diz de onde tirou cada número.")
st.caption("É orientação: defensivo só com receituário agronômico.")

if not os.getenv("OPENAI_API_KEY"):
    st.warning("O Agrônomo Digital está desligado neste computador: falta a chave da IA "
               "(`OPENAI_API_KEY` no arquivo `.env`). Depois de colar a chave, reinicie o painel.", icon=":material/key:")
    st.stop()

pid = ui.propriedade_atual()
props = dados.propriedades()
nome_prop = None
if pid is not None and not props.empty:
    linha = props.set_index("id").loc[pid]
    nome_prop = linha["nome"] + (" (DEMONSTRAÇÃO, dados fictícios)" if linha["demo"] else "")

st.session_state.setdefault("chat", [])        # [{role, content, ferramentas?}]
st.session_state.setdefault("pendentes", [])   # lançamentos aguardando confirmação

SUGESTOES = [
    "Posso pulverizar amanhã?",
    "Tem risco de geada nos próximos dias?",
    "Como estão minhas lavouras?",
    "Quanto minha soja deve render este ano?",
    "Quanto gastei por saca de soja na última safra?",
    "Qual a melhor época para plantar trigo aqui?",
    "Por que a soja de 2024 quebrou em Itapeva?",
]

NOMES_FERRAMENTA = {
    "previsao_tempo": "previsão do tempo", "janela_pulverizacao": "janela de pulverização",
    "clima_historico": "histórico de clima", "janela_plantio": "zoneamento (ZARC)",
    "minhas_lavouras": "suas lavouras", "resultado_safra": "resultado da safra",
    "custos_por_categoria": "custos × CONAB", "caderno_de_campo": "caderno de campo",
    "producao_regional": "produção regional (IBGE)", "conhecimento_regional": "base regional",
    "propor_lancamento": "preparar lançamento",
    "estimativa_safra": "estimativa de safra", "alertas_ativos": "central de alertas",
    "cotacoes": "cotações (CEPEA, Chicago, dólar)",
}


def mostrar_ferramentas(usadas: list[dict]) -> None:
    if usadas:
        nomes = list(dict.fromkeys(NOMES_FERRAMENTA.get(f["nome"], f["nome"]) for f in usadas))
        st.caption("Consultou: " + ", ".join(nomes))


with st.expander("Resumo da semana", icon=":material/calendar_today:"):
    st.caption("O tempo da semana, a fase de cada lavoura e o que fazer.")
    if st.button("Montar o resumo da semana"):
        from ai.resumo_semanal import gerar

        with st.spinner("Montando o resumo..."):
            try:
                resumo = gerar(ProvedorOpenAI(), pid, nome_prop)
                st.session_state["resumo"] = resumo.texto
                dados.gravar(registrar, "resumo semanal", resumo, pid, "resumo_semanal")
            except Exception as erro:  # noqa: BLE001
                st.error("Não deu para montar o resumo agora. Tente de novo em 1 minuto.")
                st.caption(f"Detalhe técnico: {erro}")
    if st.session_state.get("resumo"):
        st.markdown(st.session_state["resumo"])

# --- histórico -------------------------------------------------------------------------------
for msg in st.session_state["chat"]:
    with st.chat_message(msg["role"], avatar=":material/person:" if msg["role"] == "user" else ":material/eco:"):
        st.markdown(msg["content"])
        mostrar_ferramentas(msg.get("ferramentas", []))

# --- lançamentos pendentes ----------------------------------------------------------------------
for i, pendente in enumerate(list(st.session_state["pendentes"])):
    with st.container(border=True):
        st.markdown(f"**Lançamento para confirmar:** {pendente['resumo']}")
        c1, c2 = st.columns(2)
        if c1.button("Confirmar", key=f"ok_{i}", type="primary", width="stretch", icon=":material/check:"):
            ok, msg = dados.gravar(confirmar_pendente, pendente)
            if ok:
                eventos.registrar("lancamento_salvo", "agronomo", "ditado_ia")
            st.session_state["pendentes"].pop(i)
            st.session_state["chat"].append({"role": "assistant",
                                             "content": "Lançado no caderno de campo." if ok else f"Não deu para lançar: {msg}"})
            st.rerun()
        if c2.button("Cancelar", key=f"nao_{i}", width="stretch"):
            st.session_state["pendentes"].pop(i)
            st.session_state["chat"].append({"role": "assistant", "content": "Lançamento cancelado."})
            st.rerun()

# --- entrada ------------------------------------------------------------------------------------
pergunta = st.chat_input("Escreva sua pergunta ou conte o que fez na lavoura")
if not st.session_state["chat"] and not pergunta:
    st.markdown("**Experimente:**")
    cols = st.columns(2)
    for i, s in enumerate(SUGESTOES):
        if cols[i % 2].button(s, key=f"sug_{i}", width="stretch"):
            pergunta = s

if pergunta:
    eventos.registrar("pergunta_ia", "agronomo", "sugestao" if pergunta in SUGESTOES else "digitada")
    st.session_state["chat"].append({"role": "user", "content": pergunta})
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(pergunta)
    with st.chat_message("assistant", avatar=":material/eco:"):
        with st.spinner("Consultando os dados..."):
            try:
                ctx = Contexto(propriedade_id=pid)
                historico = [{"role": m["role"], "content": m["content"]} for m in st.session_state["chat"][:-1]][-10:]
                resultado = Agente(ProvedorOpenAI()).perguntar(pergunta, ctx, historico, nome_prop)
            except Exception as erro:  # noqa: BLE001 — erro de rede/chave/modelo vira mensagem clara
                st.error("O agrônomo não conseguiu responder agora. Tente de novo em 1 minuto.")
                st.caption(f"Detalhe técnico: {erro}")
                st.session_state["chat"].pop()
                st.stop()
        st.markdown(resultado.texto)
        mostrar_ferramentas(resultado.ferramentas_usadas)
    st.session_state["chat"].append({"role": "assistant", "content": resultado.texto,
                                     "ferramentas": resultado.ferramentas_usadas})
    st.session_state["pendentes"].extend(resultado.pendentes)
    dados.gravar(registrar, pergunta, resultado, pid, "chat")
    st.rerun()

if st.session_state["chat"]:
    if st.button("Nova conversa", icon=":material/refresh:"):
        st.session_state["chat"], st.session_state["pendentes"] = [], []
        st.rerun()
