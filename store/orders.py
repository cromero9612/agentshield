"""Servicio de pedidos: unico lugar donde se validan los argumentos de las herramientas.

Las herramientas de Strands solo traducen texto <-> este servicio; el backend (mock o REST) solo guarda datos.
Responsable: Persona B.
"""

from __future__ import annotations

import re

from .connectors.base import (STATUSES, InvalidRequest, Order, OrderConnectorPort)

_ID = re.compile(r"^ORD-\d{4}$")
MAX_LIMIT = 10
MAX_REASON = 200


class OrderService:
    def __init__(self, connector: OrderConnectorPort):
        self.connector = connector

    @staticmethod
    def _check_id(order_id: object) -> str:
        if not isinstance(order_id, str) or not _ID.match(order_id):
            raise InvalidRequest(f"order_id invalido: {order_id!r} (formato ORD-0000)")
        return order_id

    @staticmethod
    def _check_status(status: object) -> str:
        s = status.strip().upper() if isinstance(status, str) else status
        if s not in STATUSES:
            raise InvalidRequest(f"estado invalido: {status!r}; usa uno de {', '.join(STATUSES)}")
        return s

    def get_orders(self, order_id: str | None = None, status: str | None = None, limit: int = MAX_LIMIT) -> list[Order]:
        if order_id is not None:
            self._check_id(order_id)
        if status is not None:
            status = self._check_status(status)
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIMIT:
            raise InvalidRequest(f"limit debe estar entre 1 y {MAX_LIMIT}")
        return self.connector.get_orders(order_id=order_id, status=status, limit=limit)

    def update_order_status(self, order_id: str, new_status: str) -> Order:
        self._check_id(order_id)
        new_status = self._check_status(new_status)
        if new_status == "CANCELLED":
            raise InvalidRequest("para cancelar usa cancel_orders: requiere aprobacion")
        return self.connector.update_order_status(order_id, new_status)

    def cancel_orders(self, order_ids: list[str], reason: str) -> Order:
        if not isinstance(order_ids, list) or len(order_ids) != 1:
            raise InvalidRequest("cancel_orders acepta exactamente un order_id por ejecucion")
        self._check_id(order_ids[0])
        if not isinstance(reason, str) or not reason.strip() or len(reason) > MAX_REASON:
            raise InvalidRequest(f"reason es obligatorio y mide como maximo {MAX_REASON} caracteres")
        return self.connector.cancel_order(order_ids[0], reason.strip())
