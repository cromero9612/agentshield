"""Registro de auditoria + bus de eventos para la consola.

MVP: archivo JSONL local. El dia 4, la Persona C puede cambiar `write` para
mandar tambien a DynamoDB sin tocar el resto del codigo.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Nombres normalizados: se ignoran mayusculas, guiones y separadores.
MASKED_KEYS = {"account", "card"}
CREDENTIAL_KEYS = {
    "password", "passwd", "pwd", "token", "accesstoken", "refreshtoken", "idtoken", "authtoken", "apitoken",
    "authorization", "proxyauthorization", "apikey", "xapikey", "secret", "clientsecret", "apisecret",
    "awsaccesskeyid", "awssecretaccesskey", "awssessiontoken", "privatekey",
}
SENSITIVE_KEYS = MASKED_KEYS | CREDENTIAL_KEYS
REDACTED = "[REDACTED]"


def _minimize(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            normalized = "".join(c for c in key.casefold() if c.isalnum()) if isinstance(key, str) else ""
            if normalized in CREDENTIAL_KEYS:
                out[key] = REDACTED
            elif normalized in MASKED_KEYS and item not in (None, ""):
                if isinstance(item, (str, int, float)) and not isinstance(item, bool):
                    text = str(item)
                    out[key] = "***" + text[-4:] if len(text) > 4 else "***"
                else:
                    out[key] = REDACTED
            else:
                out[key] = _minimize(item)
        return out
    if isinstance(value, list):
        return [_minimize(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_minimize(item) for item in value)
    return value


def minimize(args: dict) -> dict:
    """Copia y redacta campos sensibles anidados; no detecta secretos dentro de texto libre."""
    return _minimize(args)


class AuditLog:
    def __init__(self, path: str | Path = "audit.jsonl"):
        self.path = Path(path)
        self.listeners: list[Callable[[dict], None]] = []

    def subscribe(self, fn: Callable[[dict], None]) -> None:
        self.listeners.append(fn)

    def write(self, record: dict) -> None:
        record = minimize({**record, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        for fn in self.listeners:
            fn(record)
