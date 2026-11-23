"""Estilo único dos gráficos do SafraViva (matplotlib).

Paleta de referência validada da skill de dataviz (modo claro):
  * categórica em ordem fixa: Itapeva = slot 1 (azul), SP = slot 2 (laranja), PR = slot 3 (verde-água).
    Até 3 séries por gráfico, que é o limite validado para "todos os pares".
  * divergente azul ↔ vermelho com meio cinza, para anomalias (acima/abaixo do normal).
  * texto sempre em tinta neutra, nunca na cor da série.
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

SUPERFICIE = "#fcfcfb"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
GRADE = "#e4e3df"

SERIE = ["#2a78d6", "#eb6834", "#1baf7a"]  # slots 1–3
CORES_LOCAL = {"Itapeva": SERIE[0], "SP": SERIE[1], "PR": SERIE[2]}

AZUL_SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DIVERGENTE = LinearSegmentedColormap.from_list(
    "diverg_azul_vermelho", ["#184f95", "#6da7ec", "#f0efec", "#f08a85", "#b8312f"]
)
CRITICO = "#d03b3b"  # status "critical": só com rótulo


def aplicar_estilo() -> None:
    mpl.rcParams.update({
        "figure.facecolor": SUPERFICIE,
        "axes.facecolor": SUPERFICIE,
        "savefig.facecolor": SUPERFICIE,
        "figure.dpi": 110,
        "font.size": 10,
        "text.color": TEXTO,
        "axes.labelcolor": TEXTO_2,
        "axes.edgecolor": GRADE,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.axisbelow": True,
        "grid.color": GRADE,
        "grid.linewidth": 0.6,
        "xtick.color": TEXTO_2,
        "ytick.color": TEXTO_2,
        "lines.linewidth": 2,
        "legend.frameon": False,
        "legend.labelcolor": TEXTO,
    })


def subtitulo(ax, texto: str) -> None:
    """Linha de contexto (fonte, unidade) logo abaixo do título."""
    ax.text(0, 1.01, texto, transform=ax.transAxes, fontsize=9, color=TEXTO_2, va="bottom")


def rotulo_final(ax, x, y, texto: str, cor: str) -> None:
    """Rótulo direto no fim da linha: marcador na cor da série, texto em tinta neutra."""
    ax.plot([x], [y], "o", color=cor, markersize=5, markeredgecolor=SUPERFICIE, markeredgewidth=2)
    ax.annotate(texto, (x, y), xytext=(6, 0), textcoords="offset points", va="center", fontsize=9, color=TEXTO)


def rotulos_finais(ax, itens: list[tuple[float, float, str, str]], folga: float = 0.05) -> None:
    """Vários rótulos de fim de linha sem colisão: empurra na vertical até a folga mínima.

    itens = [(x, y, texto, cor), ...]; folga em fração da altura do eixo.
    """
    y0, y1 = ax.get_ylim()
    minimo = folga * (y1 - y0)
    ordenados = sorted(itens, key=lambda i: i[1])
    posicoes = []
    for _, y, _, _ in ordenados:
        posicoes.append(max(y, posicoes[-1] + minimo) if posicoes else y)
    for (x, y, texto, cor), y_texto in zip(ordenados, posicoes):
        ax.plot([x], [y], "o", color=cor, markersize=5, markeredgecolor=SUPERFICIE, markeredgewidth=2)
        ax.annotate(texto, (x, y_texto), xytext=(8, 0), textcoords="offset points", va="center", fontsize=9, color=TEXTO)


def nova_figura(largura: float = 9, altura: float = 4.2):
    aplicar_estilo()
    return plt.subplots(figsize=(largura, altura))
