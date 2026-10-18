"""Consola de AgentShield. Responsable: Persona C.

    uvicorn console.app:app --reload --port 8080   ->   http://localhost:8080

Version inicial: reproduce los casos de bench/cases.jsonl contra el guard y
transmite cada decision por SSE. Funciona sin AWS (Decider mock). El dia 4 se
conecta al agente real.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from agentshield.audit import AuditLog
from agentshield.guard import Shield
from bench.run_bench import load_cases

app = FastAPI(title="AgentShield console")
STATIC = Path(__file__).parent / "static"
queues: list[asyncio.Queue] = []
loop: asyncio.AbstractEventLoop | None = None


def _broadcast(record: dict) -> None:
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


@app.post("/api/run")
def run(body: RunBody) -> dict:
    c = CASES[body.case_id]
    shield.threshold = body.threshold
    v = shield.evaluate(c["user_request"], c["tool"], c["args"], c["tool_outputs"])
    return {"case": c, "verdict": v.action, "reason": v.reason, "hint": v.hint, "checks": v.checks}


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
