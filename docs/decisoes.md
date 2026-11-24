# Registro de decisões

## D001 — DuckDB agora, PostgreSQL depois (15/10/2026)
O Docker está instalado, mas o daemon não estava rodando, e o PostgreSQL não está instalado. O DuckDB não precisa de servidor, roda SQL analítico completo (CTE, window functions) e lê CSV/Parquet direto. O SQL fica em `sql/` com sintaxe padrão para migrar para PostgreSQL quando houver app multiusuário (Fase 7).

## D002 — Sem Makefile; comandos via `python -m` (15/10/2026)
O `make` não existe no Windows desta máquina. Cada tarefa é um módulo executável em `scripts/`.

## D003 — Clima: A714 (observado) + NASA POWER/ERA5 (grade) + Open-Meteo (previsão)
A A714 é a verdade de campo desde 2006, mas a PAM vai até 1974. Para analisar clima × produtividade em séries longas, usamos a grade NASA POWER (1981→) calibrada contra a A714 no período em que as duas se sobrepõem.

## D004 — Ano-safra de julho a junho; decêndio no padrão do ZARC
Permite cruzar a PAM (ano civil da colheita), o clima diário e as janelas do ZARC em `analytics.dim_tempo`.

## D005 — Escopo de culturas
Soja, milho, feijão, trigo, aveia, cevada e sorgo. Na PAM 2025 de Itapeva, a área colhida foi de 82 mil ha de soja, 28 mil ha de trigo, 27,5 mil ha de milho, 3 mil ha de feijão e 2 mil ha de cevada.

## D006 — Sem dados da fazenda por enquanto: perfil de referência regional (15/10/2026)
O produtor ainda não sabe do projeto. Tudo o que seria dado da fazenda (coordenadas, solo, ciclo, custos) usa a **referência de Itapeva** derivada de fontes públicas (ZARC, PAM, INMET, estudos regionais) e fica configurável em `.env` e `core/config.py`, para ser trocado depois.

## D007 — Janela de plantio por "gaps and islands" no decêndio do ano-safra
O ZARC publica o risco por decêndio do ano civil. Para entregar períodos legíveis ("plante de 1/out a 31/dez") e não quebrar janelas que cruzam a virada do ano (milho safrinha), o SQL ordena pelo decêndio do ano-safra (julho = 1) e agrupa decêndios consecutivos com o mesmo risco.

## D008 — Fases fenológicas por calendário regional (28/10/2026)
Sem datas reais de plantio, cada fase (semeadura → colheita) usa datas típicas de Itapeva, derivadas das janelas de risco baixo do ZARC e da duração dos ciclos (`sql/ddl/004_fases_fenologicas.sql`). Na Fase 4, elas passam a vir do caderno de campo.

## D009 — Clima como alerta, não como previsor de sacas/ha (28/10/2026)
Na validação temporal, a regressão em painel com índices por fase quase não reduz o erro em relação a "tendência + município" (insight 7). O modelo final é enxuto (1–2 índices por cultura) e serve para **explicar** e **quantificar riscos**. A estimativa de safra da Fase 6 vai usar balanço hídrico da cultura (FAO-33/Ky) com a previsão diária.

## D010 — Flag de qualidade em vez de apagar dado (28/10/2026)
Valores suspeitos (repetição do ano anterior) continuam no banco com `suspeito_repeticao = TRUE`. As análises e o modelo os excluem, mas eles continuam visíveis e auditáveis.

## D011 — Painel em Streamlit, conexões curtas e tema claro (03/11/2026)
- **Streamlit + Plotly:** é Python puro, reaproveita o SQL e os módulos de análise, e é responsivo no celular. Um front dedicado fica para a Fase 7.
- **Conexão somente-leitura aberta e fechada a cada consulta,** com cache de 5 min (previsão) e 6 h (histórico). Assim, o painel aberto não trava o ETL, que grava no mesmo arquivo DuckDB.
- **Regras de alerta em `app/alertas.py`, sem Streamlit:** são testadas (tests/test_alertas.py) e vão ser reaproveitadas pelo Agrônomo Digital (Fase 5) e pelos avisos no celular (Fase 6).
- **Tema claro fixo:** leitura sob sol, no campo. O status nunca depende só da cor: todo cartão tem ícone e rótulo escrito.
- **ZARC ainda não publicado:** quando a portaria da cultura para a próxima safra ainda não saiu (ex.: trigo 2027), o painel projeta a janela da safra anterior e avisa isso na tela.

## D012 — Ano agrícola de julho a junho também na gestão (03/11/2026)
Um plantio pertence à safra do ano agrícola da data de plantio: soja de out/2026 = 2026/27, trigo de abr/2026 = 2025/26. Assim, a rotação soja → trigo fica junta na mesma safra, e é o mesmo critério da `dim_tempo`.

## D013 — Custo previsto e referência CONAB (03/11/2026)
- **Lavoura em andamento:** a margem usa o **custo previsto** = maior entre o já lançado e o custo CONAB por hectare (sem arrendamento e sem custo de oportunidade, porque a terra é própria).
- **Praças de referência:** trigo usa a planilha da **própria Itapeva** (CONAB, nov/2025); soja e milho usam **Ponta Grossa-PR** (mar/2026), a praça CONAB com o sistema mais parecido (Campos Gerais, plantio direto). A CONAB não tem praça de soja ou milho no Sudoeste Paulista.
- **Custos sem lavoura:** despesas da propriedade (assistência, seguro...) são rateadas por área entre os plantios da safra.

## D014 — Fazenda de demonstração, marcada e removível (03/11/2026)
O produtor ainda não forneceu dados (o formulário entra no final do projeto). A "Fazenda Exemplo" usa os custos CONAB distribuídos em operações reais do calendário, produtividades coerentes com o clima medido de cada safra e plantio dentro das janelas do ZARC. Ela fica com `demo = TRUE`, mostra um aviso em todas as telas e é apagada com um clique ou com `--remover`.

## D015 — Testes de interface com AppTest (03/11/2026)
Os formulários do Streamlit são testados com `streamlit.testing.v1.AppTest`: o teste preenche e envia o formulário num banco temporário e confere a gravação. Há também um teste de fumaça de todas as páginas sobre o banco real. É mais confiável que automação de navegador para este tipo de app.

## D016 — OpenAI como provedor, atrás de uma interface (06/11/2026)
O usuário tem chave da OpenAI. O agente usa Chat Completions com *function calling* (`gpt-5-mini` por padrão, trocável em `OPENAI_MODEL`), mas o provedor fica isolado em `ProvedorOpenAI.responder()`. Trocar de modelo ou de empresa é escrever outra classe com o mesmo método, sem mexer nas ferramentas nem nas telas. A chave fica só no `.env` (fora do git) e nunca passa pelo chat.

## D017 — Ferramentas em vez de colar dados no prompt (06/11/2026)
O modelo recebe 11 ferramentas que consultam o banco e devolvem JSON com **fonte e data**. Isso deixa o prompt pequeno e barato, os números sempre vêm do dado (não da memória do modelo), cada resposta pode citar a fonte, e as regras de alerta são as mesmas do painel (`app/alertas.py`).

## D018 — Lançamento por linguagem natural com confirmação humana (06/11/2026)
`propor_lancamento` nunca grava: monta um lançamento pendente que aparece na tela com **Confirmar / Cancelar**. A gravação usa as mesmas funções de `app/gestao.py` das telas. Erros de entrada (talhão inexistente, data futura, despesa sem categoria) voltam para o modelo, que pergunta ao produtor.

## D019 — Guardrails no prompt e verificados na avaliação (06/11/2026)
O prompt do sistema exige: dados antes de opinião, citar fonte e data, dizer o que é estimativa, "não sei" quando faltar dado, **receituário agronômico** para produto e dose, e **preço não é recomendação de investimento**. `scripts/avaliar_agente.py` confere objetivamente se cada pergunta usou as ferramentas certas e se os casos sensíveis respeitaram esses limites.

## D020 — O que a avaliação com a API real corrigiu (06–23/11/2026)
A primeira rodada (gpt-5-mini) aprovou 11/12 pelo critério automático, mas a leitura das respostas achou erros que o critério não pegava:
- **Causa inventada.** O modelo atribuiu a quebra de 2011 a veranico. Agora a ferramenta entrega a `leitura_climatica` calculada por regra fixa, e o prompt manda usá-la como está.
- **Custo parcial comparado com a CONAB.** Sem safra informada, a comparação usava a safra em andamento. Agora o padrão é a última safra fechada, com `aviso` quando a safra está aberta.
- **Solo padrão no lugar do solo do talhão.** Os plantios planejados agora trazem o ZARC calculado com o solo e o ciclo do próprio talhão.
- **Estoque invisível.** O estoque só olhava a safra mais recente e não enxergava o trigo guardado da safra anterior. Agora cobre todas as safras, com custo por saca e valor ao preço de referência.
- **Venda.** O modelo inventou uma tendência de preço e sugeriu percentuais de venda. O prompt agora proíbe tendências sem dado, percentuais e atribuir a uma fonte algo que ela não trouxe, e exige a frase de "não é recomendação de investimento".

Resultado final: 12/12, com custo de cerca de 8 mil tokens por pergunta e ~20 s de resposta.

## D021 — Alertas no painel primeiro, separados por canal (23/11/2026)
Por decisão do usuário, a Fase 6 entrega os alertas **dentro do sistema** (central de alertas, aviso na tela inicial, contador no menu). O WhatsApp vem depois. A geração (`gerar_alertas`) fica separada da publicação (`CanalSistema.publicar`), então o WhatsApp vai ser só outro canal lendo os alertas novos ainda não enviados (coluna `enviado_whatsapp_em`).

## D022 — Um alerta por situação, não por execução (23/11/2026)
Cada alerta tem uma chave (tema + alvo, ex.: `lavoura|plantio:42`):
- enquanto a situação dura, a mesma linha é **atualizada**;
- se **piora** (de atenção para crítico), volta a "não lido";
- quando a situação **passa**, é marcada como resolvida.

Assim, a rotina pode rodar várias vezes por dia sem encher a tela (nem o WhatsApp, no futuro) de repetições.

## D023 — Estimativa de safra por balanço hídrico + anos análogos (23/11/2026)
- **Modelo:** FAO-56 (Kc por fase, Ks pela água no solo) e FAO-33 (Ky por fase, combinado de forma multiplicativa).
- **Clima:** observado (A714 + NASA) → últimos 45 dias do Open-Meteo, para cobrir o atraso da série observada → previsão de 16 dias → para o resto do ciclo, **cada ano desde 1991** como cenário (p10/p50/p90).
- **Capacidade de água por classe do ZARC:** de AD1 = 40 mm a AD6 = 140 mm, uma aproximação documentada a ser refinada pela análise de solo.
- **Validação** (`docs/backtest_balanco.md`):
  - soja em Itapeva: r = 0,32, melhor que qualquer índice da Fase 2;
  - milho na região: r = 0,21;
  - trigo: r ≈ 0.
- **Consequência:** a estimativa mostra a **confiabilidade**, e só soja e milho geram alerta de produtividade. No trigo valem os alertas de geada e chuva.

## D024 — Atualização automática sem depender do computador ligado o dia todo (23/11/2026)
- **Ao abrir o painel:** se a previsão tem mais de 6 h, ele atualiza previsão e alertas (~5 s).
- **Todo dia às 6h:** `scripts/rotina_diaria.py` faz a atualização completa (NASA, transformações, INMET no dia 5, resumo semanal às segundas).
- **Agendamento:** `scripts/agendar_rotina.ps1` registra a rotina no Agendador de Tarefas do Windows, só com a autorização do usuário, e roda ao ligar o computador se ele estava desligado às 6h.

## D025 — Publicação: repositório público, Streamlit Cloud, MotherDuck e senha (23/11/2026)
- **Repositório público** no GitHub pessoal (portfólio). Ficam **fora**: `.env`, o banco, `data/` e os segredos. Nenhum dado da fazenda vai para o git.
- **Banco na nuvem: MotherDuck.** É o mesmo DuckDB, então o código não muda: `core.db.conectar()` usa `md:safraviva` quando há `MOTHERDUCK_TOKEN` e o arquivo local quando não há. Com o banco na nuvem, os lançamentos feitos no painel online não se perdem quando o Streamlit Cloud reinicia o contêiner.
- **Rotina diária pelo GitHub Actions** (`.github/workflows/rotina_diaria.yml`, 6h de Brasília), sem depender do computador de casa.
- **Senha** (`APP_SENHA` nos segredos do Streamlit) protege os dados da fazenda e os créditos da OpenAI. Em casa, sem a variável, o painel abre direto.
- **Proteção contra sobrescrita:** depois de publicado, o banco **oficial é o da nuvem**. `publicar_motherduck.py` se recusa a sobrescrevê-lo sem `--substituir` e oferece `--baixar` para backup.

## D026 — Cotações "em tempo real": o que é ao vivo e o que é diário (24/11/2026)
- **Ao vivo** (atualiza sozinho a cada 5 min na tela; busca nova se o dado tiver mais de 15 min): bolsa de Chicago e dólar comercial, com ~15 min de atraso (Yahoo Finance, fonte não oficial).
- **Diário:** CEPEA, que é o preço do físico no Brasil e sai à tarde, e a PTAX. A série completa do CEPEA (desde 1997/2004) permite histórico e sazonalidade.
- **Conversão:** Chicago vira R$/saca pela paridade (US¢/bushel × 60/kg por bushel × dólar), sem prêmio, frete nem impostos. A tela mostra o prêmio de porto (Paranaguá − Chicago).
- **Preço de referência da fazenda:** passa a vir do CEPEA de forma automática, mas um preço digitado pelo produtor nunca é sobrescrito.
- **IA:** a ferramenta `cotacoes` entrega a **decomposição Chicago × dólar** calculada por regra. Na primeira resposta real, o modelo leu "Chicago em reais" (que já inclui o câmbio) e atribuiu a alta à bolsa, quando em dólar a soja estava estável e a alta veio do dólar (+9,8%). Mesma lição do D020: interpretação pronta na ferramenta em vez de inferência do modelo.
