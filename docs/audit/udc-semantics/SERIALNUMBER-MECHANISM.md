# UDC 流水号机制（boot-starter-serialnumber 5.3.318）

**证据**：CFR 反编译 `<MAVEN_REPO>/com/seeyon/boot-starter-serialnumber/5.3.318/boot-starter-serialnumber-5.3.318.jar`；
表结构来自 `@Table`/`@Column`（nullable + columnDefinition 含中文注释，数据库层权威）。

## 1. 四 Controller / 45 端点

落在 `components/udc/serialnumber_constraints.py` `SERIAL_ENDPOINTS`：

| Controller | 基址 | 端点数 | 核心 |
| --- | --- | --- | --- |
| SerialSchemeController | serial-scheme | 17 | create / **createEasyScheme** / update-active / search-page-4-entity-fullname / context-value |
| SerialNumberController | serial-number | 13 | **get-serial-number**（取号，写操作）/ batch-serial-number / preview-serial-value（只读预览）/ reset-serial-number/{schemeId} |
| SerialRangeController | serial-range | 14 | createUnused / createBatchUnused / batch-updateForbiddenFlag |
| SerialConditionController | serial-condition | 3 | batch-create / list / eval |

取号 = 写操作（消耗流水号）；preview = 只读。`reset-serial-number/{serialSchemeId}` 按方案重置，`reset-app-serial-number/{appId}` 按应用重置。

## 2. 六张表（数据库层权威）

| 表 | 说明 | 列数 |
| --- | --- | --- |
| `ctp_serial_scheme` | 流水号方案 | 17（全覆盖） |
| `ctp_serial_section` | 流水号段（方案→多段拼接） | 19（全覆盖） |
| `ctp_serial_range` | 号段（预留/空闲） | 13 |
| `ctp_serial_condition` | 流水号条件 | 6 |
| `ctp_serial_current` | 流水号当前值 | 9 |
| `ctp_serial_history` | 流水号历史 | 7 |

`ctp_serial_scheme` 关键列：code VARCHAR(50) 非空、name VARCHAR(255) 非空、
serial_type SMALLINT 默认 APP、entity_full_name VARCHAR(255) 默认 ""、
total_size 编码长度、is_unused_priority 空号优先、serial_reset_rule 重置规则、
is_active 默认 true、is_preset 默认 false。

`ctp_serial_section` 关键列（段拼接规则）：
- type：CONSTANT(常量段)/CONTEXT(上下文段)/ENTITY(实体段)/**SERIAL(流水号段)**
- section_size 默认 4、fill_char 默认 "0"、section_rank 段序号
- fill_type：LEFT/RIGHT/NONE；cut_type：LEFT/RIGHT/NONE
- is_date_type + date_pattern（日期段）
- start_value 默认 1、end_value 默认 -1（-1=无上限）、serial_current 默认 1
- is_increase：超出最大值是否递增

## 3. 枚举值域（反编译权威）

- `SerialTypeEnum`（段类型）：CONSTANT(0)/CONTEXT(1)/ENTITY(2)/SERIAL(3)
- `SerialRuleTypeEnum`（方案类型）：APP(0) 应用内流水号 / BIG(1) 大流水号 / SMALL(2) 小流水号
- `SerialResetRuleEnum`：NONE(0)/YEAR(1)/MONTH(2)/DAY(3)
- `SerialRangeTypeEnum`：RESERVE(0) 预留 / UNUSED(1) 空闲
- `FillTypeEnum` / `CutTypeEnum`：LEFT(0)/RIGHT(1)/NONE(2)

## 4. 校验器

- `validate_serial_scheme`：必填 code/name/serialType/entityFullName + serialType/serialResetRule 值域
- `validate_serial_section`：type/fillType/cutType 值域 + SERIAL 段 startValue≤endValue + size≥1

## 5. 订单应用集成要点

1. 方案绑定实体：`entity_full_name = "com.seeyon.Order"`
2. 订单编号 = 多段拼接：如 `{年:SERIAL?}` 不对——典型组合是
   常量段 `ORD-` + 日期段 `yyyy` + 流水号段 `sequence(4位左补0)`
3. 取号：`POST /serial-number/get-serial-number`（写操作，消耗流水号）
4. 预览（设计器里看效果）：`POST /serial-number/preview-serial-value`（只读）
5. 与 udc-plugin-api 的 `UdcSerialSchemeAppService.createEasyScheme` 契约对应；
   udc-starter-runtime 的 `udc-runtime/serial-config/*` 是字段级配置面
