# Perfil agronômico de referência — Itapeva e Sudoeste Paulista

Este documento é a base de conhecimento do Agrônomo Digital. Enquanto não houver dados da fazenda,
**a região de Itapeva é a referência**. Cada afirmação traz a fonte; as seções marcadas com
📊 são calculadas a partir do banco (`analytics.*`) e atualizadas pelo ETL.

## 1. Território e clima
- **Itapeva:** 1.826 km² (IBGE, malhas), centroide −23,91 / −48,87, estação INMET **A714** a 743 m de altitude.
- **Regulação da soja (Defesa Agropecuária SP, Portaria SDA/MAPA nº 1.271/2025, mantida para 2026/27):** todos os 11 municípios do projeto estão na **Região 1** do estado.
  - **Vazio sanitário:** de 1º/jun a 31/ago, sem soja viva no campo (controle da ferrugem-asiática).
  - **Calendário de semeadura:** de 1º/set a 29/dez.
  - **Cadastro obrigatório** das áreas na Defesa Agropecuária até 15 dias após o fim do calendário (Resolução SAA 87/2024).
- **Geada:** é um risco real no outono e no inverno. O caso de referência é a onda de frio de 30/06/2021, com mínima de 1,8 °C na grade ERA5 (Open-Meteo). Os dados da A714 vão medir a frequência com precisão (📊 Fase 2).

## 2. Solos
- Não há levantamento pedológico municipal publicado em escala de detalhe. Nos estudos da Estação Ecológica de Itapeva (Instituto Florestal/SP), aparecem **Latossolo Vermelho** (textura argilosa, álico e distrófico), **Argissolo Amarelo/Vermelho-Amarelo** (textura arenosa a média), Neossolo Litólico nas encostas e Gleissolos nas várzeas.
- **Implicação prática:** os Latossolos argilosos das chapadas concentram os grãos. São profundos e mecanizáveis, mas ácidos e pobres em fósforo, então exigem calagem e adubação fosfatada.
- **ZARC:** a partir de 2023/24, o solo passa a ser classificado pela **água disponível (AD1 a AD6)**. Antes disso, usava as classes Arenoso, Textura média e Argiloso. 📊 As classes indicadas para Itapeva estão em `analytics.fato_zarc`.

## 3. Culturas (📊 PAM 2025, área colhida em Itapeva)
| Cultura | Área (ha) | Papel no sistema |
|---|---|---|
| Soja | 82.000 | carro-chefe do verão |
| Trigo | 28.000 | principal cultura de inverno, base da rotação |
| Milho | 27.500 | verão e segunda safra |
| Feijão | 3.000 | verão/"das águas" |
| Sorgo | 2.700 | segunda safra/cobertura |
| Cevada | 2.000 | inverno, sob contrato com maltarias |

## 3.1 Janelas de plantio — ZARC 2026/27 para Itapeva, sequeiro (📊 `analytics.janela_plantio`)
O risco indicado pelo ZARC é de 20% (baixo), 30% (médio) ou 40% (alto); fora das janelas, o plantio não é indicado. AD1 é o solo com menor água disponível (arenoso) e AD6 o com maior.

| Cultura | Ciclo | Solo | Risco baixo | Observação |
|---|---|---|---|---|
| Soja | Grupo II | AD4 | **1/out – 31/dez** | set = risco médio |
| Soja | Grupo II | AD1 | **1/nov – 20/dez** | out = médio/alto; solo arenoso pede plantio mais tarde |
| Soja | Grupos I–III | AD6 | 1/set – 31/dez | maior água disponível; no AD5, o início de setembro já tem risco médio nos grupos I–II |
| Milho 2ª safra | Grupo II | AD4 | **21/dez – 20/jan** e 11/fev – 10/mar | 21/jan–10/fev = médio |
| Milho 2ª safra | Grupo II | AD1 | só 11–20/fev | jan = alto; safrinha arriscada em solo arenoso |
| Trigo (2025/26) | Grupos I–II | AD4 | **1/abr – 31/mai** | após 1/jun o risco sobe (geada no espigamento / falta de água) |

**Leitura prática:** a sucessão soja → milho safrinha só funciona com soja precoce plantada no início de outubro, em solos com boa água disponível. É a mesma lógica do sistema soja → trigo, que domina a região (28 mil ha de trigo).

## 3.2 Geada medida na A714 (📊 2006–2026)
- O abrigo meteorológico (a 2 m de altura) **nunca registrou Tmín ≤ 0 °C**. Mesmo assim, já houve geada na lavoura: com 2–3 °C no abrigo, a relva pode chegar a valores negativos.
- As safras com Tmín ≤ 3 °C foram 2013/14 (0,5 °C), 2019/20 (1,3 °C), 2020/21 (1,4 °C, incluindo 30/06/2021) e **2021/22 (0,1 °C, jul/2021)**.
- O alerta de geada vai usar um limiar de abrigo de **≤ 3 °C** (Fase 6), com calibração entre A714 e NASA.

## 4. Custos e logística (referência regional)
- **CONAB, custo de produção do trigo em Itapeva-SP** (nov/2025, alta tecnologia, plantio direto, 3.500 kg/ha = 58,3 sc/ha):
  - custo variável de R$ 3.650/ha, custo operacional de **R$ 4.745/ha** e custo total de R$ 5.639/ha;
  - os maiores itens são fertilizantes (R$ 1.192), agrotóxicos (R$ 656), sementes (R$ 473) e arrendamento (R$ 700).
- **CONAB, soja em Ponta Grossa-PR** (mar/2026, 63,3 sc/ha): custo operacional de **R$ 5.448/ha**, custo total de R$ 7.728/ha. **Milho verão** (200 sc/ha): custo operacional de R$ 11.788/ha.
- **Preços ao produtor em out/2026:** soja R$ 152 (Cepea PR), milho R$ 52–55, trigo cerca de R$ 80. Com esses preços e o custo operacional CONAB, o ponto de equilíbrio da soja é de cerca de 36 sc/ha. O do trigo é de **~59 sc/ha com arrendamento** (para quem arrenda, o trigo empata com a produtividade de referência) e ~50 sc/ha em terra própria.
- **Custo operacional da soja na região de Itapeva** (Agrianual 2019, citado por Cavallari et al., UNESP, 2021), em R$/t:

  | Tipo de soja | Produtividade | Operações | Insumos | Administrativo | Pós-colheita | **Total** |
  |---|---|---|---|---|---|---|
  | Convencional | 3,36 t/ha | 150 | 532 | 66 | 75 | **824** |
  | Transgênica (2ª geração) | 3,54 t/ha | 136 | 513 | 67 | 79 | **796** |

  Isso equivale a cerca de R$ 2.700–2.800/ha a preços de 2019, valor que precisa ser atualizado (Fase 4).
- **Transporte até o Porto de Santos:** 364 km. O custo de transporte (sem a margem do transportador) é de R$ 204,50/t mais R$ 20,90/t de pedágio, total de **R$ 225/t** (mesmo estudo, base 2019).
- **Referências atuais de outros estados, só para comparação (safra 2025/26):** MT R$ 4.073–4.174/ha (Imea); MS R$ 6.116/ha com produtividade de 53 sc/ha (Aprosoja-MS).

## 5. Pendências de pesquisa
- Cultivares e grupos de maturação mais usados na região (ensaios de cultivares de IAC, Embrapa e Fundação ABC).

## Fontes
- Defesa Agropecuária SP — [lista de municípios por região da soja](https://www.defesa.agricultura.sp.gov.br/arquivos/sanidade-vegetal/LISTA-DE-MUNICIPIOS-CADA-REGIAO-SOJA.pdf)
- Agência SP — [SP inicia calendário de semeadura da soja](https://www.agenciasp.sp.gov.br/sp-inicia-calendario-de-semeadura-da-soja/)
- Compre Rural — [CNA alerta para calendário de semeadura 26/27](https://comprerural.com/cna-alerta-para-calendario-de-semeadura-26-27-e-vazio-sanitario-da-soja/)
- Instituto Florestal — [Os solos da Estação Ecológica de Itapeva](https://smastr16.blob.core.windows.net/iflorestal/RIF/SerieRegistros/IFSR40/IFSR40_217-222.pdf)
- Cavallari et al. (2021), *Energia na Agricultura* 36(4):471-477 — [Custo de transporte rodoviário de soja de Itapeva-SP até o Porto de Santos](https://revistas.fca.unesp.br/index.php/energia/article/download/4115/3164/19990)
- Compre Rural/Imea — [custo da soja 2025/26 em MT](https://comprerural.com/imea-custo-de-producao-da-soja-na-safra-2025-26-cai-196/)
- Revista Cultivar — [custo da soja 2025/26 em MS](https://revistacultivar.com.br/noticias/custo-de-producao-da-soja-sobe-1-9-em-ms-na-safra-2025-26)
- Conab — [planilhas de custo de produção da soja](https://www.conab.gov.br/info-agro/custos-de-producao/planilhas-de-custo-de-producao/itemlist/category/824-soja)
