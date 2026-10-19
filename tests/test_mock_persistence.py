import json
import sqlite3

import pytest

from store.connectors.mock import MockOrderConnector, SEED


@pytest.fixture
def open_connector():
    connections = []

    def connect(*args, **kwargs):
        connector = MockOrderConnector(*args, **kwargs)
        connections.append(connector)
        return connector

    yield connect
    for connector in connections:
        connector._conn.close()


def test_new_file_initializes_orders_and_empty_history(tmp_path, open_connector):
    connector = open_connector(str(tmp_path / "orders.sqlite"))
    assert len(connector.get_orders()) == 10
    assert connector.snapshot()["ORD-1002"] == ("PENDING", 1)
    assert connector.history() == []


def test_reopen_preserves_orders_versions_and_history(tmp_path, open_connector):
    path = str(tmp_path / "orders.sqlite")
    original = open_connector(path)
    original.update_order_status("ORD-1001", "PROCESSING")
    original.cancel_order("ORD-1002", "pedido duplicado")
    before, history = original.snapshot(), original.history()
    original._conn.close()

    reopened = open_connector(path)
    assert reopened.snapshot() == before
    assert reopened.history() == history
    assert reopened.mutation_count() == 2
    assert reopened.snapshot()["ORD-1002"] == ("CANCELLED", 2)


def test_second_connection_does_not_reset_active_database(tmp_path, open_connector):
    path = str(tmp_path / "orders.sqlite")
    original = open_connector(path)
    original.cancel_order("ORD-1002", "duplicado")

    second = open_connector(path)
    assert original.snapshot() == second.snapshot()
    assert second.snapshot()["ORD-1002"] == ("CANCELLED", 2)
    assert second.mutation_count() == 1


def test_existing_database_does_not_require_seed_file(tmp_path, open_connector):
    path = str(tmp_path / "orders.sqlite")
    original = open_connector(path)
    original.cancel_order("ORD-1002", "duplicado")

    reopened = open_connector(path, seed=tmp_path / "missing-seed.json")
    assert reopened.snapshot() == original.snapshot()
    assert reopened.mutation_count() == 1


def test_existing_empty_database_is_not_reseeded(tmp_path, open_connector):
    path = str(tmp_path / "orders.sqlite")
    original = open_connector(path)
    with original._conn:
        original._conn.execute("DELETE FROM orders")

    reopened = open_connector(path)
    assert reopened.get_orders() == []


@pytest.mark.parametrize("in_memory", [False, True], ids=["file", "memory"])
def test_explicit_reset_restores_seed_and_clears_history(tmp_path, open_connector, in_memory):
    path = ":memory:" if in_memory else str(tmp_path / "orders.sqlite")
    connector = open_connector(path)
    seed_snapshot = connector.snapshot()
    connector.cancel_order("ORD-1002", "duplicado")
    connector.update_order_status("ORD-1001", "PROCESSING")

    connector.reset()
    assert connector.snapshot() == seed_snapshot
    assert connector.history() == []
    assert connector.mutation_count() == 0
    if not in_memory:
        assert open_connector(path).snapshot() == seed_snapshot


def test_failed_reset_preserves_existing_data(tmp_path, open_connector):
    path = str(tmp_path / "orders.sqlite")
    original = open_connector(path)
    original.cancel_order("ORD-1002", "duplicado")
    before, history = original.snapshot(), original.history()
    invalid_seed = json.loads(SEED.read_text(encoding="utf-8"))
    invalid_seed["orders"].append(invalid_seed["orders"][0])
    seed_path = tmp_path / "duplicate-orders.json"
    seed_path.write_text(json.dumps(invalid_seed), encoding="utf-8")

    reopened = open_connector(path, seed=seed_path)
    with pytest.raises(sqlite3.IntegrityError):
        reopened.reset()
    assert reopened.snapshot() == before
    assert reopened.history() == history


def test_failed_initialization_can_be_retried_without_partial_tables(tmp_path, open_connector):
    path = str(tmp_path / "orders.sqlite")
    invalid_seed = json.loads(SEED.read_text(encoding="utf-8"))
    invalid_seed["orders"].append(invalid_seed["orders"][0])
    seed_path = tmp_path / "duplicate-orders.json"
    seed_path.write_text(json.dumps(invalid_seed), encoding="utf-8")

    with pytest.raises(sqlite3.IntegrityError):
        open_connector(path, seed=seed_path)

    recovered = open_connector(path)
    assert len(recovered.get_orders()) == 10
    assert recovered.history() == []


def test_incomplete_schema_is_rejected_without_overwriting_data(tmp_path, open_connector):
    path = str(tmp_path / "orders.sqlite")
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE orders (order_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO orders VALUES ('ORD-1001')")

    with pytest.raises(sqlite3.DatabaseError, match="esquema de pedidos incompleto"):
        open_connector(path)

    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT * FROM orders").fetchall() == [("ORD-1001",)]
        assert connection.execute("SELECT name FROM sqlite_master WHERE name='history'").fetchall() == []
