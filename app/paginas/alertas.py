"""Central de alertas: tudo o que merece atenção agora, do mais grave ao mais leve."""

import pandas as pd
import streamlit as st

from app import dados, notificacoes, ui
from app.alertas import Alerta

ui.titulo("Alertas", "O que pode afetar a lavoura nos próximos dias. Cada alerta some sozinho quando a situação passa.")
pid = ui.propriedade_atual()

ativos = dados.alertas_ativos(pid)
st.caption("Vêm da previsão do tempo, da fase de cada lavoura, do zoneamento (ZARC) e da estimativa de safra.")

if ativos.empty:
    st.success("Nenhum alerta agora: tempo e lavouras sem risco relevante.", icon=":material/check_circle:")
else:
    novos = ativos[ativos["novo"]]
    c1, c2 = st.columns([3, 2])
    c1.markdown(f"**{len(ativos)} ativo(s)**, {len(novos)} novo(s)")
    if len(novos) and c2.button("Marcar todos como lidos", width="stretch"):
        ok, msg = dados.gravar(notificacoes.marcar_lidos, novos["id"].tolist())
        st.rerun() if ok else st.error(msg)
    for r in ativos.itertuples():
        tema = r.tema.capitalize() + (" · NOVO" if r.novo else "")
        ui.cartao(Alerta(r.tema, r.nivel, r.titulo, r.detalhe or ""), tema)
        st.caption(f"Desde {pd.Timestamp(r.criado_em):%d/%m %Hh%M} · atualizado {pd.Timestamp(r.atualizado_em):%d/%m %Hh%M}")

resolvidos = dados.alertas_resolvidos(pid)
if not resolvidos.empty:
    with st.expander(f"Resolvidos nos últimos 14 dias ({len(resolvidos)})"):
        for r in resolvidos.itertuples():
            st.markdown(f"- ~~{r.titulo}~~ · resolvido em {pd.Timestamp(r.resolvido_em):%d/%m}")

st.divider()
st.caption("Em breve: os alertas novos também chegam no WhatsApp.")
