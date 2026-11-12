# 实体事件与 DTO 绑定（2026-10-24 实测）

## 铁律

- 事件绑的是 DTO 不是实体：`event_data` 必须指向 `udc_data_transfer_object.id`，不是实体 id
- 实体没有 DTO 时建事件是静默成功：接口 `BOOT_0000`、DB 有行、页面和列表接口都是 0 条，且不报错
- DTO 由「页面建事件」自动生成，不需要单独调 `CreateDtoPost`；手工建各种参数组合全部 `BOOT_3000`
- 事件列表 body 是 `{params:{sourceId}, sort:{orders}}`，不带 `appId`；扁平传 `appId` 会被静默忽略并返回全库前 50 条
- 「建成功 + DB 回读正确」不足以判定事件可用，必须过列表接口和页面 tab

## 1. ★ 事件绑定的不是实体，是 DTO

`udc_event.event_data` 指向 **`udc_data_transfer_object`（DTO）**，不是 `udc_entity`。

实测对照（同一个应用、同一条链路）：

| | 客户实体（页面可见） | 新建实体（页面查不到） |
| --- | --- | --- |
| `source_id` | 实体 id | 实体 id |
| `event_data` | **DTO id** `6596678094750767925` | **实体 id** `-1516209680943439395` |
| `udc_data_transfer_object` 记录 | 有（`ysEvtData2`，source=2，parent_entity_id=实体） | **没有** |

## 2. ★ 没有 DTO 时，建事件是「静默成功」

`udcEventPost` 返回 `BOOT_0000`、DB 里也确实写入了，
但页面事件 tab 空、`udcEventListPost` 返回 0 条 —— 字段值本身全对
（`enabled=1`、`publish_state=1`、`source=0`、`action_type` 正确）。

**所以「建成功 + DB 回读正确」不足以判定事件可用，必须过列表接口。**

## 3. 事件列表接口的真实 body

```
POST /service/udc/graphql?udcEventListPost
{"params": {"sourceId": "<实体id>"},
 "sort": {"orders": [{"direction": "ASC", "property": "createTime"}]}}
```

**不带 `appId`**（带了反而不生效，会返回全库前 50 条）。
只带 `appId` 而不带 `params` 嵌套时，后端忽略该值并返回别人的数据 —— 这是误判源头。

## 4. 参照列表接口的真实 body

```
POST /service/udc/graphql?udcReferConfigGroupListPost
{"params": {"appId": "<应用id>", "entityId": "<实体id>"}, "sort": <排序>}
```

扁平传 `{appId, entityId}` 会返回别的应用的数据（同样被忽略）。

## 5. DTO 创建接口

- `udcDataTransferObjectCreateDtoPost`：
  `source` 必填（`DtoSourceTypeEnum`，数字 `2` 可用；字符串 `"ENTITY"` 会报
  `BOOT_3002 No enum constant ...DtoSourceTypeEnum.ENTITY`）。
  补齐 `appId/name/caption/source=2/sourceId` 后仍报 `BOOT_3000`（其余必填项未知）。
- `udcDataTransferObjectCreateDtoWithAttrsPost`：参数是**数组**，同样 `BOOT_3000`。
- `udcEventCreateWithDataPost`：本意是一步建「事件+D₀」，本实体报
  `UDC_EVENT_0002 创建事件数据失败:null`。

**结论：DTO 生成通道尚未打通（UNVERIFIED）。**
可行方向：走页面「生成页面」按钮触发，或从前端挖 `CreateDtoWithAttrsPost` 的完整必填集。

## 6. 证据等级

- `event_data` 必须指向 DTO：**LIVE**（同应用正反对照 + DB 全列 diff）
- 缺 DTO 时静默成功：**LIVE**（create 成功 / 列表 0 条 / DB 有行）
- 接口 body 形态：**LIVE**（页面真实请求抓包）
- DTO 创建通道：**UNVERIFIED**（全部返回 3000/0002）

## 7. ★ 更正（2026-10-24 用户手建事件后取证）

用户直接在页面上建了一条事件（`name=as`, `caption=1`），**平台同时自动生成了 DTO**：

```
udc_data_transfer_object
  id           7341771973424551966
  name         asYsTypesAll          ← 事件编码 + 实体名
  caption      验收实体-全字段类型
  source       0                     ← 实体自身（不是 2）
  source_type  1                     ← 我之前传 0，错
  source_id    -1516209680943439395
  parent_entity_id  0
  is_root      1
  is_meta_data 1
  batch_id     -1032550210763374588
```

**DTO 是「建事件时自动生成」的，不需要单独调 CreateDtoPost。**
（`CreateDtoPost` / `CreateDtoWithAttrsPost` 手工建全部 `BOOT_3000`，`source` 数字/字符串、
`source=0`/`2`、`sourceType=0`/`1` 各种组合都试过 —— 这条路不通就不要再走。）

正确做法：**用页面建一条事件拿到 DTO，之后所有事件 `eventData` 指向它**。
LIVE：3 条事件改绑该 DTO 后，`udcEventListPost` 由 0 条变 4 条，页面事件 tab 全部可见。
