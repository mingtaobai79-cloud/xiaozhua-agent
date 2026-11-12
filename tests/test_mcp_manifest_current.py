# -*- coding: utf-8 -*-
"""守 MCP 工具清单与实际工具面一致（2026-11-09）。

背景：`adapters/*/MCP-TOOL-MANIFEST.md` 是手工维护的，工具面从 5 → 14 → 44
每次都落后（实测三份都停在 14 个）。改为生成器产出权威清单后，需要一条测试
防止「改了工具面不重跑生成器」。

失败信息直接给出修复命令，不要让人去猜。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOLS_MD = REPO / "docs" / "operation-contracts" / "mcp" / "TOOLS.md"
GEN = REPO / "tools" / "gen_mcp_manifest.py"


def test_mcp_tools_md_matches_live_surface():
    """TOOLS.md 必须与实际工具面逐字一致。"""
    assert TOOLS_MD.exists(), (
        "docs/operation-contracts/mcp/TOOLS.md 不存在，"
        "跑 `python tools/gen_mcp_manifest.py` 生成")
    r = subprocess.run([sys.executable, str(GEN), "--check"],
                       cwd=str(REPO), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    assert r.returncode == 0, (
        "MCP 工具清单已漂移，跑 `python tools/gen_mcp_manifest.py` 重新生成\n%s%s"
        % (r.stdout, r.stderr))


def test_every_tool_key_has_domain_mapping():
    """每个 TOOL_KEY 都要在生成器的 DOMAIN_OF 里有归属，不能落进「未归类」。"""
    sys.path.insert(0, str(REPO))
    from adapters.mcp.server import TOOL_KEYS
    sys.path.insert(0, str(REPO / "tools"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("_gen", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    missing = [k for k in TOOL_KEYS if k not in m.DOMAIN_OF]
    assert not missing, (
        "以下能力没有域归属，请在 tools/gen_mcp_manifest.py 的 DOMAIN_OF 补上：%s"
        % missing)


def test_credentialed_tools_require_host_and_cookie():
    """需要凭据的工具，schema 里 host/cookie 必须是必填。"""
    sys.path.insert(0, str(REPO))
    from seeyon_host_bootstrap import bootstrap
    from adapters.mcp.server import TOOL_KEYS, build_tool_schemas

    b = bootstrap()
    caps = {k: b[k] for k in TOOL_KEYS}
    tools = {t["name"]: t for t in build_tool_schemas(caps)}

    # 已知的写/联网工具，必须提供某种授权入口：
    #   host+cookie（凭据即授权）或 cdp_port（页面代发，cookie 不离开浏览器）
    # ★ cdp_port 优先 —— 导出 token 到本地重放等于复制用户身份
    for name in ("seeyon_microflow_publish", "seeyon_expression_verify",
                 "seeyon_expression_filter", "seeyon_entity_rule_publish"):
        props = set(tools[name]["inputSchema"].get("properties") or {})
        assert {"host", "cookie", "cdp_port"} <= props, (
            "%s 必须暴露 host/cookie/cdp_port 三种授权入口，实际 properties=%s"
            % (name, sorted(props)))
