"""Wiring: put the guard in the path of ANY Strands agent. The model can be Bedrock, Ollama, or anything Strands supports."""
from strands import Agent
from strands.models import BedrockModel  # or: from strands.models.ollama import OllamaModel

from agentshield import AgentShieldHandler, Shield
from store.tools import ALL_TOOLS  # your own @tool functions go here

shield = Shield()  # thresholds come from policies/default.yaml (decider.thresholds)
agent = Agent(model=BedrockModel(model_id="global.anthropic.claude-sonnet-4-6"), tools=ALL_TOOLS,
              interventions=[AgentShieldHandler(shield, approver=lambda prompt: input(prompt + " [y/n] ") == "y")])
# agent("Revisa el pedido ORD-1003.")   # every tool call now passes proceed / guide / confirm / deny first
