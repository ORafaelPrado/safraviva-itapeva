# Plano mestre — SafraViva Itapeva (passo 1 de 7)

> **Base:** primeiro passo do processo de 7 passos. Painel atual: `app/` (Streamlit 1.66), publicado em https://safraviva-itapeva.streamlit.app.
> Próximos documentos: `passo-2-secao-principal.md` · `passo-3-movimento.md` · `passo-4-texto.md` · `passo-5-plano-construcao.md` · `passo-6-auditoria-conversao.md` · `passo-7-plano-lancamento.md`.

**Adaptação do prompt:** não é um site de luxo, e sim um **app premium para o produtor rural**: ferramenta de trabalho diária, aberta no celular, muitas vezes no sol. "Premium" aqui é **confiança e clareza**, não brilho.

**Premissas declaradas** (corrija o que não bater):
- Não há logo nem cores de marca definidas. Proponho uma identidade abaixo. `[CONFIRMAR]`
- Concorrentes não foram informados. Uso **arquétipos** do mercado (lista na seção 3).
- Dois públicos, nesta ordem de prioridade: **1º o seu pai** (uso real), **2º quem vê o portfólio** (recrutador, colega de dados). `[CONFIRMAR a ordem]`
- Os dados da fazenda continuam sendo de **demonstração** até o formulário do produtor (final do projeto). Nada de número "real" inventado na interface.

---

## 1. A marca

| | |
|---|---|
| **Nome** | SafraViva · Itapeva |
| **O que é, em uma frase** | O agrônomo de bolso do produtor de grãos do Sudoeste Paulista: tempo, lavoura, mercado e contas no mesmo lugar. |
| **Personalidade** | Agrônomo experiente da região: calmo, direto, cita a fonte, não exagera. Nunca "startup animada". |
| **Tom** | Português do campo, frase curta, número com unidade (sc/ha, mm, °C, R$/sc). Diz o que fazer e por quê. |
| **Diferencial real (provável)** | Dados **locais** (estação do INMET de Itapeva, 52 anos de IBGE do município), **estimativa validada** contra o IBGE, IA que **mostra de onde tirou** cada número. Tudo isso já existe; só não aparece. |

## 2. O público

### O produtor (prioridade 1)
- **Quando abre:** de manhã cedo (antes de sair para a lavoura), na hora de decidir pulverizar, quando ouve preço no rádio.
- **Onde:** celular Android, sol forte, às vezes 3G, às vezes de luva/dedo sujo.
- **O que quer em 3 segundos:** "Hoje dá pra entrar na lavoura? Tem algo me ameaçando? Quanto tá a soja?"
- **O que o irrita:** menu escondido, tela comprida, termo técnico sem tradução, gráfico que não cabe na tela.

### Quem vê o portfólio (prioridade 2)
- **Quando abre:** pelo link do README/LinkedIn, no computador, por 1–2 minutos.
- **O que quer ver:** que é um produto de verdade (não um notebook com botões), dados de verdade, decisão técnica bem feita.
- **Problema hoje:** o painel tem senha. `[CONFIRMAR]` Sugestão para depois: um **modo demonstração** sem senha, só com a fazenda fictícia, ou um vídeo/GIF de 30 s no README. Decidir no passo 7.

## 3. Concorrentes que queremos superar (arquétipos)

| Arquétipo | Exemplos | O que fazem bem | Onde o SafraViva ganha |
|---|---|---|---|
| Gestão de fazenda | Aegro, Strider | Visual limpo, cadastro de talhão e caderno | Clima local + estimativa de safra + IA, sem planilha |
| Plataforma digital de grandes | Climate FieldView, xarvio | Mapa, marca forte, sensação de "tecnologia séria" | Gratuito, regional, explica em português simples |
| Clima agrícola | Agrosmart, Climatempo Agro | Previsão bonita, ícones claros | Cruza o tempo com a **fase de cada talhão** e diz o que fazer |
| Portal de mercado | Notícias Agrícolas, CEPEA | Cotação completa | Converte para **R$/saca na fazenda** e compara com o **custo por saca** |

**Barra a passar:** parecer tão "produto" quanto Aegro/FieldView na primeira tela, e ser mais útil que todos na pergunta do dia.

## 4. A sensação nos primeiros 3 segundos

> **"Já sei o que fazer hoje na lavoura."**

Na prática, ao abrir o celular, sem rolar:
1. **Um veredito do dia** em uma linha (ex.: "Bom dia para pulverizar até as 10h · sem risco de geada").
2. **O alerta mais importante**, se houver (só um, com cor de status).
3. **Três números**: chuva das próximas 24 h, preço da soja hoje (R$/sc) e a fase da lavoura principal.

Tudo o mais vem depois da rolagem ou em outra página.

## 5. Diagnóstico do painel atual

| # | O que vi | Efeito | Gravidade |
|---|---|---|---|
| D1 | Visual padrão do Streamlit (fonte, botões, cabeçalho, menu) | Parece protótipo, não produto | Alta |
| D2 | Títulos com emoji (🏠 🔔 🌾 🤖…) | Ar informal; emoji muda de desenho em cada celular | Média |
| D3 | 12 páginas numa barra lateral que **fica escondida no celular** | O produtor não descobre as outras telas | Alta |
| D4 | "Hoje na lavoura" é longa: o veredito do dia não aparece sem rolar | Os 3 segundos não acontecem | Alta |
| D5 | Sem logo, sem nome fixo no topo | Sem identidade | Média |
| D6 | Seletores de propriedade/solo/ciclo na barra lateral | No celular, ficam escondidos e o contexto some | Média |
| D7 | Cards e alertas com CSS próprio em `ui.py`, sem tokens comuns | Cores e espaçamentos variam entre páginas | Média |
| D8 | Gráficos já bons (paleta validada para daltonismo, rótulos finais) | Ponto forte; manter | — |
| D9 | Tela de senha crua | Primeira impressão do portfólio é um campo cinza | Média |

## 6. Identidade visual

### Cores (contraste medido, WCAG)
| Token | Cor | Uso | Contraste |
|---|---|---|---|
| `fundo` | `#FAF8F3` (palha clara) | fundo da página | — |
| `superficie` | `#FFFFFF` | cards | — |
| `texto` | `#1B2119` | texto principal | 15,5:1 ✅ |
| `texto-2` | `#545A50` | texto secundário | 6,7:1 ✅ |
| `texto-3` | `#6B7066` | legendas, "fonte: …" | 5,1:1 ✅ |
| `verde-safra` | `#1E6B3C` | cor da marca, botão primário, links | 6,1:1 ✅ · branco sobre ele 6,5:1 ✅ |
| `trigo` | `#8A5F12` | destaque de texto (preço, "novo") | 5,3:1 ✅ |
| `trigo-claro` | `#B07D1E` | **só** ícone e número grande (3,4:1) | ⚠️ não usar em texto pequeno |
| `perigo` | `#B42318` | alerta forte | 6,6:1 ✅ |
| `atencao` | `#8A5A00` sobre `#FFF4DC` | alerta médio | 5,4:1 ✅ |

- Fundo levemente quente (palha) em vez de branco puro: menos ofuscante no sol e mais "campo".
- **Gráficos mantêm a paleta atual** (`#2a78d6`, `#eb6834`, `#1baf7a`), que já foi validada para daltonismo. O verde da marca não entra nos gráficos, para não confundir "marca" com "dado".
- Status (bom/atenção/perigo) sempre com **ícone + palavra**, nunca só cor.

### Tipografia
- **Inter** (texto e números, com algarismos tabulares nas tabelas e cotações). Lê bem em tela pequena e no sol.
- **Títulos:** Inter 700 (uma família só = carrega rápido no 3G). Alternativa `[CONFIRMAR]`: um serifado sóbrio (ex.: Source Serif) só no título da página, para dar ar "editorial".
- Tamanho-base 16 px no celular; números-chave (veredito, preço) de 28–36 px.
- Via `theme.font` / `theme.headingFont` do Streamlit 1.66 (sem CSS de terceiros).

### Forma
- Cantos 12 px (cards) e 10 px (botões); borda de 1 px `#E4E1D8` em vez de sombra.
- Ícones **Material Symbols** do próprio Streamlit (`:material/...:`) no lugar dos emojis: desenho igual em qualquer celular.
- **Logo** `[PREENCHER: tem logo? se não, faço um símbolo simples]`. Proposta provisória: folha estilizada + "SafraViva", em SVG, aplicada com `st.logo`.

## 7. Estrutura do app

### Navegação
- **Menu no topo** (`st.navigation(position="top")`) em vez da barra lateral: no celular vira um botão de menu sempre visível. Resolve D3.
- De 12 páginas soltas para **5 seções**, com nome de verbo/pergunta do produtor:

| Seção | Páginas | Pergunta que responde |
|---|---|---|
| **Hoje** | Hoje na lavoura · Alertas | O que faço hoje? |
| **Tempo e plantio** | Previsão e clima · Época de plantio | Quando entro, quando planto? |
| **Mercado** | Cotações | Vendo agora? |
| **Minha fazenda** | Estimativa de safra · Fazenda (resultado) · Lançar · Caderno de campo | Quanto vou colher e quanto ganho? |
| **Agrônomo** | Agrônomo Digital | Pergunta livre |
| *(Região, no fim do menu)* | Produção regional · Safras boas e ruins | Para curiosos e para o portfólio |

- **Propriedade/solo/ciclo**: sai da barra lateral e vira uma **linha de contexto** no topo de cada página ("Sítio Demonstração · Solo AD3 · Ciclo médio — trocar"). Resolve D6.

### A página "Hoje na lavoura" (rolagem)
1. **Veredito do dia** (uma frase + ícone) e o alerta mais grave.
2. **Três números** (chuva 24 h · soja R$/sc hoje · fase da lavoura principal).
3. **Janela de pulverização** de hoje e amanhã (faixa horária colorida).
4. **Meus talhões**: um card por talhão (fase × tempo).
5. **Próximos 7 dias** (gráfico compacto).
6. **Atalhos**: "Perguntar ao agrônomo" · "Lançar no caderno".
7. Rodapé: fontes e horário da última atualização.

### Tela de entrada (senha)
- Logo, uma frase do que é o app, campo de senha grande, botão "Entrar". Resolve D9.

## 8. Narrativa durante a rolagem
De **decisão** para **detalhe**, sempre: primeiro o que fazer → depois por quê (dado) → depois o histórico. Cada bloco termina em uma ação ou na fonte. Em todas as páginas, a primeira dobra responde à pergunta da seção sem rolar.

## 9. Sistema de movimento (detalhe no passo 3)
- **Mínimo e funcional:** o app é ferramenta, não vitrine.
- Permitido: aparecer suave dos cards (≤ 200 ms), troca de estado em botões, indicador de "atualizando cotação".
- Proibido: parallax, contador animado em número de decisão (preço, chuva), qualquer coisa que atrase a leitura.
- `prefers-reduced-motion`: tudo desliga.

## 10. Tecnologia
- **Manter Streamlit** agora. Motivo: o app já funciona, tem 88 testes e roda de graça; o Streamlit 1.66 já permite tema, fontes, menu no topo, logo e ícones. A maior parte do ganho visual vem de **config.toml + organização**, sem reescrever.
- CSS próprio só onde o tema não alcança, **concentrado em um arquivo** (`app/estilo.css`) com os tokens da seção 6. Resolve D7.
- **Opção futura** (não agora): front-end dedicado (ex.: Next.js) consumindo uma API sobre o mesmo DuckDB/MotherDuck, se o app virar produto para outros produtores. `[CONFIRMAR: só registrar como ideia]`

## 11. Medição desde o começo
Eventos registrados numa tabela `app.evento` (no próprio banco, sem ferramenta externa):
- `pagina_vista` (página, celular/computador)
- `cta_click` (ex.: "Perguntar ao agrônomo", "Lançar no caderno", "Ver alerta")
- `alerta_aberto`, `pergunta_ia`, `lancamento_salvo`
- `ab_view` (versão do texto da primeira dobra, para o teste A/B do passo 2)
- Sem dado pessoal; só página, ação e hora.

## 12. Ordem exata de construção
1. **Tema e tokens:** `config.toml` (cores, Inter, cantos, bordas) + `app/estilo.css` + medir contraste. *(passo 2)*
2. **Logo e tela de entrada.** *(passo 2)*
3. **Menu no topo e 5 seções; ícones Material no lugar dos emojis.** *(passo 2)*
4. **Primeira dobra da "Hoje na lavoura"** (veredito + 3 números) com A/B de texto e eventos. *(passo 2)*
5. **Linha de contexto** (propriedade/solo/ciclo) no topo das páginas.
6. **Movimento mínimo** e reduzir movimento. *(passo 3)*
7. **Textos de todas as páginas** (títulos, microtextos, vazios e erros). *(passo 4)*
8. **Revisão de componentes, acessibilidade e celular 320–1920 px.** *(passo 5)*
9. **Auditoria do caminho** abrir → decidir → agir. *(passo 6)*
10. **Plano dos 30 dias** com o seu pai e com o portfólio. *(passo 7)*

Cada etapa: testes (`pytest`) passando, conferência no navegador (celular e computador) e publicação no link.

---

## O que eu preciso de você
1. **Ordem dos públicos:** seu pai primeiro e portfólio depois? `[CONFIRMAR]`
2. **Cores e logo:** aprova o verde-safra + palha + trigo? Tem logo ou faço um símbolo simples provisório? `[PREENCHER]`
3. **Fonte dos títulos:** só Inter (mais rápido) ou Inter + um serifado nos títulos (mais "editorial")? `[CONFIRMAR]`
4. **Menu:** ok trocar a barra lateral pelo menu no topo com 5 seções? `[CONFIRMAR]`
5. **Concorrentes:** se tiver um app que seu pai já usa ou que você admira, me diga o nome; senão sigo com os arquétipos.
6. **Modo demonstração sem senha** para o portfólio: quer avaliar no passo 7? `[CONFIRMAR]`

Se preferir, pode só mandar **"2"** e eu sigo com as propostas acima como padrão, deixando os `[CONFIRMAR]` anotados para a lista final.
