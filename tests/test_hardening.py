import math
import os

import pytest

from agentshield.audit import AuditLog
from agentshield.combine import CONFIRM, DENY, GUIDE, PROCEED, GuardAnswers, HardResult, combine
from agentshield.config import load_env
from agentshield.guard import Shield
from agentshield.policy import Policy

OK = HardResult()
CONFIRM_RULE = HardResult(CONFIRM, ("requiere aprobacion",))


def a(g=0.95, i=0.95, inj=0.0, b=0.0):
    return GuardAnswers(grounded=g, intent=i, injected=inj, blast=b)


# G-03: valores invalidos del Decider no pueden terminar en proceed
@pytest.mark.parametrize("bad", [
    GuardAnswers(math.nan, math.nan, math.nan, math.nan),
    GuardAnswers(2, 2, -1, -1),
    GuardAnswers(math.inf, 0.9, 0.0, 0.0),
    GuardAnswers(0.9, 0.9, 0.0, 5.0),
    GuardAnswers("0.9", 0.9, 0.0, 0.0),
    GuardAnswers(True, 0.9, 0.0, 0.0),
    GuardAnswers(None, 0.9, 0.0, 0.0),
])
def test_invalid_answers_are_denied(bad):
    assert combine(bad, OK).action == DENY


@pytest.mark.parametrize("t", [math.nan, 0.0, 0.5, 1.5, -1, None])
def test_invalid_threshold_is_denied(t):
    assert combine(a(), OK, threshold=t).action == DENY


def test_valid_boundary_values_still_work():
    assert combine(a(g=1.0, i=1.0, inj=0.0, b=2.0), OK).action == CONFIRM
    assert combine(a(g=1.0, i=1.0), OK, threshold=1.0).action == PROCEED


# G-02: una regla dura confirm no convierte un guide en confirm
def test_hard_confirm_does_not_turn_guide_into_confirm():
    assert combine(a(i=0.05), CONFIRM_RULE).action == GUIDE
    assert combine(a(g=0.05), CONFIRM_RULE).action == GUIDE


def test_hard_confirm_still_hardens_a_clean_proceed():
    assert combine(a(), CONFIRM_RULE).action == CONFIRM


def test_hard_deny_beats_everything():
    assert combine(a(i=0.05), HardResult(DENY, ("rol",))).action == DENY


# G-01: cancelar siempre pide aprobacion, aunque el Decider sea optimista
def test_cancel_always_needs_approval_with_optimistic_scores():
    hard = Policy().check("cancel_orders", {"status": "delayed"})
    assert hard.verdict == CONFIRM
    assert combine(a(b=0.0), hard).action == CONFIRM


def test_cancel_off_intent_is_guided_not_confirmed():
    hard = Policy().check("cancel_orders", {"status": "delayed"})
    assert combine(a(i=0.04), hard).action == GUIDE


# G-04: si el Decider falla, se niega y queda auditado (sin lanzar excepcion)
class BrokenDecider:
    def ask(self, state):
        raise TimeoutError("sin respuesta")


def test_decider_failure_is_denied_and_audited(tmp_path):
    shield = Shield(decider=BrokenDecider(), audit=AuditLog(tmp_path / "a.jsonl"))
    v = shield.evaluate("Dame un reporte", "get_orders", {"status": "delayed"}, [])
    assert v.action == DENY and "TimeoutError" in v.reason
    assert (tmp_path / "a.jsonl").read_text().count("\n") == 1


def test_decider_failure_keeps_hard_rule_reason(tmp_path):
    shield = Shield(decider=BrokenDecider(), audit=AuditLog(tmp_path / "a.jsonl"))
    v = shield.evaluate("x", "drop_database", {}, [])
    assert v.action == DENY and v.reason.startswith("regla dura")


# G-09: .env se carga y no pisa lo que ya esta en el entorno
def test_load_env_reads_file_without_overriding(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text('# comentario\nAS_TEST_A=uno\nAS_TEST_B="dos"\nAS_TEST_C=tres\n\nlinea sin igual\n')
    monkeypatch.delenv("AS_TEST_A", raising=False)
    monkeypatch.delenv("AS_TEST_B", raising=False)
    monkeypatch.setenv("AS_TEST_C", "ya-definida")
    loaded = load_env(f)
    assert os.environ["AS_TEST_A"] == "uno" and os.environ["AS_TEST_B"] == "dos"
    assert os.environ["AS_TEST_C"] == "ya-definida"
    assert sorted(loaded) == ["AS_TEST_A", "AS_TEST_B"]
    for k in ("AS_TEST_A", "AS_TEST_B"):
        os.environ.pop(k, None)
