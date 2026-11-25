"""Ficha da fazenda: o formulário que o produtor preenche uma vez para trocar a demonstração pelos dados reais.

Funções puras sobre uma conexão DuckDB (sem Streamlit), testadas em tests/test_ficha.py.
A tela fica em app/paginas/ficha.py.

As perguntas usam a linguagem do produtor e são convertidas aqui para o que o sistema usa:
* tipo de terra → água disponível do ZARC (AD2 a AD5);
* precoce / médio / tardio → Grupo I / II / III;
* alqueire paulista → hectare (1 alqueire = 2,42 ha).
"""

from __future__ import annotations

import json
import re
from datetime import date

import duckdb

from app import gestao
from core import config

DDL = config.DIR_SQL / "ddl" / "012_ficha.sql"
ALQUEIRE_HA = 2.42
UNIDADES = {"ha": "Hectare (ha)", "alqueire": "Alqueire paulista (2,42 ha)"}

# rótulo para o produtor → solo do ZARC (None = não sabe; o sistema usa AD4, o mais comum nas chapadas)
TERRAS = {
    "argilosa": ("Argilosa (terra vermelha, segura bem a água)", "AD4"),
    "argilosa_profunda": ("Argilosa profunda (chapada, aguenta seca)", "AD5"),
    "mista": ("Mista (nem areia, nem argila)", "AD3"),
    "arenosa": ("Arenosa (terra fraca, seca rápido)", "AD2"),
    "nao_sei": ("Não sei", None),
}
CICLOS = {
    "nao_sei": ("Não sei", None),
    "precoce": ("Precoce (ciclo curto)", "Grupo I"),
    "medio": ("Médio", "Grupo II"),
    "tardio": ("Tardio (ciclo longo)", "Grupo III"),
}
LAVOURA_AGORA = {"soja": "Soja", "milho": "Milho", "feijao": "Feijão", "nada": "Nada plantado agora / pousio"}


def ler_coordenadas(texto: str | None) -> tuple[float, float] | None:
    """'-23.982, -48.876' (como o Google Maps copia) → (-23.982, -48.876). Vazio → None."""
    if not texto or not texto.strip():
        return None
    numeros = re.findall(r"-?\d+\.\d+", texto)
    if len(numeros) != 2:
        raise ValueError("Coordenadas: copie do Google Maps no formato -23.98, -48.87 (ou deixe em branco).")
    lat, lon = float(numeros[0]), float(numeros[1])
    if not (-34 <= lat <= 6 and -74 <= lon <= -34):
        raise ValueError("Coordenadas fora do Brasil. Confira se copiou os dois números certos.")
    return lat, lon


def area_ha(valor: float | None, unidade: str) -> float | None:
    if valor is None:
        return None
    return round(valor * ALQUEIRE_HA, 2) if unidade == "alqueire" else float(valor)


def validar(r: dict) -> list[str]:
    """Problemas que impedem criar a fazenda (mensagens para o produtor)."""
    erros = []
    if not (r["fazenda"].get("nome") or "").strip():
        erros.append("Falta o **nome da fazenda**.")
    try:
        ler_coordenadas(r["fazenda"].get("coordenadas"))
    except ValueError as e:
        erros.append(str(e))
    preenchidos = [t for t in r["talhoes"] if (t.get("nome") or "").strip() or t.get("area")]
    if not preenchidos:
        erros.append("Preencha pelo menos **um talhão** (nome e área).")
    nomes = []
    for i, t in enumerate(preenchidos, 1):
        nome = (t.get("nome") or "").strip()
        if not nome:
            erros.append(f"Talhão {i}: falta o **nome** (pode ser o apelido: Sede, Chapada, Fundo...).")
        if not t.get("area") or t["area"] <= 0:
            erros.append(f"Talhão {nome or i}: falta a **área**.")
        if nome.lower() in nomes:
            erros.append(f"Há dois talhões chamados **{nome}**; use nomes diferentes.")
        nomes.append(nome.lower())
    return erros


def aplicar(con: duckdb.DuckDBPyConnection, r: dict, hoje: date | None = None) -> int:
    """Cria a propriedade real, os talhões e as lavouras da safra atual. Tudo ou nada."""
    hoje = hoje or date.today()
    nome = r["fazenda"]["nome"].strip()
    existe = con.execute("SELECT id FROM fazenda.propriedade WHERE NOT demo AND lower(nome) = lower(?)", [nome]).fetchone()
    if existe:
        raise ValueError(f"Já existe uma fazenda chamada {nome}.")
    coord = ler_coordenadas(r["fazenda"].get("coordenadas"))
    unidade = r["fazenda"].get("unidade_area", "ha")
    con.begin()
    try:
        pid = gestao.criar_propriedade(con, nome, *(coord or (None, None)))
        for t in r["talhoes"]:
            if not (t.get("nome") or "").strip():
                continue
            solo = TERRAS[t.get("terra") or "nao_sei"][1]
            tid = gestao.criar_talhao(con, pid, t["nome"].strip(), area_ha(t["area"], unidade), solo)
            if t.get("lavoura") in gestao.CULTURAS:
                plantio = date.fromisoformat(t["data_plantio"]) if t.get("data_plantio") else None
                gestao.criar_plantio(
                    con, tid, t["lavoura"], "verao", plantio,
                    safra=gestao.safra_de(plantio or hoje),
                    cultivar=(t.get("cultivar") or "").strip() or None,
                    grupo_ciclo=CICLOS[t.get("ciclo") or "nao_sei"][1],
                    produtividade_meta_sc_ha=t.get("meta_sc_ha"),
                    status="plantado" if plantio and plantio <= hoje else "planejado",
                )
        con.commit()
    except Exception:
        con.rollback()
        raise
    return pid


def salvar(con: duckdb.DuckDBPyConnection, r: dict) -> dict:
    """Guarda a ficha e, se der, cria a fazenda. Nunca perde as respostas."""
    con.execute(DDL.read_text(encoding="utf-8"))
    try:
        pid, situacao, aviso = aplicar(con, r), "aplicada", None
    except ValueError as e:
        pid, situacao, aviso = None, "guardada", str(e)
    con.execute("INSERT INTO fazenda.ficha (respostas, propriedade_id, situacao) VALUES (?, ?, ?)",
                [json.dumps(r, ensure_ascii=False, default=str), pid, situacao])
    return {"propriedade_id": pid, "situacao": situacao, "aviso": aviso}
