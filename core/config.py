"""Configuração central do SafraViva: região de estudo, culturas, estações e caminhos.

Todos os códigos abaixo foram validados contra as APIs oficiais na Fase 0
(ver docs/fontes.md). Altere aqui, nunca espalhado pelo código.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

DIR_DADOS = RAIZ / "data"
DIR_RAW = DIR_DADOS / "raw"
DIR_PROCESSED = DIR_DADOS / "processed"
DIR_SQL = RAIZ / "sql"
CAMINHO_DB = RAIZ / os.getenv("SAFRAVIVA_DB", "data/safraviva.duckdb")


@dataclass(frozen=True)
class Municipio:
    codigo_ibge: int
    nome: str
    microrregiao: str
    foco: bool = False  # True = município principal do estudo


# Microrregião de Itapeva + vizinhos relevantes (códigos IBGE 7 dígitos).
MUNICIPIOS: tuple[Municipio, ...] = (
    Municipio(3522406, "Itapeva", "Itapeva", foco=True),
    Municipio(3521705, "Itaberá", "Itapeva"),
    Municipio(3553856, "Taquarivaí", "Itapeva"),
    Municipio(3508009, "Buri", "Itapeva"),
    Municipio(3532827, "Nova Campina", "Itapeva"),
    Municipio(3523206, "Itararé", "Itapeva"),
    Municipio(3543501, "Riversul", "Itapeva"),
    Municipio(3543006, "Ribeirão Branco", "Capão Bonito"),
    Municipio(3510203, "Capão Bonito", "Capão Bonito"),
    Municipio(3517604, "Guapiara", "Capão Bonito"),
    Municipio(3522307, "Itapetininga", "Itapetininga"),
)
CODIGO_ITAPEVA = 3522406


@dataclass(frozen=True)
class Cultura:
    slug: str
    nome: str
    codigo_sidra: int  # categoria da classificação 81 da tabela SIDRA 1612
    estacao: str  # verao | inverno


# Classificação 81 da tabela SIDRA 1612 (PAM — lavouras temporárias).
CULTURAS: tuple[Cultura, ...] = (
    Cultura("soja", "Soja (em grão)", 2713, "verao"),
    Cultura("milho", "Milho (em grão)", 2711, "verao"),
    Cultura("feijao", "Feijão (em grão)", 2702, "verao"),
    Cultura("trigo", "Trigo (em grão)", 2716, "inverno"),
    Cultura("aveia", "Aveia (em grão)", 2693, "inverno"),
    Cultura("cevada", "Cevada (em grão)", 2699, "inverno"),
    Cultura("sorgo", "Sorgo (em grão)", 2714, "verao"),
)

# Variáveis da tabela SIDRA 1612.
SIDRA_VARIAVEIS = {
    109: "area_plantada_ha",
    216: "area_colhida_ha",
    214: "producao_t",
    112: "rendimento_kg_ha",
    215: "valor_mil_reais",
}


@dataclass(frozen=True)
class EstacaoInmet:
    codigo: str
    nome: str
    lat: float
    lon: float
    altitude_m: float
    distancia_itapeva_km: int


# Estação principal (A714) + apoio para preenchimento de falhas.
ESTACOES_INMET: tuple[EstacaoInmet, ...] = (
    EstacaoInmet("A714", "Itapeva", -23.98194443, -48.88583333, 743.33, 1),
    EstacaoInmet("A715", "São Miguel Arcanjo", -23.89083333, -47.99916666, 710.0, 90),
    EstacaoInmet("A725", "Avaré", -23.10166666, -48.9411111, 776.36, 98),
    EstacaoInmet("A821", "Joaquim Távora (PR)", -23.50527777, -49.94638888, 512.67, 121),
)

FAZENDA_LAT = float(os.getenv("FAZENDA_LAT", "-23.982"))
FAZENDA_LON = float(os.getenv("FAZENDA_LON", "-48.876"))
FUSO = "America/Sao_Paulo"
