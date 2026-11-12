"""CLI human-path integration: xiaozhua_cli op-execute -> PlatformOperationLayer.

Boundary: default is offline (network disabled) and must return BLOCKED, not a
fabricated result. Live readonly GET requires explicit --allow-network plus a
gateway URL and credential file, which is not exercised by offline tests.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
APP = "3289082814923688017"
ENTITY = "4649646467208458935"


def _run(*argv):
    return subprocess.run(
        [sys.executable, "-m", "xiaozhua_cli", "op-execute", *argv],
        cwd=ROOT, capture_output=True, text=True,
    )


def test_op_execute_offline_default_is_blocked_not_live():
    result = _run("--operation", "udc.application.get", "--application-id", APP)
    assert result.returncode == 2, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "BLOCKED"
    assert payload["mode"] == "readonly"
    assert payload["network"] == "disabled"
    assert payload["operation"] == "udc.application.get"
    # Blocked before any business data: error is transport/credential, not BOOT_0000.
    assert payload["error"]["kind"] in {"CREDENTIAL_RESOLUTION_FAILED", "CONNECTION_ERROR", "unavailable"}


def test_op_execute_write_operation_is_denied_before_gateway():
    result = _run("--operation", "udc.entity.create", "--application-id", APP)
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "DENIED"
    assert payload["error"]["code"] == "POLICY_DENIED"


def test_op_execute_entity_scoped_operation_requires_entity_id():
    result = _run("--operation", "udc.entity.get", "--application-id", APP)
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "UNVERIFIED"
    assert "entity_id" in payload["error"]["message"]


def test_op_execute_unknown_operation_is_unverified_discovery_error():
    result = _run("--operation", "udc.does-not-exist", "--application-id", APP)
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "UNVERIFIED"
    assert payload["error"]["kind"] == "DISCOVERY_ERROR"


def test_op_execute_evidence_out_persists_redacted_result(tmp_path):
    credential_file = tmp_path / "credentials.json"
    credential_file.write_text(
        json.dumps({"cli-default": {"Cookie": "JSESSIONID=secret-value"}}), encoding="utf-8"
    )
    out = tmp_path / "op-evidence.json"
    result = _run(
        "--operation", "udc.application.get", "--application-id", APP,
        "--credential-file", str(credential_file),
        "--evidence-out", str(out),
    )
    assert result.returncode == 2  # still blocked: network stays disabled
    assert out.exists()
    stored = json.loads(out.read_text(encoding="utf-8"))
    assert stored["status"] == "BLOCKED"
    text = out.read_text(encoding="utf-8")
    assert "secret-value" not in text
    assert "<REDACTED>" in text


def test_cli_operation_layer_composition_reaches_pass_with_stub_gateway():
    from components.platform_operations import ExecutionContext, UdcOperationRegistry
    from components.platform_operations.models import OperationIntent, OperationStatus
    from xiaozhua_cli import build_operation_layer

    class StubGateway:
        def read(self, operation, path, **kwargs):
            return {
                "verified": True,
                "response": {"body": {"status": 0, "code": "BOOT_0000", "data": {"content": {
                    "id": APP, "appId": APP, "name": "app9000000000000000001", "caption": "项目管理",
                }}}},
                "gateway": "stub", "route": "/service/udc/{target_path}", "service": "udc",
            }

    layer = build_operation_layer(StubGateway(), UdcOperationRegistry.default())
    context = ExecutionContext("s", "r", "p", "c", (f"{APP}:readonly",))
    result = layer.execute(OperationIntent("udc.application.get", APP, entity_name="application"), context)
    assert result.status == OperationStatus.PASS
    assert result.normalized_data["id"] == APP