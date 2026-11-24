"""SafraViva Itapeva — painel.

    streamlit run app/main.py

Para abrir no celular na mesma rede Wi-Fi, use o endereço "Network URL" que o Streamlit mostra.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import streamlit as st  # noqa: E402

from app import dados, eventos, ui  # noqa: E402

st.set_page_config(page_title="SafraViva Itapeva", page_icon=str(ui.ICONE), layout="centered")
ui.configurar_pagina()

# Painel online: pede a senha (segredo APP_SENHA no Streamlit Cloud). Em casa, sem a variável, não pede.
if not ui.liberar_acesso():
    st.stop()
st.logo(str(ui.LOGO), icon_image=str(ui.ICONE), size="large")

PAGINAS = RAIZ / "app" / "paginas"

# Previsão com mais de 6 h: atualiza previsão + alertas antes de desenhar (uma vez por sessão).
_falha = dados.atualizar_se_preciso()
if _falha:
    st.toast(f"Não deu para atualizar a previsão agora: {_falha}", icon="⚠️")
_alertas = dados.alertas_ativos(st.session_state.get("propriedade_id"))
NOVOS = int(_alertas["novo"].sum()) if not _alertas.empty else 0
# Menu no topo (no celular vira um botão sempre visível), por pergunta do produtor (plano mestre, seção 7).
navegacao = st.navigation(
    {
        "Hoje": [
            st.Page(PAGINAS / "inicio.py", title="Hoje na lavoura", icon=":material/wb_sunny:", default=True),
            st.Page(PAGINAS / "alertas.py", title=f"Alertas{f' ({NOVOS})' if NOVOS else ''}",
                    icon=":material/notifications:"),
        ],
        "Tempo e plantio": [
            st.Page(PAGINAS / "clima.py", title="Previsão do tempo", icon=":material/partly_cloudy_day:"),
            st.Page(PAGINAS / "plantio.py", title="Janela de plantio", icon=":material/calendar_month:"),
        ],
        "Mercado": [
            st.Page(PAGINAS / "cotacoes.py", title="Cotações", icon=":material/trending_up:"),
        ],
        "Minha fazenda": [
            st.Page(PAGINAS / "estimativa.py", title="Estimativa de safra", icon=":material/grass:"),
            st.Page(PAGINAS / "fazenda.py", title="Resultados da safra", icon=":material/payments:"),
            st.Page(PAGINAS / "lancar.py", title="Lançar", icon=":material/edit_note:"),
            st.Page(PAGINAS / "caderno.py", title="Caderno de campo", icon=":material/menu_book:"),
        ],
        "Agrônomo": [
            st.Page(PAGINAS / "agronomo.py", title="Agrônomo Digital", icon=":material/forum:"),
        ],
        "Região": [
            st.Page(PAGINAS / "producao.py", title="Produção regional", icon=":material/bar_chart:"),
            st.Page(PAGINAS / "safras.py", title="Clima e safras", icon=":material/query_stats:"),
        ],
    },
    position="top",
)

with st.sidebar:
    props = dados.propriedades()
    if not props.empty:
        rotulos = {int(r.id): r.nome for r in props.itertuples()}
        if st.session_state.get("propriedade_id") not in rotulos:  # propriedade apagada (ex.: demonstração removida)
            st.session_state.pop("propriedade_id", None)
        st.selectbox("Propriedade", list(rotulos), format_func=rotulos.get, key="propriedade_id")
    else:
        st.session_state["propriedade_id"] = None
    st.markdown("### Referência")
    opcoes = dados.opcoes_zarc()
    st.selectbox(
        "Solo (água disponível)",
        opcoes["solos"],
        index=opcoes["solos"].index("AD4") if "AD4" in opcoes["solos"] else 0,
        key="solo",
        help="AD1 = solo arenoso, segura pouca água. AD6 = solo argiloso profundo, segura muita água. "
        "Os latossolos argilosos das chapadas de Itapeva ficam em geral entre AD4 e AD6.",
    )
    st.selectbox(
        "Ciclo da cultivar",
        opcoes["ciclos"],
        index=opcoes["ciclos"].index("Grupo II") if "Grupo II" in opcoes["ciclos"] else 0,
        key="ciclo",
        help="Grupo I = ciclo curto (precoce); Grupo III = ciclo longo (tardio).",
    )
    st.caption(
        "Local: centro de Itapeva-SP. Enquanto não houver os dados da fazenda, "
        "o painel usa a referência regional (ZARC, INMET, IBGE)."
    )

navegacao.run()

# Medição (uso.evento): grava depois que a tela já foi desenhada.
eventos.registrar("pagina_vista", navegacao.url_path or "inicio")
eventos.enviar()
