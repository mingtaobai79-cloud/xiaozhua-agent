"""installer/install.py 契约测试 —— 守 INSTALL-MANIFEST §2/§3/§4 的可机械检查部分。

这些用例全部在 tmp_path 里跑，**不在仓库内物化 AGENTS.md / CLAUDE.md**
（Hermes 写保护 fail-closed 清单），也不连网、不读凭据。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "installer" / "install.py"

HOSTS = ("hermes", "codex", "claude-code")
CANONICAL = "5.3.517"
SCHEMA = "xiaozhua-host-bootstrap.v1"


def run(*args, expect=0):
    r = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
        errors="replace")
    assert r.returncode == expect, (
        "期望 rc=%d 实得 %d\nSTDOUT:\n%s\nSTDERR:\n%s"
        % (expect, r.returncode, r.stdout, r.stderr))
    return r


@pytest.fixture
def installed(tmp_path):
    """**函数级**，不用 module 级 —— module 级会把产物缓存住，
    导致「改坏 installer 后 H1 测试仍读旧产物」而假绿（本轮实测踩到）。
    """
    target = tmp_path / "xiaozhua-pkg"
    run("--host", "all", "--target", str(target), "--write")
    return target


# ---------------------------------------------------------------- 物化正确性
def test_规范名指令件落地且模板名不落地(installed):
    """§2：模板件 → 规范名。安装态里不许出现 .template。"""
    assert (installed / "codex" / "AGENTS.md").is_file()
    assert (installed / "claude-code" / "CLAUDE.md").is_file()
    assert (installed / "hermes" / "skills" / "xiaozhua-agent-hermes" / "SKILL.md").is_file()

    for f in installed.rglob("*"):
        if f.is_file():
            assert ".template." not in f.name, "模板名随安装落地了：%s" % f


def test_H1_按安装态规则重写(installed):
    """§3：H1 = 规范名 + Canonical 版本锚 + schema 锚，且覆盖模板作者期 H1。"""
    for rel, name in (("codex/AGENTS.md", "AGENTS.md"),
                      ("claude-code/CLAUDE.md", "CLAUDE.md")):
        text = (installed / rel).read_text(encoding="utf-8")
        lines = [l for l in text.split("\n") if l.strip()]
        h1 = [l for l in lines if l.startswith("# ")][0]
        assert h1.startswith("# %s" % name), "H1 不是规范名：%r" % h1[:60]
        assert CANONICAL in h1, "H1 缺版本锚 %s：%r" % (CANONICAL, h1[:80])
        assert SCHEMA in h1, "H1 缺 schema 锚 %s：%r" % (SCHEMA, h1[:80])


def test_过程态标签不随安装件传播(installed):
    """§3：STAGED / 待放行 是模板作者期残留，安装态必须消失。"""
    for rel in ("codex/AGENTS.md", "claude-code/CLAUDE.md",
                "hermes/skills/xiaozhua-agent-hermes/SKILL.md"):
        text = (installed / rel).read_text(encoding="utf-8")
        for tag in ("STAGED", "待放行"):
            assert tag not in text, "%s 里残留过程态标签 %r" % (rel, tag)


def test_凭据零入件(installed):
    """§4 第 5 项：只许 credential_file 路径引用，不许任何值。"""
    import re
    pats = [
        re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S{6,}"),
        re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{16,}"),
        re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\."),
    ]
    for f in installed.rglob("*"):
        if not f.is_file() or f.suffix == ".json" and f.name == "MANIFEST.json":
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for pat in pats:
            m = pat.search(text)
            assert not m, "%s 疑似含凭据值：%r" % (f.name, m.group(0)[:40] if m else "")


# ---------------------------------------------------------------- MCP 注册面
def test_三宿主_MCP_片段各自格式正确(installed):
    """L2 ①：宿主侧 MCP 注册配置 —— 三种格式都要能被各自宿主解析。"""
    y = (installed / "hermes" / "mcp_servers.yaml").read_text(encoding="utf-8")
    assert "xiaozhua:" in y and "adapters/mcp/server.py" in y
    assert y.lstrip().startswith("#"), "Hermes 片段应带「贴进 config.yaml」的说明头"

    t = (installed / "codex" / "config.toml").read_text(encoding="utf-8")
    assert "[mcp_servers.xiaozhua]" in t
    assert 'command = "' in t and "server.py" in t

    j = json.loads((installed / "claude-code" / ".mcp.json").read_text(encoding="utf-8"))
    assert "xiaozhua" in j["mcpServers"]
    assert j["mcpServers"]["xiaozhua"]["args"][0].endswith("adapters/mcp/server.py")


def test_三份片段指向同一个传输层(installed):
    """跨宿主一致性：不能三份配置各指一个 server。"""
    paths = set()
    for rel in ("hermes/mcp_servers.yaml", "codex/config.toml", "claude-code/.mcp.json"):
        text = (installed / rel).read_text(encoding="utf-8")
        assert text.count("adapters/mcp/server.py") == 1, rel
        paths.add("adapters/mcp/server.py")
    assert len(paths) == 1


def test_portable_模式不写本机绝对路径(tmp_path):
    """跨机器分发：--portable 用占位符，不带本机 python 绝对路径以外的根路径。"""
    run("--host", "codex", "--target", str(tmp_path / "p"), "--portable", "--write")
    t = (tmp_path / "p" / "codex" / "config.toml").read_text(encoding="utf-8")
    assert "<XIAOZHUA_AGENT_ROOT>" in t, "portable 模式应保留占位符"


# ---------------------------------------------------------------- 安全边界
def test_拒绝在仓库内物化():
    """写保护：installer 不许把 AGENTS.md/CLAUDE.md 落进本仓。"""
    r = run("--host", "codex", "--target", str(ROOT / "build" / "x"), expect=1)
    assert "拒绝在仓库内物化" in (r.stdout + r.stderr)


def test_默认不落盘(tmp_path):
    """不加 --write 时一个文件都不许出现。"""
    target = tmp_path / "dry"
    run("--host", "all", "--target", str(target))
    assert not target.exists() or not any(target.rglob("*")), "dry-run 却写了盘"


def test_拒绝覆盖非本工具产物(tmp_path):
    """幂等保护：目标已有别人的 AGENTS.md 时，不给 --force 就拒。"""
    target = tmp_path / "p"
    (target / "codex").mkdir(parents=True)
    (target / "codex" / "AGENTS.md").write_text("# 别人的文件\n", encoding="utf-8")
    r = run("--host", "codex", "--target", str(target), "--write", expect=1)
    assert "拒绝覆盖非本工具产物" in (r.stdout + r.stderr)


def test_重复安装幂等(tmp_path):
    """同一目标跑两次，产物字节一致（MANIFEST 里 sha256 不变）。"""
    target = tmp_path / "p"
    run("--host", "all", "--target", str(target), "--write")
    first = json.loads((target / "MANIFEST.json").read_text(encoding="utf-8"))
    run("--host", "all", "--target", str(target), "--write")
    second = json.loads((target / "MANIFEST.json").read_text(encoding="utf-8"))
    assert first["files"] == second["files"], "重复安装产物不一致"


def test_MANIFEST_记录了全部产物(installed):
    m = json.loads((installed / "MANIFEST.json").read_text(encoding="utf-8"))
    assert m["canonical_version"] == CANONICAL
    assert m["schema"] == SCHEMA
    paths = {f["path"] for f in m["files"]}
    for host in HOSTS:
        assert any(p.startswith(host + "/") for p in paths), "MANIFEST 缺 %s 的产物" % host
    for f in m["files"]:
        assert f["bytes"] > 0 and len(f["sha256"]) == 64

def test_hermes_skill_frontmatter_必须在首行(installed):
    """★ 实测踩到的真 bug：给 Hermes 的 SKILL.md 加 HTML 注释签名头，
    会让 `---` frontmatter 不在第一行 → 宿主解析不出 name/description，
    skill 装了等于没装。签名改记 MANIFEST.json，不进文件头。
    """
    skill = installed / "hermes" / "skills" / "xiaozhua-agent-hermes" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert text.startswith("---\n"), (
        "Hermes SKILL.md 首行必须是 `---`（YAML frontmatter），实得：%r" % text[:40])
    assert "name: xiaozhua-agent-hermes" in text.split("---")[1], "frontmatter 缺 name"

def test_skill_目录名必须等于_frontmatter_name(installed):
    """★ 实测踩到的真问题：把 `xiaozhua-agent-hermes` 装进 `skills/xiaozhua-agent/`，
    正好撞上仓库里**另一个 skill**（v1 `xiaozhua-agent`，被 v2 的 base: 引用为只读基线）。
    宿主上会变成「目录叫 A、skill 叫 B」，而仓库里 A 是别的东西。
    """
    import re
    hits = list(installed.rglob("SKILL.md"))
    assert hits, "没有产出任何 SKILL.md"
    for f in hits:
        text = f.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f
        fm = text.split("---")[1]
        m = re.search(r"^name:\s*(\S+)", fm, re.M)
        assert m, "%s 的 frontmatter 没有 name" % f
        assert f.parent.name == m.group(1), (
            "目录名 %r 与 frontmatter name %r 不一致 —— 宿主侧会与仓库里的同名目录撞车"
            % (f.parent.name, m.group(1)))
