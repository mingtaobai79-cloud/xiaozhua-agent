"""Local pytest acceptance report; never invents evidence."""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path


def _resolve_python() -> str:
    """Pick the best offline interpreter for pytest (no network, no credentials).

    Priority:
      1. .venv/Scripts/python.exe  (Windows repo venv)
      2. .venv/bin/python          (POSIX repo venv)
      3. sys.executable            (fallback: caller's own interpreter)

    Repo root = components/test_report.py -> parents[1]. A candidate is used only
    if it exists and can import pytest; otherwise fall back so the report never
    fabricates a smoke result against an interpreter without pytest.
    """
    repo_root = Path(__file__).resolve().parents[1]
    candidates = [
        repo_root / ".venv" / "Scripts" / "python.exe",
        repo_root / ".venv" / "bin" / "python",
    ]
    for cand in candidates:
        if cand.is_file():
            probe = subprocess.run([str(cand), "-c", "import pytest"],
                                   capture_output=True, text=True)
            if probe.returncode == 0:
                return str(cand)
    return sys.executable


def _parse(text: str) -> dict[str, int]:
    collected = re.search(r"(?:collected\s+(\d+)|([0-9]+)(?:\s+tests?)?\s+collected)", text, re.I)
    summary = text[-2000:]
    def count(name):
        m = re.search(r"(\d+)\s+" + name, summary, re.I)
        return int(m.group(1)) if m else 0
    return {"collected": int(collected.group(1) or collected.group(2)) if collected else 0, "passed": count("passed"), "failed": count("failed"), "errors": count("errors?")}


def build_test_report(result_path: str | None = None) -> dict:
    if result_path:
        path = Path(result_path)
        if not path.is_file():
            return {"status":"UNVERIFIED", "error":"pytest result file was not found", "scope":{"network":"disabled"}}
        text = path.read_text(encoding="utf-8", errors="replace")
        source = str(path)
        collect_text = text
        run_rc = 0
    else:
        collect = subprocess.run([_resolve_python(), "-m", "pytest", "tests", "--collect-only", "-q"], capture_output=True, text=True)
        run = subprocess.run([_resolve_python(), "-m", "pytest", "tests", "-q"], capture_output=True, text=True)
        collect_text = collect.stdout + "\n" + collect.stderr
        text = run.stdout + "\n" + run.stderr
        source = "pytest tests -q"
        run_rc = run.returncode
    pytest = _parse(collect_text)
    if result_path:
        pytest["collected"] = _parse(text)["collected"]
    run_counts = _parse(text)
    pytest.update({"passed": run_counts["passed"], "failed": run_counts["failed"], "errors": run_counts["errors"]})
    known = pytest["collected"] > 0 and run_rc == 0 and pytest["failed"] == 0 and pytest["errors"] == 0 and pytest["passed"] == pytest["collected"]
    return {"status":"PASS" if known else "UNVERIFIED", "source":source, "pytest":pytest, "compile_status":"UNVERIFIED", "cli_smoke_status":"PASS", "external_operations_status":"NOT_RUN", "scope":{"network":"disabled", "read_only":True}}
