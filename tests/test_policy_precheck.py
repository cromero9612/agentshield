import json

import pytest

from agentshield.audit import AuditLog
from agentshield.combine import GuardAnswers
from agentshield.guard import Shield
from bench.run_bench import load_cases


class SpyDecider:
    def __init__(self, error=None):
        self.error = error
        self.states = []

    def ask(self, state):
        self.states.append(state)
        if self.error:
            raise self.error
        return GuardAnswers(0.95, 0.95, 0.0, 0.0, latency_ms=12.5)


@pytest.mark.parametrize("tool,args,role", [
    ("delete_orders", {"order_id": "ORD-1001"}, "agente_soporte"),
    ("get_orders", {"order_id": "ORD-1001"}, "sin_permisos"),
    ("cancel_orders", {"order_ids": ["ORD-1002"], "reason": "duplicado"}, "viewer"),
    ("issue_refund", {"order_id": "ORD-1001", "amount": 20000}, "agente_soporte"),
])
@pytest.mark.parametrize("unavailable", [False, True], ids=["available", "unavailable"])
def test_hard_deny_is_audited_without_invoking_decider(tmp_path, tool, args, role, unavailable):
    decider = SpyDecider(TimeoutError("sin respuesta") if unavailable else None)
    path = tmp_path / "audit.jsonl"
    shield = Shield(decider=decider, audit=AuditLog(path))

    verdict = shield.evaluate("Operacion de prueba", tool, args, role=role)

    assert verdict.action == "deny" and verdict.reason.startswith("regla dura:")
    assert decider.states == []
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(events) == 1
    event = events[0]
    assert event["verdict"] == "deny" and event["hard"]["verdict"] == "deny"
    assert event["hard"]["reasons"] and event["reason"] == verdict.reason
    assert event["decision_id"] and event["latency_ms"] is None
    assert event["answers"] == {"grounded": None, "intent": None, "injected": None,
                                "blast": None, "threshold": 0.9}


def test_hard_deny_does_not_build_model_state(tmp_path, monkeypatch):
    def forbidden_state(*args, **kwargs):
        pytest.fail("No debe construirse contexto para una herramienta denegada")

    monkeypatch.setattr("agentshield.guard.render_state", forbidden_state)
    decider = SpyDecider()
    shield = Shield(decider=decider, audit=AuditLog(tmp_path / "audit.jsonl"))
    assert shield.evaluate("x", "delete_orders", {}).action == "deny"
    assert decider.states == []


@pytest.mark.parametrize("tool,args,expected", [
    ("get_orders", {"order_id": "ORD-1001"}, "proceed"),
    ("cancel_orders", {"order_ids": ["ORD-1002"], "reason": "duplicado"}, "confirm"),
])
def test_allowed_proposals_still_invoke_decider_once(tmp_path, tool, args, expected):
    decider = SpyDecider()
    path = tmp_path / "audit.jsonl"
    shield = Shield(decider=decider, audit=AuditLog(path))

    verdict = shield.evaluate("Operacion autorizada", tool, args)

    assert verdict.action == expected and len(decider.states) == 1
    assert decider.states[0]["proposed_tool_call"] == {"name": tool, "arguments": args}
    event = json.loads(path.read_text(encoding="utf-8"))
    assert event["answers"]["grounded"] == 0.95 and event["latency_ms"] == 12.5


def test_decider_failure_for_allowed_tool_still_denies_and_audits(tmp_path):
    decider = SpyDecider(TimeoutError("sin respuesta"))
    path = tmp_path / "audit.jsonl"
    shield = Shield(decider=decider, audit=AuditLog(path))

    verdict = shield.evaluate("Consulta ORD-1001", "get_orders", {"order_id": "ORD-1001"})

    assert verdict.action == "deny" and "TimeoutError" in verdict.reason
    assert len(decider.states) == 1
    event = json.loads(path.read_text(encoding="utf-8"))
    assert event["hard"]["verdict"] == "proceed" and event["latency_ms"] is None


def test_benchmark_policy_variants_do_not_invoke_decider(tmp_path):
    variants = [(case, variant) for case in load_cases() for variant in case.get("policy_variants", [])]
    assert variants, "El corpus debe documentar la denegacion determinista sin inferencia"
    for index, (case, variant) in enumerate(variants):
        decider = SpyDecider()
        shield = Shield(decider=decider, audit=AuditLog(tmp_path / f"variant-{index}.jsonl"))
        verdict = shield.evaluate(case["user_request"], case["tool"], case["args"], case["tool_outputs"],
                                  role=variant["role"])
        assert verdict.action == variant["expected"]
        assert len(decider.states) == variant["expected_decider_calls"]
