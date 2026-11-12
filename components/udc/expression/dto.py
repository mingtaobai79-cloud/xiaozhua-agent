"""ExpressionSaveDto 构造与校验 —— 公用的提交体。

各域以前各写一份（字段集就有自己的 `build_sysvar_expression_dto`），
本模块收敛成一份，差异只留在 `mapping.py` 的槽位表。

证据
----
- `ExpressionSaveDto` 键（LIVE 全过）：
  resultTypeInfo / schemas / tokens / isMultiSelect / terminalSupportType /
  sourceAppName / version
- `resultTypeInfo` 必须等于字段 dataType，否则 `FORMULA_6901`
  （"计算结果为: 文本 类型, 无法赋值给: 长整数 类型"）
- 枚举 / 选项集归一化为 LONG（前端 bundle：`Enum||CtpEnum ? Long : e`）
"""
from __future__ import annotations

from .token import validate_token

# 字段 dataType → 表达式 resultTypeInfo（LIVE 实测的对应关系）
RESULT_TYPE_BY_DATA_TYPE: dict[str, str] = {
    # 文本族
    "STRING": "STRING",
    "MULTILINESTRING": "STRING",
    "MULTILINETEXT": "STRING",
    "ATTACHMENT": "STRING",
    "DOCUMENTNUMBER": "STRING",
    "OPINION": "STRING",
    "CONTENT": "STRING",
    "SERIAL": "STRING",
    # 数值族
    "INTEGER": "INTEGER",
    "BIGINTEGER": "BIGINTEGER",
    "LONG": "BIGINTEGER",
    "DECIMAL": "DECIMAL",
    "CURRENCY": "DECIMAL",
    "DOUBLE": "DECIMAL",
    # 时间族
    "DATE": "DATE",
    "TIME": "TIME",
    "DATETIME": "DATETIME",
    # 布尔
    "BOOLEAN": "BOOLEAN",
    # 枚举族 → LONG（归一化）
    "ENUM": "LONG",
    "CTPENUM": "LONG",
    "OPTION_SET": "LONG",
}

# 必须显式给出 resultTypeInfo 之外的默认值：不给就报错，不猜
_REQUIRED_KEYS = ("resultTypeInfo", "tokens", "terminalSupportType")


def result_type_for(data_type: str) -> str:
    """字段类型 → 表达式 resultTypeInfo。未知类型抛错，不返回原值蒙混。"""
    key = (data_type or "").strip().upper()
    if key in RESULT_TYPE_BY_DATA_TYPE:
        return RESULT_TYPE_BY_DATA_TYPE[key]
    raise ValueError(
        "未知字段 dataType=%r，无法确定 resultTypeInfo。"
        "已知：%s" % (data_type, ", ".join(sorted(RESULT_TYPE_BY_DATA_TYPE)))
    )


def build_save_dto(tokens: list[dict],
                   *,
                   result_type: str,
                   terminal: str = "BACKEND",
                   schemas: list | None = None,
                   is_multi_select: bool = False,
                   source_app_name: str | None = None,
                   version: str | None = None) -> dict:
    """构造 ExpressionSaveDto。

    tokens 用 token.py 的构造器产出；result_type 用 result_type_for(data_type)。
    """
    if not isinstance(tokens, list) or not tokens:
        raise ValueError("tokens 不能为空")
    dto: dict = {
        "resultTypeInfo": result_type,
        "schemas": schemas if schemas is not None else [],
        "tokens": tokens,
        "isMultiSelect": bool(is_multi_select),
        "terminalSupportType": terminal,
    }
    if source_app_name is not None:
        dto["sourceAppName"] = source_app_name
    if version is not None:
        dto["version"] = version
    return dto


def validate_save_dto(dto: dict) -> list[str]:
    """提交前本地校验。只挡结构错，语义交平台 check。"""
    errs: list[str] = []
    if not isinstance(dto, dict):
        return ["ExpressionSaveDto 必须是 dict"]

    for k in _REQUIRED_KEYS:
        if k not in dto:
            errs.append("缺必填键 %s" % k)

    if not isinstance(dto.get("tokens"), list):
        errs.append("tokens 必须是数组")
    elif not dto["tokens"]:
        errs.append("tokens 不能为空数组（空表达式平台回 UDC_EXPRESSION_7008）")
    else:
        for i, t in enumerate(dto["tokens"]):
            for e in validate_token(t):
                errs.append("tokens[%d]: %s" % (i, e))

    schemas = dto.get("schemas")
    if schemas is not None and not isinstance(schemas, list):
        errs.append("schemas 必须是数组（没有变量就给 []，不能省成 null）")

    if dto.get("terminalSupportType") not in ("BACKEND", "FRONTEND", "ALL"):
        errs.append("terminalSupportType=%r 非法"
                    % (dto.get("terminalSupportType"),))

    rt = dto.get("resultTypeInfo")
    if not rt:
        errs.append("resultTypeInfo 不能为空（缺失报 FORMULA_6068）")

    return errs


def validate_against_data_type(dto: dict, data_type: str) -> list[str]:
    """resultTypeInfo 与字段 dataType 是否匹配（不匹配必报 FORMULA_6901）。"""
    errs = []
    try:
        expect = result_type_for(data_type)
    except ValueError as exc:
        return [str(exc)]
    got = dto.get("resultTypeInfo")
    if got != expect:
        errs.append(
            "resultTypeInfo=%r 与字段 dataType=%r 不匹配（应为 %r）；"
            "不匹配必报 FORMULA_6901" % (got, data_type, expect)
        )
    return errs


def summarize(dto: dict) -> str:
    """一行摘要，便于日志与汇报。"""
    toks = dto.get("tokens") or []
    kinds = []
    for t in toks:
        kinds.append("%s:%s" % (t.get("type"), t.get("value")))
    return "resultType=%s terminal=%s tokens[%s]" % (
        dto.get("resultTypeInfo"), dto.get("terminalSupportType"),
        ", ".join(kinds) or "-")
