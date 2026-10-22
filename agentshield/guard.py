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
from .combine import CONFIRM, DENY, GUIDE, PROCEED, Thresholds, Verdict, combine
from .decider_client import make_decider
from .policy import Policy
from .questions import render_state

try:  # Strands es opcional para correr los tests de logica pura
    from strands.interventions import Confirm, Deny, Guide, InterventionHandler, Proceed
except ImportError:  # pragma: no cover
    InterventionHandler = object  # type: ignore[misc,assignment]


class Shield:
    def __init__(self, decider=None, policy: Policy | None = None, threshold: float | None = None,
                 audit: AuditLog | None = None, mode: str = "enforce", thresholds: Thresholds | None = None):
        """Umbrales: `threshold` (un solo numero, modo original) o `thresholds` (por pregunta). Sin ninguno se usan los
        calibrados de la politica (`decider.thresholds`) y, si no existen, el umbral original 0.9."""
        self.decider = decider or make_decider()
        self.policy = policy or Policy()
        if threshold is None and thresholds is None:
            thresholds = self.policy.thresholds()
        self.thresholds = thresholds if threshold is None else None
        self.threshold = 0.9 if threshold is None else threshold
        self.audit = audit or AuditLog()
        self.mode = mode  # "enforce" bloquea; "shadow" solo registra lo que habria hecho

    def evaluate(self, user_request: str, tool_name: str, tool_input: dict,
                 tool_outputs: list[str] | None = None, role: str = "agente_soporte") -> Verdict:
        hard = self.policy.check(tool_name, tool_input, role)
        ans = None
        empty_checks = {"grounded": None, "intent": None, "injected": None, "blast": None,
                        "threshold": None if self.thresholds else self.threshold}
        gaps = [] if hard.verdict == DENY else self.policy.grounding_gaps(tool_input, user_request, tool_outputs)
        if hard.verdict == DENY:
            # La politica ya resolvio: no construir ni enviar contexto al modelo.
            verdict = Verdict(DENY, "regla dura: " + "; ".join(hard.reasons), checks=empty_checks)
        elif gaps:
            # Un ID que no aparece en la conversacion no se "valida" con probabilidades: se corrige sin consultar al modelo.
            verdict = Verdict(GUIDE, f"argumentos sin respaldo: {', '.join(gaps)} no aparece en la solicitud ni en los datos leidos",
                              hint="Pregunta al usuario el dato que falta en lugar de suponerlo.", checks=empty_checks)
        else:
            state = render_state(user_request, tool_name, tool_input, tool_outputs)
            try:
                ans = self.decider.ask(state)
            except Exception as exc:  # fail-closed: sin respuesta del Decider no se ejecuta nada
                verdict = Verdict(DENY, f"el Decider no respondio ({type(exc).__name__})", checks=empty_checks)
            else:
                verdict = combine(ans, hard, self.threshold, self.thresholds)
        self.audit.write({
            "decision_id": str(uuid.uuid4())[:8],
            "mode": self.mode,
            "tool": tool_name,
            "args": tool_input,
            "hard": {"verdict": hard.verdict, "reasons": list(hard.reasons)},
            "answers": verdict.checks,
            "latency_ms": ans.latency_ms if ans else None,
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
