"""Design-time construction/deployment write-chain contracts + deploy_plan data (R18).

agent 不出写：写契约 gate 仍 DENIED（layer.py write/effective 判定不变）；
本模块固化的是「可执行方案 data」——宿主（Hermes/CC/Codex）按 steps 执行。
证据基线：test2 活体 2026-09-24 全链（建实体 7670732978062038177 → 4 属性 →
RELEASE 构建 udc_deploy_record deploy_type=2 state=1 → 物理表
yanshouda_m5654091886000795633 @ 9000000000000000001_test2）。
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from components.platform_operations.registry import UdcOperationRegistry
from components.platform_operations.layer import PlatformOperationLayer
from components.platform_operations.models import OperationIntent, OperationStatus
from components.platform_operations import udc as udc_adapters
from components.platform_operations.deployment import (
    build_deployment_plan, infer_datatype, STEREO_TYPES, DATATYPES,
    DEPLOY_TYPES, PROJECT_TYPES, TERMINAL_TYPES, SCHEMA_ID,
)


def test_deploy_write_contract_registered_observed_live():
    reg = UdcOperationRegistry.default()
    c = reg.get("udc.deploy.normal")
    assert c.write is True
    assert c.status == OperationStatus.OBSERVED
    assert c.method == "POST"
    assert c.path == "udc/runtime/deploy-normal", "类级前缀 udc/runtime（09-27 LIVE 确诊，旧记裸 deploy-normal 会 404）"
    assert "deployType(TEST|RELEASE|ON_ONLINE|DELTA)" in c.required_inputs
    assert any(e.get("evidence_level") == "OBSERVED_LIVE" for e in c.evidence)


def test_deploy_read_contract_upgraded_to_observed_by_appversion_face():
    """udc.deploy.search_status 已被 09-28 LIVE 实证升级：真面 = POST application/appVersion/{appGuid}。"""
    reg = UdcOperationRegistry.default()
    c = reg.get("udc.deploy.search_status")
    assert c.status == OperationStatus.OBSERVED
    assert c.path == "application/appVersion/{appGuid}"
    assert "appGuid" in c.required_inputs
    assert any("appVersion/{appGuid}" in (e.get("note") or "") for e in c.evidence)


def test_write_contract_gated_denied_by_default():
    from components.platform_operations.models import ExecutionContext
    reg = UdcOperationRegistry.default()
    layer = PlatformOperationLayer(reg, udc_adapters.UdcReadAdapter(
        udc_adapters.UdcApplicationAdapter(reg), udc_adapters.UdcEntityAdapter(reg)), gateway_adapter=None)
    ctx = ExecutionContext(session_id="s", run_id="r", principal_id="p", credential_ref="test2-web-credential")
    session: list[dict] = []
    result = layer.execute(OperationIntent("udc.deploy.normal", "app9000000000000000001"),
                           execution_context=ctx, session=session)
    assert result.status == OperationStatus.DENIED, "写契约在 readonly 执行链必须 DENIED"


def test_deploy_plan_steps_cover_entity_attributes_pages_and_build():
    plan = build_deployment_plan(
        "app9000000000000000001", "YanshouDan", "验收单",
        [{"name": "acceptanceDate", "caption": "验收日期"},
         {"name": "acceptor", "caption": "验收人"},
         {"name": "conclusion", "caption": "结论"},
         {"name": "amount", "caption": "金额"}],
        deploy_type="RELEASE")
    ops = [s["op"] for s in plan["steps"]]
    assert ops == ["udc.entity.create", "udc.entity.attribute.create",
                   "udc.page.create", "udc.deploy.normal"], "顺序：实体→属性→建页(LIST+DETAIL)→构建"
    assert plan["readonly_plan"] is True
    assert plan["schema"] == SCHEMA_ID
    pages = plan["steps"][2]["body"]
    assert [p["pageType"] for p in pages] == ["LIST", "DETAIL"]
    for p in pages:
        assert p["curTerminalType"] == "PC"
        assert p["pageItems"] and p["pageItems"][0]["actionType"] == "NORMAL"
        assert p["masterEntityIds"] == "<entity_id>", "宿主执行时用实体 create 返回的 id 替换"
    # 枚举值域全带
    assert plan["enums"]["deployTypes"] == list(DEPLOY_TYPES)
    assert "RELEASE" in plan["enums"]["deployTypes"]


def test_deploy_plan_entity_body_matches_live_observed_shape():
    plan = build_deployment_plan("3289082814923688017", "X", "X", [])
    body = plan["steps"][0]["body"]
    assert body["appId"] == 3289082814923688017
    assert body["stereotype"] == "bill"
    assert body["entityNature"] == "MAIN"
    assert body["features"].startswith("basic,")


def test_datatype_inference_is_conservative_and_flagged():
    assert infer_datatype("amount", None) == ("DECIMAL", False)
    assert infer_datatype("acceptor", None) == ("STRING", False)
    assert infer_datatype("x", "DECIMAL") == ("DECIMAL", True)
    assert infer_datatype("x", "java.math.BigDecimal") == ("DECIMAL", True)
    plan = build_deployment_plan("1", "X", "X", [{"name": "weirdField"}])
    assert any("weirdField" in u for u in plan["unknowns"]), "未证实 dataType 必须进 unknowns"


def test_stereotype_out_of_domain_flagged():
    plan = build_deployment_plan("1", "X", "X", [], stereotype="notareal")
    assert any("notareal" in u for u in plan["unknowns"])


def test_value_domains_are_live_snapshots_not_invented():
    # 值域来源：169 实体回读 + 51 属性回读（OBSERVED_LIVE 证据在 deployment.py 注释）
    assert set(STEREO_TYPES) == {"archive", "standard", "bill", "archiveTree"}
    assert set(PROJECT_TYPES) == {"FRONTEND", "BACKEND", "ALL"}
    assert set(TERMINAL_TYPES) == {"ALL", "PC", "MOBILE"}
    assert {"ENTITY", "DATETIME", "ENUM", "STRING", "DECIMAL", "DATE", "BIGINTEGER"} <= set(DATATYPES)


def test_deploy_normal_body_must_be_wrapped_in_deploydto():
    """@MultiRequestBody 按形参名取子对象：平铺 body → DTO=null → EL1007E（09-27 LIVE 反证）。

    路径同批确诊：类级 @RequestMapping("udc/runtime") + 方法级 deploy-normal。
    """
    plan = build_deployment_plan("3289082814923688017", "X", "X", [])
    step = plan["steps"][3]
    assert step["op"] == "udc.deploy.normal"
    assert step["path"] == "/service/udc/runtime/deploy-normal"
    assert set(step["body"]) == {"deployDto"}, "必须按形参名包裹，平铺即 DTO=null"
    assert step["body"]["deployDto"]["appId"] == 3289082814923688017
    assert step["body"]["deployDto"]["projectType"] == "ALL"
    assert step["body"]["deployDto"]["terminalType"] == "ALL"
