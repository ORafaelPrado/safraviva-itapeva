# Passo 3: como o app se mexe

> **Base:** [plano-mestre-safraviva.md](plano-mestre-safraviva.md) (seção 9) e [passo-2-secao-principal.md](passo-2-secao-principal.md). O movimento serve ao veredito do dia e não compete com ele.

## 1. Personalidade e regra geral
O SafraViva é um **agrônomo calmo**: fala pouco e vai direto ao ponto. O movimento segue o mesmo jeito.
- **Curto:** entre 120 e 220 ms. Nada que o produtor precise esperar acabar.
- **Discreto:** só opacidade e um deslocamento de até 6 px. Nada de girar, quicar ou fazer zoom.
- **Com motivo:** algo só se mexe para **mostrar que mudou** ou para **responder ao toque**.
- **Sem JavaScript:** tudo em CSS (`app/estilo.css`), só com `opacity` e `transform`, que o celular desenha sem travar.

## 2. Onde o movimento agrega valor
| Momento | O que acontece | Por quê |
|---|---|---|
| Abrir "Hoje na lavoura" | O bloco do veredito aparece subindo 6 px (220 ms); os três números entram logo depois, um a um (atraso de 40 ms entre eles, menos de 0,4 s no total) | Guia o olho: primeiro a frase, depois os números |
| Tela de entrada | Logo, frase e campo de senha aparecem juntos, de uma vez (220 ms) | A primeira impressão parece pronta, não "piscando" |
| Tocar num botão | O botão escurece um pouco e desce 1 px enquanto está pressionado | Confirma o toque, o que importa com dedo sujo ou luva |
| Passar o mouse num botão ou link (computador) | Cor muda em 120 ms | Mostra o que é clicável |
| Navegar pelo teclado | Contorno verde de 3 px em volta do item em foco | Acessibilidade: sempre se sabe onde está |
| Cotações ao vivo | Um ponto verde "ao vivo" pulsa devagar (opacidade, a cada 2 s) ao lado da hora da última atualização | Mostra que o número está vivo sem mexer no número |

## 3. Onde o movimento só atrapalha (e não entra)
- **Número de decisão** (preço, chuva, temperatura, margem): **nunca** tem contador animado. O produtor precisa ler o valor certo na hora, e não "R$ 12... 87... 163".
- **Gráficos:** sem animação de entrada e sem transição na troca de filtro. A leitura vem antes do efeito.
- **Cartões de alerta:** não piscam nem tremem. A gravidade aparece pela cor, pelo ícone e pela palavra.
- **Rolagem:** sem parallax e sem nada aparecendo durante a rolagem. No celular, isso pesa e esconde conteúdo de quem rola rápido.
- **Atualização automática** (cotações a cada 5 min): o conteúdo troca **sem animação**, para não chamar atenção a cada 5 minutos.
- **Itens que não são clicáveis** (cartões, números) **não reagem ao mouse**: se reagisse, pareceria botão.

## 4. Estados de toque e clique
| Elemento | Repouso | Mouse em cima | Pressionado | Foco (teclado) | Desabilitado |
|---|---|---|---|---|---|
| Botão primário (verde) | `#1E6B3C` | `#18572F` | `#134626` e desce 1 px | contorno 3 px `#1E6B3C`, afastado 2 px | padrão do Streamlit (cinza) |
| Botão secundário (branco) | borda `#E4E1D8` | borda e texto verdes | fundo `#F1EEE6` e desce 1 px | contorno 3 px verde | padrão |
| Link de página | texto verde | sublinhado | — | contorno 3 px verde | — |

O contraste do branco sobre o verde do botão nos três tons: 6,5:1, 8,6:1 e 10,9:1 (todos ≥ 4,5:1).

## 5. Transição entre páginas
O Streamlit troca a página inteira. Só o **bloco principal da página "Hoje"** e a **tela de entrada** têm entrada suave. As outras páginas aparecem direto, porque quem troca de página no menu quer o conteúdo, não um efeito. Quando o app está buscando dados, o indicador "Running" do próprio Streamlit continua sendo o aviso de espera.

## 6. Elementos que nunca se mexem
1. Qualquer número de decisão: preço, chuva, temperatura, custo, margem ou produtividade.
2. O menu do topo e o logo.
3. Gráficos e tabelas.
4. Cartões de alerta.
5. Textos legais e de fonte ("Isto não é recomendação…", "Fonte: …").

## 7. Limite de desempenho no celular
- Só se animam `opacity` e `transform`. Nada que force o navegador a recalcular a página.
- No máximo 4 elementos animados ao mesmo tempo, e toda animação termina em menos de 0,4 s.
- Nenhuma biblioteca de animação e nenhum JavaScript extra.
- O que realmente pesa é o servidor: o Streamlit Community Cloud **hiberna** o app quando ninguém usa, e a primeira abertura do dia pode levar de 10 a 30 s. Isso não se resolve com movimento. Fica registrado para o passo 5 (velocidade) e o passo 7 (plano de uso).

## 8. Reduzir movimento
Com "reduzir movimento" ligado no celular ou no computador, `@media (prefers-reduced-motion: reduce)` desliga **todas** as animações e transições, inclusive o ponto "ao vivo", que fica parado e aceso. Nada some: tudo aparece de uma vez.

---

## O que eu preciso de você
1. **O ponto "ao vivo" nas cotações:** pulsando devagar está bom, ou prefere parado? `[CONFIRMAR]`
2. Se puder, abra o link no celular do seu pai e veja se a entrada do veredito parece **natural** ou **lenta**. Se parecer lenta, eu corto pela metade.
