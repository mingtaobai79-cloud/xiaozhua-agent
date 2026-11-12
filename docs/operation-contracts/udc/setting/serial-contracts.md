# 操作契约 · 设置域 / 流水号（Serial Scheme）

依据：反编译 `boot-starter-serialnumber-5.3.318.jar` 的
`SerialSchemeDto` / `SerialSectionDto` / 五个枚举 + 2026-10-21 LIVE 实测。
事实格见 `core/facts/udc/setting/serial/create.md`。

## 协议：GraphQL

端点 `udcSerialSchemeCreatePost` 等，走 `/service/udc/graphql?<op>`。

## operation 清单

| operation | 写 | 状态 |
|---|---|---|
| `udcSerialSchemeCreatePost` | 是 | **LIVE PASS** |
| `udcSerialSchemeDeletePost` | 是 | **LIVE PASS**（`{appId,id}` → content=1） |
| `udcSerialSchemeUpdatePost` | 是 | UNVERIFIED |
| `udcSerialSchemeBatchDeletePost` | 是 | UNVERIFIED（空 body 报 Index:0 Size:0） |
| `udcSerialSchemeSearchPagePost` | 否 | LIVE |
| `udcSerialSchemeMaxSortNumberAppGet` | 否 | LIVE（需 path 参数） |
| `udcSerialSchemeContextValueListGet` | 否 | LIVE |
| `udcDesignMetadataAggEntityExcludeBootGet` | 否 | LIVE |

## create body —— 字段名来自反编译

```json
{
  "appId": "<appId>",
  "appGuid": "<appGuid>",
  "code": "仅字母数字，禁中文，≤50",
  "name": "≤200",
  "totalSize": "<各段 size 之和>",
  "containFlow": true,
  "active": true,
  "serialResetRule": "NONE | YEAR | MONTH | DAY",
  "editEntity": true,
  "serialType": "APP | BIG | SMALL",
  "sortNum": 1,
  "orgId": "-1",
  "entityFullName": "",
  "sourceAppName": "udc",
  "serialSectionDtoList": [ ... ]
}
```

★ **段列表字段名是 `serialSectionDtoList`**，不是 `sections` / `serialSectionDtos`。

## 段（SerialSectionDto）

```json
{
  "size": 4,
  "type": "CONSTANT | CONTEXT | ENTITY | SERIAL",
  "value": "HT 或 currentDate",
  "caption": "",
  "fillType": "LEFT | RIGHT | NONE",
  "cutType": "LEFT | RIGHT | NONE",
  "fillChar": "0",
  "dateType": false,
  "datePattern": "yyyyMMdd",
  "show": true,
  "flow": false,
  "increase": true,
  "sectionRank": 1,
  "serialCurrent": 1,
  "startValue": 1,
  "endValue": -1,
  "sourceAppName": "udc"
}
```

**DTO 字段名 ↔ DB 列名**：

| DTO | DB |
|---|---|
| `size` | `section_size` |
| `dateType` | `is_date_type` |
| `show` | `is_show` |
| `flow` | `is_flow` |
| `increase` | `is_increase` |

## 五个枚举（传字符串，DB 存 ordinal）

```
SerialTypeEnum      CONSTANT(0) / CONTEXT(1) / ENTITY(2) / SERIAL(3)   段类型
FillTypeEnum        LEFT(0) / RIGHT(1) / NONE(2)
CutTypeEnum         LEFT(0) / RIGHT(1) / NONE(2)
SerialResetRuleEnum NONE(0) / YEAR(1) / MONTH(2) / DAY(3)
SerialRuleTypeEnum  APP(0) / BIG(1) / SMALL(2)                         serialType 用这个
```

⚠ 两个坑：

1. `serialType` 用 `SerialRuleTypeEnum`（APP/BIG/SMALL），**不是** `SerialTypeEnum`
2. **枚举语义反转落库**：传 `fillType="NONE"` 落成 `2`；真实样本固定值段 `fill_type=0`（=LEFT）
   → **写库值是 ordinal，别拿 DB 数字反推语义**

## 错误码

| 场景 | 码 / 文案 |
|---|---|
| 缺段列表 | `BOOT_1001` 流水号段 个数必须在1和12之间 |
| 段数 > 12 | 同上（DTO `@Size(1,12)`） |
| appId 缺失 | `UDC_APP_0001` 应用不存在 |
| code 含中文 | `@Pattern` 校验失败 |
| delete 缺 id | `BOOT_4002` 数据不存在或无权限查看 |

## 为什么必须反编译（不要重复踩）

GraphQL 层**不校验未知字段**：

```
传 zzzNotAField  与  传错字段名  →  返回逐字节相同的业务错
（BOOT_1001 流水号段 个数必须在1和12之间）
```

猜错和猜对无法区分 → 试错法不可能收敛。试过 11 个候选键名全失败，只能读 DTO。

## 落库表

```
ctp_serial_scheme    方案主表
ctp_serial_section   流水号段（serial_scheme_id + section_rank 排序）
ctp_serial_condition 绑定实体条件（create_expression / release_expression longtext）
```

## 组装提醒

- `totalSize` 必须等于各段 `size` 之和
- 段 `type` 语义：`CONSTANT` 填固定值、`CONTEXT` 填 `currentDate` + `datePattern`、
  `SERIAL` 留空靠 `startValue`/`endValue`
- 段数 1~12
