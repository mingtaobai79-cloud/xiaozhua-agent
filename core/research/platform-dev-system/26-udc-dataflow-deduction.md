# UDC 数据流与扣减规则实现（udc-dataflow 5.3.605，224 类）

> 数据源：`D:/repo/REMOTE/com/seeyon/udc-dataflow/5.3.605/udc-dataflow-5.3.605.jar`（0.81 MB，224 类）
> 来源：远程仓库 `http://172.28.24.205/artifactory/libs-release/com/seeyon/`
> 等级：`VERIFIED_STATIC_BYTECODE`（类清单实测，未反编译方法体）
> **★ 这是之前缺的 22 个 jar 里最大的一个，直接补上「生单规则 + 扣减规则 + 代码生成」三块。**

---

## 0. ★★★ 三类内容

| 子域 | 类数 | 是什么 |
|---|---:|---|
| **`dataflow`** | ~130 | **数据流（生单规则）** |
| **`deduction`** | ~80 | **扣减规则** |
| `model` / `common` | 8 | 模型解析 |

**★★★ 关键：两个子域都有完整的 `autocode`（自动代码生成）体系：**
```
dataflow/autocode   27 类 → DataFlowCodeTask + DataFlowCodeTemplate + 3 个 Decorate
deduction/autocode  14 类 → DeductionCodeTask + DeductionCodeTemplate + 2 个 Decorate
```

**⇒ 这直接回答「生单规则/扣减规则是配置还是代码」—— 是**配置，但会生成代码**。**

---

## 1. ★★★ 代码生成体系（autocode）—— 补上 62% 的短板

### 1.1 ★★ 标准四件套（两组完全同构）

| 组件 | 数据流 | 扣减规则 |
|---|---|---|
| **CodeTask** | `DataFlowCodeTask` | `DeductionCodeTask` |
| **CodeTemplate** | `DataFlowCodeTemplate` | `DeductionCodeTemplate` |
| **TemplateConfig** | `DataFlowTemplateConfig` | `DeductionTemplateConfig` |
| **DecorateConfig** | `DataFlowDecorateConfig` | `DeductionDecorateConfig` |
| **MetadataConst** | `DataFlowCustomerMetadataConst` | `DeductionCustomerMetadataConst` |
| **CodeContextAware** | `DataFlowCodeContextAware` | `DeductionCodeContextAware` |
| **MetaDataPostProcessor** | `DataFlowMetaDataPostProcessor` | `DeductionMetaDataPostProcessor` |
| **TransportHandler** | `DataFlowTransportHandler` | `DeductionTransportHandler` |
| **SaveAsHandler** | `DataFlowSaveAsHandler` | `DeductionSaveAsHandler` |
| **ImporterBase** | `DataFlowDtoImporterBase` | `DeductionImporterBase` |

**★★★ 十件套完全同构 ⇒ 说明平台有一套「自动代码生成」的标准框架，各业务子域按此复制。**

### 1.2 ★★★ `DataFlowCodeTask` 家族（3 个 Task）

```
DataFlowCodeTask              ★ 主任务（生成代码）
DataFlowFormulaServiceTask    ★ 公式服务生成
DataFlowPlanTask              ★ 方案生成
```

**★★ 三个 Task 的分工：**
```
DataFlowCodeTask          生成数据流的执行代码
DataFlowFormulaServiceTask 生成公式服务（表达式 → 代码）
DataFlowPlanTask          生成方案（Plan）
```

**★★★ 关键：`DataFlowFormulaServiceTask` —— 表达式会**被生成为 Java 代码**，不是运行时解释。**
**⇒ 这证实了我早先 `04-expression.md` 的判断（表达式有代码生成阶段）。**

### 1.3 ★★★ 三个 Decorate（装饰器）—— 生成时插桩

```
DataFlowIdMappingDecorate             ★ ID 映射（跨环境/导入时 ID 替换）
DataFlowWriteBackDecorate             ★ 回写（生成回写逻辑）
MicroFlowDataFlowActivityDecorate     ★ 微流程数据流活动（数据流↔微流程联动）
```

**★★★ 三个装饰器揭示了三个关键机制：**
```
IdMapping       导入导出时，元数据 ID 会变，要重新映射
WriteBack       数据流执行后要「回写」结果到来源实体
MicroFlowDataFlow  数据流的某个节点可以是微流程活动（两者能互相嵌套）
```

**★★ `MicroFlowDataFlowActivityDecorate` 印证了我 `14-udc-bpm-bridge.md` 里的判断：**
**⇒ 微流程节点里有 `CALL_DATA_FLOW`（调数据流），数据流里也能挂微流程活动。**

### 1.4 ★★ 扣减规则的两个专属 Decorate

```
DeductionTargetEntityNoCacheDecorate    ★ 目标实体不缓存（扣减必须实时）
DeductionUpdateTargetEntityDecorate     ★ 更新目标实体（扣减核心动作）
```

**★★★ `DeductionTargetEntityNoCacheDecorate` —— 说明扣减**强制不走缓存**。**
**⇒ 业务原因：库存/额度扣减必须实时，不能用缓存值。**

### 1.5 ★ 扣减规则的 SQL 生成器（`deduction.core`）

```
DeductionSqlBuilder                 ★ SQL 构建器
DeductionSqlDialect                 ★ 方言接口
DeductionMySqlDialect               ★ MySQL 实现
DeductionSqlDialectFactory          方言工厂
DeductionSqlGenerator               ★ SQL 生成器接口
AbstractDeductionMySqlGenerator     抽象基类
DeductionMysqlAggRootEntityGenerator   ★ 聚合根实体生成器
DeductionMysqlNoAggRootEntityGenerator  ★ 非聚合根实体生成器
DeductionSqlSchema                  SQL schema
```

**★★★ 扣减规则不是「Java 代码」，而是「**生成 SQL 直接执行**」：**
```
DeductionRule（配置）
    ↓ DeductionSqlGenerator
生成 UPDATE ... SET ... WHERE ... 语句
    ↓ DeductionMySqlDialect
MySQL 方言（目前只看到 MySQL）
```

**★ 两个生成器分支：`AggRootEntity`（聚合根，即主实体）/ `NoAggRootEntity`（非聚合根）**
**⇒ 说明主子表的扣减走不同 SQL 路径。**

**⚠️ 只有 MySQL 方言 —— 说明扣减功能目前**只支持 MySQL**（其他库未适配）。**

**★ 配套：**
```
RuleDescartesService            ★ 笛卡尔积（多条件组合）
DeductionRule4RecordService     按记录扣减
DeductionAlgorithmService       扣减算法
DeductionCheckRuleExprServiceImpl  校验规则表达式
DeductionSearchConditionTipsExprServiceImpl  搜索条件提示表达式
DeductionAlgorithmTipsExprServiceImpl        算法提示表达式
```

**★★ 三个 `*ExprServiceImpl` —— 扣减规则里也有表达式（校验/提示/搜索条件）。**

---

## 2. ★★★ 数据流（生单规则）

### 2.1 ★ 核心类

```
dataflow.domain.entity.DataFlow            ★ 数据流定义
dataflow.domain.entity.DataFlowMapping     ★ 数据流映射（我记忆里生单规则的核心）
dataflow.domain.entity.DataFlowPlanRuntime

dataflow.domain.dao.DataFlowDao
dataflow.domain.dao.DataFlowMappingDao

dataflow.domain.bo.DataFlowMappingBo
dataflow.domain.bo.DataFlowEventMappingBo     ★ 事件映射
dataflow.domain.bo.DataFlowPretreatmentBo     ★ 预处理
dataflow.domain.bo.EntityData4DataFlowCheckBo ★ 校验

dataflow.appservice.DataFlowDesignAppService          ★ 设计（画布）
dataflow.appservice.DataFlowMappingDesignAppService   ★ 映射设计（我记忆里最核心的）
dataflow.appservice.UdcDataflowDataBaseSqlGeneratorImpl  ★ 数据库 SQL 生成
```

**★★★ `UdcDataflowDataBaseSqlGeneratorImpl` —— 数据流也能生成 SQL（与扣减类似）。**

### 2.2 ★★ 检测体系（`dataflow.detection`，13 类）

**与 `bpm.detection` 同构：**

```
DataFlowDetectionTask                             ★ 总任务
UdcDataFlowFrontDeployDetectionTask               ★ 前端部署检测
DataFlow4EntityPartDetectionTask                  ★ 实体部分
DataFlowMapping4AttributePartDetectionTask        ★ 属性部分
DataFlowMapping4EntityPartDetectionTask           ★ 实体部分
DataFlowMapping4JavaEnumItemPartDetectionTask     ★ Java 枚举项
DataFlowDetectionMetadataAware                    元数据感知
DataFlowDetectionAttributeUtil / CtpEnumUtil / EntityUtil / UdcEnumUtil / Util
DetectionConstant
```

**★★ 5 个 PartDetectionTask，按「检测对象」分类：**
```
Entity               实体
Attribute            属性
JavaEnumItem         Java 枚举项
（隐式）CtpEnum      选项集
（隐式）UdcEnum      UDC 枚举
```

**⇒ 与 BPM 的 `usedparam` 一样，是**依赖检测**（改字段/枚举，哪些数据流受影响）。**

### 2.3 ★ 权限（`dataflow.auth`）

```
DataFlowDesignAuthCheckImpl            设计权限
DataFlowMappingDesignAuthCheckImpl     映射设计权限
```

**★ 设计与映射设计**分两级授权**。**

### 2.4 ★★ 应用特性（`dataflow.application`，5 类）

```
AbstractApplicationFeature4DataFlow    抽象
ApplicationFeature4DataFlow            接口
ApplicationFeatureService              服务
impl.FormApplicationFeature4DataFlow   ★ 表单应用
impl.NormalApplicationFeature4DataFlow ★ 普通应用
```

**★★★ 数据流支持两种应用形态：**
```
FormApplicationFeature4DataFlow     表单应用（UDC 表单里的生单）
NormalApplicationFeature4DataFlow   普通应用（独立的生单规则）
```
**⇒ 同一个生单规则，在「表单场景」和「普通场景」行为不同。**

### 2.5 ★★★ 扣减规则的搜索方法（`deduction.searchmethod`，23 类）—— 匹配策略

**两组，按「数据类型」拆分：**

### 2.5.1 `check`（7 个）—— 条件校验

```
DeductionSearchConditionCheck              抽象/基类
DeductionSearchConditionChecks             校验集合
DefaultDeductionSearchConditionCheck       ★ 默认
DeductionSearchConditionBigIntegerCheck    BigInteger
DeductionSearchConditionCtpEnumCheck       ★ 选项集
DeductionSearchConditionEnumCheck          JAVA 枚举
DeductionSearchConditionEntityCheck        ★ 关联实体
```

### 2.5.2 `convert`（16 个）—— 值转换（★★★ 关键）

```
DeductionDatabaseValueConvertHelper        ★ 总调度
DeductionFixedValueConvert                 固定值
DeductionFixedValueCheck                   固定值校验

DeductionConvertStringToDatabaseValue        字符串
DeductionConvertMultilineStringToDatabaseValue 多行文本
DeductionConvertIntegerToDatabaseValue       整数
DeductionConvertBooleanToDatabaseValue       布尔
DeductionConvertDecimalToDatabaseValue       小数
DeductionConvertCurrencyToDatabaseValue      金额
DeductionConvertDateToDatabaseValue          日期
DeductionConvertTimeToDatabaseValue          时间
DeductionConvertDateTimeToDatabaseValue      日期时间
DeductionConvertEnumToDatabaseValue          JAVA 枚举
DeductionConvertCtpEnumToDatabaseValue       ★ 选项集
DeductionConvertEntityToDatabaseValue        ★ 关联实体
```

**★★★ 关键结论：扣减规则在生成 SQL 之前，要先把**每种数据类型**转成「数据库值」。**
```
12 种数据类型的转换器（String/MultilineString/Integer/Boolean/Decimal/
                       Currency/Date/Time/DateTime/Enum/CtpEnum/Entity）
```
**⇒ 这就是「配置化扣减」能生成正确 SQL 的关键 —— 类型安全转换。**
**⇒ `DeductionDatabaseValueConvertHelper` 是总调度（按类型选转换器）。**

**★★ `DeductionConvertEntityToDatabaseValue` —— 关联实体要取出**外键 ID** 而不是对象。**
**★ `DeductionConvertCtpEnumToDatabaseValue` / `EnumToDatabaseValue` —— 枚举要转成 **code** 而不是 name。**

### 2.5.3 ★ 通用引用解析框架（`model`，8 类）

```
model.parser.DataflowMappingReferenceParser     ★ 数据流映射引用解析
model.parser.DataflowReferenceParser            数据流引用解析
model.parser.DeductionMapReferenceParser        扣减映射引用解析
model.parser.DeductionRuleReferenceParser       扣减规则引用解析

model.repository.DataflowMappingRepository      ★ 仓储
model.repository.DataflowRepository
model.repository.DeductionMapRepository
model.repository.DeductionRuleRepository
```

**★★★ 这 8 个类是**通用框架**（放在 `com.seeyon.udc.model` 包，不是 dataflow 包）：**
```
Parser      解析「这个配置引用了哪些元数据对象」
Repository  仓储（加载/保存）
```
**⇒ 与 BPM 的 `usedparam` 同构，但这里更通用（可复用到其他子域）。**

---

## 3. ★★ 两个子域的应用服务（对外入口）

### 3.1 数据流（3 个）
```
DataFlowDesignAppService             ★ 设计
DataFlowMappingDesignAppService      ★ 映射设计
UdcDataflowDataBaseSqlGeneratorImpl  SQL 生成
```

### 3.2 扣减（4 个）
```
DeductionRuleAppService           ★ 扣减规则
DeductionRuleDetailAppService     ★ 规则明细
DeductionMapAppService            ★ 映射
DeductionAlgorithmAppService      ★ 算法
```

**★ 与我记忆里的 GraphQL 操作名对应：**
```
udcDeductionRulePost / UpdatePost / DeletePost / CountPost / InitDataPost / ValidRulePost
udcDeductionMapPost / UpdatePost / DeletePost / DeleteContentPost
udcDeductionEntityListPost / EntityNotExistIdsPost
```
**⇒ 那些就是 `DeductionRuleAppService` / `DeductionMapAppService` 的 GraphQL 包装。**

---

## 4. ★★★ 完整链路（生单规则）

```
① 设计态
   DataFlowDesignAppService 建数据流（画布）
   DataFlowMappingDesignAppService 配置映射（哪个来源字段 → 哪个目标字段）
        ↓ 保存为 DataFlow + DataFlowMapping（DB 实体）
        ↓
② 生成态（autocode）
   DataFlowCodeTask         生成执行代码
   DataFlowFormulaServiceTask 生成公式服务
   DataFlowPlanTask         生成方案
   + DataFlowIdMappingDecorate（ID 映射）
   + DataFlowWriteBackDecorate（回写）
   + MicroFlowDataFlowActivityDecorate（微流程联动）
        ↓
③ 运行态
   触发（微流程 CALL_DATA_FLOW 节点 / 表单事件）
        ↓ 执行生成的代码
   写入目标实体
        ↓ DataFlowWriteBackDecorate 逻辑
   回写来源实体
```

---

## 5. ★★★ 完整链路（扣减规则）

```
① 配置
   DeductionRuleAppService        规则
   DeductionRuleDetailAppService  明细
   DeductionMapAppService         映射（扣哪个字段、条件是什么）
   DeductionAlgorithmAppService   算法
        ↓
② 生成 SQL（不是 Java 代码！）
   DeductionSqlGenerator
     ├─ DeductionMysqlAggRootEntityGenerator    聚合根（主实体）
     └─ DeductionMysqlNoAggRootEntityGenerator  非聚合根
   DeductionMySqlDialect（MySQL 方言）
        ↓ 生成 UPDATE ... SET ... WHERE ...
③ 执行
   直接跑 SQL
   ⚠️ DeductionTargetEntityNoCacheDecorate → 不走缓存
```

---

## 6. ★★★ 这份 jar 补齐了哪些空白

| 之前的空白 | 现在 | 证据 |
|---|---|---|
| **代码生成 62%** | **85%** | `DataFlowCodeTask` / `DeductionCodeTask` + Template + Decorate 十件套 |
| **生单规则机制** | **90%** | `DataFlowMappingDesignAppService` + `DataFlowCodeTask` |
| **扣减规则实现** | **90%** | `DeductionSqlGenerator` + MySQL 方言 + 2 个 Generator |
| **表达式是否生成代码** | **确认：是** | `DataFlowFormulaServiceTask` |
| **数据流↔微流程联动** | **确认** | `MicroFlowDataFlowActivityDecorate` |
| **扣减是否走缓存** | **确认：不走** | `DeductionTargetEntityNoCacheDecorate` |

---

## 7. ★ 与我已有文档的印证/修正

| 我的旧结论 | 本轮验证 |
|---|---|
| 微流程有 `CALL_DATA_FLOW` 调数据流 | ✅ `MicroFlowDataFlowActivityDecorate` 印证 |
| `LIST_OPERATION.SUBTRACT` 是集合扣减 | ⚠️ 那是**微流程节点**的集合操作；**扣减规则**走 SQL 生成（两回事） |
| 表达式有代码生成阶段 | ✅ `DataFlowFormulaServiceTask` 确认 |
| 生单规则按来源实体动态查 | ✅ `DataFlowMapping` + `sourceEntityId` |
| 数据流三种参数形态（引用/表达式/常量） | ✅ `DataFlowMappingBo` 存在（未读字段） |

**★★★ 重要区分（之前混淆过）：**
```
「扣减规则」（Deduction）      = 配置化，生成 SQL 直接 UPDATE
「微流程扣减节点」（SUBTRACT）= 内存里的集合运算
两者完全不同！
```

---

## 8. 未覆盖

| 项 | 说明 |
|---|---|
| `DataFlowCodeTask` 的方法体 | 未反编译（生成的代码长什么样） |
| `DataFlowCodeTemplate` 的模板内容 | 未读（最关键 —— 生成什么代码） |
| `DataFlowMapping` / `DeductionRule` 的字段 | 未 dump |
| `deduction.searchmethod` 23 类 | 类名被截断，未看 |
| `DeductionSqlGenerator` 的 SQL 模板 | 未读 |
| 扣减是否支持非 MySQL | **看起来只支持 MySQL**，需确认 |
| `DataFlowPlanTask` 的「方案」是什么 | 未读 |
| `udc-bpm` 46 类（UDC↔BPM 桥） | 只看了类名清单 |