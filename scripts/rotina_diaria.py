"""Rotina diária do SafraViva: atualiza tudo sem ninguém abrir o painel.

    python -m scripts.rotina_diaria            # o que o agendador roda todo dia às 6h
    python -m scripts.rotina_diaria --forcar-resumo

Passos: previsão (Open-Meteo, inclui os últimos 45 dias) → NASA POWER → cotações (CEPEA, Chicago, dólar) → INMET do ano corrente (no dia 5
de cada mês, quando o pacote mensal costuma sair) → transformações SQL → estimativas de safra → central de
alertas → às segundas, o resumo semanal do Agrônomo Digital (se houver OPENAI_API_KEY).
Log em data/logs/rotina_AAAA-MM-DD.log.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import date

from app import atualizacao
from core import config
from core.db import conectar


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forcar-resumo", action="store_true")
    args = parser.parse_args()

    pasta_log = config.DIR_DADOS / "logs"
    pasta_log.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        handlers=[logging.FileHandler(pasta_log / f"rotina_{date.today():%Y-%m-%d}.log", encoding="utf-8"),
                                  logging.StreamHandler()])
    log = logging.getLogger("rotina")

    hoje = date.today()
    fontes = ("previsao", "nasa", "cotacoes") + (("inmet",) if hoje.day == 5 else ())
    with conectar() as con:
        resumo = atualizacao.atualizar(con, fontes, transformar=True)
    log.info("Atualização: %s", json.dumps(resumo, ensure_ascii=False, default=str))

    if (hoje.weekday() == 0 or args.forcar_resumo) and os.getenv("OPENAI_API_KEY"):
        from ai import resumo_semanal

        try:
            resumo_semanal.main()
        except Exception as erro:  # noqa: BLE001
            log.warning("Resumo semanal falhou: %s", erro)


if __name__ == "__main__":
    main()
