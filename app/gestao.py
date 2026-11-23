"""Gravação e consulta dos dados da propriedade (schema fazenda).

Funções puras sobre uma conexão DuckDB, sem Streamlit. São usadas pelas telas de
lançamento, pelo carregador de demonstração e, nas próximas fases, pelo Agrônomo
Digital ("passei 2 L de glifosato no talhão 3 hoje") e pelo formulário do produtor.
"""

from __future__ import annotations

from datetime import date

import duckdb
import pandas as pd

# Rótulos em linguagem de produtor. As chaves são gravadas no banco e são as mesmas do custo CONAB.
CATEGORIAS = {
    "semente": "Semente",
    "fertilizante": "Adubo / corretivo",
    "defensivo": "Defensivo (herbicida, fungicida, inseticida)",
    "maquinas": "Máquinas e combustível",
    "mao_obra": "Mão de obra",
    "servicos": "Serviço terceirizado",
    "arrendamento": "Arrendamento",
    "frete": "Frete",
    "armazenagem": "Armazenagem / secagem",
    "seguro": "Seguro",
    "assistencia_tecnica": "Assistência técnica",
    "juros": "Juros do financiamento",
    "impostos": "Impostos (Funrural etc.)",
    "manutencao": "Manutenção",
    "depreciacao": "Depreciação",
    "outros": "Outros",
}
TIPOS_OPERACAO = {
    "preparo": "Preparo / dessecação",
    "plantio": "Plantio",
    "adubacao": "Adubação",
    "pulverizacao": "Pulverização",
    "colheita": "Colheita",
    "transporte": "Transporte",
    "outro": "Outro",
}
TIPOS_OCORRENCIA = {
    "praga": "Praga", "doenca": "Doença", "daninha": "Planta daninha", "geada": "Geada",
    "granizo": "Granizo", "seca": "Seca / veranico", "excesso_chuva": "Excesso de chuva", "outro": "Outro",
}
CULTURAS = {"soja": "Soja", "milho": "Milho", "trigo": "Trigo", "feijao": "Feijão", "aveia": "Aveia",
            "cevada": "Cevada", "sorgo": "Sorgo"}
TEMPORADAS = {"verao": "Verão (safra)", "safrinha": "Safrinha (2ª safra)", "inverno": "Inverno"}
SOLOS = ["AD1", "AD2", "AD3", "AD4", "AD5", "AD6"]


def safra_de(d: date) -> str:
    """Ano agrícola (julho a junho) de uma data: 15/10/2026 → '2026/27'; 20/04/2026 → '2025/26'."""
    inicio = d.year if d.month >= 7 else d.year - 1
    return f"{inicio}/{str(inicio + 1)[-2:]}"


def _inserir(con: duckdb.DuckDBPyConnection, tabela: str, campos: dict) -> int:
    campos = {k: v for k, v in campos.items() if v is not None}
    colunas = ", ".join(campos)
    marcadores = ", ".join("?" for _ in campos)
    return con.execute(
        f"INSERT INTO fazenda.{tabela} ({colunas}) VALUES ({marcadores}) RETURNING id", list(campos.values())
    ).fetchone()[0]


def criar_propriedade(con, nome: str, lat: float | None = None, lon: float | None = None,
                      municipio_ibge: int = 3522406, demo: bool = False) -> int:
    return _inserir(con, "propriedade", dict(nome=nome, lat=lat, lon=lon, municipio_ibge=municipio_ibge, demo=demo))


def criar_talhao(con, propriedade_id: int, nome: str, area_ha: float, solo_ad: str | None = None,
                 observacao: str | None = None) -> int:
    if solo_ad is not None and solo_ad not in SOLOS:
        raise ValueError(f"Solo inválido: {solo_ad}")
    return _inserir(con, "talhao", dict(propriedade_id=propriedade_id, nome=nome, area_ha=area_ha,
                                        solo_ad=solo_ad, observacao=observacao))


def criar_plantio(con, talhao_id: int, cultura: str, temporada: str, data_plantio: date | None = None,
                  safra: str | None = None, cultivar: str | None = None, grupo_ciclo: str | None = None,
                  area_ha: float | None = None, produtividade_meta_sc_ha: float | None = None,
                  populacao_plantas_ha: float | None = None, espacamento_cm: float | None = None,
                  status: str | None = None, observacao: str | None = None) -> int:
    if cultura not in CULTURAS:
        raise ValueError(f"Cultura inválida: {cultura}")
    if safra is None:
        if data_plantio is None:
            raise ValueError("Informe a safra ou a data de plantio.")
        safra = safra_de(data_plantio)
    if status is None:
        status = "plantado" if data_plantio and data_plantio <= date.today() else "planejado"
    return _inserir(con, "plantio", dict(
        talhao_id=talhao_id, safra=safra, temporada=temporada, cultura=cultura, cultivar=cultivar,
        grupo_ciclo=grupo_ciclo, data_plantio=data_plantio, area_ha=area_ha,
        populacao_plantas_ha=populacao_plantas_ha, espacamento_cm=espacamento_cm,
        produtividade_meta_sc_ha=produtividade_meta_sc_ha, status=status, observacao=observacao))


def registrar_operacao(con, plantio_id: int, data: date, tipo: str, produto: str | None = None,
                       dose: float | None = None, unidade: str | None = None, area_ha: float | None = None,
                       custo_total: float | None = None, categoria_custo: str | None = None,
                       observacao: str | None = None) -> int:
    if tipo not in TIPOS_OPERACAO:
        raise ValueError(f"Tipo de operação inválido: {tipo}")
    if custo_total and categoria_custo not in CATEGORIAS:
        raise ValueError("Informe a categoria do custo.")
    oid = _inserir(con, "operacao", dict(plantio_id=plantio_id, data=data, tipo=tipo, produto=produto, dose=dose,
                                          unidade=unidade, area_ha=area_ha, custo_total=custo_total,
                                          categoria_custo=categoria_custo, observacao=observacao))
    if tipo == "plantio":
        con.execute("UPDATE fazenda.plantio SET status = 'plantado', data_plantio = coalesce(data_plantio, ?) "
                    "WHERE id = ? AND status = 'planejado'", [data, plantio_id])
    return oid


def registrar_custo(con, propriedade_id: int, data: date, categoria: str, valor: float,
                    descricao: str | None = None, plantio_id: int | None = None, safra: str | None = None) -> int:
    if categoria not in CATEGORIAS:
        raise ValueError(f"Categoria inválida: {categoria}")
    return _inserir(con, "custo", dict(propriedade_id=propriedade_id, plantio_id=plantio_id,
                                       safra=safra or safra_de(data), data=data, categoria=categoria,
                                       descricao=descricao, valor=valor))


def registrar_colheita(con, plantio_id: int, data: date, sacas: float, area_colhida_ha: float | None = None,
                       umidade_pct: float | None = None, impureza_pct: float | None = None,
                       observacao: str | None = None, finalizar: bool = True) -> int:
    cid = _inserir(con, "colheita", dict(plantio_id=plantio_id, data=data, sacas=sacas, area_colhida_ha=area_colhida_ha,
                                          umidade_pct=umidade_pct, impureza_pct=impureza_pct, observacao=observacao))
    if finalizar:
        con.execute("UPDATE fazenda.plantio SET status = 'colhido' WHERE id = ?", [plantio_id])
    return cid


def registrar_venda(con, propriedade_id: int, cultura: str, safra: str, data: date, sacas: float, preco_sc: float,
                    comprador: str | None = None, observacao: str | None = None) -> int:
    return _inserir(con, "venda", dict(propriedade_id=propriedade_id, cultura=cultura, safra=safra, data=data,
                                       sacas=sacas, preco_sc=preco_sc, comprador=comprador, observacao=observacao))


def registrar_ocorrencia(con, plantio_id: int, data: date, tipo: str, severidade: int | None = None,
                         descricao: str | None = None) -> int:
    if tipo not in TIPOS_OCORRENCIA:
        raise ValueError(f"Tipo de ocorrência inválido: {tipo}")
    return _inserir(con, "ocorrencia", dict(plantio_id=plantio_id, data=data, tipo=tipo,
                                            severidade=severidade, descricao=descricao))


def atualizar_preco(con, cultura: str, preco_sc: float, data: date, fonte: str) -> None:
    con.execute("INSERT OR REPLACE INTO fazenda.preco_referencia VALUES (?, ?, ?, ?)", [cultura, preco_sc, data, fonte])


def remover_propriedade(con, propriedade_id: int) -> None:
    """Apaga a propriedade e tudo que pertence a ela (na ordem das chaves estrangeiras)."""
    plantios = "SELECT p.id FROM fazenda.plantio p JOIN fazenda.talhao t ON t.id = p.talhao_id WHERE t.propriedade_id = ?"
    for tabela in ("operacao", "colheita", "ocorrencia"):
        con.execute(f"DELETE FROM fazenda.{tabela} WHERE plantio_id IN ({plantios})", [propriedade_id])
    con.execute("DELETE FROM fazenda.custo WHERE propriedade_id = ?", [propriedade_id])
    con.execute("DELETE FROM fazenda.venda WHERE propriedade_id = ?", [propriedade_id])
    con.execute(f"DELETE FROM fazenda.plantio WHERE id IN ({plantios})", [propriedade_id])
    con.execute("DELETE FROM fazenda.talhao WHERE propriedade_id = ?", [propriedade_id])
    con.execute("DELETE FROM fazenda.propriedade WHERE id = ?", [propriedade_id])


def remover_demonstracao(con) -> int:
    ids = [r[0] for r in con.execute("SELECT id FROM fazenda.propriedade WHERE demo").fetchall()]
    for pid in ids:
        remover_propriedade(con, pid)
    return len(ids)


def resultado(con, propriedade_id: int) -> pd.DataFrame:
    return con.execute("SELECT * FROM fazenda.vw_resultado_plantio WHERE propriedade_id = ? "
                       "ORDER BY safra DESC, temporada, talhao", [propriedade_id]).df()
