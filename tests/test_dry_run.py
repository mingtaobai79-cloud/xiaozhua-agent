from components.dry_run import build_dry_run


def test_complete_evidence_produces_confirmable_dry_run_plan():
    result = build_dry_run(target="application version", environment="test2", evidence={"status": "FACT", "refs": ["udc.version", "runtime.version"]}, dependencies=["generated artifact", "runtime metadata"], risks=["schema drift"])
    assert result["mode"] == "dry-run"
    assert result["requires_confirmation"] is True
    assert result["steps"]
    assert result["dependencies"] == ["generated artifact", "runtime metadata"]
    assert result["rollback"]
    assert result["verification"]
    assert all(step["action"] != "write" for step in result["steps"])


def test_missing_evidence_forbids_executable_write_and_marks_unverified():
    result = build_dry_run(target="publish application", environment="test2", evidence={"status": "UNVERIFIED", "refs": []}, dependencies=["build artifact"], risks=[])
    assert result["requires_confirmation"] is False
    assert result["verification"]["status"] == "UNVERIFIED"
    assert result["verification"]["evidence_status"] == "UNVERIFIED"
    assert all(step["executable"] is False for step in result["steps"])
    assert all(step["action"] != "write" for step in result["steps"])
    assert any("evidence" in item.lower() for item in result["verification"]["gaps"])


def test_unknown_environment_forbids_executable_write_even_with_evidence():
    result = build_dry_run(target="update runtime", environment=None, evidence={"status": "FACT", "refs": ["runtime.probe"]}, dependencies=[], risks=["unknown target"])
    assert result["requires_confirmation"] is False
    assert result["verification"]["status"] == "UNVERIFIED"
    assert result["verification"]["environment_status"] == "UNVERIFIED"
    assert all(step["executable"] is False for step in result["steps"])
    assert any("environment" in item.lower() for item in result["verification"]["gaps"])


def test_evidence_status_is_normalized_and_dependencies_are_preserved():
    result = build_dry_run(target="inspect route", environment="local", evidence={"status": "observation", "refs": ["probe.route"]}, dependencies=("route metadata",), risks=("stale cache",))
    assert result["verification"]["evidence_status"] == "OBSERVATION"
    assert result["dependencies"] == ["route metadata"]
    assert result["risks"] == ["stale cache"]
    assert result["verification"]["status"] == "UNVERIFIED"
