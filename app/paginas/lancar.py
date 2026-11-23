"""Lançamentos rápidos: operação, despesa, colheita, venda, ocorrência, cadastro e preços.

Pensado para o celular: poucos campos, valores já preenchidos e linguagem de produtor.
"""

from datetime import date

import streamlit as st

from app import dados, gestao, ui

st.title("✍️ Lançar")
pid = ui.propriedade_atual()

if pid is None:
    st.info("Cadastre a propriedade para começar.")
    with st.form("nova_propriedade"):
        nome = st.text_input("Nome da propriedade")
        if st.form_submit_button("Criar propriedade", type="primary") and nome.strip():
            ok, msg = dados.gravar(gestao.criar_propriedade, nome.strip())
            st.rerun() if ok else st.error(msg)
    st.stop()

ui.aviso_demo(bool(dados.propriedades().set_index("id").loc[pid, "demo"]))
plantios = dados.plantios(pid)
talhoes = dados.talhoes(pid)


def rotulo_plantio(row) -> str:
    return f"{gestao.CULTURAS.get(row.cultura, row.cultura)} · {row.talhao} · {row.safra}"


abertos = plantios[plantios["status"].isin(["planejado", "plantado"])]
opcoes_abertos = {int(r.id): rotulo_plantio(r) for r in abertos.itertuples()}
opcoes_todos = {int(r.id): rotulo_plantio(r) + f" ({r.status})" for r in plantios.itertuples()}


def sucesso(ok: bool, msg, texto: str) -> None:
    if ok:
        st.success(texto)
    else:
        st.error(msg)


CATEGORIA_PADRAO = {"plantio": "semente", "adubacao": "fertilizante", "pulverizacao": "defensivo",
                    "preparo": "defensivo", "colheita": "maquinas", "transporte": "frete", "outro": "outros"}

aba_op, aba_desp, aba_col, aba_venda, aba_oc, aba_cad, aba_preco = st.tabs(
    ["Operação", "Despesa", "Colheita", "Venda", "Ocorrência", "Cadastro", "Preços"])

# --- Operação (caderno de campo) --------------------------------------------------------------------
with aba_op:
    if not opcoes_abertos:
        st.info("Nenhuma lavoura aberta. Cadastre um plantio na aba **Cadastro**.")
    else:
        tipo = st.selectbox("O que foi feito?", list(gestao.TIPOS_OPERACAO), format_func=gestao.TIPOS_OPERACAO.get)
        with st.form("operacao", clear_on_submit=True):
            plantio_id = st.selectbox("Lavoura", list(opcoes_abertos), format_func=opcoes_abertos.get)
            quando = st.date_input("Data", date.today(), format="DD/MM/YYYY")
            produto = st.text_input("Produto / máquina", placeholder="ex.: glifosato, adubo 02-20-20, colhedora")
            c1, c2 = st.columns(2)
            dose = c1.number_input("Dose", min_value=0.0, step=0.1, value=None)
            unidade = c2.selectbox("Unidade", ["L/ha", "kg/ha", "sc/ha", "mL/ha", "t/ha", "un"])
            custo = st.number_input("Custo total (R$)", min_value=0.0, step=100.0, value=None,
                                    help="Deixe vazio se o custo já foi lançado como despesa (ex.: produto comprado antes).")
            categoria = st.selectbox("Categoria do custo", list(gestao.CATEGORIAS), format_func=gestao.CATEGORIAS.get,
                                     index=list(gestao.CATEGORIAS).index(CATEGORIA_PADRAO[tipo]))
            obs = st.text_input("Observação")
            if st.form_submit_button("Salvar operação", type="primary", use_container_width=True):
                ok, msg = dados.gravar(gestao.registrar_operacao, plantio_id, quando, tipo, produto=produto or None,
                                       dose=dose, unidade=unidade if dose else None, custo_total=custo,
                                       categoria_custo=categoria if custo else None, observacao=obs or None)
                sucesso(ok, msg, f"{gestao.TIPOS_OPERACAO[tipo]} salva em {opcoes_abertos[plantio_id]}.")

# --- Despesa -------------------------------------------------------------------------------------------
with aba_desp:
    with st.form("despesa", clear_on_submit=True):
        categoria = st.selectbox("Tipo de despesa", list(gestao.CATEGORIAS), format_func=gestao.CATEGORIAS.get)
        valor = st.number_input("Valor (R$)", min_value=0.0, step=100.0, value=None)
        quando = st.date_input("Data", date.today(), format="DD/MM/YYYY", key="data_despesa")
        destino = st.selectbox("De qual lavoura?", [None] + list(opcoes_todos),
                               format_func=lambda k: "Propriedade toda (dividir pela área da safra)" if k is None else opcoes_todos[k])
        descricao = st.text_input("Descrição", placeholder="ex.: seguro agrícola, honorário do agrônomo")
        if st.form_submit_button("Salvar despesa", type="primary", use_container_width=True):
            if not valor:
                st.error("Informe o valor.")
            else:
                safra = plantios.set_index("id").loc[destino, "safra"] if destino else gestao.safra_de(quando)
                ok, msg = dados.gravar(gestao.registrar_custo, pid, quando, categoria, valor,
                                       descricao=descricao or None, plantio_id=destino, safra=safra)
                sucesso(ok, msg, f"Despesa de {ui.reais(valor, 2)} salva.")

# --- Colheita -------------------------------------------------------------------------------------------
with aba_col:
    plantados = {k: v for k, v in opcoes_abertos.items() if plantios.set_index("id").loc[k, "status"] == "plantado"}
    if not plantados:
        st.info("Nenhuma lavoura plantada esperando colheita.")
    else:
        with st.form("colheita", clear_on_submit=True):
            plantio_id = st.selectbox("Lavoura", list(plantados), format_func=plantados.get)
            quando = st.date_input("Data", date.today(), format="DD/MM/YYYY", key="data_colheita")
            sacas = st.number_input("Sacas de 60 kg (já descontadas umidade e impureza)", min_value=0.0, step=10.0, value=None)
            area_col = st.number_input("Área colhida (ha)", min_value=0.0, step=1.0, value=None,
                                       help="Vazio = área toda do plantio.")
            c1, c2 = st.columns(2)
            umidade = c1.number_input("Umidade (%)", min_value=0.0, max_value=40.0, value=None)
            impureza = c2.number_input("Impureza (%)", min_value=0.0, max_value=20.0, value=None)
            terminou = st.checkbox("Terminou de colher esta lavoura", value=True)
            if st.form_submit_button("Salvar colheita", type="primary", use_container_width=True):
                if not sacas:
                    st.error("Informe as sacas colhidas.")
                else:
                    ok, msg = dados.gravar(gestao.registrar_colheita, plantio_id, quando, sacas, area_colhida_ha=area_col,
                                           umidade_pct=umidade, impureza_pct=impureza, finalizar=terminou)
                    sucesso(ok, msg, f"Colheita de {ui.num(sacas)} sacas salva.")

# --- Venda -----------------------------------------------------------------------------------------------
with aba_venda:
    with st.form("venda", clear_on_submit=True):
        c1, c2 = st.columns(2)
        cultura = c1.selectbox("Cultura", list(gestao.CULTURAS), format_func=gestao.CULTURAS.get)
        safras = sorted(plantios["safra"].unique().tolist(), reverse=True) or [gestao.safra_de(date.today())]
        safra = c2.selectbox("Safra", safras)
        quando = st.date_input("Data", date.today(), format="DD/MM/YYYY", key="data_venda")
        c3, c4 = st.columns(2)
        sacas = c3.number_input("Sacas", min_value=0.0, step=10.0, value=None)
        preco = c4.number_input("Preço (R$/saca)", min_value=0.0, step=0.5, value=None)
        comprador = st.text_input("Comprador")
        if st.form_submit_button("Salvar venda", type="primary", use_container_width=True):
            if not sacas or not preco:
                st.error("Informe sacas e preço.")
            else:
                ok, msg = dados.gravar(gestao.registrar_venda, pid, cultura, safra, quando, sacas, preco, comprador or None)
                sucesso(ok, msg, f"Venda de {ui.num(sacas)} sc a {ui.reais(preco, 2)} salva ({ui.reais(sacas * preco)}).")

# --- Ocorrência ---------------------------------------------------------------------------------------------
with aba_oc:
    if not opcoes_todos:
        st.info("Cadastre um plantio primeiro.")
    else:
        with st.form("ocorrencia", clear_on_submit=True):
            plantio_id = st.selectbox("Lavoura", list(opcoes_todos), format_func=opcoes_todos.get, key="oc_plantio")
            quando = st.date_input("Data", date.today(), format="DD/MM/YYYY", key="data_oc")
            tipo = st.selectbox("O que aconteceu?", list(gestao.TIPOS_OCORRENCIA), format_func=gestao.TIPOS_OCORRENCIA.get)
            severidade = st.radio("Gravidade", [1, 2, 3], horizontal=True,
                                  format_func={1: "Leve", 2: "Moderada", 3: "Severa"}.get)
            descricao = st.text_area("Descrição", placeholder="ex.: lagarta na bordadura, 2 por metro")
            if st.form_submit_button("Salvar ocorrência", type="primary", use_container_width=True):
                ok, msg = dados.gravar(gestao.registrar_ocorrencia, plantio_id, quando, tipo, severidade, descricao or None)
                sucesso(ok, msg, "Ocorrência salva.")

# --- Cadastro: talhão e plantio ---------------------------------------------------------------------------------
with aba_cad:
    st.markdown("**Novo talhão**")
    with st.form("talhao", clear_on_submit=True):
        nome = st.text_input("Nome do talhão", placeholder="ex.: Chapada, Sede, Fundo")
        c1, c2 = st.columns(2)
        area = c1.number_input("Área (ha)", min_value=0.0, step=1.0, value=None)
        solo = c2.selectbox("Solo (água disponível)", gestao.SOLOS, index=3,
                            help="AD1 = arenoso, seca rápido · AD6 = argiloso profundo. Na dúvida, use a análise de textura.")
        if st.form_submit_button("Salvar talhão", use_container_width=True):
            if not nome.strip() or not area:
                st.error("Informe nome e área.")
            else:
                ok, msg = dados.gravar(gestao.criar_talhao, pid, nome.strip(), area, solo)
                sucesso(ok, msg, f"Talhão {nome} ({ui.num(area)} ha) salvo.")

    st.markdown("**Novo plantio**")
    if talhoes.empty:
        st.info("Cadastre um talhão primeiro.")
    else:
        opcoes_talhao = {int(r.id): f"{r.nome} ({ui.num(r.area_ha)} ha, {r.solo_ad})" for r in talhoes.itertuples()}
        with st.form("plantio", clear_on_submit=True):
            talhao_id = st.selectbox("Talhão", list(opcoes_talhao), format_func=opcoes_talhao.get)
            c1, c2 = st.columns(2)
            cultura = c1.selectbox("Cultura", list(gestao.CULTURAS), format_func=gestao.CULTURAS.get, key="cad_cultura")
            temporada = c2.selectbox("Temporada", list(gestao.TEMPORADAS), format_func=gestao.TEMPORADAS.get)
            data_plantio = st.date_input("Data do plantio (ou prevista)", date.today(), format="DD/MM/YYYY")
            c3, c4 = st.columns(2)
            cultivar = c3.text_input("Cultivar")
            grupo = c4.selectbox("Ciclo", ["Grupo I", "Grupo II", "Grupo III"], index=1)
            meta = st.number_input("Meta de produtividade (sc/ha)", min_value=0.0, step=1.0, value=None)
            if st.form_submit_button("Salvar plantio", use_container_width=True):
                ok, msg = dados.gravar(gestao.criar_plantio, talhao_id, cultura, temporada, data_plantio,
                                       cultivar=cultivar or None, grupo_ciclo=grupo, produtividade_meta_sc_ha=meta)
                sucesso(ok, msg, f"Plantio de {gestao.CULTURAS[cultura]} salvo (safra {gestao.safra_de(data_plantio)}).")

# --- Preços de referência ----------------------------------------------------------------------------------------
with aba_preco:
    st.caption("Usados para estimar a receita das sacas ainda não vendidas. Atualize quando quiser.")
    precos = dados.precos_referencia()
    st.dataframe(precos, hide_index=True, use_container_width=True,
                 column_config={"cultura": "Cultura", "preco_sc": st.column_config.NumberColumn("R$/saca", format="%.2f"),
                                "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"), "fonte": "Fonte"})
    with st.form("preco"):
        c1, c2 = st.columns(2)
        cultura = c1.selectbox("Cultura", list(gestao.CULTURAS), format_func=gestao.CULTURAS.get, key="preco_cultura")
        preco = c2.number_input("R$/saca", min_value=0.0, step=0.5, value=None)
        fonte = st.text_input("Fonte", value="Cotação local")
        if st.form_submit_button("Atualizar preço", use_container_width=True) and preco:
            ok, msg = dados.gravar(gestao.atualizar_preco, cultura, preco, date.today(), fonte)
            sucesso(ok, msg, "Preço atualizado.")
