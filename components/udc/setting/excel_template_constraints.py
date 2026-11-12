"""设置域 · 导入导出模板（Excel Template）实现与校验。

## 接口形态：REST，不是 GraphQL

```
POST /service/udc/excel/search            列表（PageRequest）
POST /service/udc/excel/create-template   新建
POST /service/udc/excel/update-template   更新
POST /service/udc/excel/select-by-id      详情
POST /service/udc/excel/delete            删除（@MultiRequestBody Long id）
POST /service/udc/excel/get-entity-metadata  实体元数据（选实体后拉字段）
```

⚠ 路径前缀是 `/service/udc/excel/*`，不是 `/service/excel/*`
（后者报 `server_404 excel 服务不存在`）。

## PageRequest 形态（反编译 boot-core 5.3.345）

```
PageRequest extends ListRequest {
    PageInfo pageInfo;              // 分页
}
ListRequest {
    Map<String,Object> params;      // 查询条件
    Sort sort;
}
PageInfo {
    int pageNumber = 1;
    int pageSize = 20;
    ...
}
```

正确 body：

```json
{ "pageInfo": {"pageNumber":1,"pageSize":10}, "params": {"appId":"..."} }
```

⚠ 写成 `{"page":1,"size":10,"params":{...}}` 会报 `BOOT_3000 message:null`。

## ExcelExportTemplateDto（反编译 boot-starter-excel 5.3.318）

```java
Long    id
String  name                 // @NotNull @Size(max=20)
String  appId
Long    appGuid = -1L
String  appName
String  mainFullName         // 实体全类名
Long    createUserId = -1L
String  signatureCode = ""   // md5 签名
String  metadataContent = ""  // ★ 列定义（JSON 字符串）
String  excelHeadInfo = ""    // ★ 表头信息（JSON 字符串）
Boolean isCustom = true
Boolean isImport = true      // true=导入模板 false=导出模板
Boolean isDefault = false
Boolean deleteFlag = false
List<List<ExcelColumnDto>> columnList;   // @Min(1) —— 但 search 读回来是 null
Long    belongGroupId = -1L
Long    originalId
List<String> importReminders
String  authInfo
```

⚠ **`columnList` 读回来是 null**。实际列定义存在 `metadataContent` /
`excelHeadInfo` 里（JSON 字符串，二维数组：外层 sheet、内层列）。
提交时两个都要给，且内容一致（实测平台会各自校验）。

## ExcelColumnDto（反编译，40+ 字段，关键如下）

```java
String  attributeFullName           // ★ 属性全名 <实体全类名>.<字段名>
String  parentEnumAttributeFullName
String  entityType                  // MASTER_ENTITY / SUB_ENTITY
List<List<String>> levelPath        // 层级路径（实体→子实体链）
String  type                        // java.lang.String 等
Boolean dataI18n
String  dataType                    // STRING / INTEGER / ...
String  jsr303
Integer curColIndex
CtpEnumType ctpEnumType
Long    rootEnumId
Integer enumLevel
List<String> enums
String  enumClass
List<String> ctpEnums
Map<String,Object> ctpEnumMap
Boolean unique
Boolean matchQuery
Boolean parentUnique
Boolean isAssUniqueField
Boolean notBlankOrNotNull
Boolean parentNotBlankOrNotNull = true
Boolean multiSelect
Boolean parentAssMultiSelect
String  relation
String  relationApp
String  relationEntity
String  columnType                  // varchar(50) 等物理类型
String  displayName                 // ★ 表头显示名
Boolean isHidden
SafetyDto safetyDto                 // {encryption, mask, auditLog, permission}
Map     relationMap
List<String> relationValueList
Map     enumCodeAndNameMap
MaskableDto maskable
String  cellValue
```

## 关键要点（做模板必须守）

1. **`attributeFullName` 是唯一锚点**：`<实体全类名>.<字段名>`，平台靠它定位字段。
2. **`displayName` 是 Excel 表头**，默认取 `caption`，可自定义（用户说的"配置名称"）。
3. **`metadataContent` 与 `excelHeadInfo` 都是 `[[列,...],...]` 二维 JSON 字符串**，
   每个 sheet 一组。
4. **`isImport`** 区分导入/导出模板：`true`=导入，`false`=导出。
5. `columnType` 是物理列类型（`varchar(50)`），可 null。
6. `safetyDto` 建议带上（`encryption: NOT_ENCRYPTION`、`mask: "None"`）。
"""
from __future__ import annotations

import json
from typing import Any

# 实体类型
ENTITY_MASTER = "MASTER_ENTITY"
ENTITY_SUB = "SUB_ENTITY"

# 加密方式（SafetyDto.encryption）
ENCRYPTION_NONE = "NOT_ENCRYPTION"

# java type → dataType 映射（从真实样本归纳）
JAVA_TYPE_TO_DATA_TYPE = {
    "java.lang.String": "STRING",
    "java.lang.Integer": "INTEGER",
    "java.lang.Long": "BIGINTEGER",
    "java.math.BigDecimal": "DECIMAL",
    "java.util.Date": "DATE",
    "java.lang.Boolean": "BOOLEAN",
}


def build_safety_dto(*, encryption: str = ENCRYPTION_NONE,
                     mask: str = "None", audit_log: bool = False) -> dict[str, Any]:
    return {"validate": True, "encryption": encryption, "mask": mask,
            "auditLog": bool(audit_log), "permission": False}


def build_column(attribute_full_name: str, display_name: str, *,
                 data_type: str = "STRING", java_type: str = "java.lang.String",
                 entity_type: str = ENTITY_MASTER,
                 level_path: list[list[str]] | None = None,
                 column_type: str | None = None,
                 unique: bool = False, match_query: bool = False,
                 not_blank: bool = False, multi_select: bool = False,
                 relation: str = "NONE", relation_app: str | None = None,
                 relation_entity: str | None = None,
                 cur_col_index: int | None = None,
                 root_enum_id: str | None = None, enum_level: int | None = None,
                 ctp_enums: list[str] | None = None,
                 safety: dict[str, Any] | None = None) -> dict[str, Any]:
    """构造一个模板列（ExcelColumnDto）。

    `attribute_full_name` 是唯一锚点，形如
    `com.seeyon.<app>.domain.entity.<Entity>.<field>`。
    `display_name` 是 Excel 表头。
    """
    return {
        "validate": True,
        "attributeFullName": attribute_full_name,
        "parentEnumAttributeFullName": None,
        "entityType": entity_type,
        "levelPath": level_path or [],
        "relationPath": None,
        "type": java_type,
        "dataI18n": False,
        "dataType": data_type,
        "jsr303": None,
        "curColIndex": cur_col_index,
        "ctpEnumType": None,
        "rootEnumId": root_enum_id,
        "enumLevel": enum_level,
        "enums": None,
        "enumClass": None,
        "ctpEnums": ctp_enums,
        "ctpEnumMap": {},
        "unique": bool(unique),
        "matchQuery": bool(match_query),
        "parentUnique": False,
        "isAssUniqueField": False,
        "notBlankOrNotNull": bool(not_blank),
        "parentNotBlankOrNotNull": True,
        "multiSelect": bool(multi_select),
        "parentAssMultiSelect": False,
        "relation": relation,
        "relationApp": relation_app,
        "relationEntity": relation_entity,
        "columnType": column_type,
        "displayName": display_name,
        "isHidden": False,
        "safetyDto": safety or build_safety_dto(),
        "relationMap": {},
        "relationValueList": [],
        "enumCodeAndNameMap": {},
        "maskable": None,
        "cellValue": None,
    }


def build_template_body(app_id: str | int, app_guid: str | int, *,
                        name: str, main_full_name: str,
                        sheets: list[list[dict[str, Any]]],
                        app_name: str = "",
                        is_import: bool = True,
                        is_custom: bool = True,
                        signature_code: str = "",
                        create_user_id: str = "-1",
                        belong_group_id: str = "-1") -> dict[str, Any]:
    """构造模板 body（ExcelExportTemplateDto）。

    `sheets` 是二维：外层每个 sheet，内层该 sheet 的列。

    `metadataContent` / `excelHeadInfo` 都写成 `json.dumps(sheets)`。
    （读回来时这两列存的是同一份二维数组，只是平台内部校验不同）
    """
    payload = json.dumps(sheets, ensure_ascii=False)
    return {
        "name": name,
        "appId": str(app_id),
        "appGuid": int(app_guid),
        "appName": app_name,
        "mainFullName": main_full_name,
        "createUserId": str(create_user_id),
        "signatureCode": signature_code,
        "metadataContent": payload,
        "excelHeadInfo": payload,
        "isCustom": bool(is_custom),
        "isImport": bool(is_import),
        "isDefault": False,
        "deleteFlag": False,
        "belongGroupId": str(belong_group_id),
    }


def validate_template_body(body: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["模板 body 必须是对象"]

    name = str(body.get("name") or "")
    if not name:
        errs.append("模板缺 name（DTO @NotNull）")
    elif len(name) > 20:
        errs.append(f"模板 name 超长 {len(name)} > 20（DTO @Size(max=20)）")

    for k in ("appId", "mainFullName"):
        if not body.get(k):
            errs.append(f"模板缺 {k}")
    if not str(body.get("mainFullName") or "").startswith("com.seeyon."):
        errs.append("mainFullName 应是实体全类名（com.seeyon.<app>.domain.entity.Xxx）")

    for k in ("metadataContent", "excelHeadInfo"):
        raw = body.get(k)
        if not raw:
            errs.append(f"模板缺 {k}（列定义 JSON 字符串）")
            continue
        if not isinstance(raw, str):
            errs.append(f"{k} 必须是 JSON 字符串，不是对象")
            continue
        try:
            parsed = json.loads(raw)
        except Exception as exc:
            errs.append(f"{k} 不是合法 JSON: {exc}")
            continue
        if not isinstance(parsed, list) or not parsed:
            errs.append(f"{k} 必须是非空二维数组 [[列,...],...]")
            continue
        if not isinstance(parsed[0], list):
            errs.append(f"{k} 内层必须是数组（每个 sheet 一组列）")
            continue
        for i, col in enumerate(parsed[0], 1):
            if not isinstance(col, dict):
                errs.append(f"{k} 第 {i} 列不是对象")
                continue
            if not col.get("attributeFullName"):
                errs.append(f"{k} 第 {i} 列缺 attributeFullName（唯一锚点）")
            if not col.get("displayName"):
                errs.append(f"{k} 第 {i} 列缺 displayName（Excel 表头）")
    return errs


def parse_columns(template: dict[str, Any]) -> list[list[dict[str, Any]]]:
    """从接口返回的模板里解析列定义（columnList 常为 null，回落到 metadataContent）。"""
    cl = template.get("columnList")
    if isinstance(cl, list) and cl:
        return cl
    raw = template.get("metadataContent")
    if isinstance(raw, str) and raw.strip():
        try:
            v = json.loads(raw)
            if isinstance(v, list):
                return v
        except Exception:
            pass
    return []


__all__ = [
    "ENTITY_MASTER", "ENTITY_SUB", "ENCRYPTION_NONE", "JAVA_TYPE_TO_DATA_TYPE",
    "build_safety_dto", "build_column", "build_template_body",
    "validate_template_body", "parse_columns",
]
