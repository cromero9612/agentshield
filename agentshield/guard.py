"""AgentShield: guard de tool calls para agentes Strands.

Dos capas:
- Shield.evaluate(): logica pura (reglas duras + Decider + combine). Se prueba sin Strands.
- AgentShieldHandler: el InterventionHandler que se conecta a Agent(interventions=[...]).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from .audit import AuditLog
from .combine import CONFIRM, DENY, GUIDE, PROCEED, Verdict, combine
from .decider_client import make_decider
from .policy import Policy
from .questions import render_state

try:  # Strands es opcional para correr los tests de logica pura
    from strands.interventions import Confirm, Deny, Guide, InterventionHandler, Proceed
except ImportError:  # pragma: no cover
    InterventionHandler = object  # type: ignore[misc,assignment]


class Shield:
    def __init__(self, decider=None, policy: Policy | None = None, threshold: float = 0.9,
                 audit: AuditLog | None = None, mode: str = "enforce"):
        self.decider = decider or make_decider()
        self.policy = policy or Policy()
        self.threshold = threshold
        self.audit = audit or AuditLog()
        self.mode = mode  # "enforce" bloquea; "shadow" solo registra lo que habria hecho

    def evaluate(self, user_request: str, tool_name: str, tool_input: dict,
                 tool_outputs: list[str] | None = None, role: str = "agente_soporte") -> Verdict:
        hard = self.policy.check(tool_name, tool_input, role)
        state = render_state(user_request, tool_name, tool_input, tool_outputs)
        ans = self.decider.ask(state)
        verdict = combine(ans, hard, self.threshold)
        self.audit.write({
            "decision_id": str(uuid.uuid4())[:8],
            "mode": self.mode,
            "tool": tool_name,
            "args": tool_input,
            "hard": {"verdict": hard.verdict, "reasons": list(hard.reasons)},
            "answers": verdict.checks,
            "latency_ms": ans.latency_ms,
            "verdict": verdict.action,
            "reason": verdict.reason,
        })
        return verdict


def _text_of(block: dict) -> str:
    if "text" in block:
        return block["text"]
    if "toolResult" in block:
        return " ".join(c.get("text", "") for c in block["toolResult"].get("content", []))
    return ""


def context_from_messages(messages: list[dict]) -> tuple[str, list[str]]:
    """Ultimo pedido del usuario + textos devueltos por herramientas despues de ese pedido."""
    user_request, outputs = "", []
    for m in messages:
        blocks = m.get("content", [])
        is_tool_result = any("toolResult" in b for b in blocks)
        if m.get("role") == "user" and not is_tool_result:
            user_request = " ".join(_text_of(b) for b in blocks).strip()
            outputs = []
        elif is_tool_result:
            outputs.extend(_text_of(b) for b in blocks if "toolResult" in b)
    return user_request, outputs


class AgentShieldHandler(InterventionHandler):
    """Conectar con: Agent(..., interventions=[AgentShieldHandler(shield)])."""

    name = "agentshield"

    def __init__(self, shield: Shield, approver: Callable[[str], bool] | None = None):
        self.shield = shield
        self.approver = approver  # si es None, Confirm pausa el agente

    @property
    def on_error(self):
        return "deny"  # si el guard falla, se cierra (fail-closed)

    def before_tool_call(self, event: Any, **kwargs: Any):
        tool = event.tool_use
        user_request, outputs = context_from_messages(event.agent.messages)
        v = self.shield.evaluate(user_request, tool["name"], dict(tool.get("input") or {}), outputs)

        if self.shield.mode == "shadow" or v.action == PROCEED:
            return Proceed(reason=v.reason)
        if v.action == GUIDE:
            return Guide(feedback=f"AgentShield: {v.reason}. {v.hint}", reason=v.reason)
        if v.action == CONFIRM:
            prompt = f"AgentShield pide aprobacion para {tool['name']}({tool.get('input')}): {v.reason}"
            if self.approver:
                return Confirm(prompt=prompt, reason=v.reason, response=self.approver(prompt))
            return Confirm(prompt=prompt, reason=v.reason)
        if v.action == DENY:
            return Deny(reason=f"AgentShield bloqueo la accion: {v.reason}")
        return Deny(reason="veredicto desconocido")
