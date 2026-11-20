# Seeyon 平台开发体系研究计划与证据地图（v2 修正版）

> 状态：**仅研究与规划，未实施**。待审计确认后开工。
> 修正依据：用户 6 条要求（顺序调整 / 继续追生成器 / 双线验证 / 表达式扩围 / 盲测 4 场景 / 专题八要素）
> 生成日期：2026-11-17
> 仓库：`C:/Users/白明涛/xiaozhua-agent`

---

## 零、本次修正的核心变化

| # | 用户要求 | v1 的做法 | v2 的修正 |
|---|---|---|---|
| 1 | 顺序调整 | 3-B→4→1 | **1 主子表 → 2 生成器 → 3 单据 → 4 表达式 → 5 接口 → 6 组件 → 7 关联** |
| 2 | 继续追生成器 | 「模板源码无 → 降级 BLOCKED」 | **已追出完整链路**：CodeTask(32 实现) → CodeContext → AutoCodeExecutor → Template(24 类) → OutPath(8 个) |
| 3 | 双线验证 | 只静态 | 静态 + test2 实测，**但实测需先出隔离方案**（见 §七） |
| 4 | 表达式扩围 | 只研究工具类 | 加 `macro-formula-entity.ftl` / `EntityRuleTask` / 注册机制 / runtime 入口 |
| 5 | 盲测 4 场景 | 3 个 | **4 个**：普通实体 CRUD / 主子表 CRUD / 单据保存提交流转 / 第三方接口集成 |
| 6 | 专题八要素 | 无 | 每专题固定 8 项：已有资产 / 文件与源码入口 / 待追类与方法 / 待验问题 / 预期产物 / 当前证据等级 / 资产缺口 / 是否需动态环境 |

---

## 一、资产盘点（已完成，全部逐项核实）

### 1.1 可用资产（已核实存在）

| 资产 | 规模 | 路径 | 本次用途 |
|---|---|---|---|
| 类/方法签名 | 21389 类 / 224320 方法 | `docs/audit/signatures.txt.gz` | 一切签名权威源 |
| 表面索引 | 8 MB / 100+ 文件 | `docs/audit/reference/surface-index.tar.gz` | domains 11 / action-index 682 / dto-meta 1305 / impl-map 269 / consumers 183 |
| 平台资源包 | 404 条目 | `docs/audit/reference/udc-platform-5.3.517.tar.gz` | **255 javap + 87 json + 模板清单** |
| AppService→jar | 10176 行 | `docs/audit/reference/svc-app-service.txt.gz` | 接口归属判定 |
| 反编译源码 | 212 .java | `docs/audit/modules/decompiled/` | 真实调用示例 |
| 现有 facts | 228 md + 107 json | `core/facts/` | 已有结论，只增不删 |
| 类索引 | 2669 类 / 26235 方法 | `components/construction/platform_class_index.py` | 中文检索 |

### 1.2 ★ 新追出的关键资产（v1 未发现）

#### ① `_codegen_templates.json` 完整结构：41 组 / 464 条

```
2.7/beanname 1   2.7/common 12   2.7/dto 1    2.7/entity 19   2.7/entityrule 10
2.7/enums 1      2.7/event 7     2.7/feature 12  2.7/filterplan 1  2.7/microflow 55
2.7/project 20   2.7/refer 2     2.7/referconfig 2
2.8/* 同上（entity 25 / microflow 59）
2.9/* 同上（entity 24 / microflow 65）
3.0/entity 2
```

**版本维度（2.7 / 2.8 / 2.9 / 3.0）本身就是「模板选择机制」的证据**：
模板按平台版本分目录，`3.0/entity` 只剩 2 条（说明 3.0 架构变了）。

#### ② 生成器主链（签名库逐字，非推断）

```
com.seeyon.udc.autocode.AutoCodeExecutor
  # execute(ApplicationDto, CodeParam)                        ← 对外入口
  # executeSegment(ApplicationDto, CodeParam)
  # runTask(CodeContext, List<CodeTask>): void                ← 任务调度
  # resolveSchema(CodeContext, AutoCodeResult): void          ← Schema 解析
  # outputPresetSchema(CodeContext, PersistResult): void
  # compareToLast(CodeContext, PersistResult, ...)            ← 增量对比

com.seeyon.udc.autocode.AutoCodeManager
  # execute(ApplicationDto, Map<String,Object>, ...)          ← 另一入口
  # initAppTemplate(): String
  # downloadAndZipLocal(ApplicationDto): File                 ← ★ 产出 zip
  # getAppCopySchemaInfo(long, ContextTypeEnum): List<SchemaInfo>
```

#### ③ 32 个 CodeTask 实现（枚举完成）

```
AbstractMicroFlowCodeTask      AppBeanNameModifyerTask    AppBuildInfoTask
AppDependenciesTask            AppInitFileTask            AttachmentTemplateTask
CodeConfigTask                 CtpEnumIdsMetadataTask     CtpJobTask
DtoTask                        DynamicSearchTask          EntityRuleTask
EntityTask                     EnumTask                   EventTask
FilterPlanTask                 HostAppMicroFlowCodeTask   MgnInitFileTask
MicroFlowCodeTask              MicroFlowScheduleJobTask   OssMetadataTask
OutAppAppServiceProxyTask      PageControllerTask         PageEntityControllerTask
PageInfoTask                   ReferConfigTask            ReferControllerTask
ReferenceMetaDataTask          SerialConfigTask           StaticExtFileTask
StaticFileTask                 TestDeployStaticFileTask
```

**与本任务直接相关的 6 个：**
`EntityTask` / `EntityRuleTask` / `DtoTask` / `CodeConfigTask` / `PageControllerTask` / `SerialConfigTask`

#### ④ 24 个 Template 类（模板载体，非硬编码）

```
EntityFileTemplate          ★ 实体全套生成（含 8 个 OutPath）
EntityRuleTemplate          ★ 实体规则（含 BaseServiceOutPath）
EntityRuleAggregateTemplate ★ 主子表聚合（含 LayerMap / CapRootEntityName）
DtoCodeTemplate             DtoTask 用
PageEntityControllerTemplate / PageControllerTemplate
MicroFlowTemplate / MicroFlowWebTemplate / MicroFlowWebControllerTemplate
MicroFlowTriggerTemplate / MicroFlowScheduleTemplate / HostAppMicroFlowTemplate
CustomMicroFlowControllerTemplate / CustomRestApiMicroFlowControllerTemplate
ReferTemplate / EntityReferTemplate / EntityReferTemplate2
DynamicSearchTemplate / FilterPlanTemplate / StaticFileTemplate
OutAppAppServiceProxyTemplate / PageCustomControllerDtoTemplate
ConnectorBusinessEventTemplate / CustomMicroFlowTemplateSupport
```

#### ⑤ ★★ 决定性证据：`EntityFileTemplate` 的 8 个输出路径方法

这是任务二「三层生成物包路径和命名规范」的**直接答案源**：

```java
public class com.seeyon.udc.autocode.template.EntityFileTemplate {
    // —— 8 个输出路径（三层 + 配套）——
    public String getEntityOutPath();          // 实体
    public String getDtoOutPath();             // DTO
    public String getAppServiceOutPath();      // ★ AppService 接口
    public String getAppServiceImplOutPath();  // ★ AppService 实现
    public String getControllerOutPath();      // Controller
    public String getBaseServiceOutPath();     // ★ Service（BaseService）
    public String getMybatisXmlOutPath();      // ★ Mapper XML
    public String getDaoOutPath();             // ★ DAO

    // —— 包路径 ——
    public String getAppPacketName();
    public String getEntityPackage();
    public String getDtoPackage();
    public String getEnumPackage();

    // —— 表与字段映射 ——
    public Map<String,Object> getTableInfo(EntityDto);
    public Map<String,Object> getTableInfoMap();
    public DatabaseType getDatabaseType();                    // 方言
    public String getJavaType(AttributeDto);                  // 字段→Java 类型
    public String getDataType(AttributeDto);
    public String getDataTypeName(String);

    // —— 特性解析（决定生成内容）——
    public void resolveBpmProcess(Map, EntityDto);    // ★ 单据：BPM 流程
    public void resolveSerial(Map, EntityDto);        // ★ 流水号
    public void resolveIndex(Map, EntityDto);         // 索引
    public void resolveFullText(Map, EntityDto);      // 全文检索
    public void resolveOpenApiData(Map, EntityDto);   // 开放接口
    public void resolveDefaultValue(Map, AttributeDto, ...);  // ★ 默认值表达式
    public void resolveAttachment(Map, AttributeDto, ...);    // ★ 附件
    public void resolveEntity(Map, AttributeDto);             // ★ 关联实体
    public void resolveUdcEnum / resolveCtpEnum(...);         // 枚举

    // —— 主子表 ——
    public List<EntityReferAgg4CodeDto> getEntityReferAgg4CodeDto(EntityDto);  // ★ 聚合
    public void agg2Map(EntityDto, Map<String,EntityDto>);                     // ★ 聚合→Map
    public EntityDto getRootEntityDto(EntityDto);                              // ★ 找根实体

    // —— 关键：null 重置策略 ——
    public boolean copyNeedResetNull(AttributeDto);   // ★ 与 requireNull 坑直接相关
}
```

**`copyNeedResetNull` 是唯一持有该方法的类** —— 这正是用户踩过的「表达式无条件覆盖传入值」的生成侧根因。

#### ⑥ 主子表机制入口

```java
// EntityRuleTask
private void generateAggregateRootEntityRule(
    CodeContext, Map<String,Entity4CodeDto>, Set<String>);   // ★ 聚合根规则生成
private LinkedHashMap<Long,List<EntityDto>> getEntityRule(Long, Map<Long,EntityDto>, Predicate<EntityDto>);
private void resolveEntityRule(List<EntityDto>, LinkedHashMap<...>, Map<Long,EntityDto>, Predicate);

// EntityRuleAggregateTemplate
public Map<String,List<String>> getLayerMap();        // ★ 层级（主/子分层）
public String getCapRootEntityName();                 // ★ 根实体名
public String getTargetGroupType();                   // ★ 分组类型
public Map<String,Entity4CodeDto> getEntity4CodeDtoMap();

// 关系枚举
com.seeyon.boot.starter.extmetadata.enums.EntityRelationMultiplicityEnum
    # selectByRelationType(String)
    # selectRelationTypeByEntityRelation(...)
    # code(): int
    # getRelationType(): String
```

#### ⑦ 表达式相关资源

```
udc-biz-5.3.517/resources/formula-functions.xml        ★ 表达式函数注册（XML）
udc-biz-5.3.517/resources/microflow/macro/presetMacro.json  ★ 预置宏
udc-biz-5.3.517/resources/entityrule/*.ftl 对应 5 个 Activity:
    AssignValueActivity / AttributeRequiredActivity / AttributeUniqueActivity
    DefaultValueActivity / ShowMessageActivity
```

#### ⑧ 实体特性配置（26 个 feature config.json）

```
feature/{approve,archive_basic,archive_tiled,basic,bill_basic,disable,
         form_basic,fulltext_search,nullify,organization,secret_level,
         send_down,suspend,termination,tree_entity,validity_period,
         attribute_scalability,attribute_scalability_global}/config.json
stereotype/{archive,archive_tree,basic_data,bill,form,standard}/config.json
```

**`stereotype/bill/config.json` 是任务三「单据与普通实体的区别」的直接证据源。**

#### ⑨ 微流程白名单/黑名单（决定 AppService 能否被微流程调用）

```
microflow/appServiceMethodBlackList.json              ★ 哪些方法禁止
microflow/bootStarterServiceWhiteList.json
microflow/bootStarterWhiteList.json
microflow/entityEventWhiteList.json
microflow/otherEntityAppServiceMethodNameList.json
microflow/systemPackageWhiteList.json
```

**这批文件是任务一「接口三分类（公开/内部/扩展）」的判定依据。**

### 1.3 明确不存在的资产

```
❌ 平台 jar 本体（0 个 .jar）
❌ .ftl 模板内容（0 个文件；只有清单）
❌ 模板源码（Template 类只有签名，无方法体）
❌ CFR 反编译工具（本机无）
❌ 完整生成产物样本（无 *AppServiceImpl.java / *BaseService.java / *Dao.java）
❌ autocode Java 源码（只有 EntityRuleTask/EntityService/MicroflowNodeParserFactory 3 个 javap）
```

### 1.4 资产缺口对结论等级的影响（不推断，直接标 BLOCKED）

| 想要的结论 | 需要什么 | 现状 | 等级 |
|---|---|---|---|
| 模板文件内容长什么样 | .ftl 源文件 | 无 | **BLOCKED** |
| 生成方法体内具体逻辑 | Template 类方法体 | 无 | **BLOCKED** |
| 生成产物真实代码 | 历史生成项目 | 无 | **BLOCKED** |
| 模板名→任务的映射 | 模板清单 + Task 类名 | ✅ 有 | STATIC_RULE |
| 输出路径与包名 | OutPath 方法签名 + 实测 | 部分 | STATIC_RULE → 可升 LIVE |
| 主子表生成机制 | Template 的 LayerMap/RootEntity | ✅ 签名有 | STATIC_RULE |

**⇒ 生成机制研究可以从「模板源码级」降到「契约级 + 实测产物级」：**
不读 .ftl 内容，但通过
① 模板清单（464 条）
② Template 类的 OutPath / ArgumentMap 签名
③ 在 test2 生成一次，拿到真实产物
三者交叉，足以还原「什么条件生成什么文件、输出到哪、包名是什么」。

**这是本次修正最重要的判断：生成机制研究不做 BLOCKED，改走「实测产物反推」。**

---

## 二、七个专题的详细研究地图

每个专题固定 8 要素。

---

## 专题 1：主子表与实体持久化 ★最高优先级

### 1.1 已有资产
```
core/facts/standard-product/dao-and-mybatis.md          205 行  AllInOneBaseDao 41 方法 + 22 Mapper + 10 方言
core/facts/udc/microflow/node-insert-entity.md          106 行  preCreateBatch + G34/G35 闸门
core/facts/udc/microflow/write-node-runtime-gap.md      282 行  executeExpression 覆盖坑
core/facts/udc/entity/attribute-create.md                         relationEntity / multiSelect 字段
signatures.txt.gz                                        AllInOneBaseDao 41 方法可逐字核
```

### 1.2 具体文件与源码入口
```
入口 A（静态）：
  com.seeyon.udc.autocode.template.EntityFileTemplate
    # getEntityReferAgg4CodeDto(EntityDto): List<EntityReferAgg4CodeDto>   ← 聚合定义
    # agg2Map(EntityDto, Map<String,EntityDto>): void                      ← 聚合转 Map
    # getRootEntityDto(EntityDto): EntityDto                               ← 找根
  com.seeyon.udc.autocode.template.EntityRuleAggregateTemplate
    # getLayerMap(): Map<String,List<String>>       ← 主/子分层
    # getCapRootEntityName(): String
    # getTargetGroupType(): String
  com.seeyon.udc.autocode.task.EntityRuleTask
    # generateAggregateRootEntityRule(...)          ← 聚合根规则
  com.seeyon.boot.starter.extmetadata.enums.EntityRelationMultiplicityEnum
    # selectByRelationType / code() / getRelationType()

入口 B（数据层）：
  AllInOneBaseDao<T> 41 方法（已在 dao-and-mybatis.md）
  BaseMybatisDao<T> = 22 个 Mapper 组合

入口 C（实测）：
  test2 建「主表 + 子表」实体 → 生成代码 → 调 create → 查 DB
```

### 1.3 需要追踪的类和方法
| # | 类 | 方法 | 要回答什么 |
|---|---|---|---|
| 1 | `EntityFileTemplate` | `getEntityReferAgg4CodeDto` | 聚合关系怎么描述 |
| 2 | `EntityFileTemplate` | `agg2Map` | 聚合怎么转成模板参数 |
| 3 | `EntityRuleAggregateTemplate` | `getLayerMap` | 主子分层依据 |
| 4 | `EntityRuleTask` | `generateAggregateRootEntityRule` | 聚合根规则生成 |
| 5 | `AllInOneBaseDao` | `create` / `createBatch` | 单条 vs 批量 |
| 6 | 待查 | 主键生成器 | **主表 ID 谁生成、何时生成** |
| 7 | 待查 | 子表外键回填 | **哪个方法回填、在哪一步** |
| 8 | 待查 | 事务边界 | `@Transactional` 在哪层 |

### 1.4 需要验证的问题（静态 + 动态双线）
| # | 问题 | 静态能否回答 | 必须动态 |
|---|---|---|---|
| Q1 | 主表 ID 生成时机（insert 前/后） | 部分 | ✅ |
| Q2 | 子表外键由谁回填 | ❌ | ✅ |
| Q3 | 主子表保存顺序 | ❌ | ✅ |
| Q4 | 更新策略（全量替换 vs 增量 diff） | ❌ | ✅ |
| Q5 | 删除策略（级联 vs 手动） | 部分 | ✅ |
| Q6 | 事务边界（一次 create 是否单事务） | 部分 | ✅ |
| Q7 | 批量 create 是否分批 | 部分 | ✅ |
| Q8 | `copyNeedResetNull` 对子表字段的影响 | ✅ 签名 | 需实测验证 |

### 1.5 预期产物
```
core/facts/standard-product/entity-master-detail-persistence.md
  §1 结论速查表（场景→方法→顺序→注意事项）
  §2 机制（ID 生成 → 主表 insert → 外键回填 → 子表 insert → 事务提交）
  §3 真实代码示例（可直接复制）
  §4 陷阱（子表字段被 null 覆盖、批量未分批、事务跨层）
  §5 证据（签名行 + 实测响应体 + DB 截图）
  §6 未解决
```

### 1.6 当前证据等级
`STATIC_RULE`（签名 + 模板参数名）→ 目标升 `LIVE_RULE`

### 1.7 资产缺口
- ❌ 无 `AllInOneBaseDao` 方法体 → 看不到 ID 生成逻辑
- ❌ 无 `EntityFileTemplate` 方法体 → 看不到聚合处理细节
- ❌ 无主子表生成产物样本
- ⚠️ 需 test2 实测补足

### 1.8 是否需要动态环境
**需要。** 主子表的外键回填、保存顺序、事务行为，纯静态无法确定。需先出隔离方案（§七）。

---

## 专题 2：实体生成器与三层生成机制

### 2.1 已有资产
```
udc-biz-5.3.517/_codegen_templates.json     464 条模板 / 41 组
udc-biz-5.3.517/EntityRuleTask.javap.txt    生成器入口 javap
udc-biz-5.3.517/resources/generator.properties  gg_isOverride = true（★ 覆盖策略）
core/facts/standard-product/autocode-project-templates.md  194 行
signatures.txt.gz                            5275 行 autocode
```

### 2.2 具体文件与源码入口
```
主链（签名库逐字）：
  AutoCodeExecutor#execute(ApplicationDto, CodeParam)
    → AutoCodeExecutor#runTask(CodeContext, List<CodeTask>)
      → CodeTask#code(CodeContext): String
        → <Xxx>Template#getTemplateOutMap(): Map<String,String>
        → <Xxx>Template#getArgumentMap(): Map<String,Object>

32 个 CodeTask 实现（已枚举）
24 个 Template 类（已枚举）
8 个 EntityFileTemplate OutPath 方法（已定位）
41 组 / 464 条模板清单（已解析）

资源：
  resources/generator.properties
  resources/_index.json
  resources/microflow/*WhiteList.json
```

### 2.3 需要追踪的类和方法
| # | 目标 | 状态 |
|---|---|---|
| 1 | `CodeTask` 接口定义 | 已定位 `code(CodeContext)` |
| 2 | `CodeContext` 结构（含哪些元数据） | 待查字段 |
| 3 | `AutoCodeExecutor#execute` 完整流程 | 签名有，方法体无 |
| 4 | 32 个 Task 的 `matches()` 条件 | 待查（决定谁被选中） |
| 5 | `getTemplateOutMap()` 的键值含义 | 待查（模板名→输出路径） |
| 6 | 版本选择（2.7/2.8/2.9/3.0） | 待查 |
| 7 | `generator.properties` 的 `gg_isOverride` 影响 | 已知 true，含义待验 |
| 8 | 三层职责（AppService / Service / DAO） | 部分（签名） |

### 2.4 需要验证的问题
| # | 问题 | 方法 | 等级 |
|---|---|---|---|
| Q1 | 一个实体生成哪些文件 | 模板清单 + 实测产物 | STATIC → LIVE |
| Q2 | 每个文件输出路径 | `get*OutPath()` + 实测 | STATIC → LIVE |
| Q3 | 包名规则 | `getAppPacketName/getEntityPackage/...` + 实测 | STATIC → LIVE |
| Q4 | 命名规范（`XxxAppService` / `XxxBaseService` / `XxxDao`） | 实测产物 | LIVE |
| Q5 | 生成代码与手写代码边界 | 实测 + `gg_isOverride` | LIVE |
| Q6 | 32 个 Task 谁先谁后 | 待查调度顺序 | 可能 BLOCKED |
| Q7 | 模板选择机制（版本/特性） | 清单结构 + 实测 | STATIC |
| Q8 | `EntityFileTemplate` 的 8 个 OutPath 实际值 | **实测一次生成** | LIVE |

### 2.5 预期产物
```
core/facts/standard-product/entity-codegen-mechanism.md
  §1 生成主链（CodeTask → CodeContext → Template → OutPath）
  §2 32 个 CodeTask 职责表
  §3 24 个 Template 职责表
  §4 三层生成物：文件名 / 包名 / 输出路径 / 模板
  §5 464 条模板清单（按 41 组分类）
  §6 版本差异（2.7 / 2.8 / 2.9 / 3.0）
  §7 生成代码 vs 手写代码边界（gg_isOverride）
  §8 实测产物样本（真实生成的 8 个文件路径）
```

### 2.6 当前证据等级
`STATIC_RULE`（清单 + 签名）→ 目标 `VERIFIED_RULE`（实测产物）

### 2.7 资产缺口
- ❌ .ftl 内容（**不阻塞**：改走实测产物反推）
- ❌ Template 方法体
- ❌ 历史生成项目样本
- ✅ 模板清单完整
- ✅ OutPath 方法签名完整

### 2.8 是否需要动态环境
**需要一次生成操作**（在 test2 建一个最小实体 → 触发代码生成 → 下载产物）。
这是**读操作 + 生成**，不写业务数据，风险低于专题 1。

---

## 专题 3：单据数据保存与业务流转

### 3.1 已有资产
```
udc-biz-5.3.517/resources/stereotype/bill/config.json          ★ 单据特性定义
udc-biz-5.3.517/resources/feature/{approve,bill_basic,organization,
    termination,suspend,nullify}/config.json                    ★ 7 个单据特性
core/facts/udc/entity/evidence/entity-write-2026-10-23/stereotype-authoritative.json
core/facts/bpm/*.md                                             BPM 域已有研究
signatures.txt.gz                                               BpmAppService 22 方法
```

### 3.2 具体文件与源码入口
```
静态：
  resources/stereotype/bill/config.json
    → necessaryFeatures: [basic, approve, organization, billBasic,
                          termination, suspend, nullify]
  resources/feature/approve/config.json
  resources/feature/bill_basic/config.json
  resources/feature/{termination,suspend,nullify}/config.json

  com.seeyon.udc.autocode.template.EntityFileTemplate
    # resolveBpmProcess(Map, EntityDto): void        ← ★ 单据 BPM 解析
    # getApprovalSet(): Set<String>                  ← 审批相关字段

  com.seeyon.udc.autocode.common/*.ftl 中的
    macro-appservice-approval.ftl                   ← ★ 单据 AppService 生成规则

  BpmAppService（22 方法，待逐字提取）

动态：
  test2 建 bill 实体 → 保存 → 提交 → 查状态流转
```

### 3.3 需要追踪的类和方法
| # | 类/资源 | 要回答什么 |
|---|---|---|
| 1 | `stereotype/bill/config.json` | 单据 vs 普通实体的特性差异 |
| 2 | `feature/approve/config.json` | 审批特性带来哪些生成物 |
| 3 | `EntityFileTemplate#resolveBpmProcess` | 单据实体生成时怎么处理流程 |
| 4 | `EntityFileTemplate#getApprovalSet` | 哪些字段参与审批 |
| 5 | `macro-appservice-approval.ftl`（清单） | 单据 AppService 特有方法 |
| 6 | `BpmAppService` 22 方法 | 提交/流转的正式入口 |
| 7 | 待查 | 单据能否直接用 `Dao.create` 绕过流程 |
| 8 | 待查 | 提交后状态字段谁维护 |

### 3.4 需要验证的问题
| # | 问题 | 静态 | 动态 |
|---|---|---|---|
| Q1 | 单据与普通实体本质区别 | ✅ 特性定义 | — |
| Q2 | 单据主表与明细数据关系 | 部分 | ✅ |
| Q3 | 单据保存机制（是否特殊） | ❌ | ✅ |
| Q4 | 提交与状态流转由谁驱动 | 部分（BpmAppService） | ✅ |
| Q5 | 是否必须调平台专用服务 | ❌ | ✅ |
| Q6 | **哪些操作不能直接用 DAO** | ❌ | ✅ 关键 |

### 3.5 预期产物
```
core/facts/standard-product/bill-entity-persistence.md
  §1 单据 vs 普通实体：7 个特性差异表
  §2 保存路径（草稿 → 提交 → 流转）
  §3 BpmAppService 入口方法
  §4 禁止直接 DAO 的操作清单
  §5 代码示例
  §6 证据与未解决
```

### 3.6 当前证据等级
`STATIC_RULE`（特性定义）→ 目标 `LIVE_RULE`

### 3.7 资产缺口
- ❌ `BpmAppService` 方法体
- ❌ `macro-appservice-approval.ftl` 内容
- ❌ 单据实际状态流转样本

### 3.8 是否需要动态环境
**需要。** 单据保存/提交/流转必须实测，否则 Q3-Q6 全是猜。

---

## 专题 4：表达式定义、注册与运行时执行

### 4.1 已有资产
```
core/facts/udc/expression/engine.md              421 行  design-time 编译
core/facts/udc/expression/functions.md           800 行  88 函数
core/facts/udc/expression/README.md              481 行
core/facts/udc/expression/system-variables.md    189 行  131 变量
core/facts/udc/microflow/write-node-runtime-gap.md:215-245  ★ runtime 执行
udc-biz-5.3.517/resources/formula-functions.xml  ★ 函数注册（XML）
udc-biz-5.3.517/resources/microflow/macro/presetMacro.json  ★ 预置宏
```

### 4.2 具体文件与源码入口
```
注册：
  resources/formula-functions.xml                 ← ★ 函数注册表
  resources/microflow/macro/presetMacro.json      ← ★ 预置宏

生成侧：
  udc-biz-5.3.517/resources/entityrule/
    DefaultValueActivity.ftl          ← 默认值表达式
    AssignValueActivity.ftl           ← 赋值表达式
    AttributeRequiredActivity.ftl
    AttributeUniqueActivity.ftl
    ShowMessageActivity.ftl
  common/macro-formula-entity.ftl     ← ★ 表达式与实体结合（清单已确认存在）
  common/formula-param-map.ftl        ← 参数映射

  代码：
  EntityFileTemplate#resolveDefaultValue(Map, AttributeDto, ...)
  EntityFileTemplate#getDefaultValue4JavaEnum(...)

  EntityRuleTask（整个类就是表达式规则生成）
    # generateAggregateRootEntityRule
    # buildConditionMethodName(ConditionNode): String
    # negateCondition(List<String>): List<String>
    # addNotPrefix(String): String
    # putElement2ParamMap(ConditionNode, Map<String,Boolean>): void

运行侧：
  executeExpression<实体名>(list, requireNull, getter, expFn, setter, null)
  ★ requireNull=false → 无条件覆盖（实测坑）
```

### 4.3 需要追踪的类和方法
| # | 目标 | 状态 |
|---|---|---|
| 1 | 表达式注册表（`formula-functions.xml`） | 待解析 |
| 2 | 88 个函数签名 | 已有 facts |
| 3 | design-time 编译链 | 已有 facts |
| 4 | **runtime 主动执行入口** | ❌ **核心缺口** |
| 5 | 参数上下文构建 | 部分 |
| 6 | 实体字段访问（反射 getter/setter） | 部分 |
| 7 | `copyNeedResetNull` 与 requireNull 关系 | 签名有 |
| 8 | 自定义表达式扩展点 | ❌ 待查 |

### 4.4 需要验证的问题
| # | 问题 | 方法 |
|---|---|---|
| Q1 | 表达式怎么注册 | 解析 `formula-functions.xml` |
| Q2 | 表达式怎么解析 | `engine.md` 已有 |
| Q3 | **业务代码怎么主动执行表达式** | ★ 查 `boot-starter-formula` / `boot-formula-engine` 包 |
| Q4 | 平台自动执行（preCreateBatch）机制 | 已有 facts |
| Q5 | 主动执行 vs 自动执行的区别 | 对比两者上下文 |
| Q6 | 参数传递与上下文 | 追 `expressionMap` |
| Q7 | 异常处理 | 待查 |
| Q8 | 自定义表达式扩展 | 待查 SPI/扩展点 |

### 4.5 预期产物
```
core/facts/standard-product/expression-runtime-execution.md
  §1 表达式生命周期：注册 → 解析 → 编译 → 执行
  §2 design-time 路径（/check → /transform → executableExpr）
  §3 runtime 路径 A：平台自动（preCreateBatch）
  §4 runtime 路径 B：业务主动执行 ★
  §5 两条路径的上下文差异
  §6 函数注册表（88 函数）
  §7 自定义扩展
  §8 代码示例（主动执行一个表达式）
```

### 4.6 当前证据等级
`STATIC_RULE` + 部分 `VERIFIED_RULE`（preCreateBatch 已实测）

### 4.7 资产缺口
- ❌ 函数注册表内容（有 XML 文件，待解析）
- ❌ runtime 主动执行入口（**核心缺口**）
- ❌ 自定义扩展点

### 4.8 是否需要动态环境
**部分需要。** 主动执行入口可以先纯静态找（查 formula 相关包），
找到后再实测验证。

---

## 专题 5：Dubbo、@Autowired、泛化调用

### 5.1 已有资产
```
core/facts/standard-product/dubbo-cross-service.md    166 行  DubboFactory 5 重载 + AppServiceProxy 3 形态
docs/audit/reference/svc-app-service.txt.gz           10176 行 AppService→jar
surface-index.tar.gz: impl-map.json                   269 接口→实现
surface-index.tar.gz: consumers.json                  183 接口→调用者
udc-biz-5.3.517/resources/microflow/*WhiteList.json   ★ 黑白名单
```

### 5.2 具体文件与源码入口
```
注入/获取：
  com.seeyon.boot.dubbo.DubboFactory
    # getProxy(Class)
    # getProxy(Class, String group)
    # getProxy(Class, String group, String version)
    # getProxy(Class, String group, String version, int timeout)

泛化：
  AppServiceProxy#invokeAppService / invokeAppServiceForList
                #invokeAppServiceForPage / reliableInvokeAppService
  AppServiceInvokeDto（18 字段）
  GenericInvocationAuthService#invokeAppService(String, String, ...)

分类依据：
  resources/microflow/appServiceMethodBlackList.json    ← 黑名单
  resources/microflow/bootStarterServiceWhiteList.json  ← 白名单
  resources/microflow/systemPackageWhiteList.json
  resources/microflow/entityEventWhiteList.json
```

### 5.3 需要追踪的类和方法
| # | 目标 | 状态 |
|---|---|---|
| 1 | 1000 个 AppService 完整清单（按域） | 数据有，待整理 |
| 2 | 公开 / 内部 / 扩展 三分类 | 黑白名单可判定 |
| 3 | `@Autowired` 能注什么 vs 必须 `DubboFactory` | ❌ 待查 |
| 4 | 泛化调用完整链路 | 签名有，链路待串 |
| 5 | `AppServiceInvokeDto` 18 字段含义 | 待查 |
| 6 | 权限机制 | 待查 |
| 7 | 异常机制 | 待查 |
| 8 | 事务机制 | 待查 |

### 5.4 需要验证的问题
| # | 问题 |
|---|---|
| Q1 | 什么时候直接 `@Autowired`，什么时候必须 `DubboFactory.getProxy` |
| Q2 | 泛化调用和直接调用在权限上有什么区别 |
| Q3 | 哪些接口禁止微流程调用（黑名单） |
| Q4 | 跨应用调用的租户/权限上下文怎么传 |

### 5.5 预期产物
```
core/facts/standard-product/standard-api-catalog.md
  §1 1000 个 AppService 按域分类清单
  §2 三分类判定规则（公开/内部/扩展）
  §3 注入方式决策树（@Autowired vs DubboFactory vs 泛化）
  §4 泛化调用完整链路（含代码）
  §5 黑白名单（禁止调用的方法）
  §6 权限/异常/事务
```

### 5.6 当前证据等级
`VERIFIED_STATIC_BYTECODE`

### 5.7 资产缺口
- ❌ 方法体（看不到权限校验实现）
- ✅ 签名 + 黑白名单 + impl-map 足够做分类

### 5.8 是否需要动态环境
**不需要。** 纯静态可完成。

---

## 专题 6：基础组件使用知识

### 6.1 已有资产
```
core/facts/standard-product/boot-core-utils-and-annotations.md  176 行
components/construction/platform_class_index.py                 2669 类 / 26235 方法
signatures.txt.gz                                               821 个工具类
```

### 6.2 具体文件与源码入口
```
已有索引（中文可查）：
  日期   DateUtils(61) / DateTransformUtil(19)
  JSON   JsonNodeUtil(56) / JsonUtils(28) / JsonUtil(20)
  缓存   UserCacheUtils(125) / OrgCacheUtils(47)
  文件   FileUtils(72) / ExcelTemplateUtil(70)
  HTTP   HttpClientUtil(93)
  组织   OrgCommonAppService(40)
  流程   BpmAppService(22)
  存储   StorageService（三桶 public/private/temp）
```

### 6.3 需要追踪的类和方法
不是补签名，而是补**使用边界**：

| # | 类 | 要回答 |
|---|---|---|
| 1 | `JsonUtils` | `toMap` vs `toMapThrowError` 差异；与 `license.JsonUtils` 同名坑 |
| 2 | `DateUtils` | 与表达式 `dateToString` 的选用边界 |
| 3 | `StorageService` | 附件关联到业务实体的正确姿势 |
| 4 | `OrgCommonAppService` | 查人的推荐路径 vs 备选 |
| 5 | `BpmAppService` | send vs submit vs start 边界 |
| 6 | `ExcelTemplateUtil` | 与平台导入导出模板的关系 |
| 7 | `HttpClientUtil` | 平台有 HTTP 工具，但微流程无 HTTP 节点 |
| 8 | 锁 | 分布式锁类与用法 |

### 6.4 需要验证的问题
每个类回答三问：
- 什么情况该用这个类？
- 什么情况不该用（该用什么替代）？
- 有什么坑？

### 6.5 预期产物
```
core/facts/standard-product/base-component-usage.md
  §1 组件分类总览
  §2 每类：用途 / 推荐方法 / 不该用的场景 / 替代方案 / 代码示例 / 坑
```

### 6.6 当前证据等级
`VERIFIED_STATIC_BYTECODE`

### 6.7 资产缺口
- ❌ 方法体（看不到内部行为）
- ✅ 签名足够判断用途，边界需靠已有实测经验

### 6.8 是否需要动态环境
**不需要。**

---

## 专题 7：业务能力关联与实战验证

### 7.1 已有资产
```
components/construction/business_code_bridge.py   业务意图 → 域 → 动作 → 方法 → DTO → 实现 → 调用者
components/construction/platform_class_index.py   2669 类中文检索
components/construction/business_action_index.py  业务词 → 标品能力
surface-index.tar.gz: action-index.md             682 条业务动作
```

### 7.2 需要构建的关联链
```
业务需求
  → 开发方案（选哪个专题）
  → 平台能力（哪个接口/类）
  → 类与方法（全限定名）
  → DTO / 实体（字段）
  → 调用链（顺序）
  → 验证方式（怎么确认成功）
```

### 7.3 四个盲测场景（按用户要求）

| # | 场景 | 依赖专题 | 验收标准 |
|---|---|---|---|
| 1 | **普通实体 CRUD** | 专题 1、2 | 从「建一个供应商档案，支持增删改查」出发，Agent 自己找到实体类型、生成物、DAO 方法、调用顺序 |
| 2 | **主子表 CRUD** | 专题 1 | 从「订单 + 订单明细」出发，Agent 自己找到聚合关系、ID 回填、保存顺序 |
| 3 | **单据保存、提交和流转** | 专题 3 | 从「建一个采购申请单，能提交审批」出发，Agent 自己找到单据特性、BpmAppService、状态流转 |
| 4 | **第三方接口集成** | 专题 4、5、6 | 从「调外部 ERP 接口，把数据落到本平台实体」出发，Agent 自己找到 HttpClientUtil、表达式、实体写入 |

**盲测规则（严格）：**
- 只给业务需求，**不给类名、方法名、接口名**
- Agent 必须自己通过检索找到能力
- 每个方案必须带源码/签名证据
- 找不到就标 `BLOCKED`，不许编

### 7.4 预期产物
```
core/facts/standard-product/business-dev-playbook.md
  §1 业务需求 → 能力映射总表
  §2 四个场景的完整方案（含代码）
  §3 盲测报告（Agent 独立完成的过程与结果）
  §4 未解决问题
```

### 7.5 当前证据等级
`UNVERIFIED`（待前 6 个专题完成后才有素材）

### 7.6 资产缺口
依赖专题 1-6 的产出

### 7.7 是否需要动态环境
盲测 2/3 需要（验证方案是否真能跑）

---

## 三、实施顺序与依赖

```
专题 1  主子表与实体持久化        ← 起点，最高优先
   ↓（产出：持久化机制 + 实测产物）
专题 2  实体生成器与三层机制       ← 与专题 1 共享实测产物
   ↓
专题 3  单据保存与流转
   ↓
专题 4  表达式定义/注册/执行
   ↓
专题 5  Dubbo/@Autowired/泛化      ← 可与专题 4 并行（纯静态）
   ↓
专题 6  基础组件使用知识           ← 可与专题 5 并行（纯静态）
   ↓
专题 7  业务关联与四场景盲测       ← 收口
```

**并行建议：** 专题 5、6 纯静态无依赖，可在专题 1 进行时并行推进。

---

## 四、动态环境使用方案（必须先批准）

### 4.1 环境隔离
```
环境：test2（configtest2 kubeconfig）
⚠️ 不碰 uat，不碰生产
⚠️ 必须在独立测试应用下操作，不复用现有业务应用
```

### 4.2 数据隔离与备份
```
① 测试前：记录目标应用 appId 与现有实体清单
② 只用新建的测试应用（如「ZZ研究验证-勿用」）
③ 不修改任何现有实体/页面/微流程
④ 测试数据打统一前缀（如 ZZRESEARCH_），便于清理
⑤ 测试前导出：目标库表结构与现有数据行数快照
```

### 4.3 测试范围（严格限定）
| 专题 | 允许的操作 | 禁止 |
|---|---|---|
| 1 主子表 | 建主表+子表实体、调 create、查 DB | 不改现有实体、不删数据 |
| 2 生成器 | 触发代码生成、下载产物 | 不改平台配置 |
| 3 单据 | 建 bill 实体、保存、提交、查状态 | 不提交到真实审批人 |
| 4 表达式 | 建带默认值表达式的字段 | 不改平台函数注册表 |

### 4.4 清理方案
```
① 删除测试应用（含所有实体、页面、微流程）
② 清理测试数据表（ZZRESEARCH_ 前缀）
③ 核对：实体数 / 表数 / 行数回到测试前快照
④ 输出清理确认报告
```

### 4.5 需用户明确批准的事项
- [ ] 允许在 test2 新建测试应用
- [ ] 允许触发代码生成
- [ ] 允许建 bill 实体并提交（不指定真实审批人）
- [ ] 允许查询 DB 验证
- [ ] 清理方案是否满足要求

**未经批准，不执行任何写操作。**

---

## 五、证据等级规范

| 等级 | 含义 | 判定标准 |
|---|---|---|
| `STATIC_RULE` | 源码/模板/配置静态确认 | 能在 tar 包/仓库文件里逐字找到 |
| `VERIFIED_RULE` | 调用链/测试/字节码验证 | 签名库命中 + 调用关系闭合 |
| `LIVE_RULE` | 实际运行验证 | 有真实响应体/DB 结果/生成产物 |
| `UNVERIFIED` | 尚无充分证据 | 只有推测 |
| `BLOCKED` | 缺资产无法推进 | 明确缺什么 |

**硬规则：**
- 不把类索引当使用知识
- 不把方法签名当调用规范
- 不把模板清单当生成规则
- 每条结论必须能追到：文件路径 + 行号 / 签名库逐字行 / 实测响应体

---

## 六、交付物清单

| # | 交付物 | 对应专题 | 可达 |
|---|---|---|---|
| 1 | 平台开发体系总览 | 全部 | ✅ |
| 2 | 标品接口知识库 | 5 | ✅ |
| 3 | 实体类型与生成机制知识库 | 2 | ✅（实测产物反推） |
| 4 | AppService/Service/DAO 生成规范 | 2 | ✅ |
| 5 | DAO 持久化专题 | 1、3 | ✅（需实测） |
| 6 | 表达式机制专题 | 4 | ✅（主动执行入口待查） |
| 7 | 基础组件使用知识库 | 6 | ✅ |
| 8 | 业务开发场景知识库 | 7 | ✅ |
| 9 | 类/方法/DTO/实体/业务关联索引 | 7 | ✅ |
| 10 | 证据与未解决问题清单 | 全部 | ✅ |
| 11 | Agent 检索与使用规范 | 全部 | ✅ |
| 12 | 实战验证报告（4 场景盲测） | 7 | ✅ |

---

## 七、需要你审计确认的事项

**A. 研究顺序**：1 主子表 → 2 生成器 → 3 单据 → 4 表达式 → 5 接口 → 6 组件 → 7 关联，是否符合？

**B. 生成器研究路线**：改走「模板清单 + OutPath 签名 + 实测产物反推」，
不因 .ftl 缺失而 BLOCKED。是否认可？

**C. 动态环境**：§四 的隔离/备份/范围/清理方案是否满足要求？
需要你逐项勾选批准（4.5 节 5 项）。

**D. 盲测四场景**：普通实体 CRUD / 主子表 CRUD / 单据保存提交流转 / 第三方接口集成，是否就是这四个？

**E. 专题 5、6 并行**：这两个纯静态无依赖，是否允许在专题 1 进行时并行？

**F. 产物落点**：新 facts 建议放在 `core/facts/standard-product/` 下，
新建文件不覆盖现有；是否需要单独目录（如 `core/facts/platform-dev-system/`）？

---

## 八、本阶段不做的事

- ❌ 不写新业务功能
- ❌ 不重复整理已有 228 个 facts
- ❌ 不把签名索引当使用文档
- ❌ 不把 `*Impl` 当可用接口
- ❌ 不以 Controller 为主要方向
- ❌ 不改现有 Agent 架构/工具注册
- ❌ 不覆盖现有研究
- ❌ **未经批准不执行任何 test2 写操作**
- ❌ 不因资产缺失就推断补全
