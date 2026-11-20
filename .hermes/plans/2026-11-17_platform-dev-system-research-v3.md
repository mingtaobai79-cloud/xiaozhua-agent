# Seeyon 平台开发体系研究计划与证据地图（v3 · 按体系分层）

> 状态：**仅研究与规划，未实施**。待审计确认后开工。
> v3 修正：不再按「用户踩坑深浅」排优先级，改为按**平台自身分层结构**组织研究。
> 主子表、单据、大数据量降为「持久化体系」下的子节，不单独成专题。
> 生成日期：2026-11-17
> 仓库：`C:/Users/白明涛/xiaozhua-agent`

---

## 零、为什么改：v1/v2 的结构性错误

v2 把「主子表」排成专题 1，理由是「用户最痛 + 完全空白」。**这是按痛点排序，不是按体系排序。**

错误在于：主子表本身不是平台的一层，它只是持久化体系里的一种**关联写入形态**。
把它单拎出来，会导致：

- 看不到它和普通实体 CRUD 共享同一套 DAO 能力
- 看不到它和单据写入共享同一套事务机制
- 研究完主子表，仍然不知道「平台持久化的全貌是什么」

**正确做法：以平台的分层为纲，场景为目。**
主子表、单据、大数据量都是「持久化体系」章节下的子节，共享同一套底层能力。

---

## 一、平台开发体系的分层（研究的顶层框架）

这是本次研究的组织依据，不是推测，来自已核实的生成器链路与元数据：

```
L0  业务应用 Application
      └─ 应用是生成的边界（AutoCodeExecutor#execute(ApplicationDto, CodeParam)）

L1  元数据 Metadata
      ├─ 实体 Entity（6 种 stereotype：standard/form/basicData/bill/archive/archiveTree）
      ├─ 字段 Attribute（含 relationEntity / multiSelect / 默认值表达式）
      ├─ 关联 EntityRelation（EntityRelationMultiplicityEnum）
      ├─ 页面 Page / 微流程 MicroFlow / 枚举 Enum / 流水号 Serial
      └─ 特性 Feature（26 个 config.json：approve / bill_basic / tree_entity / serial ...）

L2  代码生成 Codegen
      ├─ CodeTask（32 个实现，每个负责一类产物）
      ├─ CodeContext（承载 ApplicationDto + 全部元数据）
      ├─ Template（24 个类，getTemplateOutMap + getArgumentMap）
      └─ 产物：entity / dto / appservice / appserviceImpl / baseservice
                / controller / dao / mybatis.xml / enums / event / entityrule

L3  运行时 Runtime
      ├─ 持久化（AllInOneBaseDao 41 方法 + 22 Mapper + 10 方言）
      ├─ 表达式（注册 → 解析 → 编译 → 执行）
      ├─ 事件（entityEventWhiteList）
      └─ 微流程（29 个 Activity 模板）

L4  对外契约 Contract
      ├─ AppService 接口（1000 个，Dubbo 暴露 / @Autowired 注入 / 泛化调用）
      ├─ 微流程节点可调用的服务（黑白名单约束）
      └─ 页面 Controller（客开自己写，不进标品索引）
```

**研究的七个专题，就是这五层的横向切分 + 纵向收口：**

```
专题 1  实体与元数据体系          ← L1
专题 2  代码生成体系              ← L2
专题 3  持久化体系                ← L3 的持久化（★ 含主子表/单据/大数据 子节）
专题 4  表达式体系                ← L3 的表达式
专题 5  接口调用体系              ← L4
专题 6  基础组件体系              ← L3 横切
专题 7  业务能力关联与验证        ← 全部收口
```

---

## 二、七个体系专题

每个专题固定 8 要素。**场景（主子表/单据/大数据）作为专题内的子节出现，不再独立成专题。**

---

## 专题 1：实体与元数据体系（L1）

### 1.1 已有资产
```
core/facts/udc/entity/*.md                                    10 个实体 facts
core/facts/udc/entity/evidence/entity-write-2026-10-23/stereotype-authoritative.json
udc-biz-5.3.517/resources/stereotype/{standard,form,basic_data,bill,archive,archive_tree}/config.json
udc-biz-5.3.517/resources/feature/*/config.json               26 个特性
udc-biz-5.3.517/resources/presetData/attribute.json
udc-biz-5.3.517/resources/openApi/entityOpenApi.json
surface-index.tar.gz: dto-meta.json                           1305 个 DTO
```

### 1.2 具体文件与源码入口
```
实体类型：resources/stereotype/*/config.json         6 个
特性：    resources/feature/*/config.json            26 个
字段：    resources/presetData/attribute.json + presetAttributeCapacity.json
关联：    EntityRelationMultiplicityEnum（枚举 + selectByRelationType）
聚合：    com.seeyon.udc.dto.AggregationDto（getRelation/setRelation）
实体域服务：udc-biz-5.3.517/EntityService.javap.txt
```

### 1.3 需要追踪的类和方法
| # | 目标 | 要回答 |
|---|---|---|
| 1 | `stereotype/*/config.json` 六份 | 六种实体类型的必要特性与差异 |
| 2 | `feature/*/config.json` 26 份 | 每个特性带来什么生成物/运行时行为 |
| 3 | `EntityRelationMultiplicityEnum` | 关联重数（一对一/一对多/多对多）如何影响生成 |
| 4 | `AggregationDto` | 聚合（主子表）在元数据层怎么表达 |
| 5 | `EntityService` | 实体元数据的领域服务（增删改查元数据） |
| 6 | `entityOpenApi.json` | 哪些实体开放为 OpenAPI |

### 1.4 需要验证的问题
| # | 问题 |
|---|---|
| Q1 | 六种实体类型的本质区别是什么（不只是特性列表） |
| Q2 | 特性如何组合出实体能力（basic + approve + billBasic = 单据） |
| Q3 | 字段类型 → Java 类型 → DB 类型的三级映射规则 |
| Q4 | 关联字段（relationEntity）在元数据里怎么描述 |
| Q5 | 聚合关系（主子表）与普通关联的区别 |
| Q6 | 元数据存在哪（MySQL udc_entity/udc_attribute → Redis → OSS） |

### 1.5 预期产物
```
core/facts/platform-dev-system/01-entity-metadata-system.md
  §1 六种实体类型对照（特性 + 生成物 + 运行时行为）
  §2 26 个特性逐个说明（带来什么）
  §3 字段三级映射（UdcType → Java → DB）
  §4 关联与聚合的元数据表达
  §5 元数据存储与生命周期
```

### 1.6 当前证据等级
`VERIFIED_STATIC_BYTECODE`（6 份 stereotype config 已逐字核实）

### 1.7 资产缺口
- ❌ 特性 config.json 的完整内容（有文件，需逐个解析）
- ✅ 实体类型定义完整

### 1.8 是否需要动态环境
**不需要。** 纯静态解析。

---

## 专题 2：代码生成体系（L2）

### 2.1 已有资产
```
udc-biz-5.3.517/_codegen_templates.json           41 组 / 464 条模板
udc-biz-5.3.517/EntityRuleTask.javap.txt          生成器入口
udc-biz-5.3.517/resources/generator.properties    gg_isOverride = true
core/facts/standard-product/autocode-project-templates.md   194 行
signatures.txt.gz                                 5275 行 autocode
```

### 2.2 具体文件与源码入口（已全部打通，非推断）
```
主链：
  AutoCodeExecutor#execute(ApplicationDto, CodeParam)
    → AutoCodeExecutor#runTask(CodeContext, List<CodeTask>)
      → CodeTask#code(CodeContext): String
        → <Xxx>Template#getTemplateOutMap(): Map<String,String>
        → <Xxx>Template#getArgumentMap(): Map<String,Object>

32 个 CodeTask 实现（已枚举）
24 个 Template 类（已枚举）

★ EntityFileTemplate 的 8 个输出路径（三层生成物的直接答案）：
  getEntityOutPath()  getDtoOutPath()
  getAppServiceOutPath()      getAppServiceImplOutPath()
  getBaseServiceOutPath()     getDaoOutPath()
  getMybatisXmlOutPath()      getControllerOutPath()

包路径：
  getAppPacketName()  getEntityPackage()  getDtoPackage()  getEnumPackage()

类型映射：
  getJavaType(AttributeDto)  getDataType(AttributeDto)  getDatabaseType()
```

### 2.3 需要追踪的类和方法
| # | 目标 | 状态 |
|---|---|---|
| 1 | `CodeContext` 字段结构 | 待查 |
| 2 | 32 个 Task 的 `matches()` 条件 | 待查（决定谁被选中） |
| 3 | `getTemplateOutMap()` 键值含义 | 待查（模板名→输出路径） |
| 4 | 版本选择 2.7/2.8/2.9/3.0 | 待查 |
| 5 | `gg_isOverride` 对生成 vs 手写的影响 | 待验 |
| 6 | 三层职责（AppService/Service/DAO） | 部分（签名） |
| 7 | `EntityRuleTemplate#getDubboServiceMap()` | 待查（Dubbo 暴露怎么生成） |

### 2.4 需要验证的问题
| # | 问题 | 方法 |
|---|---|---|
| Q1 | 一个实体生成哪些文件 | 模板清单 + 实测 |
| Q2 | 每个文件输出路径与包名 | OutPath 签名 + 实测 |
| Q3 | 命名规范 | 实测产物 |
| Q4 | 三层职责边界（谁调谁） | 签名 + 实测 |
| Q5 | 生成代码 vs 手写代码边界 | `gg_isOverride` + 实测 |
| Q6 | 重新生成会不会覆盖手写代码 | ★ 实测 |
| Q7 | 版本升级（2.7→2.9）生成物差异 | 模板清单对比 |

### 2.5 预期产物
```
core/facts/platform-dev-system/02-codegen-system.md
  §1 生成主链（CodeTask → CodeContext → Template → OutPath）
  §2 32 个 CodeTask 职责表
  §3 24 个 Template 职责表
  §4 三层生成物：文件名 / 包名 / 输出路径 / 对应模板
  §5 464 条模板清单（按 41 组分类）
  §6 版本差异（2.7/2.8/2.9/3.0）
  §7 生成 vs 手写边界（gg_isOverride）
  §8 实测产物样本（真实生成的 8 个文件）
```

### 2.6 当前证据等级
`STATIC_RULE`（清单 + 签名）→ 目标 `VERIFIED_RULE`（实测产物）

### 2.7 资产缺口
- ❌ .ftl 内容（**不阻塞**：走实测产物反推）
- ❌ Template 方法体
- ✅ 模板清单 + OutPath 签名完整

### 2.8 是否需要动态环境
**需要一次生成操作**（建最小实体 → 触发生成 → 下载产物）。
只读 + 生成，不写业务数据。

---

## 专题 3：持久化体系（L3 · 本次核心）

**这是「大方向」的正确落点：持久化是一个完整体系，主子表只是其中一种写入形态。**

### 3.1 已有资产
```
core/facts/standard-product/dao-and-mybatis.md     205 行  AllInOneBaseDao 41 方法 + 22 Mapper + 10 方言
core/facts/udc/microflow/node-insert-entity.md     106 行  preCreateBatch + G34/G35
core/facts/udc/microflow/write-node-runtime-gap.md 282 行  executeExpression 覆盖坑
signatures.txt.gz                                  AllInOneBaseDao 41 方法可逐字核
udc-biz-5.3.517/resources/stereotype/bill/config.json
udc-biz-5.3.517/resources/feature/{approve,bill_basic,termination,suspend,nullify}/config.json
```

### 3.2 体系结构（专题内的六个子节）

```
3.1  通用 DAO 能力层
       AllInOneBaseDao<T> 41 方法 / BaseMybatisDao 22 Mapper / 10 方言
       ↓ 所有写入都建立在这一层上
3.2  单实体写入与主键生成
       create / createBatch / update / updateColumns / delete*
       主键：谁生成、何时生成、什么策略
       ↓
3.3  关联写入（含主子表）★
       聚合关系 / 主表 ID → 子表外键回填 / 保存顺序 / 更新删除策略
       ↓
3.4  单据写入与业务流转
       bill 七特性 / 保存 vs 提交 / BpmAppService / 状态流转
       ↓
3.5  批量与大数据量写入
       分页阈值 / 幂等 / 异步 / 锁 / 租户上下文
       ↓
3.6  查询与分页
       Mapper XML 生成 / 动态 SQL / 分页 / 关联查询 / 结果映射
```

### 3.3 具体文件与源码入口

```
子节 3.1 通用 DAO
  AllInOneBaseDao<T>（41 方法，dao-and-mybatis.md 已记录）
  BaseMybatisDao<T>（22 Mapper）
  条件三档：ByCondition(s) → ByComplexConditions(LinkedHashMap) → ByDynamicConditions(SeeyonCondition)
  ★ 返回 PageData<T>，不是 transport 的 PageResponse

子节 3.2 主键
  待查：IdentifierGenerator / @TableId 策略 / 雪花 ID
  线索：executeExpression 的 exp<雪花ID> 命名

子节 3.3 关联写入 ★
  EntityFileTemplate#getEntityReferAgg4CodeDto(EntityDto)   聚合定义
  EntityFileTemplate#agg2Map(EntityDto, Map)                聚合转 Map
  EntityFileTemplate#getRootEntityDto(EntityDto)            找根实体
  EntityRuleAggregateTemplate#getLayerMap()                 主/子分层
                              #getCapRootEntityName()       根实体名
                              #getTargetGroupType()         分组类型
  EntityRuleTask#generateAggregateRootEntityRule(...)       聚合根规则
  EntityRelationMultiplicityEnum                            关联重数
  ★ EntityFileTemplate#copyNeedResetNull(AttributeDto)      唯一持有者，与覆盖坑直接相关

子节 3.4 单据
  resources/stereotype/bill/config.json
    necessaryFeatures: [basic, approve, organization, billBasic,
                        termination, suspend, nullify]
  EntityFileTemplate#resolveBpmProcess(Map, EntityDto)      单据 BPM 解析
  EntityFileTemplate#getApprovalSet()                       审批字段
  macro-appservice-approval.ftl（清单确认存在）
  BpmAppService 22 方法（待逐字提取）

子节 3.5 批量大数据
  用户复盘文档（实测数据）：
    pageSize 默认 2000 不是 100
    ListRequest.from() 空参拉全表 → 重复 5 万行
    604 次全量 COUNT
    锁续约 40s/120s
  待查：平台是否有批量上限、事务分批

子节 3.6 查询
  mybatis.xml.ftl（清单确认存在）
  待查：动态 SQL 生成规则、分页实现、关联查询映射
```

### 3.4 需要追踪的类和方法
| # | 子节 | 目标 | 状态 |
|---|---|---|---|
| 1 | 3.1 | `AllInOneBaseDao` 41 方法逐个用途 | ✅ 已有 facts |
| 2 | 3.2 | 主键生成器 | ❌ 待查 |
| 3 | 3.2 | `create` vs `createBatch` 差异 | 部分 |
| 4 | 3.3 | `getEntityReferAgg4CodeDto` 返回结构 | 待查 |
| 5 | 3.3 | `getLayerMap` 分层依据 | 待查 |
| 6 | 3.3 | 子表外键回填时机 | ❌ 必须实测 |
| 7 | 3.4 | `resolveBpmProcess` 做了什么 | 待查 |
| 8 | 3.4 | 单据能否绕过 BPM 直接 DAO | ❌ 必须实测 |
| 9 | 3.5 | 批量上限与分批 | ❌ 待查/实测 |
| 10 | 3.6 | `mybatis.xml` 生成规则 | ❌ 需实测产物 |

### 3.5 需要验证的问题（按子节）
| 子节 | 问题 | 静态 | 动态 |
|---|---|---|---|
| 3.1 | 41 方法各自适用场景 | ✅ | — |
| 3.2 | 主键生成时机与策略 | 部分 | ✅ |
| 3.3 | 主表 ID 生成 → 子表外键回填 → 保存顺序 | ❌ | ✅ |
| 3.3 | 更新策略（全量替换 vs 增量 diff） | ❌ | ✅ |
| 3.3 | 删除策略（级联 vs 手动） | 部分 | ✅ |
| 3.4 | 单据保存与普通实体保存的区别 | ❌ | ✅ |
| 3.4 | 哪些操作不能直接用 DAO | ❌ | ✅ |
| 3.4 | 提交后状态谁维护 | 部分 | ✅ |
| 3.5 | 批量阈值与分批策略 | 部分 | ✅ |
| 3.5 | 事务边界（一次批量是否单事务） | ❌ | ✅ |
| 3.6 | XML 生成规则与动态 SQL | ❌ | ✅ 看产物 |

### 3.6 预期产物
```
core/facts/platform-dev-system/03-persistence-system.md
  §1 体系总览（六个子节的关系）
  §2 通用 DAO 能力（41 方法场景表）
  §3 单实体写入与主键
  §4 关联写入：主子表完整链路（ID → 外键 → 顺序 → 事务）
  §5 单据写入与流转（含禁止直接 DAO 清单）
  §6 批量与大数据量（阈值/幂等/异步/锁）
  §7 查询与分页（含 XML 生成规则）
  §8 陷阱汇总
```

### 3.7 当前证据等级
`STATIC_RULE`（3.1）+ `UNVERIFIED`（3.2-3.6）→ 目标 `LIVE_RULE`

### 3.8 资产缺口
- ❌ `AllInOneBaseDao` 方法体
- ❌ 主键生成器实现
- ❌ 聚合处理方法体
- ❌ 生成产物样本（需专题 2 实测产出）
- ⚠️ 3.2-3.6 全部依赖 test2 实测

### 3.9 是否需要动态环境
**必须。** 这是本次最依赖实测的专题。
建议先做专题 2 的实测（拿生成产物），再做专题 3（在产物上验证持久化）。

---

## 专题 4：表达式体系（L3）

### 4.1 已有资产
```
core/facts/udc/expression/engine.md              421 行
core/facts/udc/expression/functions.md           800 行（88 函数）
core/facts/udc/expression/README.md              481 行
core/facts/udc/expression/system-variables.md    189 行（131 变量）
core/facts/udc/microflow/write-node-runtime-gap.md:215-245
udc-biz-5.3.517/resources/formula-functions.xml
udc-biz-5.3.517/resources/microflow/macro/presetMacro.json
```

### 4.2 具体文件与源码入口
```
注册：  resources/formula-functions.xml              ★ 函数注册表
        resources/microflow/macro/presetMacro.json   预置宏
生成侧：resources/entityrule/{DefaultValue,AssignValue,AttributeRequired,
                              AttributeUnique,ShowMessage}Activity.ftl
        common/macro-formula-entity.ftl              ★ 表达式×实体
        common/formula-param-map.ftl
        EntityFileTemplate#resolveDefaultValue(...)
        EntityRuleTask#buildConditionMethodName(ConditionNode)
                     #negateCondition / #addNotPrefix / #putElement2ParamMap
运行侧：executeExpression<实体名>(list, requireNull, getter, expFn, setter, null)
```

### 4.3 需要追踪的类和方法
| # | 目标 | 状态 |
|---|---|---|
| 1 | `formula-functions.xml` 注册表 | 待解析 |
| 2 | design-time 编译链 | ✅ 已有 facts |
| 3 | **runtime 主动执行入口** | ❌ **核心缺口** |
| 4 | 平台自动执行（preCreateBatch） | ✅ 已实测 |
| 5 | 参数上下文构建 | 部分 |
| 6 | `copyNeedResetNull` 与 requireNull | 签名有 |
| 7 | 自定义扩展点 | ❌ 待查 |

### 4.4 需要验证的问题
| # | 问题 |
|---|---|
| Q1 | 表达式怎么注册（XML 结构） |
| Q2 | 编译产物 `executableExpr` 怎么被调用 |
| Q3 | **业务代码怎么主动执行表达式** ★ |
| Q4 | 主动执行 vs 平台自动执行的上下文差异 |
| Q5 | 实体字段访问机制（反射） |
| Q6 | 异常处理 |
| Q7 | 自定义扩展 |

### 4.5 预期产物
```
core/facts/platform-dev-system/04-expression-system.md
  §1 生命周期：注册 → 解析 → 编译 → 执行
  §2 design-time 路径
  §3 runtime A：平台自动（preCreateBatch）
  §4 runtime B：业务主动执行 ★
  §5 两条路径的上下文差异
  §6 88 函数注册表
  §7 自定义扩展
```

### 4.6 当前证据等级
`STATIC_RULE` + 部分 `VERIFIED_RULE`

### 4.7 资产缺口
- ❌ runtime 主动执行入口（核心缺口）
- ❌ 函数注册表内容

### 4.8 是否需要动态环境
**部分。** 先静态找入口，找到后实测。

---

## 专题 5：接口调用体系（L4）

### 5.1 已有资产
```
core/facts/standard-product/dubbo-cross-service.md    166 行
docs/audit/reference/svc-app-service.txt.gz           10176 行
surface-index.tar.gz: impl-map.json                   269 接口→实现
surface-index.tar.gz: consumers.json                  183 接口→调用者
udc-biz-5.3.517/resources/microflow/*WhiteList.json   ★ 黑白名单
```

### 5.2 具体文件与源码入口
```
DubboFactory#getProxy(Class[, group[, version[, timeout]]])   5 重载
AppServiceProxy#invokeAppService / ForList / ForPage / reliable
AppServiceInvokeDto（18 字段）
GenericInvocationAuthService#invokeAppService(String, String, ...)

分类依据：
  microflow/appServiceMethodBlackList.json
  microflow/bootStarterServiceWhiteList.json
  microflow/systemPackageWhiteList.json
  microflow/entityEventWhiteList.json
```

### 5.3 需要追踪的类和方法
| # | 目标 | 状态 |
|---|---|---|
| 1 | 1000 个 AppService 按域分类 | 数据有，待整理 |
| 2 | 公开/内部/扩展 三分类 | 黑白名单可判定 |
| 3 | `@Autowired` vs `DubboFactory` 判定 | ❌ 待查 |
| 4 | 泛化调用完整链路 | 签名有，待串 |
| 5 | 权限/异常/事务机制 | ❌ 待查 |

### 5.4 需要验证的问题
| # | 问题 |
|---|---|
| Q1 | 什么时候直接注入，什么时候必须取代理 |
| Q2 | 泛化调用与直接调用的权限差异 |
| Q3 | 哪些接口禁止微流程调用 |
| Q4 | 跨应用调用的租户/权限上下文传递 |

### 5.5 预期产物
```
core/facts/platform-dev-system/05-api-invocation-system.md
  §1 AppService 按域分类清单
  §2 三分类判定规则
  §3 注入方式决策树
  §4 泛化调用完整链路
  §5 黑白名单
  §6 权限/异常/事务
```

### 5.6 当前证据等级
`VERIFIED_STATIC_BYTECODE`

### 5.7 资产缺口
- ❌ 方法体（看不到权限实现）
- ✅ 签名 + 黑白名单足够分类

### 5.8 是否需要动态环境
**不需要。**

---

## 专题 6：基础组件体系（L3 横切）

### 6.1 已有资产
```
core/facts/standard-product/boot-core-utils-and-annotations.md  176 行
components/construction/platform_class_index.py                 2669 类 / 26235 方法
```

### 6.2 具体文件与源码入口
```
日期   DateUtils(61) / DateTransformUtil(19)
JSON   JsonNodeUtil(56) / JsonUtils(28) / JsonUtil(20)
缓存   UserCacheUtils(125) / OrgCacheUtils(47)
文件   FileUtils(72) / ExcelTemplateUtil(70)
HTTP   HttpClientUtil(93)
组织   OrgCommonAppService(40)
流程   BpmAppService(22)
存储   StorageService（三桶）
锁     待查
```

### 6.3 需要追踪的类和方法
不是补签名，是补**使用边界**：什么情况该用 / 不该用 / 替代方案 / 坑。

| # | 类 | 要回答 |
|---|---|---|
| 1 | `JsonUtils` | `toMap` vs `toMapThrowError`；同名类坑 |
| 2 | `DateUtils` | 与表达式 `dateToString` 边界 |
| 3 | `StorageService` | 附件关联到实体的姿势 |
| 4 | `OrgCommonAppService` | 查人推荐路径 |
| 5 | `BpmAppService` | send vs submit vs start |
| 6 | `ExcelTemplateUtil` | 与平台导入导出模板关系 |
| 7 | `HttpClientUtil` | 微流程无 HTTP 节点时的用法 |
| 8 | 锁 | 分布式锁类与用法 |

### 6.4 需要验证的问题
每类三问：该用 / 不该用 / 坑。

### 6.5 预期产物
```
core/facts/platform-dev-system/06-base-components.md
  §1 组件分类总览
  §2 每类：用途 / 推荐方法 / 不该用 / 替代 / 示例 / 坑
```

### 6.6 当前证据等级
`VERIFIED_STATIC_BYTECODE`

### 6.7 资产缺口
- ❌ 方法体
- ✅ 签名足够判断用途

### 6.8 是否需要动态环境
**不需要。**

---

## 专题 7：业务能力关联与验证（收口）

### 7.1 已有资产
```
components/construction/business_code_bridge.py
components/construction/platform_class_index.py
components/construction/business_action_index.py
surface-index.tar.gz: action-index.md               682 条业务动作
```

### 7.2 关联链
```
业务需求 → 开发方案 → 平台能力 → 类与方法 → DTO/实体 → 调用链 → 验证方式
```

### 7.3 四个盲测场景（覆盖全部体系层）

| # | 场景 | 依赖专题 | 覆盖了哪几层 |
|---|---|---|---|
| 1 | **普通实体 CRUD** | 1、2、3 | L1 元数据 + L2 生成 + L3 单实体持久化 |
| 2 | **主子表 CRUD** | 1、2、3 | L3 关联写入子节 |
| 3 | **单据保存、提交和流转** | 1、2、3 | L3 单据子节 |
| 4 | **第三方接口集成** | 3、4、5、6 | L3 批量 + L4 表达式/接口 + 组件 |

**注意：场景 2/3 是专题 3 内部的子节验证，不是独立研究专题。**
这样能验证「体系是否真的覆盖了场景」，而不是「场景单独研究」。

**盲测规则：**
- 只给业务需求，不给类名/方法名/接口名
- Agent 自己检索找能力
- 每个方案带证据
- 找不到标 `BLOCKED`

### 7.4 预期产物
```
core/facts/platform-dev-system/07-business-playbook.md
  §1 业务需求 → 能力映射总表
  §2 四个场景完整方案
  §3 盲测报告
  §4 未解决问题
```

### 7.5 当前证据等级
`UNVERIFIED`（待前置）

### 7.6 资产缺口
依赖专题 1-6

### 7.7 是否需要动态环境
盲测 2/3 需要

---

## 三、实施顺序（按体系依赖，不按痛点）

```
专题 1  实体与元数据体系        ← L1 地基，纯静态
   ↓
专题 2  代码生成体系            ← L2，需一次生成实测
   ↓
专题 3  持久化体系              ← L3 核心，在专题 2 的产物上验证
   ├─ 3.1 通用 DAO（静态）
   ├─ 3.2 单实体 + 主键
   ├─ 3.3 关联写入（主子表）★
   ├─ 3.4 单据 + 流转
   ├─ 3.5 批量 + 大数据
   └─ 3.6 查询 + 分页
   ↓
专题 4  表达式体系              ← L3
   ↓
专题 5  接口调用体系            ← L4（纯静态，可并行）
专题 6  基础组件体系            ← 横切（纯静态，可并行）
   ↓
专题 7  业务关联 + 四场景盲测   ← 收口
```

**关键顺序变化（相对 v2）：**
- v2：主子表 → 生成器 → 单据
- v3：**元数据 → 生成器 → 持久化（含主子表/单据/大数据）**

**理由：** 持久化建立在生成产物之上，生成产物建立在元数据之上。
不先搞清楚「一个实体生成了什么」，就无法确定「该调哪个 DAO 方法、主键在哪生成、子表外键谁回填」。

---

## 四、动态环境使用方案（需逐项批准）

### 4.1 环境隔离
```
环境：test2（configtest2 kubeconfig）
⚠️ 不碰 uat，不碰生产
⚠️ 独立测试应用，不复用现有业务应用
```

### 4.2 数据隔离与备份
```
① 测试前记录目标应用 appId 与现有实体清单
② 只用新建测试应用（如「ZZ研究验证-勿用」）
③ 不修改任何现有实体/页面/微流程
④ 测试数据统一前缀 ZZRESEARCH_
⑤ 测试前导出：表结构 + 现有数据行数快照
```

### 4.3 测试范围（按专题）
| 专题 | 允许 | 禁止 |
|---|---|---|
| 2 生成器 | 建最小实体、触发生成、下载产物 | 不改平台配置 |
| 3.2 | 单实体 create/update/delete、查 DB 验主键 | 不删现有数据 |
| 3.3 | 建主表+子表、调 create、查外键 | 不改现有实体 |
| 3.4 | 建 bill 实体、保存、提交（不指定真实审批人） | 不提交到真实审批人 |
| 3.5 | 批量插入（限 1000 条内） | 不做 6 万条压测 |
| 3.6 | 各类查询、分页 | — |
| 4 | 建带默认值表达式的字段 | 不改函数注册表 |

### 4.4 清理方案
```
① 删除测试应用（含实体/页面/微流程）
② 清理 ZZRESEARCH_ 前缀表数据
③ 核对：实体数 / 表数 / 行数 回到测试前快照
④ 输出清理确认报告
```

### 4.5 需你逐项批准
- [ ] 允许在 test2 新建测试应用
- [ ] 允许触发代码生成并下载产物
- [ ] 允许建 bill 实体并提交（不指定真实审批人）
- [ ] 允许查询 DB 验证
- [ ] 允许批量插入（限 1000 条）
- [ ] 清理方案满足要求

**未经批准，不执行任何写操作。**

---

## 五、证据等级规范

| 等级 | 含义 | 判定标准 |
|---|---|---|
| `STATIC_RULE` | 源码/模板/配置静态确认 | tar 包/仓库文件逐字找到 |
| `VERIFIED_RULE` | 调用链/测试/字节码验证 | 签名库命中 + 调用关系闭合 |
| `LIVE_RULE` | 实际运行验证 | 真实响应体/DB 结果/生成产物 |
| `UNVERIFIED` | 尚无充分证据 | 只有推测 |
| `BLOCKED` | 缺资产无法推进 | 明确缺什么 |

**硬规则：**
- 不把类索引当使用知识
- 不把方法签名当调用规范
- 不把模板清单当生成规则
- 每条结论追到：文件路径 + 行号 / 签名库逐字行 / 实测响应体

---

## 六、交付物清单（12 项）

| # | 交付物 | 专题 |
|---|---|---|
| 1 | 平台开发体系总览（分层图 + 七专题关系） | 全部 |
| 2 | 标品接口知识库 | 5 |
| 3 | 实体类型与生成机制知识库 | 1、2 |
| 4 | AppService/Service/DAO 生成规范 | 2 |
| 5 | DAO 持久化专题（含主子表/单据/大数据） | 3 |
| 6 | 表达式机制专题 | 4 |
| 7 | 基础组件使用知识库 | 6 |
| 8 | 业务开发场景知识库 | 7 |
| 9 | 类/方法/DTO/实体/业务关联索引 | 7 |
| 10 | 证据与未解决问题清单 | 全部 |
| 11 | Agent 检索与使用规范 | 全部 |
| 12 | 实战验证报告（4 场景盲测） | 7 |

**落点建议：** `core/facts/platform-dev-system/01-07-*.md`（独立目录，不动现有 `standard-product/`）

---

## 七、需要你审计确认

**A. 体系分层框架**（§一 L0-L4 五层 + 七专题）是否符合你对「大方向」的定义？

**B. 主子表降级为专题 3 的子节 3.3**，与普通实体、单据、大数据并列，是否认可？

**C. 实施顺序改为 元数据 → 生成器 → 持久化 → 表达式 → 接口/组件 → 收口**，是否认可？

**D. 动态环境**：§四 方案，需要你勾选批准 4.5 的 6 项。

**E. 盲测四场景**：普通实体 CRUD / 主子表 CRUD / 单据流转 / 第三方集成，是否就是这四个？

**F. 专题 5、6 并行**：纯静态无依赖，允许在专题 3 进行时并行吗？

**G. 产物落点**：`core/facts/platform-dev-system/` 独立目录，还是并入 `standard-product/`？

---

## 八、本阶段不做

- ❌ 不写新业务功能
- ❌ 不重复整理已有 228 个 facts
- ❌ 不把签名索引当使用文档
- ❌ 不把 `*Impl` 当可用接口
- ❌ 不以 Controller 为主要方向
- ❌ 不改现有 Agent 架构/工具注册
- ❌ 不覆盖现有研究
- ❌ **未经批准不执行 test2 写操作**
- ❌ 不因资产缺失就推断补全
