---
name: seeyon-udc-setting
description: "Use when working on the 2小爪 UDC 设置 domain: 枚举/选项集/自定义对象/页面设置等 tab 的配置、校验与删除。"
version: 1.0.0
author: 小爪 🐾
license: MIT
platforms: [windows, macos, linux]
tags: [2小爪, udc, setting, enum, option-set, custom-object]
metadata:
  hermes:
    tags: [2小爪, udc, setting, enum, option-set, custom-object]
---

# 2小爪 UDC · 设置域

## 域定位

UDC 九域之一：应用 / 实体 / 菜单 / 规则 / 流程 / BI / 栏目 / **设置** / 角色。

设置域在设计器里的入口：**应用设计 → 设置**（左树第 8 项，齿轮图标）。
下面是若干 tab，其中**枚举**是本 skill 当前唯一完全打通的子域。

设置域 tab 全表（`components/udc/setting/settings_tab_model.py::SETTING_TABS`）：

| tab | js_key | 状态 | 说明 |
|---|---|---|---|
| 枚举 | `collections` | **OK** | 已完全打通，见下 |
| 自定义对象 | — | **OK** | 创建/更新/删除/字段组装已打通，见下 |
| 选项集 | `enumeration` | **OK** | 三段写链已打通（与枚举是两套独立表），见下 |
| 参数 | — | **OK** | 创建/更新已打通，见下 |
| 流水号 | — | **OK** | 三段写链+删除已打通（字段名来自反编译 SerialSchemeDto） |
| 导入导出模板 | — | **OK** | 建模板已打通（REST，非 GraphQL），见下 |
| 二维码 | — | **OK** | 三种类型全打通（REST），见下 |
| 字段集 | — | **OK** | 父 REST + 子 GraphQL，见下 |
| 扩展实体 | — | **OK** | 父 REST + 子 GraphQL，见下 |
| 页面模板 / 外框模板 | — | **不在本域处理** | 页面/外框建完后自动同步过来，本质上在那边处理 |

### ★★ 关键模式：父子两级用两种协议（字段集 & 扩展实体都是）

这是本轮最重要的发现，两条都属于同一个模式：

```
父（壳）   REST     ← create/update 只改壳自身，不处理子集合
子（明细） GraphQL  ← 真正的子项写入入口
```

**DTO 里有 `attributes` / `scalabilityDtoList` 字段 ≠ 该类通过它写入。**
我在 REST 父级 update 上试了 4+2 种变体，全部回 `BOOT_0000` 但子表零写入（静默忽略）。

### 字段集（Attribute Set）

```
父 REST（驼峰）  POST /service/udc/attributeSet              建壳
子 GraphQL ★    udcEntityAttributePost                      加字段
读字段 REST     POST /service/udc/attributeSet/select-attribute-list {"attributeSetId": "<id>"}
读分组 REST     GET  /service/udc/attribute-group/{entityId}
```

```python
from components.udc.setting.attribute_set_constraints import (
    build_attribute_set_body, build_attribute_field_body, build_read_attributes_body,
    validate_attribute_set_body, validate_attribute_field_body)

# 1) 壳（REST）
body = build_attribute_set_body(app_id, name="zxjFieldSetA", caption="验收字段集A")
# 2) 字段（GraphQL udcEntityAttributePost）
fbody = build_attribute_field_body(app_id, set_id, name="probeA", caption="探针A")
# 3) 读
q = build_read_attributes_body(set_id)     # {"attributeSetId": ...}
```

字段 body 的坑：

- 排序占位键是**字符串 `"0"`**（`{"0": "1", ...}`）
- `widgetConfig` 是 **JSON 字符串**，不是对象
- `entityId` = `sourceId` = 字段集 id；`sourceType = "ATTRIBUTESET"`
- `name` 是编码（英文/拼音），含中文会被拦

### ★★ CTPENUM 字段：三个关联槽位缺一不可（用户现场纠正）

新建用 `udcEntityAttributePost`，**修改用 `udcEntityAttributeUpdatePost`**（别搞混）。

```python
from components.udc.setting.attribute_set_constraints import build_attribute_field_body

body = build_attribute_field_body(
    app_id, set_id, name="myField", caption="我的字段",
    data_type="CTPENUM",
    relation_code="XzhCtpEnum953322",        # ★ 平台枚举编码
    relation_entity_name="UI轨迹枚举",        # ★ 枚举显示名
    relation_enum_type="SAME_LEVEL",
    relation_enum_level=0,
)
# body 里会自动带：
#   relationCode: "XzhCtpEnum953322"
#   relationEntityName: "UI轨迹枚举"
#   relationCtpEnum: {enumType:"SAME_LEVEL", enumLevel:0}   ← 不要传 id/code
#   relationEntity: <枚举id>
```

**缺 `relationEntityName` → 页面「枚举」列显示 null**（2026-10-21 用户现场确认）。
**修改用 `udcEntityAttributeUpdatePost`**（带 field_id）。

实体类型（ENTITY）同理：`relationCode` / `relationEntity` / `relationEntityName`
三个都要传，候选来自 `udcEntityAssociationEntityAppGet` 加载后选择。

### 扩展实体（Scalability Option）

```
父 REST（连字符） POST /service/udc/scalability-option           建方案
子 GraphQL ★     udcScalabilityPost                             加预留组
读预留组 GraphQL  udcScalabilityOptionOptionGet {"optionId": "<id>"}
读方案 REST      GET /service/udc/scalability-option/select-by-appid/with-detail/{appId}
```

```python
from components.udc.setting.scalability_constraints import (
    build_scalability_option_body, build_scalability_group_body,
    validate_scalability_option_body, validate_scalability_group_body)

body = build_scalability_option_body(app_id, name="zxjExtOpt", caption="验收扩展实体")
gbody = build_scalability_group_body(option_id, app_id=app_id, prefix="probeExt", count=5)
```

`appId = -1` 表示全局扩展；`prefix` ≤20；`count` ≤50（DTO）/ ≤20（页面 UI）；
`dataTypeProperties` 是 JSON 字符串且 `minLength` 用字符串、`maxLength` 用数字。

### 页面操作要点（UI 走通记录）

两块界面都是「左列表 + 右常驻表单」：

```
字段集
  1. 左列表点行内 lined-edit 选中
  2. 右侧「名称」填显示名 → 中文自动转拼音填「编码」
  3. 点表单底部「确定」（y≈847，不是表格里的）
  ⚠ 名称/编码空着点确定只出红字，不发请求

扩展实体
  1. 左列表点 lined-edit 选中
  2. 右侧填「字段名称前缀 + 预留字段数量」
  3. 预览区实时显示派生名（probeExt01，probeExt02，…）
  4. 点 .extension-form-footer 的「确定」→ 发 udcScalabilityPost
  ⚠ 表格里的「新建」只加内存行，不提交
```

### 这两块的共同教训（下次先看这条）

遇到「父子两级 + 子项必挂父 id」的域：

1. **不要**反复试 REST 父级 update 带子集合 —— 大概率静默忽略
2. **正确做法**：在页面真实操作一次，用
   `performance.getEntriesByType('resource')` 抓 URL、页面内拦截器抓 body
3. 抓到的 op 名往往是 `udc<Domain>Post` 形态的 GraphQL，而非 REST

### 这两块的共同形态（下次遇到先看这条）

字段集和扩展实体是**同一种结构**：

```
父实体建壳 → 拿到 id → 子项必须挂父 id，但 update 对子集合静默忽略
```

遇到这种「父子两级 + 子项必挂父 id」的域，**不要反复试 create/update 带子集合**，
直接去页面真实操作一次抓 body。已证 4 种变体全部静默忽略。

⚠ 交叉命名陷阱：枚举的 JS key 叫 `collections`，选项集叫 `enumeration`——**别按 key 猜 tab**。

## 设置域的接口分两类（重要）

```
GraphQL（绝大多数）：枚举 / 选项集 / 自定义对象 / 参数 / 流水号
    POST /service/udc/graphql?<operationName>
    body = {"query":"...", "variables":{"params0":{...}}}

REST（少数）：导入导出模板 / 二维码
    POST /service/udc/excel/*           ← 注意前缀是 /udc/excel
    POST /service/udc/qrcode-rule/*
```

⚠ `/service/excel/*` 会报 `server_404 excel 服务不存在`。
排查顺序：先试后台 JSON（REST/GraphQL），不行再反编译 jar 读 DTO —— 不要靠猜字段名。

## 导入导出模板（Excel Template）

页面：**设置 → 导入导出模板**，左选实体，右边「导入模板 / 导出模板」两个 tab。
一个模板 = 选实体 + 选要导出的字段 + 给每个字段起**表头名称**。

```python
from components.udc.setting.excel_template_constraints import (
    build_column, build_template_body, validate_template_body, parse_columns)

cols = [build_column(f"{entity_full_name}.{fname}", "表头名", data_type="STRING")]
body = build_template_body(app_id, app_guid, name="我的模板",
                           main_full_name=entity_full_name,
                           sheets=[cols], is_import=True, is_custom=False)
errs = validate_template_body(body)
```

**四个坑**：

1. **`isCustom=false` 才出现在 `search` 列表**。
   `=true` 只会出现在 `search-custom-list-by-conditions`。
   （反编译实证：`selectPageByCondition` 里硬写 `columnMap.put("isCustom", false)`）
2. **`columnList` 读回来恒为 null**。列定义在 `metadataContent` / `excelHeadInfo`
   两个 JSON 字符串里，提交时两个写同一份。
3. **列的唯一锚点是 `attributeFullName`** = `<实体全类名>.<字段名>`；
   **`displayName` 才是 Excel 表头**（可自定义）。
4. **`PageRequest` 是 `{pageInfo:{pageNumber,pageSize}, params:{...}}`**，
   不是 `{page, size}`（写错报 `BOOT_3000 message:null`）。

`delete` 必须传 `{"id": ...}`，裸 Long 报 `BOOT_4002`。

### 关联实体字段要展开成两层 levelPath（你截图那个下拉框）

页面上「创建人 ▸ 姓名 ▸ 编号/性别/工作电话…」的树形多选，数据结构是 **`levelPath` 两层**：

```jsonc
"levelPath": [
  ["<appName>", "<entityFullName>", "<entityCaption>",
   "<entityFullName>.<relField>", "<relFieldCaption>"],        // 第一层：本实体的关联字段
  ["<relApp>", "<relEntityFullName>", "<relEntityCaption>",
   "<relEntityFullName>.<subField>", "<subFieldCaption>"]      // 第二层：关联实体的子字段
]
```

**三个关键**：
1. `attributeFullName` 取**第二层**（关联实体的属性全名），
   如 `com.seeyon.organization.domain.core.entity.OrgMember.code`
2. `displayName` 用「本字段名/子字段名」：`创建人/编号`、`销售员/编号`
3. `entityType` 仍是 `MASTER_ENTITY`（**不是** `SUB_ENTITY`，那是子表）；
   `relation=NONE`、`relationApp=<关联应用，如 organization>`、`relationEntity=""`

实测：`郑杰验证实体` 有 5 个 ENTITY 字段（创建人/创建机构/创建部门/创建岗位/更新人），
各展开 4 个子字段（编号/姓名/手机号码/邮箱），36 列（20 列两层展开）。
`displayName` 形如「创建人/姓名」，页面能正常渲染。

```bash
python tools/core/setting/excel_template_entity_fields.py --i-have-write-authorization
```

## 二维码（QR Code Rule）

页面：**设置 → 二维码**。给实体的某个字段配一条规则。

```python
from components.udc.setting.qrcode_constraints import (
    build_qr_rule_body, validate_qr_rule_body,
    build_search_body, build_search_no_page_body)

body = build_qr_rule_body(app_id, app_guid, name="验收二维码规则",
                          entity_full_name=ENTITY_FULL_NAME,
                          type_="FIELDQRCODE", link_type="APP",
                          value_field_code="code")
errs = validate_qr_rule_body(body)
```

**两个枚举传字符串**（DB 存 ordinal）：

```
CtpQrCodeTypeEnum     BARCODE(0) / LINKQRCODE(1) / FIELDQRCODE(2) / QRCODE(3)
CtpQrCodeLinkTypeEnum APP(0) / CUSTOM(1)
```

**页面只提供三种**（下拉框实测，没有独立的 QRCODE）：

| 页面选项 | 枚举值 | DB type | 必填 |
|---|---|---|---|
| 字段二维码 | `FIELDQRCODE` | 2 | `valueFieldCode` |
| 条形码 | `BARCODE` | 0 | `valueFieldCode` |
| 链接二维码 | `LINKQRCODE` | 1 | `pcPagePath` 或 `mobilePagePath` |

三种类型 2026-10-21 全部实测落库（`BOOT_0000` + DB 回读 + search 复查）。

★ `valueFieldCode` = 实体字段的 `name`（如 `code`、`long_url`）。
★ `search` 返回的 `type` 是**枚举字符串**，DB 里才是 ordinal —— 写枚举读枚举，回读 DB 才是数字。

### ★★ 链接二维码：必须先选实体，页面值不能自己编

**这条是用户现场纠正的，别再犯。** 正确顺序：

```
1. 选 type = LINKQRCODE
   → 表单才长出「链接类型」「实体」「WEB端页面」「移动端页面」
2. 选实体（entityFullName）
   → WEB端页面 的候选**才按该实体过滤加载**出来
3. 从候选里选页面 → 平台写入 pc_page_path
4. 提交
```

**`pcPagePath` 存的是 `udc_page_info.page_url`**，不是 URL 路由、也不是 `udc_resource.code`：

```
页面手选「数据源配置信息列表页」→ 落库 pc_page_path = 'sjypzxxListPage'
```

页面候选查询：

```sql
SELECT id, page_url, caption, page_type, url_type
FROM udc_test2.udc_page_info
WHERE app_id = ?
  AND (master_entity_ids LIKE '%<实体全类名>%'
       OR include_entity_ids LIKE '%<实体全类名>%')
ORDER BY sort_no
```

⚠ `udc_page_info` **没有 `is_deleted` 列**（`udc_resource` 才有）。

```python
from components.udc.setting.qrcode_constraints import (
    build_page_candidate_query, build_page_candidate_query_by_url,
    validate_link_page_path)

sql, args = build_page_candidate_query(app_id, EFN)
# 或 build_page_candidate_query_by_url(app_id, "sjypzxx")
codes = {r["page_url"] for r in db.query(sql, args)}
errs = validate_link_page_path(body, codes)   # 非空就别发请求
```

校验器拦三类：**自编 URL（含 `://` 或 `/` 开头）、不在候选白名单、两个页面字段都空。**

**search 的坑**：`sort` 必须是 `null`，不能是 `{}`。

```
{pageInfo, paramsDto, sort:{}}    → BOOT_3000 message:null  ❌
{pageInfo, paramsDto, sort:null}  → BOOT_0000               ✅
search-no-page 只传 {paramsDto}，不要 sort key
```

name 限 50 字。

## 选项集（Option Set）—— 与枚举是两套独立表

**这是本域最容易搞错的一条**：

```
枚举    ctp_enum / ctp_enum_category / ctp_enum_item
        udcEnumCategoryPost / udcEnumPost / udcEnumItemPost
选项集  udc_enum / udc_enum_category / udc_enum_item
        udcUdcEnumCategoryPost / udcUdcEnumPost / udcUdcEnumItemPost
```

两套表 id **不互通**。把枚举当选项集提交，页面会显示 `_<appName>_<id>` 异常串。

```python
from components.udc.setting.option_set_constraints import (
    build_option_set_category_body, build_option_set_body, build_option_set_item_body,
    validate_option_set_category_body, validate_option_set_body,
    validate_option_set_item_body)

cat = build_option_set_category_body(app_id, app_guid, name="Grp", caption="分组", order_no=1)
opt = build_option_set_body(app_id, app_guid, name="MySet", caption="我的选项集",
                            category_id=CAT_ID)
itm = build_option_set_item_body(app_id, app_guid, enum_id=OPT_ID,
                                 name="ONE", caption="选项甲", code=1)
```

**必填与坑**：

| 位置 | 缺失/非法 | 报错 |
|---|---|---|
| 分组 | appId / caption / orderNo | `BOOT_1001` 应用ID、分类名称、排序号 |
| 选项集 | caption | `BOOT_1001 选项集名称 不能为空` |
| 选项集 | **name 首字母小写** | `UDC_ENUM_0001 编码只能由首字母大写的数字和字母的组合` |
| 选项项 | caption | `BOOT_1001 选项名称 不能为空`（报错说"名称"，实际是 caption） |
| 选项项 | code | `BOOT_1001 选项值 不能为null`（整数，不是字符串） |

选项项 **name=编码(英文) / caption=显示名(中文) / code=整数**，三个都不能少。

## 参数（Parameter）

落库表 `ctp_parameter_definition`（⚠ `app_id` 是 **varchar**，不是 bigint）。

```
operation   udcCtpParameterDefinitonPost / ...UpdatePost
            ★ Definiton 少一个 i —— 平台拼写错误，写成 Definition 会 FieldUndefined
读接口      udcCtpParameterDefinitonSearch / udcDataTypeDataTypesParamGet
```

```python
from components.udc.setting.parameter_constraints import (
    build_parameter_body, validate_parameter_body)

body = build_parameter_body(app_id, app_guid, name="p1", caption="参数一",
                            data_type="STRING", value="v", order_no=10)
errs = validate_parameter_body(body)
```

⚠ **`dataTypeProperties` 提交时必须是对象**：
`{"minLength":0,"maxLength":100}` ✅ / `'{"minLength":0}'` ❌
传字符串报 `BOOT_3002 属性dataTypeProperties的值反序列化为LinkedHashMap类型时失败`。

## 流水号（Serial Scheme）—— LIVE PASS

```
落库  ctp_serial_scheme / ctp_serial_section / ctp_serial_condition
写    udcSerialSchemeCreatePost / UpdatePost
删    udcSerialSchemeDeletePost      {appId, id} → content=1
读    udcSerialSchemeSearchPagePost / udcSerialSchemeMaxSortNumberAppGet
      udcSerialSchemeContextValueListGet / udcDesignMetadataAggEntityExcludeBootGet
```

**字段名必须反编译，不能猜**：

平台 GraphQL 层**不校验未知字段** —— 传 `zzzNotAField` 和传错字段名返回
**完全一样的**业务错 `BOOT_1001 流水号段 个数必须在1和12之间`。
我先试了 11 个候选键名全失败，只能反编译：

```
jar  /d/repo/CHIT/com/seeyon/boot-starter-serialnumber/5.3.318/
     boot-starter-serialnumber-5.3.318.jar
类   .../serialnumber/domain/dto/SerialSchemeDto.java
     .../serialnumber/domain/dto/SerialSectionDto.java
```

**关键字段名**：

```
段列表  serialSectionDtoList     ← 不是 sections / serialSections / serialSectionDtos
条件    serialConditionDtoList
```

**段 DTO 字段名和 DB 列名不一样**（写库后回读要用 DB 名）：

```
DTO size        ↔ DB section_size     ← 不是 sectionSize
DTO dateType    ↔ DB is_date_type     ← 不是 isDateType
DTO show        ↔ DB is_show
DTO flow        ↔ DB is_flow
DTO increase    ↔ DB is_increase
```

**五个枚举，传字符串**：

```
SerialTypeEnum      CONSTANT / CONTEXT / ENTITY / SERIAL   （段类型）
FillTypeEnum        LEFT / RIGHT / NONE
CutTypeEnum         LEFT / RIGHT / NONE
SerialResetRuleEnum NONE / YEAR / MONTH / DAY
SerialRuleTypeEnum  APP / BIG / SMALL                       （serialType 用这个！）
```

⚠ 两个坑：
1. `serialType` 用 **`SerialRuleTypeEnum`**（APP/BIG/SMALL），不是 `SerialTypeEnum`
2. **枚举语义会反转落库**：传 `NONE` 落成 `2`，真实样本里固定值段 `fill_type=0`（=LEFT）。
   **写库值是 ordinal，别拿 DB 数字反推语义。**

```python
from components.udc.setting.serial_constraints import (
    build_serial_section, build_serial_scheme_body, validate_serial_scheme_body)

secs = [
    build_serial_section(type_="CONSTANT", size=2, value="DD", section_rank=1),
    build_serial_section(type_="CONTEXT", size=8, value="currentDate", section_rank=2,
                         date_type=True, date_pattern="yyyyMMdd", flow=True),
    build_serial_section(type_="SERIAL", size=4, section_rank=3, flow=True,
                         start_value=1, end_value=9999),
]
body = build_serial_scheme_body(app_id, app_guid, code="ZxjOrderNo",
                                name="验收订单号", sections=secs, contain_flow=True)
errs = validate_serial_scheme_body(body)
```

**实测（LIVE PASS）**：探针 `ZXJ + currentDate(yyyyMMdd) + 4位自增` →
页面显示「规则组成: 常量:ZXJ 上下文字段:系统日期 流水号」「效果预览: ZXJ202610211」✅

完整 DTO 字段清单（九段式）、段类型语义表、未验证项见
`core/facts/udc/setting/serial/create.md`，契约见
`docs/operation-contracts/udc/setting/serial-contracts.md`。

### 方法论铁律（流水号这条是典型）

**先判「这个问题能不能靠猜解决」，再决定投入。**

```
传一个肯定不存在的字段  {appId: X, zzzNotAField: 123}
  → 报 UnknownField / 字段校验错  ⇒ 平台会校验，可以逐个试名字
  → 仍返回原来的业务错            ⇒ 未知字段被静默忽略，猜名这条路是死的
```

流水号就是第二种：11 个候选键名返回**逐字节相同**的报错，不存在「猜对了就变」的信号。
此时只剩两条路：抓一次真实 UI 提交，或 **CFR 反编译 Controller 读 DTO 字段名**（更可靠）。

跳过这一步就闷头枚举，会在一个**原理上不可猜**的问题上烧掉整轮预算。

## 自定义对象（DataTransferObject）

业务定位（设计器原文）：**「支持自定义对象，用于微流程/页面规则之间的相互调用数据传递」**。
落库表 `udc_data_transfer_object`（本应用 `8704025620829192834` 现有 4 个，均为被引用对象）。

### 接口

| 动作 | operation | 写 | 状态 |
|---|---|---|---|
| 创建 | `udcDataTransferObjectPost` | 是 | LIVE PASS |
| 更新 | `udcDataTransferObjectUpdatePost` | 是 | LIVE |
| 删除 | `udcDataTransferObjectDeletePost` | 是 | LIVE PASS（单条） |
| 列表 | **平台无查询 operation** | 否 | DB 直读 |

**必填槽位**（BOOT_1001 逐字段探针实测）：

```
appId   应用Id 不能为null
appGuid 取自 udc_application.guid（不是 appId）
caption 对象显示名称 不能为空
name    对象名称（编码）不能为空
source  source不能为空（BOOT_4101）
```

⚠ `name` 是编码（英文）、`caption` 是显示名（中文）——别对调。

```python
from components.udc.setting.custom_object_constraints import (
    build_custom_object_body, validate_custom_object_body,
    build_custom_object_delete_body, validate_custom_object_delete_body)

body = build_custom_object_body(app_id, app_guid, caption="显示名", name="objCode")
errs = validate_custom_object_body(body)   # 空 = 通过
```

### 平台"没有"的东西（已证实，别去补）

| 能力 | 状态 |
|---|---|
| 查询 operation | **VACUUM** —— 探测 40+ 候选全 `FieldUndefined` → 列表走 DB |
| 批量删除 operation | **VACUUM** → 只能逐个删（单条 body `{appId, id}`） |

### 删除三段式（唯一正确的顺序）

```bash
# ① 预检：全量备份 + 阳性对照 + 四种引用形式全查 → 产出 candidates
python tools/core/setting/custom_object_delete_precheck.py
#    → <HERMES_HOME>\backups\custom-object-delete-<ts>\
#        udc_data_transfer_object.json   （全量行备份，可还原）
#        precheck.json                  （referenced / candidates + 对照结果）

# ② 批量删：只删 precheck.json 里 candidates 的 id，逐个发 + 逐个回读
python tools/core/setting/custom_object_delete_batch.py \
    --precheck <...>/precheck.json --port 9231 --i-have-write-authorization
#    进度写 <...>/progress.json，中断可续（已删的跳过）；失败即停
```

**引用分析（闸门本体）**：

```bash
python tools/core/setting/custom_object_reference_analysis.py --app-id <appId>
```

工具先做**阳性对照**（用已知被引用的实体名验证检测方法），对照不通过则退出码非 0，
此时"无引用"结论不可信。

**四种引用形式全查**：`name` / `caption` / `id` / `guid`。
只查文本（name/caption）会漏 id 形式——2026-10-20 那轮就漏了 4 个，
20 号的"224 个无引用"在补 id/guid 后是 223 个。

### 删除的两条硬经验

1. **删除成功码不可信**：缺 `id` 时平台仍回 `BOOT_0000` 但 `content=0`。
   判据只能是「DB 回读该 id 已不存在」，不是 `code=BOOT_0000`。
2. **页面列表有前端缓存**：接口删完后，设计器「设置 → 自定义对象」表格可能仍显示旧行
   （用户实际遇到：DB 只剩 6 行，页面还显示 229 个）。
   验收必须 DB 回读；页面验证要切 tab / 刷新后才可信。

### 页面验证（antd tab 的正确点法）

```javascript
// ① tab 要点 .ant-tabs-tab 本体，点内部 div/span 无效
const t = [...document.querySelectorAll('.ant-tabs-tab')]
           .find(e => (e.textContent||'').trim() === '自定义对象');
t.dispatchEvent(new MouseEvent('mousedown', {bubbles: true})); t.click();

// ② 读完所有可见 pane 里的表格，别只读第一个 table（页面上有多个 tab 的 DOM 同时存在）
[...document.querySelectorAll('.ant-tabs-tabpane')]
  .filter(p => p.offsetParent !== null)
  .flatMap(p => [...p.querySelectorAll('table')])
  .map(t => ({head: [...t.querySelectorAll('thead th')].map(x => x.innerText.trim()),
              rows: [...t.querySelectorAll('tbody tr')].map(tr =>
                      [...tr.querySelectorAll('td')].map(td => td.innerText.trim()).join(' | '))}));
```

自定义对象表格的列是「对象名称 | 对象编码 | 操作」。

### 判定口径（2026-10-21 修正）

**"无引用 ≠ 可删"仍然成立**，但也不等于"永远不删"：
- 2026-10-20 判定 223 个是"应用包导入的设计资产"→ 保留（当时结论）。
- 2026-10-21 用户明确指令「删除吧」→ 全量备份后逐个删，223 条全部 `BOOT_0000` + 回读消失，对象数 229→6，0 失败。
- 删除后复跑引用分析：707 个引用源里没有新增悬空引用，说明这批确实零引用。

结论纪律：**删除动作取决于用户授权，不取决于脚本的"无引用"结论**；
脚本的职责是把"引用面 + 阳性对照 + 全量备份"摆出来，让人有据可决。

### 字段组装（12 类数据类型）—— 另一个端点，别混

**对象本身**用 `udcDataTransferObject{Post,UpdatePost,DeletePost}`；
**对象的字段**用 `udcDataTransferObjectUpdateDtoPost`。这两个不是一回事：

- 往 `UpdatePost` 的 body 塞 `attributes` 会返回 `BOOT_0000` 但**字段零落库**（假成功，实测 8 个 key 全中招）。
- 字段的真实端点是 `udcDataTransferObjectUpdateDtoPost`（抓包实证）。
- `attributes` 是**全量替换**：传空数组报 `参数错误`，传部分会删掉未列出的字段。
  正确姿势：`SelectDtoGet` 拉全文 → append → 整体回传。

两个枚举只有两个值（踩过才知道）：

```
dataTypeCategory = PRIMITIVE | COMPOSITE | ENUM    ← 三个值
type             = OBJECT    | LIST               ← 两个值
```

12 类组装矩阵、6 个候选接口、完整 attribute 结构见
`core/facts/udc/setting/custom-object/fields.md`。

**5 个根分支的形态各不相同，必须逐分支对照**：

```
基本类型    dataType=STRING/INTEGER/…    cat=PRIMITIVE  无关联
枚举        dataType=CTPENUM             cat=PRIMITIVE  relApp=<应用名>  relEnt=<ctp_enum id>
选项集·本应用 dataType=<选项集id>          cat=ENUM       relApp=<appId>   relEnt=<udc_enum id>
选项集·BPM   dataType=<Java全类名>         cat=ENUM       relApp=bpm       relEnt="" 或残值
对象·单个    dataType=<DTO全类名>          cat=COMPOSITE  relApp=<appId>   relEnt=""     ← 空串！
对象·列表    dataType=<DTO全类名>          cat=COMPOSITE  relApp=<appId>   relEnt=<实体id> ← 要 id！
关联实体     dataType=ENTITY              cat=PRIMITIVE  relApp=<appId|bpm|organization>
```

⚠ `ctp_enum`（枚举）和 `udc_enum`（选项集）是**两套独立表**，id 不互通。

**方法论铁律**：候选树每个根分支的组装形态都不同，**只拿一个样本下结论会把整片分支做错**。
正确做法是每个根分支各手选一次、抓平台真实 body，再据此写组装器——
这条已写进 `fields.md` 第零节（本轮 4 个规则都是这么被纠正的）。

```bash
# 只读拉候选
python tools/core/setting/custom_object_relation_fields.py --mode dump
# 组装 4 类关系字段（枚举/选项集/对象/对象列表/关联实体）
python tools/core/setting/custom_object_relation_fields.py --mode build --i-have-write-authorization
```

### 操作探测的判据（枚举域教训复用）

URL 里的 operation 名**不参与** GraphQL 字段解析 → 「Invalid Syntax」对所有候选都出现。
正确判据是 `FieldUndefined: Field '<op>' in type 'Mutation'` ⇒ 该字段不存在。

### 删除成功码不可信

缺 `id` 时平台仍回 `BOOT_0000` 但 `content=0`。必须回读 DB 核对。

## 枚举（当前完全打通）

### 三类资产的位置（不要混放）

| 类别 | 位置 | 内容 |
|---|---|---|
| **脚本/实现** | `components/udc/setting/enum_*.py` | 构造器、校验器、引用分析器 |
| **事实** | `core/facts/udc/setting/enum/` | `create.md`（九段式事实格）、`enum-write-chain.md`（写链+错误字典+踩坑） |
| **操作契约** | `docs/operation-contracts/udc/setting/enum-contracts.md` | 6 条 operation 契约 |
| **操作脚本** | `tools/core/setting/` | 实际执行用脚本 |
| **skill** | 本文件 | 宿主侧使用说明 |

### 平台接口（全部 GraphQL，路径 `POST /service/udc/graphql?<operation>`）

| 动作 | operation | 落库表 |
|---|---|---|
| 分组新建 | `udcEnumCategoryPost` | `ctp_enum_category` |
| 枚举新建 | `udcEnumPost` | `ctp_enum` |
| 枚举项新建 | `udcEnumItemPost` | `ctp_enum_item` |
| 枚举批量删除 | `udcEnumBatchDeletePost` | 逻辑删除（`is_delete=1`） |
| 枚举列表 | `udcEnumSearchNoPagePost` | — |
| 分组列表 | `udcEnumCategorySearch` | — |

**body 形态**（不是 REST JSON，是 GraphQL query）：

```jsonc
{
  "query": "mutation graphqlLoader ($params0: udcEnumPostInputBody) { \n  data0: udcEnumPost(body: $params0) { code data { content } message status } }",
  "variables": { "params0": { /* 真正的 body */ } }
}
```

**必填槽位**（漏了会被 BOOT_1001 拦下，报错文案有误导性）：

```
分组    name(i18n JSON) / orderNo / appGuid / appId / hostAppName / dataStatus
枚举    name(i18n JSON) / code / orderNo / categoryId / appGuid / appId /
        hostAppName / dataStatus / bizType / expansible / enable / enumType / children
枚举项  appId / enumId / enumCode / name(i18n JSON) / itemValue / parentId /
        itemLevel / leaf / enable / orderNo / appGuid / hostAppName / dataStatus
```

三个最容易踩的：

1. `name` 必须是 `{"zh_CN":"显示名"}` 的 **JSON 字符串**。传裸文本报「枚举编码 不能为空」——报错说编码，实缺 i18n 形态。
2. 枚举项的值槽位是 **`itemValue`**（字符串），不是 `code`（整数）。
3. 顶层枚举项 `parentId` 必须是 `"0"`，缺了报「上级枚举项ID 不能为null」。

### 用 seeyon-agent 的正确姿势

```python
from components.construction.metadata_artifacts import (
    build_enum_body, build_enum_category_body, build_enum_item_body)
from components.udc.setting.enum_constraints import (
    validate_enum_body, validate_enum_category_body, validate_enum_item_body)

body = build_enum_body(app_id, caption="验收枚举", name="zxjAcceptEnum",
                       order_no=10, category_id=GROUP_ID, app_guid=APP_GUID)
errs = validate_enum_body(body)     # 空 = 通过；有错就别提交
```

**本地校验先跑，再提交**——平台 `checkSchema` 是浅校验（只查必填，不查值域语义），
本地校验器才是真正的闸门。

### 删除枚举前必做引用分析

```python
from components.udc.setting.enum_reference_analysis import classify, enum_ref_values
```

⚠ **载体搞错过一次**（2026-10-20）：页面 schema 在 `udc_page_schema` 表，
**不是** `udc_page_info`。查错表会得到「页面 0 命中」的假结论。

权威载体是参数 JSON 里的 `ctpEnumInfo` 块：

```json
{"ctpEnumInfo": {"id": "<枚举id>", "code": "<枚举code>", "appId": "...", ...}}
```

引用源：实体属性（`udc_attribute.data_type='CTPENUM'`）、页面（`udc_page_schema`）、
资源（`udc_resource`）、导出模板（`ctp_excel_export_template`）、微流程（`udc_microflow_info`）。

**四条必守判据**：

1. 载体要对
2. 阳性对照（能检出实体属性在用的枚举）——检不出则结论不可信
3. 阴性对照（不存在的枚举不得被检出）——防 code=`bool` 命中 `"boolean"`
4. 引用方有效性（`is_deleted=1` 的引用方不算活引用）

有活引用的枚举**绝对不能删**——删了产生悬空引用，表现为后端代码生成编译失败。

### 写操作授权

写面必须显式传 `WriteScope`（应用白名单 + 操作白名单 + 次数上限），
默认 fail-closed。失败即停，不重试。见 `components/platform_operations/write_scope.py`。

## 平台机制

- **表名易混**：分组落 `ctp_enum_category`（不是 `udc_enum_category`）；枚举落 `ctp_enum`（不是 `udc_enum`）。
- **逻辑删除**：`is_delete=1`，物理行仍在。回读统计必须 `is_delete=0` 过滤。
- **删除接口偶发误报**：`BOOT_4000 数据库错误` 但数据实际已生效。回读确认，勿重发。
- **输入法拼音中间态**：自动化填编码框用「set('')→set(v)」两步法会提交拼音串
  （想填 `zxjUiTraceEnum`，实际变 `UIguijimeiju`），平台**不报错**直接落库。
  编码框只填英文/数字；落库后回读 `ctp_enum.code` 核对。

## 完整细节

`core/facts/udc/setting/enum/enum-write-chain.md`（请求体全文、错误字典、踩坑清单、作废声明）

### ★ 18 种字段类型 × 能力矩阵（2026-10-21 全量实测 18/18）

`udcDataTypeDataTypesByAppIdAppGet` 实拉 18 种：

```
基础   STRING / MULTILINESTRING / INTEGER / BIGINTEGER / DECIMAL / CURRENCY
       DATE / TIME / DATETIME / BOOLEAN
关联   ENUM / CTPENUM / ATTACHMENT / ENTITY
自定义 DOCUMENTNUMBER / Serial / OPINION / CONTENT   （custom=true，base 指向基础类型）
```

**各类型的额外必填（踩过的坑）**：

| 类型 | 额外必填 | 错误码 |
|---|---|---|
| `CTPENUM` | `relationEntity`=枚举id、`relationApp`=appId | `UDC_DATATYPE_0015` |
| `ENUM` | 同上，指向 `udc_enum` | `BOOT_3000` |
| `ENTITY` | `relationEntity`=实体全类名、`relationApp`=应用名、`relationEntityCategory=ENTITY` | `UDC_DATATYPE_0017` |
| `Serial` | `serialNumberName` + `serialNumberCode` + `serialNumberGuid` | `UDC_ATTR_0019` |
| `DECIMAL`/`CURRENCY` | **`maxLength`（总精度）+ `decimalDigits`** | `UDC_DATATYPE_0006` |

⚠ **DECIMAL 精度靠 `maxLength` 表达，不是 `maxValue`** —— 传 `maxValue` 会被当成精度校验
（报「最大值取值太大，允许的最大值为38」）。真实样本 `max_length`=20/22/24。

⚠ **字段编码规则 `UDC_ENTITY_0026`**：只能字母/数字/下划线，必须以**字母开头**、
不能以下划线结尾、不能含中文（页面会自动转拼音）。

### ★ 字段级配置项全量实测 20/20

| 配置项 | 传参 | 落库列 |
|---|---|---|
| 必填 | `notNull=true` | `is_not_null` |
| 唯一 | `uniqueness=true` | `uniqueness` |
| 多选 | `multiSelect=true`（需关联） | `multi_select` |
| 审计 | `auditLog=true` | `audit_log` |
| 全文检索 | `searchable=true` | `searchable` |
| 长度 | `minLength`/`maxLength` | `min_length`/`max_length` |
| 精度 | `decimalDigits` + `maxLength` | `decimal_digits` |
| 默认值-固定 | `defaultValue` | `default_value` |
| 默认值-系统变量 | `defaultValueIsChange=false` + `defaultValueSystemVariable` | `default_value_sys_variable` |
| 描述 | `description` | `description` |
| 正则校验 | `dataFormat` + `patternMessage` | `data_format`/`pattern_message` |
| 加密 | `enableEncryption=true` + `encryption` | `encryption` |
| 脱敏 | `enableDesensitization=true` + `desensitization` | `desensitization` |
| 敏感词 | `enableSensitiveWordCheck=true` | `enable_sensitive_word_check` |
| 控件 | `widgetConfig`（JSON 字符串） | `widget_config` |

**两个枚举必须反编译读，别猜**（反编译 boot-core 5.3.358）：

```java
EncryptionType   NOT_ENCRYPTION(0) / REVERSIBLE_ENCRYPTION(1) / DECRYPT_ONLY(2)
MaskType         None(-1) / Auto(0) / All(1) / Custom(2)
```

猜 `AES`/`MD5`/`FULL` 全报 `BOOT_3002 No enum constant ...`。

`widgetConfig` 是 **JSON 字符串**：`{"pc":"Input","mobile":"Input","list":true,"detail":true,"quickSearch":true}`，
`pc`/`mobile` 可换 `Input`/`InputNumber`/`TextArea`/`Select`（实测都通过）。

### 扩展实体只支持 10 种基础类型

```
STRING / MULTILINESTRING / INTEGER / BIGINTEGER / DECIMAL / CURRENCY
DATE / TIME / DATETIME / BOOLEAN
```

关联型/自定义型（CTPENUM/ENUM/ENTITY/ATTACHMENT/DOCUMENTNUMBER/Serial/OPINION/CONTENT）
**不适用** —— 扩展实体要落成物理列，关联型没有物理列形态。

`dataTypeProperties` 是字符串化 JSON，且 `minLength` 用字符串、`maxLength` 用数字：

```json
{"minLength":"0","maxLength":50}          STRING
{"min":"0","max":"9999"}                  INTEGER
{"min":"0","max":"99999","decimalDigits":"2"}   DECIMAL
```

### 可复用脚本

```bash
# 18 种类型全量实测
python tools/core/setting/attribute_set_type_matrix.py --run --set-id <id> --prefix tq \
    --with-capabilities --ctp-enum-id <eid> --enum-id <oid> \
    --entity-full-name <efn> --serial-name <n> --serial-code <c> --serial-guid <g> \
    --i-have-write-authorization

# 20 项字段配置实测
python tools/core/setting/attribute_set_field_config.py --run --set-id <id> \
    --prefix cfg --ctp-enum-id <eid> --i-have-write-authorization

# 扩展实体 10 种类型
python tools/core/setting/scalability_type_matrix.py --run --option-id <oid> \
    --prefix sy --i-have-write-authorization
```

### ★ 表达式字段（calculate=COMPUTE）：三段链 + runtime 写不进去

**仓库已有完整事实**：`core/facts/udc/write-chain/expression-token-type-domain.md`
+ `components/udc/attribute_expression_constraints.py`（131 个系统变量、兼容表、错误码全在）

```
1) POST /service/udc/expression/schema
   {"ids":["<实体id>"], "paramType":"ENTITY", "upsource":true, "serverName":"udc"}
   ★ 不能带 appId（带上就 BOOT_3000）
2) POST /service/udc/expression/check      同 schema 结构 → true
3) POST /service/udc/expression/transform  → {designData, runtimeData}
4) 落库 POST /service/udc/entity/attribute/update（REST，不是 GraphQL）
   body = GET /service/udc/entity/attribute/{id} 的完整 DTO 改后整体回传
```

**设计态 `expressionRuntimeData` 会被拒**（实测 7 种形态全试）：

```
null / ""                 → BOOT_0000 ✅
{} / {"a":1} / {"executableExpr":"x"} / 带 base64 的  → BOOT_3000 ❌
```

⇒ 该字段只接受空值，值由**代码生成阶段**服务端写入。
客户端只写 `expressionDesignData` + `calculate=COMPUTE`。

**token 形状**（`type` 恰 5 值：CONSTANT/VARIABLE/SYSTEM/FUNCTION/OPERATOR）：

```python
{"uid":"t1","type":"SYSTEM","value":"system.currentDateTime","desc":"系统日期时间"}
{"type":"FUNCTION","value":"concat","subOps":[[{...}],[{...}]]}
```

⚠ `designData` 必须含 `context` 键（空也要 `[]`），否则检测器 NPE 导致全局检测 FAIL。

```bash
python tools/core/setting/attribute_expression_build.py --list    # 看预设方案
python tools/core/setting/attribute_expression_build.py --run \
    --set-id <id> --field-name txtCompute --plan sys_datetime \
    --i-have-write-authorization
```

### ★★ 表达式组件（「默认值 +」→「高级模式」）—— 三条接口 + 两种 sysvar 格式

**入口**：字段集右侧「默认值」输入框旁的 **`+` 号**（hover 才显现）→ Popover
「系统变量 / 高级模式」→ 点 BUTTON「高级模式」→ 表达式设置对话框。

⚠ 那个 `+` 必须用 CDP 真实鼠标（`Input.dispatchMouseEvent`）先 mouseMoved 再 click；
JS `.click()` 和合成事件都不生效。rea 在这个页面会 timeout。

**组件并发三个接口**：

```bash
POST /service/udc/expression/operator/list    # 运算符（本字段实测返回空数组）
POST /service/udc/expression/schema           # 变量 schema
POST /service/udc/expression/preset/list      # 变量树 + 函数树
```

`schema` 真实 body（★ 与旧文档不同，**三个数组都要**，且带 appId）：

```json
{"appId":"<appId>","extension":"","ids":[],"idsStr":[],"idsTuple":[],
 "paramType":"CONFIG_PARAM"}
```

`preset/list` body：`{"terminalSupportType":"BACKEND"}`

产出：`presetVariableInfo`（**131 项 / 4 组**：organization 95 / date 33 / env 2 / plugin 1）
+ `functionInfo`（**88 个 / 8 组**：基础15 日期24 数学10 文本17 条件1 聚合18 变化1 枚举2）

```bash
python tools/core/setting/expression_component_probe.py --all
python tools/core/setting/expression_component_probe.py --schema CONFIG_PARAM
```

### ★★ defaultValueSystemVariable 有两种格式，传错就白屏

| 写入内容 | 后果 |
|---|---|
| 纯文本 `"currentUser"` | ❌ 前端 `JSON.parse` 崩 → **整个字段集面板白屏** |
| 格式 A（单 token） | ❌ 字段集 STRING 字段报 `UDC_ATTR_0010` 类型不匹配 |
| 格式 B（ExpressionSaveDto） | ✅ **BOOT_0000 落库成功** |

```python
from components.udc.setting.attribute_set_constraints import (
    build_sysvar_token,              # 格式 A：真实业务字段用
    build_sysvar_expression_dto,     # 格式 B：字段集用（实测成功）
    validate_sysvar)                 # 两者都认，纯文本直接拦

dto = build_sysvar_expression_dto("currentUserId")
# {"resultTypeInfo":"ENTITY","schemas":[],
#  "tokens":[{"value":"system.currentUserId","desc":"登录人员ID",
#             "type":"SYSTEM","uid":"<uuid>"}],
#  "isMultiSelect":false,"terminalSupportType":"BACKEND"}
```

**铁律**：写完必须跑 `validate_sysvar()`。多花 10 秒确认 JSON 合法，
否则前端白屏、整块面板不可用（2026-10-21 实际踩过一次）。

### ★★ widgetConfig 按 dataType 给（全部 Input 是错的）

真实对照（全库按类型分组统计众数）：

| dataType | pc | mobile |
|---|---|---|
| `STRING` | `Input` | `Input` |
| `MULTILINESTRING` | `TextArea` | `TextArea` |
| `INTEGER` | `InputNumber` | `InputNumber` |
| **`BIGINTEGER`** | **`Input`** | **`Input`** |
| `DECIMAL` | `InputNumber` | `InputNumber` |
| `CURRENCY` | `Currency` | `Currency` |
| `DATE` | `DatePicker` | **`DateTimePicker`** |
| `TIME` | `TimePicker` | `TimePicker` |
| `DATETIME` | `DatePicker` | **`DateTimePicker`** |
| `BOOLEAN` | `Switch` | `Switch` |
| `ENUM` | `TreeSelect` | **`CascaderSelect`** |
| `CTPENUM` | `TreeSelect` | **`CascaderSelect`** |
| `ENTITY` | `UdcReference` | `UdcReference` |
| `ATTACHMENT` | `Attachment` | **`Upload`** |
| `CONTENT` | `UiBusinessContent` | `UiBusinessContent` |
| `DOCUMENTNUMBER`/`Serial`/`OPINION` | `Input` | `Input` |

**四个反直觉点**：
1. `BIGINTEGER` 用 `Input`（大整数超 JS 安全范围），不是 `InputNumber`
2. PC 与移动端常不同：DATE/DATETIME（DatePicker vs DateTimePicker）、
   ENUM/CTPENUM（TreeSelect vs CascaderSelect）、ATTACHMENT（Attachment vs Upload）
3. `CURRENCY` 有专属控件 `Currency`
4. `CONTENT` 用 `UiBusinessContent`（正文编辑器）

```python
from components.udc.setting.attribute_set_constraints import (
    DEFAULT_WIDGETS, build_widget_config)
build_widget_config("DATE")   # {"pc":"DatePicker","mobile":"DateTimePicker",...}
build_attribute_field_body(...)  # 已自动按 dataType 选
```

```bash
python tools/core/setting/attribute_widget_fix.py --dump --set-id <id>       # 查差异
python tools/core/setting/attribute_widget_fix.py --fix-all --set-id <id> \
    --i-have-write-authorization
```

⚠ 修 widgetConfig 的 UpdatePost 必须同时把 `expressionRuntimeData` 置 null（否则 BOOT_3000）。
