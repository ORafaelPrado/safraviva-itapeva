"""Modelo clima × produtividade — painel dos municípios da região.

    log(rendimento) = efeito do município + tendência tecnológica + índices climáticos por fase

* Efeito fixo de município: absorve solo, relevo e perfil de produtor (o que não muda no tempo).
* Tendência linear no ano: absorve o ganho genético e tecnológico.
* Erros-padrão agrupados por ano: o clima de um ano atinge todos os municípios ao mesmo tempo,
  então as observações do mesmo ano não são independentes.

A validação é temporal (expanding window): para prever o ano t, o modelo só vê anos < t.
Ele é comparado a uma base que só tem tendência + município, para medir quanto o clima explica.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# Variáveis finais por cultura, escolhidas pela validação temporal (docs/insights.md, insight 7):
# com 5 índices por cultura o modelo sobreajustava e perdia para a base fora da amostra;
# ficam só os de sinal físico claro na fase crítica.
VARIAVEIS = {
    "soja": ["balanco_mm__enchimento", "balanco_mm__florescimento"],
    "milho": ["balanco_mm__vegetativo", "balanco_mm__enchimento"],
    "trigo": ["dias_tmin_le3__florescimento"],
}

INDICES = ["chuva_mm", "balanco_mm", "max_veranico_dias", "dias_tmax_ge32", "dias_tmin_le3", "tmed_c"]


@dataclass
class Resultado:
    cultura: str
    dados: pd.DataFrame
    modelo: object
    base: object
    validacao: pd.DataFrame

    @property
    def coeficientes(self) -> pd.DataFrame:
        """Efeito de +1 desvio-padrão de cada índice, em % de rendimento."""
        params, conf, p = self.modelo.params, self.modelo.conf_int(), self.modelo.pvalues
        linhas = []
        for var in VARIAVEIS[self.cultura]:
            dp = self.dados[var].std()
            linhas.append({
                "indice": var,
                "efeito_1dp_pct": 100 * (np.exp(params[var] * dp) - 1),
                "ic95_inf_pct": 100 * (np.exp(conf.loc[var, 0] * dp) - 1),
                "ic95_sup_pct": 100 * (np.exp(conf.loc[var, 1] * dp) - 1),
                "p_valor": p[var],
                "desvio_padrao": dp,
            })
        return pd.DataFrame(linhas).sort_values("p_valor")


def carregar_painel(con: duckdb.DuckDBPyConnection, cultura: str, ano_min: int = 1990) -> pd.DataFrame:
    """Uma linha por município × ano, com o rendimento e os índices por fase em colunas largas."""
    producao = con.execute(
        """
        SELECT codigo_local AS codigo_ibge, nome_local, ano, rendimento_kg_ha, area_colhida_ha
        FROM analytics.fato_producao
        WHERE nivel = 'municipio' AND cultura = ? AND ano >= ?
          AND NOT suspeito_repeticao AND rendimento_kg_ha > 0 AND area_colhida_ha >= 500
        """,
        [cultura, ano_min],
    ).df()
    indices = con.execute(
        f"""
        SELECT codigo_ibge, ano_pam AS ano, fase, {", ".join(INDICES)}
        FROM analytics.indices_fase
        WHERE serie = 'nasa' AND cultura = ? AND cobertura >= 0.9
        """,
        [cultura],
    ).df()
    largo = indices.pivot_table(index=["codigo_ibge", "ano"], columns="fase", values=INDICES)
    largo.columns = [f"{indice}__{fase}" for indice, fase in largo.columns]
    painel = producao.merge(largo.reset_index(), on=["codigo_ibge", "ano"], how="inner")
    painel["log_rend"] = np.log(painel["rendimento_kg_ha"])
    painel["municipio"] = painel["codigo_ibge"].astype(str)
    return painel.dropna(subset=VARIAVEIS[cultura]).reset_index(drop=True)


def _formula(cultura: str, com_clima: bool = True) -> str:
    termos = ["C(municipio)", "ano"] + (VARIAVEIS[cultura] if com_clima else [])
    return "log_rend ~ " + " + ".join(termos)


def _ajustar(dados: pd.DataFrame, formula: str):
    return smf.ols(formula, data=dados).fit(cov_type="cluster", cov_kwds={"groups": dados["ano"]})


def validar_temporal(dados: pd.DataFrame, cultura: str, primeiro_teste: int = 2008) -> pd.DataFrame:
    """Expanding window: para cada ano ≥ primeiro_teste, treina com anos anteriores e prevê o ano."""
    linhas = []
    for ano in sorted(a for a in dados["ano"].unique() if a >= primeiro_teste):
        treino, teste = dados[dados["ano"] < ano], dados[dados["ano"] == ano]
        teste = teste[teste["municipio"].isin(treino["municipio"])]
        if teste.empty:
            continue
        for nome, com_clima in (("clima", True), ("base", False)):
            ajuste = smf.ols(_formula(cultura, com_clima), data=treino).fit()
            prev = np.exp(ajuste.predict(teste))
            erro = (prev - teste["rendimento_kg_ha"]) / teste["rendimento_kg_ha"]
            linhas.append({"ano": ano, "modelo": nome, "n": len(teste),
                           "erro_abs_medio_pct": 100 * erro.abs().mean(), "vies_pct": 100 * erro.mean()})
    return pd.DataFrame(linhas)


def ajustar(con: duckdb.DuckDBPyConnection, cultura: str) -> Resultado:
    dados = carregar_painel(con, cultura)
    return Resultado(
        cultura=cultura,
        dados=dados,
        modelo=_ajustar(dados, _formula(cultura)),
        base=_ajustar(dados, _formula(cultura, com_clima=False)),
        validacao=validar_temporal(dados, cultura),
    )


def resumo_validacao(resultado: Resultado) -> pd.Series:
    v = resultado.validacao.pivot_table(index="ano", columns="modelo", values="erro_abs_medio_pct")
    return pd.Series({
        "anos_testados": len(v),
        "erro_medio_base_pct": v["base"].mean(),
        "erro_medio_clima_pct": v["clima"].mean(),
        "reducao_erro_pct": 100 * (1 - v["clima"].mean() / v["base"].mean()),
        "anos_em_que_clima_ganha": int((v["clima"] < v["base"]).sum()),
    })
