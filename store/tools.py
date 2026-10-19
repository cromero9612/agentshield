"""Herramientas de pedidos de ElectroNova (empresa ficticia). Responsable: Persona B.

Catalogo de entrega: exactamente tres herramientas (ver docs/integracion.md). Cada una solo traduce entre texto y
`OrderService`; no hay datos ni reglas de negocio aqui. Los errores de negocio se devuelven como texto para que el
agente pueda corregir, nunca como excepcion.
"""

from __future__ import annotations

import json
from typing import Optional

from strands import tool

from .connectors.base import OrderError
from .connectors.mock import MockOrderConnector
from .orders import OrderService

SERVICE = OrderService(MockOrderConnector())


def reset() -> None:
    """Restaura los pedidos al seed (pruebas y demo)."""
    SERVICE.connector.reset()


def _error(e: OrderError) -> str:
    return f"Error [{e.code}]: {e}"


@tool
def get_orders(order_id: Optional[str] = None, status: Optional[str] = None, limit: int = 10) -> str:
    """Consulta pedidos (maximo 10). Filtra por order_id (ORD-0000) y/o por estado
    (PENDING, PROCESSING, SHIPPED, DELIVERED, CANCELLED)."""
    try:
        rows = SERVICE.get_orders(order_id=order_id, status=status, limit=limit)
    except OrderError as e:
        return _error(e)
    return json.dumps([o.to_dict() for o in rows], ensure_ascii=False) if rows else "No hay pedidos que coincidan"


@tool
def update_order_status(order_id: str, new_status: str) -> str:
    """Avanza un pedido a su siguiente estado (PENDING->PROCESSING->SHIPPED->DELIVERED). No cancela."""
    try:
        o = SERVICE.update_order_status(order_id, new_status)
    except OrderError as e:
        return _error(e)
    return f"Pedido {o.order_id} ahora esta en {o.status} (version {o.version})"


@tool
def cancel_orders(order_ids: list[str], reason: str) -> str:
    """Cancela un pedido PENDING o PROCESSING. Recibe una lista con exactamente un order_id y el motivo."""
    try:
        o = SERVICE.cancel_orders(order_ids, reason)
    except OrderError as e:
        return _error(e)
    return f"Pedido {o.order_id} cancelado (version {o.version})"


ALL_TOOLS = [get_orders, update_order_status, cancel_orders]
