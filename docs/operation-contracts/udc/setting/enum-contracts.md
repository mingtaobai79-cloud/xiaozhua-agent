# 设置域 · 枚举操作契约

> 证据等级：LIVE（2026-10-20 三段写入链全通 + DB 回读 + 设计器 UI 抓包交叉证实）
> 域归属：UDC 九域之「设置」→ 枚举 tab
> 事实格：`core/facts/udc/setting/enum/create.md`
> 写链详情：`core/facts/udc/setting/enum/enum-write-chain.md`

## 入口

设计器：**应用设计 → 设置 → 枚举**（左树「枚举管理」）。
分组是枚举树上的父节点，枚举的 `categoryId` 指向分组 id（顶层用 `"0"`）。

## 契约清单

| operation_id | GraphQL operation | 方法 | 写 | 落库表 |
|---|---|---|---|---|
| `udc.enum.category.create` | `udcEnumCategoryPost` | POST | 是 | `ctp_enum_category` |
| `udc.enum.create` | `udcEnumPost` | POST | 是 | `ctp_enum` |
| `udc.enum.item.create` | `udcEnumItemPost` | POST | 是 | `ctp_enum_item` |
| `udc.enum.batch_delete` | `udcEnumBatchDeletePost` | POST | 是 | 逻辑删除 `is_delete=1` |
| `udc.enum.search_no_page` | `udcEnumSearchNoPagePost` | POST | 否 | — |
| `udc.enum.category.search` | `udcEnumCategorySearch` | POST | 否 | — |

**统一端点**：`POST /service/udc/graphql?<operation>`

**统一 body 形态**（GraphQL query，不是 REST JSON）：

```jsonc
{
  "query": "mutation graphqlLoader ($params0: <X>InputBody) { \n  data0: <X>(body: $params0) { code data { content } message status } }",
  "variables": { "params0": { /* 真正的 body */ } }
}
```

## 必填槽位与错误字典

| 缺失/非法 | 平台报错 | code |
|---|---|---|
| `orderNo` 缺 | 排序号不能为空 | `BOOT_1001` |
| 枚举 `name` 传裸文本 | 枚举编码 不能为空（实缺 i18n 形态） | `BOOT_1001` |
| 枚举 `code` 缺 | 枚举编码 不能为空 | `BOOT_1001` |
| 枚举 `appGuid` 缺 | — | `BOOT_1001` |
| 枚举 `categoryId` 缺 | — | `BOOT_1001` |
| 枚举项 `itemValue` 缺 | 枚举项编码 不能为空 | `BOOT_1001` |
| 枚举项 `parentId` 缺 | 上级枚举项ID 不能为null | `BOOT_1001` |
| 枚举项 `enumCode` 缺 | 所属枚举ID 不能为 null | `BOOT_1001` |
| 枚举项 `enumId` 缺 | 所属枚举编码 不能为空 | `BOOT_1001` |
| 枚举项 `name` 非大写+下划线 | `UDC_ENUM_0002`（**报错说 code，实际校验 name**） | `BOOT_1001` |
| 旧写法 `code` 传字符串 | `BOOT_3002` to type Int | `BOOT_3002` |
| 分组名重复 | 枚举分类名称重复 | `ENUM_3009` |
| 删除偶发误报（数据已生效） | 数据库错误 | `BOOT_4000` |

## xiaozhua-agent 侧能力

```python
# 构造（components/construction/metadata_artifacts.py）
build_enum_category_body(app_id, name, order_no=100, parent_id=None, description="")
build_enum_body(app_id, caption, name, order_no=100, category_id="0", app_guid=None, ...)
build_enum_item_body(app_id, enum_id, caption, item_value, enum_code, order_no,
                     enable=1, parent_id="0", item_level=1)

# 校验（components/udc/setting/enum_constraints.py）
validate_enum_category_body(body) / validate_enum_body(body) / validate_enum_item_body(body)

# 引用分析（components/udc/setting/enum_reference_analysis.py）
enum_ref_values(blob) / classify(enums, sources)
```

## 删除前引用分析

| 来源 | 载体 |
|---|---|
| 实体属性 | `udc_attribute` where `data_type='CTPENUM'` → `relation_entity` |
| 页面 | `udc_page_schema.page_schema` / `.draft_page_schema` |
| 资源 | `udc_resource.url_parameters` / `.out_parameters`（`is_deleted=0` 才算活引用） |
| 导出模板 | `ctp_excel_export_template.metadata_content` / `.excel_head_info` |
| 微流程 | `udc_microflow_info.data_schema` |

权威载体是参数 JSON 里的 `ctpEnumInfo` 块（`id` / `code` / `appId` / `CTPENUM` / `relationCtpEnum`）。

⚠ 页面 schema 在 `udc_page_schema`，**不是** `udc_page_info`——查错表会得出假结论。

## 本应用实测（2026-10-20，376 个枚举）

```
活引用  7 个   codeType / enums / FieldType / JoinType / reference_type / SyncMode
                （实体属性×1 + udc_page_schema）+ XzhCtpEnum953322
死引用 10 个   全在 udc_resource（引用方已删）
无引用 359 个
```
