# Backtest do balanço hídrico (FAO-56 + FAO-33)

_Gerado por `python -m scripts.backtest_balanco` em 23/11/2026 10:49._

Para cada safra, o modelo simula uma lavoura típica (solo AD4, plantio na data típica: soja 25/out, milho verão 01/out, trigo 01/mai) com o **clima real** do ciclo e calcula a produtividade relativa (Ya/Ym). O resultado é comparado com o desvio da produtividade do IBGE em relação à média dos 5 anos anteriores, que tira o ganho tecnológico.

| Série | Cultura | n | r de Pearson | r de Spearman | Quebras IBGE (≤ −15%) | …no quartil pior do modelo |
|---|---|---|---|---|---|---|
| Itapeva (A714 + NASA) | milho | 35 | -0.04 | 0.06 | 2 | 0 |
| Itapeva (A714 + NASA) | soja | 34 | 0.32 | 0.36 | 3 | 2 |
| Itapeva (A714 + NASA) | trigo | 30 | 0.04 | 0.11 | 7 | 2 |
| 11 municípios (NASA) | milho | 334 | 0.21 | 0.26 | 36 | 13 |
| 11 municípios (NASA) | soja | 209 | 0.11 | 0.12 | 21 | 10 |
| 11 municípios (NASA) | trigo | 182 | 0.01 | 0.01 | 32 | 5 |

Referência da Fase 2: o melhor índice climático isolado tinha |r| ≈ 0,2 com o mesmo desvio.

## Soja em Itapeva, ano a ano

| Ano | Modelo (Ya/Ym) | IBGE (desvio vs 5 anos) |
|---|---|---|
| 1991 | 67% | +13% |
| 1992 | 60% | -12% |
| 1993 | 66% | -29% |
| 1994 | 95% | -12% |
| 1995 | 100% | +15% |
| 1996 | 87% | -4% |
| 1997 | 100% | +48% |
| 1998 | 98% | +20% |
| 1999 | 98% | +10% |
| 2000 | 78% | +17% |
| 2001 | 96% | +22% |
| 2002 | 100% | +26% |
| 2003 | 96% | +14% |
| 2004 | 98% | -8% |
| 2005 | 91% | -9% |
| 2006 | 85% | +7% |
| 2007 | 99% | +5% |
| 2008 | 99% | +2% |
| 2009 | 72% | +13% |
| 2010 | 96% | +27% |
| 2011 | 95% | -39% |
| 2012 | 47% | +14% |
| 2013 | 93% | +25% |
| 2014 | 26% | +4% |
| 2015 | 57% | +2% |
| 2016 | 88% | +24% |
| 2017 | 88% | +15% |
| 2018 | 85% | +11% |
| 2019 | 46% | -0% |
| 2020 | 71% | -3% |
| 2021 | 93% | -1% |
| 2022 | 60% | +11% |
| 2023 | 99% | +9% |
| 2024 | 32% | -28% |
