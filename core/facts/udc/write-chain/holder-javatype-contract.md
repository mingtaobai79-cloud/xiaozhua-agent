# 微流程 holder 的 dataType ↔ javaType 契约（权威表 + 适用边界）

> 领域：微流程 DATA_MAPPING → holder（`targetField` / `value.reference`）的 Java 类型
> 状态：**判据 VERIFIED_STATIC_BYTECODE**；**适用范围 LIVE 实测**（第二十八轮更正）
> 代码：`components/udc/data_type_java_type.py`；护栏 `tests/udc/test_data_type_java_type.py`（21 项）
> 关联：`components/udc/microflow_parse_errors.py`（`DTO_ATTR_CHANGE` = code 17 → 04004）

## 0. 结论（8 行）

| dataType | javaType | 依据 |
|---|---|---|
| STRING / MULTILINESTRING / TIME / ATTACHMENT | `java.lang.String` | 字节码（AbstractStringDataType / AbstractFileDataType） |
| INTEGER | `java.lang.Integer` | 字节码 |
| BOOLEAN | `java.lang.Boolean` | 字节码 |
| BIGINTEGER | **`java.lang.Long`** | 字节码（反直觉） |
| DECIMAL / CURRENCY | `java.math.BigDecimal` | 字节码 |
| DATE / DATETIME | `java.util.Date` | 字节码 |
| CTPENUM / ENTITY | 单选 → `java.lang.Long`；**多选 → `java.lang.String`** | 字节码 `DtoAttributeUtil.MULTI_SELECT_DATA_TYPES` + LIVE 条件载体 |
| ENUM | **`com.seeyon.{app}.enums.{Code}`**（应用自产枚举全名） | 字节码 `case ENUM` 不走 UdcDataTypeUtil |

## 1. 判据的**适用边界**（本轮最重要的更正）

判据的权威域**只有** DATA_MAPPING holder：

```
nodes[..].mappingRule.mappingRows[].targetField
nodes[..].mappingRule.mappingRows[].value.reference
```

只有这两处的不配对会触发 `DataMappingActivity.checkTargetFieldList:369` 与
`checkReferenceValue → simpleCheckReference → checkNotSameType`，各报一条 `DTO_ATTR_CHANGE` → 04004。

**不属于权威域的相似载体**（形状相近但属页面/控件层表示）：
`leftParam`、`selectParam`、`attrs[].value/selectParam`、`attrs[].attrType`、`output`、`value/selectParam`。

⇒ 若对整篇 `data_schema` 做「见 `path` 键即校验」的宽口径遍历，会把上述载体一并收进来
→ **非 holder 残差**。全库实测 **54 条残差，54/54 全部位于 holder 之外、0 条在 holder 内**。
⇒ **调用方必须自己保证传入 holder**；模块用 `is_authoritative_holder()` 供调用方自检。

## 2. 真 holder 从不携带 `multiSelect`（⇒ CTPENUM/ENTITY 必须 fail-open）

| 口径 | holder 数 | 携带 multiSelect |
|---|---|---|
| RELEASE（state=20） | **508** | **0** |
| 全库（4734 条 microflow） | **514** | **0** |

⇒ 对 CTPENUM/ENTITY，**键缺失 = 判据不可判定 = 必须放行**（宁可漏报，不可假阳）。
LIVE 反例锚点：MF `-3950259420485069209` 的 ENTITY holder `xianzhihesuandalei`
键集 = `['dataType','desc','id','javaType','name','path','type']`（无 `multiSelect`），
`javaType=java.lang.String` —— 既非单选权威值也非多选权威值。

## 3. 单/多选切分被 LIVE 确证的位点 = **条件载体**（不是 holder）

RELEASE 口径实测（`leftParam`）：

| dataType | multiSelect | javaType | 例数 |
|---|---|---|---|
| ENTITY | False | `java.lang.Long` | **152** |
| ENTITY | True | `java.lang.String` | **17** |
| CTPENUM | False | `java.lang.Long` | **248** |
| CTPENUM | True | `java.lang.String` | **10** |
| ENUM | （任一） | `com.seeyon.<app>.enums.<Code>` | 多选时 `type=ARRAY` 亦然 |

⇒ 「CTPENUM/ENTITY 恒 Long」「ENUM 恒 String」两条旧结论由此 **LIVE 证伪**。

## 4. 两个 LIVE 口径**不可混用**（登记并更正上一轮失真）

| 口径 | 载体数 | 旧表假阳 | 新表 |
|---|---|---|---|
| 样本：`app=3289082814923688017 AND state=20 LIMIT 500` | **7666** | **106** | **0** |
| 全库：4734 条 microflow | **28855** | **296** | **54**（全在 holder 外） |
| **真 holder**（mappingRows） | **514**（RELEASE 508） | **2**（ENTITY+String） | **0** |

上一轮把 7666 / 106 / 0 写成「全库」——**实为该 500 行样本口径**。全库同口径为
28855 / 296 / 54，54 条已逐条定位到 `selectParam`(43) 与 `params`(11)，无一位于 holder。
样本口径旧表 106 假阳分布：ENTITY+String 125、CTPENUM+String 49、ENUM+枚举全名 30+17、
STRING+DTO 全名 15、DECIMAL+None 8 …（同一 holder 可在多位点被计数）。

## 5. 字节码证据源（可复核）

- `udc-common-5.3.517.jar` sha256 `30085724949703b1c2f96a37e72813a6ed9e7b752ebc206c7a47d26afceb30d7`
  - `com/seeyon/udc/common/datatype/instance/*DataType`（只有 8 类覆写 `getJavaType()`）
  - `AbstractStringDataType#getJavaType`、`AbstractDateDataType#getJavaType`、`AbstractFileDataType#getJavaType`
  - `TimeDataType extends AbstractStringDataType`（javap 类头逐字）⇒ TIME = String
- `udc-biz-5.3.517.jar`
  - `com/seeyon/udc/common/utils/ExprDataTypeTransferUtil`（静态 Map，含 TIME→String）
  - `com/seeyon/udc/entity/util/DtoAttributeUtil`（`MULTI_SELECT_DATA_TYPES`；`case ENUM` 分支）
- `boot-core-5.3.358.jar`：`com/seeyon/boot/enums/DataType`（TIME(10)/ENTITY(11)/CTPENUM(18)…）

## 6. 未取到 LIVE 样本项（判据已字节码证实，样本 0 例；禁止据此反推）

- **TIME**：三源字节码一致 ⇒ `java.lang.String`；全库 4734 条 microflow 内 `dataType="TIME"` 载体 **0 例**
  （LIKE 命中 0）⇒ LIVE 样本维度仍未验证（**判据本身为 VERIFIED**，登记于 `LIVE_SAMPLE_MISSING`）。
- **CURRENCY**：本轮已取到 LIVE 样本 **21 例**，全 `java.math.BigDecimal` ⇒ 已移出 `LIVE_SAMPLE_MISSING`。
- OBJECT/ARRAY/MAP/SORTORDER/METADATA 不是建表字段类型，javaType 由 type 层决定
  （ARRAY→`List<%s>`、MAP→`Map<K,V>`，见 `MicroFlowAutoCodeJavaTypeResolver#getFullJavaType`），不在本表范围。
