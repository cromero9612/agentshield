"""Registro de auditoria + bus de eventos para la consola.

MVP: archivo JSONL local. El dia 4, la Persona C puede cambiar `write` para
mandar tambien a DynamoDB sin tocar el resto del codigo.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path

# Nunca escribir estos campos completos en la auditoria.
SENSITIVE_KEYS = {"account", "card", "password", "token"}


def minimize(args: dict) -> dict:
    out = {}
    for k, v in args.items():
        if k in SENSITIVE_KEYS and v:
            s = str(v)
            out[k] = "***" + s[-4:]
        else:
            out[k] = v
    return out


class AuditLog:
    def __init__(self, path: str | Path = "audit.jsonl"):
        self.path = Path(path)
        self.listeners: list[Callable[[dict], None]] = []

    def subscribe(self, fn: Callable[[dict], None]) -> None:
        self.listeners.append(fn)

    def write(self, record: dict) -> None:
        record = {**record, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        if "args" in record:
            record["args"] = minimize(record["args"])
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        for fn in self.listeners:
            fn(record)
