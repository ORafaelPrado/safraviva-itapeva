"""Cliente HTTP compartilhado por todos os extratores.

Lição da Fase 0: INMET e dados.agricultura.gov.br recusam ou derrubam
requisições sem User-Agent de navegador (403 / conexão encerrada), e o
servidor do IBGE não envia a cadeia completa de certificados (o bundle do
certifi falha; o repositório do sistema operacional resolve via truststore).
Por isso toda chamada externa passa por aqui.
"""

from __future__ import annotations

import logging

import requests
import truststore
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36 SafraViva/0.1"
)
TIMEOUT_PADRAO = (10, 120)  # (conexão, leitura) em segundos

log = logging.getLogger(__name__)

truststore.inject_into_ssl()


def criar_sessao() -> requests.Session:
    """Sessão com User-Agent de navegador e retentativas com backoff exponencial."""
    sessao = requests.Session()
    sessao.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*"})
    retry = Retry(
        total=4,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
    )
    adaptador = HTTPAdapter(max_retries=retry)
    sessao.mount("https://", adaptador)
    sessao.mount("http://", adaptador)
    return sessao


def get_json(url: str, params: dict | None = None, sessao: requests.Session | None = None):
    """GET que devolve JSON, levantando erro claro em caso de falha HTTP."""
    sessao = sessao or criar_sessao()
    resp = sessao.get(url, params=params, timeout=TIMEOUT_PADRAO)
    resp.raise_for_status()
    return resp.json()
