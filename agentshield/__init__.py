"""AgentShield: guard de tool calls con Strands Decider 2B."""

from .config import load_env
from .combine import GuardAnswers, HardResult, Verdict, combine
from .guard import AgentShieldHandler, Shield

load_env()  # DECIDER_URL, BEDROCK_MODEL_ID... desde .env si existe

__all__ = ["AgentShieldHandler", "GuardAnswers", "HardResult", "Shield", "Verdict", "combine"]
