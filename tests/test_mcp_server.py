"""tests/test_mcp_server.py — MCP server 三层离线覆盖（DESIGN §4 矩阵）。

层1 工具列表 / 层2 离线调用 / 层3 错误路径。全部离线确定性；
live 层留 @pytest.mark.live 默认不跑（README 纪律）。
"""
from __future__ import annotations

import io
import json

import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapters.mcp.server import (  # noqa: E402
    ERR_INVALID_PARAMS, ERR_METHOD_NOT_FOUND, MCP_TOOL_NAMES, McpServer,
    PROTOCOL_VERSION, build_tool_schemas,
)

# 2026-11-08：bootstrap 返回 15 个能力，此前只接了 5 个。补齐 9 个 metadata 构造器后共 14 个
# 2026-11-09：再补 9 个（设置/微流程节点/闸门/能力矩阵/表达式/自定义页/SPI）→ 23 个
# 2026-11-09：第二批 2 个（微流程发布 / 表达式编译，需显式 host+cookie）→ 25 个
# 2026-11-09：第三批 13 个（设置域 7 子域 body 构造器）→ 38 个
# 2026-11-09：第四批 1 个（八大模块总索引）→ 共 39 个
# （`agent` 是装配好的对象，不是可调用能力，不暴露）。
EXPECTED_TOOL_NAMES = {
    # 原有 5 个
    "xiaozhua_dispatch", "xiaozhua_generate", "xiaozhua_generate_from_requirement",
    "xiaozhua_live_probe", "xiaozhua_deploy_plan",
    # 2026-11-08 补齐的 9 个构造器
    "xiaozhua_list_page_schema", "xiaozhua_detail_page_schema", "xiaozhua_microflow_create_body",
    "xiaozhua_index_body", "xiaozhua_enum_body", "xiaozhua_enum_item_body",
    "xiaozhua_dto_body", "xiaozhua_event_body", "xiaozhua_filter_plan_body",
    # 2026-11-09 补齐的 9 个：设置域 3 + 微流程 3 + 表达式/自定义页/SPI 各 1
    "xiaozhua_enum_category_body", "xiaozhua_event_data_body", "xiaozhua_refer_config_body",
    # 能力发现：microflow_node 支持的 23 个 action → actionType
    "xiaozhua_microflow_node_actions",
    "xiaozhua_microflow_node", "xiaozhua_microflow_gates", "xiaozhua_microflow_capability",
    "xiaozhua_expression_catalog", "xiaozhua_custom_page_scaffold", "xiaozhua_spi_catalog",
    # 2026-11-09 第二批：需显式 host+cookie（不传不联网）
    "xiaozhua_microflow_publish", "xiaozhua_expression_verify",
    # 2026-11-09 第三批：设置域 7 子域（八大模块 setting/）→ 共 38 个
    "xiaozhua_option_set_category_body", "xiaozhua_option_set_body",
    "xiaozhua_option_set_item_body",
    "xiaozhua_attribute_set_body", "xiaozhua_attribute_set_field_body",
    "xiaozhua_scalability_option_body", "xiaozhua_scalability_field_body",
    "xiaozhua_qrcode_body",
    "xiaozhua_serial_scheme_body", "xiaozhua_serial_section",
    "xiaozhua_parameter_body",
    "xiaozhua_excel_template_body", "xiaozhua_excel_template_column",
    # 八大模块总索引
    "xiaozhua_capability_index",
    # 2026-11-09 第五批：微流程触发器 / dataSchema / FILTER 表达式 → 共 42 个
    "xiaozhua_microflow_trigger", "xiaozhua_microflow_data_schema",
    "xiaozhua_expression_filter",
    # 九大域口径 + 规则域（LIVE 写链原本没接）→ 共 44 个
    "xiaozhua_entity_rule_body", "xiaozhua_entity_rule_publish",
    # application 域（应用内功能页）→ 共 49 个
    "xiaozhua_repo_state", "xiaozhua_repo_sync", "xiaozhua_code_targets",
    "xiaozhua_project_shape", "xiaozhua_repo_url",
    "xiaozhua_app_dependency_body", "xiaozhua_app_dependency_remove_body",
    "xiaozhua_app_deploy_body", "xiaozhua_app_version_list",
    "xiaozhua_app_build_info",
    "xiaozhua_signature_search", "xiaozhua_microflow_service_catalog",
    "xiaozhua_ui_component_catalog",
}


@pytest.fixture(scope="module")
def server() -> McpServer:
    return McpServer(allow_network=False)


def _caps_or_skip():
    """惰性装配 bootstrap 五能力（离线，不联网）。"""
    from xiaozhua_host_bootstrap import bootstrap
    caps = bootstrap(credential_file=None, allow_network=False, audit_dir=None)
    return {k: caps[k] for k in MCP_TOOL_NAMES}


# ---------------------------------------------------------------- 层1 工具列表

def test_list_all_tools():
    caps = _caps_or_skip()
    tools = build_tool_schemas(caps)
    assert len(tools) == len(EXPECTED_TOOL_NAMES)
    assert {t["name"] for t in tools} == EXPECTED_TOOL_NAMES


def test_schema_from_signatures():
    caps = _caps_or_skip()
    schemas = {t["name"]: t["inputSchema"] for t in build_tool_schemas(caps)}
    # deploy_plan 必填三元（bootstrap 签名 L119：无默认值者）
    assert set(schemas["xiaozhua_deploy_plan"]["required"]) == {"application_id", "entity_name", "attributes"}
    # dispatch 必填 intent（target 有默认 None → 非必填）
    assert schemas["xiaozhua_dispatch"]["required"] == ["intent"]
    assert schemas["xiaozhua_dispatch"]["properties"]["target"]["default"] is None
    # live_probe 无必填（cred_file 缺省用 bootstrap credential_file）
    assert schemas["xiaozhua_live_probe"]["required"] == []


def test_enum_constraints():
    """enum 源 = deployment.py 实测常量，非手抄（DESIGN §4.1 enum_constraints）。"""
    from components.platform_operations.deployment import DEPLOY_TYPES, STEREO_TYPES
    caps = _caps_or_skip()
    schemas = {t["name"]: t["inputSchema"] for t in build_tool_schemas(caps)}
    dp = schemas["xiaozhua_deploy_plan"]["properties"]
    assert dp["stereotype"]["enum"] == list(STEREO_TYPES)
    assert dp["deploy_type"]["enum"] == list(DEPLOY_TYPES)


def test_attributes_element_schema():
    caps = _caps_or_skip()
    schemas = {t["name"]: t["inputSchema"] for t in build_tool_schemas(caps)}
    attrs = schemas["xiaozhua_generate"]["properties"]["attributes"]
    assert attrs["items"]["required"] == ["name"]
    assert "type" in attrs["items"]["properties"]
    assert "dataType" not in attrs["items"]["properties"]


def test_generate_schema_field_matches_actual_call(server: McpServer):
    tools = server.handle_frame({"jsonrpc": "2.0", "id": 20, "method": "tools/list"})["result"]["tools"]
    schema = next(t for t in tools if t["name"] == "xiaozhua_generate")["inputSchema"]
    fields = schema["properties"]["attributes"]["items"]["properties"]
    assert "type" in fields
    response = server.handle_frame({"jsonrpc": "2.0", "id": 21, "method": "tools/call", "params": {
        "name": "xiaozhua_generate", "arguments": {"application_id": "app9000000000000000001",
        "entity_name": "Example", "attributes": [{"name": "title", "type": "String"}]}}})
    assert response["result"]["isError"] is False
    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["status"] == "PASS"
    assert payload["backend"]["artifacts"]


# ---------------------------------------------------------------- 层2 离线调用

def test_call_dispatch_offline(server: McpServer):
    """未知组件 → status=UNAVAILABLE（registry 无该组件，非崩溃）。"""
    caps = _caps_or_skip()
    server._caps = caps
    resp = server.handle_frame({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                "params": {"name": "xiaozhua_dispatch",
                                           "arguments": {"intent": "unknown_component_x"}}})
    assert resp["result"]["isError"] is False
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload.get("status") == "UNAVAILABLE"


def test_call_deploy_plan_offline(server: McpServer):
    caps = _caps_or_skip()
    server._caps = caps
    resp = server.handle_frame({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                "params": {"name": "xiaozhua_deploy_plan",
                                           "arguments": {
                                               "application_id": "123",
                                               "entity_name": "XzlTest",
                                               "attributes": [{"name": "xzl_no", "caption": "编号", "dataType": "STRING"}],
                                               "stereotype": "bill", "deploy_type": "TEST"}}})
    data = json.loads(resp["result"]["content"][0]["text"])
    assert data.get("readonly_plan") is True
    steps = data.get("steps") or []
    assert len(steps) == 4
    assert [s["op"] for s in steps] == ["udc.entity.create", "udc.entity.attribute.create",
                                        "udc.page.create", "udc.deploy.normal"]


def test_call_deploy_plan_datatype_infer(server: McpServer):
    """dataType 缺省按名推断：acceptance_date → DATE 且进 unknowns。"""
    caps = _caps_or_skip()
    server._caps = caps
    resp = server.handle_frame({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                "params": {"name": "xiaozhua_deploy_plan",
                                           "arguments": {
                                               "application_id": "123",
                                               "entity_name": "XzlDate",
                                               "attributes": [{"name": "acceptance_date"}]}}})
    data = json.loads(resp["result"]["content"][0]["text"])
    step2 = (data.get("steps") or [])[1]
    attr = step2["body"][0]
    assert attr["dataType"] == "DATE"
    assert any("acceptance_date" in u for u in data.get("unknowns", []))


def test_call_live_probe_offline_blocked(server: McpServer, monkeypatch):
    monkeypatch.delenv('XIAOZHUA_ALLOW_NETWORK', raising=False)
    assert McpServer()._allow_network is False
    monkeypatch.setenv('XIAOZHUA_ALLOW_NETWORK', '1')
    assert McpServer()._allow_network is True
    assert McpServer(allow_network=False)._allow_network is False
    monkeypatch.setenv('XIAOZHUA_ALLOW_NETWORK', 'false')
    assert McpServer()._allow_network is False
    """默认离线 → live_probe 不得 PASS：无 cred=SKIPPED；有 cred 无网络=BLOCKED（实码 L96-100）。"""
    caps = _caps_or_skip()
    server._caps = caps
    # 无 cred 路径：SKIPPED（先于 allow_network 判断，bootstrap L97-98 实测）
    resp = server.handle_frame({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                                "params": {"name": "xiaozhua_live_probe", "arguments": {}}})
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload.get("status") in ("SKIPPED", "BLOCKED")  # 两者都是"未触网"语义
    assert payload.get("status") != "PASS"
    # 有 cred 路径（path 载体，非值）+离线 → BLOCKED，reason 含 allow_network
    resp2 = server.handle_frame({"jsonrpc": "2.0", "id": 41, "method": "tools/call",
                                 "params": {"name": "xiaozhua_live_probe",
                                            "arguments": {"cred_file": "shared-credentials/test2-web-credential.json"}}})
    payload2 = json.loads(resp2["result"]["content"][0]["text"])
    assert payload2.get("status") == "BLOCKED"
    assert "allow_network=False" in str(payload2.get("reason", ""))


def test_call_generate_offline(server: McpServer):
    caps = _caps_or_skip()
    server._caps = caps
    resp = server.handle_frame({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                                "params": {"name": "xiaozhua_generate",
                                           "arguments": {"application_id": "123", "entity_name": "XzlGen",
                                                         "attributes": [{"name": "xzl_no", "type": "STRING"}]}}})
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert "backend" in payload and "frontend" in payload


def test_call_generate_from_requirement_offline(server: McpServer):
    caps = _caps_or_skip()
    server._caps = caps
    resp = server.handle_frame({"jsonrpc": "2.0", "id": 6, "method": "tools/call",
                                "params": {"name": "xiaozhua_generate_from_requirement",
                                           "arguments": {"text": "做一个带编号和日期的验收单", "application_id": "123"}}})
    payload = json.loads(resp["result"]["content"][0]["text"])
    # 实码：中文句子无实体名 → status=UNVERIFIED + schema 标注（合法离线路径，非崩溃）
    assert payload.get("schema") == "udc.construction.requirement-parse.v1"
    assert payload.get("status") == "UNVERIFIED"


# ---------------------------------------------------------------- 层3 错误路径

def test_unknown_tool(server: McpServer):
    resp = server.handle_frame({"jsonrpc": "2.0", "id": 7, "method": "tools/call",
                                "params": {"name": "no_such_tool", "arguments": {}}})
    assert resp["error"]["code"] == ERR_INVALID_PARAMS
    assert "no_such_tool" in resp["error"]["message"]


def test_unknown_method(server: McpServer):
    resp = server.handle_frame({"jsonrpc": "2.0", "id": 8, "method": "resources/list", "params": {}})
    assert resp["error"]["code"] == ERR_METHOD_NOT_FOUND


def test_missing_required_param(server: McpServer):
    """缺必填 → -32602 且 message 指出字段名（DESIGN §4.3）。"""
    caps = _caps_or_skip()
    server._caps = caps
    resp = server.handle_frame({"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                                "params": {"name": "xiaozhua_deploy_plan",
                                           "arguments": {"application_id": "123"}}})
    assert resp["error"]["code"] == ERR_INVALID_PARAMS
    assert "entity_name" in resp["error"]["message"]
    assert "attributes" in resp["error"]["message"]


def test_bad_param_type(server: McpServer):
    caps = _caps_or_skip()
    server._caps = caps
    resp = server.handle_frame({"jsonrpc": "2.0", "id": 10, "method": "tools/call",
                                "params": {"name": "xiaozhua_dispatch",
                                           "arguments": {"intent": 123}}})
    assert resp["error"]["code"] == ERR_INVALID_PARAMS
    assert "intent" in resp["error"]["message"]


def test_bad_enum_value(server: McpServer):
    caps = _caps_or_skip()
    server._caps = caps
    resp = server.handle_frame({"jsonrpc": "2.0", "id": 11, "method": "tools/call",
                                "params": {"name": "xiaozhua_deploy_plan",
                                           "arguments": {"application_id": "1", "entity_name": "X",
                                                         "attributes": [], "deploy_type": "NOT_A_TYPE"}}})
    assert resp["error"]["code"] == ERR_INVALID_PARAMS
    assert "deploy_type" in resp["error"]["message"]


def test_write_not_exposed():
    """MCP 面默认只读：写动作必须由宿主显式传凭据才能执行（DESIGN §4.3）。

    2026-11-09 调整：工具面从 14 → 25，其中 microflow_publish 是**写**。
    红线不是「名字里不能有 write/publish」，而是「写能力不得默认可用」——
    所以断言改为：凡是写类工具，必须强制 host + cookie 两个必填参数，
    不传凭据就调不起来（不可能被误触发）。
    """
    caps = _caps_or_skip()
    tools = build_tool_schemas(caps)
    assert all(not t["name"].startswith("xiaozhua_write") for t in tools)

    WRITE_WORDS = ("write", "delete", "commit", "submit", "publish", "sync")
    write_tools = [t for t in tools
                   if any(w in t["name"] for w in WRITE_WORDS)]

    # 授权形态有两种，取决于写动作发生在哪：
    #   打平台  → host + cookie（凭据即授权）
    #   打本地/远端 git → confirm=True 布尔授权位（git 用 GCM，不用 cookie）
    LOCAL_WRITE = {"xiaozhua_repo_sync"}
    for t in write_tools:
        required = set(t["inputSchema"].get("required") or [])
        if t["name"] in LOCAL_WRITE:
            assert "confirm" in required, (
                "%s 是本地写工具，必须强制 confirm 必填（否则等于默认可写）" % t["name"])
            assert "confirm" in (t["inputSchema"].get("properties") or {}), (
                "%s 的 confirm 必须出现在 properties 里" % t["name"])
        else:
            # 打平台有两种授权：host+cookie（凭据）或 cdp_port（页面代发）。
            # 都不存在才算"默认可写"。
            props = set(t["inputSchema"].get("properties") or {})
            has_cookie = {"host", "cookie"} <= required
            has_cdp = "cdp_port" in props
            assert has_cookie or has_cdp, (
                "写类工具 %s 既没有强制 host+cookie，也没有 cdp_port 入口 —— 等于默认可写"
                % t["name"])

    # 只出 body 的构造器：名字里不许出现写动词
    body_only = ("_body", "_schema", "_catalog", "_capability", "_gates", "_scaffold")
    for t in tools:
        if any(s in t["name"] for s in body_only):
            assert not any(w in t["name"] for w in ("write", "delete", "commit", "submit")), t["name"]

    assert len(tools) == len(EXPECTED_TOOL_NAMES)


def test_initialize_handshake(server: McpServer):
    resp = server.handle_frame({"jsonrpc": "2.0", "id": 12, "method": "initialize",
                                "params": {"protocolVersion": "2024-11-05"}})
    assert resp["result"]["protocolVersion"] == PROTOCOL_VERSION
    assert resp["result"]["serverInfo"]["name"] == "xiaozhua-mcp"


def test_notification_silent(server: McpServer):
    """notifications/initialized → 无响应（None）。"""
    assert server.handle_frame({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


# ---------------------------------------------------------------- stdio 端到端（server 可起证据）

def test_stdio_end_to_end(server: McpServer):
    """喂两帧（initialize + tools/list）→ 读两行响应；server 可起的最小证据。"""
    fin = io.StringIO(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                  "params": {"protocolVersion": "2024-11-05"}}) + "\n"
                      + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}) + "\n")
    fout = io.StringIO()
    rc = server.serve(stdin=fin, stdout=fout)
    assert rc == 0
    lines = [json.loads(x) for x in fout.getvalue().strip().splitlines()]
    assert len(lines) == 2
    assert lines[0]["result"]["protocolVersion"] == PROTOCOL_VERSION
    assert len(lines[1]["result"]["tools"]) == len(EXPECTED_TOOL_NAMES)
    fin = io.StringIO('[]\n' + json.dumps({"jsonrpc": "2.0", "id": 3, "method": "initialize"}) + '\n')
    fout = io.StringIO()
    assert server.serve(stdin=fin, stdout=fout) == 0
    frames = [json.loads(line) for line in fout.getvalue().splitlines()]
    assert frames[0]['error']['code'] == -32600
    assert frames[1]['id'] == 3 and 'result' in frames[1]

def test_tools_list_works_without_pyyaml():
    """★ 回归守卫：缺 pyyaml 时 tools/list 仍要能工作。

    分发给别人时，人家 `pip install` 之前直接 `python adapters/mcp/server.py`，
    旧版 _config_loader 在模块级 `import yaml`，导致 tools/list 直接
    返回 internal error: ModuleNotFoundError: No module named 'yaml' ——
    握手成功、列工具崩，用户完全不知道要装包。

    现在改成延迟报错：import 不崩，只有真正读 config 时才给可读提示。
    """
    import subprocess, sys, json, shutil
    from pathlib import Path as _P

    root = _P(__file__).parents[1]
    probe = (
        "import sys, runpy\n"
        "class B:\n"
        "    def find_spec(self, n, path=None, target=None):\n"
        "        if n=='yaml' or n.startswith('yaml.'):\n"
        "            raise ModuleNotFoundError(n)\n"
        "        return None\n"
        "sys.meta_path.insert(0, B())\n"
        "for m in list(sys.modules):\n"
        "    if m=='yaml' or m.startswith('yaml.'): del sys.modules[m]\n"
        "sys.path.insert(0, '.')\n"
        "runpy.run_path('adapters/mcp/server.py', run_name='__main__')\n"
    )
    frames = "\n".join([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                               "clientInfo": {"name": "t", "version": "1"}}}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
    ]) + "\n"
    r = subprocess.run([sys.executable, "-c", probe], cwd=str(root), input=frames,
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=180)
    assert r.returncode == 0, r.stderr[-400:]
    got = []
    for line in r.stdout.splitlines():
        if line.strip():
            try:
                got.append(json.loads(line))
            except Exception:
                pass
    listed = [o for o in got if "result" in o and "tools" in o["result"]]
    assert listed, "缺 pyyaml 时 tools/list 没返回工具列表，响应：%s" % r.stdout[:300]
    from adapters.mcp.server import TOOL_KEYS as _KEYS
    assert len(listed[0]["result"]["tools"]) == len(_KEYS)

