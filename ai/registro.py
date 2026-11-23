"""Registro das conversas do Agrônomo Digital (tabela ai.conversa)."""

from __future__ import annotations

import json

from ai.agente import Resultado


def registrar(con, pergunta: str, resultado: Resultado, propriedade_id: int | None, origem: str = "chat") -> int:
    return con.execute(
        """INSERT INTO ai.conversa (propriedade_id, origem, pergunta, resposta, ferramentas, modelo,
                                    tokens_entrada, tokens_saida, segundos)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
        [propriedade_id, origem, pergunta, resultado.texto,
         json.dumps(resultado.ferramentas_usadas, ensure_ascii=False, default=str), resultado.modelo,
         resultado.tokens_entrada, resultado.tokens_saida, round(resultado.segundos, 2)],
    ).fetchone()[0]
