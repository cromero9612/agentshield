"""Ejecuta el agente REAL de Strands desde la consola y expone su avance para pintarlo en vivo.

Una corrida a la vez (los pedidos de demo son un estado global). La aprobacion humana se resuelve desde la web: el
`approver` del guard bloquea el hilo del agente hasta que llega la decision o vence el tiempo (se rechaza).
Modos: "off" (sin guard, para comparar), "enforce" (AgentShield) y "shadow" (registra y no frena).
"""

from __future__ import annotations

import threading
import time
import uuid

from strands.hooks import AfterToolCallEvent

from agent.run_agent import build_agent, describe_model
from agentshield.audit import AuditLog
from agentshield.guard import Shield
from store import tools

APPROVAL_TIMEOUT_S = 120
MODES = ("off", "enforce", "shadow")


def _orders() -> list[dict]:
    return [{"order_id": o.order_id, "status": o.status, "version": o.version}
            for o in tools.SERVICE.connector.get_orders(limit=1000)]


class Run:
    def __init__(self, request: str, mode: str):
        self.id = uuid.uuid4().hex[:8]
        self.request, self.mode = request, mode
        self.status = "running"          # running | awaiting_approval | done | error
        self.model = describe_model()
        self.calls: list[dict] = []      # cada intento de usar una herramienta, en orden
        self.decisions: list[dict] = []  # veredictos del guard, en el mismo orden que `calls`
        self.pending: dict | None = None
        self.final_text = ""
        self.error: str | None = None
        self.orders_before: list[dict] = []
        self.orders_after: list[dict] = []
        self.history: list[dict] = []
        self.started = time.time()
        self.elapsed_s: float | None = None
        self._decision = threading.Event()
        self._approved = False

    def approve(self, approved: bool) -> bool:
        if self.status != "awaiting_approval":
            return False
        self._approved = approved
        self._decision.set()
        return True

    def to_dict(self) -> dict:
        return {"id": self.id, "request": self.request, "mode": self.mode, "status": self.status, "model": self.model,
                "calls": self.calls, "decisions": self.decisions, "pending": self.pending, "final_text": self.final_text,
                "error": self.error, "orders_before": self.orders_before, "orders_after": self.orders_after,
                "history": self.history, "elapsed_s": self.elapsed_s or round(time.time() - self.started, 1)}


class Runner:
    def __init__(self, audit: AuditLog):
        self.audit = audit
        self.runs: dict[str, Run] = {}
        self._busy = threading.Lock()

    def start(self, request: str, mode: str) -> Run | None:
        """Devuelve la corrida, o None si ya hay una en curso."""
        if mode not in MODES:
            raise ValueError(f"mode debe ser uno de {', '.join(MODES)}")
        if not self._busy.acquire(blocking=False):
            return None
        run = Run(request.strip(), mode)
        self.runs[run.id] = run
        threading.Thread(target=self._execute, args=(run,), daemon=True).start()
        return run

    def _execute(self, run: Run) -> None:
        def on_decision(record: dict) -> None:
            run.decisions.append({k: record.get(k) for k in ("decision_id", "tool", "args", "verdict", "reason", "answers",
                                                              "latency_ms", "hard", "mode")})

        def approver(prompt: str) -> bool:
            run._decision.clear()
            run.pending = {"prompt": prompt, "decision": run.decisions[-1] if run.decisions else None}
            run.status = "awaiting_approval"
            decided = run._decision.wait(APPROVAL_TIMEOUT_S)
            run.pending, run.status = None, "running"
            return bool(decided and run._approved)

        def after_tool(event: AfterToolCallEvent) -> None:
            res = event.result or {}
            text = " ".join(c.get("text", "") for c in res.get("content", []))
            run.calls.append({"tool": event.tool_use.get("name"), "args": dict(event.tool_use.get("input") or {}),
                              "result": text[:600], "blocked": bool(event.cancel_message) or res.get("status") == "error"
                              and text.startswith(("DENIED", "AgentShield"))})

        try:
            tools.reset()
            run.orders_before = _orders()
            shield, shield_mode = None, None
            if run.mode != "off":
                shield_mode = "shadow" if run.mode == "shadow" else "enforce"
                shield = Shield(audit=self.audit, mode=shield_mode)
                self.audit.subscribe(on_decision)
            agent = build_agent(shield_mode, shield=shield, approver=approver, quiet=True)
            agent.hooks.add_callback(AfterToolCallEvent, after_tool)
            result = agent(run.request)
            run.final_text = str(result).strip()
            final = "done"
        except Exception as exc:  # noqa: BLE001 - la consola debe mostrar el error, no morir
            run.error, final = f"{type(exc).__name__}: {exc}", "error"
        finally:
            if on_decision in self.audit.listeners:
                self.audit.listeners.remove(on_decision)
            run.orders_after = _orders()
            run.history = tools.SERVICE.connector.history()
            run.elapsed_s = round(time.time() - run.started, 1)
            run.pending = None
            self._busy.release()
            # El estado final se publica AL ULTIMO: quien consulta ve "done" solo cuando los pedidos finales, el historial
            # y el bloqueo ya estan listos (publicarlo antes producia lecturas incompletas y 409 espurios).
            run.status = locals().get("final", "error")
