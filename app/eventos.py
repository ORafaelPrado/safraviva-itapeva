"""Medição de uso do painel: página vista, versão do texto (A/B) e cliques nas chamadas principais.

Os eventos ficam numa fila da sessão e são gravados de uma vez, no fim de cada execução do
`main.py` (depois que a tela já foi desenhada), para não atrasar o que o produtor vê.
Falha ao gravar nunca quebra o painel. Nos testes, `SAFRAVIVA_SEM_EVENTOS` desliga a gravação.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime

import streamlit as st

from core import config

DDL = config.DIR_SQL / "ddl" / "011_uso.sql"
_FILA = "_eventos_pendentes"


def sessao() -> str:
    if "_sessao" not in st.session_state:
        st.session_state["_sessao"] = uuid.uuid4().hex[:12]
    return st.session_state["_sessao"]


def dispositivo() -> str:
    try:
        agente = st.context.headers.get("User-Agent", "") or ""
    except Exception:  # fora de uma requisição (ex.: testes)
        agente = ""
    return "celular" if "Mobi" in agente or "Android" in agente else "computador"


def registrar(evento: str, pagina: str | None = None, detalhe: str | None = None) -> None:
    """Põe o evento na fila da sessão (gravado por `enviar`)."""
    st.session_state.setdefault(_FILA, []).append(
        (datetime.now(), sessao(), evento, pagina, detalhe, dispositivo())
    )


def registrar_uma_vez(evento: str, pagina: str | None = None, detalhe: str | None = None) -> None:
    """Como `registrar`, mas só uma vez por sessão para a mesma combinação (ex.: ab_view)."""
    chave = f"_ev_{evento}|{pagina}|{detalhe}"
    if not st.session_state.get(chave):
        st.session_state[chave] = True
        registrar(evento, pagina, detalhe)


def gravar(con, linhas: list[tuple]) -> int:
    con.execute(DDL.read_text(encoding="utf-8"))
    con.executemany("INSERT INTO uso.evento VALUES (?, ?, ?, ?, ?, ?)", linhas)
    return len(linhas)


def enviar() -> int:
    """Grava a fila da sessão. Devolve quantos eventos foram gravados (0 se desligado ou em falha)."""
    fila = st.session_state.get(_FILA) or []
    if not fila or os.getenv("SAFRAVIVA_SEM_EVENTOS"):
        return 0
    from core.db import conectar

    try:
        with conectar() as con:
            n = gravar(con, fila)
    except Exception:  # banco ocupado ou sem rede: tenta de novo na próxima execução
        return 0
    st.session_state[_FILA] = []
    return n
