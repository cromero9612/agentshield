"""Clientes del Decider.

- HttpDecider: habla con `strands-decider serve` (EC2 con GPU o tu laptop).
- MockDecider: heuristicas simples para trabajar SIN modelo ni GPU. Permite que
  los 4 del equipo avancen en paralelo desde el dia 1. No sirve para el benchmark.

Elegir con la variable de entorno DECIDER_URL: si esta vacia, se usa el mock.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.request

from .combine import GuardAnswers
from .questions import GUARD_QUESTIONS


class HttpDecider:
    def __init__(self, url: str, timeout: float = 5.0):
        self.url = url.rstrip("/") + "/v1/systemone"
        self.timeout = timeout

    def ask(self, state: dict) -> GuardAnswers:
        body = json.dumps({"state": state, "questions": GUARD_QUESTIONS}).encode()
        req = urllib.request.Request(self.url, data=body, headers={"Content-Type": "application/json"})
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read())
        ms = (time.perf_counter() - t0) * 1000
        a = data["answers"]
        return GuardAnswers(
            grounded=a["grounded"]["noul"],
            intent=a["intent"]["noul"],
            injected=a["injected"]["noul"],
            blast=a["blast"]["score"],
            latency_ms=data.get("latency_ms", ms),
            blast_confidence=a["blast"].get("confidence"),
        )


# Herramientas que cambian algo y lo que tiene que decir el usuario para pedirlas.
_INTENT_WORDS = {
    "cancel_orders": ["cancela", "cancelar", "anula"],
    "update_customer": ["actualiza", "cambia", "modifica"],
    "update_order_status": ["actualiza", "cambia", "pasa", "pásalo", "marca", "avanza", "mueve"],
    "update_order_amount": ["ajusta", "cambia", "precio", "monto"],
    "issue_refund": ["reembolsa", "reembolso", "devuelve"],
    "send_email": ["manda", "envia", "envía", "correo"],
}
_BLAST = {"get_inventory": 0, "get_orders": 0, "get_tickets": 0, "update_customer": 1, "update_order_status": 1,
          "update_order_amount": 1, "cancel_orders": 2, "issue_refund": 2, "send_email": 2}
_SYNONYMS = {"delayed": ["atrasad"], "paid": ["pagad"], "shipped": ["enviad"], "pending": ["pendiente"],
             "processing": ["procesando", "en proceso"], "delivered": ["entregad"], "cancelled": ["cancelad"]}
_IGNORED_ARGS = {"limit"}  # parametros de paginacion: no identifican nada que deba estar respaldado
_INJECTION = re.compile(r"ignora|ignore (all|previous)|instrucciones anteriores|de inmediato", re.I)


class MockDecider:
    """Imita al Decider con reglas obvias. Solo para desarrollo y demos sin GPU."""

    def ask(self, state: dict) -> GuardAnswers:
        user = state["user_request"].lower()
        call = state["proposed_tool_call"]
        name, args = call["name"], call["arguments"]
        outputs = " ".join(state.get("tool_outputs_seen_by_agent", []))

        text = user + " " + outputs.lower()

        def seen(v: str) -> bool:
            return v in text or any(s in text for s in _SYNONYMS.get(v, []))

        def values(v):  # los argumentos pueden ser listas (order_ids)
            return v if isinstance(v, list) else [v]

        missing = [k for k, v in args.items() if k not in _IGNORED_ARGS
                   for x in values(v) if x not in (None, "") and not seen(str(x).lower())]
        if not missing:
            grounded = 0.95
        elif any(k.endswith(("_id", "_ids")) for k in missing):
            grounded = 0.05  # un identificador inventado
        else:
            grounded = 0.60  # dato dudoso: zona de duda



        words = _INTENT_WORDS.get(name)
        intent = 0.95 if words is None or any(w in user for w in words) else 0.05

        injected = 0.0
        if _INJECTION.search(outputs) and intent < 0.5:
            injected = 0.97

        return GuardAnswers(grounded, intent, injected, float(_BLAST.get(name, 1)), latency_ms=1.0)


def make_decider():
    url = os.getenv("DECIDER_URL", "").strip()
    return HttpDecider(url) if url else MockDecider()
