# 枚举域写链（UdcEnum / UdcEnumCategory / UdcEnumItem）

> ℹ️ **本目录两份分工**：`create.md` = 九段式事实格摘要（能力/输入/约束/证据等级）；
> 本文件 = 全量操作表 + 请求体 + 错误字典 + 踩坑。**不重复维护，改一处即可。**

> 前置：本文所有 `udc*Post` 必填的 `appGuid`，取法见 [`precondition-appguid.md`](../precondition-appguid.md)（用 `udcApplicationDetailGet` 接口查，appGuid ≠ appId，无需查库）。
**证据等级**：LIVE（三段写入链全部实跑通过 + DB 回读）
**验证日期**：2026-10-20
**目标环境**：test2，`datamigration9000000000000000001`
**验证方式**：seeyon-agent 自身能力（`build_*` → `validate_*` → 提交 → DB 回读），
并用设计器真实 UI 抓包交叉证实请求体逐字段同构。

> 本文件是枚举域唯一事实源。旧记录里的「枚举项字段名未定」「枚举走 REST /udc/udc-enum」
> 均已作废，见文末「已作废的说法」。

---

## 0. 域内对象与落库表

| 业务对象 | 平台对象 | 落库表 | 关键列 |
|---|---|---|---|
| 枚举分组（分类） | `UdcEnumCategory` | `ctp_enum_category` | `name` / `order_no` / `parent_id` / `is_delete` / `app_id` / `app_guid` / `is_preset` / `data_status` |
| 枚举 | `UdcEnum` | `ctp_enum` | `code` / `name`(i18n JSON) / `category_id` / `order_no` / `is_delete` / `enum_type` / `expansible` / `enable` |
| 枚举项 | `UdcEnumItem` | `ctp_enum_item` | `item_value` / `name`(i18n JSON) / `enum_code` / `enum_id` / `parent_id` / `item_level` / `leaf` / `enable` / `order_no` |

⚠ **表名易混**：`udc_enum_category` 是**另一张表**（不是分组落库表）。分组落 `ctp_enum_category`。
枚举落 `ctp_enum`（不是 `udc_enum`）。查库前先确认表名，否则会误判「数据没落库」。

---

## 1. 入口路径：设置 → 枚举

设计器路径：`应用设计 → 设置 → 枚举`（左树「枚举管理」）。
分组是枚举树上的**父节点**，`categoryId` 指向分组 id（顶层用 `"0"`）。

---

## 2. 分组新建（udcEnumCategoryPost）

```http
POST /service/udc/graphql?udcEnumCategoryPost
Content-Type: application/json
```

```jsonc
{
  "query": "mutation graphqlLoader ($params0: udcEnumCategoryPostInputBody) { \n  data0: udcEnumCategoryPost(body: $params0) { code data { content } message status } }",
  "variables": {
    "params0": {
      "name": "{\"zh_CN\":\"分组名\"}",   // i18n JSON 字符串
      "orderNo": 1,
      "appGuid": "<udc_application.guid>",
      "hostAppName": null,
      "appId": "<appId 字符串>",
      "dataStatus": false
    }
  }
}
```

**校验（平台侧）**

| 条件 | 平台报错 | code |
|---|---|---|
| `orderNo` 缺失 | 排序号不能为空 | `BOOT_1001` |
| `name` 非 i18n JSON | 实际缺的是 name 的 i18n 形态 | `BOOT_1001` |
| 分组名重复 | 枚举分类名称重复 | `ENUM_3009` |

**seeyon-agent 能力**

```python
from components.construction.metadata_artifacts import build_enum_category_body
from components.udc.setting.enum_constraints import validate_enum_category_body

body = build_enum_category_body(app_id, name="验收分组", order_no=1)
body.update(appGuid=APP_GUID, hostAppName=None, dataStatus=False)
errs = validate_enum_category_body(body)   # 空 = 通过
```

构造器拒绝：`name` 为空/空白（`ValueError`）、`parent_id` 非 int/None（平台要 Long）。

---

## 3. 枚举新建（udcEnumPost）

```http
POST /service/udc/graphql?udcEnumPost
```

```jsonc
{
  "query": "mutation graphqlLoader ($params0: udcEnumPostInputBody) { \n  data0: udcEnumPost(body: $params0) { code data { content } message status } }",
  "variables": {
    "params0": {
      "name": "{\"zh_CN\":\"显示名\"}",     // ← i18n JSON 字符串，不是裸文本
      "code": "zxjAcceptEnum",              // ← 英文编码
      "orderNo": 10,
      "categoryId": "-2165189518708277331", // 分组 id；顶层用 "0"
      "expansible": true,
      "enable": true,
      "enumType": "SAME_LEVEL",
      "children": [],
      "appId": "<appId 字符串>",
      "hostAppName": null,
      "appGuid": "<udc_application.guid>",
      "dataStatus": false,
      "bizType": "UDC_DESIGN"
    }
  }
}
```

**校验（平台侧）**

| 条件 | 平台报错 | code |
|---|---|---|
| `name` 传裸文本 | **枚举编码 不能为空**（报错说编码，实缺 name 的 i18n 形态） | `BOOT_1001` |
| `orderNo` 缺失 | 排序号不能为空 | `BOOT_1001` |
| `code` 缺失 | 枚举编码 不能为空 | `BOOT_1001` |
| `appGuid` 缺失 | — | `BOOT_1001` |
| `categoryId` 缺失 | — | `BOOT_1001` |

**seeyon-agent 能力**

```python
from components.construction.metadata_artifacts import build_enum_body
from components.udc.setting.enum_constraints import validate_enum_body

body = build_enum_body(app_id, caption="验收枚举", name="zxjAcceptEnum",
                       order_no=10, category_id=GROUP_ID, app_guid=APP_GUID)
errs = validate_enum_body(body)
```

`validate_enum_body` 拦截：裸文本 `name`、`name` 的 JSON 缺 `zh_CN`、缺 `code`、
缺 `orderNo`、缺 `appGuid`、缺 `categoryId`。

⚠ **`appGuid` 取自 `udc_application.guid`，不是 `appId`**。两者不同，填错会被拒。

---

## 4. 枚举项新建（udcEnumItemPost）

```http
POST /service/udc/graphql?udcEnumItemPost
```

```jsonc
{
  "query": "mutation graphqlLoader ($params0: udcEnumItemPostInputBody) { \n  data0: udcEnumItemPost(body: $params0) { code data { content } message status } }",
  "variables": {
    "params0": {
      "appId": "<appId 字符串>",
      "enumId": "<枚举id>",
      "enumCode": "<枚举code>",       // ← 与 enumId 都要给，缺一不可
      "name": "{\"zh_CN\":\"显示名\"}",
      "itemValue": "1",               // ← 枚举项值（字符串）
      "parentId": "0",                // ← 上级枚举项ID；顶层项填 "0"
      "itemLevel": 1,
      "leaf": 1,
      "enable": 1,
      "orderNo": 10,
      "appGuid": "<udc_application.guid>",
      "hostAppName": null,
      "dataStatus": false
    }
  }
}
```

**校验（平台侧）**

| 条件 | 平台报错 | code |
|---|---|---|
| 缺 `itemValue` | **枚举项编码 不能为空** | `BOOT_1001` |
| 缺 `parentId` | **上级枚举项ID 不能为null** | `BOOT_1001` |
| 缺 `enumCode` | 所属枚举ID 不能为 null | `BOOT_1001` |
| 缺 `enumId` | 所属枚举编码 不能为空 | `BOOT_1001` |
| `name` 非大写字母+下划线 | `UDC_ENUM_0002`「The code contains only uppercase letters and underscores」——**报错说 code，实际校验 name** | `BOOT_1001` |
| `code` 传字符串（旧写法） | `BOOT_3002` Failed to convert String to Int | `BOOT_3002` |

**seeyon-agent 能力**

```python
from components.construction.metadata_artifacts import build_enum_item_body
from components.udc.setting.enum_constraints import validate_enum_item_body

body = build_enum_item_body(app_id, enum_id, caption="待处理",
                            item_value="1", enum_code="zxjAcceptEnum", order_no=10)
errs = validate_enum_item_body(body)
```

`validate_enum_item_body` 拦截：缺 `itemValue`、缺 `parentId`、缺 `enumCode`、
缺 `enumId`、缺 `orderNo`、`name` 非 i18n JSON、`name` 的 JSON 缺 `zh_CN`。

⚠ **`itemValue` 与枚举的 `code` 不是一回事**：
枚举的 `code` 是英文编码（字符串），枚举项的 `itemValue` 是**枚举项值**（字符串）。
旧构造器用 `code`/`caption` 两个槽位全是错的。

---

## 5. 枚举删除（udcEnumBatchDeletePost）

### 5.1 删除前必做引用分析（**载体搞错过，差点误删 363 个**）

> 2026-10-20 事故与纠正：
> 第一版引用分析只扫 `udc_page_info.page_schema`，得到「页面 0 命中」，
> 随后删除 363 个枚举。**结论是错的**——页面 schema 在 `udc_page_info` 之外的
> **`udc_page_schema`** 表（`page_schema` / `draft_page_schema` 两列）。
> 真相：页面**确实**引用枚举（下拉/单选控件绑定 ctpEnumInfo）。

**权威载体**（2026-10-20 实读原文确认）：

```jsonc
// 页面 / 资源 / 导出模板 的参数 JSON 里
{"ctpEnumInfo": {"id": "<枚举id>", "code": "<枚举code>", "appId": "<应用id>",
                 "caption": "业务类型",
                 "CTPENUM": {"appName": "...", "fullName": "...",
                             "currentAppId": "...", "id": "<枚举id>"},
                 "relationCtpEnum": {"enumType": "SAME_LEVEL", "enumLevel": 0}}}
```

**四类引用源**：

| 来源 | 载体表 / 字段 | 关系 |
|---|---|---|
| 实体属性 | `udc_attribute` where `data_type='CTPENUM'` → `relation_entity` / `relation_code` | 直接关系（最可靠） |
| 页面 | `udc_page_schema.page_schema` / `.draft_page_schema` | `ctpEnumInfo` 块 |
| 资源 | `udc_resource.url_parameters` / `.out_parameters` | `ctpEnumInfo` 块（`is_deleted=0` 才算活引用） |
| 导出模板 | `ctp_excel_export_template.metadata_content` / `.excel_head_info` | `ctpEnumInfo` 块 |
| 微流程 | `udc_microflow_info.data_schema` | `enumId` / `enumCode` 字段 |

**分析器**：`components/udc/setting/enum_reference_analysis.py`
（`enum_ref_values` + `classify`，带阳性/阴性对照门）

**四个必守判据**（对应 `tests/udc/test_enum_reference_analysis.py` 13 项）：

1. **载体要对** —— 页面查 `udc_page_schema`，不是 `udc_page_info`。
2. **阳性对照** —— 必须能检出「实体属性在用」的枚举 code（本应用 6/6）。
   检不出 → 方法有缺口，此时「无引用」结论不可信，**不许下删除结论**。
3. **阴性对照** —— 不存在的枚举不得被检出（防子串误判：`code="bool"` 命中 `"boolean"`）。
4. **引用方有效性** —— 引用方自身 `is_deleted=1` 时不算活引用。
   ⚠ 第一版还漏了 `SELECT is_deleted` 字段，把 31 条已删资源误判成活引用。

**本应用实测结果**（2026-10-20，376 个枚举）：

```
活引用（绝对不能删）  7 个：
  codeType / enums / FieldType / JoinType / reference_type / SyncMode
    ← 实体属性 ×1 + udc_page_schema
  XzhCtpEnum953322
    ← 实体属性 ×1（挂在「小爪实验实体950795V2」上；该实体删除后可一并清）

仅死引用（引用方已删）  10 个：biangengneirong / bool / business_type /
  customer_nature / frameType / fujianleixing / instance_type / kuangjialeixing /
  sales_type / shifoumeiju   ← 全在 udc_resource（is_deleted=1）

无引用                 359 个
```

### 5.2 删除接口

```http
POST /service/udc/graphql?udcEnumBatchDeletePost
```

```jsonc
{
  "query": "mutation graphqlLoader ($params0: udcEnumBatchDeletePostInputBody) { \n  data0: udcEnumBatchDeletePost(body: $params0) { code data { content } message status } }",
  "variables": { "params0": { "ids": ["3496086073116609037", "..."] } }
}
```

**语义**：**逻辑删除**（`ctp_enum.is_delete = 1`），物理行仍在表里。
界面上不再可见，但数据可恢复。回读统计必须用 `is_delete=0` 过滤，否则会误判「没删掉」。

⚠ 平台删除接口**偶发返回 `BOOT_4000 数据库错误` 但数据实际已生效**。
回读 `is_delete` 确认，不要因为报错就重发（会造成重复操作）。

---

## 6. 枚举查询（只读，供引用分析用）

| 用途 | 端点 |
|---|---|
| 枚举列表（含 `categoryId`） | `udcEnumSearchNoPagePost` |
| 分组列表 | `udcEnumCategorySearch`（`params.appId` + `params.appGuid` + `params.name`，`sort.orders` 按 `orderNo ASC` / `createTime DESC`） |
| 排序号计算 | `udcEnumCalcOrderNumPost` |

DB 侧（只读，agent 自带 `MySQLConnectionAdapter`）：

```sql
-- 枚举
SELECT id, code, name, category_id, order_no, is_delete
FROM udc_test2.ctp_enum WHERE app_id = ? AND is_delete = 0;

-- 枚举项
SELECT id, item_value, name, enum_code, enum_id, parent_id, item_level, leaf, enable
FROM udc_test2.ctp_enum_item WHERE enum_id = ? ORDER BY order_no;

-- 分组
SELECT id, name, order_no, parent_id, is_delete
FROM udc_test2.ctp_enum_category WHERE app_id = ?;
```

---

## 7. 自动化填表陷阱：输入法拼音中间态

用 CDP 填「枚举编码」框时，若采用「先 `set('')` 再 `set(value)`」两步法填**中文**，
React 受控组件会拿到**拼音中间态**——实测想填 `zxjUiTraceEnum`，
提交出去变成 `UIguijimeiju`（拼音转换结果），且**平台不报错、直接落库**。

规则：
- 编码框只填英文/数字。
- 中文显示名用原生 setter 一次性赋值，跳过 IME 组合事件。
- 落库后**必须回读 `ctp_enum.code` 核对**，不能只看接口返回成功。

---

## 8. 抓包方法（避免重复踩坑）

本域所有请求体都是用以下方式拿到的，**不要再手工猜接口名**：

```
rea:capture_browser_scenario   connect 到已有 CDP → 驱动真实 UI → 抓 request_body
skill: udc-trace-to-api        CDP 旁路 firehose → OpenAPI
```

要点：
- 先用 `rea:list_browser_targets` 确认 target 的**当前 URL**——若已是 `/login`，
  登录态失效，抓什么都是空的。
- 页面内 `window.fetch` 拦截器在**导航后立即失效**，不能用来抓跨页流程。
- 本机 Edge 155 的 `Network.*` 域返回 `-32601`（不可用），手工 CDP 抓网络必须换 rea。

---

## 9. 已作废的说法（避免旧知识误导）

| 旧说法 | 现状 |
|---|---|
| 枚举项字段名未定，要靠抓包试 | **已定**：`itemValue` + `parentId` + `enumId` + `enumCode`（见 §4） |
| 枚举走 REST `POST /service/udc/udc-enum` | **错**。走 GraphQL `udcEnumPost`（见 §3） |
| 枚举 body = `{appId, caption, name, orderNo}` | **错**。name 是 i18n JSON、code 才是编码，且多 8 个字段（见 §3） |
| 枚举项 body = `{appId, enumId, caption, code, name, orderNo}` | **错**。`code`/`caption` 不是平台槽位（见 §4） |
| 分组落 `udc_enum_category` | **错**。落 `ctp_enum_category`（见 §0） |
| 枚举删除是物理删除 | **错**。逻辑删除 `is_delete=1`（见 §5） |
| `UDC_ENUM_0002` 校验 code | **错**。校验 name（见 §4） |
