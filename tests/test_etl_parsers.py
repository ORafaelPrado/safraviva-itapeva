"""Testes dos parsers do ETL com amostras reais (sem rede)."""

import io

import pytest

from etl import ibge, inmet, zarc


@pytest.mark.parametrize(
    ("bruto", "esperado"),
    [("2949", 2949.0), ("-", 0.0), ("..", None), ("...", None), ("X", None), ("", None)],
)
def test_valor_sidra_convencoes_ibge(bruto, esperado):
    assert ibge.valor_sidra(bruto) == esperado


def test_parse_sidra_municipio():
    resposta = [
        {"NC": "Nível Territorial (Código)", "V": "Valor", "D1C": "Município (Código)", "D1N": "Município",
         "D2C": "Variável (Código)", "D2N": "Variável", "D3C": "Ano (Código)", "D3N": "Ano",
         "D4C": "Produto das lavouras temporárias (Código)", "D4N": "Produto das lavouras temporárias"},
        {"NC": "6", "V": "2949", "D1C": "3522406", "D1N": "Itapeva (SP)", "D2C": "112", "D2N": "Rendimento",
         "D3C": "2025", "D3N": "2025", "D4C": "2713", "D4N": "Soja (em grão)"},
        {"NC": "6", "V": "-", "D1C": "3522406", "D1N": "Itapeva (SP)", "D2C": "112", "D2N": "Rendimento",
         "D3C": "2025", "D3N": "2025", "D4C": "2693", "D4N": "Aveia (em grão)"},
    ]
    df = ibge.parse_sidra(resposta, "municipio")
    assert df[["codigo_local", "ano", "cultura_codigo", "valor"]].values.tolist() == [
        [3522406, 2025, 2713, 2949.0],
        [3522406, 2025, 2693, 0.0],
    ]


CABECALHO_INMET = "\n".join(
    ["REGIAO:;SE", "UF:;SP", "ESTACAO:;ITAPEVA", "CODIGO (WMO):;A714", "LATITUDE:;-23,98",
     "LONGITUDE:;-48,88", "ALTITUDE:;743,33", "DATA DE FUNDACAO:;25/07/06"]
)
COLUNAS_INMET = ";".join(f"c{i}" for i in range(19)) + ";"


def _csv_inmet(linhas: list[str]) -> io.BytesIO:
    return io.BytesIO("\n".join([CABECALHO_INMET, COLUNAS_INMET, *linhas]).encode("latin-1"))


def test_inmet_formato_novo_e_ausentes():
    df = inmet.ler_csv(
        _csv_inmet(["2025/01/01;0300 UTC;1,2;929,2;929,2;928,2;;21,3;18,9;22,3;21,3;19,2;18,9;86;82;86;105;5,2;2,2;"]),
        "A714",
    )
    linha = df.iloc[0]
    assert str(linha.ts_utc) == "2025-01-01 03:00:00"
    assert linha.chuva_mm == pytest.approx(1.2)
    assert linha.temp_c == pytest.approx(21.3)
    assert linha.vento_ms == pytest.approx(2.2)
    assert df["radiacao_kj_m2"].isna().all()


def test_inmet_formato_antigo_com_menos9999():
    df = inmet.ler_csv(
        _csv_inmet(["2006-07-25;14:00;-9999;930;930;929;1500;15,5;8;16;15;8;7;60;55;58;90;6;3;"]),
        "A714",
    )
    assert str(df.iloc[0].ts_utc) == "2006-07-25 14:00:00"
    assert df.iloc[0].chuva_mm != df.iloc[0].chuva_mm  # NaN
    assert df.iloc[0].radiacao_kj_m2 == 1500


def test_zarc_filtra_municipios_e_normaliza():
    decs = ";".join(f"dec{i}" for i in range(1, 37))
    base = "Soja;2026;2027;1;22;13;{geo};SP;X;0;N/A;1;Sequeiro;;;1;1;1;Port.1;" + ";".join(["0"] * 35) + ";20"
    linhas = [
        "﻿Nome_cultura;SafraIni;SafraFin;Cod_Cultura;Cod_Ciclo;Cod_Solo;geocodigo;UF;municipio;Cod_Clima;"
        "Nome_Clima;Cod_Outros_Manejos;Nome_Outros_Manejos;Produtividade;Cod_NM;Cod_Munic;Cod_Meso;Cod_Micro;Portaria;" + decs,
        base.format(geo="3522406"),
        base.format(geo="3550100"),
    ]
    resultado = list(zarc.filtrar_linhas(linhas, {"3522406"}))
    assert resultado[0][0] == "Nome_cultura"  # BOM removido
    assert len(resultado) == 2

    import pandas as pd

    df = zarc.normalizar(pd.DataFrame(resultado[1:], columns=resultado[0]), "2026-2027")
    assert list(df.columns) == zarc.COLUNAS_RAW
    assert df.loc[0, "dec36"] == 20 and df.loc[0, "cod_solo"] == 13
