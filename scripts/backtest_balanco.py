"""Backtest do balanço hídrico: o modelo explica as safras boas e ruins do passado?

    python -m scripts.backtest_balanco

Para cada município da região × safra (1991→), simula uma lavoura típica (plantio na data típica da
região, solo AD4) com o clima REAL do ciclo e compara a produtividade relativa do modelo (Ya/Ym) com
o desvio da produtividade do IBGE em relação à média dos 5 anos anteriores (que tira a tendência
tecnológica). Compara com a regressão da Fase 2 (melhor índice isolado: |r| ≈ 0,2).

Saída: docs/backtest_balanco.md
"""

from __future__ import annotations

from datetime import date

import duckdb
import numpy as np
import pandas as pd

from analytics import balanco_hidrico as bh
from core import config
from core.db import conectar

# Cultura: (temporada, mês/dia do plantio típico, ano do plantio relativo ao ano da PAM)
CASOS = {
    "soja": ("verao", (10, 25), -1),
    "milho": ("verao", (10, 1), -1),
    "trigo": ("inverno", (5, 1), 0),
}


def clima_municipio(con, serie: str, codigo: int) -> pd.DataFrame:
    df = con.execute("""SELECT data, chuva_mm, temp_c, temp_max_c, temp_min_c, radiacao_mj_m2
                        FROM analytics.clima_diario WHERE serie = ? AND codigo_ibge = ? ORDER BY data""",
                     [serie, codigo]).df()
    df["data"] = pd.to_datetime(df["data"])
    df["eto_mm"] = bh.eto_diaria(df)
    df["chuva_mm"] = df["chuva_mm"].fillna(0)
    return df[["data", "chuva_mm", "eto_mm"]].dropna()


def rodar(con) -> pd.DataFrame:
    pam = con.execute("""
        SELECT codigo_local AS codigo_ibge, nome_local, cultura, ano, desvio_vs_media_5a
        FROM analytics.fato_producao
        WHERE nivel = 'municipio' AND cultura IN ('soja', 'milho', 'trigo') AND ano >= 1991
          AND desvio_vs_media_5a IS NOT NULL AND NOT suspeito_repeticao AND area_colhida_ha >= 500
    """).df()
    linhas = []
    for (codigo, serie), grupo in [((c, "nasa"), None) for c in pam["codigo_ibge"].unique()] + [((config.CODIGO_ITAPEVA, "itapeva"), None)]:
        clima = clima_municipio(con, serie, int(codigo))
        for cultura, (temporada, (mes, dia), deslocamento) in CASOS.items():
            fases = bh.fases(con, cultura, temporada)
            alvo = pam[(pam["codigo_ibge"] == codigo) & (pam["cultura"] == cultura)]
            for r in alvo.itertuples():
                plantio = date(r.ano + deslocamento, mes, dia)
                try:
                    sim = bh.simular(clima, plantio, cultura, fases, bh.TAW_POR_AD["AD4"])
                except ValueError:
                    continue
                linhas.append({"serie": serie, "codigo_ibge": codigo, "municipio": r.nome_local, "cultura": cultura,
                               "ano": r.ano, "razao_modelo": sim.razao_produtividade,
                               "desvio_ibge": r.desvio_vs_media_5a})
    return pd.DataFrame(linhas)


def resumir(df: pd.DataFrame) -> pd.DataFrame:
    saida = []
    for (serie, cultura), g in df.groupby(["serie", "cultura"]):
        anos_ruins = g["desvio_ibge"] <= -0.15
        previu_ruim = g["razao_modelo"] <= g["razao_modelo"].quantile(0.25)
        saida.append({
            "serie": "Itapeva (A714 + NASA)" if serie == "itapeva" else "11 municípios (NASA)",
            "cultura": cultura, "n": len(g),
            "pearson_r": g["razao_modelo"].corr(g["desvio_ibge"]),
            "spearman_r": g["razao_modelo"].corr(g["desvio_ibge"], method="spearman"),
            "quebras_ibge": int(anos_ruins.sum()),
            "quebras_no_quartil_pior_do_modelo": int((anos_ruins & previu_ruim).sum()),
        })
    return pd.DataFrame(saida)


def main() -> None:
    with conectar(leitura=True) as con:
        df = rodar(con)
    resumo = resumir(df)
    print(resumo.round(2).to_string(index=False))
    ita = df[(df["serie"] == "itapeva") & (df["cultura"] == "soja")].sort_values("ano")
    linhas = ["# Backtest do balanço hídrico (FAO-56 + FAO-33)", "",
              f"_Gerado por `python -m scripts.backtest_balanco` em {pd.Timestamp.now():%d/%m/%Y %H:%M}._", "",
              "Para cada safra, o modelo simula uma lavoura típica (solo AD4, plantio na data típica: soja 25/out, "
              "milho verão 01/out, trigo 01/mai) com o **clima real** do ciclo e calcula a produtividade relativa "
              "(Ya/Ym). O resultado é comparado com o desvio da produtividade do IBGE em relação à média dos 5 anos "
              "anteriores, que tira o ganho tecnológico.", "",
              "| Série | Cultura | n | r de Pearson | r de Spearman | Quebras IBGE (≤ −15%) | …no quartil pior do modelo |",
              "|---|---|---|---|---|---|---|"]
    for r in resumo.itertuples():
        linhas.append(f"| {r.serie} | {r.cultura} | {r.n} | {r.pearson_r:.2f} | {r.spearman_r:.2f} | {r.quebras_ibge} | "
                      f"{r.quebras_no_quartil_pior_do_modelo} |")
    linhas += ["", "Referência da Fase 2: o melhor índice climático isolado tinha |r| ≈ 0,2 com o mesmo desvio.", "",
               "## Soja em Itapeva, ano a ano", "", "| Ano | Modelo (Ya/Ym) | IBGE (desvio vs 5 anos) |", "|---|---|---|"]
    for r in ita.itertuples():
        linhas.append(f"| {r.ano} | {100 * r.razao_modelo:.0f}% | {100 * r.desvio_ibge:+.0f}% |")
    (config.RAIZ / "docs" / "backtest_balanco.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("Relatório: docs/backtest_balanco.md")


if __name__ == "__main__":
    main()
