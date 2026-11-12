"""表达式端点权威契约 —— 来自 boot-starter-formula 5.3.318 的 ExpressionController。

证据：`docs/audit/artifacts/decompiled/r38_full/.../controller/ExpressionController.java`
LIVE 验证：test2，见 core/facts/udc/expression/README.md

★ 单一 Controller 意味着：所有域的表达式走的都是这同一组端点。
  域与域的差别不在端点，在 `paramType`（变量面）与 `terminalSupportType`（函数面）。
"""
from __future__ import annotations

# 网关前缀。/service 是平台网关，本层只记业务段。
EXPRESSION_PATH_PREFIX = "/service/udc/expression"

# 端点表。method 严格按 Controller 注解，不要按"看起来像查询"猜 GET。
EXPRESSION_ENDPOINTS: dict[str, dict] = {
    "operator_list": {
        "method": "GET",
        "path": "/operator/list",
        "returns": "QuickSymbolDto",
        "purpose": "运算符 18 个（5 类）+ 快捷函数 4 个",
        "live": "PASS",
        "note": "只接受 GET；POST 返回 405",
    },
    "preset_list": {
        "method": "POST",
        "path": "/preset/list",
        "body": "PresetLoadConditionDto",
        "returns": "PresetInfoDto",
        "purpose": "系统变量树 + 函数树（88/81 个，8 组/6 组）",
        "live": "PASS",
        "note": "body 必须带 terminalSupportType，缺省报 BOOT_3002",
    },
    "schema": {
        "method": "POST",
        "path": "/schema",
        "body": "VariableSchemaLoadDto",
        "returns": "List<SchemaStructureDto>",
        "purpose": "变量面：按 paramType 返回可用变量（含 uniformityParams.paramId 链接）",
        "live": "PASS",
        "note": "ENTITY 需 ids=[实体id]；appId 是否必需按 paramType 不同，见 facts",
    },
    "transform": {
        "method": "POST",
        "path": "/transform",
        "body": "ExpressionSaveDto",
        "returns": "ExpressionDefinitionDto",
        "purpose": "设计态 → 运行态双态产出（designData + runtimeData.executableExpr）",
        "live": "PASS",
        "note": "写库前必须过这一关；designData 缺 context 键会使检测器 NPE",
    },
    "check": {
        "method": "POST",
        "path": "/check",
        "body": "ExpressionSaveDto",
        "returns": "Boolean",
        "purpose": "纯校验（无落库副作用），走 5 段 Filter 链",
        "live": "PASS",
        "note": "参数不识别时返回 BOOT_3000 且 message 为 null",
    },
    "system_variable_list": {
        "method": "GET",
        "path": "/system-variable/list",
        "returns": "List<SystemPresetVariableDto>",
        "purpose": "系统变量扁平列表",
        "live": "N/A",
    },
    "system_variable_by_condition": {
        "method": "POST",
        "path": "/system-variable/list/by-condition",
        "returns": "List<SystemPresetVariableDto>",
        "purpose": "系统变量按条件过滤",
        "live": "N/A",
    },
    "system_by_name": {
        "method": "POST",
        "path": "/system/list",
        "body": "MultiRequestBody(name)",
        "returns": "SystemPresetVariableDto",
        "purpose": "按名称取单个系统变量",
        "live": "N/A",
    },
    "system_values": {
        "method": "GET",
        "path": "/system/values",
        "returns": "Map<String,Object>",
        "purpose": "系统变量求值",
        "live": "N/A",
    },
    "system_values_by_type": {
        "method": "GET",
        "path": "/system/values/{type}",
        "returns": "Map<String,Object>",
        "purpose": "按类型求系统变量值",
        "live": "N/A",
    },
}


def endpoint_names() -> tuple[str, ...]:
    return tuple(EXPRESSION_ENDPOINTS)


def get_endpoint(name: str) -> dict:
    try:
        return EXPRESSION_ENDPOINTS[name]
    except KeyError:
        raise KeyError(
            "未知表达式端点 %r；已登记: %s" % (name, ", ".join(endpoint_names()))
        ) from None


def full_path(name: str) -> str:
    """业务段 → 可直接 fetch 的完整路径。"""
    return EXPRESSION_PATH_PREFIX + get_endpoint(name)["path"]
