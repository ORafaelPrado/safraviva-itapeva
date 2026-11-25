"""Ficha da fazenda: formulário que o produtor preenche uma vez, no celular, para o app usar os dados reais."""

from datetime import date

import pandas as pd
import streamlit as st

from app import dados, eventos, ficha, ui

ui.titulo("Ficha da fazenda", "Preencha uma vez para o SafraViva usar os dados da sua fazenda no lugar da fazenda de exemplo.")

if st.session_state.get("_ficha_ok"):
    r = st.session_state["_ficha_ok"]
    if r["situacao"] == "aplicada":
        st.success("**Ficha recebida. Obrigado!** A sua fazenda já está no SafraViva: escolha ela no menu "
                   "lateral (Propriedade) e abra **Hoje na lavoura**.", icon=":material/check_circle:")
    else:
        st.info(f"**Ficha recebida e guardada.** {r['aviso']} O Rafael vai conferir e ajustar.",
                icon=":material/inbox:")
    if st.button("Preencher outra ficha", icon=":material/edit:"):
        st.session_state.pop("_ficha_ok")
        st.rerun()
    st.stop()

st.markdown("Leva uns **10 minutos**. **Pode deixar em branco o que não souber**: dá para completar depois.")

# Fora do formulário: mudam quantos campos aparecem.
c1, c2 = st.columns(2)
n_talhoes = c1.number_input("Quantos talhões a fazenda tem?", min_value=1, max_value=15, value=3, step=1,
                            help="Talhão = cada pedaço de lavoura que você trata separado (ex.: Sede, Chapada, Baixada).")
unidade = c2.radio("Você mede a área em", list(ficha.UNIDADES), format_func=ficha.UNIDADES.get, horizontal=True)
rotulo_area = "Área (ha)" if unidade == "ha" else "Área (alqueires)"

with st.form("ficha"):
    st.subheader("1. A fazenda")
    nome = st.text_input("Nome da fazenda ou do sítio", placeholder="ex.: Sítio Santa Rita")
    local = st.text_input("Onde fica", placeholder="ex.: Bairro dos Pereiras, estrada para Itaberá, km 8")
    coordenadas = st.text_input(
        "Localização no mapa (opcional)", placeholder="-23.98, -48.87",
        help="No Google Maps, segure o dedo em cima da sede: aparecem dois números. Toque neles para copiar e cole aqui.")

    st.subheader("2. Talhões e o que está plantado agora")
    st.caption("Para cada talhão: o tamanho, o tipo de terra e a lavoura desta safra de verão.")
    talhoes = []
    for i in range(int(n_talhoes)):
        with st.container(border=True):
            st.markdown(f"**Talhão {i + 1}**")
            t = {
                "nome": st.text_input("Nome do talhão", key=f"t{i}_nome", placeholder="ex.: Chapada"),
                "area": st.number_input(rotulo_area, key=f"t{i}_area", min_value=0.0, step=1.0, value=None),
                "terra": st.selectbox("Tipo de terra", list(ficha.TERRAS), key=f"t{i}_terra",
                                      format_func=lambda k: ficha.TERRAS[k][0]),
                "lavoura": st.selectbox("O que está plantado (ou vai plantar) nesta safra", list(ficha.LAVOURA_AGORA),
                                        key=f"t{i}_lav", format_func=ficha.LAVOURA_AGORA.get),
            }
            plantio = st.date_input("Data do plantio (pode ser aproximada)", value=None, key=f"t{i}_data",
                                    format="DD/MM/YYYY", min_value=date(2025, 7, 1), max_value=date(2027, 6, 30))
            t["data_plantio"] = plantio.isoformat() if plantio else None
            t["cultivar"] = st.text_input("Variedade / cultivar (opcional)", key=f"t{i}_cult", placeholder="ex.: BRS 1003")
            t["ciclo"] = st.selectbox("Ciclo da variedade", list(ficha.CICLOS), key=f"t{i}_ciclo",
                                      format_func=lambda k: ficha.CICLOS[k][0])
            t["meta_sc_ha"] = st.number_input("Quanto espera colher (sacas por hectare)", key=f"t{i}_meta",
                                              min_value=0.0, step=1.0, value=None)
            talhoes.append(t)

    st.subheader("3. Quanto costuma render")
    st.caption("Média dos últimos anos, em sacas por hectare. Só das lavouras que você planta.")
    h1, h2, h3 = st.columns(3)
    historico = {
        "soja": h1.number_input("Soja", min_value=0.0, step=1.0, value=None, key="h_soja"),
        "milho": h2.number_input("Milho", min_value=0.0, step=1.0, value=None, key="h_milho"),
        "trigo": h3.number_input("Trigo", min_value=0.0, step=1.0, value=None, key="h_trigo"),
    }

    st.subheader("4. Venda e custo")
    onde_vende = st.text_input("Para quem costuma vender", placeholder="ex.: cooperativa, cerealista da cidade, trading")
    custo_soja = st.number_input("Quanto gasta, mais ou menos, para plantar 1 hectare de soja (R$)",
                                 min_value=0.0, step=100.0, value=None,
                                 help="Semente, adubo, defensivo, máquina e mão de obra, tudo junto. Um chute já ajuda.")

    st.subheader("5. Para terminar")
    whatsapp = st.text_input("WhatsApp para receber os alertas no futuro (opcional)", placeholder="(15) 9 9999-9999")
    observacoes = st.text_area("Algo mais que o Rafael precisa saber?",
                               placeholder="ex.: arrendo o talhão da Baixada; planto trigo no inverno na Chapada")
    enviar = st.form_submit_button("Enviar ficha", type="primary", width="stretch", icon=":material/send:")

if enviar:
    respostas = {
        "fazenda": {"nome": nome, "local": local, "coordenadas": coordenadas, "unidade_area": unidade},
        "talhoes": talhoes,
        "historico_sc_ha": historico,
        "venda": {"onde_vende": onde_vende},
        "custo_soja_rs_ha": custo_soja,
        "whatsapp": whatsapp,
        "observacoes": observacoes,
        "enviada_em": pd.Timestamp.now().isoformat(timespec="seconds"),
    }
    erros = ficha.validar(respostas)
    if erros:
        st.error("Faltou pouco. Confira:\n\n" + "\n".join(f"- {e}" for e in erros), icon=":material/error:")
    else:
        ok, resultado = dados.gravar(ficha.salvar, respostas)
        if not ok:
            st.error(resultado)
        else:
            eventos.registrar("ficha_enviada", "ficha", resultado["situacao"])
            if resultado["propriedade_id"] is not None:  # main.py troca a propriedade antes de desenhar o menu
                st.session_state["_trocar_propriedade"] = resultado["propriedade_id"]
            st.session_state["_ficha_ok"] = resultado
            st.rerun()

ui.fonte("As respostas ficam só no banco privado do SafraViva, protegidas por senha. Não vão para o GitHub.")
