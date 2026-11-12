"""属性「计算值 / 默认值表达式」约束 —— 表达式引擎（formula）写链 LIVE 固化。

证据分层（本轮全部实测，禁止跨层互套）：
  LIVE（test2，app=8704025620829192834，实体 474806313816300867）：
    - POST /udc/expression/schema    -> 变量 schema（paramId/paramCategory 权威源）
    - POST /udc/expression/transform -> 双态产出 designData + runtimeData
    - POST /udc/expression/check     -> Boolean
    - POST /udc/entity/attribute/update -> 落库（expression_design_data / _runtime_data /
      default_value_expr_design / default_value_expr_runtime / calculate）
  CFR（udc-biz 5.3.517，本仓权威字节码）：
    - AttributeService.checkExpressionPattern:1594-1608 -> UDC_ATTR_0017 / UDC_ATTR_0018
    - AttributeService.initDefaultValueCaption:1632-1650 -> defaultValueCaption 优先链
  - AttributeService.setCtpEnumDefaultValueCaption:1652-1680 -> CTPENUM 默认值走独立一支
    （本模型只登记该分支存在，不实现其枚举项解析）
    - Expression4EntityUtil.filterComputeAttributeDto:139-140 -> 计算属性判据
    - AttributeService.resolveAggComputeExpression:383-407 -> 聚合无限循环解析
    - ExpressionSaveDto / ExpressionDesignDataDto / ExpressionDefinitionDto 形状

★ 三条本轮新证的不变量（缺一即崩，均已实测）：
  1. designData 必须含 context 键 —— 即便为空也要是 []；
     缺 context 会让检测器 EntityExprConsistencyValidationImpl.buildSchemaMap:148
     抛 NullPointerException，整个 AttributeDetectionTask FAIL（全局检测 FAIL）。
  2. update 走 BeanCopier.CopyStrategy.IGNORE_NULL（AttributeService.java:364 同族）
     => 传 null 清不掉已有表达式；清空须用空字符串（实测 "" 落库长度 0）。
  3. defaultValueCaption 是服务端派生字段，不是客户端产物：
     initDefaultValueCaption 优先链 = CTPENUM默认值 > defaultValueSystemVariable.desc
     > defaultValueExpressionDesignData.expressionTranslation > defaultValue。
     实测：写表达式后服务端回填 defaultValueCaption = "系统日期时间 "（含尾空格，
     即 expressionTranslation 原样，不 trim）。

表达式 schema 的最小必需入参（实测）：
  POST /udc/expression/schema  body = {"ids":[<实体数字id>], "paramType":"ENTITY",
    "upsource":true, "serverName":"udc"}
  ★ 带上 appId 反而报 BOOT_3000（与 ENTITY-PAGE-INVENTORY 2.7.5 记的传 appId 口径冲突，
    以本轮实测为准：省略 appId）。

token 形状（element of tokens[]）：{uid(uuid), type(FUNCTION|VARIABLE|OPERATOR|CONSTANT|SYSTEM),
  value, desc, subOps?(函数参数二维数组), controlData?}
"""
from __future__ import annotations

import json as _json

# ---------------------------------------------------------------- 端点（LIVE）
EXPRESSION_ENDPOINTS: dict[str, dict] = {
    "schema": {"method": "POST", "path": "/udc/expression/schema",
               "body": "VariableSchemaLoadDto", "gives": "List<SchemaStructureDto>"},
    "transform": {"method": "POST", "path": "/udc/expression/transform",
                  "body": "ExpressionSaveDto", "gives": "ExpressionDefinitionDto"},
    "check": {"method": "POST", "path": "/udc/expression/check",
              "body": "ExpressionSaveDto", "gives": "Boolean"},
    "preset_list": {"method": "POST", "path": "/udc/expression/preset/list",
                    "body": "PresetLoadConditionDto", "gives": "PresetInfoDto"},
}

# ExpressionSaveDto 入参键（LIVE 实测全过）
EXPRESSION_SAVE_KEYS: tuple[str, ...] = (
    "resultTypeInfo", "schemas", "tokens", "isMultiSelect",
    "terminalSupportType", "sourceAppName", "version",
)

# ExpressionDesignDataDto 回读键（transform 产出 designData 的键集，LIVE）
EXPRESSION_DESIGN_KEYS: tuple[str, ...] = (
    "expressionTranslation", "resultTypeInfo", "resultTypeFullName",
    "terminalType", "isMultiSelect", "context", "tokens", "sourceAppName", "version",
)
EXPRESSION_REQUIRED_DESIGN_KEYS: tuple[str, ...] = ("context", "resultTypeInfo", "tokens")
EXPRESSION_RUNTIME_KEYS: tuple[str, ...] = ("executableExpr",)

# 表达式承载字段（udc_attribute 列，information_schema LIKE '%expression%' 实测）
ATTRIBUTE_EXPRESSION_COLUMNS: tuple[str, ...] = (
    "expression_design_data", "expression_runtime_data", "value_scope_expression",
    "default_value_expr_design", "default_value_expr_runtime",
)

# 每个「表达式承载字段」必须成对写（design 回显 / runtime 代码生成）
ATTRIBUTE_EXPRESSION_PAIRS: tuple[tuple[str, str], ...] = (
    ("expressionDesignData", "expressionRuntimeData"),
    ("defaultValueExpressionDesignData", "defaultValueExpressionRuntimeData"),
)

# 属性计算类型与表达式的耦合（CFR Expression4EntityUtil:139-140）
COMPUTE_REQUIRES_RUNTIME_EXPR: bool = True
CALCULATE_COMPUTE = "COMPUTE"
CALCULATE_NORMAL = "NORMAL"
# 第三态：AggregationDto 家族（**不是** expressionRuntimeData 的另一种写法）
CALCULATE_AGGREGATION = "AGGREGATION"

# 结果类型与字段 dataType 解耦（实测：DATETIME 字段承载 INTEGER 表达式，检测仍 SUCCESS）
RESULT_TYPE_DECOUPLED_FROM_DATATYPE: bool = True

# designData 缺 context 会崩检测器（不变量 1）
CONTEXT_KEY_IS_MANDATORY: bool = True

# update 语义（不变量 2）
UPDATE_USES_IGNORE_NULL: bool = True
NULL_CLEARS_EXPRESSION: bool = False
EMPTY_STRING_CLEARS_EXPRESSION: bool = True

# ---------------------------------------------------------------- 错误码（CFR/LIVE）
EXPRESSION_ERROR_CODES: dict[str, str] = {
    "UDC_ATTR_0017": "expressionDesignData 缺 resultTypeInfo 或 tokens 为空（checkExpressionPattern:1601-1603）",
    "UDC_ATTR_0018": "defaultValueExpressionDesignData 缺 resultTypeInfo 或 tokens 为空（checkExpressionPattern:1604-1607）",
    "UDC_EXPRESSION_7005": "实体信息为空（AttributeDefaultValueExprServiceImpl:66-68）",
    "UDC_EXPRESSION_7008": "表达式为空",
    "FORMULA_6058": "变量不存在：CVariable :<desc> does not exist in context",
    "BOOT_3000": "expression/schema 入参不合法（实测：带 appId 或 idsStr 即报）",
}


# ================================================================ AGGREGATION 契约（常量 + 校验）
# 权威：com/seeyon/udc/dto/AggregationDto.java（CFR 逐字），见本文件 §calculate 第三态 的注释头。
AGGREGATION_DTO_KEYS: tuple[str, ...] = (
    "sourceEntityId", "targetEntityId", "sourceFieldId", "targetFieldId",
    "entityType", "functionType", "entityName", "relation",
    "targetDataType", "targetFieldName", "sourceDataType", "sourceFieldName",
    "condition",
)
# ★ 判据集 = 除 condition 外的 12 键（CFR 补默认值使 condition 永不 null）。
#   LIVE 逐键删一负控 12/12 命中 UDC_ATTR_0006，condition 删掉仍 PASS —— 与 CFR 完全一致。
AGGREGATION_REQUIRED_KEYS: tuple[str, ...] = AGGREGATION_DTO_KEYS[:-1]
AGGREGATION_OPTIONAL_KEYS: tuple[str, ...] = ("condition",)
AGGREGATION_CONDITION_KEYS: tuple[str, ...] = (
    "expressionDesignData", "expressionRuntimeData")

# AggregationTypeEnum（com/seeyon/udc/enums/AggregationTypeEnum.java）
AGGREGATION_FUNCTIONS: tuple[str, ...] = ("SUM", "COUNT", "MAX", "MIN")
AGGREGATION_FUNCTION_CODES: dict[str, int] = {"SUM": 0, "COUNT": 1, "MAX": 2, "MIN": 3}
# EntityTypeEnum（com/seeyon/udc/enums/EntityTypeEnum.java）
AGGREGATION_ENTITY_TYPES: tuple[str, ...] = ("PRIMARYWITHCHILD", "PRIMARYONLY", "CHILD")
AGGREGATION_ENTITY_TYPE_CODES: dict[str, int] = {
    "PRIMARYWITHCHILD": 0, "PRIMARYONLY": 1, "CHILD": 2}
# EntityRelationMultiplicityEnum（boot-starter-extmetadata 5.3.318）
AGGREGATION_RELATIONS: tuple[str, ...] = ("ONE2ONE", "ONE2MANY")
AGGREGATION_RELATION_CODES: dict[str, int] = {"ONE2ONE": 0, "ONE2MANY": 1}

# 服务端**不**校验的语义面（LIVE 三组负控全部 BOOT_0000）——写链侧必须自行保证
AGGREGATION_0006_IS_NULL_SHAPE_GATE_ONLY: bool = True
AGGREGATION_0006_VALIDATES_FIELD_CONSISTENCY: bool = False
AGGREGATION_RUNTIME_SHAPE_MATCHES_CALCULATE: bool = False

AGGREGATION_ERROR_CODES: dict[str, str] = {
    "UDC_ATTR_0006": "Incorrect summary field parameters —— AggregationDto 存在 null 字段"
                    "（AttributeEventListener.checkAggregation:458-459；condition 因补默认值不进判据）",
    "BOOT_3000": "枚举反序列化失败：functionType/entityType/relation 不在权威值域",
}


def validate_aggregation_runtime_data(runtime, *, field="expressionRuntimeData"):
    """校验 calculate=AGGREGATION 的 runtimeData（空=通过）。

    ★ 只复算服务端真正强制的那一条（null 形状门）；**不做**语义一致性校验，
    因为实测服务端也不做（见 AGGREGATION_0006_IS_NULL_SHAPE_GATE_ONLY）。
    """
    errs = []
    if runtime in (None, "", {}):
        return [f"calculate=AGGREGATION 必须带 {field}（AggregationDto），不得为空"]
    if isinstance(runtime, str):
        try:
            runtime = _json.loads(runtime)
        except Exception:
            return [f"{field} 不是合法 JSON"]
    if not isinstance(runtime, dict):
        return [f"{field} 须为对象，实为 {type(runtime).__name__}"]
    for k in AGGREGATION_REQUIRED_KEYS:
        if runtime.get(k) is None:
            errs.append(f"{field}.{k} 为 null —— 命中 UDC_ATTR_0006（12 键任一 null 即报）")
    ft = runtime.get("functionType")
    if isinstance(ft, str) and ft not in AGGREGATION_FUNCTIONS:
        errs.append(f"{field}.functionType '{ft}' 不在 {AGGREGATION_FUNCTIONS}（否则 BOOT_3000）")
    et = runtime.get("entityType")
    if isinstance(et, str) and et not in AGGREGATION_ENTITY_TYPES:
        errs.append(f"{field}.entityType '{et}' 不在 {AGGREGATION_ENTITY_TYPES}（否则 BOOT_3000）")
    rl = runtime.get("relation")
    if isinstance(rl, str) and rl not in AGGREGATION_RELATIONS:
        errs.append(f"{field}.relation '{rl}' 不在 {AGGREGATION_RELATIONS}（否则 BOOT_3000）")
    return errs


def validate_expression_design_data(design, *, field="expressionDesignData"):
    """校验 designData 形状（空=通过）。★ 不变量 1：context 键必须在。"""
    errs = []
    if design in (None, "", {}):
        return errs
    if not isinstance(design, dict):
        return [f"{field} 须为对象，实为 {type(design).__name__}"]
    if "context" not in design:
        errs.append(f"{field} 缺 context 键 —— 检测器 buildSchemaMap 会 NPE（须至少为 []）")
    elif not isinstance(design["context"], list):
        errs.append(f"{field}.context 须为数组")
    if not design.get("resultTypeInfo"):
        errs.append(f"{field} 缺 resultTypeInfo（UDC_ATTR_0017/0018）")
    if not design.get("tokens"):
        errs.append(f"{field}.tokens 不得为空（UDC_ATTR_0017/0018）")
    return errs


def validate_attribute_expression(body):
    """校验属性写链的表达式面（空=通过）。"""
    errs = []
    for dv, rv in ATTRIBUTE_EXPRESSION_PAIRS:
        d = body.get(dv)
        r = body.get(rv)
        if d and not r:
            errs.append(f"{dv} 已设但 {rv} 为空 —— design/runtime 必须成对（runtime 才是代码生成输入）")
        if r and not d:
            errs.append(f"{rv} 已设但 {dv} 为空 —— 设计器无法回显")
        if isinstance(d, str) and d:
            try:
                errs.extend(validate_expression_design_data(_json.loads(d), field=dv))
            except Exception:
                errs.append(f"{dv} 不是合法 JSON")
    if body.get("calculate") == CALCULATE_COMPUTE and not body.get("expressionRuntimeData"):
        errs.append("calculate=COMPUTE 必须带 expressionRuntimeData（"
                    "Expression4EntityUtil.filterComputeAttributeDto 按该列过滤）")
    if body.get("calculate") == CALCULATE_AGGREGATION:
        errs.extend(validate_aggregation_runtime_data(
            body.get("expressionRuntimeData")))
    return errs


def clear_expression_payload():
    """清空表达式的唯一有效载荷（★ 不变量 2）。

    update 走 IGNORE_NULL => 传 null 清不掉；必须用空字符串。
    实测："" 落库为 LENGTH=0，检测恢复 SUCCESS。
    """
    return {
        "calculate": "NORMAL",
        "expressionDesignData": "", "expressionRuntimeData": "",
        "defaultValueExpressionDesignData": "", "defaultValueExpressionRuntimeData": "",
    }


def derived_default_value_caption(*, default_value=None, system_variable_json=None,
                                  expression_design=None):
    """复算服务端 defaultValueCaption（CFR initDefaultValueCaption:1632-1650）。

    优先链：CTPENUM默认值（另一支，按枚举项）> defaultValueSystemVariable.desc
            > defaultValueExpressionDesignData.expressionTranslation > defaultValue。
    ★ 不 trim（实测回填 "系统日期时间 " 带尾空格）。
    """
    if system_variable_json:
        try:
            v = _json.loads(system_variable_json) if isinstance(system_variable_json, str) else system_variable_json
            if isinstance(v, dict) and v.get("desc") is not None:
                return v["desc"]
        except Exception:
            pass
    if expression_design:
        try:
            v = _json.loads(expression_design) if isinstance(expression_design, str) else expression_design
            if isinstance(v, dict) and v.get("expressionTranslation") is not None:
                return v["expressionTranslation"]
        except Exception:
            pass
    if default_value not in (None, ""):
        return default_value
    return None


# ================================================================ calculate 第三态：AGGREGATION
# ★ 第二十九轮新增（本轮 LIVE + CFR 双层实证）。此前本模块只覆盖 NORMAL/COMPUTE 两态，
#   `calculate=AGGREGATION`（code 2）**从未测过**，且它 **不是** expressionRuntimeData 的一种写法，
#   而是**另一个 DTO 家族**（AggregationDto）。
#
# CFR（udc-biz 5.3.517 反编译，本仓权威字节码）：
#   - com/seeyon/boot/starter/extmetadata/enums/AttributeCalculateEnum.java
#         NORMAL(0) / COMPUTE(1) / AGGREGATION(2)
#   - com/seeyon/udc/entity/domain/service/AttributeEventListener$checkAggregation:447-462
#         取 `attributeDto.getExpressionRuntimeData()` 反序列化为 AggregationDto；
#         condition 为 null 时**先补 new Condition()**；随后
#         `if (flag = ObjectUtils.existFieldIsNull(aggregationDto)) throw BusinessException("UDC_ATTR_0006")`
#         ⇒ 判据是「**反序列化后的对象存在任一 null 字段**」。
#         ★ 陷阱：`condition` 被前置补默认值 ⇒ 它对 existFieldIsNull **永远非 null** ⇒ **不进判据**。
#   - com/seeyon/udc/utils/ObjectUtils$existFieldIsNull:42-55
#         遍历全部声明字段，任一为 null 即 true（catch 分支返回 false）。
#   - com/seeyon/udc/dto/AggregationDto{,+$Condition}.java —— 12 字段本体（逐字）
#   - com/seeyon/udc/enums/AggregationTypeEnum.java —— SUM(0)/COUNT(1)/MAX(2)/MIN(3)
#   - com/seeyon/udc/enums/EntityTypeEnum.java —— PRIMARYWITHCHILD(0)/PRIMARYONLY(1)/CHILD(2)
#   - EntityRelationMultiplicityEnum（boot-starter-extmetadata 5.3.318）—— ONE2ONE(0)/ONE2MANY(1)
#   - Expression4EntityUtil$filterComputeAttributeDto:138-140
#         `AttributeCalculateEnum.COMPUTE.equals(...)` ⇒ **AGGREGATION 不进计算表达式环图**，
#         不参与 resolveAggInfiniteLoop 的环检测（与 COMPUTE 的真实区别之一）。
#
# LIVE（test2，app=870402282…/实体 474806313816300867，字段 expText 8016904624316689195）：
#   - **正例 PASS**：12 键齐全 + condition 全 null ⇒ `BOOT_0000`，
#     REST 回读 `calculate=AGGREGATION`，DB `calculate=2` + `expression_runtime_data` 为该 12 键 JSON。
#   - **12/12 逐键删一负控**：每删任一字段 ⇒ `UDC_ATTR_0006 Incorrect summary field parameters`。
#   - **condition 可省**：`condition` 整键缺失 ⇒ `BOOT_0000`（与 CFR 补默认值一致，非判据）。
#   - `condition` 内两子键全 null ⇒ 亦 PASS（子键是**两层嵌套**，见 §陷阱）。
#   - `functionType` 四值 SUM/COUNT/MAX/MIN 全 PASS；`AVG` ⇒ `BOOT_3000`（枚举反序列化失败）。
#   - `entityType` 三值 + 数字码 0/1/2 全 PASS；`BOGUS` ⇒ `BOOT_3000`。
#   - `relation` 两值 + 数字码 0/1 全 PASS；`MANY2MANY`/`BOGUS` ⇒ `BOOT_3000`。
#   - ★ **`UDC_ATTR_0006` 不校验语义**：`targetDataType` 与目标字段类型不符、
#     `targetFieldName` 与 `targetFieldId` 不符、源=目标同实体 — 三者**全部 BOOT_0000 通过**。
#     ⇒ 它是**空形状门（null-shape gate）**，不是字段一致性校验。写链侧必须自行保证一致性。
#   - ★ **runtime 形态无判别**：`calculate=COMPUTE` 但 runtimeData 填 AggregationDto ⇒ 同样 PASS。
#     ⇒ 服务端**不校验 calculate 与 runtimeData 形态是否匹配**（形态耦合是设计器约定，非服务端强制）。
#   - 检测面：写 AGGREGATION 后 `ERROR=0 / WARN=2`（04003×2，与本字段无关）⇒ 不引入新检测码。
#   - 前端同源（前端 bundle 逐字）：`src_pages_app-design_entity-modeling_entity-field_components_rule-Form/module-62746.js`
#     `setEntityFormula(l); setCalculate("AGGREGATION")`，`l` 即上述 12 键 + 可选 `condition`
#     （`if (l.condition === undefined) delete l.condition` ⇒ 前端**显式省略** condition）。


# ================================================================ 表达式 token 类型域 / 系统变量面
# ★ 第四十轮新增。CFR 权威件：`boot-starter-formula-5.3.318.jar`（反编译件 docs/audit/artifacts/decompiled/r38_full，202 个 .java）。
#   LIVE：test2 app=8704025620829192834，端点 POST /service/udc/expression/check（纯校验、无落库副作用）。
#
# ---------------------------------------------------------------- 1. token.type 值域（CFR 逐字）
# CFR：`com/seeyon/boot/starter/formula/enums/TokenTypeEnum.java`
#        CONSTANT / VARIABLE / SYSTEM / FUNCTION / OPERATOR  —— **恰 5 值**
#      `com/seeyon/boot/starter/formula/common/constant/TokenTypeConstant.java` 同 5 个字面量。
#      ★ **不存在 `SYSTEM_VARIABLE`**：系统变量是 `type=SYSTEM`，不是独立 type。
# CFR：`parser/ast/Factor.parse:26-50` 只认 `VARIABLE` / `CONSTANT` / `SYSTEM` / `FUNCTION`
#      四类，其余（含 OPERATOR 落到这里的情况）`return null`。
# CFR：`domain/validation/filter/TokenLexerFilter`（@ExpressionFilter(order=4)）与
#      `ResultTypeDefinitionFilter`（order=3）等构成 filters 链（ExpressionValidator.init 按 order 排序）。
# LIVE（本轮复跑，单 token）：type ∈ {SYSTEM_VARIABLE, BOGUS, ""} ⇒ 一律 `BOOT_3000`
#      （Jackson 反序列化 TokenTypeEnum 失败，message=null）；⇒ 值域外**不是**业务码而是框架反序列化失败。
EXPRESSION_TOKEN_TYPE_DOMAIN: tuple[str, ...] = (
    "CONSTANT", "VARIABLE", "SYSTEM", "FUNCTION", "OPERATOR")

# 值域外的"听起来合理"的取值——**不得**写进 tokens[].type（LIVE 实测 BOOT_3000）
EXPRESSION_TOKEN_TYPE_REJECTED_VALUES: tuple[str, ...] = (
    "SYSTEM_VARIABLE",  # ★ 上轮曾把它当成合法 type 做过 2x2 矩阵；LIVE 证伪，恒 BOOT_3000
    "BOGUS", "",        # 空串同样 BOOT_3000
)

# ---------------------------------------------------------------- 2. SYSTEM token 的两条解析通路
# ★ 同一个系统变量有**两条互不等价**的写链通路，取哪条只看 token.type：
#
#   通路 A（全名）: {"type":"SYSTEM", "value":"system.currentDateTime"}
#     CFR `parser/semantic/SemanticAnalyzer.analyze:94` → `analyzeSystem:230-240`
#         `ExpressionCache.getSystemVariableItemsMap().get(value)` 取 SystemVariableItems，
#         其 `resultType` 即分析类型（`DataType.valueOf`），`relationEntity` 非空则
#         `setEntity(true)` + `setGenericType(relationEntity)`。
#     ⇒ **只有全名在 map 里**（map 的 key 是 `SystemVariableItems.getName()`）。
#
#   通路 B（短名）: {"type":"SYSTEM", "value":"currentDateTime"}
#     CFR `dto/ExpressionToken.currentIsCallFactor:122-124`
#         `(currentIsFunction()||currentIsSystemVariable()) && functionCacheMap.containsKey(value)`
#       ⇒ 短名若**同名于某个函数**，则被 `Expr.f:64` 判定为 CALL_EXPR，
#         走 `SemanticAnalyzer.analyzeCallExpr:145-157`（**取的是函数返回类型**，不是系统变量表）。
#
#   ⇒ 两条通路的**分析类型可以不同**（见 LIVE_SHORT_VS_FULL_ANALYZED_TYPE）。
SYSTEM_TOKEN_TWO_RESOLUTION_PATHS: tuple[str, ...] = ("SYSTEM_FULL_NAME_TABLE", "SHORT_NAME_FUNCTION_CALL")
SYSTEM_SHORT_NAME_PATH_IS_FUNCTION_CALL_EXPR: bool = True
SHORT_NAME_ANALYZED_TYPE_MAY_DIFFER_FROM_FULL_NAME: bool = True

# 唯一 put 点（CFR 逐字，防"以为有多处注册"）
SYSTEM_VARIABLE_PUT_SITE: str = (
    "com/seeyon/boot/starter/formula/listener/ExpressionPresetRunner.loadSystemVariable:237 "
    "-> ExpressionCache.getSystemVariableItemsMap().put(systemVariableItems.getName(), ...) "
    "（扫 classpath*:META-INF/system/**/*.json；同处 :234 把 hidden 项或同名函数 hidden 的项 "
    "setHidden(true)）")

# ---------------------------------------------------------------- 3. hidden 项：list 过滤 / check 不过滤
# ★ 这两条必须分开记，混起来会得出错误结论。
# CFR `domain/service/ExpressionService.getI18nSystemVariables:609`
#     `if (item.isHidden()) continue;` —— 只作用于 **列表**（给前端选择器用的那一支）。
# CFR `SemanticAnalyzer.analyzeSystem:230-240` —— **无任何 hidden 判断**，
#     只看 `getSystemVariableItemsMap().get(value)` 是否取到。
# ⇒ hidden 项**在 list 里看不到，但 check 完全接受**。
SYSTEM_VARIABLE_LIST_FILTERS_HIDDEN: bool = True
SYSTEM_VARIABLE_CHECK_IGNORES_HIDDEN: bool = True

# ---------------------------------------------------------------- 4. 131 vs 132（双向闭合）
# LIVE（本轮复跑，GET /service/udc/expression/system-variable/list）：
#   data.content = 4 组 / **131 项**；`system.currentTimestamp` **不在**列表中。
# 静态（jar 内 META-INF/system/*.json 逐件计数）：date 34 + env 2 + plugin 1 + organization 95 = **132**。
# 差额 **恰 1** = date.json 里唯一 hidden 项 `system.currentTimestamp`
#   ⇒ 与「list 过滤 hidden、check 不过滤」**双向闭合**（不是巧合，两条独立证据链）。
LIVE_SYSTEM_VARIABLE_ITEM_COUNT: int = 131
JAR_SYSTEM_VARIABLE_ITEM_COUNT: int = 132
HIDDEN_SYSTEM_VARIABLE_ITEMS: tuple[str, ...] = ("system.currentTimestamp",)
LIVE_SYSTEM_VARIABLE_GROUP_COUNTS: dict[str, int] = {
    "organization": 95, "date": 33, "env": 2, "plugin": 1}

# LIVE：同一逻辑变量的"短名 / 全名"两通路**分析类型分裂**（rt 用 STRING 或 BOOLEAN 逼出 6901 报文）
#   报文形如 `Calculated result is of type <分析类型>, cannot be assigned to: <派生行键>`
LIVE_SHORT_VS_FULL_ANALYZED_TYPE: dict[str, dict[str, str]] = {
    "currentTime":     {"short": "STRING", "full": "TIME"},       # ★ 分裂
    "currentDateTime": {"short": "DATE",   "full": "DATETIME"},   # ★ 分裂
    "currentDate":     {"short": "DATE",   "full": "DATE"},
    "currentUserId":   {"short": "BIGINTEGER", "full": "BIGINTEGER"},
    "currentTimestamp": {"short": "BIGINTEGER", "full": "BIGINTEGER"},  # 全名为 hidden 项
}
# 短名走 CALL_EXPR 的存在性判别（LIVE）：`{"type":"SYSTEM","value":"abs"}` 无 subOps ⇒ BOOT_3000；
# 带 1 或 2 个参 ⇒ BOOT_0000。⇒ 短路名路径**确实**按函数调用解析（无参函数名被当函数用会崩）。
SHORT_NAME_WITHOUT_SUBOPS_IS_BOOT_3000: bool = True

# ---------------------------------------------------------------- 5. 返回类型（resultTypeInfo）域
# CFR `enums/ExprDataTypeEnum.java`：枚举**16 个常量**，但静态块 `supportedResultType`
#     只 add 了 **15 个** —— 唯一被排除的是 `OBJECTS`。
# ★ 更正：上轮交接里写的 `SUPPORTED_RESULT_TYPES (16)` 是**把枚举常量数当成了值域大小**。
# LIVE：resultTypeInfo="OBJECT" ⇒ `FORMULA_6003`；"UDCENUM"（无此 DataType）⇒ 同样 `FORMULA_6003`。
# CFR `domain/validation/filter/ResultTypeDefinitionFilter.doFilter:33`：
#      `supportedResultType.contains(resultTypeInfo)` 否则 throw RESULT_TYPE_ERROR = FORMULA_6003。
# 另：`resultTypeInfo == ENUM && resultTypeFullName 为空` ⇒ `FORMULA_6068`（ENUM_ASSIGN_ERROR）。
SUPPORTED_RESULT_TYPES: tuple[str, ...] = (
    "INTEGER", "BIGINTEGER", "DECIMAL", "STRING", "MULTILINESTRING", "DATETIME", "DATE", "TIME",
    "BOOLEAN", "CURRENCY", "ATTACHMENT", "ARRAY", "ENTITY", "CTPENUM", "ENUM")
ENUM_DATATYPE_CONSTANT_COUNT: int = 16          # 枚举常量数（含 OBJECTS）
SUPPORTED_RESULT_TYPE_IS_DATATYPE_CONSTANT_COUNT: bool = False   # ★ 两者不相等
RESULT_TYPE_OUTSIDE_DOMAIN_ERROR: str = "FORMULA_6003"
ENUM_WITHOUT_RESULT_TYPE_FULL_NAME_ERROR: str = "FORMULA_6068"

# ---------------------------------------------------------------- 6. 返回类型兼容性表（14 行）
# CFR 资源件（本仓 docs/audit/artifacts/scratch-migrated/r37_cfr/result_data_type_compatibility.json 逐字转写，14 行）
# 读取方：`domain/validation/ExpressionValidator.resultTypeCompatibilityCheck:105-134`
#   - `getResultDataTypeBySaveDto:193-202`：**派生**行键 ——
#       CTPENUM/ENTITY 且 multiSelect ⇒ STRING，否则 ⇒ BIGINTEGER；其余 ⇒ resultTypeInfo 本身。
#   - `getExpectResultDataType:182-191`：**派生**被比较侧 ——
#       CTPENUM/ENTITY 且 multiSelect ⇒ STRING，否则 ⇒ BIGINTEGER；其余 ⇒ originDataType。
#   - `terminalSupportType == null` 视为 BACKEND；BACKEND 查 backendCompatibleDataTypes。
#   - 表里**没有行** ≠ 不校验：`checkUdcEnumCast` / `checkCtpEnumCast` / `checkEntityCast`
#     三门在**查表之前**就跑了（:113-115），与兼容表**完全独立**。
RESULT_TYPE_COMPATIBILITY_ROW_IS_DERIVED_CAST_TYPE: bool = True
RESULT_TYPE_COMPATIBILITY_HAS_ENUM_ROW: bool = False
RESULT_TYPE_COMPATIBILITY_HAS_UDCENUM_ROW: bool = False
RESULT_TYPE_COMPATIBILITY_HAS_OBJECT_ROW: bool = False
# ★ 更正：上轮交接里写的「表外类型 ⇒ 无其它门 ⇒ 恒放行」**是错的**（见 §7）。
OUTSIDE_ROW_MEANS_NO_OTHER_GATE_FIRES: bool = False
RESULT_TYPE_COMPATIBILITY_TABLE: dict[str, dict[str, tuple[str, ...]]] = {
    "MULTILINESTRING": {
        "BACKEND": ("INTEGER", "BIGINTEGER", "DECIMAL", "CURRENCY", "ATTACHMENT", "STRING", "MULTILINESTRING", "CTPENUM"),
        "FRONTEND": ("INTEGER", "BIGINTEGER", "DECIMAL", "CURRENCY", "ATTACHMENT", "STRING", "MULTILINESTRING", "CTPENUM"),
    },
    "STRING": {
        "BACKEND": ("INTEGER", "BIGINTEGER", "DECIMAL", "CURRENCY", "ATTACHMENT", "STRING", "MULTILINESTRING", "CTPENUM"),
        "FRONTEND": ("INTEGER", "BIGINTEGER", "DECIMAL", "CURRENCY", "ATTACHMENT", "STRING", "MULTILINESTRING", "CTPENUM"),
    },
    "INTEGER": {
        "BACKEND": ("INTEGER", "BIGINTEGER"),
        "FRONTEND": ("INTEGER", "BIGINTEGER"),
    },
    "BIGINTEGER": {
        "BACKEND": ("INTEGER", "BIGINTEGER"),
        "FRONTEND": ("INTEGER", "BIGINTEGER", "STRING"),
    },
    "DECIMAL": {
        "BACKEND": ("INTEGER", "BIGINTEGER", "DECIMAL", "CURRENCY"),
        "FRONTEND": ("INTEGER", "BIGINTEGER", "DECIMAL", "CURRENCY"),
    },
    "BOOLEAN": {
        "BACKEND": ("BOOLEAN"),
        "FRONTEND": ("BOOLEAN"),
    },
    "DATE": {
        "BACKEND": ("DATETIME", "DATE"),
        "FRONTEND": ("DATETIME", "DATE"),
    },
    "DATETIME": {
        "BACKEND": ("DATETIME", "DATE"),
        "FRONTEND": ("DATETIME", "DATE"),
    },
    "TIME": {
        "BACKEND": ("TIME", "STRING", "MULTILINESTRING"),
        "FRONTEND": ("TIME", "STRING", "MULTILINESTRING"),
    },
    "ENTITY": {
        "BACKEND": ("ENTITY", "BIGINTEGER"),
        "FRONTEND": ("ENTITY", "BIGINTEGER"),
    },
    "ATTACHMENT": {
        "BACKEND": ("STRING", "ATTACHMENT", "MULTILINESTRING"),
        "FRONTEND": ("STRING", "ATTACHMENT", "MULTILINESTRING"),
    },
    "CURRENCY": {
        "BACKEND": ("INTEGER", "BIGINTEGER", "DECIMAL", "CURRENCY"),
        "FRONTEND": ("INTEGER", "BIGINTEGER", "DECIMAL", "CURRENCY"),
    },
    "CTPENUM": {
        "BACKEND": ("CTPENUM", "BIGINTEGER"),
        "FRONTEND": ("CTPENUM", "BIGINTEGER"),
    },
    "ARRAY": {
        "BACKEND": ("ARRAY"),
        "FRONTEND": ("ARRAY"),
    },
}

# ---------------------------------------------------------------- 7. 三门与兼容表的分工（本轮核心更正）
# CFR `ExpressionValidator.resultTypeCompatibilityCheck:113-115` 顺序：
#   checkUdcEnumCast → checkCtpEnumCast → checkEntityCast → 然后才是查表。
#
# (a) checkUdcEnumCast:137-141 —— **ENUM 的专属门**（独立于兼容表）
#       `if (!( ENUM != expected || !analyze.isUdcEnum()
#               || ( equals(analyze.genericType, resultTypeFullName)
#                    && analyze.isMultiSelect() == saveDto.isMultiSelect() ) ))
#            throw FORMULA_6071;`
#     ★ 更正：上轮写「ENUM 在兼容表内无行 ⇒ 一条都不校验 ⇒ 恒放行」**只对兼容表成立**，
#       整条链**仍会**报错。LIVE 反例（本轮复跑）：
#         SYSTEM system.currentUserId + rt=ENUM + rtn=null       ⇒ FORMULA_6071
#         SYSTEM system.currentUserId + rt=ENUM + rtn=FQN        ⇒ BOOT_0000   ← 填对就过
#         SYSTEM system.currentUserId + rt=ENUM + rtn="OrgMember" ⇒ FORMULA_6071
#         SYSTEM system.currentDate     + rt=ENUM + rtn=null      ⇒ BOOT_0000   ← genericType 同为 null
#         CONSTANT 'x' + rt=ENUM + isMultiSelect=true             ⇒ FORMULA_6071（multi 不匹配）
#       ⇒ 判据是 **genericType == resultTypeFullName 且 multi 一致**（null==null 也算相等）。
#
# (b) checkCtpEnumCast:159-180 —— CTPENUM 的专属门：rt=CTPENUM 且分析结果是 entity/udcEnum
#       ⇒ `FORMULA_6169`（LIVE：SYSTEM system.currentUserId ⇒ 6169，与 multi 无关）。
# (c) checkEntityCast:145-157 —— rt=ENTITY 且分析结果是 ctpEnum/udcEnum ⇒ `FORMULA_6170`。
#     另：rt=ENTITY + 分析 entity + fullName 不等 ⇒ 6170；期望单选而分析多选 ⇒ `FORMULA_6172`。
#     CTPENUM 多选不匹配 ⇒ `FORMULA_6171`。
# (d) 最后查表：派生行键查不到（如 ENUM）⇒ 该循环**一行都不匹配** ⇒ **本门不报**；
#     但 (a)/(b)/(c) 与 6901 仍可能报。⇒ 「表外」只说明**兼容表这一门**不生效。
CHECK_UDC_ENUM_CAST_IS_INDEPENDENT_OF_COMPAT_TABLE: bool = True
ENUM_GATE_COMPARES_GENERIC_TYPE_WITH_RESULT_TYPE_FULL_NAME: bool = True
ENUM_GATE_NULL_GENERIC_TYPE_EQUALS_NULL_FULL_NAME: bool = True

# ---------------------------------------------------------------- 8. 兼容表的判别器（本轮新证）
# ★ 用「同一 token、只翻 isMultiSelect」把派生行键打出来（这是证明"行键=派生 cast 类型"的单变量实验）：
#   token = CONSTANT 'x'（分析类型 STRING），rt=CTPENUM：
#       isMultiSelect=false ⇒ 派生行键 BIGINTEGER，BE=(INTEGER,BIGINTEGER) 不含 STRING ⇒ **FORMULA_6901**
#       isMultiSelect=true  ⇒ 派生行键 STRING，BE 含 STRING                       ⇒ **BOOT_0000**
#   ⇒ 唯一自变量 isMultiSelect，结果翻转 ⇒ 行键确为 `getResultDataTypeBySaveDto` 的**派生**值。
# ★ 同时更正上轮交接的「判别器 J」：原文写 `rt=CTPENUM + multi=True ⇒ BOOT_0000` 并把 token 记成
#   `SYSTEM system.currentDate`（分析类型 DATE）。本轮复跑：该组合 multi 真/假**都是 FORMULA_6901**
#   （DATE 既不在 BIGINTEGER 行也不在 STRING 行）⇒ 原表述的**自变量不成立**，已按上面的 STRING 例改写。
COMPAT_TABLE_ROW_KEY_DISCRIMINATOR: dict[str, dict[str, str]] = {
    "token": {"type": "CONSTANT", "value": "x"},
    "resultTypeInfo": "CTPENUM",
    "analyzedType": "STRING",
    "multiFalse": {"row": "BIGINTEGER", "code": "FORMULA_6901"},
    "multiTrue": {"row": "STRING", "code": "BOOT_0000"},
}
# 反例（上轮表述的原始组合，本轮实测证伪其"自变量"地位）
COMPAT_DISCRIMINATOR_REFUTED_VARIANT: dict[str, str] = {
    "token": "SYSTEM system.currentDate (analyzedType=DATE)",
    "resultTypeInfo": "CTPENUM",
    "multiFalse": "FORMULA_6901", "multiTrue": "FORMULA_6901",
}

# ---------------------------------------------------------------- 9. 错误码
EXPRESSION_TOKEN_ERROR_CODES: dict[str, str] = {
    "BOOT_3000": "tokens[].type 不在 TokenTypeEnum 5 值域（含 SYSTEM_VARIABLE/空串）；"
                 "或枚举字段反序列化失败（message 为 null）",
    "FORMULA_6003": "resultTypeInfo 不在 supportedResultType 15 值域（如 OBJECT/UDCENUM）"
                    "（ResultTypeDefinitionFilter:33，RESULT_TYPE_ERROR）",
    "FORMULA_6049": "FUNCTION_PARAM_NUMBER_ERROR —— 函数实参个数不符"
                    "（LIVE：FUNCTION abs + subOps=[] ⇒ 6049）",
    "FORMULA_6058": "NODE_NOT_FOUND_IN_SCHEMA_ERROR —— VARIABLE 名不在 context/schemas",
    "FORMULA_6066": "VARIABLE_NUMBER_START_ERROR —— 变量名以数字开头（TokenLexerFilter.checkVariableName）",
    "FORMULA_6068": "ENUM_ASSIGN_ERROR —— resultTypeInfo=ENUM 但 resultTypeFullName 为空",
    "FORMULA_6069": "ENUM_RESULT_MATCH_ERROR —— controlData.data.fullName 与 resultTypeFullName 不等",
    "FORMULA_6071": "ENUM_TYPE_MATCH_ERROR —— checkUdcEnumCast 判据不满足（见 §7a）",
    "FORMULA_6169": "CTPENUM_TYPE_MATCH_ERROR —— rt=CTPENUM 但分析结果是 entity/udcEnum",
    "FORMULA_6170": "ENTITY_TYPE_MATCH_ERROR —— rt=ENTITY 但分析结果是 ctpEnum/udcEnum，或 fullName 不等",
    "FORMULA_6171": "CTPENUM_MULTI_SELECT_MATCH_ERROR",
    "FORMULA_6172": "ENTITY_MULTI_SELECT_MATCH_ERROR",
    "FORMULA_6901": "返回类型不兼容 —— 派生行键的兼容列表不含派生被比较类型"
                    "（ValidationErrorHelper.throwResultTypeCastException）",
}


def derive_system_variable_function_name(system_variable_name: str) -> str:
    """全名 → 短名（CFR ExpressionCommonUtil.getSystemVaribleFunction:121-131 同构）。

    `system.currentDateTime` -> `currentDateTime`。CFR 侧实现为 `value.split(".")[1]`
    => **只取第 2 段**；不含 `.` 的输入在服务端会抛 ArrayIndexOutOfBounds（非业务码）。
    """
    parts = system_variable_name.split(".")
    if len(parts) < 2:
        raise ValueError("系统变量全名必须含 '.'（如 system.xxx），实为 %r" % (system_variable_name,))
    return parts[1]


def is_system_token_value_legal(value, *, known_names=None, known_function_names=None):
    """SYSTEM token 的 value 是否可能被服务端接受（空=通过）。

    ★ 两条通路分别判：全名必须在系统变量表内；短名必须在**函数表**内（否则解析成
      SystemVariable 后 `getSystemVariableItemsMap().get(value)` 取不到 -> NPE/BOOT_3000）。
    """
    errs = []
    names = SYSTEM_VARIABLE_ITEMS if known_names is None else known_names
    known = {n for _, n, _, _ in names}
    if value in known:
        return errs
    if known_function_names is not None and value in set(known_function_names):
        return errs
    errs.append(
        "SYSTEM token value %r 既不在系统变量表（%d 项）也不在函数表 —— "
        "服务端取 SystemVariableItems 会失败（BOOT_3000/NPE）" % (value, len(known)))
    return errs


def result_type_compatibility_allows(result_type_info, *, is_multi_select=False,
                                     analyzed_type=None, terminal="BACKEND"):
    """复算兼容表这一门（CFR getResultDataTypeBySaveDto:193-202 + :105-134）。

    返回 (row_key, compatible, in_table)。★ 只复算**兼容表**这一门；
    `checkUdcEnumCast`/`checkCtpEnumCast`/`checkEntityCast` 三门不在本函数内
    （表里无行时它们**仍会**报错，见 OUTSIDE_ROW_MEANS_NO_OTHER_GATE_FIRES=False）。
    """
    if result_type_info in ("CTPENUM", "ENTITY"):
        row_key = "STRING" if is_multi_select else "BIGINTEGER"
    else:
        row_key = result_type_info
    row = RESULT_TYPE_COMPATIBILITY_TABLE.get(row_key)
    if row is None:
        return row_key, None, False
    expected = row_key if analyzed_type is None else (
        ("STRING" if is_multi_select else "BIGINTEGER") if analyzed_type in ("CTPENUM", "ENTITY")
        else analyzed_type)
    side = "BACKEND" if terminal == "BACKEND" else "FRONTEND"
    return row_key, (expected in row[side]), True


def validate_expression_token(token):
    """校验单个 tokens[] 元素（空=通过）。只复算**本轮已实测**的强制项，不做语义外推。"""
    errs = []
    if not isinstance(token, dict):
        return ["token 须为对象，实为 %s" % type(token).__name__]
    t = token.get("type")
    if t not in EXPRESSION_TOKEN_TYPE_DOMAIN:
        errs.append("tokens[].type %r 不在 %s —— 服务端 BOOT_3000"
                    "（SYSTEM_VARIABLE 不是合法值）" % (t, (EXPRESSION_TOKEN_TYPE_DOMAIN,)))
        return errs
    if t == "SYSTEM":
        v = token.get("value") or ""
        if v in {n for _, n, _, _ in SYSTEM_VARIABLE_ITEMS}:
            pass
        elif token.get("subOps"):
            pass  # 短路名：有参即按函数调用解析（CFR Expr.f:64 -> CallExpr）
        else:
            errs.append(
                "SYSTEM token value %r 既非系统变量全名、又无 subOps —— "
                "按短路名解析会当函数调用（无参 -> BOOT_3000）" % (v,))
    return errs


# ---------------------------------------------------------------- 10. 系统变量全量（132 项，jar 静态 + LIVE 交叉）
# (group, name, functionName, resultType)；LIVE list 回读 131 项 + 静态补唯一 hidden 项。
# ★ 这是**平台面**常量（跨应用复用），不是客户业务明细。
SYSTEM_VARIABLE_ITEMS: tuple[tuple[str, str, str, str], ...] = (
    ("organization", "system.currentAllParentOrgCode", "currentAllParentOrgCode", "ARRAY"),
    ("organization", "system.currentAllParentOrgId", "currentAllParentOrgId", "ARRAY"),
    ("organization", "system.currentAllParentOrgName", "currentAllParentOrgName", "ARRAY"),
    ("date", "system.currentDate", "currentDate", "DATE"),
    ("date", "system.currentDateTime", "currentDateTime", "DATETIME"),
    ("date", "system.currentDay", "currentDay", "STRING"),
    ("organization", "system.currentFirstLevelOrgCode", "currentFirstLevelOrgCode", "STRING"),
    ("organization", "system.currentFirstLevelOrgId", "currentFirstLevelOrgId", "BIGINTEGER"),
    ("organization", "system.currentFirstLevelOrgName", "currentFirstLevelOrgName", "STRING"),
    ("organization", "system.currentInstitutionCode", "currentInstitutionCode", "STRING"),
    ("organization", "system.currentInstitutionId", "currentInstitutionId", "BIGINTEGER"),
    ("organization", "system.currentInstitutionLogo", "currentInstitutionLogo", "STRING"),
    ("organization", "system.currentInstitutionName", "currentInstitutionName", "STRING"),
    ("organization", "system.currentJobCode", "currentJobCode", "STRING"),
    ("organization", "system.currentJobId", "currentJobId", "BIGINTEGER"),
    ("organization", "system.currentJobName", "currentJobName", "STRING"),
    ("env", "system.currentLanguage", "currentLanguage", "STRING"),
    ("organization", "system.currentLeaderDepartmentCodes", "currentLeaderDepartmentCodes", "ARRAY"),
    ("organization", "system.currentLeaderDepartmentIds", "currentLeaderDepartmentIds", "ARRAY"),
    ("organization", "system.currentLeaderDepartmentNames", "currentLeaderDepartmentNames", "ARRAY"),
    ("organization", "system.currentLeaderInstitutionCodes", "currentLeaderInstitutionCodes", "ARRAY"),
    ("organization", "system.currentLeaderInstitutionIds", "currentLeaderInstitutionIds", "ARRAY"),
    ("organization", "system.currentLeaderInstitutionNames", "currentLeaderInstitutionNames", "ARRAY"),
    ("organization", "system.currentLegalOrgId", "currentLegalOrgId", "BIGINTEGER"),
    ("organization", "system.currentLevelCode", "currentLevelCode", "STRING"),
    ("organization", "system.currentLevelId", "currentLevelId", "BIGINTEGER"),
    ("organization", "system.currentLevelName", "currentLevelName", "STRING"),
    ("organization", "system.currentManagerDepartmentCodes", "currentManagerDepartmentCodes", "ARRAY"),
    ("organization", "system.currentManagerDepartmentIds", "currentManagerDepartmentIds", "ARRAY"),
    ("organization", "system.currentManagerDepartmentNames", "currentManagerDepartmentNames", "ARRAY"),
    ("organization", "system.currentManagerInstitutionCodes", "currentManagerInstitutionCodes", "ARRAY"),
    ("organization", "system.currentManagerInstitutionIds", "currentManagerInstitutionIds", "ARRAY"),
    ("organization", "system.currentManagerInstitutionNames", "currentManagerInstitutionNames", "ARRAY"),
    ("organization", "system.currentMemberOrgRoleCodes", "currentMemberOrgRoleCodes", "ARRAY"),
    ("organization", "system.currentMemberOrgRoleIds", "currentMemberOrgRoleIds", "ARRAY"),
    ("organization", "system.currentMemberPostInstitutionCodes", "currentMemberPostInstitutionCodes", "ARRAY"),
    ("organization", "system.currentMemberPostInstitutionIds", "currentMemberPostInstitutionIds", "ARRAY"),
    ("organization", "system.currentMemberPostInstitutionNames", "currentMemberPostInstitutionNames", "ARRAY"),
    ("organization", "system.currentMemberPostOrgCodes", "currentMemberPostOrgCodes", "ARRAY"),
    ("organization", "system.currentMemberPostOrgIds", "currentMemberPostOrgIds", "ARRAY"),
    ("organization", "system.currentMemberPostOrgNames", "currentMemberPostOrgNames", "ARRAY"),
    ("organization", "system.currentMemberPostPartTimeInstitutionCodes", "currentMemberPostPartTimeInstitutionCodes", "ARRAY"),
    ("organization", "system.currentMemberPostPartTimeInstitutionIds", "currentMemberPostPartTimeInstitutionIds", "ARRAY"),
    ("organization", "system.currentMemberPostPartTimeInstitutionNames", "currentMemberPostPartTimeInstitutionNames", "ARRAY"),
    ("organization", "system.currentMemberPostPartTimeOrgCodes", "currentMemberPostPartTimeOrgCodes", "ARRAY"),
    ("organization", "system.currentMemberPostPartTimeOrgIds", "currentMemberPostPartTimeOrgIds", "ARRAY"),
    ("organization", "system.currentMemberPostPartTimeOrgNames", "currentMemberPostPartTimeOrgNames", "ARRAY"),
    ("date", "system.currentMonth", "currentMonth", "INTEGER"),
    ("organization", "system.currentMultiOrgCode", "currentMultiOrgCode", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentCode", "currentMultiOrgDepartmentCode", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentDivideCode", "currentMultiOrgDepartmentDivideCode", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentDivideDepartmentCode", "currentMultiOrgDepartmentDivideDepartmentCode", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentDivideDepartmentId", "currentMultiOrgDepartmentDivideDepartmentId", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentDivideDepartmentName", "currentMultiOrgDepartmentDivideDepartmentName", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentDivideId", "currentMultiOrgDepartmentDivideId", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentDivideName", "currentMultiOrgDepartmentDivideName", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentFirstCode", "currentMultiOrgDepartmentFirstCode", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentFirstId", "currentMultiOrgDepartmentFirstId", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentFirstName", "currentMultiOrgDepartmentFirstName", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentId", "currentMultiOrgDepartmentId", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentName", "currentMultiOrgDepartmentName", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentParentCode", "currentMultiOrgDepartmentParentCode", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentParentId", "currentMultiOrgDepartmentParentId", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentParentName", "currentMultiOrgDepartmentParentName", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentResponsibleCode", "currentMultiOrgDepartmentResponsibleCode", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentResponsibleDepartmentCode", "currentMultiOrgDepartmentResponsibleDepartmentCode", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentResponsibleDepartmentId", "currentMultiOrgDepartmentResponsibleDepartmentId", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentResponsibleDepartmentName", "currentMultiOrgDepartmentResponsibleDepartmentName", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentResponsibleId", "currentMultiOrgDepartmentResponsibleId", "ARRAY"),
    ("organization", "system.currentMultiOrgDepartmentResponsibleName", "currentMultiOrgDepartmentResponsibleName", "ARRAY"),
    ("organization", "system.currentMultiOrgId", "currentMultiOrgId", "ARRAY"),
    ("organization", "system.currentMultiOrgName", "currentMultiOrgName", "ARRAY"),
    ("organization", "system.currentOrgCode", "currentOrgCode", "STRING"),
    ("organization", "system.currentOrgId", "currentOrgId", "BIGINTEGER"),
    ("organization", "system.currentOrgName", "currentOrgName", "STRING"),
    ("organization", "system.currentParentInstitutionCodes", "currentParentInstitutionCodes", "ARRAY"),
    ("organization", "system.currentParentInstitutionIds", "currentParentInstitutionIds", "ARRAY"),
    ("organization", "system.currentParentInstitutionNames", "currentParentInstitutionNames", "ARRAY"),
    ("organization", "system.currentParentOrgCode", "currentParentOrgCode", "STRING"),
    ("organization", "system.currentParentOrgId", "currentParentOrgId", "BIGINTEGER"),
    ("organization", "system.currentParentOrgName", "currentParentOrgName", "STRING"),
    ("organization", "system.currentPartTimePostCodes", "currentPartTimePostCodes", "ARRAY"),
    ("organization", "system.currentPartTimePostIds", "currentPartTimePostIds", "ARRAY"),
    ("organization", "system.currentPartTimePostNames", "currentPartTimePostNames", "ARRAY"),
    ("organization", "system.currentPostCode", "currentPostCode", "STRING"),
    ("organization", "system.currentPostCodes", "currentPostCodes", "ARRAY"),
    ("organization", "system.currentPostId", "currentPostId", "BIGINTEGER"),
    ("organization", "system.currentPostIds", "currentPostIds", "ARRAY"),
    ("organization", "system.currentPostName", "currentPostName", "STRING"),
    ("organization", "system.currentPostNames", "currentPostNames", "ARRAY"),
    ("date", "system.currentSeason", "currentSeason", "INTEGER"),
    ("organization", "system.currentSecretLevel", "currentSecretLevel", "INTEGER"),
    ("organization", "system.currentSecretLevelId", "currentSecretLevelId", "BIGINTEGER"),
    ("date", "system.currentTime", "currentTime", "TIME"),
    ("date", "system.currentTimestamp", "currentTimestamp", "BIGINTEGER"),
    ("organization", "system.currentUserCode", "currentUserCode", "STRING"),
    ("organization", "system.currentUserId", "currentUserId", "BIGINTEGER"),
    ("organization", "system.currentUserLoginName", "currentUserLoginName", "STRING"),
    ("organization", "system.currentUserName", "currentUserName", "STRING"),
    ("organization", "system.currentUserType", "currentUserType", "STRING"),
    ("date", "system.currentYear", "currentYear", "INTEGER"),
    ("date", "system.firstDay4NextMonth", "firstDay4NextMonth", "DATE"),
    ("date", "system.firstDay4NextSeason", "firstDay4NextSeason", "DATE"),
    ("date", "system.firstDay4NextWeek", "firstDay4NextWeek", "DATE"),
    ("date", "system.firstDay4NextYear", "firstDay4NextYear", "DATE"),
    ("date", "system.firstDay4PreviousMonth", "firstDay4PreviousMonth", "DATE"),
    ("date", "system.firstDay4PreviousSeason", "firstDay4PreviousSeason", "DATE"),
    ("date", "system.firstDay4PreviousWeek", "firstDay4PreviousWeek", "DATE"),
    ("date", "system.firstDay4PreviousYear", "firstDay4PreviousYear", "DATE"),
    ("date", "system.firstDay4ThisMonth", "firstDay4ThisMonth", "DATE"),
    ("date", "system.firstDay4ThisSeason", "firstDay4ThisSeason", "DATE"),
    ("date", "system.firstDay4ThisWeek", "firstDay4ThisWeek", "DATE"),
    ("date", "system.firstDay4ThisYear", "firstDay4ThisYear", "DATE"),
    ("date", "system.lastDay4NextMonth", "lastDay4NextMonth", "DATE"),
    ("date", "system.lastDay4NextSeason", "lastDay4NextSeason", "DATE"),
    ("date", "system.lastDay4NextWeek", "lastDay4NextWeek", "DATE"),
    ("date", "system.lastDay4NextYear", "lastDay4NextYear", "DATE"),
    ("date", "system.lastDay4PreviousMonth", "lastDay4PreviousMonth", "DATE"),
    ("date", "system.lastDay4PreviousSeason", "lastDay4PreviousSeason", "DATE"),
    ("date", "system.lastDay4PreviousWeek", "lastDay4PreviousWeek", "DATE"),
    ("date", "system.lastDay4PreviousYear", "lastDay4PreviousYear", "DATE"),
    ("date", "system.lastDay4ThisMonth", "lastDay4ThisMonth", "DATE"),
    ("date", "system.lastDay4ThisSeason", "lastDay4ThisSeason", "DATE"),
    ("date", "system.lastDay4ThisWeek", "lastDay4ThisWeek", "DATE"),
    ("date", "system.lastDay4ThisYear", "lastDay4ThisYear", "DATE"),
    ("plugin", "system.pluginList", "pluginList", "ARRAY"),
    ("organization", "system.rootInstitutionCode", "rootInstitutionCode", "STRING"),
    ("organization", "system.rootInstitutionId", "rootInstitutionId", "BIGINTEGER"),
    ("organization", "system.rootInstitutionName", "rootInstitutionName", "STRING"),
    ("env", "system.secretEnable", "secretEnable", "BOOLEAN"),
    ("date", "system.tomorrow", "tomorrow", "STRING"),
    ("date", "system.yesterday", "yesterday", "STRING"),
)
