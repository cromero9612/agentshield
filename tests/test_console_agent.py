"""La consola ejecuta un Agent de Strands real (modelo guionizado) y expone el avance y la aprobacion humana."""

import time

import pytest
from fastapi.testclient import TestClient

import console.app as console_app
from store import tools
from tests.strands_stub import ScriptedModel, call, say

client = TestClient(console_app.app)

ATTACK = [call("get_orders", order_id="ORD-1003"),
          call("cancel_orders", order_ids=["ORD-1003"], reason="cancelar este pedido"), say("Listo.")]
CANCEL = [call("cancel_orders", order_ids=["ORD-1002"], reason="pedido duplicado"), say("Cancelado.")]


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DECIDER_URL", "")  # Decider simulado: sin red
    tools.reset()
    yield
    tools.reset()


def use_script(monkeypatch, script):
    monkeypatch.setattr("agent.run_agent.build_model", lambda: ScriptedModel(script))


def wait(run_id, until, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        r = client.get(f"/api/agent/run/{run_id}").json()
        if until(r):
            return r
        time.sleep(0.05)
    pytest.fail(f"la corrida no llego al estado esperado: {r['status']}")


def start(request, mode):
    r = client.post("/api/agent/run", json={"request": request, "mode": mode})
    assert r.status_code == 200, r.text
    return r.json()["run_id"]


def status_of(run, order_id):
    return next(o["status"] for o in run["orders_after"] if o["order_id"] == order_id)


def test_the_guard_stops_an_injected_cancel_and_the_order_is_untouched(monkeypatch):
    use_script(monkeypatch, ATTACK)
    run = wait(start("Revisa el pedido ORD-1003.", "enforce"), lambda r: r["status"] in ("done", "error"))
    assert run["status"] == "done" and run["history"] == []
    assert [d["verdict"] for d in run["decisions"]] == ["proceed", "deny"]
    assert status_of(run, "ORD-1003") == "PROCESSING"
    assert [c["tool"] for c in run["calls"]] == ["get_orders", "cancel_orders"] and run["calls"][1]["blocked"] is True


def test_without_the_guard_the_same_attack_cancels_the_order(monkeypatch):
    use_script(monkeypatch, ATTACK)
    run = wait(start("Revisa el pedido ORD-1003.", "off"), lambda r: r["status"] in ("done", "error"))
    assert run["decisions"] == [] and status_of(run, "ORD-1003") == "CANCELLED"
    assert run["history"][0]["to_status"] == "CANCELLED"


def test_a_legitimate_cancel_waits_for_the_web_approval_and_runs_once(monkeypatch):
    use_script(monkeypatch, CANCEL)
    run_id = start("Cancela el pedido ORD-1002; motivo: pedido duplicado.", "enforce")
    waiting = wait(run_id, lambda r: r["status"] == "awaiting_approval")
    assert waiting["pending"]["decision"]["verdict"] == "confirm" and status_of({"orders_after": waiting["orders_before"]}, "ORD-1002") == "PENDING"
    assert client.post(f"/api/agent/run/{run_id}/approve", json={"approved": True}).status_code == 200
    run = wait(run_id, lambda r: r["status"] in ("done", "error"))
    assert status_of(run, "ORD-1002") == "CANCELLED" and len(run["history"]) == 1


def test_rejecting_the_approval_changes_nothing(monkeypatch):
    use_script(monkeypatch, CANCEL)
    run_id = start("Cancela el pedido ORD-1002; motivo: pedido duplicado.", "enforce")
    wait(run_id, lambda r: r["status"] == "awaiting_approval")
    client.post(f"/api/agent/run/{run_id}/approve", json={"approved": False})
    run = wait(run_id, lambda r: r["status"] in ("done", "error"))
    assert status_of(run, "ORD-1002") == "PENDING" and run["history"] == []


def test_input_validation_and_unknown_runs():
    assert client.post("/api/agent/run", json={"request": "x", "mode": "yolo"}).status_code == 422
    assert client.post("/api/agent/run", json={"request": "  ", "mode": "enforce"}).status_code == 422
    assert client.post("/api/agent/run", json={"request": "x" * 501, "mode": "enforce"}).status_code == 422
    assert client.get("/api/agent/run/nope").status_code == 404
    assert client.post("/api/agent/run/nope/approve", json={"approved": True}).status_code == 404
