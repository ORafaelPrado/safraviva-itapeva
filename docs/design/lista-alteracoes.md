# Lista única de alterações: SafraViva (depois dos 7 passos)

> Junta as pendências dos 7 documentos de [docs/design/](.) e do que está publicado em https://safraviva-itapeva.streamlit.app.
> **Prioridade:** ⛔ P0 bloqueia o uso real · 🔴 P1 antes ou logo depois do dia 1 · 🟠 P2 primeiras semanas · 🟡 P3 acabamento.
> **Quem age:** 👤 você · 🤖 eu (aplico no app) · 🛠️ limite da plataforma · 👥 rotina.
> ✳️ = consigo fazer **sem depender de nada seu**.
> **Status:** ✅ feito · 🟡 em parte · ⚪ aberto.

## Confirmações de sim ou não (destravam muita coisa)

| # | Pergunta | Origem | Padrão usado até agora | Status |
|---|---|---|---|---|
| C1 | Público: seu pai primeiro, portfólio depois? | passo 1 | sim | ⚪ |
| C2 | Cores verde-safra + palha + trigo e o logo provisório (folha)? | passo 1 | aplicado | ⚪ |
| C3 | Fonte: só Inter (sem serifada nos títulos)? | passo 1 | só Inter | ⚪ |
| C4 | Menu no topo em 6 seções? | passo 1 | aplicado | ⚪ |
| C5 | Qual texto do veredito: A (direto), B (pergunta) ou C (conversa)? | passo 2 | sorteio | ⚪ |
| C6 | Botão principal "Perguntar ao agrônomo" (ou "Lançar no caderno")? | passo 2 | agrônomo | ⚪ |
| C7 | Soja de referência: CEPEA Paraná? | passo 2 | Paraná | ⚪ |
| C8 | Ponto "ao vivo" das cotações pulsando (ou parado)? | passo 3 | pulsando | ⚪ |
| C9 | Ele pensa em alqueire ou em hectare? | passo 4 | 🟡 a ficha aceita os dois | 🟡 |
| C10 | O celular dele pode **lembrar a senha por 30 dias**? | passo 6 | não | ⚪ |
| C11 | **Link de demonstração sem senha** para o portfólio? | passo 6 | não | ⚪ |
| C12 | App dormindo: (a) avisar, (b) despertador agendado ou (c) hospedagem que não dorme? | passo 6 | nenhum | ⚪ |
| C13 | Limite de custo da IA por mês (R$)? | passo 7 | — | ⚪ |
| C14 | Data do dia 1 (apresentação ao seu pai)? | passo 7 | — | ⚪ |
| C15 | Front-end dedicado fica só como ideia para o futuro? | passo 1 | sim | ⚪ |
| C16 | Apagar a fazenda de exemplo quando a real estiver conferida? | ficha | — | ⚪ |

## ⛔ P0: bloqueia o uso real

| # | Alteração | Quem | Status |
|---|---|---|---|
| 1 | **Ficha da fazenda:** mandar o link para o seu pai e ele preencher (a tela está pronta e testada) | 👤 | 🟡 tela ✅, falta preencher |
| 2 | **App dormindo** na primeira abertura do dia: decidir (C12) e eu aplico | 👤 → 🤖 | ⚪ |
| 3 | Cronometrar a primeira abertura do dia no celular | 👤 | ⚪ |

## 🔴 P1: antes ou logo depois do dia 1

| # | Alteração | Quem | Status |
|---|---|---|---|
| 4 | Lembrar a senha por 30 dias (depende de C10) | 🤖 | ⚪ |
| 5 | Link de demonstração sem senha (depende de C11) | 🤖 | ⚪ |
| 6 | Apresentação ao vivo + atalho na tela inicial do celular dele | 👤 | ⚪ |
| 7 | Previsão, alertas e pulverização nas **coordenadas da fazenda** (hoje: centro de Itapeva), assim que a ficha chegar | 🤖 | ⚪ |
| 8 | Apagar a fazenda de exemplo depois de conferir a real (C16) | 👤 → 🤖 | ⚪ |
| 9 | Resumo da manhã e alertas no **WhatsApp** (o número vem da ficha) | 🤖 | ⚪ combinado para depois |

## 🟠 P2: primeiras semanas

| # | Alteração | Quem | Status |
|---|---|---|---|
| 10 | ✳️ Atalhos na Hoje (Alertas · Cotações · Lançar): experimento E2 | 🤖 | ⚪ |
| 11 | ✳️ Dica na tela Lançar: "pode ditar ao agrônomo" | 🤖 | ⚪ |
| 12 | ✳️ Acerto da previsão de chuva (previsão × estação de Itapeva) | 🤖 | ⚪ |
| 13 | ✳️ Criar `docs/design/diario-uso.md` para as anotações semanais | 🤖 | ⚪ |
| 14 | Revisão semanal de 15 min (checklist do passo 7) | 👥 | ⚪ |
| 15 | Fixar a versão do texto depois de 2 semanas (E1, C5) | 👤 → 🤖 | ⚪ |
| 16 | Post no LinkedIn com o print e o que aprendeu | 👤 | ⚪ |

## 🟡 P3: acabamento

| # | Alteração | Quem | Status |
|---|---|---|---|
| 17 | ✳️ Texto interno "Choose an option" das listas em português | 🤖 | ⚪ |
| 18 | ✳️ Trocar os emojis da tabela dos 7 dias e dos alertas (🔴🟡) por ícones | 🤖 | ⚪ |
| 19 | Cortar um peso da fonte se o 3G pesar (depende da medição no celular) | 🤖 | ⚪ |
| 20 | Logo definitivo (se quiser um) | 👤 | ⚪ |
| 21 | Foto real da lavoura para a tela de entrada | 👤 | ⚪ |
| 22 | Frase do seu pai (com autorização) para o portfólio | 👤 | ⚪ |
| 23 | Campo de data sem rótulo para leitor de tela | 🛠️ | ⚪ limite do Streamlit |

## Já feito nos 7 passos

Itens ✅, publicados:
- Identidade: tema, logo, ícones e menu no topo.
- Tela de entrada com fatos verificáveis e linha de privacidade.
- Veredito do dia com 3 números e teste A/B/C.
- Movimento mínimo, com "reduzir movimento" respeitado.
- Textos: títulos como pergunta, telas vazias e erros que dizem o que fazer, chamada final.
- Acessibilidade medida e corrigida: idioma, H1, alvos e campos de 44 px, contraste.
- Fuso de Brasília no banco (D028).
- Medição de uso, relatório de funil e 👍/👎.
- **Ficha da fazenda** (formulário do produtor), com conversão de terra → solo ZARC, ciclo → grupo e alqueire → hectare.

## Ordem sugerida
1. **Hoje:** mandar o link da ficha para o seu pai (item 1).
2. Responder as confirmações **C10, C11, C12 e C14** (5 minutos; destravam os itens 2, 4 e 5).
3. Enquanto isso, eu faço o bloco ✳️ (itens 10 a 13, 17 e 18).
4. Quando a ficha chegar: conferir juntos e depois fazer os itens 7 e 8.
5. Dia 1 (item 6), depois o plano de 30 dias do passo 7.
6. WhatsApp (item 9).

## Resumo

| Prioridade | Itens | 👤 você | 🤖 eu | 👥 rotina | 🛠️ plataforma | ✳️ sem depender de você |
|---|---|---|---|---|---|---|
| ⛔ P0 | 3 | 3 | 0 | 0 | 0 | 0 |
| 🔴 P1 | 6 | 2 | 4 | 0 | 0 | 0 |
| 🟠 P2 | 7 | 2 | 4 | 1 | 0 | 4 |
| 🟡 P3 | 7 | 3 | 3 | 0 | 1 | 2 |
| **Total** | **23** | **10** | **11** | **1** | **1** | **6** |

Confirmações de sim ou não: **16** (C1 a C16). Os itens marcados "👤 → 🤖" foram contados em quem age primeiro: você.
