# -*- coding: utf-8 -*-
"""MCP 44 个工具的全量冒烟测试（2026-11-09）。

与 `test_mcp_server.py` 的分工：
  test_mcp_server.py  协议面（initialize / tools/list / tools/call / 错误码 / 写红线）
  本文件              业务面（每个工具用合法参数真调一次，断言输出结构）

★ 判据不是「不抛异常」，而是「输出里有该有的键」。
  一个返回 `{}` 的工具在这里会红 —— 空壳比崩溃更危险。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


@pytest.fixture(scope="module")
def caps():
    from xiaozhua_host_bootstrap import bootstrap
    return bootstrap()


APP = "9000000000000000001"
ENTITY = "7000000000000000001"
GUID = "8000000000000000001"

# 每个工具一组合法参数 + 必须出现的键
CASES = {
    # ---- 跨模块 ----
    "dispatch": ({"intent": "inspect", "target": "request"}, ("status",)),
    "generate": ({"application_id": APP, "entity_name": "SmokeEntity"}, ("status",)),
    "generate_from_requirement": ({"text": "建一个测试实体", "application_id": APP}, ("status",)),
    "live_probe": ({}, ("status",)),
    "capability_index": ({}, ("domains", "summary")),
    "spi_catalog": ({}, ("status", "conclusion_docs")),

    # ---- entity ----
    "deploy_plan": ({"application_id": APP, "entity_name": "SmokeEntity",
                     "attributes": [{"name": "smokeName", "type": "STRING",
                                     "caption": "名称"}]},
                    ("steps", "schema")),
    "index_body": ({"caption": "idx", "entity_id": int(ENTITY),
                    "field_ids": [1, 2]}, ("caption",)),
    "dto_body": ({"app_id": int(APP[-10:]), "caption": "DTO",
                  "name": "SmokeDto",
                  "attributes": [{"name": "f1", "caption": "字段1"}]}, None),
    "refer_config_body": ({"app_id": int(APP[-10:]), "entity_id": int(ENTITY),
                           "caption": "参照", "refer_type": "List",
                           "terminals": {"PC": {"config": {}, "display_name": []}}},
                          ("referConfigDetail", "type")),

    # ---- 客开落点（跨模块）----
    "code_targets": ({"target": "custom_page", "app_name": "demo",
                      "page_url": "myPage"},
                     ("files", "route", "constraints", "meaning")),
    "repo_state": ({"repo_dir": "."}, ("ok", "repoDir", "branch")),
    "repo_sync": ({"repo_dir": ".", "action": "pull", "confirm": True},
                  ("ok",)),
    "project_shape": ({"backend_dir": "."}, ("shape",)),
    "repo_url": ({"app_name": "demo", "git_base": "https://git.example/ext"},
                 ("ok", "url")),

    # ---- application（应用内功能页：依赖/构建/版本）----
    "app_dependency_body": ({"app_id": APP, "dep_app_name": "xiaozhua-notice",
                             "dep_app_caption": "公告应用",
                             "dep_app_version": "5.3.98"},
                            ("op", "body", "dependentAppType")),
    "app_dependency_remove": ({"row_id": "123456789"},
                              ("mode", "op", "body")),
    "app_deploy_body": ({"app_id": APP}, ("op", "body", "isWrite")),
    "app_version_list": ({"app_name": "demo" + APP}, ("url", "body")),
    "app_build_info": ({"app_id": APP}, ("query", "variables")),

    # ---- rule ----
    "entity_rule_body": ({"app_id": APP, "entity_id": ENTITY,
                          "name": "smokeRule", "caption": "冒烟规则",
                          "group_type": 1},
                         ("dataSchema", "state", "groupType", "sourceId")),

    # ---- setting ----
    "enum_body": ({"app_id": 1, "caption": "枚举", "name": "SmokeEnum"}, ("name",)),
    "enum_item_body": ({"app_id": 1, "enum_id": 2, "caption": "项",
                        "item_value": "ONE", "enum_code": "ONE",
                        "order_no": 1}, ("itemValue", "parentId")),
    "enum_category_body": ({"app_id": 1, "name": "SmokeCat"}, ("name", "appId")),
    "event_body": ({"app_id": 1, "caption": "事件", "event_name": "smokeEvent",
                    "dto_id": 3}, ("name", "actionType", "eventDataType")),
    "event_data_body": ({"app_id": 1, "caption": "事件", "event_name": "smokeEvent",
                         "entity_id": 3, "attrs": []}, ("name", "eventDataList")),
    "option_set_category_body": ({"app_id": APP, "app_guid": GUID,
                                  "name": "SmokeOptCat", "caption": "选项分组"},
                                 ("appGuid", "parentId")),
    "option_set_body": ({"app_id": APP, "app_guid": GUID, "name": "SmokeOpt",
                         "caption": "选项集", "category_id": 5},
                        ("categoryId", "appGuid")),
    "option_set_item_body": ({"app_id": APP, "app_guid": GUID, "enum_id": 6,
                              "name": "ONE", "caption": "选项甲", "code": 1},
                             ("enumId", "code")),
    "attribute_set_body": ({"app_id": APP, "name": "SmokeSet", "caption": "字段集"},
                           ("sourceType", "attributes")),
    "attribute_set_field_body": ({"app_id": APP, "set_id": 7, "name": "smokeField",
                                  "caption": "字段"}, ("sourceType", "entityId",
                                                       "sourceId", "widgetConfig", "0")),
    "scalability_option_body": ({"app_id": APP, "name": "SmokeScale",
                                 "caption": "扩展方案"},
                                ("scalabilityDtoList", "attributeDtoList")),
    "scalability_field_body": ({"app_id": APP, "option_id": 8, "prefix": "smokeExt",
                                "caption": "扩展字段", "count": 3},
                               ("prefix", "count", "dataType", "optionId")),
    "qrcode_body": ({"app_id": APP, "app_guid": GUID, "name": "冒烟码",
                     "entity_full_name": "com.x.Entity",
                     "value_field_code": "code"},
                    ("type", "linkType", "appGuid")),
    "parameter_body": ({"app_id": APP, "app_guid": GUID, "name": "smokeParam",
                        "caption": "参数"}, ("dataTypeProperties", "appGuid")),
    "excel_template_body": ({"app_id": APP, "app_guid": GUID, "name": "smokeTpl",
                             "caption": "模板", "main_full_name": "com.x.Entity",
                             "columns": [{"attributeFullName": "com.x.Entity.name",
                                          "displayName": "名称",
                                          "dataType": "STRING"}]},
                            ("isCustom", "metadataContent", "excelHeadInfo", "sheets")),
    "excel_template_column": ({"attribute_full_name": "com.x.Entity.name",
                               "display_name": "名称"},
                              ("attributeFullName", "displayName")),

    # ---- serial ----
    "serial_section": ({"size": 4, "section_type": "SERIAL"}, ("size", "type",
                                                              "sectionRank")),
    "serial_scheme_body": ({"app_id": APP, "app_guid": GUID, "code": "SMOKE",
                            "name": "冒烟编号",
                            "sections": [{"size": 2, "type": "CONSTANT", "value": "HT"},
                                         {"size": 4, "type": "SERIAL"}]},
                           ("totalSize", "serialSectionDtoList", "serialResetRule")),

    # ---- flow ----
    "microflow_create_body": ({"name": "smokeFlow", "caption": "冒烟流程",
                               "application_id": APP,
                               "data_schema": {"nodes": []}}, ("name", "dataSchema")),
    "microflow_node": ({"action": "create_variable", "title": "冒烟变量",
                        "data_type": "STRING"},
                       ("nodeId", "actionType", "type")),
    "microflow_node_actions": ({}, ("count", "actions")),
    "signature_search": ({"query": "ApprovalAppService", "limit": 2},
                         ("matched_classes", "classes")),
    "microflow_service_catalog": ({"query": "ApprovalAppService", "limit": 2},
                                  ("matched_services", "services")),
    "ui_component_catalog": ({"query": "Button", "limit": 2},
                             ("matched_components", "components")),
    "microflow_gates": ({"schema": {"nodes": [],
                                    "endNode": {"type": "END", "actionType": "END_NODE",
                                                "nodeId": "MFEndNode"}}},
                        ("ok", "count", "problems")),
    "microflow_capability": ({}, ("summary",)),
    "microflow_trigger": ({"kind": "SCHEDULE", "job_caption": "冒烟任务"},
                          ("nodeId", "scheduleCronRule")),
    "microflow_data_schema": ({"name": "smokeFlow", "caption": "冒烟流程",
                               "trigger": {"nodeId": "MFStartNode", "type": "MANUAL"},
                               "nodes": []},
                              ("endNode", "nodes", "trigger", "sourceType")),

    # ---- expression ----
    "expression_catalog": ({"kind": "function"}, ("count", "items")),

    # ---- page ----
    "list_page_schema": ({"application_id": APP, "entity_name": "SmokeEntity",
                          "caption": "冒烟实体",
                          "attributes": [{"name": "smokeName", "type": "STRING",
                                          "caption": "名称"}]}, None),
    "detail_page_schema": ({"application_id": APP, "entity_name": "SmokeEntity",
                            "caption": "冒烟实体",
                            "attributes": [{"name": "smokeName", "type": "STRING",
                                            "caption": "名称"}]}, None),
    "filter_plan_body": ({"app_name": "smoke" + APP, "app_id": int(APP[-10:]),
                          "page_id": 1, "grid_suffix": "grid",
                          "driven_entity": "com.x.Entity", "caption": "过滤",
                          "conditions": []}, None),
    "custom_page_scaffold": ({"page_url": "smokePage", "app_id": APP},
                             ("target_path", "artifact", "route", "source")),
}


def test_every_tool_has_a_case(caps):
    """44 个工具里，除 4 个需凭据的，其余每一个都要有合法参数用例。

    这条防止「新加工具忘了补测试」—— 加工具不加用例直接红。
    """
    from adapters.mcp.server import TOOL_KEYS
    cred = {"microflow_publish", "expression_verify", "expression_filter",
            "entity_rule_publish"}
    missing = [k for k in TOOL_KEYS if k not in cred and k not in CASES]
    assert not missing, "以下工具没有冒烟用例，请补进 CASES：%s" % missing


@pytest.mark.parametrize("key", sorted(CASES))
def test_tool_returns_expected_shape(caps, key):
    """用合法参数真调一次，断言输出是 dict/list 且含必须键。"""
    args, expect_keys = CASES[key]
    fn = caps[key]
    result = fn(**args)

    assert result is not None, "%s 返回 None" % key
    assert isinstance(result, (dict, list)), "%s 返回 %s" % (key, type(result))

    # 空壳判据：绝不能是空 dict / 空 list
    assert result, "%s 返回空值（%r）—— 空壳比崩溃更危险" % (key, result)

    if expect_keys:
        assert isinstance(result, dict), "%s 有必须键但返回 %s" % (key, type(result))
        missing = [k for k in expect_keys if k not in result]
        assert not missing, "%s 输出缺键 %s（实际有 %s）" % (
            key, missing, sorted(result))


@pytest.mark.parametrize("key", sorted(CASES))
def test_tool_output_is_json_serializable(caps, key):
    """输出必须能直接 JSON 序列化 —— MCP content 是 JSON 文本。"""
    args, _ = CASES[key]
    result = caps[key](**args)
    text = json.dumps(result, ensure_ascii=False, default=str)
    assert len(text) > 2, "%s 序列化后为空" % key


def test_credential_tools_expose_all_auth_entries():
    """4 个凭据工具必须暴露 host / cookie / cdp_port 三种授权入口。

    cdp_port 是首选：请求由浏览器页面发出，cookie 不离开浏览器。
    导出 token 到本地再重放，等于把用户身份复制一份。
    """
    import inspect
    from xiaozhua_host_bootstrap import bootstrap
    b = bootstrap()
    for key in ("microflow_publish", "expression_verify", "expression_filter",
                "entity_rule_publish"):
        sig = inspect.signature(b[key])
        for p in ("host", "cookie", "cdp_port"):
            assert p in sig.parameters, "%s 缺参数 %s" % (key, p)


def test_entity_rule_publish_refuses_without_any_auth():
    """无 cdp_port 也无 host+cookie 时必须拒绝，不能静默跑。"""
    from xiaozhua_host_bootstrap import bootstrap
    b = bootstrap()
    dto = b["entity_rule_body"]("1", "2", "r1", group_type=1)
    r = b["entity_rule_publish"](dto)
    assert r["ok"] is False
    assert "cdp_port" in r["reason"]


def test_app_dependency_frontend_requires_extra_fields(caps):
    """FRONTEND 组件依赖缺那 10 个字段时必须拒绝构造，不能悄悄发出不生效的请求。"""
    with pytest.raises(ValueError) as ei:
        caps["app_dependency_body"](APP, "biz-lock", "锁组件", "1.0.0",
                                    dependent_app_type="FRONTEND")
    msg = str(ei.value)
    assert "packageType" in msg and "FRONTEND" in msg, \
        "拒绝时必须告诉调用方缺哪些字段，实际：%s" % msg


def test_app_dependency_frontend_accepts_full_extra(caps):
    """补齐 10 个字段后必须放行，且行字段数 = 6 基础 + 10 额外。"""
    shape = {"description": "", "dynamicModuleGroup": "", "dynamicService": True,
             "enableDelete": True, "needGenerate": False, "sort": 1,
             "supportUpgrade": True, "terminalType": "PC",
             "sourceType": "CUSTOMIZE", "packageType": "CONTROL"}
    r = caps["app_dependency_body"](APP, "biz-lock", "锁组件", "1.0.0",
                                    dependent_app_type="FRONTEND", extra=shape)
    assert r["missingFrontendFields"] == [], r["missingFrontendFields"]
    row = r["body"]["variables"]["params0"][0]
    assert len(row) == 16, "应为 6 基础 + 10 额外，实际 %d: %s" % (len(row), sorted(row))


def test_app_dependency_remove_paths_differ(caps):
    """应用依赖走 GraphQL 单删，组件依赖走 REST 批删 —— 两条路不能混。"""
    single = caps["app_dependency_remove"]("123456789")
    assert single["mode"] == "app_graphql_single"
    assert "graphql" in single["endpoint"]

    batch = caps["app_dependency_remove"](ids=["111", "222"])
    assert batch["mode"] == "component_rest_batch"
    assert "dependent-application/delete-by-ids" in batch["url"]
    assert batch["body"] == {"ids": ["111", "222"]}


def test_app_dependency_remove_rejects_non_numeric_row_id(caps):
    """传 appId / depAppName 当 row_id 必须被拒 —— 平台不报错但删不掉，是实测踩过的坑。"""
    with pytest.raises(ValueError):
        caps["app_dependency_remove"]("xiaozhua-notice")


def test_repo_url_refuses_without_git_base():
    """没 git_base 且无法反推时必须报缺，不能猜域名。

    这是 2026-11-10 的实际教训：把 gitlab.<客户域名>/extend-<env> 写死，
    换环境直接 404，且报「仓库不存在」把人带偏。
    """
    from xiaozhua_host_bootstrap import bootstrap
    r = bootstrap()["repo_url"]("demo", "")
    assert r["ok"] is False
    assert "git_base" in r["reason"]
    assert "url" not in r


def test_code_targets_custom_page_path_and_restart_warning():
    """自定义页面必须给出正确路径、路由，并提示重启 dev server。"""
    from xiaozhua_host_bootstrap import bootstrap
    t = bootstrap()["code_targets"]("custom_page", "demoApp", page_url="myPage")
    assert t["files"][0]["path"] == "pc/src/pages/myPage/customPage.tsx"
    assert t["route"].endswith("/demoApp/myPage")
    assert any("重启" in c for c in t["constraints"]), t["constraints"]


def test_code_targets_spi_points_at_extend_only():
    """SPI 落点只能是 extend/，且必须提示「扩展点要自己注册」。"""
    from xiaozhua_host_bootstrap import bootstrap
    t = bootstrap()["code_targets"]("spi", "demoApp", backend_dir=".",
                                    extension_point="Importable")
    assert "extend" in t["files"][0]["path"]
    assert any("注册" in c for c in t["constraints"]), t["constraints"]


def test_project_shape_unknown_for_missing_dir():
    """目录不存在时必须回 UNKNOWN，不能崩、不能瞎猜五模块。"""
    from xiaozhua_host_bootstrap import bootstrap
    r = bootstrap()["project_shape"]("/nonexistent/path/xyz")
    assert r["shape"] == "UNKNOWN"


def test_repo_state_rejects_non_repo():
    """不是 git 仓库时必须回 ok=False + reason，不能假装成功。"""
    from xiaozhua_host_bootstrap import bootstrap
    r = bootstrap()["repo_state"]("/nonexistent/repo/xyz")
    assert r["ok"] is False
    assert "reason" in r


def test_repo_state_is_readonly():
    """repo_state 不得暴露任何写动作 —— commit/push 必须走单独入口并显式确认。"""
    import inspect
    from xiaozhua_host_bootstrap import bootstrap
    sig = inspect.signature(bootstrap()["repo_state"])
    names = set(sig.parameters)
    for forbidden in ("commit", "push", "action", "force", "confirm"):
        assert forbidden not in names, (
            "repo_state 不该有 %r 参数 —— 读接口不给写入口" % forbidden)


def test_repo_sync_requires_confirm():
    """没有 confirm=True 时必须拒绝 —— 写能力不得默认可用。"""
    from xiaozhua_host_bootstrap import bootstrap
    r = bootstrap()["repo_sync"](".", "commit", False, "msg", ["x"])
    assert r["ok"] is False
    assert "confirm" in r["reason"]


def test_repo_sync_rejects_bulk_add():
    """commit 拒绝对全量通配 —— 一个 add -A 会把别的会话改动一起带进提交。"""
    from xiaozhua_host_bootstrap import bootstrap
    b = bootstrap()
    for bad in (["."], ["-A"], ["*"], []):
        r = b["repo_sync"](".", "commit", True, "msg", bad)
        assert r["ok"] is False, "paths=%r 应被拒" % bad


def test_repo_sync_rejects_unknown_action():
    from xiaozhua_host_bootstrap import bootstrap
    r = bootstrap()["repo_sync"](".", "rm", True)
    assert r["ok"] is False
    assert "pull" in r["reason"]


def test_repo_sync_required_confirm_in_schema():
    """confirm 必须进 inputSchema.required —— 有默认值就等于默认可写。"""
    from xiaozhua_host_bootstrap import bootstrap
    from adapters.mcp.server import TOOL_KEYS, build_tool_schemas
    b = bootstrap()
    sch = {s["name"]: s for s in build_tool_schemas({k: b[k] for k in TOOL_KEYS})}
    req = set(sch["xiaozhua_repo_sync"]["inputSchema"].get("required") or [])
    assert "confirm" in req, "confirm 必须必填，实际 required=%s" % sorted(req)


def test_entity_rule_type_is_entity_rule_not_entity():
    """★ 回归守卫：type 必须是 ENTITY_RULE。

    2026-11-10 实测：写成 "ENTITY" 平台直接
    BOOT_3002「No enum constant com.seeyon.udc.common.enums.MicroFlowTypeEnum.ENTITY」。
    真值是 MicroFlowTypeEnum: SERVICE(0) FRONTEND(1) ENTITY_RULE(2) CUSTOM(3) FUNCTION(4)。

    这条以前只断言字段存在，没断言值 —— 所以错误的枚举一路进了工具面。
    """
    from xiaozhua_host_bootstrap import bootstrap
    dto = bootstrap()["entity_rule_body"]("1", "2", "r1", "规则1", group_type=1)
    assert dto["type"] == "ENTITY_RULE", (
        "type 必须是 ENTITY_RULE，实际 %r —— 写 ENTITY 平台会 BOOT_3002" % dto["type"])


def test_entity_rule_group_type_maps_and_state_release():
    """groupType 三种取值 + state 默认 20（RELEASE）。"""
    from xiaozhua_host_bootstrap import bootstrap
    b = bootstrap()
    for gt in (1, 2, 3):
        d = b["entity_rule_body"]("1", "2", "r%s" % gt, group_type=gt)
        assert d["groupType"] == str(gt)
        assert d["state"] == 20, "state 必须默认 20，写 10 在列表接口查不到等于隐形"

def test_serial_section_type_rejects_increase():
    """★ 回归守卫：section_type 没有 INCREASE。

    SerialTypeEnum（javap boot-starter-serialnumber-5.3.603）只有
    CONSTANT / CONTEXT / ENTITY / SERIAL。传 INCREASE 平台报
    BOOT_3002「No enum constant SerialTypeEnum.INCREASE」。

    自增语义在 SerialSectionDto.increase（Boolean）上，不在 type 上。
    """
    import pytest
    from xiaozhua_host_bootstrap import bootstrap
    b = bootstrap()
    with pytest.raises(ValueError) as e:
        b["serial_section"](6, "INCREASE")
    assert "CONSTANT" in str(e.value) and "SERIAL" in str(e.value)


def test_serial_scheme_requires_exactly_one_serial_section():
    """★ 回归守卫：SERIAL 段必须恰好 1 个。

    平台 checkDto4Create 判的是 serialCount != 1 → SERIALNUMBER_1008，
    但文案写「流水段有且只能有一段」，极易误读成"段数不对"。
    实测只传一个 CONSTANT 段就报这个。
    """
    import pytest
    from xiaozhua_host_bootstrap import bootstrap
    b = bootstrap()
    const_only = [b["serial_section"](4, "CONSTANT", value="ZZVF")]
    with pytest.raises(ValueError) as e:
        b["serial_scheme_body"]("1", "2", "zzVfS", "验猫", const_only)
    assert "SERIAL" in str(e.value)

    # 一个 CONSTANT + 一个 SERIAL 才过
    ok = b["serial_scheme_body"]("1", "2", "zzVfS", "验猫",
                                 const_only + [b["serial_section"](6, "SERIAL", fill_char="0")])
    assert [s["type"] for s in ok["serialSectionDtoList"]] == ["CONSTANT", "SERIAL"]
    assert ok["totalSize"] == 10


def test_serial_scheme_type_rejects_entity():
    """serialType 用 SerialRuleTypeEnum（APP/BIG/SMALL），不是 SerialTypeEnum。

    2026-11-10 实测传 ENTITY 报 BOOT_3002 —— ENTITY 是段的类型，不是方案的类型。
    """
    import pytest
    from xiaozhua_host_bootstrap import bootstrap
    b = bootstrap()
    secs = [b["serial_section"](4, "CONSTANT", value="ZZVF"),
            b["serial_section"](6, "SERIAL", fill_char="0")]
    with pytest.raises(ValueError) as e:
        b["serial_scheme_body"]("1", "2", "zzVfS", "验猫", secs, serial_type="ENTITY")
    assert "APP" in str(e.value)

def test_refer_config_body_has_no_unknowns_key():
    """★ 回归守卫：body 不许带 unknowns。

    ReferConfigInfoDto（javap udc-biz-5.3.517）只有
    caption / appId / entityId / type / referConfigDetail / operationLog。
    unknowns 是工具自己的"未确认项"记录，以前被塞进 body 一起发给平台。
    """
    from xiaozhua_host_bootstrap import bootstrap
    d = bootstrap()["refer_config_body"](
        "1", "2", "关联1", "List", {"PC": {"config": {}, "display_name": []}})
    assert "unknowns" not in d, "body 不能带 unknowns，平台 DTO 没有这个字段"
    allowed = {"caption", "appId", "entityId", "type", "referConfigDetail", "id"}
    assert set(d) <= allowed, "出现 DTO 外字段: %s" % sorted(set(d) - allowed)


def test_refer_config_type_rejects_entity():
    """refer_type 是列表形态（List/TreeList/LeftTreeRightList），不是 source type。

    ENTITY / BASIC_DATA 属于 ReferConfigSourceTypeEnum，那是另一个字段。
    以前传错值只记 unknowns 不报错，错误的值一路发给平台。
    """
    import pytest
    from xiaozhua_host_bootstrap import bootstrap
    with pytest.raises(ValueError) as e:
        bootstrap()["refer_config_body"]("1", "2", "x", "ENTITY", {"PC": {}})
    assert "List" in str(e.value) and "TreeList" in str(e.value)

def test_dto_attribute_uses_notNull_not_isNotNull():
    """★ 回归守卫：空值约束字段名是 notNull，不是 isNotNull。

    BaseUdcAttributeDto（javap udc-common-5.3.605）：
        private Boolean notNull;
        public Boolean getNotNull();      → Jackson key = "notNull"
    无 @JsonProperty（javap -v 查无），所以 key 就是 getter 推出来的 notNull。
    用 isNotNull 平台完全不认，非空约束静默丢失。
    """
    from xiaozhua_host_bootstrap import bootstrap
    dto = bootstrap()["dto_body"]("1", "D", "ZzDto",
                                  [{"name": "f1", "caption": "F1", "notNull": True}])[0]
    attr = dto["attributes"][0]
    assert "isNotNull" not in attr, "平台字段叫 notNull，isNotNull 会被忽略"
    assert "notNull" in attr
    assert attr["notNull"] is True
    assert isinstance(attr["notNull"], bool), "Boolean 字段不能给 0/1"


def test_dto_attribute_keeps_parent_class_fields():
    """name / caption / dataType 来自父类 BaseUdcAttributeDto，必须保留。"""
    from xiaozhua_host_bootstrap import bootstrap
    d = bootstrap()["dto_body"]("1", "D", "ZzDto",
                                [{"name": "f2", "caption": "字段2", "dataType": "INTEGER"}])[0]
    a = d["attributes"][0]
    assert a["name"] == "f2" and a["caption"] == "字段2" and a["dataType"] == "INTEGER"
    assert "dataTypeCategory" in a and "type" in a

def test_scalability_field_props_never_empty_string():
    """★ 回归守卫：dataTypeProperties 不能是空串。

    实测（test2，udcScalabilityPost）：
      dataTypeProperties=""   → BOOT_3000 message:null, data:null   （无任何线索）
      dataTypeProperties="{}" → BOOT_0000 SUCCESS
    STRING/LONG/DATE/DOUBLE 四类用 "{}" 全部通过。

    空串是"平台拒但什么都不说"的典型，静默失败最难查。缺省必须给 "{}"。
    """
    from components.construction.setting_artifacts import build_scalability_field_body as f

    b = f(1, 2, "p", "c")                      # 不传 props
    assert b["dataTypeProperties"] == "{}"

    assert f(1, 2, "p", "c", data_type_properties="")["dataTypeProperties"] == "{}"
    assert f(1, 2, "p", "c", data_type_properties="   ")["dataTypeProperties"] == "{}"
    assert f(1, 2, "p", "c", data_type_properties=None)["dataTypeProperties"] == "{}"

    # 显式传值必须原样保留（dict 转 JSON 字符串）
    assert f(1, 2, "p", "c", data_type_properties='{"minLength":"0"}')["dataTypeProperties"] == '{"minLength":"0"}'
    assert f(1, 2, "p", "c", data_type_properties={"maxLength": 50})["dataTypeProperties"] == '{"maxLength": 50}'

def test_event_data_list_is_array_not_object():
    """★ 回归守卫：eventDataList 必须是数组。

    实测 udcEventCreateWithDataPost：
      传单对象 → BOOT_3002 属性eventDataList的值反序列化为ArrayList类型时失败
      传 [对象] → 通过

    DTO 声明的是 List<DataTransferObjectDto>，上一轮曾据"前端 bundle 提交单对象"
    判定单对象正确 —— 实测推翻：GraphQL 层不负责包装。
    """
    from components.construction.metadata_artifacts import build_event_with_data_body as f

    b = f(1, "c", "n", 2, [{"outputName": "f1", "description": "字段1"}])
    assert isinstance(b["eventDataList"], list), "eventDataList 必须是数组"
    assert len(b["eventDataList"]) == 1


def test_event_attribute_name_falls_back_to_name_key():
    """attributes[].name 优先取 outputName（微流程 selectParam），其次 name。

    只认 outputName 时，直接传 {"name": "f1"} 会落成 name=null，平台报
    "属性名称 不能为空" —— 完全没指向 name 字段。
    """
    from components.construction.metadata_artifacts import build_event_with_data_body as f

    b = f(1, "c", "n", 2, [{"outputName": "fromOutput", "description": "d1"}])
    assert b["eventDataList"][0]["attributes"][0]["name"] == "fromOutput"

    b2 = f(1, "c", "n", 2, [{"name": "fromName", "description": "d2"}])
    assert b2["eventDataList"][0]["attributes"][0]["name"] == "fromName"

