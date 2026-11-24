"""Hoje na lavoura: o resumo que o produtor abre de manhã.

Primeira dobra (docs/design/passo-2-secao-principal.md): veredito do dia, três números e duas ações.
Três versões de texto para teste A/B, sorteadas por sessão ou forçadas pelo link (?v=A, ?v=B, ?v=C).
"""

import random
from datetime import date

import pandas as pd
import streamlit as st

from app import alertas, dados, eventos, ui

VERSOES = ("A", "B", "C")  # A = veredito direto · B = pergunta e resposta · C = conversa

hoje = date.today()
agora = pd.Timestamp.now()
pedida = str(st.query_params.get("v", "")).upper()
if pedida in VERSOES:
    st.session_state["_versao_heroi"] = pedida
versao = st.session_state.setdefault("_versao_heroi", random.choice(VERSOES))

diaria, horaria = dados.previsao_diaria(), dados.previsao_horaria()
pid = ui.propriedade_atual()
lavouras = dados.estadio(pid) if pid is not None else None
emitida = dados.ultima_atualizacao()
emitida = None if emitida is None or pd.isna(emitida) else pd.Timestamp(emitida)


def _numero_chuva(quando: str) -> tuple[str, str, str]:
    alvo = agora.normalize() + pd.Timedelta(days=1 if quando == "amanhã" else 0)
    dia = diaria[diaria["data"].dt.normalize() == alvo]
    if dia.empty:
        return (f"Chuva {quando}", "—", "sem previsão")
    r = dia.iloc[0]
    return (f"Chuva {quando}", f"{ui.num(r.chuva_mm, 1 if r.chuva_mm < 10 else 0)} mm",
            f"{r.prob_chuva_pct:.0f}% de chance · Open-Meteo")


def _numero_soja() -> tuple[str, str, str]:
    cot = dados.cotacao_resumo()
    linha = cot[cot["serie"] == "cepea_soja_parana"]
    if linha.empty:
        return ("Soja hoje", "—", "sem cotação no banco")
    r = linha.iloc[0]
    variacao = ""
    if pd.notna(r.variacao_pct):
        classe, seta = ("sv-sobe", "▲") if r.variacao_pct >= 0 else ("sv-desce", "▼")
        variacao = f'<span class="{classe}">{seta} {ui.num(abs(r.variacao_pct), 1)}%</span> · '
    return ("Soja (saca 60 kg)", ui.reais(r.valor, 2), f"{variacao}CEPEA Paraná · {pd.Timestamp(r.data):%d/%m}")


def _numero_lavoura() -> tuple[str, str, str]:
    if lavouras is None or lavouras.empty:
        return ("Minha lavoura", "—", "Cadastre em Lançar")
    r = lavouras.sort_values("area_ha", ascending=False).iloc[0]
    demo = " · demonstração" if bool(r.demo) else ""
    fase = (r.fase or "sem fase").capitalize()
    return (f"{r.cultura.capitalize()} · {r.talhao}", fase,
            f"{int(r.dias_apos_plantio)} dias de plantada · {ui.num(r.area_ha)} ha{demo}")


# ---------------------------------------------------------------- primeira dobra
if diaria.empty:
    st.title("Hoje na lavoura")
    st.warning("Ainda não há previsão no banco. Toque em **Atualizar previsão** no fim da página.")
else:
    v = alertas.veredito_do_dia(diaria, horaria, agora)
    saudacao = "Bom dia" if agora.hour < 12 else "Boa tarde" if agora.hour < 18 else "Boa noite"
    titulo, resposta = {
        "A": (v.frase, None),
        "B": (f"{v.quando.capitalize()} dá para entrar na lavoura?", f"{v.resposta}. {v.frase}."),
        "C": (f"{saudacao}! {v.frase}.", None),
    }[versao]
    sobre = f"Itapeva-SP · {alertas.dia_curto(hoje)}"
    if emitida is not None:
        sobre += f" · previsão das {pd.Timestamp(emitida):%Hh%M}"
    ui.heroi(sobre, v.nivel, v.rotulo, titulo, v.apoio,
             [_numero_chuva(v.quando), _numero_soja(), _numero_lavoura()], resposta)
    eventos.registrar_uma_vez("ab_view", "inicio", f"v={versao}")

    c1, c2 = st.columns(2)
    if c1.button("Perguntar ao agrônomo", type="primary", icon=":material/forum:", width="stretch"):
        eventos.registrar("cta_click", "inicio", f"agronomo|v={versao}")
        st.switch_page("paginas/agronomo.py")
    if c2.button("Previsão hora a hora", icon=":material/schedule:", width="stretch"):
        eventos.registrar("cta_click", "inicio", f"previsao|v={versao}")
        st.switch_page("paginas/clima.py")

# ---------------------------------------------------------------- detalhe (depois da rolagem)
alertas_novos = dados.alertas_ativos(pid)
if not alertas_novos.empty:
    alertas_novos = alertas_novos[alertas_novos["novo"] & alertas_novos["nivel"].isin(["critico", "atencao"])]
if not alertas_novos.empty:
    graves = (alertas_novos["nivel"] == "critico").sum()
    with st.container(border=True):
        st.markdown(f"**{len(alertas_novos)} alerta(s) novo(s)**" + (f" · {graves} com atenção alta" if graves else ""))
        for r in alertas_novos.head(3).itertuples():
            st.markdown(f"{'🔴' if r.nivel == 'critico' else '🟡'} {r.titulo}")
        st.page_link("paginas/alertas.py", label="Ver todos os alertas", icon=":material/arrow_forward:")

if not diaria.empty:
    st.subheader("Tempo nos próximos dias")
    for alerta in (
        alertas.alerta_geada(diaria),
        alertas.alerta_veranico(diaria),
        alertas.alerta_calor(diaria),
        alertas.alerta_chuva_forte(diaria),
    ):
        ui.cartao(alerta)

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
        width="stretch",
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
col1, col2 = st.columns([3, 2])
col1.caption(
    f"Previsão Open-Meteo emitida em {pd.Timestamp(emitida):%d/%m às %Hh%M}." if emitida is not None else "Sem previsão."
)
if col2.button("Atualizar previsão", icon=":material/refresh:", width="stretch"):
    with st.spinner("Buscando a previsão mais recente..."):
        dados.atualizar_previsao()
    st.rerun()
ui.fonte("Open-Meteo (previsão), CEPEA/ESALQ (preço), MAPA/ZARC 2026/27 (plantio). "
         "Os alertas são orientação, não substituem o agrônomo.")
