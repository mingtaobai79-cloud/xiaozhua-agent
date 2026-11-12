"""设置域 · 参数（Parameter）实现与校验。

落库表：`ctp_parameter_definition`（注意 app_id 是 **varchar**，不是 bigint）
接口：`udcCtpParameterDefinitonPost` / `udcCtpParameterDefinitonUpdatePost`
      （`Definiton` 是平台的拼写错误，少一个 i，必须照抄）
读接口：`udcCtpParameterDefinitonSearch` + `udcDataTypeDataTypesParamGet`

证据：2026-10-21 LIVE PASS（BOOT_0000 + DB 回读），见
`core/facts/udc/setting/parameter/create.md`。

踩过的坑：
  - `dataTypeProperties` 必须传**对象**，传 JSON 字符串报
    BOOT_3002「属性dataTypeProperties的值反序列化为LinkedHashMap类型时失败」
  - 落库时它被序列化成字符串存，但**提交时必须是对象**
"""
from __future__ import annotations

from typing import Any

# 参数数据类型（与 udc_dto_attribute 的 dataType 同族，但这里是参数语义）
PARAM_DATA_TYPES = (
    "STRING", "INTEGER", "BIGINTEGER", "DECIMAL",
    "DATE", "DATETIME", "BOOLEAN",
)

# dataTypeProperties 的默认形态（按类型给默认约束）
DEFAULT_PROPERTIES: dict[str, dict[str, Any]] = {
    "STRING": {"minLength": 0, "maxLength": 100},
    "INTEGER": {"min": None, "max": None},
    "BIGINTEGER": {"min": None, "max": None},
    "DECIMAL": {"decimalDigits": 2, "min": None, "max": None},
    "DATE": {},
    "DATETIME": {},
    "BOOLEAN": {},
}


def build_parameter_body(app_id: str | int, app_guid: str | int, *,
                         name: str, caption: str,
                         data_type: str = "STRING",
                         data_type_properties: dict[str, Any] | None = None,
                         value: str = "",
                         param_group: str = "",
                         order_no: int = 1,
                         description: str = "",
                         type_: int = 0) -> dict[str, Any]:
    """参数创建/更新 body（udcCtpParameterDefinitonPost / UpdatePost）。

    实测必填：caption（参数显示名称）、appId
    """
    props = data_type_properties
    if props is None:
        props = dict(DEFAULT_PROPERTIES.get(data_type, {}))
    return {
        "appId": str(app_id),
        "appGuid": str(app_guid),
        "name": name,
        "caption": caption,
        "description": description,
        "dataType": data_type,
        "dataTypeProperties": props,      # 必须是对象
        "paramGroup": param_group,
        "value": value,
        "orderNo": int(order_no),
        "type": int(type_),
    }


def validate_parameter_body(body: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["参数 body 必须是对象"]
    if not body.get("caption"):
        errs.append("参数缺 caption（实测 BOOT_1001「参数显示名称 不能为空」）")
    if not body.get("appId"):
        errs.append("参数缺 appId")
    if not body.get("dataType"):
        errs.append("参数缺 dataType")
    elif body["dataType"] not in PARAM_DATA_TYPES:
        errs.append(f"参数 dataType 应为 {PARAM_DATA_TYPES} 之一，实际 {body['dataType']!r}")
    props = body.get("dataTypeProperties")
    if props is not None and not isinstance(props, dict):
        errs.append("dataTypeProperties 必须是对象（传字符串报 BOOT_3002 反序列化失败）")
    return errs


__all__ = ["PARAM_DATA_TYPES", "DEFAULT_PROPERTIES",
           "build_parameter_body", "validate_parameter_body"]
