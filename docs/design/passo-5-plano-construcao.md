# Passo 5 — Plano de construção

> **Base:** [plano-mestre](plano-mestre-safraviva.md) · [passo 2](passo-2-secao-principal.md) · [passo 3](passo-3-movimento.md) · [passo 4](passo-4-texto.md).
> **Adaptação:** o app já existe e está no ar, então este passo **organiza o que foi construído**, mede o resultado e lista o que falta, em vez de planejar do zero. O termo "front-end" aqui é o Streamlit com uma camada própria de estilo.

## 1. Componentes que se repetem

Todos ficam em `app/ui.py`, com o estilo em `app/estilo.css`. Uma tela nunca cria HTML próprio: ela usa estes componentes.

| Componente | Função em `ui.py` | Onde aparece | Regra |
|---|---|---|---|
| Título da tela | `titulo(texto, subtitulo)` | 11 telas | Título = pergunta da tela; subtítulo em uma linha |
| Veredito do dia | `heroi(...)` | Hoje na lavoura | Selo (ícone + palavra) + frase (H1) + apoio + 3 números |
| Cartão de alerta | `cartao(alerta)` | Hoje, Alertas, Plantio | Barra colorida + ícone + palavra (nunca só a cor) |
| Fonte do dado | `fonte(texto)` | Todas as telas com número | Sempre logo abaixo do dado |
| Indicador ao vivo | `ao_vivo(texto)` | Cotações | Ponto que pulsa; o número não se mexe |
| Aviso de demonstração | `aviso_demo(demo)` | Telas da fazenda | Some quando entrarem os dados reais |
| Tela de entrada | `tela_entrada()` | Antes da senha | Marca, promessa e fatos verificáveis |
| Gráfico | `layout(fig)` + `mostrar(fig)` + `rotulos_finais` | 8 telas | Paleta validada para daltonismo, sem animação, rótulo no fim da linha |
| Números BR | `num`, `reais` | Todas | 1.234,5 · R$ 163,79 |

## 2. Conteúdo dinâmico (de onde vem e com que frequência muda)

| Conteúdo | Fonte | Atualiza | Cache no app |
|---|---|---|---|
| Previsão e veredito | Open-Meteo → `raw.previsao_*` | Rotina das 6h + ao abrir, se tiver mais de 6 h | 5 min |
| Cotações bolsa/dólar | Yahoo/CBOT → `raw.cotacao_ultima` | Ao abrir, se tiver mais de 15 min; tela se atualiza a cada 5 min | 1 min |
| CEPEA e PTAX | CEPEA, BCB | 1×/dia (rotina) | 1 min |
| Alertas | regras sobre previsão e lavouras | Rotina + a cada atualização da previsão | 1 min |
| Dados da fazenda | lançamentos do produtor | Na hora em que ele salva | 1 min (limpo ao salvar) |
| Histórico (IBGE, clima, ZARC) | cargas do ETL | Raramente | 6 h |
| Uso do app | `uso.evento` | A cada página vista/clique | — |

## 3. Metas de velocidade no celular (medidas)

| Situação | Meta | Medido (25/11) | Observação |
|---|---|---|---|
| Veredito na tela, app já aberto ("quente") | < 2 s | **0,9 s** | Local, banco na nuvem (MotherDuck) |
| Veredito logo após o servidor reiniciar | < 10 s | **7,0 s** | Inclui a 1ª conexão ao MotherDuck (2–4 s) |
| Cada consulta ao banco | < 0,3 s | **0,15–0,18 s** | 10 consultas da tela Hoje |
| App "acordando" no Streamlit Cloud | — | **não medido** `[CONFIRMAR]` | O plano gratuito hiberna o app sem uso; acordar pode levar de 10 s a mais de 1 min e exige um clique. É a maior espera real do seu pai |
| Movimento | < 0,4 s, só opacity/transform | 0,22 s + 0,16 s | Passo 3 |

> Uma medição local deu **81 s** na primeira abertura com o painel do navegador oculto (o navegador desacelera aba escondida). Não vale como número real, mas mostra que a primeira abertura é o ponto fraco. Vai para o passo 7 (avisar o pai de que a primeira abertura do dia demora) e para a lista final (opções para manter o app acordado).

## 4. Acessibilidade (medida no navegador, celular 375 px)

| Item | Antes | Depois |
|---|---|---|
| Contraste de todo texto visível (Hoje, Lançar) | ok (≥ 4,5:1) | ok |
| Texto de exemplo nos campos | **4,2:1** ❌ | 6,1:1 ✅ |
| Idioma da página | `en` ❌ (leitor de tela lia em inglês) | `pt-BR` ✅ |
| Título principal (H1) na Hoje | **não havia** ❌ | o veredito é o H1 ✅ |
| Menu de páginas (celular) | 28 px de altura ❌ | 44 px ✅ |
| Abas de Lançar | 40 px ❌ | 44 px ✅ |
| Botão de menu e de abrir o menu | 28 px ❌ | 44 px ✅ |
| Botões principais | 44 px | 44 px ✅ |
| Imagens sem texto alternativo | 0 | 0 ✅ |
| Botões/links sem nome | 0 | 0 ✅ |
| Foco pelo teclado | contorno verde 3 px (passo 3) | ✅ |
| Reduzir movimento | respeitado (passo 3) | ✅ |
| Rolagem lateral 320–1920 px | nenhuma | nenhuma ✅ |

**Limites do Streamlit (registrados, sem conserto simples):**
- O campo de **data** não liga o rótulo ao campo para leitores de tela.
- Os botões da barra de ferramentas das tabelas (24 px) e os ícones de ajuda "?" (16 px) são menores que 44 px. Só aparecem no computador ou ao tocar na tabela.
- O texto interno "Choose an option" das listas de escolha fica em inglês (só o leitor de tela o encontra).

Ferramenta: as medições foram feitas com um script próprio dentro da página (contraste WCAG, tamanho de alvo, H1, nomes, idioma), sem baixar biblioteca externa.

## 5. Estrutura de pastas (o que é visual)

```
.streamlit/config.toml     tema: cores, fonte Inter, cantos (passo 1)
app/
  main.py                  senha → logo → menu no topo → página → medição
  ui.py                    componentes (seção 1)
  estilo.css               tokens, movimento, celular, acessibilidade
  eventos.py               medição de uso (uso.evento)
  alertas.py               regras, inclusive veredito_do_dia (sem Streamlit, testável)
  static/logo.svg, icone.svg
  paginas/                 uma tela por arquivo; só chama ui.* e dados.*
docs/design/               os 7 documentos deste processo
```

## 6. Pontos de quebra (responsivo)

| Largura | O que muda |
|---|---|
| ≤ 640 px (celular) | Margens de 16 px; os 3 números do dia empilham; colunas viram uma embaixo da outra (padrão do Streamlit); títulos menores |
| 641–~1000 px | Menu no topo pode recolher; layout centralizado |
| ≥ ~1000 px (computador) | Menu no topo completo; conteúdo centralizado em ~730 px (leitura confortável) |

Conferido em 320, 375, 800 e 1920 px, sem rolagem lateral.

## 7. Imagens e fontes

- **Imagens:** o app não usa foto. Logo e ícone em SVG (menos de 1 KB cada); na tela de entrada o logo vai embutido na página (zero requisição extra).
- **Fonte:** Inter via Google Fonts com `display=swap` (o texto aparece na hora com a fonte do sistema e troca quando a Inter chega). Quatro pesos (400, 500, 600, 700). Se o 3G pesar, dá para cortar o 500 `[decidir no passo 7]`.
- **Ícones:** Material Symbols do próprio Streamlit (já carregados por ele).
- **Gráficos:** Plotly sem barra de ferramentas e sem animação.

## 8. Checklist antes de chamar o seu pai

- [x] Testes automáticos passando (97) no computador e no GitHub
- [x] Senha protegendo todas as páginas, inclusive links diretos
- [x] Contraste, alvos de toque, idioma e H1 medidos (seção 4)
- [x] Sem rolagem lateral de 320 a 1920 px
- [x] Medição de uso gravando; registros dos meus testes apagados
- [x] Nenhum dado real da fazenda no repositório público
- [ ] **Abrir no celular dele**, no sol, com a senha `[👤 você]`
- [ ] **Primeira abertura do dia** no Streamlit Cloud: cronometrar uma vez `[👤 você]`
- [ ] Trocar a fazenda de demonstração pelos dados reais (formulário do produtor, fim do projeto)
- [ ] Alertas no WhatsApp (depois, como combinado)

---

## O que eu preciso de você
1. **Cronometre uma vez** a primeira abertura do dia do link no celular (de manhã, antes de qualquer outro acesso). Isso define se vale a pena buscar uma forma de manter o app acordado. `[PREENCHER: segundos]`
2. Se puder, abra no celular do seu pai e veja se os botões e o menu estão fáceis de tocar.
