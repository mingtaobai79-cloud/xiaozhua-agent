import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_readme_matches_current_contract():
    """README 必须描述真实能力面，不能沿用早期"只读骨架"的自我描述。

    2026-11 修：旧版这里锁死 `assert "SPI：仅保留路由占位，未实现或注册组件" in readme`，
    把过期文案固化成契约 —— 一改 README 就红，于是没人敢改，外面看到的还是"只读骨架"。
    现在改为守真实事实。
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert f"Test collection: `{_pytest_collected_count()} tests collected`" in readme

    # 必须声明真实工具面，不能只说"只读"
    assert "54 个 MCP 工具" in readme
    assert "当前版本是可测试的只读骨架" not in readme

    # CLI 命令必须都还在
    for command in (
        "udc-report", "udc-analyze", "runtime-report", "integration-report",
        "audit-summary", "probe-summary", "evidence-ledger", "udc-path-matrix",
        "impact-graph", "extension-boundary", "dry-run", "capabilities", "udc-execute",
    ):
        assert f"python -m xiaozhua_cli {command}" in readme
    assert "Evidence Ledger" in readme
    assert "Probe Summary" in readme
    assert "不会连接真实环境" in readme

    # 凭据红线必须在 README 里写明
    assert "cdp_port" in readme
    assert "cookie 永远不导出" in readme


def test_version_capabilities_and_test_count_contract_is_explicit():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert re.search(r'^version\s*=\s*"0\.1\.0"$', pyproject, re.MULTILINE)
    assert f"Test collection: `{_pytest_collected_count()} tests collected`" in readme

    result = subprocess.run(
        [sys.executable, "-m", "xiaozhua_cli", "capabilities"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["network"] == "disabled"
    assert payload["mode"] == "read-only"
    assert set(payload["components"]) == {"udc", "runtime", "integration"}
    assert all(item["read_only"] is True for item in payload["components"].values())


def test_version_audit_document_records_four_version_boundaries():
    report = (ROOT / "docs" / "audit" / "agent-version-audit.md").read_text(encoding="utf-8")
    for heading in ("代码版本", "事实版本", "验证版本", "未验证版本"):
        assert heading in report
    assert "0.1.0" in report
    assert "5.3.517" in report
    assert f"Test collection: `{_pytest_collected_count()} tests collected`" in report
    assert "UNVERIFIED" in report
    assert "BLOCKED" in report


def _pytest_collected_count():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    match = re.search(r"(?m)^(\d+) tests collected", result.stdout)
    assert match, result.stdout
    return int(match.group(1))


def _documented_count(path):
    text = path.read_text(encoding="utf-8")
    patterns = (r"Test collection:\s*`(\d+) tests collected`",)
    matches = [value for pattern in patterns for value in re.findall(pattern, text, re.IGNORECASE | re.DOTALL)]
    assert matches, f"no current test count found in {path}"
    return {int(value) for value in matches}


def test_collection_count_ignores_passed_and_skipped_counts(tmp_path):
    report = tmp_path / "report.md"
    report.write_text("Test collection: `12 tests collected`\nFull deterministic suite: `10 passed, 2 skipped`", encoding="utf-8")
    assert _documented_count(report) == {12}


def test_documented_current_test_counts_match_pytest_collection():
    collected = _pytest_collected_count()
    for path in (
        ROOT / "README.md",
        ROOT / "docs" / "audit" / "agent-version-audit.md",
        ROOT / "docs" / "audit" / "code-reality-audit.md",
    ):
        assert _documented_count(path) == {collected}, path


def test_test_report_command_reads_pytest_result_and_exposes_acceptance_buckets(tmp_path):
    result_file = tmp_path / "pytest-report.txt"
    result_file.write_text("collected 12 items\n\n10 passed, 1 failed, 1 error in 2.34s\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "xiaozhua_cli", "test-report", "--result", str(result_file)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["pytest"] == {"collected": 12, "passed": 10, "failed": 1, "errors": 1}
    assert payload["compile_status"] in {"PASS", "UNVERIFIED"}
    assert payload["cli_smoke_status"] == "PASS"
    assert payload["external_operations_status"] == "NOT_RUN"
    assert payload["scope"]["network"] == "disabled"

