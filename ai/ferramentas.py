"""Ferramentas do Agrônomo Digital: funções que o modelo pode chamar para buscar dados reais.

Regra de ouro: o modelo nunca responde "de cabeça" quando existe dado. Cada ferramenta
consulta o banco (previsão, ZARC, IBGE, INMET, CONAB, fazenda) e devolve um dicionário
JSON com a FONTE e a DATA do dado, para a resposta poder citar de onde veio.

Ferramentas de escrita não gravam nada: `propor_lancamento` só monta um lançamento
pendente, que o produtor confirma com um toque na tela (ver ai/agente.py).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable

import duckdb
import pandas as pd

from app import alertas, gestao
from core import config
from core.db import conectar

# --------------------------------------------------------------------------------------------
# Contexto e utilitários
# --------------------------------------------------------------------------------------------


@dataclass
class Contexto:
    """O que as ferramentas sabem sobre quem pergunta: propriedade, data e lançamentos pendentes."""

    propriedade_id: int | None = None
    hoje: date = field(default_factory=date.today)
    pendentes: list[dict] = field(default_factory=list)


def _ler(sql: str, params: list | None = None) -> pd.DataFrame:
    with conectar(leitura=True) as con:
        return con.execute(sql, params or []).df()


def _registros(df: pd.DataFrame, colunas: list[str] | None = None, casas: int = 1) -> list[dict]:
    """DataFrame → lista de dicts JSON-serializáveis (datas em dd/mm/aaaa, números arredondados)."""
    if colunas:
        df = df[colunas]
    saida = []
    for linha in df.to_dict("records"):
        limpa = {}
        for k, v in linha.items():
            if v is None or (isinstance(v, float) and pd.isna(v)):
                limpa[k] = None
            elif isinstance(v, (pd.Timestamp, date)):
                limpa[k] = pd.Timestamp(v).strftime("%d/%m/%Y")
            elif isinstance(v, float):
                limpa[k] = round(v, casas)
            elif hasattr(v, "item"):  # numpy
                limpa[k] = v.item()
            else:
                limpa[k] = v
        saida.append(limpa)
    return saida


def _brl(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _alerta(a: alertas.Alerta) -> dict:
    return {"nivel": a.rotulo, "titulo": a.titulo, "detalhe": a.detalhe}


def _previsoes() -> tuple[pd.DataFrame, pd.DataFrame]:
    diaria = _ler("SELECT * FROM analytics.vw_previsao_diaria_atual ORDER BY data")
    diaria["data"] = pd.to_datetime(diaria["data"])
    horaria = _ler("SELECT * FROM analytics.vw_previsao_horaria_atual ORDER BY ts_local")
    return diaria, horaria


# --------------------------------------------------------------------------------------------
# Tempo
# --------------------------------------------------------------------------------------------


def previsao_tempo(ctx: Contexto, dias: int = 7) -> dict:
    diaria, _ = _previsoes()
    diaria = diaria[diaria["data"] >= pd.Timestamp(ctx.hoje)]
    if diaria.empty:
        return {"erro": "Sem previsão para os próximos dias no banco. Peça para atualizar a previsão."}
    dias = max(1, min(int(dias), 16))
    tabela = diaria.head(dias).assign(dia=lambda d: d["data"].map(alertas.dia_curto))
    emitida = pd.Timestamp(diaria["emitida_em"].iloc[0])
    return {
        "fonte": "Open-Meteo, previsão para o centro de Itapeva",
        "emitida_em": emitida.strftime("%d/%m/%Y %H:%M"),
        "aviso": ("previsão emitida há mais de 1 dia: recomende atualizar (botão Atualizar previsão)"
                  if (pd.Timestamp(ctx.hoje) - emitida.normalize()).days >= 1 else None),
        "dias": _registros(tabela, ["dia", "temp_min_c", "temp_max_c", "chuva_mm", "prob_chuva_pct",
                                    "vento_max_kmh", "rajada_max_kmh", "et0_mm"]),
        "chuva_total_mm": round(float(tabela["chuva_mm"].fillna(0).sum()), 1),
        "alertas_16_dias": [_alerta(f(diaria)) for f in (alertas.alerta_geada, alertas.alerta_veranico,
                                                         alertas.alerta_calor, alertas.alerta_chuva_forte)],
    }


def janela_pulverizacao(ctx: Contexto, dias: int = 3) -> dict:
    _, horaria = _previsoes()
    if horaria.empty:
        return {"erro": "Sem previsão horária no banco."}
    h = alertas.horas_pulverizacao(horaria)
    h["dia"] = h["ts_local"].dt.normalize()
    resumo = []
    for dia in sorted(h["dia"].unique())[: max(1, min(int(dias), 7))]:
        hd = h[h["dia"] == dia]
        boas = hd[hd["boa"]]["ts_local"].dt.hour.tolist()
        motivos = hd[(~hd["boa"]) & hd["ts_local"].dt.hour.between(6, 20)]["motivo"].value_counts().head(2)
        resumo.append({"dia": alertas.dia_curto(dia), "horas_boas": [f"{x:02d}h" for x in boas],
                       "principais_impedimentos": motivos.index.tolist()})
    return {
        "fonte": "Open-Meteo (previsão horária) + regra SafraViva",
        "regra": "hora boa = 6h–20h, vento 3–10 km/h, Delta T 2–8 °C, chance de chuva < 30%, temperatura < 30 °C",
        "dias": resumo,
        "recomendacao": _alerta(alertas.alerta_pulverizacao(horaria)),
    }


def clima_historico(ctx: Contexto, tema: str) -> dict:
    analises = config.DIR_SQL / "analises"
    if tema == "geada_por_mes":
        df = _ler((analises / "06_geada_por_mes.sql").read_text(encoding="utf-8"))
        return {"fonte": "INMET estação A714 Itapeva, 2006–2026", "nota": "Tmín ≤ 3 °C no abrigo ≈ geada na relva",
                "meses": _registros(df)}
    if tema == "tendencia_decadas":
        df = _ler((analises / "08_tendencia_climatica.sql").read_text(encoding="utf-8"))
        return {"fonte": "NASA POWER, Itapeva, 1981–2025", "nota": "verão = out–mar; anos 2020 têm só 5 safras",
                "decadas": _registros(df)}
    if tema == "chuva_ultimos_12_meses":
        df = _ler("""
            WITH m AS (SELECT date_trunc('month', data) AS mes, sum(chuva_mm) AS chuva_mm
                       FROM analytics.fato_clima_itapeva GROUP BY 1),
                 n AS (SELECT month(mes) AS mm, avg(chuva_mm) AS normal_mm FROM m
                       WHERE year(mes) BETWEEN 1991 AND 2020 GROUP BY 1)
            SELECT strftime(mes, '%m/%Y') AS mes, chuva_mm, normal_mm FROM m JOIN n ON n.mm = month(m.mes)
            WHERE mes >= date_trunc('month', current_date) - INTERVAL 12 MONTH
              AND mes < date_trunc('month', current_date) ORDER BY m.mes""")
        return {"fonte": "INMET A714 + NASA POWER calibrada; normal 1991–2020", "meses": _registros(df)}
    if tema == "veranicos_soja":
        df = _ler((analises / "07_veranicos_soja.sql").read_text(encoding="utf-8"))
        return {"fonte": "Série de Itapeva (A714 + NASA), fases fenológicas aproximadas", "safras": _registros(df)}
    return {"erro": f"Tema desconhecido: {tema}"}


# --------------------------------------------------------------------------------------------
# Plantio (ZARC)
# --------------------------------------------------------------------------------------------

CULTURAS_ZARC = {
    "soja": "Soja", "milho_verao": "Milho 1ª Safra", "milho_safrinha": "Milho 2ª Safra", "trigo": "Trigo",
    "feijao": "Feijão", "feijao_safrinha": "Feijão 2ª Safra", "aveia": "Aveia", "cevada": "Cevada Grãos",
    "sorgo": "Sorgo Granífero",
}


def janela_plantio(ctx: Contexto, cultura: str, solo: str = "AD4", ciclo: str = "Grupo II") -> dict:
    nome = CULTURAS_ZARC.get(cultura)
    if not nome:
        return {"erro": f"Cultura sem zoneamento: {cultura}"}
    df = _ler("""
        WITH vigente AS (SELECT max(safra) AS safra FROM analytics.janela_plantio
                         WHERE codigo_ibge = ? AND nome_cultura = ?)
        SELECT j.safra, j.data_inicio, j.data_fim, j.nivel_risco, j.risco_pct
        FROM analytics.janela_plantio j, vigente
        WHERE j.codigo_ibge = ? AND j.nome_cultura = ? AND j.safra = vigente.safra
          AND j.solo = ? AND j.ciclo = ? AND j.manejo = 'Sequeiro'
        ORDER BY j.data_inicio""", [config.CODIGO_ITAPEVA, nome, config.CODIGO_ITAPEVA, nome, solo, ciclo])
    if df.empty:
        return {"erro": f"O ZARC não traz janela para {nome}, solo {solo}, {ciclo}, em Itapeva."}
    for col in ("data_inicio", "data_fim"):
        df[col] = pd.to_datetime(df[col])
    situacao = alertas.situacao_plantio(df.assign(nome_cultura=nome), nome, ctx.hoje)
    return {
        "fonte": f"MAPA, Zoneamento Agrícola de Risco Climático (ZARC), safra {df['safra'].iloc[0]}",
        "municipio": "Itapeva-SP", "cultura": nome, "solo": solo, "ciclo": ciclo, "manejo": "sequeiro",
        "janelas": _registros(df, ["data_inicio", "data_fim", "nivel_risco", "risco_pct"]),
        "situacao_hoje": _alerta(situacao),
        "nota": "risco = chance de perda por clima; fora das janelas o plantio não é indicado (afeta seguro e Proagro). "
                "Calendário da soja em SP (Região 1): semeadura 1/set–29/dez, vazio sanitário 1/jun–31/ago.",
    }


# --------------------------------------------------------------------------------------------
# Minha fazenda
# --------------------------------------------------------------------------------------------


def _propriedade(ctx: Contexto) -> dict | None:
    if ctx.propriedade_id is None:
        return None
    df = _ler("SELECT id, nome, demo FROM fazenda.propriedade WHERE id = ?", [ctx.propriedade_id])
    return None if df.empty else {"nome": df["nome"].iloc[0], "demonstracao": bool(df["demo"].iloc[0])}


def _sem_fazenda() -> dict:
    return {"erro": "Nenhuma propriedade cadastrada ainda. Os dados da fazenda entram pelo cadastro/formulário."}


def minhas_lavouras(ctx: Contexto) -> dict:
    prop = _propriedade(ctx)
    if prop is None:
        return _sem_fazenda()
    est = _ler("SELECT * FROM fazenda.vw_estadio_atual WHERE propriedade_id = ? ORDER BY talhao", [ctx.propriedade_id])
    diaria, _ = _previsoes()
    lavouras = []
    for r in est.itertuples():
        a = alertas.alerta_lavoura(r.talhao, r.cultura, r.fase, int(r.dias_apos_plantio), diaria)
        lavouras.append({"talhao": r.talhao, "cultura": r.cultura, "solo": r.solo_ad, "area_ha": r.area_ha,
                         "plantio": pd.Timestamp(r.data_plantio).strftime("%d/%m/%Y"),
                         "dias_apos_plantio": int(r.dias_apos_plantio), "fase_estimada": r.fase,
                         "sensivel_a": r.sensivel_a, "alerta_tempo": _alerta(a)})
    planejados = _ler("""SELECT talhao, cultura, temporada, safra, data_plantio, solo_ad, grupo_ciclo
                         FROM fazenda.vw_plantio
                         WHERE propriedade_id = ? AND status = 'planejado' ORDER BY data_plantio""", [ctx.propriedade_id])
    lista_planejados = []
    for p in planejados.itertuples():
        chave = "milho_safrinha" if p.cultura == "milho" and p.temporada == "safrinha" else (
            "milho_verao" if p.cultura == "milho" else p.cultura)
        zarc = janela_plantio(ctx, chave, p.solo_ad or "AD4", p.grupo_ciclo or "Grupo II") if chave in CULTURAS_ZARC else {}
        lista_planejados.append({
            "talhao": p.talhao, "cultura": p.cultura, "safra": p.safra, "solo_do_talhao": p.solo_ad,
            "ciclo": p.grupo_ciclo,
            "plantio_previsto": pd.Timestamp(p.data_plantio).strftime("%d/%m/%Y") if pd.notna(p.data_plantio) else None,
            "zarc_para_o_solo_do_talhao": zarc.get("situacao_hoje") or zarc.get("erro")})
    return {"propriedade": prop, "fonte": "Caderno da fazenda + duração típica das fases + previsão Open-Meteo + ZARC",
            "nota": "fase estimada pelos dias após o plantio (ciclo médio); confirme no campo. "
                    "O ZARC dos planejados já usa o solo e o ciclo de cada talhão.",
            "lavouras_plantadas": lavouras, "plantios_planejados": lista_planejados}


def _estoque(propriedade_id: int) -> list[dict]:
    """Sacas colhidas, vendidas e em estoque por cultura e safra (TODAS as safras com colheita ou venda),
    com o preço de referência atual para valorizar o estoque."""
    df = _ler("""
        WITH col AS (SELECT p.cultura, p.safra, sum(c.sacas) AS colhidas FROM fazenda.colheita c
                     JOIN fazenda.vw_plantio p ON p.id = c.plantio_id
                     WHERE p.propriedade_id = ? GROUP BY 1, 2),
             ven AS (SELECT cultura, safra, sum(sacas) AS vendidas, sum(sacas * preco_sc) / sum(sacas) AS preco_medio
                     FROM fazenda.venda WHERE propriedade_id = ? GROUP BY 1, 2),
             custo AS (SELECT cultura, safra, sum(custo_total) / nullif(sum(sacas), 0) AS custo_por_saca
                       FROM fazenda.vw_resultado_plantio WHERE propriedade_id = ? AND sacas IS NOT NULL GROUP BY 1, 2)
        SELECT e.*, k.custo_por_saca AS custo_por_saca_da_safra, r.preco_sc AS preco_referencia_sc,
               r.fonte AS fonte_preco, r.data AS data_preco,
               e.sacas_em_estoque * r.preco_sc AS valor_estoque_referencia_r
        FROM (SELECT cultura, safra, coalesce(colhidas, 0) AS sacas_colhidas, coalesce(vendidas, 0) AS sacas_vendidas,
                     greatest(coalesce(colhidas, 0) - coalesce(vendidas, 0), 0) AS sacas_em_estoque,
                     preco_medio AS preco_medio_vendido
              FROM col FULL JOIN ven USING (cultura, safra)) e
        LEFT JOIN custo k USING (cultura, safra)
        LEFT JOIN fazenda.preco_referencia r USING (cultura)
        ORDER BY safra DESC, cultura""", [propriedade_id, propriedade_id, propriedade_id])
    return _registros(df, casas=2)


def resultado_safra(ctx: Contexto, safra: str | None = None) -> dict:
    prop = _propriedade(ctx)
    if prop is None:
        return _sem_fazenda()
    r = _ler("SELECT * FROM fazenda.vw_resultado_plantio WHERE propriedade_id = ?", [ctx.propriedade_id])
    if r.empty:
        return {"propriedade": prop, "erro": "Nenhum plantio cadastrado."}
    safras = sorted(r["safra"].unique().tolist(), reverse=True)
    safra = safra if safra in safras else safras[0]
    rs = r[r["safra"] == safra].copy()
    rs["custo_previsto_ha"] = rs["custo_previsto"] / rs["area_ha"]
    rs["margem_prevista_ha"] = rs["margem_prevista"] / rs["area_ha"]
    area = rs["area_ha"].sum()
    return {
        "propriedade": prop, "safra": safra, "safras_disponiveis": safras,
        "fonte": "Lançamentos da fazenda; preço = vendas realizadas ou referência; custo previsto = maior entre o "
                 "lançado e o custo CONAB nas lavouras em andamento",
        "totais": {"area_ha": round(area, 1), "custo_previsto_r": round(rs["custo_previsto"].sum()),
                   "receita_r": round(rs["receita"].sum()), "margem_prevista_r": round(rs["margem_prevista"].sum()),
                   "margem_por_ha_r": round(rs["margem_prevista"].sum() / area)},
        "estoque_todas_as_safras": _estoque(ctx.propriedade_id),
        "lavouras": _registros(rs, ["talhao", "cultura", "temporada", "status", "area_ha", "custo_previsto_ha",
                                    "produtividade_sc_ha", "produtividade_meta_sc_ha", "ponto_equilibrio_sc_ha",
                                    "preco_sc", "origem_preco", "custo_por_saca", "margem_prevista_ha",
                                    "receita_estimada"]),
    }


def custos_por_categoria(ctx: Contexto, cultura: str, safra: str | None = None) -> dict:
    prop = _propriedade(ctx)
    if prop is None:
        return _sem_fazenda()
    status = _ler("""SELECT safra, bool_and(status IN ('colhido', 'perdido')) AS fechada
                     FROM fazenda.vw_plantio WHERE propriedade_id = ? AND cultura = ? GROUP BY safra
                     ORDER BY safra DESC""", [ctx.propriedade_id, cultura])
    if status.empty:
        return {"propriedade": prop, "erro": f"Nenhum plantio de {cultura} cadastrado."}
    if safra is None:  # padrão: a safra fechada mais recente (comparar custo parcial com a CONAB engana)
        fechadas = status[status["fechada"]]
        safra = (fechadas if not fechadas.empty else status)["safra"].iloc[0]
    fechada = bool(status.set_index("safra")["fechada"].get(safra, False))
    df = _ler("""
        WITH area AS (SELECT sum(area_efetiva_ha) AS a FROM fazenda.vw_plantio
                      WHERE propriedade_id = ? AND safra = ? AND cultura = ?),
             faz AS (SELECT c.categoria, sum(c.valor) / any_value(area.a) AS fazenda_r_ha
                     FROM fazenda.vw_custo_plantio c JOIN fazenda.vw_plantio p ON p.id = c.plantio_id, area
                     WHERE p.propriedade_id = ? AND p.safra = ? AND p.cultura = ? GROUP BY 1),
             ref AS (SELECT categoria, valor_ha AS conab_r_ha FROM analytics.custo_referencia
                     WHERE cultura = ? AND categoria NOT IN ('custo_variavel','custo_operacional','custo_total',
                                                             'renda_fatores','arrendamento'))
        SELECT categoria, fazenda_r_ha, conab_r_ha FROM faz FULL JOIN ref USING (categoria)
        ORDER BY coalesce(fazenda_r_ha, conab_r_ha) DESC""",
              [ctx.propriedade_id, safra, cultura, ctx.propriedade_id, safra, cultura, cultura])
    ref = _ler("SELECT DISTINCT local, mes_referencia FROM analytics.custo_referencia WHERE cultura = ?", [cultura])
    fonte_ref = (f"CONAB {ref['local'].iloc[0]} ({pd.Timestamp(ref['mes_referencia'].iloc[0]):%m/%Y}), sem arrendamento"
                 if not ref.empty else "sem referência CONAB")
    df["categoria"] = df["categoria"].map(lambda c: gestao.CATEGORIAS.get(c, c))
    return {"propriedade": prop, "safra": safra, "cultura": cultura, "fonte_referencia": fonte_ref,
            "safra_fechada": fechada,
            "aviso": None if fechada else ("SAFRA EM ANDAMENTO: custos ainda parciais (só o que já foi lançado). "
                                           "Não conclua que está abaixo da CONAB; compare só no fim da safra."),
            "unidade": "R$ por hectare",
            "total_fazenda_r_ha": round(float(df["fazenda_r_ha"].fillna(0).sum())),
            "total_conab_r_ha": round(float(df["conab_r_ha"].fillna(0).sum())),
            "categorias": _registros(df, casas=0)}


def caderno_de_campo(ctx: Contexto, talhao: str | None = None, safra: str | None = None, limite: int = 20) -> dict:
    prop = _propriedade(ctx)
    if prop is None:
        return _sem_fazenda()
    filtros, params = ["p.propriedade_id = ?"], [ctx.propriedade_id]
    if talhao:
        filtros.append("lower(p.talhao) = lower(?)")
        params.append(talhao)
    if safra:
        filtros.append("p.safra = ?")
        params.append(safra)
    df = _ler(f"""
        SELECT o.data, p.talhao, p.cultura, p.safra, o.tipo, o.produto, o.dose, o.unidade, o.custo_total,
               o.categoria_custo, o.observacao
        FROM fazenda.operacao o JOIN fazenda.vw_plantio p ON p.id = o.plantio_id
        WHERE {' AND '.join(filtros)} ORDER BY o.data DESC LIMIT ?""", params + [max(1, min(int(limite), 100))])
    oc = _ler(f"""
        SELECT oc.data, p.talhao, p.cultura, oc.tipo, oc.severidade, oc.descricao
        FROM fazenda.ocorrencia oc JOIN fazenda.vw_plantio p ON p.id = oc.plantio_id
        WHERE {' AND '.join(filtros)} ORDER BY oc.data DESC LIMIT 10""", params)
    return {"propriedade": prop, "operacoes": _registros(df, casas=2), "ocorrencias": _registros(oc)}


# --------------------------------------------------------------------------------------------
# Região
# --------------------------------------------------------------------------------------------


def _leitura_quebra(cultura: str, r) -> str:
    """Interpretação por regra (a mesma do docs/insights.md), para o modelo não inventar a causa."""
    def v(x):
        return None if x is None or x != x else x  # NaN → None

    sinais = []
    if cultura == "trigo":
        if v(r.tmin_ciclo_c) is not None and r.tmin_ciclo_c <= 0:
            sinais.append(f"geada (mínima de {r.tmin_ciclo_c:.1f} °C no ciclo)")
        if (v(r.veranico_max_dias) or 0) >= 20 or (v(r.balanco_flor_mm) or 0) < -50:
            sinais.append("seca no florescimento")
    else:
        if (v(r.dias_calor_flor) or 0) >= 8 or (v(r.balanco_flor_mm) or 0) < 0:
            sinais.append("calor e/ou falta de água no florescimento")
        if (v(r.veranico_max_dias) or 0) >= 15:
            sinais.append("veranico longo (≥ 15 dias) no florescimento/enchimento")
    if (v(r.chuva_colheita_mm) or 0) >= 250:
        sinais.append("chuva excessiva na colheita")
    perda_area = v(r.perda_area_pct) or 0
    if not sinais:
        base = "sem sinal climático claro nos índices: causa não identificada (manejo, sanidade, granizo localizado ou registro)"
        return (f"{100 * perda_area:.0f}% da área plantada não foi colhida, " + base) if perda_area >= 0.3 else base
    if perda_area >= 0.3:
        sinais.append(f"{100 * perda_area:.0f}% da área plantada não foi colhida")
    return "; ".join(sinais)


def producao_regional(ctx: Contexto, cultura: str) -> dict:
    if cultura not in ("soja", "milho", "trigo", "feijao"):
        return {"erro": "Use soja, milho, trigo ou feijao."}
    comp = _ler("""
        SELECT nome_local, round(avg(rendimento_sc_ha), 1) AS sc_ha_media_5_anos, round(avg(area_colhida_ha)) AS area_ha
        FROM analytics.fato_producao
        WHERE cultura = ? AND ano BETWEEN 2021 AND 2025 AND NOT suspeito_repeticao
          AND (codigo_local = ? OR (nivel = 'uf' AND codigo_local IN (35, 41)))
        GROUP BY 1 ORDER BY 2 DESC""", [cultura, config.CODIGO_ITAPEVA])
    evolucao = _ler("""
        SELECT (ano // 10) * 10 || 's' AS decada,
               round(avg(rendimento_sc_ha) FILTER (WHERE nivel = 'municipio' AND codigo_local = ?), 1) AS itapeva_sc_ha,
               round(avg(rendimento_sc_ha) FILTER (WHERE nivel = 'uf' AND codigo_local = 35), 1) AS sp_sc_ha,
               round(avg(area_colhida_ha) FILTER (WHERE nivel = 'municipio' AND codigo_local = ?)) AS itapeva_area_ha
        FROM analytics.fato_producao WHERE cultura = ? AND NOT suspeito_repeticao
        GROUP BY 1 ORDER BY 1""", [config.CODIGO_ITAPEVA, config.CODIGO_ITAPEVA, cultura])
    quebras = _ler("""
        SELECT p.ano, round(p.rendimento_sc_ha, 1) AS sc_ha, round(100 * p.desvio_vs_media_5a) AS desvio_pct,
               p.perda_area_pct,
               max(i.balanco_mm) FILTER (WHERE i.fase = 'florescimento')        AS balanco_flor_mm,
               max(i.max_veranico_dias) FILTER (WHERE i.fase IN ('florescimento', 'enchimento')) AS veranico_max_dias,
               max(i.dias_tmax_ge32) FILTER (WHERE i.fase = 'florescimento')    AS dias_calor_flor,
               min(i.tmin_min)                                                   AS tmin_ciclo_c,
               max(i.chuva_mm) FILTER (WHERE i.fase = 'colheita')               AS chuva_colheita_mm
        FROM analytics.fato_producao p
        LEFT JOIN analytics.indices_fase i ON i.cultura = p.cultura AND i.ano_pam = p.ano
             AND i.codigo_ibge = p.codigo_local AND i.serie = 'itapeva'
        WHERE p.nivel = 'municipio' AND p.codigo_local = ? AND p.cultura = ? AND p.ano >= 1983
          AND p.desvio_vs_media_5a <= -0.15 AND NOT p.suspeito_repeticao
        GROUP BY ALL ORDER BY p.ano""", [config.CODIGO_ITAPEVA, cultura])
    quebras["leitura_climatica"] = [_leitura_quebra(cultura, r) for r in quebras.itertuples()]
    return {"fonte": "IBGE/PAM tabela 1612 (sem anos suspeitos); clima: série de Itapeva (A714 + NASA POWER)",
            "comparacao_2021_2025": _registros(comp),
            "evolucao_por_decada": _registros(evolucao),
            "safras_de_quebra_itapeva": _registros(quebras.drop(columns=["perda_area_pct"])),
            "nota": "quebra = rendimento ≥ 15% abaixo da média dos 5 anos anteriores. Use a 'leitura_climatica' como "
                    "está: ela aplica limites fixos aos índices. O dado de soja de 2025 é suspeito (repetido de 2024)."}


TEMAS_CONHECIMENTO = {
    "territorio_e_regulacao": "## 1.",
    "solos": "## 2.",
    "culturas_e_janelas_zarc": "## 3.",
    "custos_e_logistica": "## 4.",
}


def conhecimento_regional(ctx: Contexto, tema: str) -> dict:
    """Trechos de docs/conhecimento_regional.md (pesquisa com fontes)."""
    texto = (config.RAIZ / "docs" / "conhecimento_regional.md").read_text(encoding="utf-8")
    inicio = TEMAS_CONHECIMENTO.get(tema)
    if inicio is None or inicio not in texto:
        return {"erro": f"Tema desconhecido: {tema}"}
    trecho = texto[texto.index(inicio):]
    proximo = re.search(r"\n## (?!" + re.escape(inicio[3:]) + r")\d", trecho[3:])
    trecho = trecho[: proximo.start() + 3] if proximo else trecho
    return {"fonte": "docs/conhecimento_regional.md (pesquisa SafraViva com fontes citadas)", "texto": trecho.strip()}


# --------------------------------------------------------------------------------------------
# Lançamento por linguagem natural (pendente de confirmação)
# --------------------------------------------------------------------------------------------


def propor_lancamento(ctx: Contexto, registro: str, talhao: str, data: str, cultura: str | None = None,
                      tipo_operacao: str | None = None, produto: str | None = None, dose: float | None = None,
                      unidade: str | None = None, valor: float | None = None, categoria: str | None = None,
                      sacas: float | None = None, tipo_ocorrencia: str | None = None, severidade: int | None = None,
                      observacao: str | None = None) -> dict:
    """Monta um lançamento PENDENTE. Nada é gravado até o produtor tocar em Confirmar."""
    if ctx.propriedade_id is None:
        return _sem_fazenda()
    try:
        quando = date.fromisoformat(data)
    except ValueError:
        return {"erro": "Data inválida: use AAAA-MM-DD."}
    if quando > ctx.hoje:
        return {"erro": "A data está no futuro. Lançamentos são do que já foi feito."}
    plantios = _ler("""SELECT id, talhao, cultura, safra, status FROM fazenda.vw_plantio
                       WHERE propriedade_id = ? AND lower(talhao) = lower(?)
                       ORDER BY (status = 'plantado') DESC, safra DESC""", [ctx.propriedade_id, talhao])
    if cultura:
        plantios = plantios[plantios["cultura"] == cultura]
    if plantios.empty:
        nomes = _ler("SELECT nome FROM fazenda.talhao WHERE propriedade_id = ?", [ctx.propriedade_id])["nome"].tolist()
        return {"erro": f"Não achei plantio no talhão '{talhao}'" + (f" de {cultura}" if cultura else "")
                        + f". Talhões cadastrados: {', '.join(nomes)}."}
    alvo = plantios.iloc[0]
    rotulo = f"{gestao.CULTURAS.get(alvo.cultura, alvo.cultura)} · {alvo.talhao} · safra {alvo.safra}"

    if registro == "operacao":
        if tipo_operacao not in gestao.TIPOS_OPERACAO:
            return {"erro": f"tipo_operacao deve ser um de {list(gestao.TIPOS_OPERACAO)}"}
        if valor and categoria not in gestao.CATEGORIAS:
            return {"erro": f"Com valor, informe a categoria: {list(gestao.CATEGORIAS)}"}
        argumentos = dict(plantio_id=int(alvo.id), data=quando, tipo=tipo_operacao, produto=produto, dose=dose,
                          unidade=unidade, custo_total=valor, categoria_custo=categoria if valor else None,
                          observacao=observacao)
        resumo = (f"{gestao.TIPOS_OPERACAO[tipo_operacao]} em {rotulo}, {quando:%d/%m/%Y}"
                  + (f": {produto}" if produto else "") + (f" {dose} {unidade or ''}".rstrip() if dose else "")
                  + (f", custo {_brl(valor)}" if valor else ""))
        funcao = "registrar_operacao"
    elif registro == "despesa":
        if not valor or categoria not in gestao.CATEGORIAS:
            return {"erro": f"Despesa precisa de valor e categoria: {list(gestao.CATEGORIAS)}"}
        argumentos = dict(propriedade_id=ctx.propriedade_id, data=quando, categoria=categoria, valor=valor,
                          descricao=observacao or produto, plantio_id=int(alvo.id), safra=alvo.safra)
        resumo = f"Despesa de {gestao.CATEGORIAS[categoria]} em {rotulo}: {_brl(valor)}"
        funcao = "registrar_custo"
    elif registro == "colheita":
        if not sacas:
            return {"erro": "Colheita precisa do número de sacas."}
        argumentos = dict(plantio_id=int(alvo.id), data=quando, sacas=sacas, observacao=observacao)
        resumo = f"Colheita em {rotulo}, {quando:%d/%m/%Y}: {sacas:,.0f} sacas".replace(",", ".")
        funcao = "registrar_colheita"
    elif registro == "ocorrencia":
        if tipo_ocorrencia not in gestao.TIPOS_OCORRENCIA:
            return {"erro": f"tipo_ocorrencia deve ser um de {list(gestao.TIPOS_OCORRENCIA)}"}
        argumentos = dict(plantio_id=int(alvo.id), data=quando, tipo=tipo_ocorrencia, severidade=severidade,
                          descricao=observacao)
        resumo = f"Ocorrência ({gestao.TIPOS_OCORRENCIA[tipo_ocorrencia]}) em {rotulo}, {quando:%d/%m/%Y}"
        funcao = "registrar_ocorrencia"
    else:
        return {"erro": "registro deve ser operacao, despesa, colheita ou ocorrencia."}

    ctx.pendentes.append({"funcao": funcao, "argumentos": argumentos, "resumo": resumo})
    return {"status": "PENDENTE — aguardando o produtor tocar em Confirmar na tela", "resumo": resumo}


# --------------------------------------------------------------------------------------------
# Estimativa de safra e alertas (Fase 6)
# --------------------------------------------------------------------------------------------


def estimativa_safra(ctx: Contexto) -> dict:
    """Produtividade provável de cada lavoura plantada pelo balanço hídrico + anos análogos."""
    from analytics import balanco_hidrico as bh

    prop = _propriedade(ctx)
    if prop is None:
        return _sem_fazenda()
    with conectar(leitura=True) as con:
        lista = bh.estimar_propriedade(con, ctx.propriedade_id)
        tabela = bh.tabela_estimativas(lista, con)
    if not lista:
        return {"propriedade": prop, "erro": "Nenhuma lavoura plantada com data de plantio e meta."}
    lavouras = []
    for e in lista:
        linha = tabela.set_index("plantio_id").loc[e.plantio_id]
        conf = bh.CONFIABILIDADE.get(linha["cultura"], ("não avaliada", False, ""))
        lavouras.append({
            "lavoura": e.rotulo, "meta_sc_ha": round(e.meta_sc_ha, 1),
            "provavel_p50_sc_ha": round(e.p50_sc_ha, 1), "ano_ruim_p10_sc_ha": round(e.p10_sc_ha, 1),
            "ano_bom_p90_sc_ha": round(e.p90_sc_ha, 1),
            "ponto_equilibrio_sc_ha": None if linha["ponto_equilibrio_sc_ha"] != linha["ponto_equilibrio_sc_ha"]
            else round(float(linha["ponto_equilibrio_sc_ha"]), 1),
            "perda_por_falta_de_agua_ate_hoje_pct": round(100 * (1 - e.razao_ate_hoje), 1),
            "confiabilidade": conf[0], "nota_confiabilidade": conf[2],
            "agua_por_fase_cenario_mediano": _registros(e.simulacao_mediana.por_fase[["fase", "etc_mm", "eta_mm", "perda_pct"]]),
        })
    return {"propriedade": prop,
            "fonte": "Balanço hídrico FAO-56/FAO-33 com clima observado (A714/NASA), recente e previsto (Open-Meteo) "
                     "e anos análogos desde 1991 para o resto do ciclo",
            "nota": "considera só a falta de água; doença, praga, geada e nutrição não entram. A faixa p10–p90 vem "
                    "dos anos análogos.",
            "lavouras": lavouras}


def alertas_ativos(ctx: Contexto) -> dict:
    df = _ler("""SELECT nivel, tema, titulo, detalhe, novo, criado_em FROM notif.vw_alertas_ativos
                 WHERE propriedade_id IS NULL OR propriedade_id = ? ORDER BY prioridade, atualizado_em DESC""",
              [ctx.propriedade_id])
    return {"fonte": "Central de alertas do SafraViva (previsão + fase das lavouras + ZARC + estimativa de safra)",
            "alertas": _registros(df)}


# --------------------------------------------------------------------------------------------
# Cotações
# --------------------------------------------------------------------------------------------

SERIES_POR_CULTURA = {
    "soja": ["cepea_soja_parana", "cepea_soja_paranagua", "cbot_soja"],
    "milho": ["cepea_milho", "cbot_milho"],
    "trigo": ["cepea_trigo_parana", "cbot_trigo"],
    "dolar": ["dolar", "dolar_ptax"],
}


def _pct(fracao: float) -> str:
    return f"{100 * fracao:+.1f}%".replace(".", ",")


def _decompor(cultura: str, dias: int) -> dict:
    """Quanto da variação em R$ veio da bolsa (em dólar) e quanto veio do câmbio, no período.

    Calculado por regra a partir da própria série convertida (dólar implícito = R$/sc ÷ US$/sc), para a IA
    não confundir "Chicago em reais" com "Chicago em dólar".
    """
    import math

    from etl.cotacoes import KG_POR_BUSHEL

    df = _ler(f"""
        WITH u AS (SELECT max(data) AS d FROM raw.cotacao_diaria WHERE serie = ?)
        SELECT data, valor, valor_rs_sc FROM raw.cotacao_diaria, u
        WHERE serie = ? AND data >= u.d - INTERVAL {dias} DAY AND valor_rs_sc IS NOT NULL ORDER BY data""",
              [f"cbot_{cultura}", f"cbot_{cultura}"])
    if len(df) < 2:
        return {"erro": "série de Chicago insuficiente no período"}
    ini, fim = df.iloc[0], df.iloc[-1]
    fator = 60 / KG_POR_BUSHEL[cultura] / 100
    dolar_ini, dolar_fim = ini.valor_rs_sc / (ini.valor * fator), fim.valor_rs_sc / (fim.valor * fator)
    v_bolsa, v_dolar, v_reais = fim.valor / ini.valor - 1, dolar_fim / dolar_ini - 1, fim.valor_rs_sc / ini.valor_rs_sc - 1
    motor = "o dólar" if abs(math.log1p(v_dolar)) > abs(math.log1p(v_bolsa)) else "a bolsa de Chicago"
    return {
        "periodo": f"{pd.Timestamp(ini.data):%d/%m/%Y} a {pd.Timestamp(fim.data):%d/%m/%Y}",
        "chicago_em_dolar_pct": round(float(100 * v_bolsa), 2),
        "dolar_pct": round(float(100 * v_dolar), 2),
        "chicago_em_reais_pct": round(float(100 * v_reais), 2),
        "leitura": (f"Em dólar, Chicago variou {_pct(v_bolsa)}; o dólar variou {_pct(v_dolar)}; em reais, "
                    f"{_pct(v_reais)}. Quem mais pesou foi {motor}."),
    }


def cotacoes(ctx: Contexto, cultura: str, dias: int = 30) -> dict:
    """Preço agora, variação no período, sazonalidade histórica e o preço frente ao custo da fazenda."""
    if cultura not in SERIES_POR_CULTURA:
        return {"erro": "Use soja, milho, trigo ou dolar."}
    dias = max(5, min(int(dias), 3650))
    series = SERIES_POR_CULTURA[cultura]
    resumo = _ler(f"""
        WITH s AS (SELECT * FROM raw.cotacao_diaria WHERE serie IN (SELECT unnest(?))),
             ult AS (SELECT serie, max(data) AS data FROM s GROUP BY 1),
             per AS (SELECT s.serie, min(coalesce(valor_rs_sc, valor)) AS minimo, max(coalesce(valor_rs_sc, valor)) AS maximo,
                            avg(coalesce(valor_rs_sc, valor)) AS media,
                            arg_min(coalesce(valor_rs_sc, valor), s.data) AS inicio_periodo
                     FROM s JOIN ult USING (serie) WHERE s.data >= ult.data - INTERVAL {dias} DAY GROUP BY 1)
        SELECT s.serie, s.nome, s.data AS ultimo_dia, coalesce(s.valor_rs_sc, s.valor) AS valor,
               CASE WHEN s.valor_rs_sc IS NULL THEN s.unidade ELSE 'R$/sc 60 kg' END AS unidade,
               per.minimo, per.maximo, per.media, 100 * (coalesce(s.valor_rs_sc, s.valor) / per.inicio_periodo - 1) AS variacao_periodo_pct,
               s.fonte
        FROM s JOIN ult USING (serie, data) JOIN per USING (serie) ORDER BY s.serie""", [series])
    agora = _ler("""SELECT nome, preco, unidade, round(variacao_pct, 2) AS variacao_hoje_pct, preco_rs_sc,
                           strftime(horario_mercado, '%d/%m %H:%M') AS horario
                    FROM raw.cotacao_ultima WHERE serie IN (SELECT unnest(?))""", [series])
    principal = series[0]
    sazonal = _ler("""
        WITH m AS (SELECT year(data) AS ano, month(data) AS mes, avg(coalesce(valor_rs_sc, valor)) AS v
                   FROM raw.cotacao_diaria WHERE serie = ? AND data >= current_date - INTERVAL 10 YEAR GROUP BY 1, 2),
             a AS (SELECT ano, avg(v) AS va FROM m GROUP BY 1 HAVING count(*) = 12)
        SELECT mes, round(100 * (avg(v / va) - 1), 1) AS desvio_medio_vs_ano_pct
        FROM m JOIN a USING (ano) GROUP BY mes ORDER BY mes""", [principal])
    saida = {
        "cultura": cultura,
        "fonte": "CEPEA/ESALQ (físico, diário, CC BY-NC 4.0); CBOT via Yahoo Finance (atraso ~15 min); "
                 "dólar comercial (Yahoo) e PTAX (Banco Central)",
        "nota": "CBOT em R$/sc = paridade Chicago, sem prêmio de porto, frete e impostos. O CEPEA sai uma vez por dia.",
        "ultimos_e_periodo": _registros(resumo, casas=2),
        "bolsa_agora": _registros(agora, casas=2),
        f"sazonalidade_{principal}_ultimos_10_anos": _registros(sazonal),
        "nota_sazonalidade": "média histórica de cada mês em relação à média do ano. É padrão do passado, não previsão.",
    }
    if cultura != "dolar":
        saida["decomposicao_chicago_x_dolar"] = _decompor(cultura, dias)
    if cultura == "soja":
        premio = _ler("""SELECT a.data, round(a.valor_rs_sc - b.valor_rs_sc, 2) AS premio_paranagua_vs_chicago_rs_sc
                         FROM raw.cotacao_diaria a JOIN raw.cotacao_diaria b USING (data)
                         WHERE a.serie = 'cepea_soja_paranagua' AND b.serie = 'cbot_soja' ORDER BY a.data DESC LIMIT 1""")
        saida["premio_porto"] = _registros(premio, casas=2)
    if cultura != "dolar" and ctx.propriedade_id is not None:
        estoque = [e for e in _estoque(ctx.propriedade_id) if e["cultura"] == cultura]
        saida["fazenda"] = {"propriedade": _propriedade(ctx), "estoque_e_custo_por_saca": estoque}
    return saida


# --------------------------------------------------------------------------------------------
# Catálogo: função + esquema JSON (formato de tools da OpenAI, reaproveitável em outros provedores)
# --------------------------------------------------------------------------------------------

def _f(nome: str, descricao: str, propriedades: dict | None = None, obrigatorios: list[str] | None = None) -> dict:
    return {"type": "function", "function": {
        "name": nome, "description": descricao,
        "parameters": {"type": "object", "properties": propriedades or {}, "required": obrigatorios or [],
                       "additionalProperties": False}}}


_SOLOS = {"type": "string", "enum": gestao.SOLOS, "description": "Classe de água disponível do solo (AD1 arenoso … AD6 argiloso profundo). Padrão AD4."}
_CICLOS = {"type": "string", "enum": ["Grupo I", "Grupo II", "Grupo III"], "description": "Ciclo da cultivar (I precoce … III tardio). Padrão Grupo II."}
_DATA = {"type": "string", "description": "Data no formato AAAA-MM-DD"}

FERRAMENTAS: dict[str, tuple[Callable[..., dict], dict]] = {
    "previsao_tempo": (previsao_tempo, _f(
        "previsao_tempo", "Previsão do tempo diária para Itapeva (até 16 dias) com alertas de geada, veranico, calor e chuva forte.",
        {"dias": {"type": "integer", "minimum": 1, "maximum": 16}})),
    "janela_pulverizacao": (janela_pulverizacao, _f(
        "janela_pulverizacao", "Horas boas para pulverizar nos próximos dias (vento, Delta T, chuva, temperatura).",
        {"dias": {"type": "integer", "minimum": 1, "maximum": 7}})),
    "clima_historico": (clima_historico, _f(
        "clima_historico", "Histórico de clima de Itapeva: geada por mês, tendência por década, chuva dos últimos 12 meses × normal, ou veranicos na soja por safra.",
        {"tema": {"type": "string", "enum": ["geada_por_mes", "tendencia_decadas", "chuva_ultimos_12_meses", "veranicos_soja"]}},
        ["tema"])),
    "janela_plantio": (janela_plantio, _f(
        "janela_plantio", "Janelas de plantio do ZARC (MAPA) em Itapeva por cultura, solo e ciclo, com o risco climático e a situação hoje.",
        {"cultura": {"type": "string", "enum": list(CULTURAS_ZARC)}, "solo": _SOLOS, "ciclo": _CICLOS}, ["cultura"])),
    "minhas_lavouras": (minhas_lavouras, _f(
        "minhas_lavouras", "Lavouras da fazenda: talhão, cultura, dias após o plantio, fase estimada e o alerta do tempo para essa fase.")),
    "resultado_safra": (resultado_safra, _f(
        "resultado_safra", "Resultado econômico da safra por talhão (custo, produtividade, ponto de equilíbrio, preço, margem) e o ESTOQUE de grãos de todas as safras (colhido − vendido) com o preço de referência.",
        {"safra": {"type": "string", "description": "Ano agrícola, ex.: 2026/27. Vazio = mais recente."}})),
    "custos_por_categoria": (custos_por_categoria, _f(
        "custos_por_categoria", "Custo por hectare da fazenda em cada categoria (semente, adubo, defensivo...) comparado com a referência CONAB.",
        {"cultura": {"type": "string", "enum": list(gestao.CULTURAS)},
         "safra": {"type": "string", "description": "Ano agrícola. Vazio = última safra já colhida (recomendado)."}},
        ["cultura"])),
    "caderno_de_campo": (caderno_de_campo, _f(
        "caderno_de_campo", "Últimas operações (com produto, dose e custo) e ocorrências lançadas, com filtro opcional por talhão e safra.",
        {"talhao": {"type": "string"}, "safra": {"type": "string"}, "limite": {"type": "integer", "minimum": 1, "maximum": 100}})),
    "producao_regional": (producao_regional, _f(
        "producao_regional", "Produtividade de Itapeva × SP × PR (últimos 5 anos) e as safras de quebra em Itapeva com o clima de cada uma.",
        {"cultura": {"type": "string", "enum": ["soja", "milho", "trigo", "feijao"]}}, ["cultura"])),
    "conhecimento_regional": (conhecimento_regional, _f(
        "conhecimento_regional", "Base de conhecimento pesquisada sobre a região: território e regras (vazio sanitário, calendário), solos, culturas e janelas ZARC, custos e logística.",
        {"tema": {"type": "string", "enum": list(TEMAS_CONHECIMENTO)}}, ["tema"])),
    "estimativa_safra": (estimativa_safra, _f(
        "estimativa_safra", "Produtividade provável (p10/p50/p90) de cada lavoura plantada pela água no solo, perda por falta de água até hoje, ponto de equilíbrio e confiabilidade do modelo.")),
    "alertas_ativos": (alertas_ativos, _f(
        "alertas_ativos", "Alertas ativos agora na central (geada, veranico, calor, chuva, fase das lavouras, janela de plantio, estimativa de safra).")),
    "cotacoes": (cotacoes, _f(
        "cotacoes", "Cotações de soja, milho, trigo ou dólar: CEPEA (físico, diário), bolsa de Chicago em R$/saca (atraso ~15 min), variação no período, mínimo/máximo, sazonalidade histórica por mês, prêmio de porto (soja) e, se houver fazenda, estoque e custo por saca.",
        {"cultura": {"type": "string", "enum": ["soja", "milho", "trigo", "dolar"]},
         "dias": {"type": "integer", "minimum": 5, "maximum": 3650, "description": "Período para variação/mín/máx. Padrão 30."}},
        ["cultura"])),
    "propor_lancamento": (propor_lancamento, _f(
        "propor_lancamento", "Prepara um lançamento no caderno da fazenda a partir do que o produtor contou (operação, despesa, colheita ou ocorrência). NÃO grava: fica pendente até o produtor confirmar na tela.",
        {"registro": {"type": "string", "enum": ["operacao", "despesa", "colheita", "ocorrencia"]},
         "talhao": {"type": "string"}, "data": _DATA,
         "cultura": {"type": "string", "enum": list(gestao.CULTURAS)},
         "tipo_operacao": {"type": "string", "enum": list(gestao.TIPOS_OPERACAO)},
         "produto": {"type": "string"}, "dose": {"type": "number"}, "unidade": {"type": "string"},
         "valor": {"type": "number", "description": "Valor em reais"},
         "categoria": {"type": "string", "enum": list(gestao.CATEGORIAS)},
         "sacas": {"type": "number"},
         "tipo_ocorrencia": {"type": "string", "enum": list(gestao.TIPOS_OCORRENCIA)},
         "severidade": {"type": "integer", "enum": [1, 2, 3]},
         "observacao": {"type": "string"}},
        ["registro", "talhao", "data"])),
}


def esquemas() -> list[dict]:
    return [esquema for _, esquema in FERRAMENTAS.values()]


def executar(nome: str, argumentos: dict[str, Any], ctx: Contexto) -> dict:
    """Executa uma ferramenta pelo nome; erros viram mensagem para o modelo (que pode corrigir e tentar de novo)."""
    if nome not in FERRAMENTAS:
        return {"erro": f"Ferramenta desconhecida: {nome}"}
    funcao, _ = FERRAMENTAS[nome]
    try:
        return funcao(ctx, **{k: v for k, v in argumentos.items() if v is not None})
    except TypeError as erro:
        return {"erro": f"Argumentos inválidos para {nome}: {erro}"}
    except duckdb.Error as erro:
        return {"erro": f"Falha ao consultar o banco: {erro}"}
