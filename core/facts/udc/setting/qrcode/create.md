# 设置域 · 二维码（QR Code Rule）

> 前置：本文所有 `udc*Post` 必填的 `appGuid`，取法见 [`precondition-appguid.md`](../precondition-appguid.md)（用 `udcApplicationDetailGet` 接口查，appGuid ≠ appId，无需查库）。
> 版本：`boot-starter-qrcode-5.3.262`
> 证据等级：**LIVE PASS**（三种类型全实测；链接二维码经「页面手选对照」修正过一轮）
> 实现：`components/udc/setting/qrcode_constraints.py`

## R-E1 Capability

给某实体的某个字段配一条二维码规则 —— 扫出来的码里装字段值，或跳转到应用内页面。

页面下拉框**只提供三种**：

```
字段二维码  FIELDQRCODE   码里装实体某字段的值
条形码      BARCODE       一维条码，装字段值
链接二维码  LINKQRCODE    跳转到应用内页面
```

⚠ `QRCODE(3)` 在枚举里有值但**页面 UI 不给选**，登记为 VACUUM，不对外视为支持。

## R-E2 Version / 协议

**REST，不是 GraphQL**。前缀 `/service/udc/qrcode-rule/*`。
实现不在 udc 构件里 —— 在 `boot-starter-qrcode-5.3.262.jar`
（`CtpQrCodeRuleController`）。

```
POST /service/udc/qrcode-rule/create            新建
POST /service/udc/qrcode-rule/update            更新
POST /service/udc/qrcode-rule/update-fieldcode  只改字段
POST /service/udc/qrcode-rule/update-implement  改实现
POST /service/udc/qrcode-rule/delete            删除（body {"id": ...}）
POST /service/udc/qrcode-rule/batch-delete      批量删（body {"ids": [...]}）
POST /service/udc/qrcode-rule/physical-delete   物理删除
POST /service/udc/qrcode-rule/deactivate        停用
POST /service/udc/qrcode-rule/start-using       启用
POST /service/udc/qrcode-rule/search            分页（3 个 @MultiRequestBody）
POST /service/udc/qrcode-rule/search-no-page    不分页（2 个 @MultiRequestBody）
GET  /service/udc/qrcode-rule/{id}              按 id 查
GET  /service/udc/qrcode-rule/detail/{guid}     按 guid 查
POST /service/udc/qrcode-rule/search-for-design-drop-down-list
```

## R-E3 Input

### CtpQrCodeRuleDesignDto（反编译原文）

```java
Long    id
String  name                 // @NotBlank @Size(max=50)
CtpQrCodeTypeEnum type
CtpQrCodeLinkTypeEnum linkType
Long    appGuid = null
Long    appId = null
String  entityFullName       // 实体全类名
String  valueFieldCode       // 字段码/条码：取哪个字段
String  pcPagePath           // 链接码：页面 page_url
String  mobilePagePath
```

### 两个枚举（**API 传字符串，DB 存 ordinal**）

```java
CtpQrCodeTypeEnum     BARCODE(0) / LINKQRCODE(1) / FIELDQRCODE(2) / QRCODE(3)
CtpQrCodeLinkTypeEnum APP(0) / CUSTOM(1)
```

### 三种类型各自的必填

| 页面选项 | type | 必填 | 应留空 |
|---|---|---|---|
| 字段二维码 | `FIELDQRCODE` | `valueFieldCode` | pc/mobilePagePath |
| 条形码 | `BARCODE` | `valueFieldCode` | pc/mobilePagePath |
| 链接二维码 | `LINKQRCODE` | `pcPagePath` 或 `mobilePagePath` | valueFieldCode |

## R-E4 Required（错误字典）

| 缺失/非法 | 报错 |
|---|---|
| name | `BOOT_1001` 规则名称不能为空 |
| name 超 50 | `@Size(max=50)` 个数必须在1到50之间 |
| type / appId | 前端必填红字 |
| `FIELDQRCODE`/`BARCODE` 缺 valueFieldCode | 必填未填 |
| `LINKQRCODE` 缺页面 | 必填未填 |

## R-E5 Execution —— 链接二维码必须先选实体

**这一步不能跳，也不能自己编 URL。** 用户 2026-10-21 现场纠正：

```
1. 选 type = LINKQRCODE
   → 表单才长出「链接类型」「实体」「WEB端页面」「移动端页面」
2. 选实体（entityFullName）
   → WEB端页面 的候选才按该实体过滤加载出来
   → 候选 = 该实体绑定的页面
3. 从候选里选页面 → 平台写入 pc_page_path
4. POST create
```

**`pcPagePath` 存的是 `udc_page_info.page_url`**，不是 URL 路由、也不是 `udc_resource.code`：

```
页面手选「数据源配置信息列表页」
  → 落库 pc_page_path = 'sjypzxxListPage'
  → 该值 = udc_page_info.page_url
```

### 页面候选查询（权威口径）

```sql
SELECT id, page_url, caption, page_type, url_type
FROM udc_test2.udc_page_info
WHERE app_id = ?
  AND (master_entity_ids LIKE '%<实体全类名>%'
       OR include_entity_ids LIKE '%<实体全类名>%')
ORDER BY sort_no
```

⚠ `udc_page_info` **没有 `is_deleted` 列**（`udc_resource` 才有）。
备用查法（实体名拼音缩写）：`page_url LIKE '%sjypzxx%'`。

实测该实体候选 3 个：

```
sjypzxxListPage        数据源配置信息列表页              SEARCH_LIST
sjypzxxListPagecopy    数据源配置信息列表弹窗选择页面      SEARCH_LIST
sjypzxxDetailPage      数据源配置信息详情页              DETAIL
```

### 字段二维码 / 条形码

```
1. 取实体全类名（com.seeyon.<appName>.domain.entity.<Name>）
2. valueFieldCode = 该实体某属性的 name（如 code / long_url）
3. POST create
```

## R-E6 Side Effects

写 `ctp_qr_code_rule`（一条规则一行），`is_active=1`、`release_state=0`、`is_delete=0`。

```
id / create_time / update_time / version / guid
is_active / app_guid / app_id / code / create_id / is_delete
entity_full_name / field_code / mobile_page_path / name / pc_page_path
release_state / type / update_id / value_field_code / logo_file_id
original_id / link_type
```

DB 里 `type` / `link_type` 是 ordinal；`search` 回读返回枚举字符串。

## R-E7 Constraints

- `name` ≤ 50 字
- `type` / `linkType` 传**字符串枚举**
- `valueFieldCode` 必须是该实体真实存在的属性 `name`
- `pcPagePath` / `mobilePagePath` 必须是该实体页面候选里的 `page_url`，**禁止自编 URL 路由**
- `search` 的 `sort` 必须是 `null`（传 `{}` 报 `BOOT_3000 message:null`）
- `search-no-page` 只传 `{"paramsDto":{...}}`，不要 sort key
- `delete` 传 `{"id": ...}`（`@MultiRequestBody Long id`）

## R-E8 Evidence

```
反编译  /d/repo/CHIT/com/seeyon/boot-starter-qrcode/5.3.262/boot-starter-qrcode-5.3.262.jar
        → CtpQrCodeRuleController / CtpQrCodeRuleDesignDto / 两个枚举
抓包    performance.getEntriesByType('resource') 拿 tab 加载请求（确认 REST 前缀）
页面手选 2026-10-21 15:01 用户在弹窗里「选实体 → 选页面 → 确定」
        → SELECT * FROM udc_test2.ctp_qr_code_rule WHERE name='ZxjLinkQrUi'
        → pc_page_path='sjypzxxListPage'
        → 对照出我此前自编 URL 的错误（原来写 /main/portal/<appId>）
DB 回读 三类各一条，type/link_type/value_field_code/pc_page_path 全部符合
search  search-no-page 复查多条全在，type 返回枚举字符串
```

## R-E9 Verified

| 项 | 状态 | 证据 |
|---|---|---|
| 字段二维码 `FIELDQRCODE` | **LIVE PASS** | id=8848545734030393997，type=2，value_field_code='code' |
| 条形码 `BARCODE` | **LIVE PASS** | id=6879767127262436641，type=0，value_field_code='code' |
| 链接二维码 `LINKQRCODE` | **LIVE PASS** | id=-848036747914238368，type=1，pc_page_path='sjypzxxListPage'（与页面手选同值） |
| 页面候选 = `udc_page_info.page_url` | **LIVE PASS** | 页面手选值与 DB 落库值逐字相同 |
| `search` / `search-no-page` | **LIVE PASS** | sort 必须 null |
| `delete` `{"id":...}` | **LIVE PASS** | content=1，回读消失 |
| `update` / `update-fieldcode` / `update-implement` | **UNVERIFIED** | 端点存在（反编译），未实测 |
| `linkType=CUSTOM` | **UNVERIFIED** | 只验了 APP |
| `QRCODE(3)` | **VACUUM** | 枚举有值，页面 UI 不给选 |
| `logo_file_id` 嵌入 | **UNVERIFIED** | 上传链路未验 |
| 运行时生成码（`ctp_qr_code`） | **UNVERIFIED** | 需实体数据 |
| `field_code` 与 `value_field_code` 的区别 | **UNVERIFIED** | 只传后者，前者落 null |

## 待删除清单（清理时处理）

| 对象 | 判定依据 | 处置 | 状态 |
|---|---|---|---|
| `链接二维码-验收`（id=5906812661751892366） | `pc_page_path` 是自编 URL `/main/portal/<appId>`，不是页面 `page_url` | 删 | **DONE 2026-10-21**（content=1，回读消失） |

## 可用构造器

```python
from components.udc.setting.qrcode_constraints import (
    build_qr_rule_body, validate_qr_rule_body, validate_link_page_path,
    build_page_candidate_query, build_page_candidate_query_by_url,
    build_search_body, build_search_no_page_body)

# 字段二维码 / 条形码
b1 = build_qr_rule_body(app_id, app_guid, name="字段码", entity_full_name=EFN,
                        type_="FIELDQRCODE", value_field_code="code")

# 链接二维码（必须先查候选，禁止自编 URL）
sql, args = build_page_candidate_query(app_id, EFN)
# 或 build_page_candidate_query_by_url(app_id, "sjypzxx")
codes = {r["page_url"] for r in db.query(sql, args)}
b2 = build_qr_rule_body(app_id, app_guid, name="链接码", entity_full_name=EFN,
                        type_="LINKQRCODE", pc_page_path="sjypzxxListPage")
errs = validate_qr_rule_body(b2) + validate_link_page_path(b2, codes)
# errs 非空就别发请求
```

校验器拦三类：

```
① 形态：含 :// 或以 / 开头 → 判为自编 URL
② 白名单：不在 allowed_codes 里 → 判为不在该实体候选内
③ 必填：LINKQRCODE 既无 pcPagePath 也无 mobilePagePath
```
