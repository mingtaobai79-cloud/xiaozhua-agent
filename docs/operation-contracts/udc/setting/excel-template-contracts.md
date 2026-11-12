# 操作契约 · 设置域 / 导入导出模板（Excel Template）

> 事实格：`core/facts/udc/setting/excel-template/create.md`
> 实现：`components/udc/setting/excel_template_constraints.py`
> 脚本：`tools/core/setting/excel_template_seed.py`、`excel_template_entity_fields.py`

## ★ 协议：REST，不是 GraphQL

```
✅ POST /service/udc/excel/*
❌ POST /service/excel/*        → server_404「excel 服务不存在，请重启服务或重新发布应用」
```

实现在 `boot-starter-excel`，不在 udc-web 构件里。

## operation 清单

| operation | 方法 | 路径 | 写 | 状态 |
|---|---|---|---|---|
| `setting.excel.template.create` | POST | `/udc/excel/template/create` | 是 | **LIVE PASS** |
| `setting.excel.template.search` | POST | `/udc/excel/template/search` | 否 | **LIVE PASS** |
| `setting.excel.template.delete` | POST | `/udc/excel/template/delete` | 是 | LIVE |
| 自定义列表 | POST | `/udc/excel/template/search-custom-list-by-conditions` | 否 | LIVE |

## 四个坑

### 1. `isCustom=false` 才出现在 search 列表

反编译实证：`selectPageByCondition` 里硬写 `columnMap.put("isCustom", false)`。
`isCustom=true` 只会出现在 `search-custom-list-by-conditions`。

### 2. `columnList` 读回来恒为 null

列定义在 `metadataContent` / `excelHeadInfo` 两个 **JSON 字符串**里，提交时两个写同一份。

> ⚠ **这不是写失败**。写侧是成功的，只是读的不是那个字段。
> 本域还有另外三种「成功码 + 空」，处置完全不同 —— 见 [`README.md`](./README.md) §〇★。
> 照着 null 去重写，会把本来已经对的写坏。

### 3. 列的唯一锚点是 `attributeFullName`

```
attributeFullName = <实体全类名>.<字段名>      ← 唯一锚点
displayName       = Excel 表头名（可自定义）    ← 不是锚点
```

### 4. `PageRequest` 形态

```json
{"pageInfo": {"pageNumber": 1, "pageSize": 20}, "params": {...}}
```

⚠ 不是 `{page, size}`。写错报 `BOOT_3000 message:null`。

## create body

```json
{
  "appId": "<appId>",
  "appGuid": "<guid>",
  "name": "模板编码",
  "caption": "模板名",
  "mainFullName": "<实体全类名>",
  "isImport": true,
  "isCustom": false,
  "sheets": [{
    "columns": [{
      "attributeFullName": "<实体全类名>.<字段名>",
      "displayName": "表头名",
      "dataType": "STRING"
    }]
  }],
  "metadataContent": "<同上列的 JSON 字符串>",
  "excelHeadInfo": "<同上列的 JSON 字符串>"
}
```

## 关联实体字段：展开成两层 `levelPath`

页面上「创建人 ▸ 姓名 ▸ 编号/性别/手机号」的树形多选，数据结构：

```jsonc
"levelPath": [
  ["<appName>", "<entityFullName>", "<entityCaption>",
   "<entityFullName>.<relField>", "<relFieldCaption>"],        // 第一层：本实体的关联字段
  ["<relApp>", "<relEntityFullName>", "<relEntityCaption>",
   "<relEntityFullName>.<subField>", "<subFieldCaption>"]      // 第二层：关联实体的子字段
]
```

三个关键：

```
① attributeFullName 取第二层（关联实体的属性全名）
② displayName 用「本字段名/子字段名」，如「创建人/编号」
③ entityType 仍是 MASTER_ENTITY（不是 SUB_ENTITY）；
   relation=NONE、relationApp=<关联应用名，如 organization>、relationEntity=""
```

## 删除

```json
{"id": "<模板id>"}
```

⚠ 裸 Long 报 `BOOT_4002`。必须传 `{id}`。

## 未验证

```
update 系列                                  UNVERIFIED
Excel 导入/导出的运行期行为                    UNVERIFIED
多 sheet 的语义                              UNVERIFIED
isCustom=true 的完整流程                      UNVERIFIED
```
