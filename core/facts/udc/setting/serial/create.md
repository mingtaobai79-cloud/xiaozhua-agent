# 设置域 · 流水号（Serial Scheme）

> 前置：本文所有 `udc*Post` 必填的 `appGuid`，取法见 [`precondition-appguid.md`](../precondition-appguid.md)（用 `udcApplicationDetailGet` 接口查，appGuid ≠ appId，无需查库）。
> 版本：`boot-starter-serialnumber-5.3.318`
> 证据等级：**LIVE PASS**（创建 + 主表/段表全落库 + 页面正确渲染）
> 字段名来源：**反编译** `SerialSchemeDto` / `SerialSectionDto`（不是猜的）
> 实现：`components/udc/setting/serial_constraints.py`

## R-E1 Capability

新建流水号方案：由若干「段」拼成编号，如 `HT` + `20261021` + `0001` = `HT202610210001`。

段有四种类型：

```
CONSTANT  固定值         value='HT'
CONTEXT   上下文字段     value='currentDate' + datePattern='yyyyMMdd'
ENTITY    实体字段       取实体字段值
SERIAL    流水号（自增）  startValue / endValue 定区间
```

## R-E2 Version / 协议

**GraphQL**（与设置域多数子模块一致）。端点 `udcSerialSchemeCreatePost`。

```
写  udcSerialSchemeCreatePost / udcSerialSchemeUpdatePost
    udcSerialSchemeDeletePost（{appId, id} → content=1）
    udcSerialSchemeBatchDeletePost（空 body 报 BOOT_3000，需参数）
读  udcSerialSchemeSearchPagePost
    udcSerialSchemeMaxSortNumberAppGet（需 path 参数）
    udcSerialSchemeContextValueListGet
    udcDesignMetadataAggEntityExcludeBootGet（实体候选）
```

## R-E3 Input

### SerialSchemeDto（反编译原文）

```java
Long    id
Integer version = 0
String  code                       // @Size(1,50) @Pattern(^[^\u4e00-\u9fa5]*$) 仅字母数字
String  name                       // @Size(1,200)
String  appGuid = "-1"
String  appId = "-1"
String  entityFullName = ""
String  orgId = "-1"
Integer totalSize = 0              // 须等于各段 size 之和
Boolean createUnused = false        // 空号优先
Boolean unusedPriority = false
Integer sortNum = 1
Boolean containFlow = false
Boolean active = true
SerialResetRuleEnum serialResetRule = NONE
Boolean editEntity = true
Boolean deleteFlag = false
Boolean preset = false
Boolean reset = false
SerialRuleTypeEnum serialType = APP
List<SerialSectionDto> serialSectionDtoList     // @Size(min=1,max=12) ★ 段列表
List<SerialConditionDto> serialConditionDtoList
String  sourceAppName
String  serialAppName
```

⚠ **段列表字段名是 `serialSectionDtoList`** —— 不是 `sections` / `serialSectionDtos`。

### SerialSectionDto（反编译原文）

```java
Long    id
Long    serialSchemeId
Integer size = 4                   // ★ 不是 sectionSize
SerialTypeEnum type = CONSTANT
String  value = ""
String  caption = ""               // @Size(max=255)
FillTypeEnum fillType = NONE
CutTypeEnum  cutType = NONE
String  fillChar = "0"
Boolean dateType = false           // ★ 不是 isDateType
String  datePattern = ""
Boolean show = true                // ★ 不是 isShow
Boolean flow = false               // ★ 不是 isFlow
Boolean increase = true            // ★ 不是 isIncrease
Integer sectionRank = 1
Long    serialCurrent = 1
ActionType actionType = NORMAL
Boolean deleteFlag = false
String  sourceAppName
Long    startValue = 1
Long    endValue = -1
```

**DTO 名 vs DB 列名**（回读要用 DB 名）：

```
DTO size        ↔ DB section_size
DTO dateType    ↔ DB is_date_type
DTO show        ↔ DB is_show
DTO flow        ↔ DB is_flow
DTO increase    ↔ DB is_increase
```

### 五个枚举（**传字符串**）

```java
SerialTypeEnum      CONSTANT(0) / CONTEXT(1) / ENTITY(2) / SERIAL(3)
FillTypeEnum        LEFT(0) / RIGHT(1) / NONE(2)
CutTypeEnum         LEFT(0) / RIGHT(1) / NONE(2)
SerialResetRuleEnum NONE(0) / YEAR(1) / MONTH(2) / DAY(3)
SerialRuleTypeEnum  APP(0) / BIG(1) / SMALL(2)
```

⚠ `serialType` 用 **`SerialRuleTypeEnum`**（APP/BIG/SMALL），**不是** `SerialTypeEnum`（段类型）。

## R-E4 Required

| 缺失/非法 | 报错 |
|---|---|
| appId | `UDC_APP_0001` 应用不存在 |
| 段列表缺 | `BOOT_1001` 流水号段 个数必须在1和12之间 |
| 段数 > 12 | 同上（DTO `@Size(1,12)`） |
| code 含中文 | `@Pattern` 校验失败 |

## R-E5 Execution

```
1. 取实体全类名、appId、appGuid
2. 组 sections（每段 size / type / value / datePattern / startValue / endValue）
3. totalSize = 各段 size 之和（平台会校验一致）
4. POST udcSerialSchemeCreatePost
```

标准三段样例：

```python
secs = [
    build_serial_section(type_="CONSTANT", size=2, value="HT", section_rank=1),
    build_serial_section(type_="CONTEXT", size=8, value="currentDate", section_rank=2,
                         date_type=True, date_pattern="yyyyMMdd", flow=True),
    build_serial_section(type_="SERIAL", size=4, section_rank=3, flow=True,
                         start_value=1, end_value=9999),
]
body = build_serial_scheme_body(app_id, app_guid, code="ZxjOrderNo",
                                name="验收订单号", sections=secs, contain_flow=True)
```

## R-E6 Side Effects

写两张表：

```
ctp_serial_scheme    方案主表（code/name/total_size/serial_type/serial_reset_rule/sort_num）
ctp_serial_section   流水号段（serial_scheme_id + section_rank 排序）
```

`is_active=1`、`is_delete=0`、`release_state=0`。

## R-E7 Constraints

- 段数 1~12（DTO `@Size`）
- `totalSize` 必须等于各段 `size` 之和
- `code` 仅字母数字，禁中文
- 段 `type` / `fillType` / `cutType` 传字符串枚举
- **枚举语义会反转落库**：传 `fillType="NONE"` 落库成 `2`；
  真实样本里固定值段是 `fill_type=0`（对应 `LEFT`）。

  > **写库值是 ordinal，别拿 DB 数字反推语义。**

## R-E8 Evidence

```
反编译  /d/repo/CHIT/com/seeyon/boot-starter-serialnumber/5.3.318/
        boot-starter-serialnumber-5.3.318.jar
        → SerialSchemeDto / SerialSectionDto / 五个枚举

证伪    GraphQL 层不校验未知字段：
        传 zzzNotAField 与传错字段名返回逐字节相同的业务错
        （BOOT_1001 流水号段 个数必须在1和12之间）
        → 猜字段名这条路是死的；试过 11 个候选全失败，只能反编译

实测    探针 ZxjSerialProbe：CONSTANT"ZXJ" + currentDate(yyyyMMdd) + SERIAL 4位
        BOOT_0000 → 主表 + 3 段全部落库
        页面「规则组成: 常量:ZXJ 上下文字段:系统日期 流水号」
             「效果预览: ZXJ202610211」
        探针已删（引用核对后）
```

## R-E9 Verified

| 项 | 状态 | 证据 |
|---|---|---|
| 创建（三段组合） | **LIVE PASS** | 主表 + 3 段落库，页面预览正确 |
| 删除 `{appId,id}` | **LIVE PASS** | content=1，回读消失 |
| 读面 4 个接口 | **LIVE** | 抓包确认（SearchPage / MaxSortNumber / ContextValueList / EntityExcludeBoot） |
| `serialType=APP` | **LIVE PASS** | 落库 serial_type=0 |
| `serialType=BIG/SMALL` | **UNVERIFIED** | 只验了 APP |
| `createUnused` / `unusedPriority`（空号优先） | **UNVERIFIED** | 表里有列，未测 |
| `reset` / `preset` 字段用途 | **UNVERIFIED** | DTO 有，未测 |
| `serialConditionDtoList`（绑定实体条件） | **UNVERIFIED** | 只读了表结构 |
| `serialAppName` 与 `sourceAppName` 区别 | **UNVERIFIED** | 样本里前者 null |
| `update` body | **UNVERIFIED** | 端点存在，未测 |
| 批量删除参数形态 | **UNVERIFIED** | 空 body 报 Index:0 Size:0 |

## 本应用验收样本（保留）

```
验收订单号   ZxjOrderNo     id=8675205859679440414  总长14  3段
             常量"DD" + 日期 yyyyMMdd + 流水号 4 位
验收合同编号 ZxjContractNo  id=-1087839647902612473 总长13  3段
             常量"HT" + 日期 yyyyMM + 流水号 5 位
```

## 可用构造器

```python
from components.udc.setting.serial_constraints import (
    build_serial_section, build_serial_scheme_body, validate_serial_scheme_body,
    SERIAL_TYPE, FILL_TYPE, CUT_TYPE, RESET_RULE, RULE_TYPE, MAX_SECTIONS)

body = build_serial_scheme_body(app_id, app_guid, code="ZxjOrderNo",
                                name="验收订单号", sections=secs, contain_flow=True)
errs = validate_serial_scheme_body(body)   # 空 = 通过
```

校验器拦六类：

```
① 缺 serialSectionDtoList（明确提示不是 sections / serialSectionDtos）
② 段数超出 1~12
③ totalSize 与各段 size 之和不一致
④ 用了 sectionSize 而不是 size
⑤ 枚举值不在值域内
⑥ serialType 用了 SerialTypeEnum（应为 SerialRuleTypeEnum）
⑦ code 含中文
```
