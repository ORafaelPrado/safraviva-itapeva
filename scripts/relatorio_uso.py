"""Relatório de uso do painel (docs/design/passo-6-auditoria-conversao.md).

    python -m scripts.relatorio_uso            # últimos 30 dias
    python -m scripts.relatorio_uso --dias 7

Mostra: dias de uso por semana (a métrica principal), o funil da sessão
(viu o veredito → clicou numa chamada → agiu: pergunta à IA ou lançamento) e a versão A/B/C.
Lê `uso.evento`; não grava nada.
"""

from __future__ import annotations

import argparse

import duckdb
import pandas as pd

from app.eventos import DDL
from core.db import conectar

SQL_SESSOES = """
WITH e AS (SELECT * FROM uso.evento WHERE ts >= current_timestamp::TIMESTAMP - to_days(CAST(? AS INTEGER)))
SELECT sessao,
       min(ts)::DATE                                                                AS dia,
       any_value(dispositivo)                                                       AS dispositivo,
       max(CASE WHEN evento = 'ab_view' THEN replace(detalhe, 'v=', '') END)         AS versao,
       bool_or(evento = 'pagina_vista' AND pagina = 'inicio')                       AS viu_veredito,
       bool_or(evento = 'cta_click')                                                AS clicou,
       bool_or(evento IN ('pergunta_ia', 'lancamento_salvo'))                       AS agiu,
       count(DISTINCT pagina) FILTER (WHERE evento = 'pagina_vista')                AS telas
FROM e GROUP BY sessao
"""


def sessoes(con: duckdb.DuckDBPyConnection, dias: int = 30) -> pd.DataFrame:
    con.execute(DDL.read_text(encoding="utf-8"))  # tabela pode ainda não existir num banco novo
    return con.execute(SQL_SESSOES, [dias]).df()


def resumo(s: pd.DataFrame) -> dict:
    """Números do funil a partir da tabela de sessões (função pura, testada)."""
    if s.empty:
        return {"sessoes": 0}
    dias = pd.to_datetime(s["dia"])
    semanas = max(1.0, (dias.max() - dias.min()).days / 7 + 1 / 7)
    pct = lambda col: round(100 * s[col].mean(), 0)  # noqa: E731
    por_versao = (s.dropna(subset=["versao"]).groupby("versao")
                  .agg(sessoes=("sessao", "count"), clicou=("clicou", "mean"), agiu=("agiu", "mean")))
    return {
        "sessoes": len(s),
        "dias_com_uso": int(dias.dt.date.nunique()),
        "dias_por_semana": round(dias.dt.date.nunique() / semanas, 1),
        "viu_veredito_pct": pct("viu_veredito"),
        "clicou_pct": pct("clicou"),
        "agiu_pct": pct("agiu"),
        "duas_telas_ou_mais_pct": round(100 * (s["telas"] >= 2).mean(), 0),
        "celular_pct": round(100 * (s["dispositivo"] == "celular").mean(), 0),
        "por_versao": por_versao.round(2).to_dict("index"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dias", type=int, default=30)
    args = ap.parse_args()
    with conectar() as con:
        r = resumo(sessoes(con, args.dias))
    if not r["sessoes"]:
        print(f"Nenhum uso registrado nos últimos {args.dias} dias.")
        return
    print(f"Últimos {args.dias} dias · {r['sessoes']} sessões · {r['dias_com_uso']} dias com uso "
          f"· {r['dias_por_semana']} dias/semana (meta: 4)")
    print(f"Funil: viu o veredito {r['viu_veredito_pct']:.0f}% → clicou {r['clicou_pct']:.0f}% → agiu {r['agiu_pct']:.0f}%")
    print(f"Visitou 2+ telas: {r['duas_telas_ou_mais_pct']:.0f}% · no celular: {r['celular_pct']:.0f}%")
    for versao, v in r["por_versao"].items():
        print(f"  versão {versao}: {v['sessoes']} sessões · clicou {100 * v['clicou']:.0f}% · agiu {100 * v['agiu']:.0f}%")


if __name__ == "__main__":
    main()
