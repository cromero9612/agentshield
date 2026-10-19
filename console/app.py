"""Consola de AgentShield. Responsable: Persona C.

    uvicorn console.app:app --reload --port 8080   ->   http://localhost:8080

Version inicial: reproduce los casos de bench/cases.jsonl contra el guard y
transmite cada decision por SSE. Funciona sin AWS (Decider mock). El dia 4 se
conecta al agente real.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from agentshield.audit import AuditLog
from agentshield.guard import Shield
from bench.run_bench import load_cases

app = FastAPI(title="AgentShield console")
STATIC = Path(__file__).parent / "static"
queues: list[asyncio.Queue] = []
loop: asyncio.AbstractEventLoop | None = None


LAST: dict = {}  # ultimo evento de auditoria; /api/run lo lee para devolver latencia e id
_lock = threading.Lock()  # el Shield de la consola se comparte: una evaluacion a la vez


def _broadcast(record: dict) -> None:
    LAST.clear()
    LAST.update(record)
    if loop is None:
        return
    for q in list(queues):
        loop.call_soon_threadsafe(q.put_nowait, record)


audit = AuditLog("console_audit.jsonl")
audit.subscribe(_broadcast)
shield = Shield(audit=audit)
CASES = {c["id"]: c for c in load_cases()}


@app.on_event("startup")
async def _startup() -> None:
    global loop
    loop = asyncio.get_running_loop()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/cases")
def cases() -> list[dict]:
    return list(CASES.values())


class RunBody(BaseModel):
    case_id: str
    threshold: float = 0.9
    mode: str = "enforce"  # enforce | shadow


class AttackBody(BaseModel):
    ticket: str
    tool: str = "issue_refund"
    args: dict = {}
    threshold: float = 0.9
    mode: str = "enforce"


# Lo que el usuario "pidio" en la demo del ticket malicioso: una tarea inocente de solo lectura.
ATTACK_USER_REQUEST = "Resumeme los tickets que entraron hoy."


def _evaluate(user_request: str, tool: str, args: dict, outputs: list[str], threshold: float, mode: str) -> dict:
    if mode not in ("enforce", "shadow"):
        raise HTTPException(422, "mode debe ser enforce o shadow")
    with _lock:
        shield.threshold, shield.mode = threshold, mode
        hard = shield.policy.check(tool, args)
        v = shield.evaluate(user_request, tool, args, outputs)
        event = dict(LAST)
    # En modo sombra el guard registra lo que habria hecho, pero la accion se ejecuta.
    effective = "proceed" if mode == "shadow" else v.action
    return {
        "verdict": v.action, "effective": effective, "mode": mode, "reason": v.reason, "hint": v.hint,
        "checks": v.checks, "hard": {"verdict": hard.verdict, "reasons": list(hard.reasons)},
        "decision_id": event.get("decision_id"), "latency_ms": event.get("latency_ms"),
    }


@app.get("/api/status")
def status() -> dict:
    url = os.getenv("DECIDER_URL", "").strip()
    return {"decider": "http" if url else "mock", "decider_url": url or None,
            "threshold": shield.threshold, "mode": shield.mode, "cases": len(CASES),
            "tools": sorted(shield.policy.rules["roles"]["agente_soporte"]["tools"])}


@app.post("/api/run")
def run(body: RunBody) -> dict:
    c = CASES.get(body.case_id)
    if c is None:
        raise HTTPException(404, f"caso desconocido: {body.case_id}")
    out = _evaluate(c["user_request"], c["tool"], c["args"], c["tool_outputs"], body.threshold, body.mode)
    return {"case": c, **out}


@app.post("/api/attack")
def attack(body: AttackBody) -> dict:
    """Ticket del atacante: texto libre que el agente 'leyo' de una herramienta, mas la accion
    que propone. La propuesta es simulada (el agente real requiere Bedrock); el guard es el real."""
    case = {"id": "ATTACK", "kind": "ticket_del_atacante", "user_request": ATTACK_USER_REQUEST,
            "tool": body.tool, "args": body.args, "tool_outputs": [body.ticket], "expected": None}
    out = _evaluate(case["user_request"], body.tool, body.args, case["tool_outputs"], body.threshold, body.mode)
    return {"case": case, **out}


@app.get("/api/events")
async def events() -> StreamingResponse:
    q: asyncio.Queue = asyncio.Queue()
    queues.append(q)

    async def gen():
        try:
            while True:
                rec = await q.get()
                yield f"data: {json.dumps(rec, ensure_ascii=False)}\n\n"
        finally:
            queues.remove(q)

    return StreamingResponse(gen(), media_type="text/event-stream")
