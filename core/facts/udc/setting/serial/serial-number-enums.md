# 流水号：枚举取值域与 DTO 字段

> 证据级：**VERIFIED_STATIC_BYTECODE**（`javap -p` / `javap -c` 直接读 class）
> 来源：`<MAVEN_REPO>/com/seeyon/boot-starter-serialnumber/5.3.603/boot-starter-serialnumber-5.3.603.jar`
> 类：`com.seeyon.boot.starter.serialnumber.enums.*` / `...domain.dto.*`

## 1. Capability

写流水号方案时，`type` 和 `serialType` 到底能填什么。
这两个字段用的是**两个不同的枚举**，填错报 `BOOT_3002 No enum constant`。

## 2. 六个枚举，逐字

```
SerialTypeEnum        ← SerialSectionDto.type
  CONSTANT  ordinal 0  code 0
  CONTEXT   ordinal 1  code 1
  ENTITY    ordinal 2  code 2
  SERIAL    ordinal 3  code 3

SerialRuleTypeEnum    ← SerialSchemeDto.serialType
  APP
  BIG
  SMALL

SerialResetRuleEnum   ← SerialSchemeDto.serialResetRule
  NONE / YEAR / MONTH / DAY

FillTypeEnum          ← SerialSectionDto.fillType
  LEFT / RIGHT / NONE

CutTypeEnum           ← SerialSectionDto.cutType
  LEFT / RIGHT / NONE

SerialRangeTypeEnum   ← 未在 DTO 中直接出现
  RESERVE / UNUSED
```

★ `SerialTypeEnum` 里**没有 `INCREASE`**。
   「自增」这个语义不在 `type` 上，而在 `SerialSectionDto.increase`（Boolean）上。
★ `SerialRuleTypeEnum` 里**没有 `ENTITY`** —— `ENTITY` 是 `SerialTypeEnum` 的值，
   拿它填 `serialType` 必然 `BOOT_3002`。

## 3. SerialSectionDto 全字段（22 个）

```
id                 Long
serialSchemeId     Long
size               Integer
type               SerialTypeEnum        ← CONSTANT / CONTEXT / ENTITY / SERIAL
value              String               ← CONSTANT 段的具体文本
caption            String
fillType           FillTypeEnum          ← LEFT / RIGHT / NONE
cutType            CutTypeEnum           ← LEFT / RIGHT / NONE
fillChar           String
dateType           Boolean
datePattern        String
show               Boolean
flow               Boolean
increase           Boolean              ← ★ 自增开关在这
sectionRank        Integer              ← ★ 段序，可能比数组顺序更权威
serialCurrent      Long
actionType         ActionType
deleteFlag         Boolean
sourceAppName      String
startValue         Long
endValue           Long
```

## 4. SerialSchemeDto 全字段（24 个）

```
id / version / code / name / appGuid / appId / entityFullName / orgId
totalSize            Integer   ← 各段 size 之和
createUnused         Boolean   ← 工具未传
unusedPriority       Boolean   ← 工具未传
sortNum              Integer
containFlow          Boolean
active               Boolean
serialResetRule      SerialResetRuleEnum
editEntity           Boolean
deleteFlag           Boolean
preset               Boolean   ← 工具未传
reset                Boolean   ← 工具未传
serialType           SerialRuleTypeEnum   ← APP / BIG / SMALL
serialSectionDtoList List<SerialSectionDto>
serialConditionDtoList List<SerialConditionDto>   ← 工具完全没这个
sourceAppName        String
serialAppName        String   ← 工具未传
```

## 5. 创建校验：checkDto4Create 逐分支（字节码直读）

`SerialSchemeService.checkDto4Create(SerialSchemeDto)` 的完整逻辑（`javap -c` 还原）：

```java
checkCodeUnique(dto);
boolean flow = false;      int totalSize = 0;
long serialCurrent = -1;   int serialCount = 0;

for (SerialSectionDto s : dto.getSerialSectionDtoList()) {
    if (s.getType().code() == SerialTypeEnum.SERIAL.code()) {
        serialCount++;
        if (isBlank(s.getFillChar()))                             throw SERIALNUMBER_1006;
        if (s.getSize() < 1)                                      throw SERIALNUMBER_1016;
        if (s.getSerialCurrent() == null)                         throw SERIALNUMBER_1007;
        if (String.valueOf(s.getSerialCurrent()).length() > s.getSize())
                                                                  throw SERIALNUMBER_1004;
        if (!LONG_MINUS_ONE.equals(s.getEndValue())
            && s.getStartValue() >= s.getEndValue())              throw SERIAL_SECTION_1002;
        serialCurrent = s.getSerialCurrent();
    } else {
        if (isBlank(s.getValue()))                                throw SERIALNUMBER_1014;
        if (s.getValue().length() > 255)                          throw SERIALNUMBER_1015;
    }
    totalSize += s.getSize();
    if (s.getFlow()) flow = true;
}

if (serialCount != 1) throw SERIALNUMBER_1008;   // ★ 必须恰好一个 SERIAL 段
```

### 5.1 1008 的真实含义

i18n 文案是「流水段有且只能有一段」，**但代码判的是 `serialCount != 1`**，
其中 `serialCount` 只统计 `type == SERIAL` 的段。

⇒ 正确读法：**必须恰好有一个 `type=SERIAL` 的段**，其他类型可以任意多。

⇒ 之前踩的坑：只传一个 `CONSTANT` 段（文本前缀），`serialCount=0` → 报 1008，
文案误导成「段数不对」，实际是「缺 SERIAL 段」。

### 5.2 两类段的不同必填

| 段类型 | 必填 | 约束 |
|---|---|---|
| `SERIAL` | `fillChar`、`size`、`serialCurrent` | `size>=1`；`len(serialCurrent)<=size`；`endValue!=-1` 时 `startValue<endValue` |
| 其他（CONSTANT/CONTEXT/ENTITY） | `value` | 非空且 `length<=255` |

### 5.3 最小可用方案

```
1 个 CONSTANT 段：value="ZZVF", size=4, fillChar=""（非 SERIAL 段不校验 fillChar）
1 个 SERIAL 段：  size=6, fillChar="0", serialCurrent=1, startValue=1, endValue=-1
serialType = APP | BIG | SMALL（SerialRuleTypeEnum，不是 ENTITY）
```

★ 这条是**按校验逻辑推出来的**，尚未真机提交。但它满足了全部 throw 分支的前置条件。
