"""installer/hostlink.py —— 链接逻辑与 Cancelled 判定。

真实踩到的坑固化成断言：
* `hermes mcp add` 无 stdin 时回 "Cancelled." 但退出码 0 → 必须判失败
* 已存在时宿主报 "already exists" → 必须先 remove 再 add
* probe 不能靠 `hermes mcp list`（transport 列会被截断，永远匹配不上）
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "installer"))

import hostlink  # noqa: E402


def test_link_removes_then_adds(monkeypatch):
    calls = []

    def fake_run(cmd, dry_run, stdin_text=None):
        calls.append((cmd, stdin_text))
        return 0, "Saved 'xiaozhua' to config.yaml"

    monkeypatch.setattr(hostlink, "cli_for", lambda h: "hermes")
    monkeypatch.setattr(hostlink, "_run", fake_run)
    rep = hostlink.link(["hermes"], "C:/py/python.exe", "C:/x/server.py")

    assert rep[0]["ok"] is True
    verbs = [c[0][:3] for c in calls]
    assert verbs[0] == ["hermes", "mcp", "remove"], verbs
    assert verbs[1] == ["hermes", "mcp", "add"], verbs
    # add 必须喂 Y，否则宿主交互式提问会直接取消
    assert calls[1][1] and "Y" in calls[1][1]


def test_add_command_carries_install_paths(monkeypatch):
    seen = {}

    def fake_run(cmd, dry_run, stdin_text=None):
        if "add" in cmd:
            seen["add"] = cmd
        return 0, "ok"

    monkeypatch.setattr(hostlink, "cli_for", lambda h: "codex")
    monkeypatch.setattr(hostlink, "_run", fake_run)
    hostlink.link(["codex"], "C:/py/python.exe", "C:/x/server.py")

    assert "C:/py/python.exe" in seen["add"]
    assert "C:/x/server.py" in seen["add"]


def test_cancelled_counts_as_failure_and_retries(monkeypatch):
    n = {"add": 0}

    def fake_run(cmd, dry_run, stdin_text=None):
        if "add" in cmd:
            n["add"] += 1
            # _run 已把 "Cancelled." + 退出码 0 判定为失败，这里模拟它的返回值
            return 1, "  Cancelled."
        return 0, ""

    monkeypatch.setattr(hostlink, "cli_for", lambda h: "hermes")
    monkeypatch.setattr(hostlink, "_run", fake_run)
    rep = hostlink.link(["hermes"], "C:/py/python.exe", "C:/x/server.py")

    assert rep[0]["ok"] is False
    assert n["add"] == 2                      # 失败后立刻重试一次
    assert "Cancelled" in rep[0]["detail"]


def test_real_run_marks_cancelled_as_error():
    """走真实 subprocess：宿主打印 Cancelled 但退出码 0，也必须算失败。"""
    code, out = hostlink._run(
        [sys.executable, "-c", "print('  Cancelled.')"], dry_run=False)
    assert code != 0 and "Cancelled" in out


def test_missing_cli_is_skipped(monkeypatch):
    monkeypatch.setattr(hostlink, "cli_for", lambda h: None)
    rep = hostlink.link(["hermes"], "C:/py/python.exe", "C:/x/server.py")
    assert rep[0]["action"] == "skipped"
    assert hostlink.summary(rep) == "跳过 hermes"


def test_probe_hermes_reads_config_file(monkeypatch, tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "mcp_servers:\n  other:\n    command: y\n"
        "  xiaozhua:\n    command: C:/install/venv/Scripts/python.exe\n"
        "    args:\n      - C:/install/src/adapters/mcp/server.py\n"
        "    enabled: true\n",
        encoding="utf-8",
    )

    class R:
        stdout = str(cfg) + "\n"
        stderr = ""

    monkeypatch.setattr(hostlink, "cli_for", lambda h: "hermes")
    monkeypatch.setattr(hostlink.subprocess, "run", lambda *a, **k: R())

    assert hostlink.probe("hermes", "C:/install/src") is True
    assert hostlink.probe("hermes", "C:/elsewhere/src") is False


def test_probe_codex_uses_mcp_get(monkeypatch):
    class R:
        stdout = ("xiaozhua\n  command: C:/install/venv/Scripts/python.exe\n"
                  "  args: C:/install/src/adapters/mcp/server.py\n")
        stderr = ""

    monkeypatch.setattr(hostlink, "cli_for", lambda h: "codex")
    monkeypatch.setattr(hostlink.subprocess, "run", lambda *a, **k: R())

    assert hostlink.probe("codex", "C:/install/src") is True
    assert hostlink.probe("codex", "C:/other/src") is False