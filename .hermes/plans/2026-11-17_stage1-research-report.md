# 阶段 1 研究报告：统计口径 · 元数据全景 · 生成器映射 · 证据地图

> **状态：静态研究，未经审计不得转为正式 facts。**
> 本轮未操作 test2、未改业务代码、未修改现有 facts。
> 生成日期：2026-11-17
> 平台版本：`udc-platform-5.3.517`
> 对应计划：`.hermes/plans/2026-11-17_platform-dev-system-research-v4.md`（阶段 1）

---

## 0. 阅读指引

本文是**阶段 1 交付物**，包含 5 个部分：

| 节 | 内容 | 是否可直接进 facts |
|---|---|---|
| §1 | 统计口径登记表 | ❌ 需审计后转为 `statistics-registry.md` |
| §2 | 元数据对象全景清单 | ❌ 待审计 |
| §3 | CodeTask ↔ Template 映射 | ❌ 待审计 |
| §4 | 模板资源与版本选择证据 | ❌ 待审计 |
| §5 | 现有资产与缺失证据地图 | ❌ 待审计 |

**所有结论都标注了证据等级与可复现依据。**
统计数字全部由 `scripts/research/stats_registry.py` 生成，可重跑。

---

## 1. 统计口径登记表

### 1.1 通用信息

| 项 | 值 |
|---|---|
| 数据源根 | `C:/Users/白明涛/xiaozhua-agent` |
| 平台版本 | `udc-platform-5.3.517` |
| 统计脚本 | `scripts/research/stats_registry.py` |
| 复现命令 | `./.venv/Scripts/python.exe scripts/research/stats_registry.py --md` |
| 统计时间 | 2026-11-17 01:03:07 |
| 是否只读 | 是（脚本无任何写操作） |

### 1.2 逐项登记

#### S1 签名库总量

| 字段 | 内容 |
|---|---|
| 统计对象 | 全平台类与方法签名 |
| 数据源 | `docs/audit/signatures.txt.gz`（2,236,202 bytes） |
| 版本 | udc-platform-5.3.517 |
| 统计规则 | 逐行读取；第 2 列为 `class/interface/enum/@interface` 者计为类声明；含 `#` 且含 `(` 者计为方法声明 |
| 结果 | 总行数 **245709**；类声明 **21389**；方法声明 **224320** |
| 证据等级 | `STATIC_RULE` |
| 已知局限 | 签名不含方法体，无法证明运行行为 |

#### S2 CodeTask 实现类

| 字段 | 内容 |
|---|---|
| 统计对象 | 实现/声明 `code(CodeContext)` 的类 |
| 数据源 | `docs/audit/signatures.txt.gz` |
| 统计规则 | 检索含 `#code(com.seeyon.udc.common.autocode.context.CodeContext)` 的行，取 `#` 前类名去重 |
| 结果 | **53 个** |
| 证据等级 | `VERIFIED_STATIC_BYTECODE`（签名级，非实现级） |

**53 个的构成（必须区分，不能只报一个数字）：**

| 包 | 数量 | 性质 |
|---|---|---|
| `com.seeyon.udc.autocode.task` | 30 | 主生成任务 |
| `com.seeyon.udc.autocode.task.front` | 5 | 前端元数据任务 |
| `com.seeyon.udc.autocode.v27.task` | 9 | **版本化任务（v27）** |
| `com.seeyon.udc.autocode.v27.task.front` | 5 | **版本化前端任务（v27）** |
| `com.seeyon.udc.common.autocode` | 1 | **接口自身 `CodeTask`，不是实现** |
| `com.seeyon.udc.extend.task` | 1 | 扩展任务 `CtpExcelJsonTask` |
| `com.seeyon.udc.extend.detection.associate.deploy` | 1 | 扩展任务 `AssociateCodeTask` |
| `com.seeyon.udc.extend.domain.service.deploy` | 1 | 扩展任务 `CtpEnumCodeTask` |

**⇒ 关键口径结论：**
- **真实实现类 = 52 个**（53 减去接口自身）
- 其中 **版本化 v27 任务 14 个**（9 + 5）
- 其中 **扩展包任务 3 个**（extend.*）
- **主任务 30 个**

**对照口径（不可混用）：** 类名以 `Task` 结尾的全平台类 = **204 个**。
这个数字包含大量与代码生成无关的 Task，**不能当作 CodeTask 实现数**。

**v3 的「32 个」来源已查明，且这个数字本身需要拆解：**

`com.seeyon.udc.autocode.task` 包内 `class` 声明 = **32 个**，但其中：
- `AbstractMicroFlowCodeTask` —— **抽象基类，不实现 `code()`**
- `PageControllerTask` —— **在本包内未声明 `code(CodeContext)`**（可能继承自外部基类）
- 其余 **30 个**声明了 `code(CodeContext)`

**⇒ v3 的 32 是「包内 class 声明数」，比实际实现多 2 个。**
**⇒ v4 的 53 是「全库声明 code(CodeContext) 的类去重」，比包内多出 v27 与 extend 部分。**
**两个数字都对，但口径完全不同，不能互相替代。**

#### S3 Template 类

**必须区分两个完全不同的口径：**

| 口径 | 定义 | 数量 | 适用 |
|---|---|---|---|
| **A（主）** | 声明 `getTemplateOutMap()` 的类去重 | **36** | ≈ 实际参与生成的模板载体 |
| B（对照） | 类名以 `Template` 结尾的全平台类 | **74** | 含 bpm/cip/portal 无关模板，**不可用** |

**口径 A 的 36 个构成：**

| 包 | 数量 |
|---|---|
| `com.seeyon.udc.autocode.template` | 23 |
| `com.seeyon.udc.autocode.v27.template` | 13 |

**另有 4 个抽象基类（不是模板载体本身）：**
```
com.seeyon.udc.autocode.template.base.AbstractUdcFreemarkerTemplate
com.seeyon.udc.autocode.template.base.AbstractUdcDecoratableFreemarkerTemplate
com.seeyon.udc.autocode.template.base.AbstractDecorateEntityTemplate
com.seeyon.udc.autocode.template.base.AbstractDecorateMicroFlowTemplate
```

**⇒ 口径结论：**
- `getTemplateOutMap()` 是模板载体的**必要条件**（有它才能输出文件映射）
- 但**不能反推**「36 个 = 实际参与某次生成的模板数」——一次生成只走其中一部分
- **实际参与生成的模板数 = 动态的**，取决于应用里有哪些元数据

**v4 计划中写的「24 个」来源已查明：** 那是按类名手工枚举的估算值，非脚本统计。
**⇒ v4 的 24 是手工枚举，已废弃，以 36 为准。**

#### S4 模板清单 `_codegen_templates.json`

| 字段 | 内容 |
|---|---|
| 统计对象 | 模板资源记录 |
| 数据源 | `udc-platform-5.3.517.tar.gz` 内 `udc-biz-5.3.517/_codegen_templates.json` |
| 统计规则 | 解析 JSON，对 41 个顶层 key 的 value 数组求和 |
| 结果 | 分组 **41**，条目 **464** |
| 版本分布 | 2.7 → 13 组；2.8 → 14 组；2.9 → 13 组；3.0 → 1 组 |
| 证据等级 | `STATIC_RULE` |
| **重要局限** | ① 条目含目录占位（如 `"third/"`），**不是纯文件数** ② 只证明**资产记录存在**，不证明选择机制 ③ 不含 .ftl 文件内容 |

#### S5 DAO 方法

| 类 | 方法数 | 唯一名 | 重载数 |
|---|---|---|---|
| `com.seeyon.boot.starter.mybatis.inone.dao.AllInOneBaseDao`（接口） | **41** | 36 | 5 |
| `com.seeyon.boot.starter.mybatis.AbstractAllInOneBaseDao`（抽象类） | **55** | 50 | 5 |

**⇒ 口径结论：**
- 41 是**接口声明**的方法数，含 5 组重载（同名不同参）
- 55 是**抽象类**的方法数，**包含父类方法**（签名库对该类只列自身声明+继承可见的公开方法）
- **两者不是「41 + 55 = 96」的简单相加关系**——抽象类实现了接口，方法有重叠
- **未判定：** 实现类（各实体生成的 `*Dao`）如何继承、是否覆盖

**v4 写的「41 方法」正确，但当时未区分「唯一名 36 / 重载 5」，也未说明抽象类关系。已补正。**

#### S6 AppService

**必须区分四个口径：**

| 口径 | 定义 | 数量 |
|---|---|---|
| 文件总行数 | `svc-app-service.txt.gz` 全部行 | 10176 |
| 含方法行 | 含 `#` 的行 | **9343** |
| 唯一 owner 类 | `#` 前类名去重 | **830** |
| 名字以 `AppService` 结尾 | 上述 830 中符合 | **830**（全部） |
| 名字以 `AppServiceImpl` 结尾 | 上述 830 中符合 | **0** |

**⇒ 关键发现：该文件 830 个 owner 全部是 `*AppService`（接口），零个 `*AppServiceImpl`。**
说明这是**对外暴露的 AppService 接口清单**，不含实现类。

**⇒ 口径结论：**
- 「830」= **AppService 接口类数**（不是实现类数，不是能力数）
- 「9343」= **这些接口声明的方法总数**
- **一个接口 ≠ 一种能力**；一个接口平均 11.3 个方法
- **v4 写的「1000 个 AppService」是概数，已废弃；v4 修正稿写的「830 类 / 9343 方法」正确**

#### S7 udc 实体 Service 接口

| 字段 | 内容 |
|---|---|
| 统计规则 | 类名匹配 `udc.*\.(api\|service)\.\w+Service$` 且有方法行 |
| 结果 | **179** |
| 证据等级 | `VERIFIED_STATIC_BYTECODE` |
| 局限 | 这是「平台预置的实体领域服务」；各客户应用生成的 Service 不在签名库内 |

### 1.3 数字变更台账（v4 → 阶段 1）

| 指标 | v4 报告值 | 阶段 1 实测 | 差异原因 |
|---|---|---|---|
| CodeTask 实现 | 53 | **53**（含接口）/ **52**（实现） | v4 未区分接口自身 |
| CodeTask 包内类数 | 32（v3） | 32（确认为包内 class 数） | 口径不同，v3 误用 |
| Template | 36 | **36**（口径 A）/ 74（口径 B） | v4 未给对照口径 |
| Template（v3） | 24 | 废弃 | 手工枚举，非脚本 |
| 模板条目 | 464 | **464** | 一致 |
| 模板分组 | 41 | **41** | 一致 |
| AppService 类 | 830 | **830**（全为接口） | v4 未说明零实现类 |
| AppService 方法 | 9343 | **9343** | 一致 |
| DAO 接口方法 | 41 | **41**（唯一名 36，重载 5） | v4 未给重载信息 |
| DAO 抽象类方法 | 55 | **55**（唯一名 50，重载 5） | v4 未给重载信息 |

**⇒ 所有数字已可复现。任何后续报告必须引用本表口径，不得只写裸数字。**

---

## 2. 元数据对象全景清单

### 2.1 证据来源

```
udc-biz-5.3.517/resources/stereotype/*/config.json          6 份
udc-biz-5.3.517/resources/feature/*/config.json             26 份
udc-biz-5.3.517/resources/presetData/*.json                 14 份
udc-biz-5.3.517/resources/openApi/entityOpenApi.json
udc-biz-5.3.517/resources/upgrade/componentMapping.json
udc-biz-5.3.517/resources/microflow/*.json                  9 份
udc-biz-5.3.517/resources/auth/*.json                       2 份
core/facts/udc/entity/evidence/entity-write-2026-10-23/stereotype-authoritative.json
```

### 2.2 六种实体类型（逐字核实）

| stereotype | 中文 | necessaryFeatures（逐字） |
|---|---|---|
| `standard` | 标准 | `basic` |
| `form` | 表单 | `basic`, `formBasic` |
| `basicData` | 基础资料 | `basic` |
| `bill` | 单据 | `basic`, `approve`, `organization`, `billBasic`, `termination`, `suspend`, `nullify` |
| `archive` | 平铺档案 | `basic`, `archiveBasic`, `approve`, `archiveTiled` |
| `archiveTree` | 树形档案 | `basic`, `archiveBasic`, `approve`, `treeEntity` |

**证据等级：** `VERIFIED_STATIC_BYTECODE`（来自 stereotype-authoritative.json，已有实测核实记录）

**待验证：** 特性列表相同/相近的实体（如 `standard` 与 `basicData` 都只有 `basic`），
**它们的生成物与运行时行为是否真的相同？** 必须靠专题 2 实测产物对比。

### 2.3 26 个 feature 清单（文件存在，语义待解析）

```
approve                     archive_basic               archive_tiled
attribute_scalability       attribute_scalability_global basic
bill_basic                  disable                     form_basic
fulltext_search             nullify                     organization
secret_level                send_down                   suspend
termination                 tree_entity                 validity_period
```

**（共 18 个顶层 feature；另有 8 个子目录带 template/config.json，合计 26 个 config.json）**

**状态：** `STATIC_RULE`（文件存在）→ 语义待解析（专题 1 阶段 2）

### 2.4 presetData 元数据对象

| 文件 | 内容（据文件名） | 状态 |
|---|---|---|
| `entity.json` | 实体定义 | 待解析 |
| `attribute.json` | 字段定义 | 待解析 |
| `attributeSet.json` | 字段集 | 待解析 |
| `customerAttributeSet.json` | 客户字段集 | 待解析 |
| `presetAttributeCapacity.json` | 字段容量 | 待解析 |
| `dependencyGraph.json` | **对象依赖图** | 待解析（★ 关键） |
| `billEnum.json` / `formEnum.json` / `archiveEnum.json` | 各类型枚举 | 待解析 |
| `scalability.json` / `scalabilityGlobal.json` | 扩展机制 | 待解析 |
| `basicDataEntityExtension.json` | 基础资料扩展 | 待解析 |
| `event/defaultevent.json` | 默认事件 | 待解析 |

### 2.5 元数据对象关系（当前已知，待补全）

```
Application
  ├─ Entity（6 stereotype）
  │    ├─ Attribute（字段）
  │    │    ├─ relationEntity（关联字段）
  │    │    ├─ multiSelect（多选）
  │    │    └─ 默认值表达式
  │    ├─ EntityRelation（关联，EntityRelationMultiplicityEnum）
  │    ├─ Aggregation（聚合 = 主子表）
  │    └─ Feature（特性，26 种）
  ├─ Page（页面）
  ├─ MicroFlow（微流程，29 Activity 模板）
  ├─ Enum（枚举：UdcEnum / CtpEnum）
  ├─ Serial（流水号）
  └─ OpenApi（entityOpenApi.json）
```

**⇒ 这是当前可证的骨架，`dependencyGraph.json` 解析后才能补全依赖方向。**

### 2.6 参与生成 vs 参与运行时（初步判断，待证）

| 对象 | 参与代码生成 | 参与运行时 | 依据 |
|---|---|---|---|
| Application | ✅ | ✅ | `AutoCodeExecutor#execute(ApplicationDto, ...)` |
| Entity | ✅ | ✅ | 生成 entity/dto/dao；运行时元数据 |
| Attribute | ✅ | ✅ | `getJavaType(AttributeDto)` |
| EntityRelation | ✅ | ✅ | 生成关联字段 |
| Aggregation | ✅ | ✅ | `getEntityReferAgg4CodeDto` |
| Feature | ✅ | ✅ | `resolveBpmProcess` / `resolveSerial` |
| Page | ✅ | ✅ | `PageControllerTask` |
| MicroFlow | ✅ | ✅ | `MicroFlowCodeTask` |
| Enum | ✅ | ✅ | `EnumTask` |
| Serial | ✅ | ✅ | `SerialConfigTask` |
| OpenApi | ✅ | ✅ | `resolveOpenApiData` |

**⇒ 全部对象都既参与生成又参与运行时。** 差别在**参与深度**，待专题 2 量化。

---

## 3. CodeTask ↔ Template 映射

### 3.1 已证实的调度链路（签名级）

```
CodeParam
  ├─ getCodeVersion(): String              ← ★ 版本
  ├─ getCodeLanguage(): CodeLanguage       ← 语言
  ├─ getContextTypeEnum(): ContextTypeEnum
  ├─ isDeploy(): boolean                   ← ★ 是否部署
  ├─ getDeployId(): Long
  ├─ getCodeTaskList(): List<CodeTask>     ← ★ 任务列表
  ├─ getInterceptorList(): List<TemplateInterceptor>   ← ★ 模板拦截
  ├─ getTransportHandlerList(): List<TransportHandler> ← ★ 部署传输
  ├─ getContextAwareList(): List<CodeContextAware>
  ├─ getDynamicArgs(): Map<String,Object>
  └─ getComparedSchemaIdSet(): Set<String>  ← 增量对比

        ↓ AutoCodeExecutor#execute(ApplicationDto, CodeParam)

CodeContext
  ├─ getAutoCodeProperties(): AutoCodeProperties   ← ★ 模板目录/版本配置
  ├─ getVersionControl(): VersionControl
  ├─ getBasePackage() / getAppName4Package()
  ├─ getModelJavaPath(String...)                   ← ★ Java 输出路径
  ├─ getModelResourcePath(String...)               ← ★ 资源输出路径
  ├─ getAppDbInfoDto() / getI18nContext()
  └─ (共 13 个方法，不含实体元数据本身)

        ↓ AutoCodeExecutor#runTask(CodeContext, List<CodeTask>)

CodeTask#code(CodeContext): String     ← 52 个实现
        ↓
<Template>#getTemplateOutMap(): Map<String,String>   ← 模板名 → 输出路径
<Template>#getArgumentMap(): Map<String,Object>      ← 渲染参数
        ↓
AbstractUdcFreemarkerTemplate#writeToString(Object, String): String
        ↓
TransportHandler#out(CodeContext): List<SchemaInfo>  ← ★ 部署
```

**★ 阶段 1 的关键发现（v4 未包含）：**

1. **CodeTask 不是硬编码列表，由插件注册**
   ```
   com.seeyon.udc.PluginDefinition#getCodeTasks(): Collection<CodeTask>
   com.seeyon.udc.common.autocode.extension.param.CodeParam#addTask(CodeTask)
                                                          #addAllTask(List<CodeTask>)
   ```
   ⇒ **「32/52 个 Task 谁被选中」取决于运行时注册了哪些插件**，不是静态全跑。

2. **版本选择由 CodeParam 驱动**
   ```
   CodeParam#getCodeVersion(): String
   CodeParam#setCodeVersion(String)
   AutoCodeProperties#getCodeVersions(): List<String>       ← 支持的版本列表
   AutoCodeProperties#getDefaultTemplatePrefix(): String
   AutoCodeProperties#getTemplateDir(): String              ← 模板根目录
   ```

3. **模板可被拦截改写**
   ```
   TemplateInterceptor（接口）
     ├─ SanyTemplateInterceptor
     ├─ Sany2TemplateInterceptor
     └─ SanyContractBasicDataTemplateInterceptor
   CodeParam#addTemplateInterceptor(...)
   ```
   ⇒ **同一个模板在不同客户下可产出不同代码**，这是「模板 → 产物」不能简单一对一的原因。

4. **部署是独立阶段**
   ```
   TransportHandler（接口）
     # out(CodeContext): List<SchemaInfo>
     # compare(SchemaComparisonSourcePool)
     # isFormDeploy(CodeContext): boolean
     # group(): String
   ```
   已枚举 **30+ 个 TransportHandler**（Entity/Dto/Page/MicroFlow/UdcEnum/SerialNumber/
   GanttChart/FormConvert/CtpQrCodeRule/FilterPlan/ReferConfig/Scalability/...）

   ⇒ **「生成文件」和「部署到平台」是两件事**，v4 的链路缺了这一环。

### 3.2 CodeTask ↔ Template 候选映射

**⚠️ 严格声明：下表是「命名与包结构上的候选对应」，不是已证实的调用关系。**
证实需要：① 反编译 `code()` 方法体看它 new 了哪个 Template；② 或实测产物反推。

| CodeTask（主包，30） | 候选 Template | 对应依据 |
|---|---|---|
| `EntityTask` | `EntityFileTemplate` | `EntityTask#deployEntity(EntityFileTemplate, EntityDto)` **★ 签名直接证实** |
| `EntityRuleTask` | `EntityRuleTemplate` + `EntityRuleAggregateTemplate` | 命名 + `EntityRuleAggregateTemplate#getLayerMap` |
| `DtoTask` | `DtoCodeTemplate` | 命名 |
| `PageEntityControllerTask` | `PageEntityControllerTemplate` | 命名 |
| `PageControllerTask` | `PageControllerTemplate` | 命名 |
| `ReferConfigTask` | `ReferTemplate` | 命名 |
| `ReferControllerTask` | `EntityReferTemplate` / `EntityReferTemplate2` | 命名 |
| `MicroFlowCodeTask` | `MicroFlowTemplate` | 命名 |
| `MicroFlowScheduleJobTask` | `MicroFlowScheduleTemplate` | 命名 |
| `HostAppMicroFlowCodeTask` | `HostAppMicroFlowTemplate` | 命名 |
| `FilterPlanTask` | `FilterPlanTemplate` | 命名 |
| `DynamicSearchTask` | `DynamicSearchTemplate` | 命名 |
| `OutAppAppServiceProxyTask` | `OutAppAppServiceProxyTemplate` | 命名 |
| `StaticFileTask` / `StaticExtFileTask` | `StaticFileTemplate` | 命名 |
| `AttachmentTemplateTask` | ? | **无对应 Template** |
| `CodeConfigTask` | ? | **无对应 Template** |
| `EnumTask` | ?（可能走 `enums.java.ftl` 无 Template 类） | **无对应 Template** |
| `EventTask` | `ConnectorBusinessEventTemplate`? | 弱 |
| `SerialConfigTask` | ? | **无对应 Template** |
| `CtpJobTask` | ? | **无对应 Template** |
| `CtpEnumIdsMetadataTask` | ? | **无对应 Template** |
| `AppBeanNameModifyerTask` | ? | **无对应 Template** |
| `AppBuildInfoTask` | ? | **无对应 Template** |
| `AppDependenciesTask` | ? | **无对应 Template** |
| `AppInitFileTask` | ? | **无对应 Template** |
| `MgnInitFileTask` | ? | **无对应 Template** |
| `OssMetadataTask` | ? | **无对应 Template** |
| `PageInfoTask` | ? | **无对应 Template** |
| `ReferenceMetaDataTask` | ? | **无对应 Template** |
| `TestDeployStaticFileTask` | `StaticFileTemplate`? | 弱 |

**⇒ 关键结论：**

- **只有 `EntityTask → EntityFileTemplate` 有签名级直接证据**
  （`EntityTask#deployEntity(EntityFileTemplate, EntityDto): String`）
- **其余 29 个主任务中，约 13 个有命名对应的候选 Template，约 16 个无对应**
- **⇒ 绝对不能宣称「CodeTask 与 Template 一一对应」**
- 无对应 Template 的任务，说明它们要么不渲染模板（纯逻辑生成字符串），
  要么模板载体不在 36 个口径 A 内

**v27 包 14 个任务 + 13 个 Template 的对应关系同样待证。**

### 3.3 待证问题清单（交给阶段 2）

| # | 问题 | 验证方法 |
|---|---|---|
| 1 | 每个 CodeTask 实际 new 了哪个 Template | 反编译 `code()` 方法体 |
| 2 | `matches()` 条件如何决定 Task 是否执行 | 反编译（`EntityRuleTask#matches` 已见） |
| 3 | `getTemplateOutMap()` 的 key 是模板路径还是逻辑名 | 反编译或实测 |
| 4 | `writeToString(Object, String)` 第二参是模板路径吗 | 反编译基类 |
| 5 | v27 任务与主任务的启用条件 | 查 `CodeParam#getCodeVersion` 的取值来源 |
| 6 | `TemplateInterceptor` 如何改写模板 | 反编译 3 个 Sany 实现 |
| 7 | `TransportHandler` 与生成文件如何对应 | 反编译 `EntityTransportHandler#out` |

---

## 4. 模板资源与版本选择证据

### 4.1 版本维度（已证实存在）

`_codegen_templates.json` 顶层 key 含版本前缀：

```
2.7/*   13 组
2.8/*   14 组
2.9/*   13 组
3.0/*    1 组（仅 entity，2 条）
```

**⇒ 模板按平台版本分目录，这是事实（`STATIC_RULE`）。**

**但「谁决定用哪个版本」当时未查到。阶段 1 已找到答案（见 4.2）。**

### 4.2 版本选择机制（★ 阶段 1 核心发现）

```java
com.seeyon.udc.common.autocode.extension.param.CodeParam
  # getCodeVersion(): String              ← 每次生成传入的版本
  # setCodeVersion(String): void

com.seeyon.udc.common.autocode.config.AutoCodeProperties
  # getCodeVersions(): List<String>       ← 平台支持的版本列表
  # getDefaultTemplatePrefix(): String    ← 默认模板前缀
  # getTemplateDir(): String              ← 模板根目录
  # getProjectDir(): String               ← 项目输出目录
  # getProjectExtDir(): String            ← 扩展输出目录
  # getTestDeployProjectDir(): String     ← 测试部署目录
  # getNeedInterceptTemplate(): Boolean   ← ★ 是否启用模板拦截
  # getFormatJava(): Boolean              ← 是否格式化 Java
  # getWriteAsync(): Boolean              ← 是否异步写
  # getOutputTimeOut(): Integer           ← 输出超时
  # getPresetSchema(): Boolean            ← 是否预置 schema
  # getSupportDbType(): List<String>      ← 支持的数据库类型
  # getCreateRollbackSql(): Boolean       ← 是否生成回滚 SQL
  # getCompatibilityCheck(): Boolean      ← 兼容性检查
  # getTransportExtendCode(): Boolean     ← 是否传输扩展代码
  # getCopyExtendCode(): Boolean
  # getEnablePublishState(): Boolean
  # getSchemaCacheTimeOut(): Integer
  # getContextType(): String
  # getAppCapacity(): Integer
  # getAppTemplateCapacity(): Integer
  # getEnableSchemaConfig(): Boolean
  # getDetectAfterImport(): Boolean
  # getCustomerMetadataList(): List<String>
  # getUdcMetadataList(): List<String>
  # getEnableDropColumn(): Boolean
  # getEnableWriteContext(): Boolean
  # getDownloadFatAppPackage(): Boolean
```

**⇒ 结论：版本选择是「配置 + 调用方传入」双驱动，不是硬编码 if-else。**

**证据等级：** `VERIFIED_STATIC_BYTECODE`（签名级）
**待证：** `getCodeVersion()` 的实际取值来源（前端传入？应用配置？平台版本？）→ 需反编译或实测。

### 4.3 模板加载路径（部分可证）

```java
CodeContext#getModelJavaPath(String...): String      ← Java 文件输出路径
CodeContext#getModelResourcePath(String...): String  ← 资源文件输出路径
CodeContext#getBasePackagePathStr(): String
CodeContext#getPackage(ApplicationDto, String...): String

AutoCodeProperties#getTemplateDir(): String          ← 模板根目录
AutoCodeProperties#getDefaultTemplatePrefix(): String
```

**⇒ 模板根目录由配置提供（`getTemplateDir()`），输出路径由 `CodeContext` 拼接。**
**待证：** 具体拼接规则（需反编译这两个方法）。

### 4.4 模板拦截（★ v4 完全遗漏的机制）

```java
// 引用点（签名库可证）
com.seeyon.udc.common.autocode.extension.param.CodeParam
  # addTemplateInterceptor(com.seeyon.boot.starter.autocode.template.TemplateInterceptor)
  # addAllTemplateInterceptor(List<TemplateInterceptor>)
  # getInterceptorList(): List<TemplateInterceptor>
  # setInterceptorList(List<TemplateInterceptor>)

com.seeyon.udc.common.autocode.context.AppCodeContext
  # getInterceptorList(): List<TemplateInterceptor>

com.seeyon.udc.autocode.interceptor.BaseAppCodeParamInterceptor

com.seeyon.udc.common.autocode.config.AutoCodeProperties
  # getNeedInterceptTemplate(): Boolean   ← 开关

// 已实现（3 个，均在客户定制包，签名库有 class 声明）
com.seeyon.udc.autocode.interceptor.template.SanyTemplateInterceptor
com.seeyon.udc.autocode.interceptor.template.Sany2TemplateInterceptor
com.seeyon.udc.autocode.interceptor.template.SanyContractBasicDataTemplateInterceptor
```

**⚠️ 证据边界（自检发现）：**
- `TemplateInterceptor` **接口自身在签名库中无类型声明行**，只出现在参数/返回值位置
- ⇒ 它来自外部依赖包（`com.seeyon.boot.starter.autocode.template`），**不在本次签名扫描范围内**
- ⇒ 因此**不能断言它的方法签名**，只能说「存在这个类型的拦截点，且有 3 个客户实现类」

**3 个实现类的可见方法（仅 4 个 getter，无 intercept 方法）：**
```
getAppId(): Long
getNewAppName(): String
getNewBasePackage(): String
getTablePrefix(): String
```
⇒ 这说明它们的作用是**重写应用名/包名/表前缀**，即「同一份设计在不同客户下生成不同命名」。
但**具体的改写方法不在签名库内**（可能来自接口默认方法或父类）。

**⇒ 关键推论（降级表述）：模板产出不是「一个模板一个产物」的静态关系。**
存在拦截点，可在渲染前改写；但**改写逻辑本身未验证**。

**证据等级：** `STATIC_RULE`（存在性 + 接入点）→ **不是** `VERIFIED_STATIC_BYTECODE`
**待证：** 拦截器接口定义、改写逻辑（需 jar）

### 4.5 部署/更新机制（★ v4 完全遗漏的机制）

```java
com.seeyon.udc.common.autocode.transport.TransportHandler    ← 接口
  # out(CodeContext): List<SchemaInfo>              ← 输出 schema
  # compare(SchemaComparisonSourcePool)             ← 对比
  # buildDmlFileDto(List<? extends BaseEntity>, ...)← 生成 DML
  # isFormDeploy(CodeContext): boolean
  # group(): String

com.seeyon.udc.common.autocode.transport.TransportHandlerAdapter
com.seeyon.udc.common.autocode.transport.DownloadTransportHandlerAdapter
```

**已枚举 30+ 个 TransportHandler 实现（按对象分）：**

```
元数据类：EntityTransportHandler / DtoTransportHandler / AttributeSetTransportHandler
          AttributeGroupTransportHandler / EntityGroupTransportHandler
          BasicDataTransportHandler / ExtendAttributeTransportHandler
          ScalabilityTransportHandler / UdcEnumTransportHandler
          CtpEnumTransportHandler / CtpParameterTransportHandler / CtpJobTransportHandler
          ReferConfigTransportHandler / FilterPlanTransportHandler
          FilterPlanFormalTransportHandler
页面类：  PageTransportHandler / PageLayoutTransportHandler / PageTemplateTransportHandler
流程类：  MicroFlowTransportHandler / MicroFlowGroupTransportHandler
          AppCollaborationTransportHandler
其他：    EventTransportHandler / BaseInfoTransportHandler
          DependentApplicationTransportHandler / FormAppLastVersionTransportHandler
          SerialNumberTransportHandler / GanttChartTransportHandler
          FormConvertTransportHandler / CtpQrCodeRuleTransportHandler
          CtpExcelExportTemplateTransportHandler
升级类：  DeployRecordUpgradeTransportHandler / ServiceMetadataUpgradeTransportHandler
```

**⇒ 结论：**
1. **「生成文件」≠「部署到平台」**，是两套机制
2. `TransportHandler` 负责把生成的 schema 部署进平台
3. `CodeParam#isDeploy()` / `getDeployId()` 控制是否走部署
4. `AutoCodeManager#downloadAndZipLocal(ApplicationDto): File` 是下载路径（不走部署）

**⇒ 这解释了为什么 v4 的三层证据（清单 + 签名 + 产物）不够：**
**产物只是文件，部署才是「代码真正生效」的环节。**

### 4.6 重复生成策略（部分可证）

| 线索 | 值 | 含义 |
|---|---|---|
| `generator.properties` → `gg_isOverride` | `true` | 静态代码生成文件是否覆盖 |
| `AutoCodeProperties#getNeedInterceptTemplate()` | Boolean | 是否启用模板拦截 |
| `AutoCodeProperties#getCopyExtendCode()` | Boolean | 是否复制扩展代码 |
| `AutoCodeProperties#getTransportExtendCode()` | Boolean | 是否传输扩展代码 |
| `CodeParam#getComparedSchemaIdSet()` | Set<String> | 增量对比范围 |
| `AutoCodeExecutor#compareToLast(...)` | void | 与上次对比 |

**⇒ 有「覆盖」和「增量对比」两套机制并存，但具体策略（覆盖哪些、保留哪些）需反编译。**

**⚠️ `gg_isOverride = true` 只说明「默认覆盖」，不能推断「会覆盖用户手写代码」。**
用户手写代码通常在 `custom` 包（不受模板管），但**这一点未经证实，不得作为结论。**

### 4.7 模板渲染失败处理（未查到）

**状态：`BLOCKED`**
- 未找到明确的异常处理类/方法
- `AutoCodeProperties#getOutputTimeOut()` 存在，说明有超时控制，但失败后行为未知

### 4.8 表达式模板的使用环节（待证）

```
2.7/entityrule/  10 条模板
  AssignValueActivity.ftl / AttributeRequiredActivity.ftl
  AttributeUniqueActivity.ftl / DefaultValueActivity.ftl / ShowMessageActivity.ftl
  common/EntityRuleTemplateUtil.ftl / common/SetValueUtil.ftl
  entityValueForRoot.ftl / ruleservice.java.ftl

2.7/common/  12 条
  macro-formula-entity.ftl      ← ★ 表达式 × 实体
  formula-param-map.ftl         ← 参数映射
  macro-entity-update.ftl       ← ★ 更新逻辑
  macro-entity-check.ftl
  macro-entity-attribute-check-not-null.ftl
  macro-entity-trim.ftl
  macro-appservice-approval.ftl ← ★ 单据审批
  macro-dto-entity.ftl
  macro.ftl / utils.ftl / orgUtils.ftl / constants.ftl
```

**⇒ `macro-formula-entity.ftl` 在 `common/` 下，说明它是被其他模板 include 的宏，不是独立生成的产物。**
**待证：** 被哪些模板 include（需 .ftl 内容，当前 BLOCKED）。

---

## 5. 现有资产与缺失证据地图

### 5.1 可用资产（已核实）

| 资产 | 规模 | 路径 | 等级 |
|---|---|---|---|
| 类/方法签名 | 245709 行 / 21389 类 / 224320 方法 | `docs/audit/signatures.txt.gz` | VERIFIED_STATIC_BYTECODE |
| 表面索引 | 100+ 文件 | `docs/audit/reference/surface-index.tar.gz` | STATIC_RULE |
| 平台资源包 | 404 条目 | `docs/audit/reference/udc-platform-5.3.517.tar.gz` | STATIC_RULE |
| 模板清单 | 464 条 / 41 组 / 4 版本 | 包内 `_codegen_templates.json` | STATIC_RULE |
| AppService 清单 | 830 接口 / 9343 方法 | `docs/audit/reference/svc-app-service.txt.gz` | STATIC_RULE |
| 反编译源码 | 212 .java | `docs/audit/modules/decompiled/` | VERIFIED_STATIC_BYTECODE |
| 现有 facts | 228 md + 107 json | `core/facts/` | 混合 |
| 类索引 | 2669 类 / 26235 方法 | `components/construction/platform_class_index.py` | 已建成 |
| **统计脚本** | 可复现 | `scripts/research/stats_registry.py` | **本轮新建** |

### 5.2 缺失证据

| 缺失项 | 影响 | 当前可做 | 补足方式 |
|---|---|---|---|
| 平台 jar 本体 | 无法反编译方法体 | 签名级 | 需你提供路径 |
| .ftl 模板内容 | 无法看模板语法与 include 关系 | 清单级 | 需 jar |
| CFR 反编译工具 | 同上 | 签名级 | 可安装（需批准） |
| Template 方法体 | 无法证 `getTemplateOutMap()` 返回值 | 签名级 | 需 jar |
| CodeTask `code()` 方法体 | 无法证 Task→Template 调用 | 候选映射 | 需 jar |
| `TemplateInterceptor` 实现 | 无法证模板改写 | 存在性 | 需 jar |
| `TransportHandler#out` 实现 | 无法证部署细节 | 存在性 | 需 jar |
| 生成产物样本 | 无法确认包名/命名 | OutPath 签名 | 需生成（审批 B） |
| 运行时持久化行为 | 无法确认主键/外键/顺序 | 静态部分 | 需实测（审批 E） |

### 5.3 资产缺口对阶段 2 的影响

| 阶段 2 任务 | 能否完成 | 前提 |
|---|---|---|
| CodeTask 完整清单与包分布 | ✅ 已完成 | — |
| Template 完整清单 | ✅ 已完成 | — |
| Task→Template 调用关系 | ❌ | 需 jar 反编译 |
| `getTemplateOutMap()` 返回值语义 | ❌ | 需 jar 或实测产物 |
| 版本选择完整规则 | ⚠️ 部分 | 需反编译 `getCodeVersion` 来源 |
| 模板加载路径拼接规则 | ❌ | 需反编译 |
| 拦截器改写逻辑 | ❌ | 需 jar |
| 部署机制细节 | ⚠️ 部分 | 需反编译 `TransportHandler#out` |
| 生成物结构与命名 | ✅ 可做 | 需实测产物（审批 B） |
| 重复生成策略 | ⚠️ 部分 | 需实测（审批 B） |

**⇒ 阶段 2 的结论会分成三层（按你的要求）：**

```
① 生成器执行链已验证      入口/任务分发/模板调用关系
                          → 目前只有签名级，Task→Template 待证
② 生成物结构已验证        文件/包名/类名/方法
                          → 需实测产物（审批 B）
③ 模板内部规则未完全还原   .ftl 内容、拦截器逻辑、渲染细节
                          → 明确标注缺失
```

---

## 6. 阶段 1 自评：哪些是真结论，哪些还需验证

### 6.1 可直接使用的结论（有硬证据）

| # | 结论 | 证据 |
|---|---|---|
| 1 | CodeTask 接口是 `code(CodeContext): String` | 签名库 |
| 2 | 52 个实现类 + 1 个接口自身 | 脚本统计 |
| 3 | v27 版本化任务 14 个存在 | 脚本统计 |
| 4 | CodeTask 由 `PluginDefinition#getCodeTasks()` 注册 | 签名库 |
| 5 | 任务列表可由 `CodeParam#addTask()` 动态追加 | 签名库 |
| 6 | 版本由 `CodeParam#getCodeVersion()` 传入 | 签名库 |
| 7 | 支持版本列表在 `AutoCodeProperties#getCodeVersions()` | 签名库 |
| 8 | 模板目录在 `AutoCodeProperties#getTemplateDir()` | 签名库 |
| 9 | 模板可被 `TemplateInterceptor` 改写 | 签名库（接入点）+ 3 个客户实现类（仅 getter 可见） |
| 10 | 部署由 `TransportHandler#out()` 承担，30+ 实现 | 签名库 |
| 11 | `EntityTask#deployEntity(EntityFileTemplate, EntityDto)` 直接证实 EntityTask 用 EntityFileTemplate | 签名库；**v27 的 `EntityTaskV27#deployEntity` 同签名，证实 v27 也用同一个 `EntityFileTemplate`（非 v27 版本）** |
| 12 | 6 种 stereotype 的必要特性 | stereotype-authoritative.json |
| 13 | 模板清单 464 条 / 41 组 / 4 版本 | 脚本解析 |
| 14 | AppService 830 个全为接口，零实现类 | 脚本统计 |
| 15 | DAO 接口 41 方法（36 唯一 + 5 重载） | 脚本统计 |

### 6.2 需降级表述的结论

| # | 原表述 | 修正表述 | 原因 |
|---|---|---|---|
| 1 | 「CodeTask 与 Template 一一对应」 | 「仅 `EntityTask→EntityFileTemplate` 有直接证据；其余为命名候选」 | 无调用关系证据 |
| 2 | 「24 个 Template」 | 「36 个声明 `getTemplateOutMap()`；实际参与生成的数目是动态的」 | 口径不同 |
| 3 | 「`copyNeedResetNull` 是覆盖坑根因」 | 「该方法零调用者，根因待验证」 | 无调用证据 |
| 4 | 「模板清单 = 生成规则」 | 「模板清单 = 资产记录；选择机制见 §4.2」 | 证据等级不同 |
| 5 | 「生成 → 产物」 | 「生成 → 产物 → 部署（两阶段）」 | 遗漏 TransportHandler |

### 6.3 阶段 1 未能解决的问题（交给阶段 2）

| # | 问题 | 阻塞原因 |
|---|---|---|
| 1 | Task → Template 实际调用关系 | 需反编译 `code()` |
| 2 | `getTemplateOutMap()` 返回值语义 | 需反编译或实测 |
| 3 | 模板加载的路径拼接规则 | 需反编译 |
| 4 | 拦截器改写逻辑 | 需反编译 |
| 5 | 重复生成策略 | 需反编译 + 实测 |
| 6 | 渲染失败处理 | 未找到相关类 |
| 7 | `getCodeVersion()` 取值来源 | 需反编译 |
| 8 | `dependencyGraph.json` 内容 | 未解析 |
| 9 | 26 个 feature 的语义 | 未解析 |

---

## 7. 交付清单与审计请求

### 7.1 本轮产出

| # | 文件 | 说明 |
|---|---|---|
| 1 | `scripts/research/stats_registry.py` | 可复现统计脚本（只读） |
| 2 | `.hermes/plans/2026-11-17_stage1-research-report.md` | 本文件 |

**未产出（按你的要求）：**
- ❌ 未写入 `core/facts/platform-dev-system/`（等审计）
- ❌ 未修改任何现有 facts
- ❌ 未操作 test2

### 7.2 需要你审计的 6 点

**A. 统计口径登记表（§1）**：8 个统计项的口径、数据源、规则、局限是否够？还需要补什么字段？

**B. CodeTask 口径修正**：53 → 区分「52 实现 + 1 接口自身 + 14 个 v27 版本化 + 3 个扩展包」，
并查明 v3 的「32」是包内类数。这个修正方式认可吗？

**C. Template 口径修正**：24 → 「36 个声明 `getTemplateOutMap()`」+ 明确「实际参与生成的数目是动态的」+ 4 个抽象基类单列。认可吗？

**D. Task↔Template 映射（§3.2）**：只有 1 个有签名级证据，其余为命名候选，约 16 个任务无对应 Template。
这个「不宣称一一对应」的处理方式，是否满足你的要求？

**E. 新发现的三个机制**（v4 完全遗漏）：
- `PluginDefinition#getCodeTasks()` — Task 由插件注册，非硬编码
- `TemplateInterceptor` — 模板可被改写，同一模板可产出不同代码
- `TransportHandler`（30+）— 生成与部署是两个阶段

这三个发现是否应该成为阶段 2 的重点？

**F. 阶段 1 结论分级（§6）**：15 条可直接用、5 条需降级、9 条未解决。
这个分级方式是否便于你审计？

### 7.3 审计通过后，阶段 2 的计划

```
阶段 2 前置（需要你决策）：
  ① 是否提供平台 jar（决定能否反编译）
  ② 是否安装 CFR
  ③ 是否批准「生成代码」审批项 B

阶段 2 内容：
  ① 反编译 code() 方法体 → 建立真实 Task→Template 映射
  ② 反编译 EntityFileTemplate → OutPath 拼接规则
  ③ 反编译 TemplateInterceptor 实现 → 改写逻辑
  ④ 反编译 TransportHandler#out → 部署机制
  ⑤ 解析 dependencyGraph.json → 元数据依赖
  ⑥ 解析 26 个 feature config → 特性语义
  ⑦ 实测生成产物（若批准）→ 验证包名/命名
```

---

## 8. 最后：关于「最终目标」的对齐

你最后强调的判断，我完全认同，并且这一轮的工作方式已经按这个目标调整：

```
不是解释 53 个任务、36 个模板、830 个 AppService
而是让 Agent 能回答：
  我要开发什么业务？
  平台有哪些现成能力？
  应该生成什么？
  应该调用什么？
  数据应该怎么写？
  哪些操作有风险？
  如何验证开发结果？
```

**阶段 1 的统计与映射，是这条路的「地基」而不是「目的」。**
地基的价值在于：**当 Agent 说「该调 `createDtoWithAttrsAndRefDtos`」时，这句话背后有可复现的口径、可追溯的证据、明确的适用范围。**

这也是我这一轮主动推翻 v3 数字、撤销 `copyNeedResetNull` 根因判断的原因——
**宁可少一个结论，不要多一个错误结论。**
