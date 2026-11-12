"""token 语法 —— 表达式的最小组成单位。

证据：
  CFR  `enums/TokenTypeEnum` = CONSTANT / VARIABLE / SYSTEM / FUNCTION / OPERATOR（恰 5 值）
  CFR  `parser/ast/Factor.parse:26-50` 只认 VARIABLE / CONSTANT / SYSTEM / FUNCTION 四类
  LIVE 值域外的 type（如 SYSTEM_VARIABLE / BOGUS / ""）⇒ BOOT_3000（message 为 null）
       —— 这是框架反序列化失败，不是业务错误码

★ 变量链接（用户强调的"一定会用到"）
  `schema` 返回的每个节点都带 `uniformityParams.paramId`：
      实体根  paramCategory=Entity  paramId=实体 id
      字段    paramCategory=Attr    paramId=属性 id
      应用参数 paramCategory=CONFIG_PARAM paramId=参数定义 id
  变量 token 必须带这个 paramId，否则 `VariableCheckFilter` 报
  NODE_NOT_FOUND_IN_SCHEMA_ERROR（FORMULA_6058 一族）。
  函数参数里的变量同样如此 —— 这就是"牵扯到变量字段链接一定会用到"的实体。
"""
from __future__ import annotations

import uuid

# token.type 值域（恰 5 值，CFR 权威）
TOKEN_TYPE_CONSTANT = "CONSTANT"
TOKEN_TYPE_VARIABLE = "VARIABLE"
TOKEN_TYPE_SYSTEM = "SYSTEM"
TOKEN_TYPE_FUNCTION = "FUNCTION"
TOKEN_TYPE_OPERATOR = "OPERATOR"

TOKEN_TYPES: tuple[str, ...] = (
    TOKEN_TYPE_CONSTANT,
    TOKEN_TYPE_VARIABLE,
    TOKEN_TYPE_SYSTEM,
    TOKEN_TYPE_FUNCTION,
    TOKEN_TYPE_OPERATOR,
)

# 走 paramId 链接的类型
# ★ 只有 VARIABLE。
#   SYSTEM token 用**全名**（`system.currentUserId`）由
#   ExpressionPresetRunner.loadSystemVariable → getSystemVariableItemsMap 解析，
#   不需要 paramId —— 字段集域 LIVE PASS 的写法就是不带 paramId 的
#   （components/udc/setting/attribute_set_constraints.build_sysvar_expression_dto）。
#   早期若给 SYSTEM 也强制 paramId，会把字段集那条已验证的写法判成非法。
LINKED_TOKEN_TYPES: tuple[str, ...] = (TOKEN_TYPE_VARIABLE,)


def new_uid() -> str:
    """token.uid —— 平台按 uid 做节点标识，必须是每次新建的唯一值。"""
    return str(uuid.uuid4())


def _base(token_type: str, value: str, desc: str, uid: str | None) -> dict:
    if token_type not in TOKEN_TYPES:
        raise ValueError(
            "非法 token.type=%r；值域恰 5 值: %s" % (token_type, ", ".join(TOKEN_TYPES))
        )
    return {"uid": uid or new_uid(), "type": token_type,
            "value": value, "desc": desc}


def build_constant_token(value: str, desc: str | None = None,
                         uid: str | None = None) -> dict:
    """常量：数字 / 文本 / 日期字面量。"""
    return _base(TOKEN_TYPE_CONSTANT, value, desc or value, uid)


def build_operator_token(value: str, desc: str | None = None,
                         uid: str | None = None) -> dict:
    """运算符。value 取 operators.OPERATORS 里的 value（如 '+'、'=='、'&'）。"""
    return _base(TOKEN_TYPE_OPERATOR, value, desc or value, uid)


def build_variable_token(param_id, value: str, desc: str,
                         uid: str | None = None,
                         control_data: dict | None = None,
                         entity_name: str | None = None,
                         entity_desc: str | None = None,
                         index: int | None = None) -> dict:
    """变量（实体字段 / 应用参数等）。

    param_id 来自 schema 节点的 uniformityParams.paramId —— 必填。

    ★★ 实体字段必须传 entity_name / entity_desc（2026-10-23 更正）：
       `value` = "实体名.字段名"，`desc` = "实体标题.字段标题"。
       只给短名会过 check/transform，但**页面回显报** FORMULA_6058
       「变量:xxx 在上下文中不存在」—— 因为页面按「树 + 点路径」解析。
       三维对照见 schema_binding 模块头。

    应用参数（paramCategory=CONFIG_PARAM）不需要前缀，直接传短名。
    """
    if param_id in (None, ""):
        raise ValueError(
            "变量 token 必须带 paramId（来自 schema 的 uniformityParams.paramId），"
            "否则 VariableCheckFilter 会报变量不存在"
        )
    if entity_name:
        if not value.startswith(entity_name + "."):
            value = "%s.%s" % (entity_name, value)
        if entity_desc and not desc.startswith(entity_desc + "."):
            desc = "%s.%s" % (entity_desc, desc)
    elif "." not in value and desc and entity_desc is None:
        # 未给实体上下文时保持旧行为，但调用方应知道这是危险形态
        pass

    tok = _base(TOKEN_TYPE_VARIABLE, value, desc, uid)
    tok["paramId"] = str(param_id)
    if control_data is not None:
        tok["controlData"] = control_data
    if index is not None:
        tok["g_l_index"] = str(index)
    return tok


def build_system_token(value: str, desc: str,
                       uid: str | None = None,
                       param_id=None,
                       control_data: dict | None = None) -> dict:
    """系统变量。

    ★ 两条解析通路互不等价（既有事实，勿混用）：
      A 全名   value='system.currentDateTime'  → 用 getSystemVariableItemsMap 的 resultType
      B 短名   value='currentDateTime'         → 只要同名于某函数就被当函数调用，取函数返回类型
    已知会分裂的：currentTime（STRING vs TIME）、currentDateTime（DATE vs DATETIME）。
    需要稳定类型时走全名。
    """
    tok = _base(TOKEN_TYPE_SYSTEM, value, desc, uid)
    if param_id not in (None, ""):
        tok["paramId"] = str(param_id)
    if control_data is not None:
        tok["controlData"] = control_data
    return tok


def build_function_token(name: str, desc: str, sub_ops: list,
                         uid: str | None = None,
                         control_data: dict | None = None) -> dict:
    """函数。

    sub_ops 是「参数二维数组」：subOps[i] 是第 i 个参数的 token 列表。
    无参函数传 []。
    """
    if not isinstance(sub_ops, list):
        raise TypeError("subOps 必须是二维数组（每个参数一组 token）")
    tok = _base(TOKEN_TYPE_FUNCTION, name, desc, uid)
    tok["subOps"] = sub_ops
    if control_data is not None:
        tok["controlData"] = control_data
    return tok


def validate_token(token: dict) -> list[str]:
    """结构级校验。返回错误列表，空 = 通过。

    只校验**本层能确定**的东西（类型值域、必填键、paramId 链接），
    语义与类型兼容性交给平台 `check` 端点 —— 不要在这里重复实现引擎。
    """
    errs: list[str] = []
    if not isinstance(token, dict):
        return ["token 必须是 dict，实际 %r" % type(token).__name__]

    t = token.get("type")
    if t not in TOKEN_TYPES:
        errs.append("type=%r 不在值域 %s" % (t, TOKEN_TYPES))

    for k in ("uid", "value"):
        if not token.get(k):
            errs.append("缺必填键 %s" % k)

    if t in LINKED_TOKEN_TYPES and not token.get("paramId"):
        errs.append("%s token 缺 paramId（变量/系统变量必须链接 schemas）" % t)

    if t == TOKEN_TYPE_FUNCTION:
        so = token.get("subOps")
        if not isinstance(so, list):
            errs.append("FUNCTION token 必须带 subOps（二维数组，无参传 []）")
        else:
            for i, group in enumerate(so):
                if not isinstance(group, list):
                    errs.append("subOps[%d] 必须是 token 列表" % i)

    return errs
