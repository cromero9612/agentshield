"""Agente de soporte de ElectroNova con AgentShield. Responsable: Persona B.

Uso:
    python -m agent.run_agent "Resumeme los tickets que entraron hoy"
    python -m agent.run_agent --shadow "..."      # solo registra, no bloquea
    python -m agent.run_agent --no-shield "..."   # para el video: que haria sin guard

Requiere credenciales de AWS con acceso a Bedrock (aws configure o variables de entorno).
"""

from __future__ import annotations

import argparse
import os

from strands import Agent
from strands.models import BedrockModel

from agentshield import AgentShieldHandler, Shield
from store.tools import ALL_TOOLS, DB, SENT_EMAILS

SYSTEM_PROMPT = (
    "Eres el agente de soporte interno de ElectroNova, una tienda de electronica. "
    "Ayudas a empleados con pedidos, inventario, clientes y tickets. "
    "Usa las herramientas disponibles para completar lo que te piden."
)


def build_agent(shield_mode: str | None = "enforce", threshold: float = 0.9) -> Agent:
    model = BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
    interventions = []
    if shield_mode:
        shield = Shield(threshold=threshold, mode=shield_mode)
        interventions.append(AgentShieldHandler(shield, approver=_cli_approver))
    return Agent(model=model, tools=ALL_TOOLS, system_prompt=SYSTEM_PROMPT, interventions=interventions)


def _cli_approver(prompt: str) -> bool:
    return input(f"\n{prompt}\n¿Aprobar? (s/n) ").strip().lower() in {"s", "si", "sí", "y", "yes"}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("request")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--shadow", action="store_true")
    g.add_argument("--no-shield", action="store_true")
    p.add_argument("--threshold", type=float, default=0.9)
    a = p.parse_args()
    mode = None if a.no_shield else ("shadow" if a.shadow else "enforce")
    agent = build_agent(mode, a.threshold)
    agent(a.request)
    print("\n--- Estado final ---")
    print("Reembolsos:", DB["refunds"])
    print("Correos:", SENT_EMAILS)


if __name__ == "__main__":
    main()
