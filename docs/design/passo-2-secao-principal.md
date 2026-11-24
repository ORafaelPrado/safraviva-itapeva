# Passo 2 — A primeira coisa que o produtor vê

> **Base:** [plano-mestre-safraviva.md](plano-mestre-safraviva.md) (passo 1). Segui as propostas do plano como padrão; os `[CONFIRMAR]` de lá continuam anotados para a lista final.

**Adaptação:** num app, a "seção principal" é a **primeira dobra da tela "Hoje na lavoura"**: o que aparece no celular sem rolar. Para quem vem do portfólio, a primeira coisa é a **tela de entrada** (senha), que também foi refeita.

---

## 1. O que a pessoa estava fazendo antes de abrir

| Quem | Momento | Estado de espírito |
|---|---|---|
| Produtor | 5h30–7h, café, antes de sair; ou parado na beira do talhão olhando o céu | Pressa; quer uma decisão, não um relatório |
| Produtor | Ouviu preço no rádio / no grupo de WhatsApp | Quer conferir o número |
| Portfólio | Clicou no link do README ou do LinkedIn | Curioso, 1–2 minutos, julga pela primeira tela |

## 2. A promessa que importa

> **"Abra e saiba, em uma frase, se hoje é dia de entrar na lavoura."**

Tudo mais (gráfico, histórico, IA) é apoio para essa frase.

## 3. A prova mais forte sem rolar

Não temos (nem inventamos) depoimento ou nota. A prova aqui é **o próprio dado, com a fonte e a hora**:
- O veredito vem de regras abertas (vento 3–10 km/h, Delta T 2–8 °C, chuva < 30%, geada ≤ 3 °C), calculadas sobre a previsão do **Open-Meteo** para as coordenadas da fazenda.
- Os três números mostram de onde vêm e de quando são: "Open-Meteo · 17h29", "CEPEA/ESALQ · 23/11".
- Na tela de entrada (portfólio): os fatos verificáveis do projeto, todos já documentados no README: **52 anos de IBGE · 45 anos de clima diário · estimativa validada contra o IBGE**.

## 4. A ação em menos de 10 segundos

- **Botão primário:** **Perguntar ao agrônomo**: leva ao Agrônomo Digital (o diferencial do app).
- **Botão secundário:** **Previsão hora a hora**: leva à página do tempo, para quem quer conferir antes de decidir.
- Os dois registram `cta_click` com a versão do texto (A/B).

## 5. O que foi criado

### Primeira dobra da "Hoje na lavoura"
1. **Linha de cima:** "Itapeva-SP · ter 24/11 · Previsão das 17h29".
2. **Selo de situação:** ícone + palavra (Tranquilo / Atenção / Atenção alta), nunca só cor.
3. **Título (veredito do dia):** uma frase calculada pelas regras (`alertas.veredito_do_dia`), por ordem de importância:
   1. alerta grave (geada forte, veranico severo) → "Cuidado";
   2. chuva ≥ 10 mm no dia → "Hoje não";
   3. tem janela boa para pulverizar → "Sim, das Xh às Yh";
   4. senão → "Dá para trabalhar, mas não para pulverizar", com o melhor dia.
   Depois das 18h, o veredito passa a falar de **amanhã**.
4. **Linha de apoio:** o porquê, ou o alerta de atenção mais importante.
5. **Três números:** chuva prevista no dia (mm e chance) · soja CEPEA Paraná (R$/sc e variação) · lavoura principal (talhão maior: fase e dias).
6. **Botões:** primário e secundário (item 4).

### "Imagem de apoio"
Não uso foto de banco de imagens: num app de decisão, ela empurra o veredito para baixo no celular. A "imagem" é o **bloco do veredito** (fundo de cor suave e símbolo da folha). `[PREENCHER: se quiser, uma foto real da lavoura do seu pai para a tela de entrada — tirada de dia, horizontal]`

### Identidade aplicada (do passo 1)
- Tema: verde-safra `#1E6B3C`, fundo palha `#FAF8F3`, texto `#1B2119`, bordas `#E4E1D8`, cantos 12/10 px, fonte **Inter**.
- Logo provisório em SVG (folha + "SafraViva") com `st.logo`.
- Menu no topo com as seções do plano; ícones Material no lugar dos emojis no menu e nos títulos.
- Tela de entrada nova: logo, frase do app, três fatos do projeto e o campo de senha.

## 6. Três versões de texto para teste A/B

Cada sessão recebe uma versão ao acaso (ou forçada pelo link `?v=A`, `?v=B`, `?v=C`). O veredito é o mesmo; muda o **enquadramento**.

| Versão | Título | Exemplo |
|---|---|---|
| **A · Veredito** | a frase do dia, direto | **Dá para pulverizar hoje, das 7h às 11h** |
| **B · Pergunta** | pergunta fixa + resposta curta | **Hoje dá para entrar na lavoura?** → *Sim. Dá para pulverizar das 7h às 11h.* |
| **C · Conversa** | saudação + frase | **Bom dia! Hoje dá para pulverizar, das 7h às 11h.** |

**Eventos registrados** (tabela `uso.evento`, no próprio banco, sem dado pessoal):
`pagina_vista` · `ab_view` (versão) · `cta_click` (botão + versão).

**Métrica que decide:** % de sessões com `cta_click` na primeira dobra, por versão.
**Atenção honesta:** com um usuário só (seu pai) não há volume para teste estatístico. Nas primeiras semanas, o teste serve para **conversar com ele** ("qual destas você entende mais rápido?"); a métrica passa a valer se o app ganhar outros produtores.

## 7. Acessibilidade e celular (medido)
- Contraste do texto (seção 6 do plano): todos ≥ 4,5:1. O selo de situação usa cor só no ícone; a palavra fica em texto escuro.
- Botões com altura ≥ 44 px.
- Sem rolagem lateral de 320 a 1920 px (conferido no navegador, resultado no fim do passo).

---

## O que eu preciso de você
1. **Qual das três versões** (A, B ou C) parece mais com o jeito do seu pai falar? Se ele puder ver as três, melhor ainda: `?v=A`, `?v=B`, `?v=C`.
2. **Botão primário:** "Perguntar ao agrônomo" é a ação certa, ou para ele seria "Lançar no caderno"? `[CONFIRMAR]`
3. **Foto da lavoura** para a tela de entrada (opcional). `[PREENCHER]`
4. **Soja de referência:** usei CEPEA **Paraná** (mais perto do preço que ele recebe em Itapeva). Se ele acompanha outra praça ou cooperativa, me diga. `[CONFIRMAR]`
