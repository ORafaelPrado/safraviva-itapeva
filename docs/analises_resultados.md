# Resultados das análises SQL

_Gerado automaticamente por `python -m scripts.rodar_analises` em 28/10/2026 23:37. Não edite à mão; a interpretação está em [insights.md](insights.md)._

## 01_evolucao_por_decada

**como área e produtividade de soja, milho e trigo evoluíram em Itapeva, década a década?**

Consulta: [`sql/analises/01_evolucao_por_decada.sql`](../sql/analises/01_evolucao_por_decada.sql)

| cultura | decada | area_media_ha | rendimento_sc_ha | ganho_rend_vs_decada_ant_pct |
|---|---|---|---|---|
| milho | 1970s | 11.385 | 23,1 | – |
| milho | 1980s | 14.143 | 36,4 | 57 |
| milho | 1990s | 18.230 | 60,5 | 66 |
| milho | 2000s | 29.728 | 105,7 | 75 |
| milho | 2010s | 31.375 | 125,4 | 19 |
| milho | 2020s | 35.833 | 121,3 | -3 |
| soja | 1970s | 5.977 | 20,1 | – |
| soja | 1980s | 3.168 | 25 | 24 |
| soja | 1990s | 2.129 | 34,7 | 39 |
| soja | 2000s | 21.433 | 50 | 44 |
| soja | 2010s | 59.400 | 60,8 | 22 |
| soja | 2020s | 78.300 | 65,5 | 8 |
| trigo | 1970s | 3.233 | 16,3 | – |
| trigo | 1980s | 2.827 | 20,2 | 24 |
| trigo | 1990s | 2.278 | 26 | 28 |
| trigo | 2000s | 6.018 | 37 | 42 |
| trigo | 2010s | 13.938 | 51,3 | 39 |
| trigo | 2020s | 31.400 | 55,7 | 9 |

## 02_ranking_regional

**qual o peso de Itapeva na região e como ela se posiciona em área e produtividade?**

Consulta: [`sql/analises/02_ranking_regional.sql`](../sql/analises/02_ranking_regional.sql)

| cultura | nome_local | area_media_ha | participacao_regiao_pct | rank_area | rendimento_sc_ha | rank_rendimento |
|---|---|---|---|---|---|---|
| milho | Itapeva (SP) | 33.900 | 27,9 | 1 | 121,4 | 2 |
| milho | Buri (SP) | 16.680 | 13,7 | 2 | 93,1 | 10 |
| milho | Itaberá (SP) | 16.400 | 13,5 | 3 | 110,4 | 4 |
| milho | Capão Bonito (SP) | 15.400 | 12,7 | 4 | 100,2 | 6 |
| milho | Itapetininga (SP) | 12.020 | 9,9 | 5 | 100,5 | 5 |
| milho | Itararé (SP) | 8.180 | 6,7 | 6 | 138,5 | 1 |
| milho | Ribeirão Branco (SP) | 8.080 | 6,6 | 7 | 96 | 9 |
| milho | Taquarivaí (SP) | 5.800 | 4,8 | 8 | 114,2 | 3 |
| milho | Guapiara (SP) | 3.600 | 3 | 9 | 99 | 7 |
| milho | Riversul (SP) | 1.300 | 1,1 | 10 | 96,3 | 8 |
| milho | Nova Campina (SP) | 312 | 0,3 | 11 | 84,6 | 11 |
| soja | Itapeva (SP) | 78.500 | 30,9 | 1 | 65,9 | 5 |
| soja | Itaberá (SP) | 42.400 | 16,7 | 2 | 60 | 10 |
| soja | Buri (SP) | 34.809 | 13,7 | 3 | 60,7 | 8 |
| soja | Itapetininga (SP) | 26.000 | 10,2 | 4 | 68,7 | 2 |
| soja | Capão Bonito (SP) | 25.800 | 10,2 | 5 | 76,3 | 1 |
| soja | Itararé (SP) | 21.600 | 8,5 | 6 | 63,5 | 6 |
| soja | Taquarivaí (SP) | 11.840 | 4,7 | 7 | 60,5 | 9 |
| soja | Guapiara (SP) | 5.400 | 2,1 | 8 | 66,1 | 4 |
| soja | Riversul (SP) | 4.960 | 2 | 9 | 56,8 | 11 |
| soja | Ribeirão Branco (SP) | 2.120 | 0,8 | 10 | 62,4 | 7 |
| soja | Nova Campina (SP) | 230 | 0,1 | 11 | 66,5 | 3 |
| trigo | Itapeva (SP) | 31.400 | 32,8 | 1 | 58,3 | 1 |
| trigo | Itaberá (SP) | 25.000 | 26,1 | 2 | 48,9 | 4 |
| trigo | Buri (SP) | 9.840 | 10,3 | 3 | 35 | 10 |
| trigo | Itararé (SP) | 9.080 | 9,5 | 4 | 49,8 | 2 |
| trigo | Capão Bonito (SP) | 8.400 | 8,8 | 5 | 49,7 | 3 |
| trigo | Itapetininga (SP) | 4.800 | 5 | 6 | 44,8 | 5 |
| trigo | Taquarivaí (SP) | 3.728 | 3,9 | 7 | 39,6 | 9 |
| trigo | Guapiara (SP) | 2.000 | 2,1 | 8 | 41,7 | 6 |
| trigo | Riversul (SP) | 860 | 0,9 | 9 | 40 | 7 |
| trigo | Ribeirão Branco (SP) | 620 | 0,6 | 10 | 40 | 7 |
| trigo | Nova Campina (SP) | 70 | 0,1 | 11 | 30 | 11 |

## 03_itapeva_vs_estados

**Itapeva produz mais por hectare que SP e PR? A vantagem é estável?**

Consulta: [`sql/analises/03_itapeva_vs_estados.sql`](../sql/analises/03_itapeva_vs_estados.sql)

| cultura | ano | itapeva_mm5 | sp_mm5 | pr_mm5 | vantagem_vs_sp_pct |
|---|---|---|---|---|---|
| milho | 1990 | 40,3 | 44,1 | 39,9 | -9 |
| milho | 2000 | 77,7 | 52 | 56 | 50 |
| milho | 2010 | 118,7 | 78,9 | 84,3 | 50 |
| milho | 2015 | 120,1 | 86,2 | 97,2 | 39 |
| milho | 2020 | 127,5 | 92,1 | 96,9 | 38 |
| milho | 2025 | 121,4 | 93,4 | 91,3 | 30 |
| soja | 1990 | 28,8 | 32,8 | 33,7 | -12 |
| soja | 2000 | 40 | 38,5 | 43,8 | 4 |
| soja | 2010 | 54,9 | 44,7 | 45,9 | 23 |
| soja | 2015 | 54,3 | 46,9 | 51,5 | 16 |
| soja | 2020 | 67,2 | 56,3 | 57,1 | 19 |
| soja | 2025 | 65,9 | 56,1 | 55 | 17 |
| trigo | 1990 | 21,8 | 25,7 | 27,2 | -16 |
| trigo | 2000 | 26,9 | 28,1 | 29,8 | -4 |
| trigo | 2010 | 37,2 | 35,5 | 38,5 | 5 |
| trigo | 2015 | 44,3 | 43,5 | 41,8 | 2 |
| trigo | 2020 | 55,6 | 52 | 44,5 | 7 |
| trigo | 2025 | 58,3 | 50 | 46,9 | 17 |

## 04_crescimento_area

**onde e quanto a soja, o milho e o trigo cresceram em área desde 2000?**

Consulta: [`sql/analises/04_crescimento_area.sql`](../sql/analises/04_crescimento_area.sql)

| cultura | nome_local | area_2000_ha | area_2025_ha | cagr_pct_aa |
|---|---|---|---|---|
| milho | Itapeva (SP) | 26000 | 27500 | 0,2 |
| milho | Buri (SP) | 2350 | 23500 | 9,6 |
| milho | Itaberá (SP) | <NA> | 22000 | – |
| milho | Capão Bonito (SP) | 10200 | 13500 | 1,1 |
| milho | Itapetininga (SP) | 15000 | 11000 | -1,2 |
| milho | Ribeirão Branco (SP) | 500 | 9500 | 12,5 |
| milho | Itararé (SP) | 15500 | 7300 | -3 |
| milho | Taquarivaí (SP) | 1700 | 6400 | 5,4 |
| milho | Guapiara (SP) | 2000 | 5500 | 4,1 |
| milho | Riversul (SP) | 2400 | 1300 | -2,4 |
| soja | Itapeva (SP) | 4000 | 82000 | 12,8 |
| soja | Itaberá (SP) | <NA> | 48000 | – |
| soja | Buri (SP) | 500 | 43000 | 19,5 |
| soja | Capão Bonito (SP) | 0 | 30000 | – |
| soja | Itapetininga (SP) | 800 | 28500 | 15,4 |
| soja | Itararé (SP) | 1500 | 22000 | 11,3 |
| soja | Taquarivaí (SP) | 2800 | 12000 | 6 |
| soja | Riversul (SP) | 0 | 5500 | – |
| soja | Guapiara (SP) | 0 | 4500 | – |
| soja | Ribeirão Branco (SP) | 0 | 2500 | – |
| trigo | Itapeva (SP) | 3000 | 28000 | 9,3 |
| trigo | Itaberá (SP) | <NA> | 25000 | – |
| trigo | Buri (SP) | 240 | 16000 | 18,3 |
| trigo | Capão Bonito (SP) | 200 | 10000 | 16,9 |
| trigo | Itararé (SP) | 1500 | 8000 | 6,9 |
| trigo | Itapetininga (SP) | 800 | 5000 | 7,6 |
| trigo | Taquarivaí (SP) | 0 | 3600 | – |
| trigo | Guapiara (SP) | 0 | 1000 | – |
| trigo | Riversul (SP) | 0 | 1000 | – |

## 05_anos_de_quebra

**quais safras quebraram em Itapeva e o que o clima mostra na fase crítica?**

Consulta: [`sql/analises/05_anos_de_quebra.sql`](../sql/analises/05_anos_de_quebra.sql)

| cultura | ano | sc_ha | desvio_pct | chuva_flor_mm | balanco_flor_mm | veranico_max_dias | dias_calor_flor | tmin_ciclo_c | chuva_colheita_mm |
|---|---|---|---|---|---|---|---|---|---|
| milho | 1994 | 36 | -28 | 153 | -9 | 4 | 2 | 9,3 | 210 |
| milho | 2011 | 38,8 | -67 | 259 | 89 | 7 | 1 | 10 | 130 |
| soja | 1983 | 15,2 | -29 | 260 | – | 2 | 0 | 10,6 | 263 |
| soja | 1993 | 25 | -29 | 264 | 124 | 5 | 4 | 10,4 | 165 |
| soja | 2011 | 33,3 | -39 | 288 | 141 | 14 | 3 | 10 | 128 |
| soja | 2024 | 49,2 | -28 | 95 | -45 | 9 | 13 | 10,5 | 103 |
| trigo | 1984 | 10 | -47 | 108 | -2 | 11 | 0 | 1,2 | 109 |
| trigo | 1990 | 16,8 | -28 | 247 | 142 | 19 | 0 | -0,1 | 166 |
| trigo | 1994 | 16,7 | -21 | 29 | -117 | 36 | 3 | -1,7 | 191 |
| trigo | 1996 | 16,7 | -24 | 56 | -74 | 14 | 0 | 4,1 | 218 |
| trigo | 2000 | 8 | -75 | 134 | 18 | 9 | 0 | -1,5 | 158 |
| trigo | 2009 | 25 | -45 | 157 | 42 | 14 | 0 | 3,8 | 285 |
| trigo | 2018 | 45,3 | -25 | 111 | -8 | 14 | 0 | 4,7 | 153 |
| trigo | 2019 | 46,7 | -21 | 16 | -123 | 33 | 0 | 1,3 | 124 |
| trigo | 2020 | 45 | -23 | 92 | -37 | 21 | 0 | 4,6 | 100 |

## 06_geada_por_mes

**em que meses há risco de geada em Itapeva e com que frequência?**

Consulta: [`sql/analises/06_geada_por_mes.sql`](../sql/analises/06_geada_por_mes.sql)

| mes | dias_tmin_le3 | dias_tmin_le1 | media_dias_por_ano | pct_anos_com_evento | tmin_absoluta_c |
|---|---|---|---|---|---|
| 5 | 0 | 0 | 0 | 0 | 3,7 |
| 6 | 5 | 0 | 0,24 | 19 | 1,4 |
| 7 | 6 | 2 | 0,29 | 14 | 0,1 |
| 8 | 2 | 0 | 0,1 | 10 | 2,5 |
| 9 | 0 | 0 | 0 | 0 | 3,9 |

## 07_veranicos_soja

**com que frequência a soja de Itapeva enfrenta veranico no florescimento/enchimento?**

Consulta: [`sql/analises/07_veranicos_soja.sql`](../sql/analises/07_veranicos_soja.sql)

| safra | veranico_flor_dias | veranico_ench_dias | chuva_flor_ench_mm | balanco_mm | classificacao |
|---|---|---|---|---|---|
| 2006/07 | 5 | 10 | 434 | 134 | moderado |
| 2007/08 | 7 | 6 | 472 | 176 | - |
| 2008/09 | 4 | 7 | 432 | 145 | - |
| 2009/10 | 2 | 9 | 500 | 201 | - |
| 2010/11 | 4 | 14 | 409 | 104 | moderado |
| 2011/12 | 4 | 8 | 349 | 7 | - |
| 2012/13 | 6 | 7 | 387 | 82 | - |
| 2013/14 | 9 | 5 | 259 | -98 | - |
| 2014/15 | 11 | 4 | 467 | 143 | moderado |
| 2015/16 | 14 | 6 | 512 | 216 | moderado |
| 2016/17 | 3 | 6 | 431 | 134 | - |
| 2017/18 | 4 | 7 | 304 | 16 | - |
| 2018/19 | 11 | 5 | 364 | 40 | moderado |
| 2019/20 | 6 | 12 | 247 | -29 | moderado |
| 2020/21 | 7 | 6 | 359 | 90 | - |
| 2021/22 | 6 | 10 | 265 | -62 | moderado |
| 2022/23 | 6 | 3 | 459 | 217 | - |
| 2023/24 | 8 | 9 | 221 | -83 | - |
| 2024/25 | 5 | 8 | 410 | 99 | - |
| 2025/26 | 7 | 8 | 220 | -86 | - |

## 08_tendencia_climatica

**o clima de Itapeva mudou desde os anos 1980?**

Consulta: [`sql/analises/08_tendencia_climatica.sql`](../sql/analises/08_tendencia_climatica.sql)

| decada | safras | chuva_verao_mm | tmax_verao_c | dias_ge32_verao | tmin_inverno_c | dias_le3_inverno |
|---|---|---|---|---|---|---|
| 1980s | 9 | 948 | 27,3 | 12,1 | 10,5 | 1,2 |
| 1990s | 10 | 1.028 | 27,1 | 9,7 | 10,8 | 1,9 |
| 2000s | 10 | 945 | 27,4 | 10 | 11 | 1,5 |
| 2010s | 10 | 896 | 27,8 | 17,4 | 11,3 | 1 |
| 2020s | 5 | 711 | 29,2 | 39 | 11,3 | 1,6 |

## 09_correlacao_clima_rendimento

**que variável climática, em que fase, mais explica a produtividade na região?**

Consulta: [`sql/analises/09_correlacao_clima_rendimento.sql`](../sql/analises/09_correlacao_clima_rendimento.sql)

| cultura | fase | n | r_chuva | r_balanco | r_veranico | r_calor | r_frio | r_tmed |
|---|---|---|---|---|---|---|---|---|
| milho | semeadura | 342 | -0,11 | -0,12 | 0,04 | 0,03 | 0,12 | 0,01 |
| milho | vegetativo | 342 | 0,14 | 0,15 | -0,07 | -0,1 | – | 0,01 |
| milho | florescimento | 342 | 0,07 | 0,06 | -0,03 | -0,12 | – | -0,08 |
| milho | enchimento | 342 | 0,23 | 0,24 | -0,08 | -0,14 | – | -0,12 |
| milho | colheita | 342 | 0,08 | 0,06 | 0,01 | -0,1 | -0,04 | -0,05 |
| soja | semeadura | 210 | -0,03 | 0,03 | 0,01 | -0,06 | – | -0,07 |
| soja | vegetativo | 210 | 0,11 | 0,13 | -0,15 | -0,11 | – | -0,05 |
| soja | florescimento | 210 | -0,04 | -0,03 | 0,11 | -0,12 | – | -0,09 |
| soja | enchimento | 210 | 0,19 | 0,19 | -0,09 | -0,15 | – | -0,08 |
| soja | colheita | 210 | 0,15 | 0,17 | 0,14 | -0,16 | 0,09 | -0,2 |
| trigo | semeadura | 185 | 0,19 | 0,17 | -0,08 | 0,12 | -0,04 | -0,03 |
| trigo | perfilhamento | 185 | 0,03 | 0,02 | 0,07 | – | -0,09 | 0,08 |
| trigo | florescimento | 185 | -0,16 | -0,17 | 0,2 | -0,12 | -0,15 | -0,03 |
| trigo | enchimento | 185 | 0,07 | 0,06 | 0,03 | -0,08 | -0,01 | -0,08 |
| trigo | colheita | 185 | -0,04 | -0,02 | 0,06 | -0,09 | – | -0,15 |

## 10_janela_plantio_hoje

**o que posso plantar hoje em Itapeva e com qual risco (ZARC vigente)?**

Consulta: [`sql/analises/10_janela_plantio_hoje.sql`](../sql/analises/10_janela_plantio_hoje.sql)

| nome_cultura | manejo | ciclo | solos_indicados_hoje |
|---|---|---|---|
| Feijão | Irrigado | Grupo I | AD1 (baixo, até 20/02); AD2 (baixo, até 20/02); AD3 (baixo, até 20/02); AD4 (baixo, até 20/02); AD5 (baixo, até 20/02); AD6 (baixo, até 20/02) |
| Feijão | Irrigado | Grupo II | AD1 (baixo, até 20/02); AD2 (baixo, até 20/02); AD3 (baixo, até 20/02); AD4 (baixo, até 20/02); AD5 (baixo, até 20/02); AD6 (baixo, até 20/02) |
| Feijão | Sequeiro | Grupo I | AD3 (médio, até 31/10); AD4 (baixo, até 31/12); AD5 (baixo, até 31/12); AD6 (baixo, até 31/12) |
| Feijão | Sequeiro | Grupo II | AD2 (alto, até 31/10); AD3 (baixo, até 31/12); AD4 (baixo, até 31/12); AD5 (baixo, até 31/12); AD6 (baixo, até 31/12) |
| Milho 1ª Safra | Sequeiro | Grupo I | AD1 (médio, até 31/12); AD2 (baixo, até 31/12); AD3 (baixo, até 31/12); AD4 (baixo, até 31/12); AD5 (baixo, até 31/12); AD6 (baixo, até 31/12) |
| Milho 1ª Safra | Sequeiro | Grupo II | AD1 (médio, até 31/12); AD2 (baixo, até 31/12); AD3 (baixo, até 31/12); AD4 (baixo, até 31/12); AD5 (baixo, até 31/12); AD6 (baixo, até 31/12) |
| Milho 1ª Safra | Sequeiro | Grupo III | AD1 (médio, até 20/12); AD2 (baixo, até 10/12); AD3 (baixo, até 31/12); AD4 (baixo, até 31/12); AD5 (baixo, até 31/12); AD6 (baixo, até 31/12) |
| Milho 1ª Safra consorciado com Braquiária | Sequeiro | Grupo I | AD1 (médio, até 31/12); AD2 (baixo, até 31/12); AD3 (baixo, até 31/12); AD4 (baixo, até 31/12); AD5 (baixo, até 31/12); AD6 (baixo, até 31/12) |
| Milho 1ª Safra consorciado com Braquiária | Sequeiro | Grupo II | AD1 (médio, até 31/12); AD2 (baixo, até 31/12); AD3 (baixo, até 31/12); AD4 (baixo, até 31/12); AD5 (baixo, até 31/12); AD6 (baixo, até 31/12) |
| Milho 1ª Safra consorciado com Braquiária | Sequeiro | Grupo III | AD1 (médio, até 20/12); AD2 (baixo, até 10/12); AD3 (baixo, até 31/12); AD4 (baixo, até 31/12); AD5 (baixo, até 31/12); AD6 (baixo, até 31/12) |
| Soja | Sequeiro | Grupo I | AD1 (médio, até 10/11); AD2 (baixo, até 31/12); AD3 (baixo, até 31/12); AD4 (baixo, até 31/12); AD5 (baixo, até 31/12); AD6 (baixo, até 31/12) |
| Soja | Sequeiro | Grupo II | AD1 (médio, até 31/10); AD2 (baixo, até 31/12); AD3 (baixo, até 31/12); AD4 (baixo, até 31/12); AD5 (baixo, até 31/12); AD6 (baixo, até 31/12) |
| Soja | Sequeiro | Grupo III | AD1 (baixo, até 10/12); AD2 (baixo, até 20/12); AD3 (baixo, até 31/12); AD4 (baixo, até 31/12); AD5 (baixo, até 31/12); AD6 (baixo, até 31/12) |
| Sorgo Granífero | Sequeiro | Grupo I | Arenoso (baixo, até 20/12); Textura média (baixo, até 20/12); Argiloso (baixo, até 20/12) |
| Sorgo Granífero | Sequeiro | Grupo II | Arenoso (baixo, até 20/12); Textura média (baixo, até 20/12); Argiloso (baixo, até 20/12) |
| Sorgo Granífero | Sequeiro | Grupo III | Arenoso (baixo, até 20/12); Textura média (baixo, até 20/12); Argiloso (baixo, até 20/12) |

## 11_calibracao_nasa_a714

**quanto a NASA POWER erra em relação à estação de Itapeva, mês a mês?**

Consulta: [`sql/analises/11_calibracao_nasa_a714.sql`](../sql/analises/11_calibracao_nasa_a714.sql)

| mes | dias_pareados | vies_tmin_c | vies_tmax_c | corr_tmin | corr_chuva_diaria | razao_chuva |
|---|---|---|---|---|---|---|
| 1 | 575 | 0,28 | 0,38 | 0,85 | 0,61 | 1,04 |
| 2 | 524 | 0,34 | 0,71 | 0,82 | 0,51 | 1,02 |
| 3 | 529 | 0,41 | 0,83 | 0,84 | 0,48 | 0,89 |
| 4 | 477 | 0,43 | 0,51 | 0,91 | 0,75 | 0,95 |
| 5 | 490 | 0,52 | 0 | 0,91 | 0,8 | 0,94 |
| 6 | 593 | 0,82 | 0,34 | 0,89 | 0,8 | 1,02 |
| 7 | 603 | 0,83 | 0,41 | 0,86 | 0,72 | 0,91 |
| 8 | 627 | 0,83 | -0,11 | 0,85 | 0,79 | 0,83 |
| 9 | 623 | 0,84 | -0,89 | 0,87 | 0,68 | 0,97 |
| 10 | 556 | 0,81 | -0,98 | 0,87 | 0,71 | 0,98 |
| 11 | 571 | 0,68 | -0,4 | 0,93 | 0,55 | 1,05 |
| 12 | 577 | 0,48 | -0,31 | 0,88 | 0,58 | 1,1 |

## 12_janelas_pulverizacao

**quando dá para pulverizar nos próximos dias?**

Consulta: [`sql/analises/12_janelas_pulverizacao.sql`](../sql/analises/12_janelas_pulverizacao.sql)

| dia | horas_boas | horarios | prob_chuva_max_pct | vento_max_kmh |
|---|---|---|---|---|
| 29/10 Thu | 0 | – | 100 | 9 |
| 30/10 Fri | 2 | 09h 10h | 80 | 14 |
| 31/10 Sat | 1 | 09h | 89 | 15 |
| 01/11 Sun | 6 | 08h 09h 10h 11h 12h 13h | 52 | 12 |
| 02/11 Mon | 3 | 08h 09h 10h | 60 | 13 |
| 03/11 Tue | 2 | 10h 11h | 56 | 12 |
| 04/11 Wed | 2 | 07h 08h | 84 | 14 |
