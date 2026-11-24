"""Configuração comum dos testes.

Os testes NUNCA podem tocar o banco da nuvem: com MOTHERDUCK_TOKEN no .env, `core.db.conectar()` usaria
o MotherDuck, e alguns testes gravam (ex.: envio do formulário de operação). Por isso o token é removido
do ambiente em todos os testes.
"""

import pytest


@pytest.fixture(autouse=True)
def _sem_banco_na_nuvem(monkeypatch):
    monkeypatch.delenv("MOTHERDUCK_TOKEN", raising=False)
    monkeypatch.setenv("SAFRAVIVA_SEM_ATUALIZAR", "1")  # telas não buscam dados na internet durante os testes
