# 实体设计器 参照/事件/索引 tab —— GraphQL 写入面（e6）

> 状态：**三类全 LIVE PASS**（2026-10-23，实验数据全部复原，实体回 10 条基线）
> 证据：GraphQL LIVE 实测 + 带外 CFR（`udc-common`/`udc-plugin-api`/`udc-biz`/`udc-web` 5.3.517，jar 在 `<MAVEN_REPO>`）

## 1. 事件 tab（udcEvent*）

| 动作 | op | 关键点 |
|---|---|---|
| 建 | `udcEventPost` (mutation, body) | 实体事件最小集见下 |
| 详情 | `udcEventGet` (query, path `{appId,id}`) | 回读 source/actionType/triggerType 全一致 |
| 列表 | `udcEventListPost` (mutation, body) | **sourceId 过滤不生效**（返回全应用 49 条），精确校验用 Get |
| 删 | `udcEventDeletePost` (mutation, body `{appId,id}`) | BOOT_0000 |

实体事件最小 body（LIVE 通过）：
```jsonc
{"name":"evProbe1","caption":"…","appId":…,
 "source":"ENTITY","sourceId":<实体id>,"type":"ENTITY_EVENT","actionType":"CREATE",
 "triggerType":"AFTER","enabled":true,"eventDataType":"OBJECT","eventData":<实体id>,
 "eventDataFullName":"<entityFullName>","numberFiredOnce":"1"}
```
坑：
- `actionType` 合法值是 **CREATE**（INSERT/ADD/SAVE/NEW 全被 `EventActionTypeEnum` 拒）
- 缺 `eventData` → `BOOT_4101 event_data不能为空`（错误信息可当必填引导）
- GraphQL 建出的 `type` 回读为 `BUSINESS_EVENT`（发 ENTITY_EVENT 也归一化），`publishState=UNPUBLISH`

## 2. 索引 tab（udcIndex*）

| 动作 | op | 关键点 |
|---|---|---|
| 建 | `udcIndexPost` (mutation, body) | name/caption/fieldIds/type=NORMAL |
| 列表 | `udcIndexEntityListPost` (mutation, **body=Long 实体id**，非对象) | 返回含 fieldNames/fieldCaptions/indexSource |
| 删 | `udcIndexDeletePost` (mutation, body `{appId,id}`) | BOOT_0000 |

坑：
- `fieldIds` 是**逗号分隔字符串**（`"-7881…"`），传数组报 `属性fieldIds的值反序列化为String类型时失败`
- 系统自动生成 `name/code = idx_<19位id>`；`indexSource=MANUAL_CREATE`；`publishState=UNPUBLISH`

## 3. 参照 tab（udcReferConfigCreateOrUpdatePost，GraphQL 面）

最小 body（LIVE 通过）：
```jsonc
{"appId":…,"caption":"…","entityId":<实体id>,"type":"List",
 "displayName":"[\"…\"]",            // JSON 字符串
 "configInfo":"{\"columns\":[…],\"search\":[],\"orders\":[],\"whereCond\":[],\"entities\":[…]}",
 "terminalType":"PC","pageId":0,"relationEntity":<实体id>}
```
坑（按反编译 `ReferConfigService.validationOnCreate` 定位）：
- **`relationEntity` 非空 + `pageId` 非空**，否则 `BOOT_1001 参数错误`（两处报错同文案：DTO 校验与 service 校验，难分辨）
- `sourceType` **不用传**——服务端按 relationEntity 前缀/`relationApp=boot-starter-basicdata` 自动设 `ENTITY`/`BASIC_DATA`（枚举就这两个值，带外 CFR 确认）
- `actionType` 同名不同枚举：`com.seeyon.boot.enums.ActionType`，不传即可
- `terminalType`：ALL(0)/PC(1)/MOBILE(2)，字符串 `"PC"` 合法
- 回读：`GET /udc/refer-config/{id}`（REST 面）；分组列表 `udcReferConfigGroupListPost` 返回的是**全应用**数据（含其他应用样本，前端自己过滤）
- 删：`POST /udc/refer-config/delete`，body 必须是**对象** `{"id":…}`——标量数字会被 `@MultiRequestBody` 解析失败报 `BOOT_4002 数据不存在`（误导性报错）

## 4. 通用教训

- 同名枚举三处不同：`EventActionTypeEnum.CREATE` / `ReferConfigSourceTypeEnum.ENTITY|BASIC_DATA` / `boot ActionType`——错值报 `BOOT_3002 No enum constant`（带引用链，可直接定位字段）
- 探针建实体：`udcEntityPost` 必带 `stereotype`（standard 等），缺失报 `BOOT_1001 业务版型 archive,standard,bill,archiveTree,form 选一 不能为空`
- GraphQL 报错信息中的枚举类名可直接去 `<MAVEN_REPO>/com/seeyon/<module>/5.3.517/*.jar` 解 class 得合法值（cfr.jar 在仓 `_attic_pending/mirrored-skills-20261022/.../tools/cfr.jar`，路径含空格勿直接 -jar 引用，先 cp）

## 5. 参照配置「填满」—— display_name / config_info / group_id（2026-10-23 补）

「能创建」不等于「能用」。空壳参照（`config_info={"template":"LIST"}`）在页面上表现为
**参照显示字段 / 下拉字段显示「请配置字段」、显示列为空**。

### 完整结构（对照全库 400+ 条真实配置得出）

```jsonc
// display_name：参照显示字段（JSON 字符串）
[{"path":[{"fieldId":"<字段id>","entity":{"id":"<实体id>","appName":null}}],
  "uuid":"<短id>"}]

// config_info（JSON 字符串）
{
  "id": "<参照配置id>",
  "entities": ["<实体id>"],
  "columns": [{"path":[{"fieldId":"...","entity":{"id":"...","appName":null}}],
               "uuid":"<短id>","width":160,"widthType":"px",
               "lineLimitedContent":"custom","caption":"<字段标题>"}],
  "search":  [{"path":[{"fieldId":"...","entity":{"id":"...","appName":null}}]}],
  "orders":  [{"path":[{"fieldId":"...","entity":{"id":"...","appName":null}}],
               "direction":"DESC"}],
  "whereCond": []
}
```

### ★ 关键坑：不传 `groupId` 会静默落 0，参照列表就看不到

```
udc_refer_config.group_id = 0  →  参照列表（按分组展示）里不出现
```

- `entity_id` 在 `udc_refer_config` 里**本来就是 0**（全库 400+ 条皆如此），
  真实关联走 `group_id → udc_refer_config_group.entity_id`。**别把 entity_id=0 当损坏**。
- 建/改参照时 body 必须带 `groupId`，指向 `udc_refer_config_group` 的 id。
- 分组列表 `udcReferConfigGroupListPost` 返回**全应用**数据（实测 405 条），
  前端自己按 entityId 过滤 —— 接口返回里能找到目标分组不代表列表会显示。

### 已验证

```
参照配置 8913291678640898985 → group_id 已关联 -5032854357981235740
display_name = [{path:[{fieldId:-4144494497326241617,...}], uuid}]
config_info  = columns 3 / search 1 / orders 1 / entities 1
udcReferConfigGroupListPost 返回中含该分组
```

### 未证

- 页面 UI 渲染（需人工点开确认「参照显示字段」不再显示「请配置字段」）
- 参照下拉字段（对应 `display_name` 之外的槽位，本次未配）
- REST `GET /udc/refer-config/{id}` 实测 **405**（方法不对，读面走 GraphQL group 列表）

## 6. ★ 更正（2026-10-23 页面验收后）：一次写 PC+MOBILE 才是正规做法

上一节用 `createOrUpdate` 只写了 PC 一条，页面表现：

- 参照显示字段 → 正常（displayName 生效）
- **参照下拉字段 → 仍是「请配置字段」**
- **显示列 → 仍是空**（DB 里 columns 有 3 项，页面不渲染）

根因两条：

1. **漏了 `pullDisplayName`** —— 参照下拉字段读的是它，不是 displayName。
   结构与 displayName 同构（路径数组），可多级。
2. **只建了 PC 一端**。PC / MOBILE 必须成对且逐项一致
   （检码 `UDC_CE_ENTITY_02119`），单端会让前端渲染不全。

### 正规通道：`POST /service/udc/refer-config/create-config-info`

```jsonc
{
  "caption": "<参照名>", "appId": "...", "entityId": "<实体id>", "type": "List",
  "referConfigDetail": [   // PC + MOBILE 两条，displayName/pullDisplayName/configInfo 完全相同
    {"caption":"…","appId":"…","entityId":"…","type":"List",
     "displayName":"[…]","pullDisplayName":"[…]","configInfo":"{…}",
     "terminalType":1,"groupId":"<分组id>","pageId":0,
     "relationEntity":"<实体id>","sourceType":0,"isDefault":1},
    {“…同上，terminalType:2”}
  ]
}
```

- **返回的 content 是新的 group id**（不是 config id）
- 它会自动建分组并写两条，**旧的单端记录会变成重复**，记得清理
- 路径必须带 `/service` 前缀（`/udc/refer-config/...` 直接 405）

### ★ uuid 必须是 21 位 base62

`displayName` / `pullDisplayName` / `columns[].uuid` 里的 uuid 形态是
`5SQlR8H2U1PBMc4y7QfcF`（21 位字母数字）。用 `refColF01xx` 这种自造短串
可能导致前端解析失败。两条终端里的 uuid 要**相同**才算一致。

### 清理

| 动作 | 路径 |
|---|---|
| 按分组删 | `POST /service/udc/refer-config/delete-by-group-id` body `{"groupId": "<id>"}` |
| 单条删 | `POST /service/udc/refer-config/delete` body `{"id": "<id>"}`（**必须对象**，标量报 BOOT_4002） |

删完组再逐条删成员会报 `BOOT_4002 数据不存在或无权限查看`——组删除已连带删成员，属正常。

### 页面验收（2026-10-23）

```
参照列表  选择小爪验收实体全量(列表)
实体      小爪验收实体全量
参照显示字段  文本字段
参照下拉字段  文本字段        ← 原来是「请配置字段」
显示列    文本字段(160) / 整数字段(100) / 日期字段(120)
终端      PC 与 MOBILE 两份配置完全一致
```
