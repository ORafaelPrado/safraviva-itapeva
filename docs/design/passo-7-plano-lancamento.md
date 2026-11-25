# Passo 7: plano dos primeiros 30 dias

> **Base:** passos [1](plano-mestre-safraviva.md) · [2](passo-2-secao-principal.md) · [3](passo-3-movimento.md) · [4](passo-4-texto.md) · [5](passo-5-plano-construcao.md) · [6](passo-6-auditoria-conversao.md).
> **Adaptação:** o "lançamento" é **apresentar o app ao seu pai** e usá-lo como peça de portfólio. O dia 1 é o dia em que ele recebe o link. `[PREENCHER: data]`

## 1. Fontes de "tráfego" que você controla

| Fonte | Para quem | Como usar | Custo |
|---|---|---|---|
| **Você, ao vivo** | Seu pai | Apresentação de 15 min no celular dele: abrir o link, salvar na tela inicial, digitar a senha junto e fazer uma pergunta ao agrônomo | zero |
| Atalho na tela inicial do celular | Seu pai | Chrome → ⋮ → "Adicionar à tela inicial" (vira um ícone, como um app) | zero |
| Lembrete pessoal | Seu pai | Na 1ª semana, uma mensagem sua de manhã: "viu o SafraViva hoje?" (até o resumo no WhatsApp existir) | zero |
| README do GitHub | Portfólio | Já tem o print, os destaques e o link | zero |
| LinkedIn | Portfólio | Um post curto com o print da Hoje e o problema real (o seu pai, o campo, o sol) `[PREENCHER: quando publicar]` | zero |

## 2. Telas que pedem atenção imediata (semana 1)

1. **Abrir o link (app dormindo):** a maior trava. Na apresentação, mostre ao seu pai a tela do Streamlit em inglês e o botão de acordar, para ele não se assustar. Decisão P0-1 do passo 6.
2. **Hoje na lavoura:** confira com ele se o veredito do dia **bate com o que ele faria**. Cada vez que discordar, anote o dia e o motivo: é a melhor correção de regra que existe.
3. **Agrônomo Digital:** veja a primeira pergunta real dele e a resposta (tabela `ai.conversa`). Se a resposta errar, a correção vai para a ferramenta, como nos casos D020 e D026.
4. **Lançar:** veja se ele consegue lançar sozinho uma operação. Se travar, ensine o atalho de ditar ao agrônomo.

## 3. Feedback gastando pouco

| Meio | Quando | O que perguntar ou ver |
|---|---|---|
| **👍/👎 no veredito** (criado neste passo) | Todo dia, dentro do app | "Esse resumo ajudou?" O voto é gravado com a versão do texto (A/B/C) |
| Conversa de 10 min | Toda semana | 1) O que você olhou no app esta semana? 2) Teve algo que você não entendeu? 3) O veredito errou algum dia? |
| Olhar ele usando, sem ajudar | Uma vez, na semana 2 | Onde ele hesita, o que ele procura e não acha |
| Respostas da IA | Toda semana | Ler as perguntas dele em `ai.conversa` (são dele, não vão para o repositório) |

## 4. Métricas com pouco tráfego

Com um usuário só, **não se olha porcentagem diária**: olha-se a tendência semanal.

| Métrica | De onde vem | Meta no mês 1 |
|---|---|---|
| **Dias por semana com o veredito visto** (principal) | `relatorio_uso` | ≥ 4 |
| Ações por semana (pergunta ou lançamento) | `relatorio_uso` | ≥ 2 |
| 👍 no veredito | `relatorio_uso` | maioria 👍; cada 👎 vira conversa |
| Rotina das 6h rodou | GitHub Actions | 7 de 7 dias |
| Custo da IA na semana | `relatorio_uso` (tokens) | dentro do que você aceita `[PREENCHER: limite em R$]` |

## 5. Checklist de revisão semanal (15 minutos, toda segunda)

- [ ] `python -m scripts.relatorio_uso --dias 7`: dias de uso, funil, 👍/👎, versão A/B/C, perguntas e tokens da IA
- [ ] GitHub → Actions → **rotina-diaria**: 7 execuções verdes? Os **testes** do último envio estão verdes?
- [ ] Abrir o app no celular: o veredito de hoje faz sentido com o céu lá fora?
- [ ] Ler as perguntas da semana em `ai.conversa` e conferir 1 resposta por amostra
- [ ] Alertas da semana: algum alarme falso? Algum que faltou?
- [ ] Conversa de 10 min com seu pai (seção 3) e anotar o que ele disse em `docs/design/diario-uso.md` `[criar no dia 1]`
- [ ] Escolher **no máximo uma** mudança para a semana seguinte

## 6. Três experimentos prioritários (em ordem)

| # | Experimento | Semanas | Métrica | Decide |
|---|---|---|---|---|
| E1 | Texto do veredito **A × B × C** (já no ar; force pelo link `?v=`) | 1–2 | O que ele entende mais rápido + 👍 por versão | Fixar uma versão |
| E2 | **Atalhos na Hoje** (Alertas · Cotações · Lançar) × só o menu **»** | 3–4 | % de sessões que visitam uma 2ª tela | Manter se ≥ 50% |
| E3 | **Resumo da manhã no WhatsApp** × sem resumo | depois do canal pronto | dias por semana com uso | Manter se subir de forma consistente |

## 7. Quando parar de mexer

Pare de mudar a interface quando, **por 3 semanas seguidas**:
1. ele viu o veredito em **4 ou mais dias** por semana;
2. fez **ao menos 2 ações** por semana;
3. **nenhuma queixa nova** apareceu na conversa semanal.

A partir daí, a interface fica congelada. O esforço vai para o que falta de verdade: o **formulário com os dados reais da fazenda** e o **WhatsApp**. Mudanças de tela só entram se vierem de uma queixa dele.

Sinal para **voltar a mexer:** duas semanas seguidas abaixo de 3 dias de uso. Primeiro pergunte o motivo, depois mude.

## 8. Calendário

| Semana | Foco |
|---|---|
| Dia 1 | Apresentação ao vivo, atalho na tela inicial, primeira pergunta ao agrônomo junto com ele |
| 1 | Lembrete seu toda manhã; anotar quando o veredito discordar dele; decidir P0-1 (app dormindo) |
| 2 | Olhar ele usar sem ajudar; encerrar o E1 (fixar a versão do texto) |
| 3–4 | E2 (atalhos); primeira leitura de "parar de mexer"; post no LinkedIn com o que aprendeu |
| Depois | Formulário do produtor (dados reais) → WhatsApp → E3 |

---

## O que eu preciso de você
1. **Data do dia 1** (quando vai apresentar ao seu pai). `[PREENCHER]`
2. **Limite de custo da IA** por mês que você aceita. `[PREENCHER: R$]`
3. As três decisões pendentes do passo 6: app dormindo, lembrar a senha e link de demonstração. `[CONFIRMAR]`
4. Quer que eu monte a **lista única de alterações** (`lista-alteracoes.md`) juntando tudo dos 7 passos?
