"""planner.plan_build 构建面接线测试 — 订单应用 spec→有序写操作契约。

契约锚点（docs/audit/udc-semantics/UDC-MAINLINE-AUDIT 主目标）：
- spec 声明的每个对象都出现在计划里（多实体/多字段/多微流程/多页面不漏对象）；
- 顺序：应用 → 实体(逐字段) → 微流程(checkSchema→create) → 页面(base→菜单) → 部署；
- 每步带 channel + evidence 分级（GraphQL=STATIC_CATALOG，微流程=LIVE_SMOKE，
  页面=OBSERVED_LIVE，部署=STATIC_CATALOG）；
- 部署标 destructive（宿主须先确认）；
- agent 不出写：executed/writes_performed 恒 False；
- spec 未声明项（索引/事件/选项集）落 unknowns，不臆造生成；
- 既有 plan()/plan_application() 只读契约不变（write_operations==[]）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.models import (
    ApplicationSpec, EntitySpec, FieldSpec, PageSpec, MicroFlowSpec,
    IndexSpec, EventSpec, ReferSpec, MenuSpec, EnumOptionSpec, ExcelSpec)
from components.udc.planner import UdcPlanner


def _order_spec():
    return ApplicationSpec(
        name="orderapp", caption="订单应用",
        entities=[
            EntitySpec("Order", fields=[
                FieldSpec("orderNo", "STRING", length=64, required=True),
                FieldSpec("status", "ENUM"),
                FieldSpec("buyer", "ENTITY"),
            ]),
            EntitySpec("OrderDetail", fields=[FieldSpec("qty", "INTEGER")]),
        ],
        pages=[PageSpec("OrderList", page_url="/order/list"), PageSpec("OrderDetailPage")],
        microflows=[MicroFlowSpec("SaveOrder", trigger="MANUAL"),
                    MicroFlowSpec("OnOrderEvent", trigger="BUSINESS_EVENT")],
    )


def test_plan_build_sequence_order():
    plan = UdcPlanner().plan_build(_order_spec())
    actions = [s["action"] for s in plan["steps"]]
    assert actions == [
        "create_application",
        "create_entity", "create_attribute", "create_attribute", "create_attribute",
        "create_entity", "create_attribute",
        "microflow_check_schema", "microflow_create",
        "microflow_check_schema", "microflow_create",
        "page_create_base", "page_menu_create", "page_schema_formal",
        "page_create_base", "page_menu_create", "page_schema_formal",
        "deploy_online",
    ]
    # seq 连续
    assert [s["seq"] for s in plan["steps"]] == list(range(1, len(actions) + 1))


def test_plan_build_evidence_grading():
    plan = UdcPlanner().plan_build(_order_spec())
    by_action = {}
    for s in plan["steps"]:
        by_action.setdefault(s["action"], set()).add(s["evidence"])
    assert by_action["create_application"] == {"STATIC_CATALOG"}
    assert by_action["create_entity"] == {"LIVE"}   # live_template 升级（datamigration 实证）
    assert by_action["create_attribute"] == {"STATIC_CATALOG"}
    assert by_action["microflow_check_schema"] == {"LIVE_SMOKE"}
    assert by_action["microflow_create"] == {"LIVE_SMOKE"}
    assert by_action["page_create_base"] == {"LIVE"}   # live_template（datamigration 实证）
    assert by_action["page_menu_create"] == {"OBSERVED_LIVE"}   # 原级保留（live_template 只升级低级证据）
    assert by_action["deploy_online"] == {"STATIC_CATALOG"}


def test_plan_build_no_agent_writes_and_destructive_marked():
    plan = UdcPlanner().plan_build(_order_spec())
    assert plan["executed"] is False
    assert plan["writes_performed"] is False
    deploy = [s for s in plan["steps"] if s["action"] == "deploy_online"]
    assert deploy and deploy[0].get("destructive") is True
    assert all(s["executed"] is False for s in plan["steps"])


def test_plan_build_undeclared_objects_go_to_unknowns_not_steps():
    plan = UdcPlanner().plan_build(_order_spec())
    actions = {s["action"] for s in plan["steps"]}
    # _order_spec() 未声明 索引/事件/选项集/参照/菜单/Excel → 不生成对应步骤
    # （spec 模型已扩展可声明这些对象，未声明=宿主按需省略，planner 不臆造生成）
    assert not ({"create_index", "create_event", "create_enum",
                 "create_refer", "update_refer", "menu_create", "excel_export"} & actions)


def test_plan_build_invalid_trigger_recorded():
    spec = ApplicationSpec("x", "x", microflows=[MicroFlowSpec("f", trigger="CRON")])
    plan = UdcPlanner().plan_build(spec)
    assert any("CRON" in u and "不在" in u for u in plan["unknowns"])
    # 即使 trigger 非法，微流程步骤仍生成（宿主可修 trigger 后执行）
    assert [s["action"] for s in plan["steps"] if "microflow" in s["action"]] == [
        "microflow_check_schema", "microflow_create"]


def test_plan_build_write_operations_summary_matches_steps():
    plan = UdcPlanner().plan_build(_order_spec())
    assert len(plan["write_operations"]) == len(plan["steps"])
    for i, w in enumerate(plan["write_operations"], start=1):
        assert w["seq"] == i
        assert w["op"] == plan["steps"][i - 1]["op"]
        assert w["channel"] == plan["steps"][i - 1]["channel"]
        assert w["evidence"] == plan["steps"][i - 1]["evidence"]


def test_entity_fields_all_covered_no_dup_loss():
    """多字段不漏对象（orderNo/status/buyer + OrderDetail.qty）。"""
    plan = UdcPlanner().plan_build(_order_spec())
    attr_targets = [s["target"] for s in plan["steps"] if s["action"] == "create_attribute"]
    assert attr_targets == [
        "Order.orderNo", "Order.status", "Order.buyer", "OrderDetail.qty"]


def test_plan_readonly_contract_unchanged():
    """既有只读契约：plan() 永不产写操作。"""
    spec = _order_spec()
    plan = UdcPlanner().plan(spec)
    assert plan["mode"] == "dry-run"
    assert plan["write_operations"] == []
    assert all(s["action"].startswith("inspect_") for s in plan["steps"])
    pa = UdcPlanner().plan_application(spec)
    assert pa.mode == "dry-run" and pa.write_operations == []


def _full_spec():
    """订单应用全语义 spec：声明索引/事件/选项集/参照/菜单/Excel/页面工具栏/规则/面板/详情/微流程绑定。"""
    return ApplicationSpec(
        name="orderapp", caption="订单应用",
        enums=[EnumOptionSpec("orderStatus", "订单状态",
                              items=[{"code": 1, "caption": "新订单", "name": "NEW"}])],
        entities=[EntitySpec(
            "Order", caption="订单", stereotype="单据",
            fields=[
                FieldSpec("orderNo", "STRING", length=64, required=True, uniqueness=True),
                FieldSpec("status", "ENUM", enum_name="orderStatus"),
                FieldSpec("buyer", "ENTITY", multi_select=True,
                          reference={"relationApp": "organization",
                                     "relationEntity": "OrgMember"}),
            ],
            indexes=[IndexSpec("idx_order_no", "NORMAL", ["orderNo"])],
            events=[EventSpec("onCreate", "创建时")],
            refer=[ReferSpec("订单参照", "OrderDetail")],
            data_permission=True,
        )],
        menus=[MenuSpec("订单菜单", page="OrderList", icon="order")],
        excel=[ExcelSpec("Order", "export", data=[{"orderNo": "O1"}])],
        pages=[PageSpec("OrderList", page_url="/order/list", page_type="LIST",
                        toolbar=["新增", "查询", "测试1"],
                        detail={"穿透": "详情"},
                        panels=[{"caption": "流转日志"}],
                        page_rules=[{"caption": "默认过滤"}],
                        columns=[{"field": "orderNo", "width": 120}],
                        bind_microflow="SaveOrder")],
        microflows=[MicroFlowSpec("SaveOrder", trigger="MANUAL",
                                   group_type="VALIDATE", source_id="Order")],
        app_stereotype="单据",
    )


def test_full_spec_generates_all_declared_steps():
    plan = UdcPlanner().plan_build(_full_spec())
    actions = [s["action"] for s in plan["steps"]]
    # 全声明对象都有对应步骤
    for act in ("create_enum", "create_enum_items", "create_index", "create_event",
                "create_refer", "menu_create", "excel_export",
                "page_rules_create", "page_panels_bind", "page_toolbar_bind",
                "page_detail_bind", "page_bind_microflow"):
        assert act in actions, f"{act} 未生成: {actions}"
    # 序列：枚举先于实体（被字段引用）；实体→索引→事件→参照；微流程 group_type 入 note
    assert actions.index("create_enum") < actions.index("create_entity")
    for s in plan["steps"]:
        if s["action"] == "microflow_check_schema":
            assert "VALIDATE" in s["note"] and "sourceId=Order" in s["note"]


def test_full_spec_refer_creates_not_updates_without_id():
    plan = UdcPlanner().plan_build(_full_spec())
    refer = [s for s in plan["steps"] if s["action"].endswith("refer") and s["action"] != "page_bind_microflow"]
    assert refer and refer[0]["action"] == "create_refer"
    assert refer[0]["op"] == "udcReferConfigCreateConfigInfoPost"


def test_spec_to_dict_serializes_full_semantics():
    d = _full_spec().to_dict()
    assert d["enums"][0]["items"][0]["code"] == 1
    ent = d["entities"][0]
    assert ent["indexes"][0]["fields"] == ["orderNo"]
    assert ent["events"][0]["name"] == "onCreate"
    assert ent["refer"][0]["entity"] == "OrderDetail"
    assert ent["data_permission"] is True
    assert d["menus"][0]["page"] == "OrderList"
    assert d["excel"][0]["direction"] == "export"
    pg = d["pages"][0]
    assert pg["toolbar"] == ["新增", "查询", "测试1"]
    assert pg["bind_microflow"] == "SaveOrder"
    assert d["microflows"][0]["group_type"] == "VALIDATE"


def test_create_event_uses_create_with_data_op():
    """§2.8.2① 坐实：事件 tab 主链走 udcEventCreateWithDataPost（非 udcEventPost）。"""
    plan = UdcPlanner().plan_build(_full_spec())
    ev = [s for s in plan["steps"] if s["action"] == "create_event"]
    assert ev and ev[0]["op"] == "udcEventCreateWithDataPost"
    assert "build_event_with_data_body" in ev[0]["body_builder"]


def test_body_builder_refs_resolve_to_real_symbols():
    """防指错模块：每个被引用的 模块.符号 必须真能 import + 存在。

    历史坑：曾把 construction/metadata_artifacts 写成裸 metadata_artifacts.*，
    宿主会去 udc/ 找而落空。此测试钉住引用可解析。
    """
    import importlib
    import re
    refs = []   # (module, symbol) 显式登记 planner 允许引用的构造器入口
    for s in UdcPlanner().plan_build(_full_spec())["steps"]:
        bb = s.get("body_builder", "")
        for m in re.finditer(r"([a-z_]+(?:\.[a-z_]+)*)\.([A-Za-z_]\w*)", bb):
            mod, sym = m.group(1), m.group(2)
            if mod.startswith("construction.") or mod in (
                    "attribute_semantics", "layout_model", "function_node_model",
                    "excel_model", "deploy_chain_model"):
                refs.append((mod, sym))
    assert refs, "计划里没有可解析的 body_builder 引用"
    for mod, sym in refs:
        full = mod if mod.startswith("components.") or mod.startswith("construction") else f"components.udc.{mod}"
        if mod.startswith("construction"):
            full = f"components.{mod}"
        m = importlib.import_module(full)
        assert hasattr(m, sym), f"{full}.{sym} 不存在（body_builder 指错模块）"
