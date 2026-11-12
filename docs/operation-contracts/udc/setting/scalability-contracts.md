# 操作契约 · 设置域 / 扩展实体（Scalability Option）

依据：反编译 `udc-web-5.3.517.jar` 的 `ScalabilityOptionController`，
`udc-biz-5.3.517.jar` 的 `ScalabilityOptionDto` / `ScalabilityDto`。
事实格见 `core/facts/udc/setting/scalability/create.md`。

## 协议：REST，路径连字符 `udc/scalability-option`

⚠ 与字段集 `udc/attributeSet`（驼峰）风格不同。

## operation 清单

| operation | 方法 | 路径 | 写 | 状态 |
|---|---|---|---|---|
| `setting.scalability.create` | POST | `/udc/scalability-option` | 是 | **LIVE PASS**（壳） |
| `setting.scalability.update` | POST | `/udc/scalability-option/update` | 是 | LIVE（壳）/ 预留组 BLOCKED |
| `setting.scalability.delete` | POST | `/udc/scalability-option/delete` | 是 | UNVERIFIED |
| `setting.scalability.get` | GET | `/udc/scalability-option/{id}` | 否 | UNVERIFIED |
| `setting.scalability.select_by_appid_tree` | GET | `/udc/scalability-option/select-by-appid/tree/{appId}` | 否 | LIVE |
| `setting.scalability.select_by_appid_detail` | GET | `/udc/scalability-option/select-by-appid/with-detail/{appId}` | 否 | **LIVE PASS** |
| `setting.scalability.select_all_name` | POST | `/udc/scalability-option/select-all-optionName` | 否 | UNVERIFIED |
| `setting.scalability.data_types` | GET | `/udc/scalability-option/data-type/{appId}` | 否 | UNVERIFIED |

## create body（ScalabilityOptionDto）

```json
{
  "appId": "<appId>",
  "name": "方案编码",
  "caption": "方案名称",
  "scalabilityDtoList": [],
  "attributeDtoList": []
}
```

⚠ `appId = -1` 表示**全局扩展**（不绑定具体应用）。

⚠ **不能一次带 `scalabilityDtoList`**：子项 `optionId` 有 `@NotNull`，
create 时方案 id 还不存在 → `BOOT_1001 方案id 不能为null`。

## ScalabilityDto（预留组）

```json
{
  "id": 0,
  "appId": "<appId>",
  "optionId": "<方案 id>",
  "prefix": "≤20字 字段名前缀",
  "caption": "显示名称",
  "count": 5,
  "dataType": "STRING",
  "dataTypeProperties": ""
}
```

约束：

- `prefix` `@NotBlank @Size(max=20)`
- `count` `@NotNull @Max(50)`；**页面 UI 限 20**
- `optionId` `@NotNull`

## 错误码

| 场景 | 码 / 文案 |
|---|---|
| 缺 appId | `BOOT_1001` appId 不能为null |
| 子项缺 optionId | `BOOT_1001` 方案id 不能为null |
| 子项 id 缺省（update） | `BOOT_1001` id 不能为null |

## ★ 预留组写入是 GraphQL，不是 REST

```
REST    父级  POST /udc/scalability-option   不处理 scalabilityDtoList（静默忽略）
GraphQL 子级  udcScalabilityPost             ← 真正的预留组写入入口
```

预留组 body（完整，页面发的逐字）：

```json
{
  "dataType": "STRING",
  "prefix": "probeExt",
  "count": 5,
  "dataTypeProperties": "{\"minLength\":\"0\",\"maxLength\":50}",
  "optionId": "<方案id>",
  "caption": "probeExt"
}
```

⚠ `dataTypeProperties` 是 JSON 字符串，`minLength` 用字符串、`maxLength` 用数字。

读某方案的预留组：`POST graphql?udcScalabilityOptionOptionGet {"optionId": "<id>"}`

## 已推翻的 REST 尝试（留档）

```
① create 带 scalabilityDtoList（子项无 optionId） → 方案id 不能为null
② 建壳后 update 带子项（optionId 有，子项 id 缺）  → id 不能为null
③ 同上但子项 id=0                                → BOOT_0000，udc_scalability 仍 0 行
```

结论：**REST 父级不处理子集合**。与字段集同一模式（`attribute-set-contracts.md` §已推翻的 REST 尝试）。

> ⚠ 本节是「真没写进去」；**本节下方 §关键对照 的 `udc_scalability` 0 行恰恰是"正常空"** ——
> 同一份文件里就有一个反例。四种成因的对照见 [`README.md`](./README.md) §〇★。

## 页面操作要点（UI 走通记录）

1. 左方案列表点 `lined-edit` 选中
2. 右侧填「字段名称前缀 + 预留字段数量」
3. 预览区实时显示派生字段名（`probeExt01，probeExt02，…`）
4. 点 `.extension-form-footer` 的「确定」→ 发 `udcScalabilityPost`
5. ⚠ 表格里的「新建」只加内存行，**不提交**

## 关键对照（说明「0 行」可能是正常的）

本 app 真实方案 `dsa`（测试流程查询出参，2026-10-21 12:11 创建）：

```
udc_scalability_option 有记录
scalabilityDtoList = 0
attributeDtoList   = 0
udc_scalability 表 = 0 行
```

**真实业务方案也是 0 行** —— 预留字段很可能是**懒派生**（实际用到时才生成），
不是建方案时立即落库。所以「方案存在 + 预留组 0 行」不能判为失败。

## 落库

```
udc_scalability_option   方案主表
  id / create_time / tenant_id / update_time / version / guid / publish_state
  caption / name / owner_code / backup_code / app_id / original_id

udc_scalability          预留组
  id / create_time / tenant_id / update_time / version / guid / publish_state
  caption / count / data_type / data_type_properties / option_id / prefix / owner_code

udc_custom_ext_field     实际扩展字段（本 app 0 行）
  app_name / entity_full_name / attribute_name / attribute_caption / data_type / state
```
