# Dicionário de dados — SafraViva

Fluxo: `etl/*.py` → **raw** (como veio da fonte) → `sql/transform/*.sql` → **analytics** (consumo).
Para recarregar: `python -m scripts.rodar_etl`. Para recalcular só a camada analytics: `--so-transformar`.

## Dimensões (`analytics`)
| Tabela | Grão | Destaques |
|---|---|---|
| `dim_municipio` | município | código IBGE, microrregião, `foco` (Itapeva), centroide `lat/lon`, `area_km2` |
| `dim_cultura` | cultura | `slug` (soja, milho...), `codigo_sidra`, `estacao` (verão/inverno) |
| `dim_estacao` | estação INMET | A714 Itapeva + 3 de apoio, distância até Itapeva |
| `dim_tempo` | dia (1970–2035) | `ano_safra` (jul→jun, ex.: `2026/27`), `decendio` 1–36 (padrão ZARC), estação do ano |

## Fatos (`analytics`)
| Tabela | Grão | Origem | Colunas principais |
|---|---|---|---|
| `fato_producao` | nível × local × cultura × ano | IBGE PAM 1612 (1974→) | áreas (ha), `producao_t`, `rendimento_kg_ha` / `_sc_ha`, `valor_mil_reais`, `perda_area_pct`, `var_rendimento_aa`, `media_movel_5a_kg_ha`, `desvio_vs_media_5a`, `suspeito_repeticao` |
| `fato_clima_inmet_diario` | estação × dia local | INMET BDMEP horário | chuva, Tmáx/Tmín/Tméd, umidade, vento, rajada, radiação (MJ/m²); só vale o dia com ≥ 20 h válidas |
| `fato_clima_nasa_diario` | município × dia (1981→) | NASA POWER | chuva, temperaturas, umidade, vento a 2 m, radiação |
| `calibracao_nasa_a714` | mês | A714 × NASA | viés de Tmín/Tmáx/Tméd, correlações e razão de chuva |
| `fato_clima_itapeva` | dia | A714 + NASA calibrada | série única de Itapeva; `fonte` diz a origem de cada dia |
| `clima_diario` | série × município × dia | NASA / Itapeva | entrada única dos índices (`serie` = `nasa` ou `itapeva`) |
| `dim_fase_fenologica` | cultura × fase | calendário regional | datas típicas de semeadura → colheita (soja, milho verão, trigo) |
| `indices_fase` | série × município × cultura × ano PAM × fase | `clima_diario` | chuva, dias de chuva, maior veranico, ETo, balanço hídrico, graus-dia, dias ≥ 32 °C, dias ≤ 3 °C, `cobertura` |
| `fato_zarc` | safra × município × cultura × ciclo × solo × manejo × decêndio | MAPA ZARC | `risco_pct` (20/30/40; 0 = não indicado), `indicado`, rótulos de ciclo e solo |
| `janela_plantio` | período contínuo com o mesmo risco | `fato_zarc` (gaps and islands) | `data_inicio`, `data_fim`, `nivel_risco` (baixo/médio/alto), `n_decendios`; atravessa a virada do ano |

## Views
| View | Uso |
|---|---|
| `vw_previsao_diaria_atual` | últimos 16 dias de previsão emitidos (Open-Meteo) |
| `vw_previsao_horaria_atual` | previsão horária + `delta_t_c` (janela de pulverização ideal: 2–8 °C) |

## Convenções
- O nível SIDRA `municipio` cobre os 11 municípios da região; `uf` cobre SP (35) e PR (41); `brasil` cobre o país.
- Datas de clima no horário local (UTC−3); o INMET vem em UTC e é convertido na agregação diária.
- Unidades no nome da coluna (`_mm`, `_c`, `_pct`, `_ha`, `_t`, `_kg_ha`, `_sc_ha`).

## Análises
`sql/analises/NN_*.sql` são 12 consultas, uma pergunta de negócio cada. `python -m scripts.rodar_analises` gera
`data/processed/analises/*.csv` e [analises_resultados.md](analises_resultados.md).

## Gestão da propriedade (`fazenda`, Fase 4)
| Tabela | Grão | Destaques |
|---|---|---|
| `propriedade` | fazenda | `demo` = TRUE na fazenda de demonstração |
| `talhao` | talhão | `area_ha`, `solo_ad` (AD1–AD6, mesma classe do ZARC) |
| `plantio` | talhão × safra × temporada | `cultura`, `cultivar`, `grupo_ciclo`, `data_plantio`, `produtividade_meta_sc_ha`, `status` (planejado → plantado → colhido/perdido) |
| `operacao` | operação no campo | caderno de campo: `tipo`, `produto`, `dose`, `unidade`, `custo_total` + `categoria_custo` (opcionais) |
| `custo` | despesa | com `plantio_id`: custo direto; sem: custo da propriedade na safra, rateado por área |
| `colheita` | colheita | `sacas` de 60 kg, umidade, impureza |
| `venda` | venda | `sacas`, `preco_sc`, `comprador` |
| `ocorrencia` | ocorrência | praga, doença, geada, granizo, seca...; `severidade` 1–3 |
| `preco_referencia` | cultura | preço da saca para estimar a receita do que não foi vendido (editável) |

| View | Uso |
|---|---|
| `vw_plantio` | plantio + talhão + propriedade + área efetiva |
| `vw_custo_plantio` | custos por plantio e categoria: operações, despesas diretas e rateio |
| `vw_resultado_plantio` | custo, custo previsto, produtividade, preço (vendas ou referência), receita, margem, custo por saca, **ponto de equilíbrio** |
| `vw_estadio_atual` | fase atual de cada lavoura plantada (`analytics.dim_fase_duracao`) |

Referências: `raw.conab_custo` (planilhas CONAB) → `analytics.custo_referencia` (custo mais recente por cultura e categoria, na praça mais parecida com Itapeva).

## Agrônomo Digital (`ai`, Fase 5)
| Tabela | Grão | Destaques |
|---|---|---|
| `ai.conversa` | pergunta respondida | `origem` (chat, resumo_semanal, avaliacao), `pergunta`, `resposta`, `ferramentas` (JSON com nome, argumentos e erro), `modelo`, `tokens_entrada`, `tokens_saida`, `segundos` |

## Alertas e estimativa (Fase 6)
| Tabela / view | Grão | Destaques |
|---|---|---|
| `notif.alerta` | alerta (uma linha por situação) | `chave` (tema + alvo), `nivel` (critico/atencao/info), `titulo`, `detalhe`, `criado_em`, `atualizado_em`, `resolvido_em`, `lido_em`, `enviado_whatsapp_em` |
| `notif.vw_alertas_ativos` | alerta ativo | + `novo` (não lido) e `prioridade` |
| `raw.clima_recente_diario` | dia (últimos 45) | chuva, ET0, Tmáx/Tmín do Open-Meteo, para cobrir o atraso da série observada no balanço hídrico |

A estimativa de safra é calculada sob demanda (`analytics/balanco_hidrico.py`) e não fica gravada; o painel guarda em cache por 30 min.

## Cotações
| Tabela | Grão | Destaques |
|---|---|---|
| `raw.cotacao_diaria` | série × dia | `serie` (cepea_soja_parana, cepea_soja_paranagua, cepea_milho, cepea_trigo_parana, cbot_soja/milho/trigo, dolar, dolar_ptax), `valor` na unidade original, `valor_rs_sc` normalizado para R$/saca 60 kg |
| `raw.cotacao_intradia` | série × 15 min (bolsa) / 5 min (dólar) | último pregão |
| `raw.cotacao_ultima` | série de bolsa | preço, variação do dia, horário do mercado, `preco_rs_sc` |

## Uso do painel (`uso`)
| Tabela | Grão | Colunas |
|---|---|---|
| `uso.evento` | um evento | `ts`, `sessao` (id aleatório por sessão), `evento` (`pagina_vista` · `ab_view` · `cta_click`), `pagina`, `detalhe` (ex.: `agronomo\|v=B`), `dispositivo` (`celular` · `computador`). Sem dado pessoal. |

Eventos de ação (passo 6): `pergunta_ia` (detalhe `sugestao` ou `digitada`; página `agronomo` ou `cotacoes`) e `lancamento_salvo` (detalhe = tipo, ex.: `colheita`, ou `ditado_ia` quando confirmado no Agrônomo). Relatório: `python -m scripts.relatorio_uso`.

## Ficha da fazenda (`fazenda.ficha`)
| Coluna | Descrição |
|---|---|
| `id`, `enviada_em` | identificação e hora do envio |
| `respostas` | JSON com tudo o que o produtor preencheu (fazenda, talhões, histórico sc/ha, venda, custo, WhatsApp, observações) |
| `propriedade_id` | propriedade criada a partir da ficha (NULL se só guardada) |
| `situacao` | `aplicada` (fazenda criada) ou `guardada` (para conferência) |
