import pytest

from agent import run_agent


def test_bedrock_is_the_default_provider(monkeypatch):
    monkeypatch.delenv("AGENT_MODEL_PROVIDER", raising=False)
    assert type(run_agent.build_model()).__name__ == "BedrockModel"
    assert run_agent.describe_model().startswith("Bedrock")


def test_ollama_is_an_explicit_local_alternative_and_is_labelled_as_not_bedrock(monkeypatch):
    monkeypatch.setenv("AGENT_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
    model = run_agent.build_model()
    assert type(model).__name__ == "OllamaModel" and model.config["model_id"] == "qwen3:8b"
    assert "no es Bedrock" in run_agent.describe_model()


def test_unknown_provider_is_rejected(monkeypatch):
    monkeypatch.setenv("AGENT_MODEL_PROVIDER", "magia")
    with pytest.raises(ValueError, match="no es valido"):
        run_agent.build_model()
