"""installer/selfupdate.py 的离线契约测试。

只测「不联网也能判定」的部分：命令能跑、状态文件能存能读、文档与实现里的一键命令一致。
真联网的 `git fetch` 与 `pip install` 不进单测（由 CI/人工跑 `xiaozhua update` 覆盖）。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from installer import selfupdate as su  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """状态文件写到 tmp，绝不碰用户 ~/.xiaozhua/state.json。"""
    monkeypatch.setattr(su, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.delenv("XIAOZHUA_TARGET", raising=False)
    monkeypatch.delenv("XIAOZHUA_HOSTS", raising=False)
    return tmp_path / "state.json"


def test_version_reads_version_file():
    assert su.read_version(ROOT) == (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def test_cli_version(capsys):
    assert su.main(["version"]) == 0
    out = capsys.readouterr().out
    assert "xiaozhua-agent" in out and su.read_version(ROOT) in out


def test_doctor_offline_does_not_touch_network(monkeypatch, capsys):
    called = []
    real_git = su.git

    def spy(*args, **kwargs):
        called.append(args[0])
        return real_git(*args, **kwargs)

    monkeypatch.setattr(su, "git", spy)
    code = su.main(["doctor"])                    # 不加 --fetch
    assert code in (0, 1)                         # 环境不完美时允许 1
    assert "fetch" not in called, "doctor 默认不得联网"
    out = capsys.readouterr().out
    assert "Python" in out and "MCP" in out


def test_mcp_selfcheck_counts_tools():
    ok, detail = su.mcp_selfcheck(ROOT)
    assert ok, detail
    assert "tools=" in detail
    assert int(detail.rsplit("tools=", 1)[1]) > 0


def test_state_roundtrip(isolated_state):
    assert su.load_state() == {}
    su.save_state({"hosts": ["hermes"], "target": "X:/pkg", "version": "9.9.9"})
    assert json.loads(isolated_state.read_text(encoding="utf-8"))["hosts"] == ["hermes"]
    assert su.load_state()["version"] == "9.9.9"


def test_update_refuses_without_git_repo(monkeypatch, capsys):
    monkeypatch.setattr(su, "is_git_repo", lambda *_a, **_k: False)
    assert su.main(["update"]) == 2
    assert "install" in capsys.readouterr().out      # 引导去一键安装


def test_parser_rejects_unknown_command():
    with pytest.raises(SystemExit):
        su.main(["frobnicate"])


def test_bootstrap_scripts_exist():
    for rel in ("scripts/install.sh", "scripts/install.ps1"):
        assert (ROOT / rel).is_file(), rel


def test_install_docs_carry_the_same_raw_urls():
    """文档里的一键命令必须与代码里的 RAW_BASE 同源，避免 404。"""
    doc = (ROOT / "INSTALL.md").read_text(encoding="utf-8-sig")
    assert f"{su.RAW_BASE}/scripts/install.sh" in doc
    assert f"{su.RAW_BASE}/scripts/install.ps1" in doc


def test_install_sh_is_syntactically_valid():
    """bash -n：语法错会在 curl|bash 时炸在一半，必须静态挡住。"""
    sh = (ROOT / "scripts" / "install.sh")
    proc = subprocess.run(["bash", "-n", str(sh)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_windows_only_cases_skip_on_posix():
    if sys.platform.startswith("win"):
        assert (ROOT / "scripts" / "install.ps1").is_file()
    else:
        pytest.skip("PowerShell 脚本只在 Windows 上做真实验证")


def test_install_sh_never_self_upgrades_pip():
    """回归：`pip install --upgrade pip` 在 Windows 上会把 pip/ 改名成 ~ip/ 再失败，
    留下没有 pip 的 venv（真机踩过）。bootstrap 阶段不允许出现这条命令。"""
    raw = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    code = "\n".join(l for l in raw.splitlines() if not l.lstrip().startswith("#"))
    assert "--upgrade pip" not in code, "bootstrap 阶段不得自我升级 pip"
    assert "ensurepip" in code, "pip 坏掉时必须有 ensurepip 自愈路径"


def test_install_sh_accepts_both_venv_layouts():
    """macOS/Linux 是 bin/python，Windows git-bash 是 Scripts/python.exe，两种都要认。"""
    sh = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    assert '$VENV/bin/python' in sh
    assert "Scripts/python.exe" in sh


def test_install_ps1_is_ascii_and_bomless():
    """install.ps1 必须纯 ASCII 且无 BOM —— 两条路径的编码陷阱都踩过：

    * 带 BOM 走 irm|iex：BOM 变成字符串首字符，`[CmdletBinding()]` 前多出一个"语句"，
      解析报 unexpected attribute CmdletBinding（PS 5.1 实测 5 个 parse error）。
    * 无 BOM 但有中文、走 powershell -File：PS 5.1 按 ANSI 码页解码，UTF-8 中文变成
      含 ASCII 标点的乱码，照样解析失败。
    只有 ASCII + 无 BOM 两条路都干净。中文文案放在 INSTALL.md。
    """
    raw = (ROOT / "scripts" / "install.ps1").read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "install.ps1 不能带 BOM（irm|iex 会解析失败）"
    bad = [i for i, b in enumerate(raw) if b > 127]
    assert not bad, "install.ps1 必须纯 ASCII，首个非 ASCII 字节偏移 %d" % (bad[0] if bad else -1)
    assert b"ensurepip" in raw

def test_min_python_matches_pyproject():
    """安装器的版本下限必须与 pyproject 的 requires-python 一致，否则
    `pip install -e .` 会在运行时被 metadata 拒绝（3.11 实测过这个坑）。"""
    import re
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'requires-python\s*=\s*">=\s*(\d+)\.(\d+)"', pyproject)
    assert m, "pyproject 里没有 requires-python >=X.Y"
    assert (int(m.group(1)), int(m.group(2))) == su.MIN_PY, (
        "selfupdate.MIN_PY=%s 与 pyproject requires-python=%s.%s 不一致" % (su.MIN_PY, m.group(1), m.group(2)))
