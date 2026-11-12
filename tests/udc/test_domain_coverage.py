"""全量审计测试：7 导航项 × 4 核心域覆盖矩阵（"每个地方都要测试到"）。

方法：对设计器每个导航域，断言仓库里有对应的可执行模型/契约落点（builder /
registry op / validator / op catalog），并记录其证据级。任何域「空」即 FAIL，
强制覆盖不遗漏。这是补齐内容的验收面——不是 live 行为验收（那需宿主执行），
而是「用法都进代码了」的完整性断言。

证据级约定（与全仓一致）：
- VERIFIED_STATIC_BYTECODE：javap 字节码实证
- OBSERVED_LIVE：活体抓包/curl 实证
- STATIC：前端 bundle/源码静态
- 本测试只断言「有落点 + 落点可用」，不声称 live 行为 PASS。
"""
import json

import pytest

import importlib


def _has(module_attrs):
    """module_attrs: [(module_path, [attr,...]), ...]；全部可 import 才 True。"""
    import importlib
    for mod, attrs in module_attrs:
        m = importlib.import_module(mod)
        for a in attrs:
            if not hasattr(m, a):
                return False
    return True


# 每个导航域 → 它的可执行落点（模型/契约/builder/validator/op目录）
DOMAIN_COVERAGE = {
    "应用": {
        "module_attrs": [
            ("components.platform_operations.registry", ["UdcOperationRegistry"]),
            ("components.construction.skeleton", ["JavaSkeletonRenderer"]),
            ("components.udc.deploy_chain_model", ["DeployRequest", "DEPLOY_OPS"]),
        ],
        "registry_ops": ["udc.application.get", "udc.application.search.no_page",
                         "udc.application.deploy_info"],
        "evidence": "VERIFIED_STATIC_BYTECODE",
        "note": "基本信息/依赖/版本/沙箱：registry application 族 + 版本状态机（round2 LIVE）",
    },
    "实体": {
        "module_attrs": [
            ("components.platform_operations.registry", ["UdcOperationRegistry"]),
            ("components.construction.metadata_artifacts",
             ["build_index_body", "build_enum_body", "build_enum_item_body",
              "build_dto_with_attrs_body", "build_event_body"]),
            ("components.udc.attribute_semantics",
             ["AttributeSemantics", "build_attribute_plan", "DEFAULT_VALUE_KEYS"]),
            ("components.udc.entity_page_model",
             ["EntityTabBinding", "TAB_WRITE_OPS", "check_delete_plan"]),
            ("components.udc.graphql_write_ops", ["MODULES", "catalog"]),
        ],
        "registry_ops": ["udc.entity.create", "udc.entity.get", "udc.entity.list",
                         "udc.attribute.list"],
        "evidence": "VERIFIED_STATIC_BYTECODE",
        "note": "五 tab（基本/字段/参照/事件/索引）builder + registry entity 族（round2 LIVE）",
    },
    "菜单": {
        "module_attrs": [
            ("components.platform_operations.registry", ["UdcOperationRegistry"]),
            ("components.udc.function_node_model", ["FunctionNode", "FunctionTree"]),
        ],
        "registry_ops": ["udc.microflow.function_node_tree"],
        "evidence": "VERIFIED_STATIC_BYTECODE",
        "note": "菜单功能节点树（function_node_tree）；写侧 UNVERIFIED（只读契约封顶）",
    },
    "规则": {
        "module_attrs": [
            ("components.udc.microflow_model",
             ["MicroFlowGraph", "parse_data_schema", "classify_microflow_type"]),
            ("components.construction.microflow",
             ["build_microflow_create_body", "check_schema_body", "fill_schema_template"]),
            ("components.udc.flow_model",
             ["DataFlowGraph", "DeductionRule", "assert_object_boundary_facts"]),
        ],
        "registry_ops": ["udc.applog.search_microflow", "udc.applog.search_details_microflow",
                         "udc.applog.search_details_microflow_flowlog"],
        "evidence": "STATIC + OBSERVED_LIVE",
        "note": "微流程节点/动作模型 + 校验器（本轮新）+ create/checkSchema builder + 日志读契约",
    },
    "流程": {
        "module_attrs": [
            ("components.udc.bi_flow_ops", ["flow_ops", "FLOW_PAGE_TABS", "FLOW_TEMPLATE_KINDS"]),
            ("components.platform_operations.registry", ["UdcOperationRegistry"]),
        ],
        "registry_ops": ["udc.flow.bpm_node_info_search", "udc.flow.form_data_query",
                         "udc.flow.data_flow_map_get_by_id"],
        "evidence": "OBSERVED_LIVE + VERIFIED_STATIC_BYTECODE",
        "note": "bpm 设计态 op 目录（round2 LIVE）+ registry flow 只读族（生单/扣减边界）",
    },
    "BI": {
        "module_attrs": [
            ("components.udc.bi_flow_ops", ["bi_ops", "BI_DATANAALYSIS_TABS"]),
            ("components.platform_operations.registry", ["UdcOperationRegistry"]),
        ],
        "registry_ops": ["udc.bi.ganttchart_running_dynamic_select_by_entity",
                         "udc.bi.ganttchart_schema_select_by_id",
                         "udc.bi.ganttchart_schema_search_list"],
        "evidence": "OBSERVED_LIVE + VERIFIED_STATIC_BYTECODE",
        "note": "cdp-data 设计态 op 目录（round2 LIVE 四 tab）+ registry ganttchart 只读族",
    },
    "栏目": {
        "module_attrs": [
            ("components.platform_operations.registry", ["UdcOperationRegistry"]),
            ("components.udc.layout_model", ["PageLayout", "SubPageConstraint", "PAGE_TYPES"]),
        ],
        "registry_ops": ["udc.page_info.select_host_and_only_page"],
        "evidence": "VERIFIED_STATIC_BYTECODE",
        "note": "页面信息/栏目 portal 读面（round1 LIVE）；PORTLET 写侧 UNVERIFIED",
    },
    "设置": {
        "module_attrs": [
            ("components.construction.metadata_artifacts",
             ["build_enum_body", "build_enum_item_body", "build_dto_with_attrs_body",
              "build_filter_plan_body"]),
            ("components.udc.excel_model",
             ["ExcelTemplateModel", "side_effect_classification"]),
            ("components.udc.setting.settings_tab_model", ["SETTING_TABS", "tab_catalog"]),
        ],
        "registry_ops": ["udc.entity.ext.tree", "udc.entity.ext.list"],
        "evidence": "OBSERVED_LIVE",
        "note": "13 tab：枚举/选项集/自定义对象/字段集 builder + 扩展实体只读族（SETTINGS-TABS LIVE）",
    },
    "角色": {
        "module_attrs": [
            ("components.platform_operations.registry", ["UdcOperationRegistry"]),
        ],
        "registry_ops": ["udc.role.has_system_admin"],
        "evidence": "VERIFIED_STATIC_BYTECODE",
        "note": "ctp-user 域（挂 udc 网关）；角色资源矩阵 round1 LIVE，写侧 create-system-admin 是写",
    },
}


def test_every_nav_domain_has_executable_landing_point():
    """7+ 导航域每个都有可执行模型/契约落点（不遗漏）。"""
    missing = {}
    for domain, spec in DOMAIN_COVERAGE.items():
        ok = _has(spec["module_attrs"])
        if not ok:
            missing[domain] = [m for m, _ in spec["module_attrs"]]
    assert not missing, f"以下导航域缺可执行落点: {missing}"
    assert len(DOMAIN_COVERAGE) >= 7


def test_core_domains_have_builder_or_validator():
    """4 核心域（BI/流程/微流程/页面）各自有可执行的 builder 或 validator。"""
    # 微流程
    assert _has([("components.udc.microflow_model", ["parse_data_schema"])])
    # 页面
    assert _has([("components.construction.page_schema", ["PageSchemaRenderer"])])
    assert _has([("components.udc.page_event_model", ["PageEventValidator"])])
    # BI
    assert _has([("components.udc.bi_flow_ops", ["bi_ops"])])
    # 流程
    assert _has([("components.udc.bi_flow_ops", ["flow_ops"])])


def test_registry_op_ids_declared_for_domains():
    """DOMAIN_COVERAGE 引用的 registry op id 都真实登记（不臆造 op 名）。"""
    from components.platform_operations.registry import UdcOperationRegistry
    reg = UdcOperationRegistry.default()
    all_ops = reg.all()
    unknown = []
    for domain, spec in DOMAIN_COVERAGE.items():
        for op in spec["registry_ops"]:
            if op not in all_ops:
                unknown.append((domain, op))
    assert not unknown, f"registry 未登记的 op: {unknown}"


def test_domain_coverage_report_is_serializable():
    """覆盖矩阵可落盘为事实件（供审计/宿主复核）。"""
    report = {
        "schema": "udc.nav-domain-coverage.v1",
        "domains": {},
    }
    for domain, spec in DOMAIN_COVERAGE.items():
        report["domains"][domain] = {
            "evidence": spec["evidence"],
            "registry_ops": spec["registry_ops"],
            "note": spec["note"],
            "has_landing_point": _has(spec["module_attrs"]),
        }
    # 可序列化 + 全 9 域都在
    blob = json.loads(json.dumps(report, ensure_ascii=False))
    assert len(blob["domains"]) == len(DOMAIN_COVERAGE) == 9
    # 全部域都有落点
    assert all(d["has_landing_point"] for d in blob["domains"].values()), \
        f"缺落点: {[k for k,v in blob['domains'].items() if not v['has_landing_point']]}"


def test_microflow_model_is_wired_into_udc_package():
    """微流程模型已导出到 components.udc（宿主可用）。"""
    from components.udc import parse_data_schema, classify_microflow_type, MicroFlowGraph
    g = parse_data_schema(json.dumps({"nodes": [
        {"type": "ACTIVITY", "nodeId": "n1", "caption": "c", "actionType": "RETRIEVE", "output": "v1"}
    ]}))
    assert isinstance(g, MicroFlowGraph)
    assert g.status() == "PASS"
    assert classify_microflow_type("eventmonitor") == ("SERVICE", "BUSINESS_EVENT")


def test_page_event_validator_is_wired_into_udc_package():
    """页面事件校验器已导出（组件事件/面板/微流程按钮用法进代码）。"""
    from components.udc import PageEventValidator
    v = PageEventValidator([
        {"id": "e", "eventType": "b", "actionType": "buildin", "actionName": "openPage",
         "paramsMapping": {"pageInfoType": "DETAIL", "PRESET_DETAIL_PAGE_OPEN_MODE": "edit",
                            "PRESET_ID": {"type": "CONTEXT_VARIABLE", "value": "x"}}},
    ])
    assert v.status() == "PASS"


def test_bi_flow_op_catalog_is_wired_into_udc_package():
    """BI/流程 op 目录已导出，可生成事实件。"""
    from components.udc import bi_ops, flow_ops, to_catalog_json
    assert len(bi_ops()) >= 4
    assert len(flow_ops()) >= 1
    cat = to_catalog_json()
    assert cat["schema"].endswith("op-catalog.v1")
