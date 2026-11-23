"""Componentes visuais do painel: tema Plotly, cartões de alerta e configuração de referência.

Paleta: referência validada da skill de dataviz (até 3 séries categóricas; status
com ícone + rótulo; divergente azul ↔ vermelho com meio cinza).
"""

from __future__ import annotations

import html

import plotly.graph_objects as go
import streamlit as st

from app.alertas import Alerta

SERIE = ["#2a78d6", "#eb6834", "#1baf7a"]
TEXTO, TEXTO_2, GRADE, SUPERFICIE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
NEUTRO = "#c9c8c2"
STATUS = {"critico": "#d03b3b", "atencao": "#fab219", "ok": "#0ca30c", "info": "#2a78d6"}
RISCO = {"baixo": "#0ca30c", "médio": "#fab219", "alto": "#ec835a"}

CONFIG_PLOTLY = {"displayModeBar": False, "locale": "pt-BR"}

CSS = """
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 3rem;}
h1 {font-size: 2rem !important;}
@media (max-width: 640px) {
  h1 {font-size: 1.6rem !important;}
  h3 {font-size: 1.15rem !important;}
  .block-container {padding-left: 1rem; padding-right: 1rem;}
}
.sv-card {border: 1px solid #e4e3df; border-left: 6px solid var(--sv-cor); border-radius: 10px;
          padding: 12px 14px; margin-bottom: 10px; background: #ffffff;}
.sv-card .sv-rotulo {font-size: 0.75rem; color: #52514e; text-transform: uppercase; letter-spacing: .04em;}
.sv-card .sv-titulo {font-size: 1.02rem; font-weight: 650; color: #0b0b0b; margin: 2px 0 4px;}
.sv-card .sv-detalhe {font-size: 0.9rem; color: #3a3936; line-height: 1.35;}
.sv-fonte {font-size: 0.78rem; color: #6b6a65;}
</style>
"""


def num(valor: float, casas: int = 0) -> str:
    """Número no padrão brasileiro: 1.234,5."""
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def configurar_pagina() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def cartao(alerta: Alerta, tema: str | None = None) -> None:
    """Cartão de alerta: barra lateral colorida + ícone + rótulo escrito (nunca só a cor)."""
    tema = tema or alerta.tema.capitalize()
    st.markdown(
        f"""<div class="sv-card" style="--sv-cor:{STATUS[alerta.nivel]}">
              <div class="sv-rotulo">{alerta.icone} {html.escape(tema)} · {alerta.rotulo}</div>
              <div class="sv-titulo">{html.escape(alerta.titulo)}</div>
              <div class="sv-detalhe">{html.escape(alerta.detalhe)}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def fonte(texto: str) -> None:
    st.markdown(f'<div class="sv-fonte">Fonte: {html.escape(texto)}</div>', unsafe_allow_html=True)


def layout(fig: go.Figure, titulo: str | None = None, altura: int = 340, legenda: bool = True) -> go.Figure:
    fig.update_layout(
        title=dict(text=titulo, x=0, xanchor="left", font=dict(size=15, color=TEXTO)) if titulo else None,
        height=altura,
        margin=dict(l=12, r=12, t=56 if titulo else 16, b=12),
        paper_bgcolor=SUPERFICIE,
        plot_bgcolor=SUPERFICIE,
        font=dict(family="Source Sans Pro, sans-serif", size=13, color=TEXTO_2),
        hoverlabel=dict(bgcolor="white", font_size=13, font_color=TEXTO),
        showlegend=legenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, font=dict(color=TEXTO)),
        separators=",.",
    )
    fig.update_xaxes(showgrid=False, linecolor=GRADE, tickfont=dict(color=TEXTO_2), automargin=True)
    fig.update_yaxes(gridcolor=GRADE, zeroline=False, tickfont=dict(color=TEXTO_2), automargin=True)
    return fig


def rotulos_finais(fig: go.Figure, itens: list[tuple[float, float, str, str]], y_range: tuple[float, float],
                   altura_plot_px: int = 250, folga_px: int = 16) -> None:
    """Marcador + valor no fim de cada linha, sem colisão: afasta na vertical os rótulos próximos.

    itens = [(x, y, texto, cor)]. Fixa o eixo y em y_range para converter valor em pixel com segurança.
    """
    fig.update_yaxes(range=list(y_range))
    px_por_unidade = altura_plot_px / (y_range[1] - y_range[0])
    ordenados = sorted(itens, key=lambda i: i[1])
    anterior = None
    for x, y, texto, cor in ordenados:
        pos = y * px_por_unidade
        if anterior is not None and pos - anterior < folga_px:
            pos = anterior + folga_px
        anterior = pos
        fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers", showlegend=False, hoverinfo="skip",
                                 marker=dict(color=cor, size=9, line=dict(color="white", width=2))))
        fig.add_annotation(x=x, y=y, text=texto, showarrow=False, xanchor="left", xshift=8,
                           yshift=pos - y * px_por_unidade, font=dict(color=TEXTO, size=12))


def mostrar(fig: go.Figure) -> None:
    st.plotly_chart(fig, use_container_width=True, config=CONFIG_PLOTLY, theme=None)


def referencia() -> tuple[str, str]:
    """Solo e ciclo de referência escolhidos na barra lateral (padrão: AD4, Grupo II)."""
    return st.session_state.get("solo", "AD4"), st.session_state.get("ciclo", "Grupo II")


def reais(valor: float, casas: int = 0) -> str:
    return "R$ " + num(valor, casas)


def propriedade_atual() -> int | None:
    """Propriedade escolhida no menu lateral (None se ainda não houver cadastro)."""
    return st.session_state.get("propriedade_id")


def aviso_demo(demo: bool) -> None:
    if demo:
        st.warning("**Fazenda de demonstração:** os números são fictícios (custos com base na CONAB e produtividade "
                   "coerente com o clima real). Eles vão ser trocados pelos dados reais da fazenda.", icon="🧪")


def liberar_acesso() -> bool:
    """Tela de senha do painel online. Sem a variável APP_SENHA (uso em casa), libera direto."""
    import hmac
    import os

    senha = os.getenv("APP_SENHA")
    if not senha or st.session_state.get("_acesso_liberado"):
        return True
    st.title("🌱 SafraViva Itapeva")
    st.caption("Painel da fazenda. Entre com a senha.")
    with st.form("entrar"):
        digitada = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar", type="primary", use_container_width=True):
            if hmac.compare_digest(digitada.encode(), senha.encode()):
                st.session_state["_acesso_liberado"] = True
                st.rerun()
            st.error("Senha incorreta.")
    return False
