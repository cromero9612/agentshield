"""Backend simulado de pedidos sobre SQLite (en memoria por defecto). Responsable: Persona B."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path

from .base import (CANCELLABLE, NEXT_STATUS, InvalidTransition, NotCancellable, Order,
                   OrderNotFound, VersionConflict)

SEED = Path(__file__).resolve().parent.parent / "orders_seed.json"

_SCHEMA = """
CREATE TABLE orders (order_id TEXT PRIMARY KEY, customer_alias TEXT NOT NULL, organization_id TEXT NOT NULL,
  status TEXT NOT NULL, version INTEGER NOT NULL, source_system TEXT NOT NULL, customer_note TEXT);
CREATE TABLE history (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT NOT NULL, from_status TEXT NOT NULL,
  to_status TEXT NOT NULL, reason TEXT, at TEXT NOT NULL);
"""


class MockOrderConnector:
    connector_id = "mock"

    def __init__(self, db_path: str = ":memory:", seed: Path = SEED):
        self._seed = Path(seed)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self.reset()

    def reset(self) -> None:
        """Vuelve al seed. Es solo para pruebas y demos; no hay endpoint publico que lo llame."""
        data = json.loads(self._seed.read_text(encoding="utf-8"))
        with self._lock, self._conn:
            self._conn.executescript("DROP TABLE IF EXISTS orders; DROP TABLE IF EXISTS history;" + _SCHEMA)
            self._conn.executemany(
                "INSERT INTO orders VALUES (?,?,?,?,1,'mock',?)",
                [(o["order_id"], o["customer_alias"], data["organization_id"], o["status"], o.get("customer_note"))
                 for o in data["orders"]])

    # -- lectura ---------------------------------------------------------------------------------
    @staticmethod
    def _order(row: sqlite3.Row) -> Order:
        return Order(**{k: row[k] for k in row.keys()})

    def get_orders(self, order_id: str | None = None, status: str | None = None, limit: int = 10) -> list[Order]:
        sql, args = "SELECT * FROM orders WHERE 1=1", []
        if order_id:
            sql += " AND order_id = ?"; args.append(order_id)
        if status:
            sql += " AND status = ?"; args.append(status)
        with self._lock:
            rows = self._conn.execute(sql + " ORDER BY order_id LIMIT ?", [*args, limit]).fetchall()
        return [self._order(r) for r in rows]

    # -- escritura -------------------------------------------------------------------------------
    def _get_for_update(self, order_id: str, expected_version: int | None) -> Order:
        rows = self.get_orders(order_id=order_id, limit=1)
        if not rows:
            raise OrderNotFound(f"el pedido {order_id} no existe")
        if expected_version is not None and rows[0].version != expected_version:
            raise VersionConflict(f"{order_id} cambio: version {rows[0].version}, se esperaba {expected_version}")
        return rows[0]

    def _write(self, order: Order, to_status: str, reason: str | None) -> Order:
        with self._conn:
            cur = self._conn.execute(
                "UPDATE orders SET status=?, version=version+1 WHERE order_id=? AND version=?",
                (to_status, order.order_id, order.version))
            if cur.rowcount != 1:  # otro cambio llego primero
                raise VersionConflict(f"{order.order_id} cambio mientras se actualizaba")
            self._conn.execute("INSERT INTO history (order_id, from_status, to_status, reason, at) VALUES (?,?,?,?,?)",
                               (order.order_id, order.status, to_status, reason, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
        return self.get_orders(order_id=order.order_id, limit=1)[0]

    def update_order_status(self, order_id: str, new_status: str, expected_version: int | None = None) -> Order:
        with self._lock:
            order = self._get_for_update(order_id, expected_version)
            if NEXT_STATUS.get(order.status) != new_status:
                allowed = NEXT_STATUS.get(order.status)
                raise InvalidTransition(
                    f"{order_id} esta en {order.status}; "
                    + (f"solo puede pasar a {allowed}" if allowed else "ya no admite cambios de estado"))
            return self._write(order, new_status, None)

    def cancel_order(self, order_id: str, reason: str, expected_version: int | None = None) -> Order:
        with self._lock:
            order = self._get_for_update(order_id, expected_version)
            if order.status not in CANCELLABLE:
                raise NotCancellable(f"{order_id} esta en {order.status}; solo se cancela desde PENDING o PROCESSING")
            return self._write(order, "CANCELLED", reason)

    # -- evidencia (pruebas y demo antes/despues) -------------------------------------------------
    def mutation_count(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]

    def history(self, order_id: str | None = None) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT order_id, from_status, to_status, reason, at FROM history"
                + (" WHERE order_id=?" if order_id else "") + " ORDER BY id", [order_id] if order_id else []).fetchall()
        return [dict(r) for r in rows]

    def snapshot(self) -> dict[str, tuple[str, int]]:
        return {o.order_id: (o.status, o.version) for o in self.get_orders(limit=1000)}
