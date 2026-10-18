"""Herramientas simuladas de ElectroNova (empresa ficticia). Responsable: Persona B.

Nada de esto toca sistemas reales: todo vive en memoria y se reinicia con reset().
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from strands import tool

_SEED = json.loads((Path(__file__).parent / "data.json").read_text(encoding="utf-8"))
DB: dict = {}
SENT_EMAILS: list[dict] = []


def reset() -> None:
    DB.clear()
    DB.update(copy.deepcopy(_SEED))
    SENT_EMAILS.clear()


reset()


@tool
def get_inventory(sku: str, store: str) -> str:
    """Consulta cuantas unidades de un producto hay en una tienda."""
    qty = DB["inventory"].get(store, {}).get(sku)
    return f"{sku} en {store}: {qty} unidades" if qty is not None else "Producto o tienda no encontrados"


@tool
def get_orders(status: str = "", week: int = 0) -> str:
    """Lista pedidos, opcionalmente filtrados por estado (delayed, paid, shipped)."""
    rows = [o for o in DB["orders"] if not status or o["status"] == status]
    return json.dumps(rows, ensure_ascii=False)


@tool
def get_tickets() -> str:
    """Devuelve los tickets de soporte que entraron hoy (texto libre de clientes)."""
    return "\n".join(f"Ticket #{t['id']}: {t['text']}" for t in DB["tickets"])


@tool
def update_customer(customer_id: str, phone: str) -> str:
    """Actualiza el telefono de un cliente."""
    c = DB["customers"].get(customer_id)
    if not c:
        return "Cliente no encontrado"
    c["phone"] = phone
    return f"Telefono de {customer_id} actualizado"


@tool
def update_order_amount(order_id: str, amount: float) -> str:
    """Cambia el monto total de un pedido."""
    for o in DB["orders"]:
        if o["id"] == order_id:
            o["amount"] = amount
            return f"Pedido {order_id} ahora cuesta Q{amount}"
    return "Pedido no encontrado"


@tool
def cancel_orders(status: str) -> str:
    """Cancela todos los pedidos con el estado indicado."""
    n = 0
    for o in DB["orders"]:
        if o["status"] == status:
            o["status"] = "cancelled"
            n += 1
    return f"{n} pedidos cancelados"


@tool
def issue_refund(order_id: str, amount: float, account: str) -> str:
    """Emite un reembolso a una cuenta bancaria."""
    DB["refunds"].append({"order_id": order_id, "amount": amount, "account": account})
    return f"Reembolso de Q{amount} enviado"


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Envia un correo."""
    SENT_EMAILS.append({"to": to, "subject": subject})
    return f"Correo enviado a {to}"


ALL_TOOLS = [get_inventory, get_orders, get_tickets, update_customer,
             update_order_amount, cancel_orders, issue_refund, send_email]
