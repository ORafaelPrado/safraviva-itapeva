"""Resumo semanal do Agrônomo Digital.

    python -m ai.resumo_semanal            # gera, salva em data/processed/resumos/ e registra em ai.conversa

Usa o mesmo agente e as mesmas ferramentas do chat, com um pedido fixo. Na Fase 6 este
texto vai ser enviado automaticamente para o celular toda segunda de manhã.
"""

from __future__ import annotations

from datetime import date

import duckdb

from ai.agente import Agente, Provedor, ProvedorOpenAI, Resultado
from ai.ferramentas import Contexto
from core import config
from core.db import conectar

PEDIDO = """Monte o RESUMO DA SEMANA para o produtor, para ler no celular em 1 minuto. Use as ferramentas
(previsão do tempo de 7 dias, janela de pulverização, minhas lavouras, época de plantio das culturas
que estiverem perto da janela, e o resultado da safra atual se houver fazenda). Formato:

**Tempo da semana** — 2 linhas (chuva total, dias de chuva, risco de geada/calor/veranico).
**Lavouras** — 1 linha por talhão com a fase e o que o tempo significa para ela.
**Tarefas sugeridas** — até 4 itens práticos com dia (ex.: "qui: melhor janela para pulverizar, 7h–11h").
**Atenção** — só se houver algo importante (janela de plantio fechando, chuva na colheita, custo acima da CONAB).
Termine com as fontes numa linha."""


def gerar(provedor: Provedor, propriedade_id: int | None, nome_propriedade: str | None = None) -> Resultado:
    ctx = Contexto(propriedade_id=propriedade_id)
    return Agente(provedor).perguntar(PEDIDO, ctx, nome_propriedade=nome_propriedade)


def main() -> None:
    from ai.registro import registrar

    with conectar(leitura=True) as con:
        linha = con.execute("SELECT id, nome, demo FROM fazenda.propriedade ORDER BY demo, id LIMIT 1").fetchone()
    pid, nome = (linha[0], linha[1] + (" (DEMONSTRAÇÃO)" if linha[2] else "")) if linha else (None, None)
    resultado = gerar(ProvedorOpenAI(), pid, nome)
    destino = config.DIR_PROCESSED / "resumos" / f"{date.today():%Y-%m-%d}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(resultado.texto, encoding="utf-8")
    with conectar() as con:
        registrar(con, "resumo semanal", resultado, pid, "resumo_semanal")
    print(resultado.texto)
    print(f"\n[{resultado.modelo} · {resultado.tokens_entrada}+{resultado.tokens_saida} tokens · "
          f"{resultado.segundos:.0f}s · salvo em {destino.relative_to(config.RAIZ)}]")


if __name__ == "__main__":
    main()
