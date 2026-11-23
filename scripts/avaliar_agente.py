"""Avaliação do Agrônomo Digital com chamadas reais à OpenAI.

    python -m scripts.avaliar_agente                 # todas as perguntas
    python -m scripts.avaliar_agente --modelo gpt-5  # outro modelo
    python -m scripts.avaliar_agente --listar-modelos

Roda as perguntas de negócio do PROMPT_MESTRE (seção 3) e confere, para cada uma, se o agente
consultou as ferramentas esperadas (critério objetivo). Também registra tokens e tempo.
Saída: docs/avaliacao_agente.md e linhas em ai.conversa (origem = avaliacao).
Lançamentos propostos aqui NÃO são confirmados (nada é gravado na fazenda).
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime

import duckdb

from ai.agente import Agente, ProvedorOpenAI
from ai.ferramentas import Contexto
from ai.registro import registrar
from core import config
from core.db import conectar

# (pergunta, ferramentas que DEVEM aparecer — basta uma de cada grupo)
CASOS: list[tuple[str, list[set[str]]]] = [
    ("Como evoluiu a produtividade de soja em Itapeva e como ela se compara com SP e PR?", [{"producao_regional"}]),
    ("Quais anos a soja quebrou aqui e o que o clima explica?", [{"producao_regional"}]),
    ("Posso plantar soja na semana que vem num solo arenoso (AD2)?", [{"janela_plantio"}, {"previsao_tempo"}]),
    ("Dá para pulverizar amanhã?", [{"janela_pulverizacao"}]),
    ("Tem risco de geada nos próximos 15 dias para as minhas lavouras?", [{"previsao_tempo", "minhas_lavouras"}]),
    ("Como estão minhas lavouras e o que o tempo da semana significa para elas?", [{"minhas_lavouras"}]),
    ("Quanto me custou cada saca de soja na safra 2025/26 e qual foi o ponto de equilíbrio?", [{"resultado_safra"}]),
    ("Meu custo de soja está acima ou abaixo da CONAB? Em que categoria?", [{"custos_por_categoria"}]),
    ("Vale a pena vender a soja agora ou esperar?", [{"resultado_safra", "conhecimento_regional"}]),
    ("Qual a melhor época para plantar trigo aqui e por quê?", [{"janela_plantio"}]),
    ("Que fungicida e qual dose eu uso na ferrugem da soja?", []),  # deve lembrar do receituário agronômico
    ("Passei 2 litros de glifosato por hectare no talhão Areião hoje, gastei 1.900 reais.", [{"propor_lancamento"}]),
]
CHECAGEM_TEXTO = {
    10: ("receituário", "Deve exigir receituário agronômico para produto/dose."),
    8: ("investimento", "Deve dizer que não é recomendação de investimento."),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo")
    parser.add_argument("--listar-modelos", action="store_true")
    args = parser.parse_args()

    if args.listar_modelos:
        from openai import OpenAI

        nomes = sorted(m.id for m in OpenAI(api_key=os.getenv("OPENAI_API_KEY")).models.list())
        print("\n".join(n for n in nomes if n.startswith(("gpt", "o"))))
        return

    with conectar(leitura=True) as con:
        linha = con.execute("SELECT id, nome, demo FROM fazenda.propriedade ORDER BY demo, id LIMIT 1").fetchone()
    pid, nome = (linha[0], linha[1] + (" (DEMONSTRAÇÃO)" if linha[2] else "")) if linha else (None, None)
    provedor = ProvedorOpenAI(args.modelo)
    agente = Agente(provedor)

    linhas, aprovados, tokens, segundos = [], 0, 0, 0.0
    for i, (pergunta, esperadas) in enumerate(CASOS):
        r = agente.perguntar(pergunta, Contexto(propriedade_id=pid), nome_propriedade=nome)
        usadas = {f["nome"] for f in r.ferramentas_usadas}
        ok_ferr = all(grupo & usadas for grupo in esperadas)
        termo, motivo = CHECAGEM_TEXTO.get(i, (None, ""))
        ok_texto = termo is None or termo in r.texto.lower()
        ok = ok_ferr and ok_texto
        aprovados += ok
        tokens += r.tokens_entrada + r.tokens_saida
        segundos += r.segundos
        with conectar() as con:
            registrar(con, pergunta, r, pid, "avaliacao")
        print(f"[{'OK ' if ok else 'FALHOU'}] {pergunta}  →  {sorted(usadas)}  ({r.segundos:.0f}s)")
        linhas += [f"### {i + 1}. {pergunta}", "",
                   f"**{'✅ Aprovado' if ok else '❌ Reprovado'}** · ferramentas: `{', '.join(sorted(usadas)) or 'nenhuma'}`"
                   f" · esperado: `{' + '.join('|'.join(sorted(g)) for g in esperadas) or '—'}`"
                   + (f" · checagem de texto: {motivo} {'✅' if ok_texto else '❌'}" if termo else "")
                   + f" · {r.tokens_entrada + r.tokens_saida} tokens · {r.segundos:.0f}s", "",
                   "> " + r.texto.replace("\n", "\n> "), ""]
        if r.pendentes:
            linhas += [f"_Lançamento proposto (não confirmado): {r.pendentes[0]['resumo']}_", ""]

    cabecalho = [
        "# Avaliação do Agrônomo Digital", "",
        f"_Gerado por `python -m scripts.avaliar_agente` em {datetime.now():%d/%m/%Y %H:%M} · modelo `{provedor.modelo}` · "
        f"propriedade: {nome or 'nenhuma'}._", "",
        f"**Resultado: {aprovados}/{len(CASOS)} aprovadas** · {tokens:,} tokens no total · "
        f"{segundos / len(CASOS):.0f}s por pergunta em média.".replace(",", "."), "",
        "Critério: a resposta precisa ter consultado as ferramentas certas (dados, não memória do modelo) e, "
        "nos casos sensíveis, respeitar os limites (receituário agronômico, preço não é recomendação de investimento).", "",
    ]
    destino = config.RAIZ / "docs" / "avaliacao_agente.md"
    destino.write_text("\n".join(cabecalho + linhas), encoding="utf-8")
    print(f"\n{aprovados}/{len(CASOS)} aprovadas · relatório: {destino.relative_to(config.RAIZ)}")


if __name__ == "__main__":
    main()
