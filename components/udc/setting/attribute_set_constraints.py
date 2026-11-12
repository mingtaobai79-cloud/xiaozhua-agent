"""设置域 · 字段集（Attribute Set）实现与校验。

## 协议：混合 —— 父级 REST，子级 GraphQL（★ 这是本轮最大发现）

```
父（字段集本身）  REST     /service/udc/attributeSet        ← 驼峰
父（分组）        REST     /service/udc/attribute-group     ← 连字符
子（字段）        GraphQL  udcEntityAttributePost           ← ★ 不是 REST
```

**我最初以为字段也走 REST `attributeSet/update`，4 种变体全部静默失败**
（回 BOOT_0000 但 `udc_attribute` 零写入）。真实入口是 GraphQL
`udcEntityAttributePost` —— 2026-10-21 从页面真实操作抓包才确认。

## 完整可用链路（LIVE PASS）

```python
# 1) 建字段集壳（REST）
POST /service/udc/attributeSet
{appId, name, caption, sourceType, attributes: []}     → data.content = 字段集 id

# 2) 加字段（GraphQL）
mutation udcEntityAttributePost
body = build_attribute_field_body(app_id, set_id, name=..., caption=...)
→ BOOT_0000, data.content = 字段 id

# 3) 读字段（REST）
POST /service/udc/attributeSet/select-attribute-list  {"attributeSetId": "<id>"}
```

## 页面操作要点（UI 走通记录）

字段集界面是「左列表 + 右常驻表单」：

1. 左列表点行内 `lined-edit` 选中字段集
2. 右侧「名称」填显示名 —— 中文会自动转拼音填到「编码」
   （`验收字段集U` → `yanshouziduanjiU`）
3. 点「确定」（在 `.extension-form-footer`，y≈847；不是表格里的）
4. ⚠ 名称/编码空着点确定只出红字「请输入名称/请输入编码」，**不发请求**

证据：字段 `yanshouziduanjiU`（页面建）+ `probeFieldTwo`（接口复现）均落库，
`udc_attribute.entity_id` 指向字段集、`source_type=1`。
"""
from __future__ import annotations

import json
from typing import Any

# AttributeSetSourceTypeEnum
SOURCE_TYPE = {"UDC": 1, "ISV": 2, "APP": 3}

# 18 种平台 dataType（2026-10-21 从 udcDataTypeDataTypesByAppIdAppGet 实拉）
FIELD_DATA_TYPES = (
    # 基础
    "STRING", "MULTILINESTRING", "INTEGER", "BIGINTEGER", "DECIMAL", "CURRENCY",
    "DATE", "TIME", "DATETIME", "BOOLEAN",
    # 关联
    "ENUM", "CTPENUM", "ATTACHMENT", "ENTITY",
    # 自定义类型（custom=True，base 指向基础类型）
    "DOCUMENTNUMBER", "Serial", "OPINION", "CONTENT",
)

# 需要关联目标的类型（缺了报 UDC_DATATYPE_0015 / 0017）
NEEDS_RELATION = {
    "CTPENUM": "关联枚举不存在 → 需 ctpEnums / rootEnumId",
    "ENUM": "选项集 → 需关联 udc_enum",
    "ENTITY": "关联实体不存在 → 需 relationEntity",
}

NAME_MAX = 30
CAPTION_MAX = 50

# ---------------------------------------------------------------- 控件默认值（按 dataType）
# ★ 2026-10-21 从 DB 真实样本按 dataType 分组统计得出（每组取众数）。
#   之前一律用 Input 是错的：日期用 Input 装不了、枚举用 Input 选不了、附件用 Input 传不了。
#
# 格式：dataType -> (pc 控件, mobile 控件)
DEFAULT_WIDGETS: dict[str, tuple[str, str]] = {
    "STRING":          ("Input",           "Input"),
    "MULTILINESTRING": ("TextArea",        "TextArea"),
    "INTEGER":         ("InputNumber",     "InputNumber"),
    "BIGINTEGER":      ("Input",           "Input"),        # 注意：BIGINTEGER 真实样本是 Input
    "DECIMAL":         ("InputNumber",     "InputNumber"),
    "CURRENCY":        ("Currency",        "Currency"),
    "DATE":            ("DatePicker",      "DateTimePicker"),
    "TIME":            ("TimePicker",      "TimePicker"),
    "DATETIME":        ("DatePicker",      "DateTimePicker"),
    "BOOLEAN":         ("Switch",          "Switch"),
    "ENUM":            ("TreeSelect",      "CascaderSelect"),
    "CTPENUM":         ("TreeSelect",      "CascaderSelect"),
    "ENTITY":          ("UdcReference",    "UdcReference"),
    "ATTACHMENT":      ("Attachment",      "Upload"),
    "DOCUMENTNUMBER":  ("Input",           "Input"),
    "Serial":          ("Input",           "Input"),
    "OPINION":         ("Input",           "Input"),
    "CONTENT":         ("UiBusinessContent", "UiBusinessContent"),
}

# 默认的 list/detail/quickSearch（按真实样本众数）
DEFAULT_WIDGET_FLAGS: dict[str, dict] = {
    "STRING":          {"list": True,  "detail": True,  "quickSearch": True},
    "MULTILINESTRING": {"list": True,  "detail": True,  "quickSearch": False},
    "INTEGER":         {"list": False, "detail": False, "quickSearch": False},
    "BIGINTEGER":      {"list": False, "detail": False, "quickSearch": False},
    "DECIMAL":         {"list": True,  "detail": True,  "quickSearch": True},
    "CURRENCY":        {"list": True,  "detail": True,  "quickSearch": True},
    "DATE":            {"list": True,  "detail": True,  "quickSearch": True},
    "TIME":            {"list": True,  "detail": True,  "quickSearch": True},
    "DATETIME":        {"list": False, "detail": False, "quickSearch": False},
    "BOOLEAN":         {"list": True,  "detail": True,  "quickSearch": True},
    "ENUM":            {"list": False, "detail": False, "quickSearch": False},
    "CTPENUM":         {"list": True,  "detail": True,  "quickSearch": True},
    "ENTITY":          {"list": False, "detail": False, "quickSearch": False},
    "ATTACHMENT":      {"list": False, "detail": True,  "quickSearch": False},
    "CONTENT":         {"list": False, "detail": True,  "quickSearch": False},
}


def build_widget_config(data_type: str,
                        *, pc: str | None = None, mobile: str | None = None,
                        list_: bool | None = None, detail: bool | None = None,
                        quick_search: bool | None = None) -> str:
    """按 dataType 生成正确形态的 widgetConfig（JSON 字符串）。

    不传 pc/mobile 时用该类型的默认控件（见 DEFAULT_WIDGETS）。
    """
    dpc, dmob = DEFAULT_WIDGETS.get(data_type, ("Input", "Input"))
    flags = dict(DEFAULT_WIDGET_FLAGS.get(data_type, {}))
    if list_ is not None:
        flags["list"] = bool(list_)
    if detail is not None:
        flags["detail"] = bool(detail)
    if quick_search is not None:
        flags["quickSearch"] = bool(quick_search)
    return json.dumps({
        "pc": pc or dpc,
        "mobile": mobile or dmob,
        "list": flags.get("list", True),
        "detail": flags.get("detail", True),
        "quickSearch": flags.get("quickSearch", True),
    }, ensure_ascii=False, separators=(",", ":"))


# 兼容旧引用：STRING 的默认值
DEFAULT_WIDGET_CONFIG = build_widget_config("STRING")


def build_attribute_set_body(app_id: str | int, *,
                             name: str, caption: str,
                             source_type: str = "APP",
                             order_no: int = 1,
                             description: str = "",
                             set_id: str | int | None = None) -> dict[str, Any]:
    """构造字段集 body（AttributeSetDto）—— REST create/update 用。

    ⚠ `attributes` 在这里**不生效**（父级不处理子集合）；
      加字段用 `build_attribute_field_body` + GraphQL `udcEntityAttributePost`。
    """
    body: dict[str, Any] = {
        "appId": str(app_id),
        "name": name,
        "caption": caption,
        "description": description,
        "sourceType": source_type,
        "orderNo": int(order_no),
        "attributes": [],
    }
    if set_id is not None:
        body["id"] = str(set_id)
    return body


def build_attribute_field_body(app_id: str | int, set_id: str | int, *,
                               name: str, caption: str,
                               data_type: str = "STRING",
                               order_no: int = 1,
                               not_null: bool = False,
                               min_length: int = 0, max_length: int = 50,
                               searchable: bool = False, uniqueness: bool = False,
                               attribute_group: str = "",
                               widget_config: str | None = None,
                               # CTPENUM 专用（★ 关系型字段三个都要传，缺一个页面就显示 null）
                               relation_code: str | None = None,
                               relation_entity_name: str | None = None,
                               relation_enum_type: str = "SAME_LEVEL",
                               relation_enum_level: int = 0,
                               field_id: str | int | None = None,
                               multi_select: bool = False,
                               # 正则校验（2026-10-22 补：20 项配置矩阵里此前无构造入口，
                               #   只能手改 body，导致「正则校验」这一项只能在脚本里裸拼）
                               data_format: str | None = None,
                               pattern_message: str | None = None,
                               # 脱敏 / 加密 / 敏感词（同样是 20 项配置里的项）
                               enable_desensitization: bool = False,
                               desensitization: str = "None",
                               enable_encryption: bool = False,
                               encryption: str = "NOT_ENCRYPTION",
                               enable_sensitive_word_check: bool = False,
                               # DECIMAL/CURRENCY 精度（UDC_DATATYPE_0006：maxLength 表达总精度，<=38）
                               decimal_digits: int | None = None,
                               ) -> dict[str, Any]:
    """构造字段 body。

    新建 → GraphQL `udcEntityAttributePost`
    修改 → GraphQL `udcEntityAttributeUpdatePost`（必须带 field_id）

    CTPENUM 字段三个关联槽位缺一不可（2026-10-21 用户现场纠正）：

      relationCode          平台枚举编码（如 XzhCtpEnum953322）
      relationEntity        枚举 id
      relationEntityName    枚举显示名（缺了页面「枚举」列显示 null）

    以及 relationCtpEnum（只带 enumType/enumLevel，不要 id/code）。
    """
    body: dict[str, Any] = {
        "0": str(order_no),
        "caption": caption,
        "name": name,
        "dataType": data_type,
        "notNull": bool(not_null),
        "searchable": bool(searchable),
        "defaultValue": "",
        "multiSelect": bool(multi_select),
        "uniqueness": bool(uniqueness),
        "auditLog": False,
        "minLength": int(min_length),
        "maxLength": int(max_length),
        "relationType": "Many2OneAssociation",
        "defaultValueSystemVariable": "",
        "defaultValueExpressionDesignData": "",
        "defaultValueExpressionRuntimeData": "",
        "defaultValueIsChange": True,
        "defaultValueCaption": "",
        "calculate": "NORMAL",
        "expressionDesignData": "",
        "expressionRuntimeData": "",
        "sourceType": "ATTRIBUTESET",
        "entityId": str(set_id),
        "sourceId": str(set_id),
        "appId": str(app_id),
        "description": "",
        # ★ 按 dataType 自动选正确控件（日期用 Input 装不了、枚举用 Input 选不了）
        "widgetConfig": widget_config or build_widget_config(data_type),
    }
    if field_id is not None:
        body["id"] = str(field_id)
    # DECIMAL/CURRENCY 精度：平台用 maxLength 表达总精度（<=38）+ decimalDigits
    if decimal_digits is not None:
        body["decimalDigits"] = int(decimal_digits)
    # 字段级配置项（20 项矩阵里此前只能手改 body 的几项）
    if data_format:
        body["dataFormat"] = data_format
        body["patternMessage"] = pattern_message or ""
    if enable_desensitization:
        body["enableDesensitization"] = True
        body["desensitization"] = desensitization
    if enable_encryption:
        body["enableEncryption"] = True
        body["encryption"] = encryption
    if enable_sensitive_word_check:
        body["enableSensitiveWordCheck"] = True
    if data_type == "CTPENUM":
        if not (relation_code and relation_entity_name):
            raise ValueError(
                "CTPENUM 字段必须同时给 relation_code（平台枚举编码，如 XzhCtpEnum953322）"
                "和 relation_entity_name（枚举显示名）—— 缺一个页面「枚举」列就显示 null"
                "（2026-10-21 用户现场确认）")
        body["relationCode"] = relation_code
        body["relationEntityName"] = relation_entity_name
        body["relationCtpEnum"] = {
            "enumType": relation_enum_type,
            "enumLevel": int(relation_enum_level),
        }
    return body


def build_read_attributes_body(attribute_set_id: str | int) -> dict[str, Any]:
    """`select-attribute-list` 的 body（REST）。

    键名是 `attributeSetId`，不是 `id`（传 id 报 UDC_ENTITY_0022 字段集不存在）。
    """
    return {"attributeSetId": str(attribute_set_id)}


def validate_attribute_set_body(body: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["字段集 body 必须是对象"]

    if not body.get("appId"):
        errs.append("缺 appId（实测 BOOT_1001「字段集所属应用Id 不能为null」）")

    name = str(body.get("name") or "")
    if not name:
        errs.append("缺 name（DTO @NotBlank）")
    elif len(name) > NAME_MAX:
        errs.append(f"name 超长 {len(name)} > {NAME_MAX}（DTO @Length(max=30)）")

    caption = str(body.get("caption") or "")
    if not caption:
        errs.append("缺 caption（实测 BOOT_1001「字段集显示名称 不能为空」）")
    elif len(caption) > CAPTION_MAX:
        errs.append(f"caption 超长 {len(caption)} > {CAPTION_MAX}（DTO @Length(max=50)）")

    st = body.get("sourceType")
    if st is None:
        errs.append("缺 sourceType（DTO @NotNull；值为 APP / UDC / ISV 或 3/1/2）")
    elif isinstance(st, str) and st not in SOURCE_TYPE:
        errs.append(f"sourceType 字符串须为 {tuple(SOURCE_TYPE)} 之一，实际 {st!r}")

    if body.get("attributes"):
        errs.append("⚠ attributes 在本接口不生效 —— 加字段请用 "
                    "build_attribute_field_body + GraphQL udcEntityAttributePost")
    return errs


def validate_attribute_field_body(body: dict[str, Any],
                                  set_id: str | int | None = None) -> list[str]:
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["字段 body 必须是对象"]

    for k in ("name", "caption"):
        if not body.get(k):
            errs.append(f"字段缺 {k}（两者不同：name=编码、caption=显示名）")

    nm = str(body.get("name") or "")
    if nm:
        if any("\u4e00" <= ch <= "\u9fa5" for ch in nm):
            errs.append("字段 name（编码）不能含中文 —— 页面会自动转拼音，"
                        "如 验收字段集U → yanshouziduanjiU")
        # 实测 UDC_ENTITY_0026：只能字母/数字/下划线，必须以字母开头、不能以下划线结尾
        import re as _re
        if not (_re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", nm) and not nm.endswith("_")):
            errs.append(
                f"字段 name={nm!r} 不合规（实测 UDC_ENTITY_0026：只能字母/数字/下划线，"
                "必须以字母开头，不能以下划线结尾）")

    dt = body.get("dataType")
    if dt not in FIELD_DATA_TYPES:
        errs.append(f"字段 dataType 须为 {FIELD_DATA_TYPES} 之一，实际 {dt!r}")

    if not body.get("entityId"):
        errs.append("字段缺 entityId（DTO @NotNull；实测「实体主键ID 不能为null」）")
    elif set_id is not None and str(body["entityId"]) != str(set_id):
        errs.append(f"字段 entityId={body['entityId']!r} 必须等于字段集 id {set_id!r}")

    if body.get("sourceType") != "ATTRIBUTESET":
        errs.append("字段 sourceType 应为 'ATTRIBUTESET'")

    if set_id is not None and str(body.get("sourceId")) != str(set_id):
        errs.append(f"字段 sourceId={body.get('sourceId')!r} 必须等于字段集 id {set_id!r}")

    wc = body.get("widgetConfig")
    if wc is not None and not isinstance(wc, str):
        errs.append("widgetConfig 必须是 JSON **字符串**，不是对象")
    elif isinstance(wc, str):
        try:
            json.loads(wc)
        except Exception:
            errs.append("widgetConfig 不是合法 JSON 字符串")
    return errs


__all__ = [
    "SOURCE_TYPE", "FIELD_DATA_TYPES", "NAME_MAX", "CAPTION_MAX", "DEFAULT_WIDGET_CONFIG",
    "build_attribute_set_body", "build_attribute_field_body",
    "build_read_attributes_body",
    "validate_attribute_set_body", "validate_attribute_field_body",
]


# ---------------------------------------------------------------- 系统变量默认值
# ★ 2026-10-21 实测：defaultValueSystemVariable 传纯文本会让前端 JSON.parse 崩溃，
#   整个字段集面板白屏。必须传 JSON 字符串。
#
# 两种合法格式（同一位置，不同域用不同格式）：
#   A 单 token（真实业务字段）：{"type":"SYSTEM_VARIABLE","value":"currentUserId",
#                               "desc":"登录人员ID","dataType":"BIGINTEGER"}
#   B ExpressionSaveDto（字段集）：{"resultTypeInfo":"ENTITY","schemas":[],
#                                 "tokens":[{"value":"system.currentUserId",...}],
#                                 "isMultiSelect":false,"terminalSupportType":"BACKEND"}

SYSTEM_VARIABLE_NAMES = {
    "currentUserId": ("登录人员ID", "BIGINTEGER"),
    "currentUserName": ("登录人员姓名", "STRING"),
    "currentInstitutionId": ("登录人员机构ID", "BIGINTEGER"),
    "currentOrgId": ("登录部门ID", "BIGINTEGER"),
    "currentPostId": ("登录岗位ID", "BIGINTEGER"),
    "currentDate": ("系统日期", "DATE"),
    "currentDateTime": ("系统日期时间", "DATETIME"),
    "currentTime": ("系统时间", "TIME"),
    "currentLanguage": ("当前语言", "STRING"),
    "secretEnable": ("密级启用", "BOOLEAN"),
}


def build_sysvar_token(name: str) -> str:
    """构造**格式 A**（单 token 对象）—— 真实业务字段用这个。"""
    if name not in SYSTEM_VARIABLE_NAMES:
        raise ValueError(f"未知系统变量 {name!r}，可用：{sorted(SYSTEM_VARIABLE_NAMES)}")
    desc, dtype = SYSTEM_VARIABLE_NAMES[name]
    return json.dumps({"type": "SYSTEM_VARIABLE", "value": name,
                       "desc": desc, "dataType": dtype},
                      ensure_ascii=False, separators=(",", ":"))


def build_sysvar_expression_dto(name: str, *, result_type: str = "ENTITY",
                                uid: str | None = None) -> str:
    """构造**格式 B**（ExpressionSaveDto）—— 字段集用这个（实测落库成功）。"""
    import uuid as _uuid
    if name not in SYSTEM_VARIABLE_NAMES:
        raise ValueError(f"未知系统变量 {name!r}，可用：{sorted(SYSTEM_VARIABLE_NAMES)}")
    desc, _ = SYSTEM_VARIABLE_NAMES[name]
    return json.dumps({
        "resultTypeInfo": result_type,
        "schemas": [],
        "tokens": [{"value": f"system.{name}", "desc": desc, "type": "SYSTEM",
                    "uid": uid or str(_uuid.uuid4())}],
        "isMultiSelect": False,
        "terminalSupportType": "BACKEND",
    }, ensure_ascii=False, separators=(",", ":"))


def validate_sysvar(raw) -> list[str]:
    """校验 defaultValueSystemVariable：非空时必须是合法 JSON 对象。

    ★ 纯文本（如 "currentUser"）会让前端 JSON.parse 崩溃 → 整个字段集面板白屏。
    """
    if raw in (None, ""):
        return []
    if not isinstance(raw, str):
        return ["defaultValueSystemVariable 必须是字符串（内部为 JSON 文本）"]
    try:
        d = json.loads(raw)
    except Exception as exc:
        return [f"defaultValueSystemVariable 不是合法 JSON（{exc}）—— "
                "前端 JSON.parse 会崩，整个字段集面板白屏。"
                "用 build_sysvar_token / build_sysvar_expression_dto 构造"]
    if not isinstance(d, dict):
        return ["defaultValueSystemVariable 必须是 JSON 对象"]
    # 格式 A
    if d.get("type") == "SYSTEM_VARIABLE":
        for k in ("value", "desc", "dataType"):
            if k not in d:
                return [f"格式 A 缺 {k}"]
        return []
    # 格式 B
    if "tokens" in d or "resultTypeInfo" in d:
        if not isinstance(d.get("tokens"), list):
            return ["格式 B 的 tokens 必须是数组"]
        for i, t in enumerate(d["tokens"]):
            if not isinstance(t, dict) or "type" not in t or "value" not in t:
                return [f"格式 B 第 {i} 个 token 缺 type/value"]
        return []
    return ["defaultValueSystemVariable 既不是格式 A（type=SYSTEM_VARIABLE）"
            "也不是格式 B（含 tokens / resultTypeInfo）"]
