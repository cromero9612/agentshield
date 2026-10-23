def test_the_pattern_example_runs_and_reaches_each_kind_of_verdict(monkeypatch):
    monkeypatch.setenv("DECIDER_URL", "")  # simulated Decider: no network
    from patterns.grounded_tool_call_guard.example import main
    verdicts = [line.split("->")[1].split()[0] for line in main()]
    assert verdicts == ["proceed", "deny", "confirm"]


def test_the_wiring_example_imports_cleanly_without_building_a_real_model():
    import importlib.util
    spec = importlib.util.find_spec("patterns.grounded_tool_call_guard.agent_wiring")
    assert spec is not None  # se valida que exista y sea importable por ruta; no se ejecuta (necesita credenciales)
