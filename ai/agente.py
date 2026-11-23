"""Agrônomo Digital: laço de tool calling sobre as ferramentas do SafraViva.

    from ai.agente import Agente, ProvedorOpenAI
    agente = Agente(ProvedorOpenAI())
    r = agente.perguntar("Posso pulverizar amanhã?", ctx=Contexto(propriedade_id=1))
    r.texto, r.ferramentas_usadas, r.pendentes

O provedor de modelo fica atrás de uma interface pequena (`Provedor.responder`). Hoje usamos a
OpenAI (Chat Completions com tools); trocar de provedor é escrever outra classe com o mesmo método.
Os testes usam um provedor roteirizado, sem rede.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from ai import ferramentas
from ai.ferramentas import Contexto
from core import config

PROMPT_SISTEMA = (config.RAIZ / "ai" / "prompts" / "agronomo.md").read_text(encoding="utf-8")
DIAS_SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MAX_RODADAS = 8          # chamadas ao modelo por pergunta (evita laço infinito de ferramentas)
MAX_CHARS_FERRAMENTA = 12_000
MODELO_PADRAO = "gpt-5-mini"


@dataclass
class ChamadaFerramenta:
    id: str
    nome: str
    argumentos: dict


@dataclass
class RespostaModelo:
    texto: str | None
    chamadas: list[ChamadaFerramenta]
    tokens_entrada: int = 0
    tokens_saida: int = 0
    bruto: dict | None = None  # mensagem do assistente no formato da API, para devolver no histórico


class Provedor(Protocol):
    modelo: str

    def responder(self, mensagens: list[dict], ferramentas: list[dict]) -> RespostaModelo: ...


class ProvedorOpenAI:
    """OpenAI Chat Completions com function calling. Lê OPENAI_API_KEY e OPENAI_MODEL do .env."""

    def __init__(self, modelo: str | None = None, chave: str | None = None):
        from openai import OpenAI

        chave = chave or os.getenv("OPENAI_API_KEY")
        if not chave:
            raise RuntimeError("OPENAI_API_KEY não configurada no arquivo .env")
        self.modelo = modelo or os.getenv("OPENAI_MODEL") or MODELO_PADRAO
        self._cliente = OpenAI(api_key=chave, timeout=90, max_retries=2)

    def responder(self, mensagens: list[dict], ferramentas: list[dict]) -> RespostaModelo:
        resp = self._cliente.chat.completions.create(
            model=self.modelo, messages=mensagens, tools=ferramentas, tool_choice="auto",
        )
        msg = resp.choices[0].message
        chamadas = [
            ChamadaFerramenta(c.id, c.function.name, json.loads(c.function.arguments or "{}"))
            for c in (msg.tool_calls or [])
        ]
        bruto = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            bruto["tool_calls"] = [
                {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                for c in msg.tool_calls
            ]
        uso = resp.usage
        return RespostaModelo(msg.content, chamadas, getattr(uso, "prompt_tokens", 0) or 0,
                              getattr(uso, "completion_tokens", 0) or 0, bruto)


@dataclass
class Resultado:
    texto: str
    ferramentas_usadas: list[dict] = field(default_factory=list)  # [{nome, argumentos, resultado_resumido}]
    pendentes: list[dict] = field(default_factory=list)
    tokens_entrada: int = 0
    tokens_saida: int = 0
    segundos: float = 0.0
    modelo: str = ""


def prompt_sistema(ctx: Contexto, nome_propriedade: str | None) -> str:
    hoje: date = ctx.hoje
    return PROMPT_SISTEMA.format(
        hoje=hoje.strftime("%d/%m/%Y"), hoje_iso=hoje.isoformat(), dia_semana=DIAS_SEMANA[hoje.weekday()],
        propriedade=nome_propriedade or "nenhuma cadastrada (responda só com dados da região)",
    )


def _compactar(resultado: dict) -> str:
    texto = json.dumps(resultado, ensure_ascii=False, default=str)
    if len(texto) > MAX_CHARS_FERRAMENTA:
        texto = texto[:MAX_CHARS_FERRAMENTA] + ' …"(resultado cortado)"'
    return texto


class Agente:
    def __init__(self, provedor: Provedor):
        self.provedor = provedor

    def perguntar(self, pergunta: str, ctx: Contexto, historico: list[dict] | None = None,
                  nome_propriedade: str | None = None) -> Resultado:
        """Responde uma pergunta. `historico` = turnos anteriores [{role: user|assistant, content}]."""
        inicio = time.perf_counter()
        mensagens = [{"role": "system", "content": prompt_sistema(ctx, nome_propriedade)}]
        mensagens += [m for m in (historico or []) if m.get("role") in ("user", "assistant") and m.get("content")]
        mensagens.append({"role": "user", "content": pergunta})
        resultado = Resultado(texto="", modelo=self.provedor.modelo)

        for _ in range(MAX_RODADAS):
            resposta = self.provedor.responder(mensagens, ferramentas.esquemas())
            resultado.tokens_entrada += resposta.tokens_entrada
            resultado.tokens_saida += resposta.tokens_saida
            if not resposta.chamadas:
                resultado.texto = (resposta.texto or "").strip() or "Não consegui formular uma resposta. Pode reformular?"
                break
            mensagens.append(resposta.bruto or {"role": "assistant", "content": resposta.texto, "tool_calls": [
                {"id": c.id, "type": "function", "function": {"name": c.nome, "arguments": json.dumps(c.argumentos)}}
                for c in resposta.chamadas]})
            for chamada in resposta.chamadas:
                saida = ferramentas.executar(chamada.nome, chamada.argumentos, ctx)
                resultado.ferramentas_usadas.append({"nome": chamada.nome, "argumentos": chamada.argumentos,
                                                     "erro": saida.get("erro")})
                mensagens.append({"role": "tool", "tool_call_id": chamada.id, "content": _compactar(saida)})
        else:
            resultado.texto = ("Precisei consultar dados demais para essa pergunta. "
                               "Tente dividir em perguntas menores.")

        resultado.pendentes = list(ctx.pendentes)
        resultado.segundos = time.perf_counter() - inicio
        return resultado


def confirmar_pendente(con, pendente: dict) -> int:
    """Grava um lançamento pendente aprovado pelo produtor (usa as mesmas funções das telas)."""
    from app import gestao

    funcao = getattr(gestao, pendente["funcao"])
    return funcao(con, **pendente["argumentos"])
