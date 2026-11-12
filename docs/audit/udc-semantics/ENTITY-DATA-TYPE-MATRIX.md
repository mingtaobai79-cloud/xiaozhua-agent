# 实体属性 dataType 约束 —— 权威矩阵（前端设计器 + 后端双源对账）

**版本**：boot-starter-datatype 5.3.358 / boot-starter-condition 5.3.318 / udc-common 5.3.517 / udc-biz 5.3.517 / 前端设计器 bundle（src_redux_store_ts module-65420 + module-31623）

> 本文解决"数据约束不对"的根因：`dataType` 的权威值域有三层，各层范围不同，混淆即出错。

## 三层权威源（各管各的事，不可混用）

| 层 | 来源 | 数量 | 用途 |
| --- | --- | --- | --- |
| A 设计器全量注册表 | 前端 `module-65420` `pe`（JavaType→dataType） | **34** | 设计时可选的全部类型（含 LONG/FLOAT/DOUBLE/OBJECT/DTO/METADATA 等非建表类型） |
| B 设计器字段模板 | 前端 `module-31623` `Uz` | **14** | 实体字段设计器实际带默认值的类型 |
| C 运行时 UdcDataType | udc-common `datatype/instance/*`（DataTypeManager 扫描注册） | **22** | 后端运行时真正识别的类型 |
| D boot-starter-datatype | `instance/*`（15 实例） | **15** | 基础类型子集，caption 走 i18n key `com.seeyon.boot.enums.DataType.<NAME>` |

**写约束规则时取交集原则**：实体字段用 B（14）∪ C（22）= C 为准（运行时必须认识）；前端 UI 展示选项用 A；提示文案用 D 的 i18n key。

## A 层全量表（34 种，前端 `pe`）

```
STRING INTEGER FLOAT DOUBLE LONG BIGINTEGER DECIMAL BOOLEAN
DATE DATETIME TIME ENTITY OBJECT DTO CTPENUM ENUM ATTACHMENT
CURRENCY MULTILINESTRING IMAGE ARRAY SELECTPEOPLE Serial CONTENT
OPINIONHANDLER MAP ORGGROUP ASSOCIATEDOCUMENT METADATA DATA_SOURCE
DOCUMENTNUMBER OPINION ELEMENT PERSONSELECTOR
```

## B 层：设计器默认模板（`Uz`，14 种）→ 落入 `DATA_TYPE_DEFAULT_TEMPLATE`

| dataType | 关键默认值 |
| --- | --- |
| STRING | maxLength 50, notNull false, uniqueness false, searchable false, defaultValue "", encryption "NOT_ENCRYPTION", desensitization "None", calculate "NORMAL", sourceType "ENTITY" |
| MULTILINESTRING | maxLength 300 |
| INTEGER/BIGINTEGER | 无 decimalDigits；min/max "" |
| DECIMAL/CURRENCY | decimalDigits 2 |
| DATE/TIME/DATETIME | min/max ""（日期类无长度） |
| BOOLEAN | defaultValue "true" |
| ENUM/CTPENUM/ENTITY | relationType "Many2OneAssociation"，含 relationApp/relationEntityName/relationEntity（CTPENUM 多 relationCode） |
| ATTACHMENT | multiSelect true, searchable false |

通用默认（所有模板）：`defaultValueIsChange true`、`calculate "NORMAL"`、`sourceType "ENTITY"`、`columnName ""`。

## 值域（`WB`，权威 min/max）→ 落入 `DATA_TYPE_VALUE_RANGE`

| dataType | min | max |
| --- | --- | --- |
| STRING（长度） | 0 | 4000 |
| MULTILINESTRING（长度） | 0 | 10000 |
| INTEGER | -2147483648 | 2147483647 |
| BIGINTEGER/DECIMAL/CURRENCY | -9007199254740991 | 9007199254740991 |

## 渲染控件（`py`，PC/MOBILE）→ 落入 `DATA_TYPE_WIDGET`

STRING→Input/Input；MULTILINESTRING→TextArea；INTEGER/DECIMAL→InputNumber；BIGINTEGER→Input；
CURRENCY→Currency；DATE→DatePicker（移动 DateTimePicker）；TIME→TimePicker；DATETIME→DatePicker（移动 DateTimePicker）；
BOOLEAN→Switch；ENUM/CTPENUM→TreeSelect（移动 CascaderSelect）；ATTACHMENT→Attachment（移动 Upload）；
ENTITY/Serial→UdcReference / Input；CONTENT→UiBusinessContent；DOCUMENTNUMBER→UiBusinessEdocMark；
OPINION→UiBusinessEdocOpinionBox；PERSONSELECTOR→UiBusinessSelectPeople。

## 中文名 / 日期格式（`d4` / `fU`）

ENUM 选项集 / CTPENUM 枚举 / ENTITY 实体 / ATTACHMENT 附件 / CURRENCY 货币 / Serial 流水号 / CONTENT 正文 /
OPINION 意见 / DOCUMENTNUMBER 文号 / SORTORDER 排序号 / PERSONSELECTOR 选人规则 / SELECTPEOPLE 发布范围 等。
日期格式：DATE `YYYY-MM-DD`、TIME `HH:mm:ss`、DATETIME `YYYY-MM-DD HH:mm:ss`。

## 设计器可新建类型（`mG`，9 种白名单）→ `ENTITY_CREATABLE_DATA_TYPES`

STRING / INTEGER / BIGINTEGER / DECIMAL / CURRENCY / DATE / TIME / DATETIME / BOOLEAN
（其余类型只能通过"引用型字段"或高级模式引入——引用型需 relationType，默认 `Many2OneAssociation`）

## 条件域对账（boot-starter-condition 5.3.318）

- `OperatorEnum` 22 个（与 5.308 一致）：EQ/NEQ/GT/LT/GE/LE/RLIKE/LLIKE/LIKE/NOTLIKE/IN/NOTIN/NULL/NOTNULL/ZERO/NOTZERO/BETWEEN/NOTBETWEEN/INCLUDEALL/INCLUDEANY/NOTINCLUDEALL/NOTINCLUDEANY
- `ParamTypeEnum`：CONSTANT / CONTEXT_VARIABLE / SYSTEM_VARIABLE / EXPRESSION / ENTITY_FIELD（**5.3.318 实测 5 个**，原文档 2 个不完整）
- `NullRightValueConditionEnum`：IGNORE_IF_ANY_NULL / USE_DEFAULT_VALUE / INVALID_IF_ANY_NULL
- `ConditionService.check` 契约（反编译）：leftParam/operator/rightParams 不可 null；GROUP 内从第 2 个条件起 logicalOperator 不可空；type 只能 GROUP/CONDITION
- dataType→操作符矩阵已按 5.3.318 修正：BOOLEAN 支持 ZERO/NOTZERO；BIGINTEGER 补 NULL/NOTNULL；INTEGER/DATETIME 补 ZERO/NOTZERO

## 落地位置（可执行约束）

- `components/udc/entity_constraints.py`：`ENTITY_DATA_TYPES`(34) / `ENTITY_CREATABLE_DATA_TYPES`(9) / `ENTITY_FIELD_DATA_TYPES`(14) / `DATA_TYPE_LABELS` / `DATA_TYPE_DATE_FORMAT` / `DATA_TYPE_VALUE_RANGE` / `DATA_TYPE_WIDGET` / `DATA_TYPE_DEFAULT_TEMPLATE` / `DATA_TYPE_ALLOWED_ATTRS` / `validate_attribute_datatype()`
- `components/udc/microflow_constraints.py`：`CONDITION_REQUIRED_PARTS` / `CONDITION_GROUP_LOGICAL_OPERATOR_REQUIRED_FROM_INDEX`（ConditionService 契约）
- `components/udc/microflow_model.py`：`CONDITION_TYPE_OPERATORS`（5.3.318 修正后）
- 测试：`tests/udc/test_entity_constraints.py`（9）、`tests/udc/test_microflow_condition_constraints.py`、`tests/udc/test_microflow_constraints.py`
