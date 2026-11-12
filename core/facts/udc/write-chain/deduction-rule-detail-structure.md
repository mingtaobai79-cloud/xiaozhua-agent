# udc_deduction_rule_detail 明细结构契约（LIVE + STATIC）

> 环境：test2（`lowcode-test2.example.com`，租户 `-8112660841495312922`）
> 取证方式：MySQL 直连 LIVE + CFR 反编译 STATIC + REST LIVE（`POST /udc/deduction/rule/init-data`、`POST /udc/deduction/rule`、`GET /udc/deduction/rule/{id}`）
> 结论等级：**表结构 LIVE / DTO 契约 LIVE / 生成机制 LIVE / 写入路径 LIVE**

## 0. 一句话结论

`udc_deduction_rule_detail` 是**扣减规则按「单据状态」拆分的行级明细表**：一条扣减规则 × 每个单据状态枚举项 = 一行明细，承载该状态下用哪个算法（`deduction_algorithm_id`）、提示什么文案（`notice`）、检查规则是什么（`check_rule`）。**它不是必填层**——只有当源实体的 `stereotype='bill'` 且存在唯一的 `statusType`（`dataType=ENUM`）属性时，平台才会生成明细行；普通 `standard` 实体（本应用全部 9 个实体均属此类）永远生成 0 行，这是**机制必然**，不是数据缺失。

## 1. 表结构（LIVE：`SHOW CREATE TABLE udc_test2.udc_deduction_rule_detail`）

```sql
CREATE TABLE `udc_deduction_rule_detail` (
  `id` bigint(20) NOT NULL COMMENT '主键',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `tenant_id` bigint(20) NOT NULL COMMENT '租户ID',
  `update_time` datetime NOT NULL COMMENT '修改时间',
  `version` smallint(6) NOT NULL COMMENT '版本号',
  `guid` bigint(20) NOT NULL COMMENT 'guid',
  `publish_state` smallint(6) DEFAULT NULL COMMENT '发布状态',
  `app_id` bigint(20) NOT NULL COMMENT '所属应用ID',
  `bill_status_info` longtext COMMENT '单据状态JSON',
  `check_rule` longtext COMMENT '检查规则',
  `deduction_algorithm_id` bigint(20) DEFAULT NULL COMMENT '扣减算法ID',
  `deduction_rule_id` bigint(20) NOT NULL COMMENT '扣减规则ID',
  `notice` varchar(500) DEFAULT NULL COMMENT '提示信息',
  `owner_code` varchar(32) DEFAULT NULL COMMENT '所有者编码',
  `backup_code` varchar(100) DEFAULT NULL COMMENT '数据备份标识（如文件系统的storageKey）',
  `order_no` smallint(6) NOT NULL COMMENT '排序号',
  `original_id` bigint(20) NOT NULL DEFAULT '0' COMMENT '原始id',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_u_d_r_d_app_id` (`app_id`) USING BTREE,
  KEY `idx_u_d_r_d_rule_id` (`deduction_rule_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8
```

- 全实例（`udc` / `udc_test2` / `udc_uat`）三份同名表 **DDL 完全一致**，仅 BTREE 显式标注差异，无版本漂移。
- 字符集 `utf8`（非 utf8mb4）；`bill_status_info` / `check_rule` 是 `longtext`。

## 2. 字段语义（逐列，含写入来源）

| 列 | 类型 | 可空 | 写入来源 / 语义 |
|---|---|---|---|
| `id` | bigint | NO | 服务端 `Ids.gidLong()` 生成（`DeductionRuleService.handleDetail`：`if (id == null) id = Ids.gidLong()`）。客户端传 id 不规范会被忽略/覆盖语义。 |
| `create_time` / `update_time` | datetime | NO | 框架 BaseEntity 自动填充 |
| `tenant_id` | bigint | NO | 租户，test2 实测 `-8112660841495312922` |
| `version` | smallint | NO | 乐观锁，新建为 0 |
| `guid` | bigint | NO | 框架生成（实测为负数 long） |
| `publish_state` | smallint | YES | **DB 实测 NULL**；数值域来自 `PublishStateEnum`：`PUBLISHED(0)` / `UNPUBLISH(1)`。新建明细不写该列 |
| `app_id` | bigint | NO | **服务端强制覆写**为 `dto.getAppId()`（`handleDetail`），客户端传值被规则头 appId 覆盖 |
| `bill_status_info` | longtext | YES | **核心列**：`deductionBillStatusInfoDtoList` 的 JSON 序列化（`JsonUtils.toJson`），DTO 侧字段名是 `deductionBillStatusInfoDtoList`，DB 列名是 `bill_status_info`——**两处名字不同，勿混** |
| `check_rule` | longtext | YES | 老字段，DTO 上标 `@Deprecated`；同一语义的新承载是 `checkRule`（亦已 @Deprecated），实测写 NULL |
| `deduction_algorithm_id` | bigint | YES | **由 `algorithmCode` 关联而来**，不是客户端直传（见 §5） |
| `deduction_rule_id` | bigint | NO | **服务端强制覆写**为规则主表 id（`handleDetail`） |
| `notice` | varchar(500) | YES | 提示信息，DTO 校验 `@Length(max=500)`；⚠ Entity 注解写的是 `VARCHAR(50)`，**以 DDL 的 500 为准**（注解与 DDL 不一致，实际按 500） |
| `owner_code` / `backup_code` | varchar | YES | 框架字段，业务不写 |
| `order_no` | smallint | NO | 排序；`createBatch` 会**覆盖**为「该规则现存明细数 + 递增」，客户端传值无效 |
| `original_id` | bigint | NO (default 0) | 模板复制追源，新建为 0 |

## 3. DTO 契约（STATIC：CFR `udc-common-5.3.517`）

```java
@DtoInfo("扣减规则详情", entity="com.seeyon.udc.deduction.domain.entity.DeductionRuleDetail")
public class DeductionRuleDetailDto extends UdcBaseEntityDto {
    private Long appId;                       // 应用id
    private Long deductionRuleId;             // 扣减规则id
    private Long deductionAlgorithmId;        // 算法id
    private String billStatusInfo;            // 单据状态JSON（hidden=true，服务端派生）
    @Deprecated private String checkRule;     // 检查规则（已废弃）
    @Deprecated @Length(max=500) private String notice;  // 提示信息
    private List<DeductionBillStatusInfoDto> deductionBillStatusInfoDtoList;  // 单据状态
    private String algorithmCode;             // 算法编码，用于关联规则详情
    private Integer orderNum;                 // 排序号
}
// 继承 UdcBaseEntityDto：publishState / ownerCode / backupCode / createTime / updateTime
// 继承 UdcBaseAppEntity 侧：appId
```

**JSON 键名 = 字段名**（驼峰），只有 `bill_status_info` ↔ `deductionBillStatusInfoDtoList` 这一对存在库列/DTO 名不一致。

### 3.1 `DeductionBillStatusInfoDto`（明细内的状态项）

```java
@DtoInfo("单据状态dto 各个状态进行组合")
public class DeductionBillStatusInfoDto extends BaseDto {
    private DeductionFieldDto fieldDto;  // 表头字段（状态字段本身）
    private String caption;              // 显示名称，用于表头展示
    private String data;                 // 数据值（枚举项中文，如「草稿」）
    private String dataInfo;             // 数据值对应的属性值（枚举项 name，如 DRAFT）
    private boolean billStatus;          // 是否为单据状态字段
    private DeductionFieldTypeEnum type; // 字段类型，实测 BILL_STATUS
    private Long dataId;                 // 数据ID（枚举项 id）
}
```

`DeductionFieldTypeEnum` 实测取值 `BILL_STATUS`（同 `BillStatusOfJavaEnumRuleDetailServiceImpl` 里 `info.setType(DeductionFieldTypeEnum.BILL_STATUS)`）。

### 3.2 `DeductionFieldDto`（LIVE，init-data 实际返回）

```json
{
  "validate": true, "fixedValue": null,
  "attributeFullName": "com.seeyon.<appName><appId>.domain.entity.<Entity>.statusType",
  "attributeId": "<attrId>", "entityId": "<entityId>",
  "entityName": "<entityName>",
  "entityFullName": "com.seeyon.<appName><appId>.domain.entity.<Entity>",
  "attributeName": "statusType", "caption": "<状态字段中文名>",
  "fieldJavaType": "com.seeyon.<appName><appId>.enums.<Entity>billStatus",
  "dataType": "ENUM"
}
```

## 4. 生成机制（LIVE + STATIC 双向确认）

**触发条件**（`BillStatusOfJavaEnumRuleDetailServiceImpl.match`）：

```java
EntityDto entityDto = dto.getEntityDto();
boolean attributeMatch = attributes.anyMatch(x -> x.getName().equals("statusType") && x.getDataType()==ENUM);
return "bill".equals(entityDto.getStereotype()) && attributeMatch;
```

**两步都是硬门槛**：
1. `stereotype == 'bill'` —— 普通 `standard` 实体直接不匹配；
2. 存在 `name='statusType'` 且 `dataType=ENUM` 的属性 —— `generateTypeDataList` 里用 `Assert.isTrue(size==1, "单据状态字段是唯一的")` 断言唯一，用 `Assert.notNull(udcEnumDto, "单据状态枚举必定存在")` 断言枚举存在。

**笛卡尔展开**（`RuleDescartesService.generateDeductionRuleDetail`）：
- 遍历容器里所有 `RuleDetailService` 实现（当前仅 `BillStatusOfJavaEnumRuleDetailServiceImpl`，`@Order(1)`）；
- 每个实现产出 `List<DeductionBillStatusInfoDto>`（该实体状态枚举的全部项）；
- `DescartesUtils.getDescartes(dataList)` 做**笛卡尔积**；
- 每个积 = 一行 `DeductionRuleDetailDto`，`appId` 来自入参，`deductionBillStatusInfoDtoList` = 该行组合，其余字段（id/ruleId/algorithmId/orderNum/notice）全 null。

**实测验证**：
- `bill` 实体 `xianjinchituisong`（app `1656355078954763084`）→ init-data 返回 **8 行**明细（= 状态枚举 8 项），单行完整结构见 §6。
- `bill` 实体 `wrkjsq`（app `4396215186967839451`）→ 同样 **8 行**。
- 本应用 `standard` 实体 `xzhExp950795` → **0 行**（契约级负证据：不是没取到，是条件不满足）。

## 5. 写入接口契约（LIVE，实跑验证）

### 5.1 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| W | `POST /service/udc/deduction/rule` | 新增扣减规则（**内联明细**），`SingleResponse<DeductionResultDto>` |
| W | `POST /service/udc/deduction/rule/update` | 更新扣减规则（内联明细） |
| W | `POST /service/udc/deduction/rule/delete` | 删除规则（级联删明细） |
| R | `GET /service/udc/deduction/rule/{id}` | 读规则详情，返回含 `deductionRuleDetailDtoList` |
| R | `POST /service/udc/deduction/rule/search` | 规则列表（**不含明细**，只有头字段） |
| R | `POST /service/udc/deduction/rule/init-data` | **生成明细模板**（平台自己算出应有哪些行） |
| — | `POST /service/udc/deduction/rule/validRule` | 先校验（`checkRuleDetail` 在此链上） |

**没有独立的 detail 写端点对外**。`DeductionRuleDetailAppService` 有 `create/createBatch/update/selectByDeductionRuleId`，但 `DeductionRuleController` **未暴露**对应 REST 路径——明细只能随规则头一起提交。

### 5.2 必填与请求体形态（LIVE 实测）

`POST /udc/deduction/rule` 请求体里明细段：

```json
"deductionRuleDetailDtoList": [
  {
    "appId": "8704025620829192834",
    "algorithmCode": "s0alg",
    "orderNum": 1,
    "notice": "S0结构取证样本",
    "checkRule": null,
    "deductionBillStatusInfoDtoList": [
      {
        "fieldDto": {
          "attributeId": "8016904624316689195",
          "attributeFullName": "com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795.expText",
          "entityId": "474806313816300867",
          "entityName": "xzhExp950795",
          "entityFullName": "com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795",
          "attributeName": "expText",
          "caption": "实验文本(已改)",
          "dataType": "STRING"
        },
        "caption": "单据状态",
        "data": "草稿",
        "dataInfo": "DRAFT",
        "billStatus": true,
        "type": "BILL_STATUS"
      }
    ]
  }
]
```

**服务端会覆写/派生的字段**（`DeductionRuleService.handleDetail` + `buildRelationBetweenAlgorithmAndDetail`）：

| 字段 | 行为 |
|---|---|
| `id` | null 时服务端 `Ids.gidLong()` 生成 |
| `deductionRuleId` | **强制覆写**为规则头 id |
| `appId` | **强制覆写**为规则头 appId |
| `deductionAlgorithmId` | **不由客户端直传生效**：按 `algorithmCode` 去 `deductionAlgorithmDtoList` 里 `code` 匹配，命中才回填 id |
| `billStatusInfo` | 服务端由 `deductionBillStatusInfoDtoList` `JsonUtils.toJson` 生成 |
| `orderNum` | `createBatch` 覆盖为「现存明细数 + 递增」 |

### 5.3 校验规则（STATIC `DeductionRuleService.checkRuleDetail`）

```java
// 对每个明细行，若其第一个状态项 billStatus==true 且 dataInfo=="PENDING_REVIEW"
// 则 algorithmCode 与 deductionAlgorithmId 不能同时为空，否则：
throw new BusinessException("UDC_DEDUCTION_RULE_0013", data);
```

即「待审状态下必须指定算法」。`isPendingReview` 硬编码字符串 `"PENDING_REVIEW"`。

### 5.4 ★ update 路径的静默陷阱（LIVE 实测，重要）

`POST /udc/deduction/rule/update` 里明细走 `DeductionRuleDetailService.updateBatch`，其首行逻辑：

```java
List ids = detailDtoList.stream().map(BaseTraceableDto::getId)...;
List ruleDetailDataList = dao.selectByIds(ids);
if (CollectionUtils.isEmpty(ruleDetailDataList)) return 0;   // ← 静默返回 0
```

**后果**：给一条「明细为空」的既有规则用 update 追加明细（明细 DTO 无 id，或 id 在库中不存在）时，
接口仍返回 `BOOT_0000 / affectCount:1`，但 **detail 表 0 行**——200 与成功无关。
必须走 `POST /udc/deduction/rule`（create 路径 → `createBatch`）或给明细带上真实已存在 id。

**本次实测记录**：
- `rule/update` 追加无 id 明细 → HTTP 200 `{"validate":true,"affectCount":1}`，DB `udc_deduction_rule_detail` 仍 **0 行**（`probe_s0_readback.py` 回读）。
- `rule`（create）带 1 条明细 → HTTP 200 `{"id":"9146189328702437369","affectCount":1}`，DB `udc_deduction_rule_detail` **1 行**，字段值与请求逐项对账一致（见 §6）。
- 删除该探针规则 → HTTP 200 `{"content":1}`，DB 回到 **0 行**，原「小爪扣减规则」1 行未受影响。

## 6. 真实落库样本（LIVE，2026-10-17 15:17:20 实测）

探针规则 `9146189328702437369`（`S0明细结构取证` / `xzhS0DetailProbe*`）产生的明细行：

```
id                     -1053486964057834812
create_time            2026-10-17 15:17:20
tenant_id              -8112660841495312922
update_time            2026-10-17 15:17:20
version                0
guid                   -392464900923832725
publish_state          NULL
app_id                 8704025620829192834
bill_status_info       [{"validate":true,"fieldDto":{"validate":true,"fixedValue":null,
                         "attributeFullName":"com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795.expText",
                         "attributeId":8016904624316689195,"entityId":474806313816300867,
                         "entityName":"xzhExp950795",
                         "entityFullName":"com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795",
                         "attributeName":"expText","caption":"实验文本(已改)","fieldJavaType":null,
                         "dataType":"STRING"},"caption":"单据状态","data":"草稿","dataInfo":"DRAFT",
                         "billStatus":true,"type":"BILL_STATUS","dataId":null}]
check_rule             NULL
deduction_algorithm_id 8885745114777306199   ← 由 algorithmCode="s0alg" 关联得到
deduction_rule_id      9146189328702437369
notice                 S0结构取证样本
owner_code             NULL
backup_code            NULL
order_no               1
original_id            0
```

**关键观察**：
1. `deduction_algorithm_id` 确实由 `algorithmCode` 关联回填（请求里未直传该 id，落库却有值）。
2. `publish_state` 落库为 NULL，但 **读接口返回 `publishState:"PUBLISHED"`** —— 读时按 `PublishStateEnum.PUBLISHED(0)` 反序列化，NULL 与 0 在 DTO 层等价。**别拿读接口的 PUBLISHED 当「已发布」证据**。
3. `bill_status_info` 里 `fieldDto.attributeId`/`entityId` 是**裸 JSON 数字**，而 DTO 层是字符串——服务端 JSON 化时未统一类型，反向解析能兼容。
4. `fieldJavaType` 手写为 null 也落库成功（非必填）。

## 7. 本应用 vs 样本应用的严格区分

| 项 | 本应用 `datamigration9000000000000000001`（appId `8704025620829192834`） | 样本来源 |
|---|---|---|
| `udc_deduction_rule_detail` 原始行数 | **0 行**（取证前，机制必然：9 个实体全 `standard`，无 `statusType`） | — |
| `udc_deduction_rule` | 1 行（`xzhDedRule` / 小爪扣减规则 / `publishState=UNPUBLISH`） | — |
| 明细真实样本 | **本次授权自造 1 行**（探针规则，已删；表结构/写入语义由此 LIVE 确认） | 探针规则 `9146189328702437369` |
| 他应用 init-data 模板 | 不适用 | `xianjinchituisong`（app `1656355078954763084`，8 行）、`wrkjsq`（app `4396215186967839451`，8 行） |
| 全实例 detail 总行数 | `udc`=0 / `udc_test2`=0 / `udc_uat`=0（取证前；三 schema DDL 一致） | — |

**禁止混淆**：样本应用（`1656355078954763084` / `4396215186967839451`）的实体 id、枚举 id、appId **不得**回填进本应用契约当默认值。本应用若要真正产生明细行，前置条件是先把源实体改成 `bill` 原型并加 `statusType` ENUM —— 那属于后续阶段，不在本切片。

## 8. 复现脚本

| 脚本 | 作用 |
|---|---|
| `docs/audit/artifacts/scratch-migrated/root/probe_s0_detail.py` | 全 schema 定位 `udc_deduction_rule_detail` + `SHOW CREATE` |
| `docs/audit/artifacts/scratch-migrated/root/probe_s0_wide.py` | 全实例表族扫描 + 精确行数 |
| `docs/audit/artifacts/scratch-migrated/root/probe_s0_readback.py` | 明细表逐列回读 + 与 rule/algorithm 联查 |
| `docs/audit/artifacts/scratch-migrated/root/s0_initdata.py` | 调 `rule/init-data` 让平台生成明细模板（bill vs standard 对照） |
| `docs/audit/artifacts/scratch-migrated/root/s0_create_detail.py` | 授权应用内 create 带明细的探针规则 → 回读 → 删除 |
| `docs/audit/artifacts/scratch-migrated/root/s0_roundtrip.py` | `GET rule/{id}` 明细回读，核对服务端派生字段 |

反编译依据：`udc-common-5.3.517.jar`（`DeductionRuleDetailDto` / `DeductionBillStatusInfoDto` / `PublishStateEnum`）、`udc-dataflow-5.3.517.jar`（`DeductionRuleDetail` 实体 / `DeductionRuleService` / `DeductionRuleDetailService` / `RuleDescartesService` / `BillStatusOfJavaEnumRuleDetailServiceImpl`）、`udc-web-5.3.517.jar`（`DeductionRuleController`）。

## 9. 未验证 / 边界

- `UDC_DEDUCTION_RULE_0013`「待审必须指定算法」的**真实触发**未跑（需构造 `dataInfo=PENDING_REVIEW` 的明细行；本次只用 `DRAFT`）。
- `check_rule` 的表达式语法未取证（DTO 已 @Deprecated，推测被 `checkRule` 取代，两者实测均 NULL）。
- 明细的 `publish_state` 在**发布流程**（S1）中如何被写入，未取证。
- 笛卡尔积多实现场景（当前只有 1 个 `RuleDetailService` 实现）无法构造多列组合样本。
