"""Puerto de pedidos: el contrato unico que cumplen todos los backends (mock y REST).

El guard y las herramientas dependen de este modulo, nunca de un backend concreto.
Datos ficticios de ElectroNova. Responsable: Persona B.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol

STATUSES = ("PENDING", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED")
# Unico camino valido de avance. CANCELLED solo se alcanza con cancel_order (requiere aprobacion).
NEXT_STATUS = {"PENDING": "PROCESSING", "PROCESSING": "SHIPPED", "SHIPPED": "DELIVERED"}
CANCELLABLE = frozenset({"PENDING", "PROCESSING"})


class OrderError(Exception):
    """Error de negocio con un codigo estable (sirve para auditoria y para el agente)."""

    code = "order_error"


class InvalidRequest(OrderError):
    code = "invalid_request"


class OrderNotFound(OrderError):
    code = "not_found"


class InvalidTransition(OrderError):
    code = "invalid_transition"


class NotCancellable(OrderError):
    code = "not_cancellable"


class VersionConflict(OrderError):
    code = "version_conflict"


@dataclass(frozen=True)
class Order:
    order_id: str
    customer_alias: str
    organization_id: str
    status: str
    version: int
    source_system: str
    customer_note: str | None = None  # texto NO confiable: puede traer instrucciones (inyeccion indirecta)

    def to_dict(self) -> dict:
        d = asdict(self)
        if d["customer_note"] is None:
            del d["customer_note"]
        return d


class OrderConnectorPort(Protocol):
    """Operaciones canonicas. Toda mutacion incrementa `version` y puede exigir la version esperada."""

    connector_id: str

    def get_orders(self, order_id: str | None = None, status: str | None = None,
                   limit: int = 10) -> list[Order]: ...

    def update_order_status(self, order_id: str, new_status: str,
                            expected_version: int | None = None) -> Order: ...

    def cancel_order(self, order_id: str, reason: str,
                     expected_version: int | None = None) -> Order: ...
