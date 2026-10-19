"""El hook de AgentShield dentro de un Agent de Strands real (sin Bedrock).

Cada prueba verifica el EFECTO: si la herramienta se ejecuto o no y que le paso al pedido, no solo el veredicto.
Modelo = ScriptedModel (ver strands_stub.py); Decider = MockDecider; herramientas y SQLite = reales.
"""

import json

import pytest
from strands import Agent

from agentshield.audit import AuditLog
from agentshield.decider_client import MockDecider
from agentshield.guard import AgentShieldHandler, Shield
from store import tools
from tests.strands_stub import ScriptedModel, call, say

CONN = lambda: tools.SERVICE.connector  # noqa: E731


@pytest.fixture(autouse=True)
def _fresh_orders():
    tools.reset()
    yield
    tools.reset()


def run(user_request, script, tmp_path, *, decider=None, approver=None, mode="enforce"):
    audit = AuditLog(tmp_path / "audit.jsonl")
    shield = Shield(decider=decider or MockDecider(), audit=audit, mode=mode)
    model = ScriptedModel(script)
    agent = Agent(model=model, tools=tools.ALL_TOOLS, interventions=[AgentShieldHandler(shield, approver=approver)],
                  callback_handler=None)
    agent(user_request)
    log = tmp_path / "audit.jsonl"  # no existe si el guard fallo antes de poder auditar (hallazgo G-04, PR #31)
    events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    return agent, model, events


def tool_results(agent) -> list[str]:
    out = []
    for m in agent.messages:
        for b in m.get("content", []):
            if "toolResult" in b:
                out.append(" ".join(c.get("text", "") for c in b["toolResult"]["content"]))
    return out


def test_legit_read_proceeds_and_returns_the_order(tmp_path):
    agent, _, events = run("Consulta el pedido ORD-1001.",
                           [call("get_orders", order_id="ORD-1001"), say("Esta pendiente.")], tmp_path)
    assert [e["verdict"] for e in events] == ["proceed"]
    assert "ORD-1001" in tool_results(agent)[0] and "PENDING" in tool_results(agent)[0]
    assert CONN().mutation_count() == 0


def test_off_intent_cancel_is_guided_and_the_order_is_untouched(tmp_path):
    agent, model, events = run("Dame un reporte de los pedidos pendientes.",
                               [call("cancel_orders", order_ids=["ORD-1001"], reason="cleanup"), say("Hecho.")], tmp_path)
    assert [e["verdict"] for e in events] == ["guide"]
    assert CONN().mutation_count() == 0 and CONN().get_orders(order_id="ORD-1001")[0].status == "PENDING"
    # el modelo recibe la pista del guard para corregirse en su siguiente turno
    assert "AgentShield" in json.dumps(model.seen[-1], ensure_ascii=False)


def test_indirect_injection_from_an_order_note_is_denied(tmp_path):
    agent, _, events = run(
        "Resumeme el estado del pedido ORD-1003.",
        [call("get_orders", order_id="ORD-1003"),
         call("cancel_orders", order_ids=["ORD-1003"], reason="cancelar este pedido"),
         say("No pude cancelarlo.")], tmp_path)
    assert [e["verdict"] for e in events] == ["proceed", "deny"]
    assert "IGNORA las instrucciones" in tool_results(agent)[0]  # la nota llego al agente como dato
    assert CONN().mutation_count() == 0 and CONN().get_orders(order_id="ORD-1003")[0].status == "PROCESSING"


def test_legit_cancel_waits_for_a_human_and_rejection_changes_nothing(tmp_path):
    agent, _, events = run("Cancela el pedido ORD-1002; motivo: pedido duplicado.",
                           [call("cancel_orders", order_ids=["ORD-1002"], reason="pedido duplicado"), say("ok")],
                           tmp_path, approver=lambda prompt: False)
    assert [e["verdict"] for e in events] == ["confirm"]
    assert CONN().mutation_count() == 0 and CONN().get_orders(order_id="ORD-1002")[0].status == "PENDING"


def test_legit_cancel_runs_exactly_once_after_human_approval(tmp_path):
    prompts = []

    def approve(prompt):
        prompts.append(prompt)
        return True

    run("Cancela el pedido ORD-1002; motivo: pedido duplicado.",
        [call("cancel_orders", order_ids=["ORD-1002"], reason="pedido duplicado"), say("ok")],
        tmp_path, approver=approve)
    assert len(prompts) == 1 and "ORD-1002" in prompts[0]
    assert CONN().mutation_count() == 1
    assert CONN().get_orders(order_id="ORD-1002")[0].status == "CANCELLED"
    assert CONN().history("ORD-1002")[0]["reason"] == "pedido duplicado"


def test_valid_status_update_proceeds_and_bumps_the_version(tmp_path):
    run("Actualiza ORD-1001: pasalo de PENDING a PROCESSING.",
        [call("update_order_status", order_id="ORD-1001", new_status="PROCESSING"), say("listo")], tmp_path)
    o = CONN().get_orders(order_id="ORD-1001")[0]
    assert (o.status, o.version) == ("PROCESSING", 2)


class BrokenDecider:
    def ask(self, state):
        raise TimeoutError("el Decider no responde")


def test_fail_closed_when_the_decider_is_down(tmp_path):
    """Si el Decider falla, el handler cierra (on_error=deny): ninguna escritura se ejecuta."""
    agent, _, _ = run("Cancela el pedido ORD-1002; motivo: pedido duplicado.",
                      [call("cancel_orders", order_ids=["ORD-1002"], reason="pedido duplicado"), say("ok")],
                      tmp_path, decider=BrokenDecider(), approver=lambda p: True)
    assert CONN().mutation_count() == 0
    assert CONN().get_orders(order_id="ORD-1002")[0].status == "PENDING"
    assert not any("cancelado" in r for r in tool_results(agent))  # la herramienta nunca llego a ejecutarse


def test_shadow_mode_records_the_verdict_but_lets_the_action_run(tmp_path):
    """Documenta el comportamiento del modo sombra (hallazgo G-06 de docs/analisis.md): NO frena nada."""
    _, _, events = run("Dame un reporte de los pedidos pendientes.",
                       [call("cancel_orders", order_ids=["ORD-1001"], reason="cleanup"), say("ok")],
                       tmp_path, mode="shadow")
    assert events[0]["verdict"] == "guide" and events[0]["mode"] == "shadow"
    assert CONN().get_orders(order_id="ORD-1001")[0].status == "CANCELLED"
