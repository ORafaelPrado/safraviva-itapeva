"""Leitura do banco para o painel.

Cada consulta abre uma conexão somente-leitura curta e fecha em seguida. Assim o
painel aberto não trava o ETL, que precisa gravar no mesmo arquivo DuckDB.
O cache do Streamlit evita bater no banco a cada clique.
"""

from __future__ import annotations

import duckdb
import pandas as pd
import streamlit as st

from core import config
from core.db import conectar

CACHE_CURTO = 300  # previsão: 5 min
CACHE_LONGO = 6 * 3600  # dados históricos: 6 h


def consultar(sql: str, params: list | None = None) -> pd.DataFrame:
    with conectar(leitura=True) as con:
        return con.execute(sql, params or []).df()


@st.cache_data(ttl=CACHE_CURTO, show_spinner=False)
def previsao_diaria() -> pd.DataFrame:
    df = consultar("SELECT * FROM analytics.vw_previsao_diaria_atual ORDER BY data")
    df["data"] = pd.to_datetime(df["data"])
    return df


@st.cache_data(ttl=CACHE_CURTO, show_spinner=False)
def previsao_horaria() -> pd.DataFrame:
    return consultar("SELECT * FROM analytics.vw_previsao_horaria_atual ORDER BY ts_local")


@st.cache_data(ttl=CACHE_LONGO, show_spinner=False)
def janelas_plantio(solo: str, ciclo: str, manejo: str = "Sequeiro") -> pd.DataFrame:
    """Janelas da safra mais recente de cada cultura, para o solo/ciclo escolhidos em Itapeva."""
    df = consultar(
        """
        WITH vigente AS (
            SELECT nome_cultura, max(safra) AS safra FROM analytics.janela_plantio
            WHERE codigo_ibge = ? GROUP BY nome_cultura
        )
        SELECT j.* FROM analytics.janela_plantio j JOIN vigente USING (nome_cultura, safra)
        WHERE j.codigo_ibge = ? AND j.solo = ? AND j.ciclo = ? AND j.manejo = ?
        ORDER BY j.nome_cultura, j.data_inicio
        """,
        [config.CODIGO_ITAPEVA, config.CODIGO_ITAPEVA, solo, ciclo, manejo],
    )
    for col in ("data_inicio", "data_fim"):
        df[col] = pd.to_datetime(df[col])
    return df


@st.cache_data(ttl=CACHE_LONGO, show_spinner=False)
def opcoes_zarc() -> dict[str, list[str]]:
    df = consultar(
        "SELECT DISTINCT solo, cod_solo, ciclo, cod_ciclo FROM analytics.janela_plantio WHERE codigo_ibge = ? AND cod_solo >= 11",
        [config.CODIGO_ITAPEVA],
    )
    return {
        "solos": df.sort_values("cod_solo")["solo"].unique().tolist(),
        "ciclos": df.sort_values("cod_ciclo")["ciclo"].dropna().unique().tolist(),
    }


@st.cache_data(ttl=CACHE_LONGO, show_spinner=False)
def rendimento_comparado(cultura: str) -> pd.DataFrame:
    return consultar(
        """
        SELECT ano,
               max(rendimento_sc_ha) FILTER (WHERE nivel = 'municipio' AND codigo_local = ? AND NOT suspeito_repeticao) AS "Itapeva",
               max(rendimento_sc_ha) FILTER (WHERE nivel = 'uf' AND codigo_local = 35) AS "São Paulo",
               max(rendimento_sc_ha) FILTER (WHERE nivel = 'uf' AND codigo_local = 41) AS "Paraná"
        FROM analytics.fato_producao WHERE cultura = ? AND ano >= 1990
        GROUP BY ano ORDER BY ano
        """,
        [config.CODIGO_ITAPEVA, cultura],
    )


@st.cache_data(ttl=CACHE_LONGO, show_spinner=False)
def ranking_regional(cultura: str) -> pd.DataFrame:
    return consultar(
        """
        SELECT replace(nome_local, ' (SP)', '') AS municipio,
               avg(area_colhida_ha) FILTER (WHERE ano BETWEEN 2021 AND 2025) AS area_ha,
               avg(rendimento_sc_ha) FILTER (WHERE ano BETWEEN 2021 AND 2025 AND NOT suspeito_repeticao) AS sc_ha
        FROM analytics.fato_producao
        WHERE nivel = 'municipio' AND cultura = ?
        GROUP BY ALL HAVING area_ha > 0 ORDER BY area_ha DESC
        """,
        [cultura],
    )


@st.cache_data(ttl=CACHE_LONGO, show_spinner=False)
def area_itapeva() -> pd.DataFrame:
    return consultar(
        """
        SELECT ano, cultura, area_colhida_ha / 1000 AS mil_ha FROM analytics.fato_producao
        WHERE nivel = 'municipio' AND codigo_local = ? AND cultura IN ('soja', 'milho', 'trigo') AND ano >= 1990
        ORDER BY ano
        """,
        [config.CODIGO_ITAPEVA],
    )


@st.cache_data(ttl=CACHE_LONGO, show_spinner=False)
def desvios_safra(cultura: str) -> pd.DataFrame:
    return consultar(
        """
        SELECT p.ano, p.rendimento_sc_ha, p.desvio_vs_media_5a * 100 AS desvio_pct, p.suspeito_repeticao,
               max(i.balanco_mm) FILTER (WHERE i.fase = 'florescimento')        AS balanco_flor_mm,
               max(i.dias_tmax_ge32) FILTER (WHERE i.fase = 'florescimento')    AS dias_calor_flor,
               max(i.dias_tmin_le3) FILTER (WHERE i.fase = 'florescimento')     AS dias_frio_flor,
               max(i.max_veranico_dias) FILTER (WHERE i.fase IN ('florescimento', 'enchimento')) AS veranico_dias,
               max(i.chuva_mm) FILTER (WHERE i.fase = 'colheita')               AS chuva_colheita_mm
        FROM analytics.fato_producao p
        LEFT JOIN analytics.indices_fase i
               ON i.cultura = p.cultura AND i.ano_pam = p.ano AND i.codigo_ibge = p.codigo_local AND i.serie = 'itapeva'
        WHERE p.nivel = 'municipio' AND p.codigo_local = ? AND p.cultura = ? AND p.ano >= 1995
        GROUP BY ALL ORDER BY p.ano
        """,
        [config.CODIGO_ITAPEVA, cultura],
    )


@st.cache_data(ttl=CACHE_LONGO, show_spinner=False)
def geada_por_mes() -> pd.DataFrame:
    return consultar((config.DIR_SQL / "analises" / "06_geada_por_mes.sql").read_text(encoding="utf-8"))


@st.cache_data(ttl=CACHE_LONGO, show_spinner=False)
def tendencia_climatica() -> pd.DataFrame:
    return consultar((config.DIR_SQL / "analises" / "08_tendencia_climatica.sql").read_text(encoding="utf-8"))


@st.cache_data(ttl=CACHE_LONGO, show_spinner=False)
def chuva_mensal_vs_normal() -> pd.DataFrame:
    """Chuva dos últimos 12 meses (A714 + NASA calibrada) contra a normal 1991–2020."""
    return consultar(
        """
        WITH mensal AS (
            SELECT date_trunc('month', data) AS mes, sum(chuva_mm) AS chuva_mm
            FROM analytics.fato_clima_itapeva GROUP BY 1
        ),
        normal AS (
            SELECT month(mes) AS m, avg(chuva_mm) AS normal_mm FROM mensal
            WHERE year(mes) BETWEEN 1991 AND 2020 GROUP BY 1
        )
        SELECT mes, chuva_mm, normal_mm
        FROM mensal JOIN normal ON normal.m = month(mensal.mes)
        WHERE mes >= date_trunc('month', current_date) - INTERVAL 12 MONTH
          AND mes < date_trunc('month', current_date)
        ORDER BY mes
        """
    )


def ultima_atualizacao() -> pd.Timestamp | None:
    df = consultar("SELECT max(emitida_em) AS t FROM raw.previsao_diaria")
    return df["t"].iloc[0]


def atualizar_previsao() -> None:
    """Baixa a previsão nova (Open-Meteo) e limpa o cache. Usa conexão de escrita curta."""
    from app import atualizacao
    from core.db import conectar

    with conectar() as con:
        atualizacao.atualizar(con)  # previsão + estimativas + central de alertas
    st.cache_data.clear()


# ----------------------------------------------------------------------------------------
# Gestão da propriedade (Fase 4)
# ----------------------------------------------------------------------------------------
CACHE_GESTAO = 60


def gravar(funcao, *args, **kwargs):
    """Executa uma função de app.gestao numa conexão de escrita curta e limpa o cache.

    Devolve (ok, resultado_ou_mensagem). Se o ETL estiver gravando no banco ao mesmo
    tempo, o DuckDB recusa o acesso; o usuário recebe uma mensagem clara em vez de erro.
    """
    from core.db import conectar

    try:
        with conectar() as con:
            resultado = funcao(con, *args, **kwargs)
    except duckdb.IOException:
        return False, "O banco está ocupado (atualização de dados em andamento). Tente de novo em 1 minuto."
    except (ValueError, duckdb.ConstraintException) as erro:
        return False, f"Não foi possível salvar: {erro}"
    st.cache_data.clear()
    return True, resultado


@st.cache_data(ttl=CACHE_GESTAO, show_spinner=False)
def propriedades() -> pd.DataFrame:
    return consultar("SELECT id, nome, demo FROM fazenda.propriedade ORDER BY demo, id")


@st.cache_data(ttl=CACHE_GESTAO, show_spinner=False)
def talhoes(propriedade_id: int) -> pd.DataFrame:
    return consultar("SELECT * FROM fazenda.talhao WHERE propriedade_id = ? AND ativo ORDER BY nome", [propriedade_id])


@st.cache_data(ttl=CACHE_GESTAO, show_spinner=False)
def plantios(propriedade_id: int) -> pd.DataFrame:
    return consultar(
        "SELECT * FROM fazenda.vw_plantio WHERE propriedade_id = ? ORDER BY safra DESC, temporada, talhao",
        [propriedade_id],
    )


@st.cache_data(ttl=CACHE_GESTAO, show_spinner=False)
def resultado(propriedade_id: int) -> pd.DataFrame:
    return consultar(
        "SELECT * FROM fazenda.vw_resultado_plantio WHERE propriedade_id = ? ORDER BY safra DESC, temporada, talhao",
        [propriedade_id],
    )


@st.cache_data(ttl=CACHE_GESTAO, show_spinner=False)
def custo_por_categoria(propriedade_id: int, safra: str, cultura: str) -> pd.DataFrame:
    """R$/ha por categoria: média da fazenda (plantios da cultura na safra) × referência CONAB."""
    return consultar(
        """
        WITH fazenda AS (
            SELECT c.categoria, sum(c.valor) / any_value(a.area) AS fazenda_ha
            FROM fazenda.vw_custo_plantio c
            JOIN fazenda.vw_plantio p ON p.id = c.plantio_id
            CROSS JOIN (SELECT sum(area_efetiva_ha) AS area FROM fazenda.vw_plantio
                        WHERE propriedade_id = ? AND safra = ? AND cultura = ?) a
            WHERE p.propriedade_id = ? AND p.safra = ? AND p.cultura = ?
            GROUP BY c.categoria
        ),
        conab AS (
            SELECT categoria, valor_ha AS conab_ha FROM analytics.custo_referencia
            WHERE cultura = ? AND categoria NOT IN ('custo_variavel', 'custo_operacional', 'custo_total',
                                                   'renda_fatores', 'arrendamento')
        )
        SELECT categoria, coalesce(fazenda_ha, 0) AS fazenda_ha, coalesce(conab_ha, 0) AS conab_ha
        FROM fazenda FULL JOIN conab USING (categoria)
        WHERE coalesce(fazenda_ha, 0) + coalesce(conab_ha, 0) > 0
        ORDER BY coalesce(fazenda_ha, conab_ha) DESC
        """,
        [propriedade_id, safra, cultura, propriedade_id, safra, cultura, cultura],
    )


@st.cache_data(ttl=CACHE_LONGO, show_spinner=False)
def referencia_conab() -> pd.DataFrame:
    return consultar("SELECT DISTINCT cultura, local, mes_referencia, produtividade_sc_ha FROM analytics.custo_referencia")


@st.cache_data(ttl=CACHE_LONGO, show_spinner=False)
def produtividade_municipal() -> pd.DataFrame:
    """Média dos últimos 5 anos válidos de Itapeva (IBGE/PAM), por cultura."""
    return consultar(
        """
        SELECT cultura, avg(rendimento_sc_ha) AS itapeva_sc_ha
        FROM (SELECT *, row_number() OVER (PARTITION BY cultura ORDER BY ano DESC) AS n
              FROM analytics.fato_producao
              WHERE nivel = 'municipio' AND codigo_local = ? AND NOT suspeito_repeticao AND rendimento_sc_ha > 0)
        WHERE n <= 5 GROUP BY cultura
        """,
        [config.CODIGO_ITAPEVA],
    )


@st.cache_data(ttl=CACHE_GESTAO, show_spinner=False)
def estadio(propriedade_id: int) -> pd.DataFrame:
    return consultar("SELECT * FROM fazenda.vw_estadio_atual WHERE propriedade_id = ? ORDER BY talhao", [propriedade_id])


@st.cache_data(ttl=CACHE_GESTAO, show_spinner=False)
def caderno(propriedade_id: int) -> pd.DataFrame:
    return consultar(
        """
        SELECT o.data, p.talhao, p.cultura, p.safra, o.tipo, o.produto, o.dose, o.unidade, o.custo_total,
               o.categoria_custo, o.observacao, 'operação' AS registro
        FROM fazenda.operacao o JOIN fazenda.vw_plantio p ON p.id = o.plantio_id
        WHERE p.propriedade_id = ?
        UNION ALL
        SELECT c.data, coalesce(p.talhao, 'propriedade'), p.cultura, c.safra, 'despesa', c.descricao, NULL, NULL,
               c.valor, c.categoria, NULL, 'despesa'
        FROM fazenda.custo c LEFT JOIN fazenda.vw_plantio p ON p.id = c.plantio_id
        WHERE c.propriedade_id = ?
        UNION ALL
        SELECT oc.data, p.talhao, p.cultura, p.safra, 'ocorrência: ' || oc.tipo, oc.descricao, oc.severidade, NULL,
               NULL, NULL, NULL, 'ocorrência'
        FROM fazenda.ocorrencia oc JOIN fazenda.vw_plantio p ON p.id = oc.plantio_id
        WHERE p.propriedade_id = ?
        ORDER BY data DESC
        """,
        [propriedade_id, propriedade_id, propriedade_id],
    )


@st.cache_data(ttl=CACHE_GESTAO, show_spinner=False)
def vendas(propriedade_id: int) -> pd.DataFrame:
    return consultar("SELECT * FROM fazenda.venda WHERE propriedade_id = ? ORDER BY data DESC", [propriedade_id])


@st.cache_data(ttl=CACHE_GESTAO, show_spinner=False)
def precos_referencia() -> pd.DataFrame:
    return consultar("SELECT * FROM fazenda.preco_referencia ORDER BY cultura")


# ----------------------------------------------------------------------------------------
# Alertas e estimativa de safra (Fase 6)
# ----------------------------------------------------------------------------------------


@st.cache_data(ttl=CACHE_GESTAO, show_spinner=False)
def alertas_ativos(propriedade_id: int | None) -> pd.DataFrame:
    return consultar(
        """SELECT * FROM notif.vw_alertas_ativos
           WHERE propriedade_id IS NULL OR propriedade_id = ?
           ORDER BY novo DESC, prioridade, atualizado_em DESC""", [propriedade_id])


@st.cache_data(ttl=CACHE_GESTAO, show_spinner=False)
def alertas_resolvidos(propriedade_id: int | None, dias: int = 14) -> pd.DataFrame:
    return consultar(
        """SELECT * FROM notif.alerta
           WHERE resolvido_em IS NOT NULL AND resolvido_em >= current_timestamp - to_days(?)
             AND (propriedade_id IS NULL OR propriedade_id = ?)
           ORDER BY resolvido_em DESC""", [dias, propriedade_id])


@st.cache_data(ttl=1800, show_spinner=False)
def estimativas(propriedade_id: int):
    """Estimativas de safra das lavouras plantadas (balanço hídrico + anos análogos). Cache de 30 min."""
    from analytics import balanco_hidrico

    with conectar(leitura=True) as con:
        lista = balanco_hidrico.estimar_propriedade(con, propriedade_id)
        return lista, balanco_hidrico.tabela_estimativas(lista, con)


def atualizar_se_preciso() -> str | None:
    """Ao abrir o painel: se a previsão tiver mais de 6 h, atualiza previsão + alertas. Uma vez por sessão."""
    import os

    if st.session_state.get("_auto_atualizado") or os.getenv("SAFRAVIVA_SEM_ATUALIZAR"):
        return None
    st.session_state["_auto_atualizado"] = True
    from app import atualizacao

    with conectar(leitura=True) as con:
        velha = atualizacao.previsao_velha(con)
    if not velha:
        return None
    ok, msg = gravar(atualizacao.atualizar)
    return None if ok else msg


# ----------------------------------------------------------------------------------------
# Cotações
# ----------------------------------------------------------------------------------------
IDADE_MAX_BOLSA_MIN = 15
IDADE_MAX_CEPEA_H = 12


def cotacoes_atualizar_se_preciso() -> str | None:
    """Bolsa/dólar com mais de 15 min → atualização rápida; CEPEA com mais de 12 h → carga completa."""
    import os

    from etl import cotacoes

    if os.getenv("SAFRAVIVA_SEM_ATUALIZAR"):  # testes: sem rede e sem gravar
        return None

    with conectar(leitura=True) as con:
        ult = con.execute("SELECT max(carregado_em) FROM raw.cotacao_ultima").fetchone()[0]
        cep = con.execute("SELECT max(carregado_em) FROM raw.cotacao_diaria WHERE serie LIKE 'cepea_%'").fetchone()[0]
    agora = pd.Timestamp.now()
    if cep is None or agora - pd.Timestamp(cep) > pd.Timedelta(hours=IDADE_MAX_CEPEA_H):
        ok, msg = gravar(cotacoes.executar)
    elif ult is None or agora - pd.Timestamp(ult) > pd.Timedelta(minutes=IDADE_MAX_BOLSA_MIN):
        ok, msg = gravar(cotacoes.executar_rapido)
    else:
        return None
    return None if ok else msg


@st.cache_data(ttl=60, show_spinner=False)
def cotacao_resumo() -> pd.DataFrame:
    """Último valor de cada série diária, com a variação sobre o dia anterior."""
    return consultar("""
        WITH r AS (SELECT *, row_number() OVER (PARTITION BY serie ORDER BY data DESC) AS n FROM raw.cotacao_diaria)
        SELECT a.serie, a.cultura, a.nome, a.data, coalesce(a.valor_rs_sc, a.valor) AS valor,
               100 * (coalesce(a.valor_rs_sc, a.valor) / coalesce(b.valor_rs_sc, b.valor) - 1) AS variacao_pct, a.fonte
        FROM r a LEFT JOIN r b ON b.serie = a.serie AND b.n = 2
        WHERE a.n = 1""")


@st.cache_data(ttl=60, show_spinner=False)
def cotacao_bolsa() -> pd.DataFrame:
    return consultar("SELECT * FROM raw.cotacao_ultima")


@st.cache_data(ttl=60, show_spinner=False)
def cotacao_intradia(serie: str) -> pd.DataFrame:
    return consultar("SELECT ts, valor FROM raw.cotacao_intradia WHERE serie = ? ORDER BY ts", [serie])


@st.cache_data(ttl=600, show_spinner=False)
def cotacao_historico(series: tuple[str, ...], desde: str) -> pd.DataFrame:
    return consultar("""SELECT serie, nome, data, coalesce(valor_rs_sc, valor) AS valor FROM raw.cotacao_diaria
                        WHERE serie IN (SELECT unnest(?)) AND data >= CAST(? AS DATE) ORDER BY data""",
                     [list(series), desde])


@st.cache_data(ttl=3600, show_spinner=False)
def cotacao_sazonalidade(serie: str) -> pd.DataFrame:
    return consultar("""
        WITH m AS (SELECT year(data) AS ano, month(data) AS mes, avg(coalesce(valor_rs_sc, valor)) AS v
                   FROM raw.cotacao_diaria WHERE serie = ? AND data >= current_date - INTERVAL 10 YEAR GROUP BY 1, 2),
             a AS (SELECT ano, avg(v) AS va FROM m GROUP BY 1 HAVING count(*) = 12)
        SELECT mes, 100 * (avg(v / va) - 1) AS desvio_pct FROM m JOIN a USING (ano) GROUP BY mes ORDER BY mes""", [serie])
