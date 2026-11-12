from core.policy import PolicyGate


def test_policy_gate_allows_offline_inspection_and_dry_run():
    gate = PolicyGate(network_enabled=False)
    assert gate.evaluate("inspect_application")["allowed"] is True
    assert gate.evaluate("dry_run")["allowed"] is True


def test_policy_gate_denies_mutating_actions():
    gate = PolicyGate(network_enabled=True)
    for action in ("create", "save", "publish", "deploy", "restart", "delete"):
        decision = gate.evaluate(action)
        assert decision["allowed"] is False
        assert decision["status"] == "DENIED"


def test_policy_gate_denies_mutating_http_methods():
    gate = PolicyGate(network_enabled=True)
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        decision = gate.evaluate("http_request", provider="http", method=method)
        assert decision["allowed"] is False
        assert decision["status"] == "DENIED"


def test_policy_gate_blocks_live_reads_when_network_is_disabled():
    decision = PolicyGate(network_enabled=False).evaluate("http_request", provider="http", method="GET")
    assert decision["allowed"] is False
    assert decision["status"] == "BLOCKED"


def test_policy_gate_denies_kubernetes_mutations():
    gate = PolicyGate(network_enabled=True)
    for action in ("exec", "apply", "patch", "delete"):
        decision = gate.evaluate(action, provider="kubernetes")
        assert decision["allowed"] is False
        assert decision["status"] == "DENIED"
