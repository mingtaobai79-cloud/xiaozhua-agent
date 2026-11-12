"""校验链 —— `POST /expression/check` 背后的 5 段 Filter。

证据：CFR `domain/validation/ExpressionValidator.java` + `filter/*.java`（5.3.318）

    ExpressionValidator.validatingExpression(saveDto)
        filters = Spring 注入的全部 ExpressionValidationFilter（@Order 排序）
        FilterChain.doFilter(...)  → 依次执行
        全部通过后：语义分析 + resultTypeCompatibilityCheck()

    5 个 Filter（按反编译件的类职责，非猜测）：
        1 TokenLexerFilter            词法：token 结构、邻居合法性
        2 SchemaDefinitionFilter      schema 定义：类型是否支持、枚举信息是否齐
        3 VariableCheckFilter         变量存在性：token 是否在 schemas 里
        4 ResultTypeDefinitionFilter  结果类型定义
        （ExpressionValidationFilter 是接口，FilterChain 是调度器，不计入 5 个实现）

★ 关键分工（决定"哪些错该本地挡、哪些必须交给平台"）：
    - 本地只挡**结构错**（type 值域、缺 uid/value、FUNCTION 缺 subOps、VARIABLE 缺 paramId）
      → 这类错平台会回 BOOT_3000 且 message 为 null，几乎无法定位，必须先在本层拦
    - 类型兼容、聚合合法性、枚举分支、类型转换（FORMULA_6071/6170/6172 等）
      → **必须**交平台 check，本地不要重复实现，否则会出现"本地过了平台不过"的假阳性
"""
from __future__ import annotations

# Filter 链顺序（CFR 类职责；执行顺序由 @Order 决定，这里记职责序）
VALIDATION_FILTERS: tuple[str, ...] = (
    "TokenLexerFilter",
    "SchemaDefinitionFilter",
    "VariableCheckFilter",
    "ResultTypeDefinitionFilter",
)

# 调度器与接口（不是 Filter 实现，别当第 5 个）
VALIDATION_INFRA: tuple[str, ...] = (
    "ExpressionValidator",       # 入口，最后做 resultTypeCompatibilityCheck
    "FilterChain",               # 责任链调度
    "ExpressionValidationFilter",  # 接口
)

# 错误码。分两类：结构错（本地该拦）/ 语义错（交平台）
EXPRESSION_ERROR_CODES: dict[str, str] = {
    # —— 本地可拦的结构错
    "BOOT_3000": "token.type 值域外 / 端点入参不识别（message 为 null，最难定位，必须本地拦）",
    "BOOT_3002": "preset/list 的 terminalSupportType 缺失或非法",
    # —— 平台语义错
    "FORMULA_6058": "变量不存在：CVariable :<desc> does not exist in context",
    "FORMULA_6066": "TokenLexerFilter：token 结构非法（<desc>）",
    "FORMULA_6068": "ResultTypeDefinitionFilter：结果类型缺失",
    "FORMULA_6071": "UDC 枚举类型转换不兼容",
    "FORMULA_6170": "实体类型转换不兼容",
    "FORMULA_6172": "实体多值/单值不匹配",
    "UDC_EXPRESSION_7005": "实体信息为空（paramType=ENTITY 系列未传 ids）",
    "UDC_EXPRESSION_7008": "表达式为空",
    "UDC_ATTR_0017": "expressionDesignData 缺 resultTypeInfo 或 tokens 为空",
    "UDC_ATTR_0018": "defaultValueExpressionDesignData 缺 resultTypeInfo 或 tokens 为空",
}

# 结构错 —— 本地必须在提交前拦掉的（否则平台只回 null message）
STRUCTURAL_ERRORS: tuple[str, ...] = ("BOOT_3000", "BOOT_3002")

# 必须交平台 check 的语义错（本地不实现）
SEMANTIC_ERROR_PREFIXES: tuple[str, ...] = ("FORMULA_", "UDC_ATTR_", "UDC_EXPRESSION_")


def validation_chain_order() -> tuple[str, ...]:
    return VALIDATION_FILTERS


def is_structural(code: str) -> bool:
    return code in STRUCTURAL_ERRORS


def is_semantic(code: str) -> bool:
    return any(code.startswith(p) for p in SEMANTIC_ERROR_PREFIXES)


def explain(code: str) -> str:
    if code in EXPRESSION_ERROR_CODES:
        return EXPRESSION_ERROR_CODES[code]
    if is_semantic(code):
        return "平台语义错（未登记细则，查 CFR %s 族）" % code.split("_")[0]
    return "未登记错误码 %s" % code


# 表达式承载字段成对写（design 回显 / runtime 代码生成）—— 与具体域无关的约束
DESIGN_RUNTIME_PAIRS: tuple[tuple[str, str], ...] = (
    ("expressionDesignData", "expressionRuntimeData"),
    ("defaultValueExpressionDesignData", "defaultValueExpressionRuntimeData"),
)

# designData 必须含的键（缺 context 会让 UDC 检测器 NPE）
DESIGN_MIN_KEYS: tuple[str, ...] = ("context", "resultTypeInfo", "tokens")
