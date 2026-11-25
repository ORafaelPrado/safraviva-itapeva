"""Componentes visuais do painel: tema Plotly, cartões de alerta e configuração de referência.

Paleta: referência validada da skill de dataviz (até 3 séries categóricas; status
com ícone + rótulo; divergente azul ↔ vermelho com meio cinza).
"""

from __future__ import annotations

import html
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from app.alertas import Alerta

SERIE = ["#2a78d6", "#eb6834", "#1baf7a"]
TEXTO, TEXTO_2, GRADE, SUPERFICIE = "#1B2119", "#545A50", "#E4E1D8", "#FAF8F3"  # tokens do tema
NEUTRO = "#c9c8c2"
STATUS = {"critico": "#d03b3b", "atencao": "#fab219", "ok": "#0ca30c", "info": "#2a78d6"}
RISCO = {"baixo": "#0ca30c", "médio": "#fab219", "alto": "#ec835a"}

CONFIG_PLOTLY = {"displayModeBar": False, "locale": "pt-BR"}

CSS = Path(__file__).with_name("estilo.css").read_text(encoding="utf-8")
LOGO = Path(__file__).with_name("static") / "logo.svg"
ICONE = Path(__file__).with_name("static") / "icone.svg"


def num(valor: float, casas: int = 0) -> str:
    """Número no padrão brasileiro: 1.234,5."""
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def configurar_pagina() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def titulo(texto: str, subtitulo: str) -> None:
    """Título da página (a pergunta que ela responde) + uma linha do que tem ali (docs/design/passo-4-texto.md)."""
    st.title(texto)
    st.markdown(f'<p class="sv-subtitulo">{html.escape(subtitulo)}</p>', unsafe_allow_html=True)


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
        font=dict(family="Inter, sans-serif", size=13, color=TEXTO_2),
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
    st.plotly_chart(fig, width="stretch", config=CONFIG_PLOTLY, theme=None)


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
                   "coerente com o clima real). Eles vão ser trocados pelos dados reais da fazenda.", icon=":material/science:")


def liberar_acesso() -> bool:
    """Tela de senha do painel online. Sem a variável APP_SENHA (uso em casa), libera direto."""
    import hmac
    import os

    senha = os.getenv("APP_SENHA")
    if not senha or st.session_state.get("_acesso_liberado"):
        return True
    tela_entrada()
    with st.form("entrar"):
        digitada = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar", type="primary", width="stretch", icon=":material/login:"):
            if hmac.compare_digest(digitada.encode(), senha.encode()):
                st.session_state["_acesso_liberado"] = True
                st.rerun()
            st.error("Senha incorreta.")
    return False


FATOS_PROJETO = (  # fatos verificáveis, documentados no README (nada inventado)
    "52 anos de produção do IBGE",
    "45 anos de clima diário",
    "Estimativa de safra validada contra o IBGE",
)


def _html(trecho: str) -> None:
    """HTML numa linha só: no Markdown do Streamlit, linha recuada depois de linha vazia vira bloco de código."""
    st.markdown(" ".join(linha.strip() for linha in trecho.splitlines() if linha.strip()), unsafe_allow_html=True)


def _svg_base64(caminho: Path) -> str:
    import base64

    return "data:image/svg+xml;base64," + base64.b64encode(caminho.read_bytes()).decode()


def tela_entrada() -> None:
    """Primeira tela do painel online: marca, promessa e fatos do projeto, antes da senha."""
    fatos = "".join(f"<li>{html.escape(f)}</li>" for f in FATOS_PROJETO)
    _html(
        f"""<div class="sv-entrada">
              <img src="{_svg_base64(LOGO)}" alt="SafraViva">
              <h1>Abra e saiba se hoje é dia de entrar na lavoura.</h1>
              <p>Tempo, lavoura, mercado e contas da fazenda em um só lugar, com dados de Itapeva-SP.</p>
              <ul class="sv-fatos">{fatos}</ul>
            </div>"""
    )


CORES_SELO = {  # (cor do ponto, fundo do selo): a palavra fica sempre em texto escuro (contraste >= 4,5:1)
    "ok": ("var(--sv-ok)", "var(--sv-ok-fundo)"),
    "atencao": ("var(--sv-atencao)", "var(--sv-atencao-fundo)"),
    "critico": ("var(--sv-critico)", "var(--sv-critico-fundo)"),
    "info": ("var(--sv-info)", "var(--sv-info-fundo)"),
}


def heroi(sobre: str, nivel: str, rotulo: str, titulo: str, apoio: str,
          numeros: list[tuple[str, str, str]], resposta: str | None = None) -> None:
    """Primeira dobra: selo de situação, veredito, apoio e três números (rótulo, valor, detalhe em HTML seguro)."""
    cor, fundo = CORES_SELO[nivel]
    blocos = "".join(
        f'<div class="sv-num"><div class="sv-rot">{html.escape(r)}</div>'
        f'<div class="sv-val">{html.escape(v)}</div><div class="sv-det">{d}</div></div>'
        for r, v, d in numeros
    )
    linha_resposta = f'<p class="sv-resposta">{html.escape(resposta)}</p>' if resposta else ""
    _html(
        f"""<section class="sv-heroi" aria-label="Resumo do dia">
              <div class="sv-sobre">{html.escape(sobre)}</div>
              <span class="sv-selo" style="--sv-selo-cor:{cor};--sv-selo-fundo:{fundo}">{html.escape(rotulo)}</span>
              <h2 class="sv-titulo-heroi">{html.escape(titulo)}</h2>
              {linha_resposta}
              <p class="sv-apoio">{html.escape(apoio)}</p>
              <div class="sv-numeros">{blocos}</div>
            </section>"""
    )


def ao_vivo(texto: str) -> None:
    """Indicador de dado que se atualiza sozinho: um ponto que pulsa devagar (o número nunca se mexe)."""
    st.markdown(f'<span class="sv-aovivo"><b>Ao vivo</b> · {html.escape(texto)}</span>', unsafe_allow_html=True)
