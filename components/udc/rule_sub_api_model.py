"""规则域 —— 微流程周边子域 controller API 综合模型。

controller（udc-web-5.3.517 javap，STATIC_BYTECODE）：
- MicroFlowFunctionalCheckController（udc/micro-flow-functional-check，9）：功能检查/性能分析
- DeductionRuleController（udc/deduction，16）：扣减规则 + 关系图
- MicroFlowUpgradeController（udc/micro-flow-upgrade，4）：第三方/手写/事件 FullName 升级
- MicroFlowRefactorController（udc/microflow-refactor，3）：引用关系重构
- MicroFlowGroupController（udc/micro-flow-group，7）：微流程分组
- MicroFlowMacroController（udc/micro-flow-macro，2）：微流程宏
- TempPresetMicroFlowController（udc/preset/microflow，1）：预置微流程生成

与 microflow_api_model（MicroFlowController 66）互补：本模型覆盖规则域其余 7 controller。

证据边界：STATIC_BYTECODE。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.rule.microflow-sub.v1"

_API = (Path(__file__).resolve().parents[2] / "docs" / "audit" / "artifacts"
        / "udc-web-5.3.517-contracts" / "_api_full.json")

RULE_SUB_CONTROLLERS = [
    "MicroFlowFunctionalCheckController", "DeductionRuleController",
    "MicroFlowUpgradeController", "MicroFlowRefactorController",
    "MicroFlowGroupController", "MicroFlowMacroController",
    "TempPresetMicroFlowController",
]

RULE_SUB_OPS: dict[str, tuple[str, str]] = {
    # 功能检查
    "功能检查_页面规则性能": ("MicroFlowFunctionalCheckController", "checkPageRulePerformance"),
    "功能检查_事件绑定页面规则": ("MicroFlowFunctionalCheckController", "findEventBoundPageRule"),
    "功能检查_少节点页面规则": ("MicroFlowFunctionalCheckController", "findLtSpecifiedNumNodesFrontendMicroFlow"),
    "功能检查_含指定节点页面规则": ("MicroFlowFunctionalCheckController", "findPageRuleIncludeSpecifiedTypeNode"),
    "功能检查_未用后端微流程": ("MicroFlowFunctionalCheckController", "findUnusedBackendMicroFlow"),
    "功能检查_节点占比": ("MicroFlowFunctionalCheckController", "calculateNodesNumberPercentage"),
    "功能检查_使用占比": ("MicroFlowFunctionalCheckController", "calculateMicroFlowUsagePercentage"),
    "功能检查_调用AppService": ("MicroFlowFunctionalCheckController", "searchCallAppService"),
    "功能检查_字段控件属性": ("MicroFlowFunctionalCheckController", "analyseFieldControlAttributes"),
    # 扣减规则
    "扣减_创建图": ("DeductionRuleController", "create"),
    "扣减_更新图": ("DeductionRuleController", "update"),
    "扣减_图按应用": ("DeductionRuleController", "selectByAppId"),
    "扣减_图详情": ("DeductionRuleController", "selectById"),
    "扣减_删图": ("DeductionRuleController", "deleteById"),
    "扣减_删线或节点": ("DeductionRuleController", "deleteLineOrNode4deductionMap"),
    "扣减_创建规则": ("DeductionRuleController", "createRule"),
    "扣减_校验规则": ("DeductionRuleController", "validRule"),
    "扣减_更新规则": ("DeductionRuleController", "updateRule"),
    "扣减_规则列表": ("DeductionRuleController", "selectRuleListByCondition"),
    "扣减_规则详情": ("DeductionRuleController", "selectRuleById"),
    "扣减_规则初始化数据": ("DeductionRuleController", "initData"),
    "扣减_删规则": ("DeductionRuleController", "deleteRuleById"),
    "扣减_规则数按实体": ("DeductionRuleController", "selectDeductionRuleCountByEntityId"),
    "扣减_实体列表": ("DeductionRuleController", "selectEntityListByCondition"),
    "扣减_不存在实体": ("DeductionRuleController", "entity4NotExist"),
    # 升级
    "升级_第三方实体方法": ("MicroFlowUpgradeController", "thirdEntity"),
    "升级_批量第三方实体": ("MicroFlowUpgradeController", "batchThirdEntity"),
    "升级_手写代码fullname": ("MicroFlowUpgradeController", "extendFullName"),
    "升级_实体事件fullname": ("MicroFlowUpgradeController", "upgradeCallExtendAppService"),
    # 重构
    "重构_收集组件关系": ("MicroFlowRefactorController", "collectComponentRelationships"),
    "重构_解析节点引用": ("MicroFlowRefactorController", "resolveNodesReferenceRelationships"),
    "重构_执行": ("MicroFlowRefactorController", "refactored"),
    # 分组
    "微流程分组_创建": ("MicroFlowGroupController", "create"),
    "微流程分组_更新": ("MicroFlowGroupController", "update"),
    "微流程分组_批量移动": ("MicroFlowGroupController", "batchMove"),
    "微流程分组_删除": ("MicroFlowGroupController", "deleteById"),
    "微流程分组_批量删除": ("MicroFlowGroupController", "deleteBatchGroupAndContent"),
    "微流程分组_详情": ("MicroFlowGroupController", "selectById"),
    "微流程分组_按应用": ("MicroFlowGroupController", "selectByAppId"),
    # 宏
    "微流程宏_详情": ("MicroFlowMacroController", "selectById"),
    "微流程宏_项列表": ("MicroFlowMacroController", "selectItemPageList"),
    # 预置
    "预置微流程_生成": ("TempPresetMicroFlowController", "getMicroFlowDefinition"),
}


def _load() -> dict[str, Any]:
    if not _API.exists():
        return {}
    return json.loads(_API.read_text(encoding="utf-8"))


def rule_sub_api_map() -> dict[str, dict[str, Any]]:
    data = _load()
    out: dict[str, dict[str, Any]] = {}
    for op, (ctrl, name) in RULE_SUB_OPS.items():
        v = data.get(ctrl, {})
        m = next((x for x in v.get("methods", []) if x["method"] == name), None)
        out[op] = ({"controller": ctrl, "class_mapping": v.get("class_mapping"),
                    "http": m["http"], "full_path": m["full_path"],
                    "desc": m.get("desc", ""), "resolved": True}
                   if m else {"controller": ctrl, "method_name": name, "resolved": False})
    return out


def rule_sub_summary() -> dict[str, Any]:
    data = _load()
    return {"schema": SCHEMA_ID,
            "controllers": {c: {"class_mapping": data.get(c, {}).get("class_mapping"),
                                "api_count": data.get(c, {}).get("api_count", 0)}
                            for c in RULE_SUB_CONTROLLERS},
            "op_count": len(RULE_SUB_OPS)}


__all__ = ["SCHEMA_ID", "RULE_SUB_CONTROLLERS", "RULE_SUB_OPS",
           "rule_sub_api_map", "rule_sub_summary"]
