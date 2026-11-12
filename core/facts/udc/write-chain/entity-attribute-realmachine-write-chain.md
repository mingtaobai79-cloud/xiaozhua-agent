# 实体属性真机写链（CDP 取证）—— udcAttributeGroupOperateBatchPost

> 来源：CDP 连真实设计器（`/main/child-frame/udc/app-design/entity?appId=...`）+ 真机点「保存」捕获载荷
> 状态：**真机保存协议已取证 + 计算值缺陷已修正 LIVE PASS**
> 意义：REST 直觉拼的入参（下划线键、calculate 0/1）**全部错**；真机协议才是权威。

## 1. 真机保存协议（唯一权威）

前端不调 `udc/entity/attribute/update`，而是 **GraphQL 批量**：

```
POST /service/udc/graphql?udcAttributeGroupOperateBatchPost
{"query":"mutation graphqlLoader ($params0: udcAttributeGroupOperateBatchPostInputBody) {
   data0: udcAttributeGroupOperateBatchPost(body: $params0) { code data { content } message status } }",
 "variables":{"params0":[ <AttributeGroupDto>, ... ]}}
```

**顶层是属性组数组**，组内含 `attributeDtoList`。保存即提交**全部组 + 全部属性**（整表提交）。

### 组级字段
`appId, caption, entityId, guid, id, orderNo, preset, publishState, virtual, attributeDtoList[], uniqueKey`

### ★ 属性字段全清单（78 个，真机实测键名）

**驼峰**（不是 REST 直觉的下划线）：
```
actionType, appId, attributeFullName, attributeGroup, attributeGroupId, auditLog,
calculate,            ← 枚举字符串："NORMAL" | "COMPUTE"（不是 0/1！）
caption, columnName, createTime, dataFormat, dataI18n, dataType, dataTypeDisplayName,
decimalDigits, defaultValue, defaultValueCaption,
defaultValueExpressionDesignData, defaultValueExpressionRuntimeData, defaultValueIsChange,
defaultValueSystemVariable, description, desensitization, edit,
enableDesensitization, enableEncryption, enableOpenApiEncrypt, enableSensitiveWordCheck,
encryption, entityId, existDto, expressionDesignData, expressionRuntimeData,
guid, hidden, id, inCondition, inDataMapping, index, key, max, maxLength, min, minLength,
multiSelect, name, notNull, orderNo, parentEnumAttributeId, parentKey, pattern, patternMessage,
permission, publishState, relationApp, relationCode, relationCtpEnum, relationEntity,
relationEntityCategory, relationEntityName, relationStarter, relationType, searchable,
serialNumberCode, serialNumberGuid, serialNumberName, sourceId, sourceType, system,
uniqueKey, uniqueness, updateTime, useSnapshot, valueScopeExpression, widgetConfig
```

`actionType` = `"UPDATE"`（改）| `"ADD"`（新增）。

## 2. ★ 真机暴露的两个缺陷（我 REST 拼的）

| 字段 | 我建的（错） | 真机读回 | 问题 |
|---|---|---|---|
| `expText`（STRING） | `calculate=0` + 有表达式 "实验数量 + 1"（INTEGER） | `calculate:"NORMAL"` + expr 在 | **语义矛盾**：有表达式却不是 COMPUTE；且结果 INTEGER ≠ 字段 STRING |
| `expDate`（DATETIME） | `calculate=1` + 表达式 "实验数量 * 2" + `resultTypeInfo=INTEGER` | `calculate:"COMPUTE"` | **类型不匹配**：表达式返回 INTEGER，字段是 DATETIME |

**校验器真话**（保存时服务端返回）：
```json
UDC_ENTITY_100 {"8016904624316689195":{"calculable":["表达式返回值类型不匹配"]}}
```
即 `expressionDesignData.resultTypeInfo` **必须等于字段 `dataType`**。

### 修法（LIVE PASS）
- `expText`：`calculate="COMPUTE"`，表达式 `"小爪计算"`（CONSTANT 字符串），`resultTypeInfo="STRING"` ✅
- `expDate`：`calculate="COMPUTE"`，表达式 `当前时间`（SYSTEM_VARIABLE），`resultTypeInfo="DATETIME"`，`resultTypeFullName="java.util.Date"` ✅
- 结果：`BOOT_0000`，DB 回读 `calculate=1`、`expression_design_data` 类型对齐；真机表格渲染 `"小爪计算"` 正常。

## 3. `calculate` 值域（CFR + 真机双证）

```
NORMAL   = 0   （普通字段）
COMPUTE  = 1   （计算字段 —— 必须有 expressionDesignData 且 resultTypeInfo == dataType）
```
**有表达式就必须 COMPUTE；COMPUTE 就必须 resultTypeInfo 与字段类型一致。**

## 4. `defaultValue` 编码规则（真机实测）

- 字符串字段：**JSON 编码** —— `STRING` 的默认值 `"默认文本"` 存成 `"\"默认文本\""`（含引号）
- 布尔字段：裸 `"false"`
- 数值字段：裸数字字符串
- 另有 `defaultValueCaption`（显示名）、`defaultValueIsChange`、`defaultValueSystemVariable`、`defaultValueExpressionDesignData/RuntimeData`

## 5. `expressionDesignData` 结构（真机）

```jsonc
{
  "expressionTranslation": "实验数量 + 1 ",     // 人读翻译
  "resultTypeInfo": "INTEGER",                 // ★ 必须等于字段 dataType
  "resultTypeFullName": null,                  // 引用类型时给 FQCN
  "terminalType": "BACKEND",
  "isMultiSelect": false,
  "context": [ { "name":"xzhExp950795", "description":"<实体名>", "type":"OBJECT",
                 "selectable":true, "properties":[{ "name":"expNum","description":"实验数量",
                 "type":"INTEGER","uniformityParams":{"paramId":"<attrId>","paramCategory":"Attr",...} }],
                 "uniformityParams":{"paramId":"<entityId>","paramCategory":"Entity",...} } ],
  "tokens": [ {"uid":"<uuid>","type":"VARIABLE","value":"xzhExp950795.expNum","desc":"实验数量"},
              {"uid":"<uuid>","type":"OPERATOR","value":"+","desc":"+"},
              {"uid":"<uuid>","type":"CONSTANT","value":"1","desc":"1"} ],
  "sourceAppName": null,
  "version": "1"
}
```
`expressionRuntimeData` = `{"executableExpr":"<加密前缀>+%28 <expr> +%29+"}`（服务端加密生成，别手写）。

## 6. 前端接口调用约定（bundle 取证）

所有 UDC 接口走 **GraphQL，op 名在 URL**：
```
POST /service/udc/graphql?<opName>
{ "query": "mutation|query <docName> ($body|$paramsN: <opName>InputBody|InputPath) { ... }", "variables": {...} }
```
前端封装 `udcApolloQuery(doc, vars)`。op 目录已提取 **391 个**（见 `frontend_ops.json`）。
批量 op 用 `graphqlLoader` + `$params0..$paramsN` 一次打多个。

## 7. 实体页加载的真实 op（真机捕获）

```
udcEntitySelectAllByAppidAppGet / udcEntityGroupSelectByAppidAppGet / udcEntityGet
udcAttributeGroupEntityGet            ← 组+属性全量（含 attributeDtoList）
udcEntityAttributePresetAttributeCapacityAllAppGet
udcEntitySelectMasterEntityCountAppGet / udcApplicationIsLastVersionAppGet
udcMultiEditLockPost                  ← 编辑锁
udcEntityBatchUpdateEntityGroupIdAndOrdernoPost
udcApplicationFetchLastVersionMetadataPost / udcEntityAssociationEntityAppGet / udcDataTypeDataTypesByAppIdAppGet
```
**保存**：`udcAttributeGroupOperateBatchPost`（实时提取的 GraphQL doc 原文见 `save_payload.json` 同源抓包）。

## 8. 复现

```bash
node cdp_login.js "https://lowcode-test2.example.com/main/child-frame/udc/app-design/entity?appId=<appId>"
node cdp_act.js "-" <点保存脚本> 5000 16000 > cap.txt   # 全量请求+响应
python analyze/…                                        # 解析载荷
```
