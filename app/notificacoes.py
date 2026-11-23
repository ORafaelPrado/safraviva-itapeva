"""Geração e publicação de alertas (central de alertas do SafraViva).

    gerar_alertas(con, propriedade_id)  → lista de AlertaNovo (o que está acontecendo agora)
    CanalSistema().publicar(con, alertas, propriedade_id) → grava/atualiza/resolve em notif.alerta

O envio fica separado por canal: hoje só o painel (CanalSistema). O WhatsApp vai ser outro
canal com o mesmo método `publicar`, lendo os alertas novos ainda não enviados.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import duckdb
import pandas as pd

from app import alertas

ORDEM_NIVEL = {"info": 0, "atencao": 1, "critico": 2}


@dataclass(frozen=True)
class AlertaNovo:
    chave: str
    tema: str
    nivel: str          # critico | atencao | info
    titulo: str
    detalhe: str
    plantio_id: int | None = None


def _previsao(con) -> pd.DataFrame:
    diaria = con.execute("SELECT * FROM analytics.vw_previsao_diaria_atual ORDER BY data").df()
    diaria["data"] = pd.to_datetime(diaria["data"])
    return diaria[diaria["data"] >= pd.Timestamp(date.today())]


def gerar_alertas(con: duckdb.DuckDBPyConnection, propriedade_id: int | None,
                  estimativas: pd.DataFrame | None = None) -> list[AlertaNovo]:
    """Situações que merecem aviso agora. Só entra o que é atenção ou crítico (e 'pronta para colher')."""
    saida: list[AlertaNovo] = []
    diaria = _previsao(con)
    if not diaria.empty:
        for funcao in (alertas.alerta_geada, alertas.alerta_veranico, alertas.alerta_calor, alertas.alerta_chuva_forte):
            a = funcao(diaria)
            if a.nivel in ("critico", "atencao"):
                saida.append(AlertaNovo(f"{a.tema}|regiao", a.tema, a.nivel, a.titulo, a.detalhe))

    if propriedade_id is None:
        return saida

    # Lavouras plantadas: o tempo previsto cruzado com a fase de cada uma.
    estadio = con.execute("SELECT * FROM fazenda.vw_estadio_atual WHERE propriedade_id = ?", [propriedade_id]).df()
    for r in estadio.itertuples():
        a = alertas.alerta_lavoura(r.talhao, r.cultura, r.fase, int(r.dias_apos_plantio), diaria)
        if a.nivel in ("critico", "atencao") or r.fase == "pronta para colher":
            nivel = "info" if a.nivel == "ok" else a.nivel
            saida.append(AlertaNovo(f"lavoura|plantio:{r.plantio_id}", "lavoura", nivel, a.titulo, a.detalhe,
                                    int(r.plantio_id)))

    # Plantios planejados: a janela de risco baixo do ZARC para o solo do talhão está fechando?
    planejados = con.execute("""
        SELECT p.id, p.talhao, p.cultura, p.temporada, p.solo_ad, p.grupo_ciclo, p.data_plantio
        FROM fazenda.vw_plantio p WHERE p.propriedade_id = ? AND p.status = 'planejado'""", [propriedade_id]).df()
    for p in planejados.itertuples():
        nome_zarc = {"soja": "Soja", "trigo": "Trigo", "feijao": "Feijão", "aveia": "Aveia",
                     "milho": "Milho 2ª Safra" if p.temporada == "safrinha" else "Milho 1ª Safra"}.get(p.cultura)
        if not nome_zarc:
            continue
        j = con.execute("""
            SELECT nome_cultura, data_inicio, data_fim, nivel_risco, risco_pct FROM analytics.janela_plantio
            WHERE codigo_ibge = 3522406 AND nome_cultura = ? AND solo = ? AND ciclo = ? AND manejo = 'Sequeiro'
              AND safra = (SELECT max(safra) FROM analytics.janela_plantio WHERE nome_cultura = ?)""",
                        [nome_zarc, p.solo_ad or "AD4", p.grupo_ciclo or "Grupo II", nome_zarc]).df()
        baixo = j[(j["nivel_risco"] == "baixo") & (pd.to_datetime(j["data_fim"]) >= pd.Timestamp(date.today()))]
        if baixo.empty:
            continue
        fim = pd.Timestamp(baixo["data_fim"].max())
        dias = (fim - pd.Timestamp(date.today())).days
        previsto = pd.Timestamp(p.data_plantio) if pd.notna(p.data_plantio) else None
        if previsto is not None and previsto < pd.Timestamp(date.today()):
            saida.append(AlertaNovo(f"plantio|plantio:{p.id}", "plantio", "info",
                                    f"{nome_zarc} · {p.talhao}: plantio previsto para {previsto:%d/%m} não foi lançado",
                                    f"Se já plantou, lance o plantio em Lançar → Operação. O risco baixo do ZARC "
                                    f"({p.solo_ad}) vai até {fim:%d/%m} ({dias} dias).", int(p.id)))
        elif previsto is not None and previsto > fim:
            saida.append(AlertaNovo(f"plantio|plantio:{p.id}", "plantio", "critico",
                                    f"{nome_zarc} · {p.talhao}: plantio previsto depois da janela",
                                    f"Previsto para {previsto:%d/%m}, mas o risco baixo do ZARC ({p.solo_ad}) vai só até {fim:%d/%m}. "
                                    "Fora da janela não há cobertura do seguro rural/Proagro.", int(p.id)))
        elif dias <= 10:
            saida.append(AlertaNovo(f"plantio|plantio:{p.id}", "plantio", "atencao",
                                    f"{nome_zarc} · {p.talhao}: janela de plantio fecha em {dias} dias",
                                    f"Risco baixo do ZARC ({p.solo_ad}) até {fim:%d/%m}.", int(p.id)))

    # Estimativa de safra (balanço hídrico): produtividade provável abaixo da meta ou do ponto de equilíbrio.
    if estimativas is not None and not estimativas.empty:
        for e in estimativas.itertuples():
            if not e.usar_em_alertas:  # cultura em que o modelo hídrico não se mostrou confiável (ex.: trigo)
                continue
            if e.p50_sc_ha < e.ponto_equilibrio_sc_ha:
                nivel, msg = "critico", f"abaixo do ponto de equilíbrio ({e.ponto_equilibrio_sc_ha:.0f} sc/ha)"
            elif e.p50_sc_ha < 0.85 * e.meta_sc_ha:
                nivel, msg = "atencao", f"{100 * (1 - e.p50_sc_ha / e.meta_sc_ha):.0f}% abaixo da meta ({e.meta_sc_ha:.0f} sc/ha)"
            else:
                continue
            saida.append(AlertaNovo(f"estimativa|plantio:{e.plantio_id}", "estimativa", nivel,
                                    f"{e.rotulo}: estimativa de {e.p50_sc_ha:.0f} sc/ha".replace(".", ","),
                                    f"Pela falta de água até agora, a produtividade provável está {msg}. "
                                    f"Faixa provável: {e.p10_sc_ha:.0f} a {e.p90_sc_ha:.0f} sc/ha.", int(e.plantio_id)))
    return saida


class CanalSistema:
    """Publica na central de alertas do painel (tabela notif.alerta)."""

    def publicar(self, con: duckdb.DuckDBPyConnection, atuais: list[AlertaNovo], propriedade_id: int | None) -> dict:
        ativos = con.execute(
            "SELECT id, chave, nivel FROM notif.alerta WHERE resolvido_em IS NULL "
            "AND (propriedade_id = ? OR propriedade_id IS NULL OR ? IS NULL)", [propriedade_id, propriedade_id]
        ).df().set_index("chave")
        novos = atualizados = agravados = 0
        for a in atuais:
            if a.chave in ativos.index:
                anterior = ativos.loc[a.chave]
                piorou = ORDEM_NIVEL[a.nivel] > ORDEM_NIVEL[anterior["nivel"]]
                con.execute(
                    "UPDATE notif.alerta SET nivel = ?, titulo = ?, detalhe = ?, atualizado_em = current_timestamp"
                    + (", lido_em = NULL" if piorou else "") + " WHERE id = ?",
                    [a.nivel, a.titulo, a.detalhe, int(anterior["id"])])
                agravados += piorou
                atualizados += 1
            else:
                con.execute(
                    "INSERT INTO notif.alerta (chave, propriedade_id, plantio_id, tema, nivel, titulo, detalhe) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [a.chave, None if a.chave.endswith("|regiao") else propriedade_id, a.plantio_id, a.tema, a.nivel,
                     a.titulo, a.detalhe])
                novos += 1
        resolver = [k for k in ativos.index if k not in {a.chave for a in atuais}]
        for chave in resolver:
            con.execute("UPDATE notif.alerta SET resolvido_em = current_timestamp WHERE id = ?",
                        [int(ativos.loc[chave, "id"])])
        return {"novos": novos, "atualizados": atualizados, "agravados": agravados, "resolvidos": len(resolver)}


def marcar_lidos(con, ids: list[int]) -> None:
    if ids:
        con.execute(f"UPDATE notif.alerta SET lido_em = current_timestamp WHERE id IN ({','.join('?' * len(ids))})",
                    [int(i) for i in ids])


def atualizar_central(con, propriedade_id: int | None, estimativas: pd.DataFrame | None = None) -> dict:
    """Gera os alertas do momento e publica no painel."""
    return CanalSistema().publicar(con, gerar_alertas(con, propriedade_id, estimativas), propriedade_id)
