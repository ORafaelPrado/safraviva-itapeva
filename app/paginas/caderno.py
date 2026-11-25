"""Caderno de campo: tudo o que foi feito e gasto, com filtro e exportação."""

import streamlit as st

from app import dados, gestao, ui

ui.titulo("Caderno de campo", "Tudo o que foi lançado, por talhão e por data.")
pid = ui.propriedade_atual()
if pid is None:
    st.info("Nenhuma fazenda cadastrada ainda. Comece em **Lançar → Cadastro**.")
    st.stop()
ui.aviso_demo(bool(dados.propriedades().set_index("id").loc[pid, "demo"]))

c = dados.caderno(pid)
if c.empty:
    st.info("Nada lançado ainda. Anote a primeira operação em **Lançar**.")
    st.stop()

c1, c2 = st.columns(2)
safras = sorted(c["safra"].dropna().unique().tolist(), reverse=True)
safra = c1.selectbox("Safra", ["Todas"] + safras)
talhoes = sorted(c["talhao"].dropna().unique().tolist())
talhao = c2.selectbox("Talhão", ["Todos"] + talhoes)
filtro = c.copy()
if safra != "Todas":
    filtro = filtro[filtro["safra"] == safra]
if talhao != "Todos":
    filtro = filtro[filtro["talhao"] == talhao]

filtro["o_que"] = filtro["tipo"].map(
    lambda t: gestao.TIPOS_OPERACAO.get(t) or gestao.TIPOS_OCORRENCIA.get(t.replace("ocorrência: ", ""), t).join(["⚠️ ", ""])
    if t.startswith("ocorrência") else gestao.TIPOS_OPERACAO.get(t, t.capitalize()))
filtro["categoria"] = filtro["categoria_custo"].map(lambda k: gestao.CATEGORIAS.get(k, "") if k else "")
st.metric("Gasto no período filtrado", ui.reais(filtro["custo_total"].fillna(0).sum()))
st.dataframe(
    filtro[["data", "talhao", "o_que", "produto", "dose", "unidade", "custo_total", "categoria", "observacao"]],
    hide_index=True, width="stretch", height=480,
    column_config={
        "data": st.column_config.DateColumn("Data", format="DD/MM/YY"),
        "talhao": "Talhão", "o_que": "O quê", "produto": "Produto / descrição",
        "dose": st.column_config.NumberColumn("Dose", format="%.1f"), "unidade": "Un.",
        "custo_total": st.column_config.NumberColumn("R$", format="%.0f"), "categoria": "Categoria",
        "observacao": "Obs.",
    },
)
st.download_button("⬇️ Baixar caderno (CSV)", filtro.drop(columns=["o_que"]).to_csv(index=False, sep=";", decimal=",")
                   .encode("utf-8-sig"), file_name="caderno_de_campo.csv", mime="text/csv")
