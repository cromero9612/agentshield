"""Modelo guionizado para probar agentes de Strands sin Bedrock.

`ScriptedModel` hace el papel del modelo generativo: en cada turno responde lo que dicta el guion
(llamar una herramienta o contestar texto). Todo lo demas es Strands real: el `Agent`, el bucle de eventos,
las herramientas y el hook de intervenciones. Sirve para tests y para ensayar sin cuota de Bedrock;
**no** sustituye la prueba con el modelo real.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

from strands.models import Model

_USAGE = {"usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2}, "metrics": {"latencyMs": 1}}


def call(name: str, **tool_input: Any) -> dict:
    """Turno en el que el modelo pide usar una herramienta."""
    return {"tool": name, "input": tool_input}


def say(text: str) -> dict:
    """Turno en el que el modelo contesta con texto y termina."""
    return {"text": text}


class ScriptedModel(Model):
    def __init__(self, script: list[dict]):
        self.script = list(script)
        self.turn = 0
        self.seen: list[list[dict]] = []  # mensajes que recibio el modelo en cada turno

    def update_config(self, **model_config: Any) -> None:  # pragma: no cover
        pass

    def get_config(self) -> Any:  # pragma: no cover
        return {}

    async def structured_output(self, output_model, prompt, system_prompt=None, **kwargs):  # pragma: no cover
        raise NotImplementedError

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs) -> AsyncGenerator[dict, None]:
        self.seen.append(json.loads(json.dumps(messages, default=str)))
        step = self.script[min(self.turn, len(self.script) - 1)]
        self.turn += 1
        yield {"messageStart": {"role": "assistant"}}
        if "tool" in step:
            yield {"contentBlockStart": {"start": {"toolUse": {"toolUseId": f"t{self.turn}", "name": step["tool"]}}}}
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(step["input"])}}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            yield {"contentBlockStart": {"start": {}}}
            yield {"contentBlockDelta": {"delta": {"text": step["text"]}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}
        yield {"metadata": _USAGE}
