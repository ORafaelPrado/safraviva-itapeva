"""Resultados da safra: custo, produtividade, ponto de equilíbrio e margem de cada talhão."""

import plotly.graph_objects as go
import streamlit as st

from app import dados, gestao, ui

ui.titulo("Resultados da safra", "Quanto custou cada saca, quanto sobra e quanto precisa colher para empatar.")
pid = ui.propriedade_atual()

if pid is None:
    st.info("Nenhuma fazenda cadastrada ainda. Os dados reais vão entrar pelo formulário do produtor; "
            "até lá, dá para ver a gestão funcionando com uma fazenda de exemplo.")
    if st.button("Ver com uma fazenda de exemplo", type="primary", icon=":material/science:"):
        from scripts.carregar_demo import carregar

        ok, msg = dados.gravar(carregar)
        st.rerun() if ok else st.error(msg)
    st.stop()

props = dados.propriedades().set_index("id")
demo = bool(props.loc[pid, "demo"])
ui.aviso_demo(demo)

r = dados.resultado(pid)
if r.empty:
    st.info("Nenhum plantio cadastrado. Use **Lançar → Cadastro** para criar talhões e plantios.")
    st.stop()

safras = r["safra"].drop_duplicates().tolist()
safra = st.segmented_control("Safra (ano agrícola, jul→jun)", safras, default=safras[0]) or safras[0]
rs = r[r["safra"] == safra].copy()

# --- Resumo da safra ------------------------------------------------------------------------------
area = rs["area_ha"].sum()
custo = rs["custo_previsto"].sum()
receita = rs["receita"].sum()
margem = rs["margem_prevista"].sum()
em_andamento = (~rs["status"].isin(["colhido", "perdido"])).any()
c1, c2 = st.columns(2)
c1.metric("Área plantada" + (" (soma das temporadas)" if rs["temporada"].nunique() > 1 else ""), f"{ui.num(area)} ha")
c2.metric(("Custo previsto" if em_andamento else "Custo") + f" · {ui.reais(custo / area)}/ha", ui.reais(custo))
c3, c4 = st.columns(2)
c3.metric("Receita" + (" estimada" if rs["receita_estimada"].any() else ""), ui.reais(receita))
c4.metric(("Margem prevista" if em_andamento else "Margem") + f" · {ui.reais(margem / area)}/ha",
          ui.reais(margem))
if em_andamento:
    st.caption("Lavouras em andamento: a receita usa a meta de produtividade e o preço de referência; o custo previsto é "
               "o maior entre o já lançado e o custo de referência da CONAB.")

# --- Produtividade × ponto de equilíbrio -------------------------------------------------------------
st.subheader("Quanto colheu × quanto precisava colher")
rs["rotulo"] = rs["cultura"].map(gestao.CULTURAS) + " · " + rs["talhao"]
prod = rs["produtividade_sc_ha"].fillna(rs["produtividade_meta_sc_ha"])
colhido = rs["produtividade_sc_ha"].notna()
fig = go.Figure()
fig.add_trace(go.Bar(
    y=rs["rotulo"], x=prod, orientation="h", name="Produtividade (colhida ou meta)",
    marker=dict(color=[ui.SERIE[0] if c else "#9ec5f4" for c in colhido], line=dict(width=0)),
    text=[f"{ui.num(v, 1)} sc/ha" + ("" if c else " (meta)") for v, c in zip(prod, colhido)],
    textposition="outside", textfont=dict(color=ui.TEXTO, size=12), cliponaxis=False,
    hovertemplate="%{y}<br>%{x:.1f} sc/ha<extra></extra>",
))
fig.add_trace(go.Scatter(
    y=rs["rotulo"], x=rs["ponto_equilibrio_sc_ha"], mode="markers", name="Ponto de equilíbrio",
    marker=dict(symbol="line-ns", size=26, line=dict(color=ui.TEXTO, width=3)),
    hovertemplate="%{y}<br>Precisa de %{x:.1f} sc/ha para pagar o custo<extra></extra>",
))
fig.update_yaxes(autorange="reversed", showgrid=False)
fig.update_xaxes(ticksuffix=" sc", gridcolor=ui.GRADE, showgrid=True, range=[0, prod.max() * 1.55])
ui.layout(fig, None, 90 + 52 * len(rs))
fig.update_layout(legend=dict(orientation="h", y=-0.12, yanchor="top"), bargap=0.35)
ui.mostrar(fig)
st.caption("A barra mostra o que o talhão rendeu (ou a meta, em azul-claro). O traço preto é o ponto de equilíbrio: "
           "quantas sacas por hectare pagam o custo. A distância entre os dois é o lucro por hectare.")

# --- Tabela por talhão ---------------------------------------------------------------------------------
tabela = rs.assign(
    margem_ha=rs["margem_prevista"] / rs["area_ha"],
    custo_ha_prev=rs["custo_previsto"] / rs["area_ha"],
)[["rotulo", "status", "area_ha", "custo_ha_prev", "produtividade_sc_ha", "ponto_equilibrio_sc_ha", "preco_sc", "margem_ha"]]
st.dataframe(
    tabela, hide_index=True, width="stretch",
    column_config={
        "rotulo": "Lavoura", "status": "Situação",
        "area_ha": st.column_config.NumberColumn("Área (ha)", format="%.0f"),
        "custo_ha_prev": st.column_config.NumberColumn("Custo R$/ha", format="%.0f"),
        "produtividade_sc_ha": st.column_config.NumberColumn("Colheu sc/ha", format="%.1f"),
        "ponto_equilibrio_sc_ha": st.column_config.NumberColumn("Equilíbrio sc/ha", format="%.1f"),
        "preco_sc": st.column_config.NumberColumn("Preço R$/sc", format="%.2f"),
        "margem_ha": st.column_config.NumberColumn("Margem R$/ha", format="%.0f"),
    },
)

# --- Comparação com a região -------------------------------------------------------------------------------
st.subheader("Comparado com a região")
regiao = dados.produtividade_municipal().set_index("cultura")["itapeva_sc_ha"]
conab = dados.referencia_conab().set_index("cultura")
for cultura, grupo in rs[rs["produtividade_sc_ha"].notna()].groupby("cultura"):
    minha = (grupo["sacas"].sum() / grupo["area_ha"].sum())
    cols = st.columns(3)
    cols[0].metric(f"{gestao.CULTURAS[cultura]}: fazenda", f"{ui.num(minha, 1)} sc/ha")
    if cultura in regiao:
        cols[1].metric("Itapeva (IBGE, 5 anos)", f"{ui.num(regiao[cultura], 1)} sc/ha",
                       f"{100 * (minha / regiao[cultura] - 1):+.0f}%")
    if cultura in conab.index:
        ref = conab.loc[cultura]
        cols[2].metric(f"CONAB ({ref['local'].split('-')[0]})", f"{ui.num(ref['produtividade_sc_ha'], 1)} sc/ha",
                       f"{100 * (minha / ref['produtividade_sc_ha'] - 1):+.0f}%")

# --- Custo por categoria × CONAB --------------------------------------------------------------------------------
culturas_safra = rs["cultura"].unique().tolist()
cultura_custo = st.segmented_control("Custo por categoria", culturas_safra, default=culturas_safra[0],
                                     format_func=gestao.CULTURAS.get, key="cultura_custo") or culturas_safra[0]
cat = dados.custo_por_categoria(pid, safra, cultura_custo)
if not cat.empty:
    cat = cat.sort_values("fazenda_ha")
    nomes = cat["categoria"].map(lambda c: gestao.CATEGORIAS.get(c, c).split(" (")[0])
    fig = go.Figure()
    fig.add_trace(go.Bar(y=nomes, x=cat["conab_ha"], orientation="h", name="Referência CONAB", marker_color=ui.NEUTRO,
                         hovertemplate="CONAB: R$ %{x:,.0f}/ha<extra></extra>"))
    fig.add_trace(go.Bar(y=nomes, x=cat["fazenda_ha"], orientation="h", name="Fazenda", marker_color=ui.SERIE[0],
                         hovertemplate="Fazenda: R$ %{x:,.0f}/ha<extra></extra>"))
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.05)
    fig.update_xaxes(tickprefix="R$ ", gridcolor=ui.GRADE, showgrid=True)
    fig.update_yaxes(showgrid=False)
    ui.mostrar(ui.layout(fig, "R$ por hectare", 120 + 34 * len(cat)))
    ref = conab.loc[cultura_custo] if cultura_custo in conab.index else None
    if ref is not None:
        ui.fonte(f"CONAB, custo de produção {ref['local']} ({ref['mes_referencia']:%m/%Y}), sem arrendamento. "
                 "A fazenda inclui custos ainda em lançamento nas lavouras em andamento.")

# --- Vendas -------------------------------------------------------------------------------------------------------
v = dados.vendas(pid)
v = v[v["safra"] == safra]
if not v.empty:
    st.subheader("Vendas")
    for cultura, g in v.groupby("cultura"):
        preco_medio = (g["sacas"] * g["preco_sc"]).sum() / g["sacas"].sum()
        colhidas = rs.loc[rs["cultura"] == cultura, "sacas"].sum()
        st.markdown(f"**{gestao.CULTURAS[cultura]}:** {ui.num(g['sacas'].sum())} sc vendidas de {ui.num(colhidas)} colhidas, "
                    f"preço médio {ui.reais(preco_medio, 2)}/sc.")
    st.dataframe(v[["data", "cultura", "sacas", "preco_sc", "comprador"]], hide_index=True, width="stretch",
                 column_config={"data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                                "cultura": "Cultura", "sacas": st.column_config.NumberColumn("Sacas", format="%.0f"),
                                "preco_sc": st.column_config.NumberColumn("R$/sc", format="%.2f"), "comprador": "Comprador"})

if demo:
    st.divider()
    if st.button("Apagar a fazenda de exemplo", icon=":material/delete:"):
        ok, msg = dados.gravar(gestao.remover_demonstracao)
        st.rerun() if ok else st.error(msg)
