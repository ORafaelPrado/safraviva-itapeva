"""Carrega a "Fazenda Exemplo (demonstração)" para mostrar a gestão funcionando.

    python -m scripts.carregar_demo          # recria a demonstração
    python -m scripts.carregar_demo --remover

Tudo aqui é FICTÍCIO, mas ancorado em dados reais da região:
* custo por hectare = distribuição do custo CONAB de referência (analytics.custo_referencia),
  com variação de ±8% por talhão; sem arrendamento (terra própria);
* produtividades coerentes com o clima de cada safra em Itapeva (2025/26 teve balanço
  hídrico negativo no enchimento da soja, conforme docs/insights.md);
* datas de plantio dentro das janelas de risco baixo do ZARC para cada classe de solo.
A propriedade fica com demo = TRUE e some com --remover ou pelo botão no painel.
"""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta

from app import gestao
from core.db import conectar

NOME = "Fazenda Exemplo (demonstração)"
TALHOES = [  # nome, área ha, solo
    ("Chapada", 120, "AD5"),
    ("Sede", 85, "AD4"),
    ("Baixada", 55, "AD3"),
    ("Areião", 40, "AD2"),
]
# Como cada categoria CONAB vira lançamento: (tipo de operação ou None = despesa, dias após o plantio)
DISTRIBUICAO = {
    "semente": [("plantio", 0, 1.0)],
    "fertilizante": [("adubacao", 0, 1.0)],
    "defensivo": [("preparo", -10, 0.25), ("pulverizacao", 30, 0.2), ("pulverizacao", 55, 0.2),
                  ("pulverizacao", 75, 0.2), ("pulverizacao", 95, 0.15)],
    "maquinas": [(None, 0, 0.35), (None, 60, 0.25), (None, 120, 0.4)],
}
PRODUTOS = {"preparo": "Dessecação (glifosato + 2,4-D)", "plantio": "Semente tratada", "adubacao": "Adubo NPK no sulco",
            "pulverizacao": "Fungicida/inseticida"}


def custo_ha(con, cultura: str) -> dict[str, float]:
    linhas = con.execute(
        """SELECT categoria, valor_ha FROM analytics.custo_referencia
           WHERE cultura = ? AND categoria NOT IN ('custo_variavel', 'custo_operacional', 'custo_total',
                                                  'renda_fatores', 'arrendamento')""",
        [cultura],
    ).fetchall()
    if not linhas:
        raise RuntimeError("Sem custo de referência: rode `python -m scripts.rodar_etl --fontes conab` antes.")
    return {cat: val for cat, val in linhas if val}


def lancar_custos(con, propriedade_id: int, plantio_id: int, plantio: date, area: float, cultura: str,
                  rng: random.Random, ate: date) -> None:
    """Gera operações e despesas do plantio a partir do custo CONAB por hectare (só até a data `ate`)."""
    fator = rng.uniform(0.92, 1.08)
    for categoria, valor_ha in custo_ha(con, cultura).items():
        total = valor_ha * area * fator
        for tipo, dias, parte in DISTRIBUICAO.get(categoria, [(None, 110, 1.0)]):
            quando = plantio + timedelta(days=dias)
            if quando > ate:
                continue
            if tipo:
                gestao.registrar_operacao(con, plantio_id, quando, tipo, produto=PRODUTOS.get(tipo), area_ha=area,
                                          custo_total=round(total * parte, 2), categoria_custo=categoria)
            else:
                gestao.registrar_custo(con, propriedade_id, quando, categoria, round(total * parte, 2),
                                       descricao=gestao.CATEGORIAS[categoria], plantio_id=plantio_id)


def carregar(con, hoje: date | None = None) -> int:
    hoje = hoje or date.today()
    rng = random.Random(42)
    gestao.remover_demonstracao(con)
    pid = gestao.criar_propriedade(con, NOME, lat=-23.95, lon=-48.90, demo=True)
    talhoes = {nome: (gestao.criar_talhao(con, pid, nome, area, solo), area, solo) for nome, area, solo in TALHOES}

    # --- Safra 2025/26: soja (verão, colhida) ----------------------------------------------
    soja_2526 = {  # data de plantio dentro do risco baixo do ZARC por solo; produtividade com o veranico de jan/fev-2026
        "Chapada": (date(2025, 10, 10), 58.0), "Sede": (date(2025, 10, 18), 55.0),
        "Baixada": (date(2025, 10, 25), 51.0), "Areião": (date(2025, 11, 8), 42.0),
    }
    sacas_soja = 0.0
    for nome, (plantou, prod) in soja_2526.items():
        tid, area, _ = talhoes[nome]
        p = gestao.criar_plantio(con, tid, "soja", "verao", plantou, cultivar="Grupo II (exemplo)", grupo_ciclo="Grupo II",
                                 produtividade_meta_sc_ha=62, populacao_plantas_ha=280_000, espacamento_cm=45)
        lancar_custos(con, pid, p, plantou, area, "soja", rng, hoje)
        if nome in ("Baixada", "Areião"):
            gestao.registrar_ocorrencia(con, p, date(2026, 1, 28), "seca", 2,
                                        "Veranico no enchimento de grãos (balanço hídrico negativo em jan–fev/2026).")
        colheu = plantou + timedelta(days=rng.randint(122, 130))
        sacas = round(prod * area * rng.uniform(0.98, 1.02))
        gestao.registrar_colheita(con, p, colheu, sacas, area_colhida_ha=area, umidade_pct=13.5, impureza_pct=1.0)
        sacas_soja += sacas
    for quando, parte, preco, comprador in [(date(2026, 3, 20), 0.4, 128.0, "Cooperativa (exemplo)"),
                                            (date(2026, 6, 15), 0.3, 136.0, "Trading (exemplo)"),
                                            (date(2026, 9, 10), 0.3, 147.0, "Cooperativa (exemplo)")]:
        gestao.registrar_venda(con, pid, "soja", "2025/26", quando, round(sacas_soja * parte), preco, comprador)
    gestao.registrar_custo(con, pid, date(2026, 2, 1), "assistencia_tecnica", 9_000, "Agrônomo (rateado)", safra="2025/26")

    # --- Inverno 2026: trigo nos talhões de melhor solo -----------------------------------------
    sacas_trigo = 0.0
    for nome, plantou, prod in [("Chapada", date(2026, 4, 22), 61.0), ("Sede", date(2026, 5, 2), 57.0)]:
        tid, area, _ = talhoes[nome]
        p = gestao.criar_plantio(con, tid, "trigo", "inverno", plantou, cultivar="Trigo pão (exemplo)",
                                 grupo_ciclo="Grupo II", produtividade_meta_sc_ha=58)
        lancar_custos(con, pid, p, plantou, area, "trigo", rng, hoje)
        if nome == "Sede":
            gestao.registrar_ocorrencia(con, p, date(2026, 7, 14), "geada", 1, "Geada leve na baixada do talhão, no perfilhamento.")
        sacas = round(prod * area * rng.uniform(0.98, 1.02))
        gestao.registrar_colheita(con, p, plantou + timedelta(days=rng.randint(140, 150)), sacas, area_colhida_ha=area)
        sacas_trigo += sacas
    gestao.registrar_venda(con, pid, "trigo", "2025/26", date(2026, 10, 20), round(sacas_trigo * 0.6), 78.0, "Moinho (exemplo)")

    # --- Safra 2026/27: soja em andamento ---------------------------------------------------------
    for nome, plantou in [("Chapada", date(2026, 10, 8)), ("Sede", date(2026, 10, 20)),
                          ("Baixada", date(2026, 10, 28)), ("Areião", date(2026, 11, 10))]:
        tid, area, _ = talhoes[nome]
        p = gestao.criar_plantio(con, tid, "soja", "verao", plantou, cultivar="Grupo II (exemplo)",
                                 grupo_ciclo="Grupo II", produtividade_meta_sc_ha=63,
                                 status="plantado" if plantou <= hoje else "planejado")
        lancar_custos(con, pid, p, plantou, area, "soja", rng, hoje)
    return pid


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--remover", action="store_true", help="apaga a fazenda de demonstração")
    args = parser.parse_args()
    with conectar() as con:
        if args.remover:
            print(f"Propriedades de demonstração removidas: {gestao.remover_demonstracao(con)}")
            return
        pid = carregar(con)
        r = gestao.resultado(con, pid)
        print(r[["safra", "temporada", "talhao", "cultura", "status", "area_ha", "custo_ha",
                 "produtividade_sc_ha", "preco_sc", "margem", "ponto_equilibrio_sc_ha"]].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
