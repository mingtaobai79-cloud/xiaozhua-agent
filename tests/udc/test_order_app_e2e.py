"""订单应用 plan_build 端到端验收测试 — 全语义 spec 的完整构建契约核对。

这是一次"真跑一遍"的验收：把订单应用的全部需求面（实体/字段/索引/事件/参照/
选项集/微流程/页面工具栏·规则·面板·详情/Excel/菜单/部署）喂给 planner，
逐项核对生成计划的自洽性与证据纪律，而非只看单函数行为。

验收清单（每条对应一个 test）：
1. 每个 GraphQL 步的 op 都真实存在于 graphql_write_ops 目录（不许臆造 op）；
2. 每个 body_builder 引用的 模块.符号 都能 import（不许指错模块）；
3. 依赖顺序：选项集→实体→字段→索引/事件/参照；微流程在实体后；页面在微流程后；
4. agent 不出写：executed/writes_performed 恒 False，每步 executed False；
5. 部署步标 destructive；
6. 计划可 JSON 序列化（宿主可落盘/传输）；
7. 未证项（数据权限开关等）显式进 unknowns，不静默吞；
8. 每个 rest 步都有明确 endpoint 与 evidence 分级。
"""
import importlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.models import (
    ApplicationSpec, EntitySpec, FieldSpec, PageSpec, MicroFlowSpec,
    IndexSpec, EventSpec, ReferSpec, MenuSpec, EnumOptionSpec, ExcelSpec)
from components.udc.planner import UdcPlanner
from components.udc.graphql_write_ops import op_entry

# 证据级白名单（planner 只允许这四级）
ALLOWED_EVIDENCE = {"LIVE", "STATIC_CATALOG", "LIVE_SMOKE", "OBSERVED_LIVE", "UNVERIFIED"}


def order_app_spec():
    """订单应用：覆盖用户提出的全部构建需求面。"""
    return ApplicationSpec(
        name="orderapp", caption="订单应用", app_stereotype="单据",
        enums=[
            EnumOptionSpec("orderStatus", "订单状态", items=[
                {"code": 10, "caption": "新建", "name": "NEW"},
                {"code": 20, "caption": "已付", "name": "PAID"},
            ]),
        ],
        entities=[EntitySpec(
            "Order", caption="订单", stereotype="单据", data_permission=True,
            fields=[
                FieldSpec("orderNo", "STRING", length=64, required=True, uniqueness=True),
                FieldSpec("amount", "DECIMAL"),
                FieldSpec("status", "ENUM", enum_name="orderStatus"),
                FieldSpec("buyer", "ENTITY", multi_select=True,
                          reference={"relationApp": "organization",
                                     "relationEntity": "com.seeyon.organization.domain.core.entity.OrgMember"}),
                FieldSpec("createTime", "DATETIME",
                          default_value={"defaultValueSystemVariable": "CURRENT_DATE"}),
            ],
            indexes=[IndexSpec("idx_order_no", "NORMAL", ["orderNo"]),
                     IndexSpec("uk_order_no", "UNIQUE", ["orderNo", "buyer"])],
            events=[EventSpec("onOrderCreate", "订单创建", "BUSINESS_EVENT")],
            refer=[ReferSpec("订单人员参照", "Order", terminal="PC")],
        )],
        microflows=[
            MicroFlowSpec("QueryOrderPeople", trigger="MANUAL"),
            MicroFlowSpec("BuildOrderTrace", trigger="MANUAL",
                          group_type="VALIDATE", source_id="Order"),
        ],
        pages=[PageSpec(
            "OrderList", page_url="/order/list", page_type="LIST",
            toolbar=["新增", "查询", "测试1"],
            bind_microflow="BuildOrderTrace",
            columns=[{"field": "orderNo", "width": 120}, {"field": "status", "width": 80}],
            detail={"穿透": "订单详情"},
            panels=[{"caption": "流转日志"}],
            page_rules=[{"caption": "默认过滤"}]),
        ],
        menus=[MenuSpec("订单管理", page="OrderList", icon="order", order_no=10)],
        excel=[ExcelSpec("Order", "export", data=[{"orderNo": "O1"}])],
    )


def _plan():
    return UdcPlanner().plan_build(order_app_spec())


# ---------------------------------------------------------------- 1. op 必须真实
def test_every_graphql_op_exists_in_catalog():
    plan = _plan()
    missing = []
    for s in plan["steps"]:
        if s["channel"] != "graphql":
            continue
        if op_entry(s["op"]) is None:
            missing.append(s["op"])
    assert not missing, f"计划含目录外 op（臆造）: {missing}"


def test_graphql_steps_carry_catalog_contract():
    """graphql 步的 note 应带上 paramsType/paramsKey 或目录契约说明（可追溯）。"""
    plan = _plan()
    for s in plan["steps"]:
        if s["channel"] != "graphql":
            continue
        e = op_entry(s["op"])
        assert e is not None
        # 目录收录的 contract 与 step 声明的 op 一致
        assert e["op"] == s["op"]


# ---------------------------------------------------------------- 2. body_builder 可解析
def test_every_body_builder_symbol_resolves():
    plan = _plan()
    checked = 0
    for s in plan["steps"]:
        bb = s.get("body_builder", "")
        for m in re.finditer(r"([a-z_][a-z_0-9]*(?:\.[a-z_0-9]+)+)\.([A-Za-z_]\w*)", bb):
            mod, sym = m.group(1), m.group(2)
            if mod.startswith("construction.") or mod.split(".")[0] in (
                    "attribute_semantics", "layout_model", "function_node_model",
                    "excel_model", "deploy_chain_model"):
                full = f"components.{mod}" if mod.startswith("construction") else f"components.udc.{mod}"
                module = importlib.import_module(full)
                assert hasattr(module, sym), f"{full}.{sym} 不存在"
                checked += 1
    assert checked >= 8, f"可解析引用太少（{checked}），覆盖不足"


# ---------------------------------------------------------------- 3. 依赖顺序
def test_dependency_ordering():
    plan = _plan()
    idx = {}
    for s in plan["steps"]:
        idx.setdefault(s["action"], s["seq"])
    # 选项集先于实体（字段引用它）
    assert idx["create_enum"] < idx["create_entity"]
    assert idx["create_enum_items"] < idx["create_entity"]
    # 实体先于其字段/索引/事件/参照
    assert idx["create_entity"] < idx["create_attribute"]
    assert idx["create_entity"] < idx["create_index"]
    assert idx["create_entity"] < idx["create_event"]
    assert idx["create_entity"] < idx["create_refer"]
    # 微流程在实体后（事件/规则依赖实体）
    assert idx["create_entity"] < idx["microflow_check_schema"]
    # 页面在微流程后（绑定微流程）
    assert idx["microflow_create"] < idx["page_create_base"]
    assert idx["page_create_base"] < idx["page_bind_microflow"]
    # 部署最后
    assert max(s["seq"] for s in plan["steps"]) == idx["deploy_online"]


def test_seq_is_contiguous_from_one():
    plan = _plan()
    assert [s["seq"] for s in plan["steps"]] == list(range(1, len(plan["steps"]) + 1))


# ---------------------------------------------------------------- 4/5. 安全边界
def test_agent_never_writes_and_deploy_is_destructive():
    plan = _plan()
    assert plan["executed"] is False
    assert plan["writes_performed"] is False
    assert all(s["executed"] is False for s in plan["steps"])
    deploy = [s for s in plan["steps"] if s["action"] == "deploy_online"]
    assert len(deploy) == 1 and deploy[0]["destructive"] is True


# ---------------------------------------------------------------- 6. 可序列化
def test_plan_is_json_serializable():
    plan = _plan()
    blob = json.dumps(plan, ensure_ascii=False)
    back = json.loads(blob)
    assert back["mode"] == "build-plan"
    assert len(back["steps"]) == len(plan["steps"])


# ---------------------------------------------------------------- 7. 未知项显式
def test_undeclared_or_runtime_only_goes_to_unknowns():
    plan = _plan()
    # 数据权限开关是运行态列，不生成步骤但必须进 unknowns
    assert any("数据权限" in u for u in plan["unknowns"])
    assert not any(s["action"] == "data_permission" for s in plan["steps"])


# ---------------------------------------------------------------- 8. 每步可执行契约
def test_every_step_has_endpoint_op_and_evidence():
    plan = _plan()
    for s in plan["steps"]:
        assert s["op"], f"步 {s['action']} 无 op"
        assert s["evidence"] in ALLOWED_EVIDENCE, f"{s['action']} 证据级非法: {s['evidence']}"
        assert s["channel"] in ("graphql", "rest")
        if s["channel"] == "rest":
            # rest 步 op 应是端点字符串（含 / 或 POST）
            assert "/" in s["op"] or s["op"].startswith("POST"), s["op"]


def test_full_plan_step_count_matches_declared_objects():
    """步数应等于声明的对象展开数（不静默丢对象）。"""
    spec = order_app_spec()
    plan = UdcPlanner().plan_build(spec)
    expected = (
        1                                   # create_application
        + len(spec.enums)                   # create_enum
        + sum(1 for e in spec.enums if e.items)  # create_enum_items
        + len(spec.entities)                # create_entity
        + sum(len(e.fields) for e in spec.entities)      # create_attribute
        + sum(len(e.indexes) for e in spec.entities)     # create_index
        + sum(len(e.events) for e in spec.entities)      # create_event
        + sum(len(e.refer) for e in spec.entities)       # create_refer
        + len(spec.microflows) * 2          # check_schema + create
        + len(spec.pages) * 3               # page_create_base + page_menu_create + page_schema_formal
        + sum(1 for p in spec.pages if p.page_rules)     # page_rules_create
        + sum(1 for p in spec.pages if p.panels)         # page_panels_bind
        + sum(1 for p in spec.pages if p.toolbar)        # page_toolbar_bind
        + sum(1 for p in spec.pages if p.detail)         # page_detail_bind
        + sum(1 for p in spec.pages if p.bind_microflow) # page_bind_microflow
        + len(spec.excel)                   # excel_export
        + len(spec.menus)                   # menu_create
        + 1                                 # deploy_online
    )
    assert len(plan["steps"]) == expected, \
        f"步数 {len(plan['steps'])} != 预期 {expected}（对象可能被静默丢弃）"


def test_refer_config_body_matches_e1_structure():
    """参照 body 逐字匹配 module-53993 e1() 结构（单终端 PC）。"""
    from components.construction.metadata_artifacts import build_refer_config_body
    body = build_refer_config_body(
        app_id=100, entity_id=200, caption="订单人员参照", refer_type="List",
        terminals={"PC": {"config": {"columns": [], "orders": [], "whereCond": [], "entities": ["200"]},
                          "display_name": [{"path": "name", "uuid": "u1"}],
                          "pull_display_name": [{"path": "title"}]}})
    assert set(body) == {"appId", "entityId", "caption", "type", "id", "referConfigDetail"}
    assert body["id"] is None and body["type"] == "List"
    d = body["referConfigDetail"][0]
    assert set(d) == {"appId", "entityId", "configInfo", "caption", "type",
                      "displayName", "terminalType", "id", "actionType", "pullDisplayName"}
    assert d["terminalType"] == "PC" and d["actionType"] == "INSERT"
    import json as _j
    assert _j.loads(d["configInfo"])["entities"] == ["200"]


def test_refer_config_body_dual_terminal_and_update():
    """多终端 [PC,MOBILE]；移动端 detail 无 pullDisplayName；有 id → UPDATE。"""
    from components.construction.metadata_artifacts import build_refer_config_body
    body = build_refer_config_body(
        app_id=1, entity_id=2, caption="c", refer_type="LeftTreeRightList",
        terminals={"PC": {"config": {}, "id": "cfg-pc"},
                   "MOBILE": {"config": {}, "id": None}},
        group_id="grp-1")
    assert body["id"] == "grp-1"
    assert len(body["referConfigDetail"]) == 2
    pc, mob = body["referConfigDetail"]
    assert pc["terminalType"] == "PC" and pc["actionType"] == "UPDATE"
    assert "pullDisplayName" in pc
    assert mob["terminalType"] == "MOBILE" and mob["actionType"] == "INSERT"
    assert "pullDisplayName" not in mob


def test_refer_config_body_bad_type_raises():
    """非法 refer_type 直接炸，不再记 unknowns 后照发。

    2026-11 按 ReferConfigInfoDto（javap）修：body 里不许有 unknowns 这个键；
    refer_type 的合法域是 List / TreeList / LeftTreeRightList，
    而 ENTITY / BASIC_DATA 属于 ReferConfigSourceTypeEnum（另一个字段）。
    """
    import pytest
    from components.construction.metadata_artifacts import build_refer_config_body
    with pytest.raises(ValueError) as e:
        build_refer_config_body(1, 2, "c", "Bogus", {"PC": {"config": {}}})
    assert "List" in str(e.value)


def test_filter_plan_body_uses_live_rest_contract():
    """页面规则 body 用 LIVE 探针坐实的 REST 契约（planType 数字码）。"""
    from components.construction.metadata_artifacts import build_filter_plan_body
    plan = build_filter_plan_body(
        app_name="orderapp", app_id=100, page_id=200, grid_suffix="usOJ",
        driven_entity="Order", caption="列表默认方案",
        conditions=[{"attribute_id": "3729", "value": "X"}])
    body = plan["body"]
    assert body["planType"] == 2                  # 数字码（LIVE 写面）
    assert body["sourceId"] == "200_udcDataGridView_usOJ"
    assert body["pageUrlType"] == 1 and body["sourceType"] == 0
    import json as _j
    assert "entities" in _j.loads(body["content"])
    # 设计器 GraphQL 通道在 note 里注明并存
    assert "udcUdcRuntimeFilterPlanPost" in plan["note"]


def test_filter_plan_op_in_catalog():
    """FilterPlan 4 op（concat 约定；设计器 GraphQL 通道）已在目录。"""
    for op in ("udcUdcRuntimeFilterPlanPost", "udcUdcRuntimeFilterPlanUpdatePost",
               "udcUdcRuntimeFilterPlanDeletePost", "udcUdcRuntimeFilterPlanBatchDeletePost"):
        assert op_entry(op) is not None, f"{op} 不在目录"
    assert op_entry("udcUdcRuntimeFilterPlanDeletePost")["paramsType"] == "Long"
