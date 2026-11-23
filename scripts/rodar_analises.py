"""Executa as consultas de sql/analises/ e publica os resultados.

    python -m scripts.rodar_analises            # todas
    python -m scripts.rodar_analises 05 07      # só as que começam com 05 e 07

Saídas: data/processed/analises/<nome>.csv e docs/analises_resultados.md
(gerado; não editar à mão).
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd

from core import config
from core.db import conectar

DIR_ANALISES = config.DIR_SQL / "analises"
DIR_SAIDA = config.DIR_PROCESSED / "analises"
RELATORIO = config.RAIZ / "docs" / "analises_resultados.md"


def pergunta(sql: str) -> str:
    """Primeira linha '-- Pergunta: ...' do arquivo."""
    for linha in sql.splitlines():
        if linha.startswith("-- Pergunta:"):
            return linha.removeprefix("-- Pergunta:").strip()
    return ""


def tabela_markdown(df: pd.DataFrame, max_linhas: int = 40) -> str:
    def fmt(v) -> str:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "–"
        if isinstance(v, float):
            return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".").rstrip("0").rstrip(",")
        return str(v)

    linhas = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    for registro in df.head(max_linhas).itertuples(index=False):
        linhas.append("| " + " | ".join(fmt(v) for v in registro) + " |")
    if len(df) > max_linhas:
        linhas.append(f"\n_… {len(df) - max_linhas} linhas omitidas (ver CSV)._")
    return "\n".join(linhas)


def executar(con: duckdb.DuckDBPyConnection, arquivos: list[Path]) -> list[tuple[Path, str, pd.DataFrame]]:
    DIR_SAIDA.mkdir(parents=True, exist_ok=True)
    resultados = []
    for arquivo in arquivos:
        sql = arquivo.read_text(encoding="utf-8")
        df = con.execute(sql).df()
        df.to_csv(DIR_SAIDA / f"{arquivo.stem}.csv", index=False, encoding="utf-8")
        resultados.append((arquivo, pergunta(sql), df))
        print(f"{arquivo.stem:<36} {len(df):>4} linhas")
    return resultados


def publicar(resultados: list[tuple[Path, str, pd.DataFrame]]) -> None:
    partes = [
        "# Resultados das análises SQL",
        "",
        f"_Gerado automaticamente por `python -m scripts.rodar_analises` em {datetime.now():%d/%m/%Y %H:%M}. "
        "Não edite à mão; a interpretação está em [insights.md](insights.md)._",
    ]
    for arquivo, texto, df in resultados:
        partes += ["", f"## {arquivo.stem}", "", f"**{texto}**", "",
                   f"Consulta: [`sql/analises/{arquivo.name}`](../sql/analises/{arquivo.name})", "",
                   tabela_markdown(df)]
    RELATORIO.write_text("\n".join(partes) + "\n", encoding="utf-8")


def main() -> None:
    filtros = sys.argv[1:]
    arquivos = [
        a for a in sorted(DIR_ANALISES.glob("*.sql"))
        if not filtros or any(a.name.startswith(f) for f in filtros)
    ]
    with conectar(leitura=True) as con:
        resultados = executar(con, arquivos)
    if not filtros:
        publicar(resultados)
        print(f"Relatório: {RELATORIO.relative_to(config.RAIZ)}")


if __name__ == "__main__":
    main()
