# 操作契约 · 设置域 / 字段集（Attribute Set）

依据：反编译 `udc-web-5.3.517.jar` 的 `AttributeSetController` /
`AttributeGroupController`，`udc-plugin-api-5.3.517.jar` 的 `AttributeSetDto`，
`udc-common-5.3.517.jar` 的 `AttributeDto` / `AttributeSetSourceTypeEnum`。
事实格见 `core/facts/udc/setting/attribute-set/create.md`。

## 协议：REST，路径驼峰 `udc/attributeSet`

⚠ 字段集是 `udc/attributeSet`（**驼峰**），字段分组是 `udc/attribute-group`（**连字符**）。
  写 `/udc/attribute-set` 会被 nginx 403 拒（路径不存在）。

## operation 清单

| operation | 方法 | 路径 | 写 | 状态 |
|---|---|---|---|---|
| `setting.attribute_set.create` | POST | `/udc/attributeSet` | 是 | **LIVE PASS**（壳） |
| `setting.attribute_set.update` | POST | `/udc/attributeSet/update` | 是 | LIVE（壳）/ 字段 BLOCKED |
| `setting.attribute_set.delete` | POST | `/udc/attributeSet/delete` | 是 | UNVERIFIED |
| `setting.attribute_set.batch_delete` | POST | `/udc/attributeSet/batch-delete` | 是 | UNVERIFIED |
| `setting.attribute_set.get` | GET | `/udc/attributeSet/{id}` | 否 | UNVERIFIED |
| `setting.attribute_set.search_list` | POST | `/udc/attributeSet/search-list` | 否 | UNVERIFIED |
| `setting.attribute_set.select_by_appid` | POST | `/udc/attributeSet/select-by-appid` | 否 | UNVERIFIED |
| `setting.attribute_set.search_term` | POST | `/udc/attributeSet/search/term` | 否 | LIVE（页面加载） |
| `setting.attribute_set.select_attributes` | POST | `/udc/attributeSet/select-attribute-list` | 否 | **LIVE PASS** |
| `setting.attribute_group.get` | GET | `/udc/attribute-group/{entityId}` | 否 | **LIVE PASS** |
| `setting.attribute_group.operate_batch` | POST | `/udc/attribute-group/operate-batch` | 是 | UNVERIFIED（要求字段已存在） |
| **`setting.attribute_set.field.create`** | POST | `graphql?udcEntityAttributePost` | 是 | **LIVE PASS** |

## ★ 字段写入是 GraphQL，不是 REST

```
REST  父级  POST /udc/attributeSet        不处理 attributes（静默忽略）
GraphQL 子级 udcEntityAttributePost       ← 真正的字段写入入口
```

我之前 4 种 REST 变体全部失败（回 BOOT_0000 但 udc_attribute 零写入），
从页面抓包才拿到真实入口。

字段 body（完整）：

```json
{
  "0": "1",
  "caption": "显示名", "name": "编码（英文/拼音）",
  "dataType": "STRING", "notNull": false, "searchable": false,
  "defaultValue": "", "uniqueness": false,
  "minLength": 0, "maxLength": 50, "auditLog": false, "attributeGroup": "",
  "defaultValueSystemVariable": "", "defaultValueExpressionDesignData": "",
  "defaultValueExpressionRuntimeData": "", "defaultValueIsChange": true,
  "defaultValueCaption": "", "calculate": "NORMAL",
  "expressionDesignData": "", "expressionRuntimeData": "",
  "sourceType": "ATTRIBUTESET", "entityId": "<字段集id>", "sourceId": "<字段集id>",
  "appId": "<appId>", "description": "",
  "widgetConfig": "{\"pc\":\"Input\",\"mobile\":\"Input\",\"list\":true,\"detail\":true,\"quickSearch\":true}"
}
```

⚠ `"0"` 是排序占位（键名就是字符串 "0"）；`widgetConfig` 是 JSON 字符串。

⚠ **`widgetConfig` 不能统一写 `Input`**（2026-10-21 用户现场纠正）：
上面这行只是 STRING 字段的形态。其余类型必须按 dataType 给，
否则日期装不了、枚举选不了、金额显示不出货币格式。完整对照表见事实格
`attribute-set/create.md` §十六 与 `components/udc/setting/attribute_set_constraints.py`
的 `DEFAULT_WIDGETS` / `build_widget_config()`：

```
MULTILINESTRING TextArea/TextArea        INTEGER      InputNumber/InputNumber
BIGINTEGER      Input/Input              DECIMAL      InputNumber/InputNumber
CURRENCY        Currency/Currency        DATE         DatePicker/DateTimePicker
TIME            TimePicker/TimePicker    DATETIME     DatePicker/DateTimePicker
BOOLEAN         Switch/Switch            ENUM/CTPENUM TreeSelect/CascaderSelect
ENTITY          UdcReference/UdcReference
ATTACHMENT      Attachment/Upload        CONTENT      UiBusinessContent
```

四个反直觉点：`BIGINTEGER` 用 `Input`（超 JS 安全整数）；PC 与移动端常不同
（DATE/DATETIME、ENUM/CTPENUM、ATTACHMENT）；`CURRENCY` 有专属控件；
`CONTENT` 用正文编辑器。

## create body（AttributeSetDto）

```json
{
  "appId": "<appId>",
  "name": "≤30字 方案编码",
  "caption": "≤50字 显示名称",
  "description": "",
  "sourceType": "APP | UDC | ISV",
  "orderNo": 1,
  "attributes": []
}
```

⚠ `attributes` 传了也会被**静默忽略**（BLOCKED）。建壳只传 `[]`。

## 读字段 body

```json
{ "attributeSetId": "<字段集 id>" }
```

⚠ 键名是 `attributeSetId`，不是 `id`（传 `id` 报 `UDC_ENTITY_0022 字段集不存在`）。

## AttributeDto（字段）关键槽位

```json
{
  "name": "字段编码",
  "caption": "字段显示名",
  "dataType": "STRING | INTEGER | BIGINTEGER | DECIMAL | DATE | DATETIME | BOOLEAN",
  "notNull": false,
  "minLength": 0, "maxLength": 50, "decimalDigits": 0,
  "multiSelect": false,
  "relationEntityCategory": "ENTITY",
  "relationType": "Many2OneAssociation",
  "searchable": false, "uniqueness": false,
  "defaultValueIsChange": true,
  "calculate": "NORMAL",
  "attributeGroupId": 0,
  "encryption": "NOT_ENCRYPTION", "desensitization": "None",
  "entityId": "<字段集 id>",          // ★ @NotNull
  "orderNo": 1,
  "sourceType": "ATTRIBUTESET",       // ★
  "sourceId": "<字段集 id>",          // ★
  "serialNumberGuid": 0, "parentEnumAttributeId": 0,
  "widgetConfig": "{\"pc\":\"Input\",\"mobile\":\"Input\",\"list\":true,\"detail\":true,\"quickSearch\":true}",
  "columnName": "字段编码",
  "useSnapshot": false
}
```

## 错误码

| 场景 | 码 / 文案 |
|---|---|
| 缺 appId | `BOOT_1001` 字段集所属应用Id 不能为null |
| 缺 caption | `BOOT_1001` 字段集显示名称 不能为空 |
| 字段缺 entityId | `BOOT_1001` 实体主键ID 不能为null |
| 分组缺 caption | `BOOT_1001` 分组名称 不能为空 |
| operate-batch 但字段不存在 | `BOOT_1000` 当前实体下未查询到字段信息 |
| 读字段传 `id` | `UDC_ENTITY_0022` 字段集不存在 |

## 已推翻的 REST 尝试（留档）

```
① create 带 attributes（entityId 空） → BOOT_1001 实体主键ID 不能为null
② create 自带 id + 字段 entityId 指向它 → BOOT_0000，字段读回 0（静默忽略）
③ 先建壳再 update 带 attributes      → BOOT_0000 content=1，字段读回 0
④ update 带 sourceType=APP/3/缺省    → 0000 或 1001，字段始终 0
```

结论：**REST 父级不处理子集合**，字段必须走 GraphQL `udcEntityAttributePost`。

> ⚠ **别把这一条当通则**：「成功码 + 字段读回 0」在本域有 **4 种**成因（真没写进去 / 写进去了但读错字段 /
> 本来就是空 / 上下文不对），处置相反。四者对照见 [`README.md`](./README.md) §〇★。
> 本条属于第 ① 种：**写入侧真的没生效**。

## 页面操作要点（UI 走通记录）

字段集是「左列表 + 右常驻表单」：
1. 左列表点行内 `lined-edit` 选中字段集
2. 右侧「名称」填显示名 —— 中文自动转拼音填「编码」（`验收字段集U` → `yanshouziduanjiU`）
3. 点「确定」（在表单底部，y≈847）
4. ⚠ 名称/编码空着点确定只出红字，**不发请求**

## 落库

```
udc_attribute_set     字段集主表
udc_attribute         字段（entity_id = 字段集 id，source_type=1）
udc_attribute_group   字段分组（字段集只有一个虚拟分组 id="1", virtual=true）
```
