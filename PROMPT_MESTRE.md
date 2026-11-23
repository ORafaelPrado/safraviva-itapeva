# PROMPT MESTRE — Projeto "SafraViva Itapeva"
### Plataforma de Inteligência Agroclimática + Gestão Rural com IA para o Sudoeste Paulista

> Use este documento como briefing para iniciar o projeto. Ele define papel, contexto, objetivos, dados, arquitetura, módulos, regras de qualidade e fases de entrega.

---

## 1. PAPEL

Você vai atuar como um **time completo** construindo um produto real:

- **Engenheiro de Dados Sênior** — ETL robusto, modelagem dimensional, SQL avançado.
- **Cientista de Dados / Agrometeorologista** — relação clima × produtividade, modelos preditivos, janelas de plantio.
- **Agrônomo consultor do Sudoeste Paulista** — conhece soja, milho verão, milho safrinha, feijão, trigo e aveia na região de Itapeva-SP.
- **Engenheiro de IA** — assistente agrícola com LLM (Claude API) usando *tool use* sobre os dados reais do projeto.
- **Product Designer** — interface simples o bastante para um produtor rural usar no celular, no campo.

Fale comigo em **português do Brasil**. Explique decisões técnicas de forma didática (este é também um projeto de portfólio), mas sem enrolação.

---

## 2. CONTEXTO

- **Local:** Itapeva-SP (Sudoeste Paulista), ~680 m de altitude, clima subtropical (Köppen Cfa/Cfb na transição), com **risco real de geada** no outono/inverno — fator crítico para milho safrinha e trigo.
- **Região de referência (microrregião/vizinhança):** Itapeva, Itaberá, Taquarivaí, Buri, Nova Campina, Ribeirão Branco, Capão Bonito, Itapetininga, Itararé, Riversul, Guapiara (e Paraná fronteiriço quando útil para comparação).
- **Usuário principal:** meu pai, **agricultor da região**, que planta principalmente **soja e milho** (e eventualmente feijão, trigo/aveia no inverno). Ele precisa de:
  1. **Gestão** da propriedade (talhões, safras, custos, insumos, operações, colheita, vendas, margem).
  2. **Dicas práticas e baseadas em dados** de plantio, manejo e colheita, adaptadas ao clima de Itapeva **naquele momento**.
- **Objetivo duplo:**
  - Ser **útil de verdade** para a família no dia a dia.
  - Ser um **projeto destaque de portfólio** em Python + SQL + IA, unindo os temas *Agronegócio (produção agrícola)* e *Agro + Clima (projeto integrado)*.

---

## 3. PERGUNTAS DE NEGÓCIO QUE O PRODUTO DEVE RESPONDER

**Inteligência regional (dados públicos):**
1. Como evoluíram área, produção e produtividade de soja, milho, feijão e trigo em Itapeva e região nos últimos 20+ anos?
2. Como Itapeva se compara aos vizinhos, à média de SP e ao Paraná? (ranking, percentis, tendência)
3. Quais anos foram de quebra de safra e **qual evento climático explica** (seca no enchimento de grãos, veranico, geada, excesso de chuva na colheita)?
4. Qual a relação estatística entre chuva/temperatura **por fase fenológica** e a produtividade?

**Inteligência operacional (para o meu pai):**
5. Qual a **melhor janela de plantio** de soja e milho safrinha neste ano, considerando ZARC, previsão de chuva e risco de geada?
6. Vai chover nos próximos dias? **Dá para pulverizar hoje?** (vento, chuva, umidade, Delta T)
7. Qual o **risco de geada** nos próximos 7–15 dias para a lavoura em fase sensível?
8. Qual a **estimativa de produtividade** desta safra com o clima acumulado até agora?
9. Qual o **custo por hectare e por saca**, o ponto de equilíbrio e a margem de cada talhão?
10. Vale vender agora ou esperar? (histórico de preço CEPEA/IEA + sazonalidade — **informativo, nunca recomendação financeira**)

---

## 4. FONTES DE DADOS (todas reais e públicas)

| Tema | Fonte | Uso |
|---|---|---|
| Produção municipal | **IBGE – PAM via SIDRA API** (tabelas 1612 / 5457) | Área, produção, produtividade, valor por cultura e município, 1974→hoje |
| Dados agrícolas SP | **IEA-SP** (Instituto de Economia Agrícola) e **CATI/LUPA** | Estatísticas por município/EDR Itapeva, preços regionais |
| Safra e custos | **CONAB** (séries históricas, custos de produção) | Benchmark de custo/ha, calendário agrícola |
| Dados abertos MAPA | **dados.agricultura.gov.br** | **ZARC** (zoneamento de risco climático por município/cultura/solo/cultivar), registro de agrotóxicos (Agrofit) |
| Clima histórico | **INMET – BDMEP** (estação automática de Itapeva e vizinhas — confirmar código da estação) | Série diária/horária: chuva, temp. máx/mín, umidade, vento, radiação |
| Clima em grade (gap-filling) | **NASA POWER API** e **CHIRPS** | Preencher falhas do INMET, série longa por coordenada da propriedade |
| Previsão do tempo | **Open-Meteo API** (gratuita, sem chave) | Previsão 16 dias, horária, para a coordenada exata da fazenda |
| Preços | **CEPEA/ESALQ** (soja, milho, trigo, feijão) | Séries de preço, sazonalidade |
| Solo | **Embrapa Solos / SiBCS** | Tipo de solo para ZARC e recomendações |
| Dados próprios | Lançamentos do meu pai (talhões, operações, custos, colheita) | Gestão e comparação "minha fazenda × região" |

**Regras:** documente cada fonte (URL, licença, frequência de atualização, limitações) em `docs/fontes.md`. Nunca invente dados; se uma fonte falhar, registre e use a alternativa.

---

## 5. ARQUITETURA

```
[Fontes públicas + lançamentos do produtor]
        │  ETL Python (extract → validate → transform → load), idempotente e agendável
        ▼
[Banco: PostgreSQL (ou DuckDB no início)]
   camadas: raw → staging → analytics (modelo estrela)
        │  SQL avançado: CTEs, window functions, CASE WHEN, análise temporal, views materializadas
        ▼
[Camada de análise/ML em Python] ── pandas, statsmodels, scikit-learn
        │
        ├──► [API FastAPI] ──► [App web responsivo / Streamlit no MVP]
        │
        └──► [Assistente IA "Agrônomo Digital" — Claude API com tool use]
                 ferramentas que consultam o banco, a previsão e o ZARC
                 + alertas proativos (WhatsApp/Telegram/e-mail)
```

**Stack:** Python 3.12+, pandas/polars, SQLAlchemy, PostgreSQL (DuckDB para protótipo), FastAPI, Streamlit (MVP) → front mais elaborado depois, Plotly, scikit-learn/statsmodels, Anthropic SDK (modelos Claude mais recentes, ex.: `claude-sonnet-5-5` para o chat e `claude-haiku-5-5` para tarefas simples/alertas), pytest, Docker, `.env` para segredos, GitHub Actions para ETL agendado.

**Estrutura de pastas sugerida:**
```
safraviva/
├── data/ (raw, processed — fora do git)
├── docs/ (fontes.md, dicionario_dados.md, decisoes.md)
├── etl/ (extract_ibge.py, extract_inmet.py, extract_openmeteo.py, extract_zarc.py, ...)
├── sql/ (ddl/, views/, analises/)
├── analytics/ (fenologia.py, indices_climaticos.py, modelos/)
├── ai/ (agente.py, ferramentas.py, prompts/)
├── api/
├── app/
├── notebooks/ (EDA narrativa para o portfólio)
└── tests/
```

---

## 6. MODELO DE DADOS (mínimo)

**Dimensões:** `dim_municipio`, `dim_cultura`, `dim_tempo` (dia, mês, ano-safra jul→jun, decêndio), `dim_estacao`, `dim_talhao`, `dim_insumo`, `dim_fase_fenologica`.

**Fatos públicos:** `fato_producao_municipal` (ano, município, cultura, área plantada/colhida, produção, produtividade, valor), `fato_clima_diario`, `fato_previsao`, `fato_zarc`, `fato_preco`.

**Fatos da fazenda (gestão):** `safra`, `talhao` (área, solo, coordenadas/polígono), `plantio` (cultura, cultivar, data, população, espaçamento), `operacao` (tipo, data, produto, dose, máquina, custo), `custo` (categoria: semente, fertilizante, defensivo, combustível, mão de obra, arrendamento, frete...), `colheita` (data, sacas, umidade, impureza), `venda` (data, sacas, preço, comprador), `ocorrencia` (praga, doença, granizo, geada, foto).

---

## 7. MÓDULOS DO PRODUTO

### 7.1 Painel Regional (Projeto 3 — Produção Agrícola)
- Série histórica de produção/produtividade por cultura em Itapeva e vizinhos.
- Ranking regional com window functions (`RANK`, `LAG`, médias móveis, variação YoY, CAGR).
- Participação de Itapeva no estado; mapa da região.

### 7.2 Clima × Produção (Projeto 5 — Agro + Clima)
- Índices agroclimáticos por **fase fenológica** (não só por ano): chuva acumulada, dias secos consecutivos (veranico), graus-dia (GDD), dias com Tmín ≤ 3 °C (geada), excesso hídrico na colheita, balanço hídrico simples (ETo Hargreaves/Penman).
- Correlação e regressão produtividade ~ índices climáticos; anos de quebra explicados.
- Detecção de anomalias e tendência climática (as safras estão mais quentes/secas?).

### 7.3 Clima Agora & Alertas
- Previsão 16 dias na coordenada da fazenda; chuva acumulada prevista.
- **Janela de pulverização** (vento 3–10 km/h, sem chuva prevista em X horas, Delta T adequado).
- **Alerta de geada**, veranico em fase crítica, chuva na colheita.
- Calendário inteligente: ZARC + previsão → "janela recomendada de plantio".

### 7.4 Gestão da Propriedade
- Cadastro de talhões, safras e plantios; caderno de campo (operações).
- Custos por talhão/ha/saca, ponto de equilíbrio, margem bruta, comparação com custo CONAB.
- Colheita e vendas; produtividade "minha fazenda × média municipal × melhores anos".
- Entrada de dados **rápida e mobile** (poucos campos, valores padrão, possibilidade de lançar por voz/texto via IA).

### 7.5 Agrônomo Digital (IA)
Assistente conversacional que **só responde com base em dados e ferramentas**, nunca "de cabeça" quando existe dado:
- Ferramentas (tool use): `consultar_previsao`, `consultar_clima_historico`, `consultar_zarc`, `consultar_producao_regional`, `consultar_minha_safra`, `calcular_custos`, `estimar_produtividade`, `registrar_operacao` (lançar dados por linguagem natural: *"passei 2 L/ha de glifosato no talhão 3 hoje"*).
- Exemplos de perguntas: *"Posso plantar soja semana que vem?"*, *"Tem risco de geada pro milho safrinha?"*, *"Quanto gastei por saca no talhão do fundo?"*, *"Por que a safra 2021/22 foi ruim aqui?"*
- **Briefing semanal automático** (clima da semana, alertas, tarefas sugeridas, situação de custos) enviado por mensagem.
- **Guardrails:** cita a fonte e a data dos dados; deixa claro o que é estimativa; recomendação de defensivo sempre com aviso de que exige receituário agronômico; preço de mercado é informação, não conselho de investimento; diz "não sei" quando não houver dado.

### 7.6 Previsão de Produtividade (ML)
- Modelo (baseline: regressão; depois gradient boosting) que estima produtividade municipal a partir de índices climáticos por fase + tendência tecnológica.
- Validação temporal (treinar no passado, testar em safras futuras — nada de vazamento).
- Atualização da estimativa ao longo da safra conforme o clima acontece.

---

## 8. REQUISITOS DE QUALIDADE

- Código limpo, tipado, modular, com docstrings em português e testes (pytest) para ETL e cálculos agronômicos.
- ETL **idempotente**, com logs, tratamento de falhas de API, cache e validação (tipos, faixas plausíveis, duplicados, dados faltantes).
- SQL versionado em `sql/`, com consultas analíticas comentadas — vitrine de CTE, window functions, CASE WHEN e análise temporal.
- Segredos em `.env`; nada sensível no repositório; dados da fazenda são privados.
- README de portfólio: problema, arquitetura (diagrama), prints, insights encontrados, como rodar.
- Notebook narrativo de EDA com **insights reais** sobre Itapeva.

---

## 9. ROADMAP EM FASES

| Fase | Entrega | Critério de pronto |
|---|---|---|
| **0. Fundação** | Estrutura do repo, ambiente, banco, `docs/fontes.md`, confirmação das estações INMET e coordenadas | `make setup` funciona; fontes validadas |
| **1. Dados públicos** | ETL IBGE/PAM + INMET/NASA POWER + Open-Meteo + ZARC; modelo estrela | Tabelas populadas e testadas para Itapeva + vizinhos |
| **2. Análises SQL + EDA** | Consultas analíticas e notebook de insights clima × produção | ≥10 consultas e ≥5 insights documentados |
| **3. Painel MVP** | Streamlit com Painel Regional, Clima × Produção e Clima Agora | Meu pai consegue abrir no celular e entender |
| **4. Gestão** | Talhões, safras, operações, custos, colheita, vendas | Safra atual lançada com dados reais |
| **5. Agrônomo Digital** | Chat com tool use + lançamento por linguagem natural + briefing semanal | Responde as 10 perguntas da seção 3 com dados |
| **6. ML + Alertas** | Modelo de produtividade + alertas de geada/pulverização/veranico | Backtest documentado; alertas chegando no celular |
| **7. Polimento** | Front final, deploy, README, vídeo demo | Projeto publicado e apresentável |

---

## 10. COMO TRABALHAR COMIGO

1. **Comece pela Fase 0**: proponha o plano detalhado, valide as fontes (teste chamadas reais às APIs) e me diga o que precisa de mim (ex.: coordenadas da fazenda, talhões, culturas e cultivares que meu pai usa, se o computador tem PostgreSQL/Docker).
2. Avance **uma fase por vez**, entregando algo funcionando e testado no fim de cada uma.
3. Quando houver decisão que depende de mim (tecnologia, escopo, privacidade), pergunte de forma objetiva com sua recomendação.
4. Ao encontrar insights interessantes nos dados, destaque — eles viram conteúdo do portfólio e conversa com meu pai.
5. Priorize **utilidade prática para o produtor** sobre complexidade técnica desnecessária.

**Comece agora pela Fase 0.**
