# Fontes de dados — SafraViva Itapeva

Validadas com chamadas reais em **15/10/2026** (`python -m scripts.validar_fontes` → 9/9 OK).

| # | Fonte | Endpoint | Licença | Atualização | Uso no projeto | Status |
|---|---|---|---|---|---|---|
| 1 | IBGE Localidades | `servicodados.ibge.gov.br/api/v1/localidades` | Pública | Rara | Códigos dos municípios | ✔ |
| 2 | IBGE SIDRA — PAM tabela **1612** | `apisidra.ibge.gov.br/values/t/1612/...` | Pública | Anual (set/out) | Área, produção, rendimento e valor por município, **1974–2025** | ✔ |
| 3 | INMET — catálogo de estações | `apitempo.inmet.gov.br/estacoes/T` | Pública | Contínua | Metadados das estações | ✔ |
| 4 | INMET — BDMEP histórico | `portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip` | Pública | Mensal (o pacote do ano corrente é atualizado) | Série **horária** da A714 (2006→30/09/2026) | ✔ (~90 MB/ano) |
| 5 | NASA POWER | `power.larc.nasa.gov/api/temporal/daily/point` | Pública (NASA) | Diária (atraso de alguns dias) | Série longa por coordenada, desde 1981; preenche falhas | ✔ |
| 6 | Open-Meteo — previsão | `api.open-meteo.com/v1/forecast` | CC BY 4.0 | Horária | Previsão de 16 dias para a fazenda | ✔ |
| 7 | Open-Meteo — histórico (ERA5) | `archive-api.open-meteo.com/v1/archive` | CC BY 4.0 | Diária | Reanálise 1940→, apoio a gap-filling | ✔ |
| 8 | MAPA — ZARC Tábua de Risco | `dados.agricultura.gov.br` (CKAN), dataset `tabua-de-risco-zoneamento-agricola-de-risco-climatico` | CC BY | Por safra | Janelas de plantio por decêndio, cultura, solo e ciclo; safras 2016/17 → **2026/27** | ✔ (CSV nacional grande; filtrar por geocódigo) |
| 9 | CEPEA/ESALQ | `cepea.org.br/br/indicador/*.aspx` | Uso com citação | Diária | Preços de soja, milho, trigo, feijão | ✔ acessível; sem API (planilha/raspagem) |

## Custos e preços (Fase 4)
| Fonte | Endpoint | Uso | Status |
|---|---|---|---|
| **CONAB — custos de produção** | `gov.br/conab/.../arquivos-custo-de-producao/agricolas/*.xls` (uma aba por praça e ano) | Trigo: **Itapeva-SP** (nov/2025, R$ 4.745/ha de custo operacional, 58 sc/ha). Soja e milho verão: **Ponta Grossa-PR** (mar/2026, R$ 5.448/ha e R$ 11.788/ha). | ✔ (`etl/conab_custos.py`) |
| Preços ao produtor (pesquisa em 03/11/2026) | Cepea/Esalq (soja PR R$ 152,22 em 30/10); Deral/SEAB e Copagril (trigo ~R$ 80); cooperativas e CONAB PR (milho R$ 52–55,50) | Preço de referência editável em `fazenda.preco_referencia` | manual |

Observação: o portal `portaldeinformacoes.conab.gov.br` não responde daqui (erro de certificado/conexão). As planilhas no gov.br funcionam.

## Cotações (24/11/2026)
| Fonte | Endpoint | O que é | Licença / observação |
|---|---|---|---|
| **CEPEA/ESALQ** | `cepea.org.br/br/indicador/series/{produto}.aspx?id=…` (planilha) | Preço do físico, diário: soja Paraná (id 12, desde 1997) e Paranaguá (92), milho ESALQ/B3 Campinas (77), trigo Paraná (178, em R$/t → convertido para R$/sc) | **CC BY-NC 4.0**: uso não comercial com crédito. A planilha vem com uma irregularidade de formato (lida com `ignore_workbook_corruption`) |
| **CBOT via Yahoo Finance** | `query1.finance.yahoo.com/v8/finance/chart/{ZS=F, ZC=F, ZW=F, BRL=X}` | Futuros de Chicago (US¢/bushel) e dólar comercial; intradiário de 15 min (bolsa) e 5 min (dólar); histórico diário de 2 anos | **Não oficial**, pode mudar sem aviso; atraso de ~10–15 min. Convertido para R$/sc sem prêmio, frete e impostos |
| **Banco Central (PTAX)** | `olinda.bcb.gov.br/olinda/servico/PTAX/...` | Dólar PTAX oficial, diário | API pública oficial |

## Ainda não validadas (próximas fases)
- **IEA-SP / CATI-LUPA** — estatísticas do EDR de Itapeva e preços regionais.
- **Embrapa Solos** — tipo de solo (necessário para escolher a linha correta do ZARC).
- **CHIRPS** — chuva por satélite (opcional, se NASA/ERA5 não bastarem).

## Pegadinhas descobertas na Fase 0
1. **User-Agent obrigatório**: INMET encerra a conexão e o CKAN do MAPA responde 403 para clientes sem User-Agent de navegador. Resolvido em `core/http.py`.
2. **Certificado do IBGE**: o servidor não envia a cadeia completa, então o `certifi` falha no Python e o curl do Windows passa. Resolvido usando o repositório de certificados do sistema (`truststore`).
3. **API de dados do INMET** (`/estacao/{ini}/{fim}/{cod}`) devolve **204 sem conteúdo** sem token. Por isso usamos o pacote anual do BDMEP para o histórico e o Open-Meteo para o tempo recente e a previsão.
4. **Range HTTP não é suportado** no CSV do ZARC: é preciso baixar o arquivo inteiro em streaming e filtrar Itapeva durante a leitura.
5. No SIDRA, `..` = não disponível, `-` = zero absoluto e `...` = não se aplica. O ETL precisa tratar os três de forma diferente.

## Qualidade dos dados (achados da carga inicial — 15/10/2026)
| Fonte | Achado | Tratamento |
|---|---|---|
| PAM / Itapeva | A soja de **2025 repete 2024** (241.819 t × 241.814 t; 2.949 kg/ha nos dois anos), enquanto os vizinhos variam (Itaberá: 2.528 → 3.930 kg/ha). Guapiara, Nova Campina e Ribeirão Branco também repetem. É provável que o informante municipal tenha repetido o valor do ano anterior. | Marcar como **suspeito** na Fase 2 e conferir com IEA/CONAB antes de usar em modelos. |
| INMET A714 | 91,5% dos dias com chuva válida e 93% com Tmín válida (2006→30/09/2026). | Dias inválidos são preenchidos com NASA POWER (`fato_clima_itapeva.fonte`). |
| NASA × A714 | Correlação de 0,95 na Tmín e 0,66 na chuva diária; razão do total de chuva de 0,99; **NASA 0,6 °C mais fria** na Tmín. | Calibrar na Fase 2; a correlação diária da chuva é moderada, então a NASA serve para acumulados, não para o dia a dia. |
| Estações de apoio | A715 80%, A725 73%, A821 69% de dias completos. | Uso só como apoio. |

## Estações INMET próximas
| Código | Estação | Distância | Altitude | Desde |
|---|---|---|---|---|
| **A714** | **Itapeva** | ~1 km do centro | 743 m | 2006 |
| A715 | São Miguel Arcanjo | 90 km | 710 m | 2006 |
| A725 | Avaré | 98 km | 776 m | 2006 |
| A821 | Joaquim Távora (PR) | 121 km | 513 m | 2006 |
