"""9 个 metadata 构造器的 MCP 暴露面回归闸门。

**为什么有这文件**：`seeyon_host_bootstrap.bootstrap()` 一直返回 15 个能力，
但 `adapters/mcp/server.py` 的 `TOOL_KEYS` 只接了 5 个 —— 9 个构造器
（pageSchema / microflow / index / enum / enum-item / dto / event / filter）
在宿主侧**完全看不见**。2026-11-08 补齐。

`tests/test_mcp_server.py` 只断言「工具在列表里、schema 正确」，
不断言「调出来有东西」。这里补的正是后者 —— 加进 TOOL_KEYS 不等于能用。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "mcp"))

from server import MCP_TOOL_NAMES, TOOL_KEYS, McpServer  # noqa: E402

APP = "6419954374508955097"
APP_INT = 6419954374508955097
ATTRS = [
    {"name": "code", "type": "String", "caption": "单号"},
    {"name": "amount", "type": "BigDecimal", "caption": "金额"},
]

# 每个新工具一组「最小合法入参」
CALLS = {
    "seeyon_list_page_schema": dict(
        application_id=APP, entity_name="PurchaseApply", caption="采购申请单", attributes=ATTRS),
    "seeyon_detail_page_schema": dict(
        application_id=APP, entity_name="PurchaseApply", caption="采购申请单", attributes=ATTRS),
    "seeyon_microflow_create_body": dict(
        name="pf_flow", caption="采购流程", application_id=APP,
        data_schema={"nodes": [], "endNode": {}}, trigger_type="MANUAL"),
    "seeyon_index_body": dict(caption="单号索引", entity_id=12345, field_ids=[1, 2]),
    "seeyon_enum_body": dict(app_id=APP_INT, caption="状态", name="status_enum"),
    "seeyon_enum_item_body": dict(
        app_id=APP_INT, enum_id=777, caption="待审批", item_value="0",
        enum_code="status_enum", order_no=1),
    "seeyon_dto_body": dict(app_id=APP_INT, caption="采购DTO", name="PurchaseDTO", attributes=ATTRS),
    "seeyon_event_body": dict(app_id=APP_INT, caption="保存事件", event_name="onSave", dto_id=888),
    "seeyon_filter_plan_body": dict(
        app_name="demoapp", app_id=APP_INT, page_id=999, grid_suffix="main",
        driven_entity="PurchaseApply", caption="默认过滤",
        conditions=[{"field": "code", "op": "like"}]),
}


@pytest.fixture(scope="module")
def server() -> McpServer:
    return McpServer(allow_network=False)


def _call(server, name, args):
    resp = server.handle_frame({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": args},
    })
    assert "error" not in resp, resp.get("error")
    res = resp["result"]
    assert res.get("isError") is False, res["content"][0]["text"][:300]
    return res["content"][0]["text"]


# ---------------------------------------------------------------- 覆盖度
def test_九个构造器全部在_TOOL_KEYS_里():
    for key in ("list_page_schema", "detail_page_schema", "microflow_create_body",
                "index_body", "enum_body", "enum_item_body", "dto_body",
                "event_body", "filter_plan_body"):
        assert key in TOOL_KEYS, "%s 没接进 MCP —— bootstrap 有、宿主看不见" % key
        assert key in MCP_TOOL_NAMES


def test_tool_keys_与_MCP_NAMES_一一对应():
    assert set(TOOL_KEYS) == set(MCP_TOOL_NAMES)
    assert len(set(MCP_TOOL_NAMES.values())) == len(MCP_TOOL_NAMES), "MCP 工具名有重复"


# ---------------------------------------------------------------- 逐个真调
@pytest.mark.parametrize("name", sorted(CALLS))
def test_构造器返回非空真实产出(server, name):
    text = _call(server, name, CALLS[name])
    assert len(text) > 40, "%s 产出太小（%d B），可能是空壳" % (name, len(text))
    assert "Traceback" not in text


def test_列表页_pageSchema_有控件与工具栏(server):
    import json
    data = json.loads(_call(server, "seeyon_list_page_schema", CALLS["seeyon_list_page_schema"]))
    assert data["readonly_plan"] is True
    ps = data["pageSchema"]
    assert ps, "pageSchema 为空"
    # 实测形态：pageType=SEARCH_LIST + 列（dataIndex/dataFieldCaption/componentName）
    assert ps.get("pageType") == "SEARCH_LIST", ps.get("pageType")
    flat = json.dumps(ps, ensure_ascii=False)
    assert "dataIndex" in flat, "列表页没有列定义"
    assert "code" in flat and "amount" in flat, "入参 attributes 没进列定义"


def test_详情页_pageSchema_非空(server):
    import json
    data = json.loads(_call(server, "seeyon_detail_page_schema", CALLS["seeyon_detail_page_schema"]))
    assert data["readonly_plan"] is True
    assert data["pageSchema"]


def test_枚举项保留平台槽位语义(server):
    """`itemValue`=枚举项值、`parentId`=上级项ID 是实测槽位，不能被改名。"""
    import json
    data = json.loads(_call(server, "seeyon_enum_item_body", CALLS["seeyon_enum_item_body"]))
    assert data["itemValue"] == "0"
    assert data["parentId"] == "0", "顶层项 parentId 必须是字符串 \"0\""
    assert data["enumCode"] == "status_enum"


def test_微流程_body_把_dataSchema_字符串化(server):
    import json
    data = json.loads(_call(server, "seeyon_microflow_create_body",
                            CALLS["seeyon_microflow_create_body"]))
    ds = data.get("dataSchema")
    assert isinstance(ds, str), "dataSchema 必须是字符串（平台接口要字符串，不是对象）"


def test_过滤方案带_readonly_标记(server):
    import json
    data = json.loads(_call(server, "seeyon_filter_plan_body", CALLS["seeyon_filter_plan_body"]))
    assert data["readonly_plan"] is True
    assert data["body"]


# ---------------------------------------------------------------- 安全面
@pytest.mark.parametrize("name", sorted(CALLS))
def test_九个构造器都不落库(server, name):
    """构造器只出 body：产出里不许出现提交/成功类字样。"""
    text = _call(server, name, CALLS[name])
    for word in ("已提交", "已创建成功", "created successfully", "committed"):
        assert word not in text, "%s 的产出出现「%s」—— 构造器不该声称已写入" % (name, word)


def test_不存在的工具名报参数错(server):
    resp = server.handle_frame({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                "params": {"name": "seeyon_write_entity", "arguments": {}}})
    assert resp["error"]["code"] == -32602
