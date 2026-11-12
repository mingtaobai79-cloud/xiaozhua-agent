"""components/construction/setting_artifacts.py — 设置域 7 子域 + 应用菜单 的 body 构造器。

口径：只把参数拼成平台认的 body，不联网、不落库、不校验服务端语义。

契约来源（逐函数注明）：
  docs/operation-contracts/udc/setting/{option-set,attribute-set,scalability,
                                        qrcode,serial,parameter,excel-template}-contracts.md
事实来源：
  core/facts/udc/setting/{option-set,attribute-set,scalability,qrcode,
                          serial,parameter,excel-template}/
  core/facts/udc/application/
  docs/audit/udc-semantics/S7-WRITE-CHAIN-LIVE.md（菜单 LIVE 实证）

两条通用前置（core/facts/udc/setting/precondition-appguid.md）：
  ★ appGuid ≠ appId。9 个子域的 udc*Post 都要 appGuid，缺则 BOOT_1001 或静默落 app_guid=-1
  ★ 取法：udcApplicationDetailGet(path:{id: appId}) → data.content.guid

四条跨子域的坑（都写在对应函数 docstring 里，别在调用方重复踩）：
  ① 选项集与枚举是两套表（udc_enum* vs ctp_enum*），id 不互通
  ② 字段集父子两套协议：父 REST 驼峰 udc/attributeSet，子 GraphQL udcEntityAttributePost
  ③ 扩展实体删除只能走 GraphQL udcScalabilityDeletePost，REST delete 六种形态全 BOOT_3000
  ④ 导入导出模板 isCustom 必须 false，否则 search 列表看不到
"""
from __future__ import annotations

import json
from typing import Any

# ---------------------------------------------------------------- 选项集（udc_enum*）
# 契约：option-set-contracts.md；事实：core/facts/udc/setting/option-set/create.md
# ★ 与「枚举」ctp_enum* 是完全独立两套表，id 不互通；混用页面显示 _<appName>_<id> 异常串
# ★ 编码 name 必须首字母大写（UDC_ENUM_0001）；item 三槽位 name/caption/code 缺一不可


def build_option_set_category_body(app_id: Any, app_guid: str, name: str, caption: str,
                                   *, order_no: int = 1, parent_id: str = "0",
                                   description: str = "") -> dict[str, Any]:
    """选项集分组 body → udcUdcEnumCategoryPost → udc_enum_category。

    ★ name 必须首字母大写，否则 UDC_ENUM_0001。
    """
    return {"appId": str(app_id), "appGuid": app_guid,
            "name": name, "caption": caption,
            "orderNo": order_no, "parentId": parent_id,
            "description": description}


def build_option_set_body(app_id: Any, app_guid: str, name: str, caption: str,
                          category_id: Any, *, order_no: int = 10) -> dict[str, Any]:
    """选项集 body → udcUdcEnumPost → udc_enum。

    category_id 必须是 build_option_set_category_body 返回的 id。
    """
    return {"appId": str(app_id), "appGuid": app_guid,
            "name": name, "caption": caption,
            "categoryId": str(category_id), "orderNo": order_no}


def build_option_set_item_body(app_id: Any, app_guid: str, enum_id: Any,
                               name: str, caption: str, code: int,
                               *, order_no: int = 1,
                               enable: bool = True) -> dict[str, Any]:
    """选项集项 body → udcUdcEnumItemPost → udc_enum_item。

    ★ 三槽位缺一不可：name(英文) / caption(中文) / code(整数)
    """
    return {"appId": str(app_id), "appGuid": app_guid,
            "enumId": str(enum_id),
            "name": name, "caption": caption, "code": code,
            "orderNo": order_no, "enable": enable}


# ---------------------------------------------------------------- 字段集（父子两套协议）
# 契约：attribute-set-contracts.md；事实：core/facts/udc/setting/attribute-set/create.md
# ★ 父 REST 驼峰 /service/udc/attributeSet；子 GraphQL udcEntityAttributePost
# ★ REST update 带 attributes 会被静默忽略（4 种变体全试过）—— 字段必须走子接口


def build_attribute_set_body(app_id: Any, name: str, caption: str, *,
                             description: str = "", source_type: str = "APP",
                             order_no: int = 1) -> dict[str, Any]:
    """字段集 body → REST POST /service/udc/attributeSet。

    name ≤30 字，caption ≤50 字；source_type ∈ APP / UDC / ISV。
    attributes 恒为空列表——字段走 build_attribute_set_field_body 单独提交。
    """
    return {"appId": str(app_id), "name": name, "caption": caption,
            "description": description, "sourceType": source_type,
            "orderNo": order_no, "attributes": []}


def build_attribute_set_field_body(app_id: Any, set_id: Any, name: str, caption: str,
                                   *, data_type: str = "STRING", not_null: bool = False,
                                   min_length: int = 0, max_length: int = 50,
                                   decimal_digits: int = 0, multi_select: bool = False,
                                   searchable: bool = False, uniqueness: bool = False,
                                   attribute_group_id: int = 0, order_no: int = 1,
                                   column_name: str = "", widget_config: str = "",
                                   encryption: str = "NOT_ENCRYPTION",
                                   desensitization: str = "None") -> dict[str, Any]:
    """字段集字段 body → GraphQL udcEntityAttributePost。

    ★ entityId / sourceId 都等于字段集 id；sourceType 恒 ATTRIBUTESET
    ★ 字符串键 "0" 必须带（平台 DTO 里是 Map 形态）
    ★ widgetConfig 是 JSON 字符串，不是对象
    data_type ∈ STRING / INTEGER / BIGINTEGER / DECIMAL / DATE / DATETIME / BOOLEAN
    """
    wc = widget_config or json.dumps(
        {"pc": "Input", "mobile": "Input", "list": True,
         "detail": True, "quickSearch": True}, ensure_ascii=False)
    return {"0": "1",
            "appId": str(app_id),
            "name": name, "caption": caption,
            "dataType": data_type, "notNull": not_null,
            "searchable": searchable, "uniqueness": uniqueness,
            "defaultValue": "", "minLength": min_length, "maxLength": max_length,
            "decimalDigits": decimal_digits, "multiSelect": multi_select,
            "auditLog": False, "attributeGroup": "",
            "attributeGroupId": attribute_group_id,
            "defaultValueSystemVariable": "",
            "defaultValueExpressionDesignData": "",
            "defaultValueExpressionRuntimeData": "",
            "defaultValueIsChange": True, "defaultValueCaption": "",
            "calculate": "NORMAL",
            "expressionDesignData": "", "expressionRuntimeData": "",
            "sourceType": "ATTRIBUTESET",
            "entityId": str(set_id), "sourceId": str(set_id),
            "description": "",
            "orderNo": order_no,
            "columnName": column_name or name,
            "encryption": encryption, "desensitization": desensitization,
            "serialNumberGuid": 0, "parentEnumAttributeId": 0,
            "useSnapshot": False,
            "widgetConfig": wc}


# ---------------------------------------------------------------- 扩展实体
# 契约：scalability-contracts.md；事实：core/facts/udc/setting/scalability/create.md
# ★ delete 只能走 GraphQL udcScalabilityDeletePost（body {appId,id}）；
#   REST /udc/scalability-option/delete 六种 body 形态全报 BOOT_3000 message:null
# ★ data-type 18 种全 validate=true，实测 17 种可写，仅 CTPENUM 被拒（级联枚举不允许）
# ★ prefix ≤20，count ≤50（DTO）/ ≤20（UI）


def build_scalability_option_body(app_id: Any, name: str, caption: str) -> dict[str, Any]:
    """扩展实体方案 body → REST POST /service/udc/scalability-option。"""
    return {"appId": str(app_id), "name": name, "caption": caption,
            "scalabilityDtoList": [], "attributeDtoList": []}


def build_scalability_field_body(app_id: Any, option_id: Any, prefix: str, caption: str,
                                 *, count: int = 5, data_type: str = "STRING",
                                 data_type_properties: Any = "") -> dict[str, Any]:
    """扩展实体字段 body → GraphQL udcScalabilityPost。

    ★ prefix ≤20；count ≤50（DTO）/ ≤20（UI）
    ★ data_type 17 种可写，CTPENUM 被拒（BOOT_1000 扩展字段不允许选择级联枚举）
    ★ data_type_properties 是 JSON 字符串（如 {"minLength":"0","maxLength":50}）
    ★ **不能是空字符串** —— 实测空串一律 BOOT_3000 且 message 为 null（最没线索的错），
      而 "{}" 对 STRING/LONG/DATE/DOUBLE 全部通过。所以缺省填空对象，不填 ""。
    """
    props = data_type_properties
    if isinstance(props, dict):
        props = json.dumps(props, ensure_ascii=False)
    if props is None or (isinstance(props, str) and not props.strip()):
        props = "{}"
    return {"id": 0, "appId": str(app_id), "optionId": str(option_id),
            "prefix": prefix, "caption": caption, "count": count,
            "dataType": data_type, "dataTypeProperties": props}


# ---------------------------------------------------------------- 二维码 / 条码 / 链接码
# 契约：qrcode-contracts.md；事实：core/facts/udc/setting/qrcode/create.md
# ★ 走 REST /service/udc/qrcode-rule/*（非 GraphQL，实现在 boot-starter-qrcode）
# ★ type/linkType 传字符串枚举名，DB 存 ordinal
# ★ 链接码 pcPagePath = udc_page_info.page_url（页面候选按实体过滤，禁止自编 URL）
# ★ search 的 sort 必须 null


def build_qrcode_body(app_id: Any, app_guid: str, name: str,
                      *, qr_type: str = "FIELDQRCODE", link_type: str = "APP",
                      entity_full_name: str = "",
                      value_field_code: str = "",
                      pc_page_path: str = "",
                      mobile_page_path: str = "") -> dict[str, Any]:
    """二维码/条码/链接码 body → REST POST /service/udc/qrcode-rule/。

    qr_type ∈ FIELDQRCODE(2) / BARCODE(0) / LINKQRCODE(1) / QRCODE(3，VACUUM 不可选)
    ★ 字段码/条码必填 value_field_code（实体属性 name）
    ★ 链接码必填 pc_page_path，且必须来自 udc_page_info.page_url
    """
    body = {"name": name, "type": qr_type, "linkType": link_type,
            "appId": str(app_id), "appGuid": app_guid,
            "entityFullName": entity_full_name}
    if value_field_code:
        body["valueFieldCode"] = value_field_code
    if pc_page_path:
        body["pcPagePath"] = pc_page_path
    if mobile_page_path:
        body["mobilePagePath"] = mobile_page_path
    return body


# ---------------------------------------------------------------- 流水号
# 契约：serial-contracts.md；事实：core/facts/udc/setting/serial/create.md
# ★ 段列表字段名是 serialSectionDtoList（试过 11 个候选全失败；GraphQL 不校验未知字段，
#   所以只能从反编译 SerialSchemeDto 拿）
# ★ 段 DTO 用 size/dateType/show/flow/increase（不是 sectionSize/isXxx）
# ★ 段数 1~12；totalSize = 各段 size 之和
# ★ serialType 用 SerialRuleTypeEnum 枚举语义反转落库，写 ordinal 勿反推


# SerialTypeEnum（javap 自 boot-starter-serialnumber-5.3.603）—— 只有这四个，没有 INCREASE
_SERIAL_TYPE_ENUM = ("CONSTANT", "CONTEXT", "ENTITY", "SERIAL")
_SERIAL_RULE_TYPE_ENUM = ("APP", "BIG", "SMALL")


def build_serial_section(*, size: int, section_type: str = "CONSTANT",
                         value: str = "", caption: str = "",
                         fill_type: str = "NONE", cut_type: str = "NONE",
                         fill_char: str = "0", date_type: bool = False,
                         date_pattern: str = "yyyyMMdd", show: bool = True,
                         flow: bool = False, increase: bool = True,
                         section_rank: int = 1, serial_current: int = 1,
                         start_value: int = 1, end_value: int = -1,
                         source_app_name: str = "udc") -> dict[str, Any]:
    """流水号的一个段。

    section_type 取值域来自 javap（SerialTypeEnum）：CONSTANT / CONTEXT / ENTITY / SERIAL。
    ★ 整个方案里必须**恰好一个** SERIAL 段，否则平台报 SERIALNUMBER_1008
      （文案是「流水段有且只能有一段」，实际判的是 SERIAL 段计数 != 1）。
    ★ 自增语义在 `increase`（Boolean）上，不在 section_type 上 —— 没有 INCREASE 这个类型。
    ★ SERIAL 段必填 fillChar / size(>=1) / serialCurrent(len<=size)；
      其他段必填 value（非空且 <=255 字符）。
    """
    if section_type not in _SERIAL_TYPE_ENUM:
        raise ValueError("section_type 必须是 %s 之一，收到 %r"
                         % (" / ".join(_SERIAL_TYPE_ENUM), section_type))
    return {"size": size, "type": section_type, "value": value,
            "caption": caption, "fillType": fill_type, "cutType": cut_type,
            "fillChar": fill_char, "dateType": date_type,
            "datePattern": date_pattern, "show": show, "flow": flow,
            "increase": increase, "sectionRank": section_rank,
            "serialCurrent": serial_current, "startValue": start_value,
            "endValue": end_value, "sourceAppName": source_app_name}


def build_serial_scheme_body(app_id: Any, app_guid: str, code: str, name: str,
                             sections: list[dict[str, Any]],
                             *, contain_flow: bool = True, active: bool = True,
                             reset_rule: str = "NONE", edit_entity: bool = True,
                             serial_type: str = "APP", sort_num: int = 1,
                             org_id: str = "-1", entity_full_name: str = "",
                             source_app_name: str = "udc") -> dict[str, Any]:
    """流水号方案 body → GraphQL udcSerialSchemeCreatePost。

    ★ code 仅字母数字、禁中文、≤50；name ≤200
    ★ sections 段数 1~12；totalSize 自动算（各段 size 之和）
    ★ reset_rule ∈ NONE / YEAR / MONTH / DAY
    """
    if not sections:
        raise ValueError("流水号至少要 1 个段（平台段数 1~12）")
    if len(sections) > 12:
        raise ValueError("流水号段数上限 12，收到 %d" % len(sections))
    if serial_type not in _SERIAL_RULE_TYPE_ENUM:
        raise ValueError("serial_type 必须是 %s 之一，收到 %r"
                         % (" / ".join(_SERIAL_RULE_TYPE_ENUM), serial_type))
    # 平台 checkDto4Create 判的是「SERIAL 段计数 != 1」→ SERIALNUMBER_1008
    n_serial = sum(1 for s in sections if s.get("type") == "SERIAL")
    if n_serial != 1:
        raise ValueError(
            "必须恰好有 1 个 type=SERIAL 的段，当前 %d 个。"
            "平台报 SERIALNUMBER_1008「流水段有且只能有一段」，实际判的就是这个计数。"
            % n_serial)
    return {"appId": str(app_id), "appGuid": app_guid,
            "code": code, "name": name,
            "totalSize": sum(int(s.get("size") or 0) for s in sections),
            "containFlow": contain_flow, "active": active,
            "serialResetRule": reset_rule, "editEntity": edit_entity,
            "serialType": serial_type, "sortNum": sort_num, "orgId": org_id,
            "entityFullName": entity_full_name, "sourceAppName": source_app_name,
            "serialSectionDtoList": sections}


# ---------------------------------------------------------------- 参数
# 契约：parameter-contracts.md；事实：core/facts/udc/setting/parameter/create.md
# ★ 落库 ctp_parameter_definition，app_id 是 varchar 不是 bigint
# ★ operation 名是 Definiton 少一个 i（平台拼写错误）；写 Definition 报 FieldUndefined
# ★ dataTypeProperties 提交时必须是对象，传 JSON 字符串报 BOOT_3002 反序列化失败


def build_parameter_body(app_id: Any, app_guid: str, name: str, caption: str,
                         *, data_type: str = "STRING",
                         data_type_properties: dict | None = None,
                         description: str = "", param_group: str = "",
                         value: str = "", order_no: int = 10,
                         param_type: int = 0) -> dict[str, Any]:
    """应用参数 body → GraphQL udcCtpParameterDefinitonPost（★ 注意拼写）。

    ★ data_type_properties 必须是 dict（对象），传字符串报 BOOT_3002
    """
    return {"appId": str(app_id), "appGuid": app_guid,
            "name": name, "caption": caption, "description": description,
            "dataType": data_type,
            "dataTypeProperties": data_type_properties or {"minLength": 0, "maxLength": 100},
            "paramGroup": param_group, "value": value,
            "orderNo": order_no, "type": param_type}


# ---------------------------------------------------------------- 导入导出模板
# 契约：excel-template-contracts.md；事实：core/facts/udc/setting/excel-template/create.md
# ★ 走 REST /service/udc/excel/*（实现在 boot-starter-excel；/service/excel/* 报 404）
# ★ isCustom 必须 false，否则 search 列表看不到（selectPageByCondition 硬写该列）
# ★ 列唯一锚点 attributeFullName = <实体全类名>.<字段名>；displayName 才是 Excel 表头
# ★ PageRequest 是 {pageInfo, params} 不是 {page,size}


def build_excel_template_column(attribute_full_name: str, display_name: str,
                                data_type: str = "STRING") -> dict[str, Any]:
    """导入导出模板的一列。attribute_full_name = <实体全类名>.<字段名>。"""
    return {"attributeFullName": attribute_full_name,
            "displayName": display_name, "dataType": data_type}


def build_excel_template_body(app_id: Any, app_guid: str, name: str, caption: str,
                              main_full_name: str,
                              columns: list[dict[str, Any]],
                              *, is_import: bool = True,
                              is_custom: bool = False) -> dict[str, Any]:
    """导入导出模板 body → REST POST /service/udc/excel/。

    ★ is_custom 必须 false（否则 search 列表看不到）
    ★ columns 同时写进 sheets[0].columns / metadataContent / excelHeadInfo 三处，
      后两者是 JSON 字符串（平台读这两个，sheets 只给前端回显）
    """
    cols_json = json.dumps(columns, ensure_ascii=False)
    return {"appId": str(app_id), "appGuid": app_guid,
            "name": name, "caption": caption,
            "mainFullName": main_full_name,
            "isImport": is_import, "isCustom": is_custom,
            "sheets": [{"columns": columns}],
            "metadataContent": cols_json,
            "excelHeadInfo": cols_json}


__all__ = [
    "build_option_set_category_body", "build_option_set_body",
    "build_option_set_item_body",
    "build_attribute_set_body", "build_attribute_set_field_body",
    "build_scalability_option_body", "build_scalability_field_body",
    "build_qrcode_body",
    "build_serial_section", "build_serial_scheme_body",
    "build_parameter_body",
    "build_excel_template_column", "build_excel_template_body",
]
