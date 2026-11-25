# Passo 6 — Auditoria de conversão

> **Base:** passos [1](plano-mestre-safraviva.md) · [2](passo-2-secao-principal.md) · [3](passo-3-movimento.md) · [4](passo-4-texto.md) · [5](passo-5-plano-construcao.md).
> **Adaptação:** o app não vende nada, então "conversão" quer dizer **o produtor usar o app para decidir e agir**. Para o portfólio, quer dizer **o visitante ver o produto funcionando**.

## 0. O que é conversão aqui

| Público | Conversão | Evento que mede |
|---|---|---|
| Seu pai | **Ação:** perguntar ao agrônomo ou lançar algo no caderno | `pergunta_ia`, `lancamento_salvo` (criados neste passo) |
| Seu pai | **Hábito:** voltar no dia seguinte | dias com sessão por semana (`uso.evento`) |
| Seu pai | **Decisão:** ler o veredito e tocar na primeira chamada | `cta_click` (`agronomo` ou `final`), por versão A/B/C |
| Portfólio | Ver o painel por dentro | hoje é **impossível** sem senha (ver P1-2) |

**Dados reais de uso:** ainda não há nenhum. A tabela `uso.evento` está vazia, porque apaguei os registros dos meus testes e o app ainda não foi apresentado ao seu pai. Esta auditoria percorre o caminho e mede tempo e atrito, não comportamento. O relatório `python -m scripts.relatorio_uso` passa a mostrar o funil real assim que ele começar a usar.

## 1. O caminho, da entrada à ação

| Etapa | O que acontece | Atrito | Gravidade |
|---|---|---|---|
| **1. Abrir o link** | O Streamlit Cloud pode estar **hibernando**: aparece uma tela em inglês ("This app has gone to sleep… Yes, get this app back up!") e a espera vai de 10 s a mais de 1 min | Inglês + espera + um botão que ele não conhece. É o maior risco de desistência | ⛔ |
| **2. Senha** | Tela de entrada nova; senha a cada sessão nova (celular que dormiu, aba fechada) | Digitar senha todo dia no campo | 🔴 |
| **3. Veredito** | Frase do dia + 3 números + 2 botões, sem rolar (passo 2) | Baixo. O aviso "Fazenda de demonstração" confunde até entrarem os dados reais | 🟠 |
| **4. Ir além** | Menu no celular atrás do botão **»** | Ele pode não descobrir as outras 11 telas | 🟠 |
| **5. Agir** | Agrônomo: perguntas prontas + campo de texto. Lançar: 7 abas | Digitar no celular é lento; o agrônomo aceita lançamento ditado, mas **isso não está dito na tela de Lançar** | 🟠 |
| **6. Voltar amanhã** | Nada o chama de volta (alertas só dentro do app, por decisão) | Hábito depende só da memória dele | 🔴 |

## 2. Dúvidas sem resposta antes do clique

| Dúvida | Onde surge | Resposta hoje | Ação |
|---|---|---|---|
| "Quem vê os dados da minha fazenda?" | Tela de entrada | nenhuma | ✅ **feito:** linha "Acesso com senha: os dados da fazenda não são públicos." |
| "Essa previsão acerta?" | Veredito | só a fonte (Open-Meteo) | P2: mostrar "acerto da chuva nos últimos 30 dias" comparando previsão × estação INMET `[decidir]` |
| "Posso falar em vez de digitar?" | Agrônomo/Lançar | não | P2: dica "Pode contar do seu jeito: 'passei fungicida na Chapada hoje'" na tela Lançar |
| "Quanto custa perguntar?" | Agrônomo | — | Não é dúvida do produtor (custo é seu, ~8 mil tokens por pergunta); acompanhar no passo 7 |

## 3. Sinais de confiança que ele procura

| Sinal | Situação |
|---|---|
| É de Itapeva (não genérico) | ✅ "Itapeva-SP" no veredito, estação A714 nas fontes |
| De onde vem cada número | ✅ fonte e hora embaixo de cada dado |
| A IA mostra o que consultou | ✅ "Consultou: …" em cada resposta |
| Não manda passar veneno | ✅ "defensivo só com receituário agronômico" |
| Alguém conhecido usa / recomenda | ❌ não há (e não se inventa) `[PREENCHER depois do uso real]` |
| Os dados são dele, protegidos | ✅ feito neste passo (tela de entrada) |

## 4. Melhorias por prioridade

| # | Prioridade | Melhoria | Quem | Status |
|---|---|---|---|---|
| P0-1 | ⛔ | **Primeira abertura do dia:** medir o tempo de acordar (passo 5) e decidir entre (a) avisar o pai de que a 1ª abertura demora e do botão em inglês, (b) um "despertador" agendado que abra o app de manhã antes dele, (c) hospedagem que não hiberna (pode ter custo) | 👤 decidir · 🤖 aplicar | aberto `[CONFIRMAR]` |
| P1-1 | 🔴 | **Não pedir senha todo dia:** lembrar o aparelho por 30 dias (cookie assinado) | 🤖 | aberto `[CONFIRMAR: aceitável para você?]` |
| P1-2 | 🔴 | **Portfólio:** modo demonstração **sem senha**, só com a fazenda fictícia e dados públicos, num link separado | 👤 decidir · 🤖 | aberto `[CONFIRMAR]` |
| P1-3 | 🔴 | **Chamar de volta:** resumo da manhã no WhatsApp (já planejado, canal separado) | 🤖 depois | combinado para depois |
| P1-4 | 🔴 | **Medir a ação real:** eventos `pergunta_ia` e `lancamento_salvo` + relatório de funil | 🤖 | ✅ feito |
| P2-1 | 🟠 | Atalhos visíveis na Hoje (Alertas · Cotações · Lançar) em vez de depender do **»** | 🤖 | experimento E2 |
| P2-2 | 🟠 | Dica de ditar o lançamento ao agrônomo, na tela Lançar | 🤖 | aberto |
| P2-3 | 🟠 | Trocar a fazenda de demonstração pelos dados reais (formulário do produtor) | 👤 + 🤖 | fim do projeto |
| P2-4 | 🟠 | Acerto da previsão de chuva (previsão × estação) | 🤖 | aberto |
| P3-1 | 🟡 | Emojis restantes no chat (avatares e "✅ Confirmar") trocados por ícones | 🤖 | ✅ feito |

## 5. As três mudanças de maior impacto
1. **Abrir rápido e sem senha todo dia** (P0-1 + P1-1): sem isso, nada depois acontece. Uma espera longa com tela em inglês, mais a senha, na primeira semana pode matar o hábito.
2. **Resumo da manhã no WhatsApp** (P1-3): leva o veredito até ele, sem precisar lembrar de abrir. É a maior alavanca de hábito.
3. **Modo demonstração aberto** (P1-2): para o portfólio, transforma "tem senha, não dá para ver" em "veja funcionando".

## 6. Experimentos, nesta ordem

| # | Experimento | Duração | Métrica que prova | Critério |
|---|---|---|---|---|
| E1 | Texto do veredito A × B × C (já no ar) | 2 semanas, **qualitativo** com seu pai (1 usuário não dá estatística) | qual ele entende mais rápido + `cta_click` por versão | escolher uma versão e fixar |
| E2 | Atalhos na Hoje × só o menu **»** | 2 semanas | % de sessões que visitam uma 2ª tela | ≥ 50% com atalhos → manter |
| E3 | Resumo da manhã no WhatsApp × sem resumo | 3 semanas (depois do canal pronto) | **dias com sessão por semana** | sobe de forma consistente → manter |

## 7. A métrica que prova que funcionou

> **Dias por semana em que seu pai abriu o app e viu o veredito** (`pagina_vista` da Hoje, por dia).
> Meta para o primeiro mês: **≥ 4 dias por semana**.

Métrica de apoio: **% de sessões com uma ação** (`pergunta_ia` ou `lancamento_salvo`). Ela mostra se o app ajuda a fazer, e não só a ler.

## 8. Feito neste passo
- Eventos `pergunta_ia` (Agrônomo e Cotações) e `lancamento_salvo` (Lançar e lançamento confirmado pela IA).
- `python -m scripts.relatorio_uso`: sessões, dias de uso, funil (viu → clicou → agiu) e versão A/B/C.
- Linha de privacidade na tela de entrada.
- Ícones no lugar dos últimos emojis do chat.

---

## O que eu preciso de você
1. **P0-1:** depois de cronometrar a primeira abertura do dia, escolha entre (a) avisar, (b) despertador agendado ou (c) hospedagem sem hibernação. `[CONFIRMAR]`
2. **P1-1:** posso fazer o celular dele **lembrar a senha por 30 dias**? `[CONFIRMAR]`
3. **P1-2:** quer um **link de demonstração sem senha** para o portfólio (só a fazenda fictícia)? `[CONFIRMAR]`
