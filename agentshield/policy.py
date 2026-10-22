"""Reglas duras (deterministas). Corren ANTES del Decider y siempre mandan.

Las reglas viven en policies/default.yaml para que se puedan cambiar sin tocar codigo.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .combine import CONFIRM, DENY, PROCEED, HardResult, Thresholds

DEFAULT_POLICY = Path(__file__).resolve().parent.parent / "policies" / "default.yaml"


class Policy:
    def __init__(self, path: str | Path = DEFAULT_POLICY):
        self.rules = yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    def thresholds(self) -> Thresholds | None:
        """Umbrales calibrados por pregunta (seccion `decider.thresholds` del YAML); None si no estan definidos."""
        cfg = (self.rules.get("decider") or {}).get("thresholds")
        return Thresholds(**cfg) if cfg else None

    @staticmethod
    def grounding_gaps(tool_input: dict, user_request: str, tool_outputs: list[str] | None) -> list[str]:
        """Identificadores de pedido que el agente uso pero que no aparecen ni en lo que pidio el usuario ni en lo que
        leyo. Es una comprobacion exacta (no una probabilidad): un ID inventado no se resuelve preguntando al modelo."""
        text = (user_request + "\n" + "\n".join(tool_outputs or [])).lower()
        ids = []
        for key in ("order_id", "order_ids"):
            v = tool_input.get(key)
            ids += v if isinstance(v, list) else [v]
        return [i for i in ids if isinstance(i, str) and i and i.lower() not in text]

    def check(self, tool_name: str, tool_input: dict, role: str = "agente_soporte") -> HardResult:
        r = self.rules
        reasons: list[tuple[str, str]] = []

        allowed = r["roles"].get(role, {}).get("tools", [])
        if tool_name not in allowed:
            reasons.append((DENY, f"el rol {role} no puede usar {tool_name}"))

        amount = tool_input.get("amount")
        if amount is not None:
            lim = r["limits"]
            if amount > lim["max_amount_deny"]:
                reasons.append((DENY, f"monto {amount} supera el maximo {lim['max_amount_deny']}"))
            elif amount > lim["max_amount_confirm"]:
                reasons.append((CONFIRM, f"monto {amount} requiere aprobacion"))

        to = tool_input.get("to")
        if to:
            domain = str(to).split("@")[-1].lower()
            if domain not in r["email"]["allowed_domains"]:
                reasons.append((CONFIRM, f"dominio externo {domain}"))

        if tool_name in r.get("always_confirm", []):
            reasons.append((CONFIRM, f"{tool_name} siempre requiere aprobacion"))

        if any(v == DENY for v, _ in reasons):
            verdict = DENY
        elif any(v == CONFIRM for v, _ in reasons):
            verdict = CONFIRM
        else:
            verdict = PROCEED
        return HardResult(verdict, tuple(m for _, m in reasons))
