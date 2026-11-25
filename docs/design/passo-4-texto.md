# Passo 4 — O texto de cada tela

> **Base:** [plano-mestre-safraviva.md](plano-mestre-safraviva.md) · [passo-2-secao-principal.md](passo-2-secao-principal.md) · [passo-3-movimento.md](passo-3-movimento.md). Tom do plano mestre: agrônomo calmo da região, frase curta, número sempre com unidade.

## 1. Nível de consciência de quem chega

| Quem | Sabe que tem o problema? | Conhece a solução? | O que o texto precisa fazer |
|---|---|---|---|
| **Seu pai** | Sim: decide todo dia se entra na lavoura, olha o céu, ouve o preço no rádio e no grupo | Não: nunca viu o app | Responder a pergunta dele **na linguagem dele**, sem explicar tecnologia |
| **Portfólio** | Não é produtor | Conhece apps e dados | Mostrar em 10 segundos que é produto real, com dado real e decisão técnica |

Regra que vale para os dois: **título = a pergunta que a tela responde**, e o subtítulo diz em uma linha o que tem ali.

## 2. Objeções que aparecem durante a rolagem (e onde o texto responde)

| Objeção | Onde aparece | Resposta no texto |
|---|---|---|
| "Isso é de Itapeva mesmo ou é genérico?" | Primeira tela | "com dados de Itapeva-SP"; "estação do INMET em Itapeva" nas fontes |
| "Quem garante esse número?" | Em todo número | Fonte e hora logo abaixo (já existe em todas as telas) |
| "A IA vai inventar?" | Agrônomo Digital | "Ele consulta os dados e diz de onde tirou" + a linha "Consultou: …" em cada resposta |
| "Vai me dizer qual veneno passar?" | Agrônomo Digital | "Defensivo só com receituário agronômico" (já é regra da IA) |
| "Esses números da fazenda são meus?" | Telas da fazenda | Aviso "Fazenda de demonstração" até entrarem os dados reais |
| "É complicado de anotar?" | Lançar | Subtítulo diz o que dá para lançar; cada campo tem exemplo |

## 3. Provas e depoimentos reais

- **Depoimentos:** não há. Nada inventado. `[PREENCHER: depois de uma ou duas semanas de uso, uma frase do seu pai, com autorização, para o README/portfólio]`
- **Provas que já existem e podem aparecer:** 52 anos de IBGE, 45 anos de clima diário, estimativa validada contra o IBGE (r = 0,32 na soja), 12 perguntas de avaliação da IA. Todas estão documentadas no repositório.

## 4. As palavras do produtor

Não tenho entrevista com o seu pai, então estas são **hipóteses**, tiradas do vocabulário comum do produtor de grãos da região. `[CONFIRMAR com ele]`

| Ele provavelmente diz | O app passa a dizer | Evitar |
|---|---|---|
| "entrar na lavoura", "dá pra passar veneno?" | "entrar na lavoura", "pulverizar" | "janela operacional" |
| "a soja tá quanto?" | "Quanto está a saca" | "cotação spot" |
| "talhão", "saca", "alqueire" | talhão, saca de 60 kg, **ha** (alqueire `[CONFIRMAR se ele pensa em alqueire paulista]`) | "gleba", "t/ha" |
| "veranico", "geada", "seca" | os mesmos | "déficit hídrico" sem explicação |
| "quanto sobrou" | "quanto sobra", "margem" | "EBITDA", "resultado operacional" |

## 5. Hierarquia de títulos (título · subtítulo)

| Tela | Título (H1) | Subtítulo |
|---|---|---|
| Hoje na lavoura | *(o veredito do dia, passo 2)* | — |
| Alertas | Alertas | O que pode afetar a lavoura nos próximos dias. Cada alerta some sozinho quando a situação passa. |
| Previsão do tempo | Previsão do tempo | Chuva, temperatura e vento dos próximos 16 dias, e as melhores horas para pulverizar. |
| Janela de plantio | Janela de plantio | Quando plantar com menos risco, pelo zoneamento oficial do Ministério da Agricultura (ZARC) para Itapeva. |
| Cotações | Cotações | Quanto está a saca hoje e se o preço mexeu por causa de Chicago ou do dólar. |
| Estimativa de safra | Estimativa de safra | Quanto cada lavoura deve render com a chuva que caiu até agora. |
| Resultados da safra | Resultados da safra | Quanto custou cada saca, quanto sobra e quanto precisa colher para empatar. |
| Lançar | Lançar | Anote o que foi feito: operação, despesa, colheita, venda ou problema na lavoura. |
| Caderno de campo | Caderno de campo | Tudo o que foi lançado, por talhão e por data. |
| Agrônomo Digital | Agrônomo Digital | Pergunte como perguntaria ao agrônomo. Ele consulta os dados do SafraViva e diz de onde tirou cada número. |
| Produção regional | Produção regional | Como Itapeva produz em comparação com os vizinhos, com São Paulo e com o Paraná. |
| Clima e safras | Clima e safras | Quais safras foram boas ou ruins em Itapeva, e o clima de cada uma. |

Subtítulos de seção (H3): pergunta ou afirmação curta, **sem emoji** (o emoji muda de desenho em cada celular).

## 6. Microtextos

### Botões
| Onde | Antes | Depois |
|---|---|---|
| Agrônomo | 🧹 Nova conversa | Nova conversa (ícone de atualizar) |
| Agrônomo | 📋 Resumo da semana | Resumo da semana (ícone de calendário) |
| Agrônomo | Gerar resumo agora | Montar o resumo da semana |
| Resultados | 🧪 Carregar fazenda de demonstração | Ver com uma fazenda de exemplo |
| Resultados | 🗑️ Remover a fazenda de demonstração | Apagar a fazenda de exemplo |
| Hoje (fim da página) | — | **Perguntar ao agrônomo** (CTA final) |

### Telas vazias (dizem o que fazer, não só o que falta)
| Onde | Depois |
|---|---|
| Caderno, Lançar, Estimativa sem fazenda | Nenhuma fazenda cadastrada ainda. Comece em **Lançar → Cadastro**. |
| Caderno sem lançamento | Nada lançado ainda. Anote a primeira operação em **Lançar**. |
| Estimativa sem lavoura | A estimativa aparece quando houver uma lavoura **plantada**, com data de plantio e meta de produtividade (em **Lançar → Cadastro**). |
| Previsão sem dados | Ainda não há previsão. Abra **Hoje na lavoura** e toque em **Atualizar previsão**. |
| Alertas vazios | Nenhum alerta agora: tempo e lavouras sem risco relevante. |

### Erros (o que houve + o que fazer, sem jargão; o detalhe técnico fica pequeno, embaixo)
| Onde | Depois |
|---|---|
| IA sem chave | O Agrônomo Digital está desligado neste computador: falta a chave da IA (`OPENAI_API_KEY` no arquivo `.env`). |
| IA sem resposta | O agrônomo não conseguiu responder agora. Tente de novo em 1 minuto. |
| Resumo falhou | Não deu para montar o resumo agora. Tente de novo em 1 minuto. |

### Formulários
Os rótulos e exemplos atuais já seguem o padrão ("Produto / máquina — ex.: glifosato, adubo 02-20-20"); ficam como estão. Mensagem de sucesso sempre diz **o que foi salvo e onde ver**.

## 7. CTA final
No fim da "Hoje na lavoura", depois das fontes:

> **Ficou alguma dúvida sobre a lavoura?**
> O Agrônomo Digital responde com os dados de hoje.
> **[ Perguntar ao agrônomo ]**

Registra `cta_click` com `final|v=<versão>`, para comparar com o botão da primeira dobra.

---

## O que eu preciso de você
1. **Palavras do seu pai:** confirme ou corrija a tabela da seção 4. Principalmente: ele fala em **alqueire** ou em hectare? `[CONFIRMAR]`
2. **Depoimento:** depois de algumas semanas de uso, uma frase dele (com autorização) para o portfólio. `[PREENCHER]`
3. Algum termo do app que ele **não entendeu** ao usar? Isso vale mais que qualquer hipótese minha.
