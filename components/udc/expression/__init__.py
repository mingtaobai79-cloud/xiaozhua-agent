"""UDC 表达式公用层 —— 跨域能力，不属于任何单一域。

为什么单独成层
--------------
「表达式设置」在设计器里出现于多处，看起来是各模块自己的功能：

    实体域   字段的 默认值 / 计算值 / 取值范围
    设置域   字段集、参数（应用参数）
    菜单域   页面规则、页面事件
    流程域   微流程节点入参 / 条件分支
    规则域   实体规则、生单/扣减规则条件

但**引擎只有一套**。权威证据见 `core/facts/udc/expression/README.md`：

    boot-starter-formula-5.3.318.jar（单一 ExpressionController，9 个端点）
    校验 = ExpressionValidator → FilterChain → 5 个 Filter（与调用方无关）
    函数 = 88（BACKEND）/ 81（FRONTEND），由 terminalSupportType 裁剪，不由模块决定

各模块的差别**只在两处**，都在本层的扩展点上：

    paramType      变量面（哪来的变量）        @ParamLoadService(type=...)
    terminal       函数面（前后端能跑哪些）    terminalSupportType

所以正确做法是：公用层建一次，各域只注册自己的 SchemaLoader 并声明 terminal。

分层
----
    endpoints.py    9 个端点的权威契约（来自 ExpressionController）
    token.py        token 五型语法 + 变量链接（uniformityParams.paramId）
    operators.py    18 运算符 / 5 类
    param_types.py  paramType 注册表 = 扩展点
    terminal.py     terminalSupportType 裁剪（88 / 81）
    validation.py   5 个 Filter 的校验链 + 错误码

不做的事
--------
- 不在本层写任何具体域的业务语义（实体字段、页面规则各自的落库字段不同）
- 不把某个域的落库位置（如 udc_attribute.expression_*）写成公用常识
"""
from .endpoints import (
    EXPRESSION_ENDPOINTS,
    EXPRESSION_PATH_PREFIX,
    endpoint_names,
    get_endpoint,
)
from .frontend_schema import (
    DEFAULT_UNLOADED_SCHEMAS,
    ENUM_RESULT_TYPE_CAST,
    FRONTEND_FLOW_TYPES,
    FRONT_NODE,
    MODULE_LABELS,
    build_front_node,
    normalize_result_type,
    should_load_schema,
    terminal_for_flow_type,
)
from .operators import (
    OPERATOR_OP_TYPES,
    OPERATORS,
    QUICK_FUNCTIONS,
    operators_by_type,
)
from .schema_binding import (
    MINIMAL_SCHEMA_KEYS,
    bind_schemas,
    check_binding,
    iter_tokens,
    minimal_node,
    required_param_ids,
    variable_tokens,
)
from .dto import (
    RESULT_TYPE_BY_DATA_TYPE,
    build_save_dto,
    result_type_for,
    summarize as dto_summary,
    validate_against_data_type,
    validate_save_dto,
)
from .mapping import (
    ABSENT_SLOTS,
    CALCULATE_AGGREGATION,
    CALCULATE_COMPUTE,
    CALCULATE_NORMAL,
    ExpressionSlot,
    columns_for,
    get_slot,
    slots_for_domain,
    validate_slot_consistency,
)
from .param_types import (
    PARAM_TYPE_REGISTRY,
    ParamTypeSpec,
    is_registered,
    registered_types,
    spec_for,
)
from .terminal import (
    TERMINAL_BACKEND,
    TERMINAL_FRONTEND,
    TERMINAL_SUPPORTED,
    function_count_for,
    is_valid_terminal,
)
from .token import (
    TOKEN_TYPES,
    TOKEN_TYPE_CONSTANT,
    TOKEN_TYPE_FUNCTION,
    TOKEN_TYPE_OPERATOR,
    TOKEN_TYPE_SYSTEM,
    TOKEN_TYPE_VARIABLE,
    build_constant_token,
    build_function_token,
    build_operator_token,
    build_system_token,
    build_variable_token,
    validate_token,
)
from .validation import (
    EXPRESSION_ERROR_CODES,
    VALIDATION_FILTERS,
    validation_chain_order,
)

__all__ = [
    "EXPRESSION_ENDPOINTS", "EXPRESSION_PATH_PREFIX", "endpoint_names", "get_endpoint",
    "DEFAULT_UNLOADED_SCHEMAS", "ENUM_RESULT_TYPE_CAST", "FRONTEND_FLOW_TYPES",
    "FRONT_NODE", "MODULE_LABELS", "build_front_node", "normalize_result_type",
    "should_load_schema", "terminal_for_flow_type",
    "OPERATOR_OP_TYPES", "OPERATORS", "QUICK_FUNCTIONS", "operators_by_type",
    "MINIMAL_SCHEMA_KEYS", "bind_schemas", "check_binding", "iter_tokens",
    "minimal_node", "required_param_ids", "variable_tokens",
    "RESULT_TYPE_BY_DATA_TYPE", "build_save_dto", "result_type_for", "dto_summary",
    "validate_against_data_type", "validate_save_dto",
    "ABSENT_SLOTS", "CALCULATE_AGGREGATION", "CALCULATE_COMPUTE", "CALCULATE_NORMAL",
    "ExpressionSlot", "columns_for", "get_slot", "slots_for_domain",
    "validate_slot_consistency",
    "PARAM_TYPE_REGISTRY", "ParamTypeSpec", "is_registered", "registered_types", "spec_for",
    "TERMINAL_BACKEND", "TERMINAL_FRONTEND", "TERMINAL_SUPPORTED",
    "function_count_for", "is_valid_terminal",
    "TOKEN_TYPES", "TOKEN_TYPE_CONSTANT", "TOKEN_TYPE_FUNCTION", "TOKEN_TYPE_OPERATOR",
    "TOKEN_TYPE_SYSTEM", "TOKEN_TYPE_VARIABLE",
    "build_constant_token", "build_function_token", "build_operator_token",
    "build_system_token", "build_variable_token", "validate_token",
    "EXPRESSION_ERROR_CODES", "VALIDATION_FILTERS", "validation_chain_order",
]
