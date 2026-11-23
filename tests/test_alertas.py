"""Testes das regras de alerta do painel (sem banco, sem rede)."""

from datetime import date

import pandas as pd
import pytest

from app import alertas


def _diaria(tmin=None, tmax=None, chuva=None, prob=None, n=16):
    datas = pd.date_range("2026-06-01", periods=n, freq="D")
    return pd.DataFrame({
        "data": datas,
        "temp_min_c": tmin or [10.0] * n,
        "temp_max_c": tmax or [25.0] * n,
        "chuva_mm": chuva if chuva is not None else [5.0] * n,
        "prob_chuva_pct": prob if prob is not None else [60.0] * n,
    })


@pytest.mark.parametrize(
    ("minima", "nivel"),
    [(8.0, "ok"), (2.5, "atencao"), (0.5, "critico")],
)
def test_geada_niveis(minima, nivel):
    tmin = [10.0] * 16
    tmin[4] = minima
    alerta = alertas.alerta_geada(_diaria(tmin=tmin))
    assert alerta.nivel == nivel
    if nivel != "ok":
        assert "05/06" in alerta.titulo  # 5º dia da série


def test_veranico_conta_maior_sequencia():
    chuva = [5.0] * 3 + [0.0] * 11 + [5.0] * 2
    prob = [60.0] * 3 + [10.0] * 11 + [60.0] * 2
    dias, inicio = alertas.maior_sequencia_seca(_diaria(chuva=chuva, prob=prob))
    assert dias == 11 and pd.Timestamp(inicio) == pd.Timestamp("2026-06-04")
    assert alertas.alerta_veranico(_diaria(chuva=chuva, prob=prob)).nivel == "critico"


def test_veranico_ignora_dia_seco_com_chance_alta_de_chuva():
    # Chuva prevista 0 mm, mas 80% de chance: não conta como dia seco garantido.
    alerta = alertas.alerta_veranico(_diaria(chuva=[0.0] * 16, prob=[80.0] * 16))
    assert alerta.nivel == "ok"


def test_calor_exige_tres_dias():
    tmax = [25.0] * 16
    tmax[2] = tmax[3] = 33.0
    assert alertas.alerta_calor(_diaria(tmax=tmax)).nivel == "ok"
    tmax[9] = 34.0
    alerta = alertas.alerta_calor(_diaria(tmax=tmax))
    assert alerta.nivel == "atencao" and "34" in alerta.detalhe


def _horaria(vento, delta_t, prob=0.0, temp=25.0):
    ts = pd.date_range("2026-11-04 00:00", periods=48, freq="h")
    return pd.DataFrame({"ts_local": ts, "vento_kmh": vento, "delta_t_c": delta_t, "prob_chuva_pct": prob, "temp_c": temp})


def test_pulverizacao_hora_boa_e_motivos():
    h = alertas.horas_pulverizacao(_horaria(vento=6.0, delta_t=4.0), agora=pd.Timestamp("2026-11-04 00:00"))
    boas = h[h["boa"]]
    assert set(boas["ts_local"].dt.hour) == set(range(6, 21))  # só entre 6h e 20h
    ruim = alertas.horas_pulverizacao(_horaria(vento=15.0, delta_t=4.0), agora=pd.Timestamp("2026-11-04 00:00"))
    assert not ruim["boa"].any() and set(ruim["motivo"]) == {"vento"}
    seco = alertas.horas_pulverizacao(_horaria(vento=6.0, delta_t=10.0), agora=pd.Timestamp("2026-11-04 00:00"))
    assert seco["motivo"].str.contains("ar seco").all()


def test_pulverizacao_ignora_horas_passadas():
    h = alertas.horas_pulverizacao(_horaria(vento=6.0, delta_t=4.0), agora=pd.Timestamp("2026-11-04 15:30"))
    assert h["ts_local"].min() == pd.Timestamp("2026-11-04 15:00")


def test_alerta_pulverizacao_sem_janela():
    alerta = alertas.alerta_pulverizacao(_horaria(vento=20.0, delta_t=4.0), agora=pd.Timestamp("2026-11-04 00:00"))
    assert alerta.nivel == "atencao"


def _janelas():
    return pd.DataFrame({
        "nome_cultura": ["Soja", "Soja", "Trigo"],
        "data_inicio": pd.to_datetime(["2026-09-01", "2026-10-01", "2027-04-01"]),
        "data_fim": pd.to_datetime(["2026-09-30", "2026-12-31", "2027-05-31"]),
        "nivel_risco": ["médio", "baixo", "baixo"],
        "risco_pct": [30, 20, 20],
    })


def test_plantio_dentro_fora_e_risco_medio():
    assert alertas.situacao_plantio(_janelas(), "Soja", date(2026, 11, 3)).nivel == "ok"
    medio = alertas.situacao_plantio(_janelas(), "Soja", date(2026, 9, 15))
    assert medio.nivel == "atencao" and "01/10" in medio.detalhe
    fora = alertas.situacao_plantio(_janelas(), "Trigo", date(2026, 11, 3))
    assert fora.nivel == "info" and "01/04" in fora.detalhe
    assert alertas.situacao_plantio(_janelas(), "Milho", date(2026, 11, 3)).nivel == "info"


def test_plantio_projeta_janela_quando_zarc_novo_nao_saiu():
    projetada = alertas.situacao_plantio(_janelas(), "Trigo", date(2027, 7, 1))
    assert projetada.nivel == "info" and "01/04 a 31/05" in projetada.detalhe and "ainda não publicou" in projetada.detalhe


def test_lavoura_mesma_seca_pesa_diferente_por_fase():
    chuva = [0.0] * 12 + [10.0] * 4
    prob = [5.0] * 12 + [80.0] * 4
    diaria = _diaria(chuva=chuva, prob=prob)
    florescimento = alertas.alerta_lavoura("T1", "soja", "florescimento", 60, diaria)
    vegetativo = alertas.alerta_lavoura("T1", "soja", "vegetativo", 30, diaria)
    assert florescimento.nivel == "critico" and "12 dias" in florescimento.titulo
    assert vegetativo.nivel == "ok"


def test_lavoura_geada_so_importa_no_trigo_sensivel():
    tmin = [10.0] * 16
    tmin[3] = 2.0
    diaria = _diaria(tmin=tmin)
    assert alertas.alerta_lavoura("T2", "trigo", "florescimento", 70, diaria).nivel == "critico"
    assert alertas.alerta_lavoura("T2", "trigo", "perfilhamento", 30, diaria).nivel == "atencao"
    assert alertas.alerta_lavoura("T2", "soja", "vegetativo", 30, diaria).nivel == "ok"


def test_lavoura_chuva_na_colheita():
    diaria = _diaria(chuva=[10.0] * 16)
    assert alertas.alerta_lavoura("T3", "soja", "maturação", 115, diaria).nivel == "atencao"
