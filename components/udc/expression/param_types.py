"""paramType 注册表 —— 这**就是**表达式的扩展点。

证据：CFR `@ParamLoadService`（boot-starter-formula common/annotation/ParamLoadService.java）
已注册实现（反编译件全库 grep `@ParamLoadService`，无遗漏）：

    type="CONFIG_PARAM"        uidc  AppParamExpressionSchemaLoadServiceImpl  (useCustom=true)
                               formula ParameterModuleContextServiceImpl
    type="ENTITY"              udc  EntityParamExprServiceImpl
    type="ATTR_DEFAULT_VALUE"  udc  AttributeDefaultValueExprServiceImpl
    type="ATTRIBUTE_SCOPE"     udc  AttributeScopeExprServiceImpl

LIVE 验证（test2，2026-10-23）：
    CONFIG_PARAM       → BOOT_0000，返回 3 个应用参数
    ENTITY             → BOOT_0000，需 ids=[实体id]；缺则 UDC_EXPRESSION_7005
    ATTR_DEFAULT_VALUE → BOOT_0000
    ATTRIBUTE_SCOPE    → BOOT_0000
    EVENT_ATTR         → UDC_EXPRESSION_7005（已注册，但需要实体上下文）
    MICROFLOW / BPM / BPMAUTO / PARAM_CONFIG → BOOT_3000（未注册）

★ 注意两套枚举不要混：
    ExprParamTypeEnum（formula 层）= ENTITY / BPM / BPMAUTO / PARAM_CONFIG / EVENT_ATTR
      其中 BPMAUTO、PARAM_CONFIG 的 code 字面量**带尾空格**（"BPMAUTO " / "PARAM_CONFIG "）
    @ParamLoadService 注册表（真正生效的）= 上表 4 个 + EVENT_ATTR
    接口认的是**注册表**，不是 formula 层枚举 → 传 PARAM_CONFIG 报 BOOT_3000，传 CONFIG_PARAM 才通。

扩展方式：新模块要加变量面时，注册一个新的 ParamTypeSpec，不要改公用层。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParamTypeSpec:
    """一个 paramType 的契约。"""

    param_type: str
    owner_domain: str
    impl_class: str
    requires_entity: bool = False
    use_custom: bool = False
    live: str = "PASS"
    note: str = ""
    required_body_keys: tuple[str, ...] = field(default_factory=tuple)


# 生效的注册表（LIVE 全部验过 code=BOOT_0000 或明确的业务错误码）
_REGISTRY: tuple[ParamTypeSpec, ...] = (
    ParamTypeSpec(
        param_type="CONFIG_PARAM",
        owner_domain="setting",
        impl_class="com.seeyon.udc.expression.domain.service.AppParamExpressionSchemaLoadServiceImpl",
        requires_entity=False,
        use_custom=True,
        note="应用参数（设置域「参数」）。LIVE 返回 3 项；body 需 appId",
        required_body_keys=("appId",),
    ),
    ParamTypeSpec(
        param_type="ENTITY",
        owner_domain="entity",
        impl_class="com.seeyon.udc.expression.domain.service.EntityParamExprServiceImpl",
        requires_entity=True,
        note="实体字段。LIVE 返回实体根节点，字段在 children；缺 ids 报 UDC_EXPRESSION_7005",
        required_body_keys=("ids",),
    ),
    ParamTypeSpec(
        param_type="ATTR_DEFAULT_VALUE",
        owner_domain="entity",
        impl_class="com.seeyon.udc.expression.domain.service.AttributeDefaultValueExprServiceImpl",
        requires_entity=True,
        note="字段默认值表达式。与 ENTITY 同批注册，但语义是「这个字段要算默认值」",
        required_body_keys=("ids",),
    ),
    ParamTypeSpec(
        param_type="ATTRIBUTE_SCOPE",
        owner_domain="entity",
        impl_class="com.seeyon.udc.expression.domain.service.AttributeScopeExprServiceImpl",
        requires_entity=True,
        note="字段取值范围表达式",
        required_body_keys=("ids",),
    ),
    ParamTypeSpec(
        param_type="EVENT_ATTR",
        owner_domain="entity",
        impl_class="(formula ExprParamTypeEnum 声明；udc 侧走实体上下文)",
        requires_entity=True,
        live="PARTIAL",
        note="LIVE 报 UDC_EXPRESSION_7005 —— 已注册但实体上下文传法未定，勿当可用",
        required_body_keys=("ids",),
    ),
)

PARAM_TYPE_REGISTRY: dict[str, ParamTypeSpec] = {s.param_type: s for s in _REGISTRY}

# formula 层声明但**未在 @ParamLoadService 注册**的类型（传了报 BOOT_3000）
UNREGISTERED_FORMULA_TYPES: tuple[str, ...] = ("BPM", "BPMAUTO", "PARAM_CONFIG")

# formula 层枚举原文，注意尾空格 —— 这是坑，不是笔误
FORMULA_ENUM_LITERALS: dict[str, str] = {
    "ENTITY": "ENTITY",
    "BPM": "BPM",
    "BPMAUTO": "BPMAUTO ",
    "PARAM_CONFIG": "PARAM_CONFIG ",
    "EVENT_ATTR": "EVENT_ATTR",
}


def registered_types() -> tuple[str, ...]:
    return tuple(PARAM_TYPE_REGISTRY)


def is_registered(param_type: str) -> bool:
    return param_type in PARAM_TYPE_REGISTRY


def spec_for(param_type: str) -> ParamTypeSpec:
    try:
        return PARAM_TYPE_REGISTRY[param_type]
    except KeyError:
        raise KeyError(
            "paramType=%r 未注册；已注册: %s；formula 层未注册的: %s"
            % (param_type, ", ".join(registered_types()),
               ", ".join(UNREGISTERED_FORMULA_TYPES))
        ) from None


def types_by_domain() -> dict[str, list[str]]:
    """按域归组 —— 用于回答「这个域能用哪些 paramType」。"""
    out: dict[str, list[str]] = {}
    for s in _REGISTRY:
        out.setdefault(s.owner_domain, []).append(s.param_type)
    return out


def check_body(param_type: str, body: dict) -> list[str]:
    """按注册表检查 body 必填键。返回错误列表，空 = 通过。"""
    errs: list[str] = []
    spec = spec_for(param_type)
    for k in spec.required_body_keys:
        v = body.get(k)
        if v in (None, "", [], {}):
            errs.append("%s 需要 body.%s（不得为空）" % (param_type, k))
    return errs
