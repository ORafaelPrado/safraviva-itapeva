"""Hoje na lavoura: o resumo que o produtor abre de manhã."""

from datetime import date

import pandas as pd
import streamlit as st

from app import alertas, dados, ui

hoje = date.today()
st.title("🌱 Hoje na lavoura")
st.caption(f"Itapeva-SP · {alertas.dia_curto(hoje)} de {hoje:%Y}")

alertas_novos = dados.alertas_ativos(ui.propriedade_atual())
if not alertas_novos.empty:
    alertas_novos = alertas_novos[alertas_novos["novo"] & alertas_novos["nivel"].isin(["critico", "atencao"])]
if not alertas_novos.empty:
    graves = (alertas_novos["nivel"] == "critico").sum()
    with st.container(border=True):
        st.markdown(f"**🔔 {len(alertas_novos)} alerta(s) novo(s)**" + (f" · {graves} com atenção alta" if graves else ""))
        for r in alertas_novos.head(3).itertuples():
            st.markdown(f"{'🔴' if r.nivel == 'critico' else '🟡'} {r.titulo}")
        st.page_link("paginas/alertas.py", label="Ver todos os alertas", icon="➡️")

diaria, horaria = dados.previsao_diaria(), dados.previsao_horaria()
if diaria.empty:
    st.warning("Ainda não há previsão no banco. Toque em **Atualizar previsão**.")
else:
    st.subheader("Tempo nos próximos dias")
    for alerta in (
        alertas.alerta_geada(diaria),
        alertas.alerta_veranico(diaria),
        alertas.alerta_calor(diaria),
        alertas.alerta_chuva_forte(diaria),
    ):
        ui.cartao(alerta)

    pid = ui.propriedade_atual()
    lavouras = dados.estadio(pid) if pid is not None else None
    if lavouras is not None and not lavouras.empty:
        st.subheader("Minhas lavouras")
        ui.aviso_demo(bool(lavouras["demo"].iloc[0]))
        for r in lavouras.itertuples():
            ui.cartao(alertas.alerta_lavoura(r.talhao, r.cultura, r.fase, int(r.dias_apos_plantio), diaria), "Lavoura")

    st.subheader("Pulverização")
    ui.cartao(alertas.alerta_pulverizacao(horaria), "Pulverização")

    st.subheader("Próximos 7 dias")
    semana = diaria.head(7).assign(
        dia=lambda d: d["data"].map(alertas.dia_curto),
        tempo=lambda d: d.apply(
            lambda r: "🌧️" if r.chuva_mm >= 10 else "🌦️" if r.chuva_mm >= 1 else "⛅" if r.prob_chuva_pct >= 30 else "☀️",
            axis=1,
        ),
    )
    st.dataframe(
        semana[["dia", "tempo", "temp_min_c", "temp_max_c", "chuva_mm", "prob_chuva_pct"]],
        hide_index=True,
        use_container_width=True,
        column_config={
            "dia": "Dia",
            "tempo": "",
            "temp_min_c": st.column_config.NumberColumn("Mín", format="%.0f°"),
            "temp_max_c": st.column_config.NumberColumn("Máx", format="%.0f°"),
            "chuva_mm": st.column_config.NumberColumn("mm", format="%.0f"),
            "prob_chuva_pct": st.column_config.NumberColumn("Chance", format="%.0f%%"),
        },
    )

solo, ciclo = ui.referencia()
st.subheader("Época de plantio (ZARC)")
st.caption(f"Referência: solo {solo}, cultivar {ciclo}, sequeiro. Troque no menu lateral.")
janelas = dados.janelas_plantio(solo, ciclo)
for cultura in ("Soja", "Milho 2ª Safra", "Trigo"):
    ui.cartao(alertas.situacao_plantio(janelas, cultura, hoje), "Plantio")

st.divider()
emitida = dados.ultima_atualizacao()
col1, col2 = st.columns([3, 2])
col1.caption(
    f"Previsão Open-Meteo emitida em {pd.Timestamp(emitida):%d/%m às %Hh%M}." if emitida is not None else "Sem previsão."
)
if col2.button("🔄 Atualizar previsão", use_container_width=True):
    with st.spinner("Buscando a previsão mais recente..."):
        dados.atualizar_previsao()
    st.rerun()
ui.fonte("Open-Meteo (previsão), MAPA/ZARC 2026/27 (plantio). Os alertas são orientação, não substituem o agrônomo.")
