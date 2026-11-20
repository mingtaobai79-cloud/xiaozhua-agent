# Seeyon 平台开发体系研究计划 v4（可审计版）

> **状态：仅重构研究计划。未实施研究、未改代码、未改 facts、未操作 test2。**
> 生成日期：2026-11-17
> 仓库：`C:/Users/白明涛/xiaozhua-agent`
> 前序：v3（`.hermes/plans/2026-11-17_platform-dev-system-research-v3.md`，保留不覆盖）

---

## 零、v4 相对 v3 的实质性修正

v3 存在**证据等级虚高**和**统计口径不一致**两类问题。v4 逐条修正：

| # | v3 的问题 | v4 的修正 | 影响 |
|---|---|---|---|
| 1 | 「32 个 CodeTask」当成全部实现 | 实测 `code(CodeContext)` 实现类 **53 个**；32 只是 `autocode.task` 顶层包 | 口径必须写清包范围 |
| 2 | 「24 个 Template」 | 实测声明 `getTemplateOutMap()` 的类 **36 个** | 数量与判定依据都错 |
| 3 | 「`copyNeedResetNull` 是覆盖坑的根因」 | 签名库全库检索：**该方法零调用者**，只有声明 | **必须降级为待验证**，不得认定为根因 |
| 4 | 「1000 个 AppService」 | 实测 `svc-app-service.txt.gz`：**830 个类 / 9343 个方法** | 概数改实测值 |
| 5 | `AllInOneBaseDao` 包名未写 | 真实包名 `com.seeyon.boot.starter.mybatis.inone.dao`（41 方法）+ `AbstractAllInOneBaseDao`（55 方法） | 41 方法对，但父类还有 55 |
| 6 | 「模板清单 = 生成规则」倾向 | 模板清单只证明**资产记录存在**，不证明选择机制 | 证据等级降为 `STATIC_RULE` |
| 7 | 未区分方法存在 vs 运行行为 | 全文贯彻：签名只证明存在 | 每个结论标判定依据 |
| 8 | 五方向/七专题关系未说清 | 明确：五方向是**研究组织模型**，非平台真实架构 | 防止把模型当事实 |

### 0.1 统计口径声明（v4 所有数字的来源）

| 指标 | 实测值 | 统计来源 | 统计口径 | 版本 |
|---|---|---|---|---|
| 签名库总量 | 245709 行 | `docs/audit/signatures.txt.gz` | 全文件行数 | udc-platform-5.3.517 |
| 类声明 | 21389 | 同上 | 第 2 列为 class/interface/enum/@interface | 同上 |
| 方法声明 | 224320 | 同上 | 含 `#` 且含 `(` | 同上 |
| `code(CodeContext)` 实现类 | **53** | 同上 | 含 `#code(com.seeyon.udc.common.autocode.context.CodeContext)` 的类去重 | 同上 |
| ├ 其中 `autocode.task` 顶层包 | 30 | 同上 | 包名精确等于 `com.seeyon.udc.autocode.task` | 同上 |
| ├ `autocode.task.front` | 5 | 同上 | — | 同上 |
| ├ `autocode.v27.task` | 9 | 同上 | 版本化任务 | 同上 |
| ├ `autocode.v27.task.front` | 5 | 同上 | — | 同上 |
| ├ `common.autocode`（接口自身） | 1 | 同上 | `CodeTask` 接口 | 同上 |
| └ `extend.*` 扩展任务 | 3 | 同上 | `AssociateCodeTask` / `CtpEnumCodeTask` / `CtpExcelJsonTask` | 同上 |
| 声明 `getTemplateOutMap()` 的类 | **36** | 同上 | 含该方法签名的类去重 | 同上 |
| ├ `autocode.template` | 23 | 同上 | — | 同上 |
| └ `autocode.v27.template` | 13 | 同上 | — | 同上 |
| `template.base` 抽象基类 | 4 | 同上 | `Abstract*FreemarkerTemplate` / `AbstractDecorate*` | 同上 |
| 类名以 Template 结尾（全平台） | 73 | 同上 | 第 2 列为 class/interface | 同上 |
| 模板清单条目 | **464** | `udc-biz-5.3.517/_codegen_templates.json` | 41 组全部 value 元素计数 | udc-biz-5.3.517 |
| 模板清单分组 | 41 | 同上 | 顶层 key 数 | 同上 |
| 模板版本目录 | 4 | 同上 | 2.7 / 2.8 / 2.9 / 3.0 | 同上 |
| `AllInOneBaseDao` 方法 | **41** | `signatures.txt.gz` | `com.seeyon.boot.starter.mybatis.inone.dao.AllInOneBaseDao#` | 同上 |
| `AbstractAllInOneBaseDao` 方法 | 55 | 同上 | `com.seeyon.boot.starter.mybatis.AbstractAllInOneBaseDao#` | 同上 |
| AppService 类 | **830** | `docs/audit/reference/svc-app-service.txt.gz` | 含 `#` 行的类去重 | udc-platform-5.3.517 |
| AppService 方法 | 9343 | 同上 | 含 `#` 的行数 | 同上 |
| udc 实体 Service 接口 | 179 | `signatures.txt.gz` | 类名匹配 `udc.*\.(api|service)\.\w+Service` 且有方法行 | 同上 |
| 全平台 `Template` 相关类 | 73 | 同上 | 类名后缀 Template | 同上 |

**硬规则：任何报告里的数字，必须能在这里找到口径。对不上的数字一律重新统计，不许沿用。**

---

## 一、研究组织模型（不是平台架构）

### 1.1 五个研究方向

```
方向 A  应用与元数据        Application / Entity / Attribute / Relation / Bill / Page / MicroFlow
方向 B  代码生成            AutoCodeExecutor → CodeContext → CodeTask → Template → 产物
方向 C  生成物与持久化       Entity / DTO / AppService / Service / DAO / Mapper / XML → 运行时写入
方向 D  运行时能力           表达式 / 事件 / 微流程 / 单据生命周期
方向 E  平台服务与对外集成    Dubbo / @Autowired / 泛化 / 微流程调用 / 第三方
```

**⚠️ 重要声明：这五个方向是「研究组织模型」，不是已证实的平台内部架构。**
它们由元数据分组、包名聚类和调用链观察归纳而来，**不得在任何产物中表述为平台官方分层**。

### 1.2 七个专题与五方向的映射

| 专题 | 主要方向 | 次要方向 |
|---|---|---|
| 1 实体与元数据体系 | A | B |
| 2 代码生成体系 | B | A、C |
| 3 生成物与持久化体系 | C | B、D |
| 4 表达式与运行时能力 | D | C、B |
| 5 接口调用体系 | E | C |
| 6 基础组件体系 | E 横切 | 全部 |
| 7 业务能力关联体系 | 全部收口 | — |

---

## 二、专题一：应用与元数据体系

### 1. 研究目标
搞清平台有哪些元数据对象、它们怎么存、怎么改、谁参与生成、谁参与运行时。

### 2. 已有证据
| 证据 | 位置 | 等级 |
|---|---|---|
| 6 种 stereotype 定义 | `udc-biz-5.3.517/resources/stereotype/*/config.json` | STATIC_RULE |
| 26 个 feature 定义 | `udc-biz-5.3.517/resources/feature/*/config.json` | STATIC_RULE |
| 实体类型必要特性 | `core/facts/udc/entity/evidence/entity-write-2026-10-23/stereotype-authoritative.json` | VERIFIED_STATIC_BYTECODE |
| 元数据存储链路 | 记忆条目 + `core/facts/udc/entity/*.md` | 部分 LIVE_RULE |
| DTO 中文字段 | `surface-index.tar.gz: dto-meta.json`（1305 个） | STATIC_RULE |

**已逐字核实的 6 种 stereotype（来自 stereotype-authoritative.json）：**
```
standard      basic
form          basic + formBasic
basicData     basic
bill          basic + approve + organization + billBasic + termination + suspend + nullify
archive       basic + archiveBasic + approve + archiveTiled
archiveTree   basic + archiveBasic + approve + treeEntity
```

### 3. 现有资产与文件路径
```
udc-biz-5.3.517/resources/stereotype/{standard,form,basic_data,bill,archive,archive_tree}/config.json
udc-biz-5.3.517/resources/feature/*/config.json                     26 份
udc-biz-5.3.517/resources/presetData/{entity,attribute,attributeSet,billEnum,
    formEnum,archiveEnum,dependencyGraph,scalability,scalabilityGlobal}.json
udc-biz-5.3.517/resources/openApi/entityOpenApi.json
udc-biz-5.3.517/EntityService.javap.txt                              实体领域服务
core/facts/udc/entity/*.md                                           10 个已有 facts
surface-index.tar.gz: dto-meta.json                                  1305 DTO
```

### 4. 待研究类、方法和资源
| # | 对象 | 待查 |
|---|---|---|
| 1 | `stereotype/*/config.json` 6 份 | 每个特性的具体字段与含义 |
| 2 | `feature/*/config.json` 26 份 | 每个特性带来哪些生成物/运行时行为 |
| 3 | `EntityService`（javap 已有） | 元数据 CRUD 的领域方法 |
| 4 | `presetData/dependencyGraph.json` | 元数据对象间依赖关系 |
| 5 | `presetData/scalability*.json` | 扩展字段机制 |
| 6 | `entityOpenApi.json` | 哪些实体开放为 OpenAPI |
| 7 | `EntityRelationMultiplicityEnum` | 关联重数的取值与语义 |
| 8 | `AggregationDto` | 聚合（主子表）的元数据表达 |

### 5. 待验证问题
| # | 问题 | 判定依据 |
|---|---|---|
| Q1 | 六种实体类型除特性列表外，还有什么本质区别 | config.json 全文 + 生成物差异 |
| Q2 | 特性如何组合出实体能力（basic+approve+billBasic = 单据？） | 需实测对比生成物 |
| Q3 | 元数据对象之间的依赖关系图 | dependencyGraph.json |
| Q4 | 哪些对象参与代码生成、哪些只参与运行时 | 需交叉 CodeContext 字段 |
| Q5 | 元数据存储：MySQL → Redis → OSS 的具体分工 | 需实测确认 |
| Q6 | 关联字段（relationEntity）与聚合字段的区别 | 元数据定义 + 生成物 |

### 6. 具体研究步骤
```
1. 解压 udc-platform-5.3.517.tar.gz 到工作目录（只读，不改仓库）
2. 逐个解析 6 份 stereotype config.json，产出对照表
3. 逐个解析 26 份 feature config.json，产出「特性 → 行为」表
4. 解析 dependencyGraph.json，画出对象依赖图
5. 解析 presetData/*.json，确认字段类型体系
6. 交叉 EntityService javap 方法，确认元数据 CRUD 入口
7. 把「参与生成 / 参与运行时」两列填满（依据 CodeContext 字段 + 运行时调用）
```

### 7. 预期产物
```
core/facts/platform-dev-system/01-application-metadata.md
  §1 元数据对象全景（Application/Entity/Attribute/Relation/Bill/Page/MicroFlow）
  §2 六种 stereotype 对照表（特性 + 生成物 + 运行时行为）
  §3 26 个 feature 逐个说明
  §4 对象依赖关系图（来源：dependencyGraph.json）
  §5 元数据存储位置与生命周期
  §6 参与生成 vs 参与运行时 分类表
  §7 关联与聚合的元数据表达
```

### 8. 验收标准
- [ ] 6 份 stereotype config 全部解析，字段级对照，无「待补」
- [ ] 26 份 feature config 全部解析
- [ ] 依赖图能追溯到 dependencyGraph.json 的具体条目
- [ ] 「参与生成/运行时」两列每个对象都有判定依据
- [ ] 所有结论标 STATIC_RULE 或以上，无 UNVERIFIED 混入正文

### 9. 证据等级
`STATIC_RULE` 为主；`EntityService` 相关可到 `VERIFIED_STATIC_BYTECODE`

### 10. 阻塞与降级方案
| 阻塞 | 降级 |
|---|---|
| feature config 语义不明（只有 JSON 无文档） | 只描述字段结构，不解释语义，标 UNVERIFIED |
| dependencyGraph 结构复杂 | 只提取直接依赖，不做传递闭包 |

### 11. 是否需要动态环境
**不需要。** 纯静态解析。

### 12. 依赖关系
- 被依赖：专题 2（生成器需要元数据输入）、专题 3（持久化需要实体结构）
- 依赖：无

---

## 三、专题二：代码生成体系

### 1. 研究目标
还原「元数据 → 生成物」的完整机制，建立 **CodeTask → Template → 模板资源 → 输出产物** 映射表。

### 2. 已有证据
| 证据 | 位置 | 等级 |
|---|---|---|
| 生成主链签名 | `signatures.txt.gz`（见下） | VERIFIED_STATIC_BYTECODE |
| `EntityRuleTask` javap | `udc-biz-5.3.517/EntityRuleTask.javap.txt` | VERIFIED_STATIC_BYTECODE |
| 模板清单 464 条 | `udc-biz-5.3.517/_codegen_templates.json` | STATIC_RULE（**仅证明资产记录存在**） |
| `generator.properties` | `gg_isOverride = true` | STATIC_RULE |
| 8 个 OutPath 方法签名 | `EntityFileTemplate` | VERIFIED_STATIC_BYTECODE（**仅证明方法存在**） |
| `ExpressionCodeGenerator` | `generateCode(config): CodeGenerateResult` | VERIFIED_STATIC_BYTECODE |

**已逐字核实的生成主链（签名库）：**
```java
com.seeyon.udc.autocode.AutoCodeExecutor
  # execute(ApplicationDto, CodeParam)
  # executeSegment(ApplicationDto, CodeParam)
  # runTask(CodeContext, List<CodeTask>): void
  # resolveSchema(CodeContext, AutoCodeResult): void
  # outputPresetSchema(CodeContext, PersistResult): void
  # compareToLast(CodeContext, PersistResult, ...)

com.seeyon.udc.autocode.AutoCodeManager
  # execute(ApplicationDto, Map<String,Object>, ...)
  # downloadAndZipLocal(ApplicationDto): File
  # getAppCopySchemaInfo(long, ContextTypeEnum): List<SchemaInfo>

com.seeyon.udc.common.autocode.CodeTask        ← 接口
  # code(CodeContext): String

com.seeyon.udc.autocode.template.base.AbstractUdcFreemarkerTemplate
  # getCodeContext(): CodeContext
  # writeToString(Object, String): String        ← ★ Freemarker 渲染入口
```

**⚠️ 关键澄清：`writeToString` 证明模板是 Freemarker 渲染，但不证明渲染参数如何构建。**

### 3. 现有资产与文件路径
```
udc-biz-5.3.517/_codegen_templates.json                464 条 / 41 组 / 4 版本
udc-biz-5.3.517/EntityRuleTask.javap.txt               生成器实现（部分）
udc-biz-5.3.517/resources/generator.properties         gg_isOverride
udc-biz-5.3.517/resources/_index.json                  资源索引
core/facts/standard-product/autocode-project-templates.md   已有 194 行
signatures.txt.gz                                      5275 行 autocode 相关
```

### 4. 待研究类、方法和资源
| # | 对象 | 待查 | 已知 |
|---|---|---|---|
| 1 | `CodeContext` | 字段结构（承载哪些元数据） | 类型名 |
| 2 | 53 个 `code(CodeContext)` 实现 | 每个的 `matches()` 条件 | 类名全 |
| 3 | 36 个 `getTemplateOutMap()` 类 | 返回 Map 的键值语义 | 类名全 |
| 4 | `AbstractUdcFreemarkerTemplate#writeToString` | 参数 2 是模板路径？ | 签名 |
| 5 | 模板资源加载路径 | 从 classpath 还是文件系统 | **未知** |
| 6 | 版本选择（2.7/2.8/2.9/3.0） | 谁决定用哪个版本目录 | **未知** |
| 7 | `EntityFileTemplate` 8 个 OutPath | 实际拼接规则 | 签名 |
| 8 | `gg_isOverride=true` | 覆盖策略具体行为 | 值 |
| 9 | `ExpressionCodeGenerator#generateCode` | 表达式代码生成链路 | 签名 |
| 10 | `CodeGenerateResult` | 6 个字段的语义 | 签名 |

**已枚举的 53 个实现（按包，v4 精确口径）：**
```
com.seeyon.udc.autocode.task            30 个
com.seeyon.udc.autocode.task.front       5 个
com.seeyon.udc.autocode.v27.task         9 个
com.seeyon.udc.autocode.v27.task.front   5 个
com.seeyon.udc.common.autocode           1 个（接口自身）
com.seeyon.udc.extend.task               1 个（CtpExcelJsonTask）
com.seeyon.udc.extend.detection.associate.deploy  1 个（AssociateCodeTask）
com.seeyon.udc.extend.domain.service.deploy       1 个（CtpEnumCodeTask）
```

**⚠️ v27 包有 14 个版本化任务（9 + 5），这是版本选择机制的实证入口，但「谁选 v27」仍未知。**

### 5. 待验证问题
| # | 问题 | 可能判定依据 | 若失败则 |
|---|---|---|---|
| Q1 | CodeTask 与 Template 是否一一对应 | 需 `matches()` + `getTemplateOutMap()` 交叉 | **标 UNVERIFIED，禁止宣称对应** |
| Q2 | 模板资源从哪加载（classpath/文件系统/DB） | 需反编译 `AbstractUdcFreemarkerTemplate` | BLOCKED |
| Q3 | 版本目录（2.7/2.8/2.9/3.0）选择逻辑 | 需反编译或实测 | BLOCKED |
| Q4 | 8 个 OutPath 的拼接规则（包名+文件名+路径） | 需反编译 `EntityFileTemplate` | 实测产物反推 |
| Q5 | 重新生成是否覆盖手写代码 | `gg_isOverride` + 实测 | 需动态 |
| Q6 | 主子表聚合生成完整调用链 | `EntityRuleTask#generateAggregateRootEntityRule` 反编译 | 实测产物 |
| Q7 | 表达式代码如何注入实体代码 | `Expression4EntityUtil` + `CodeGenerateResult` | BLOCKED |

**★ 关于 `copyNeedResetNull` 的专门澄清（v3 错误修正）：**

```
实测：全签名库检索 copyNeedResetNull
  → 仅 1 行：com.seeyon.udc.autocode.template.EntityFileTemplate#copyNeedResetNull(AttributeDto):boolean
  → 零调用者、零其他实现

结论：
  ✓ 该方法存在于 EntityFileTemplate
  ✗ 无法证明它被谁调用
  ✗ 无法证明它影响运行时行为
  ✗ 绝不能认定为「表达式覆盖坑」的根因

待办：
  1. 反编译 EntityFileTemplate 看方法体
  2. 看它在 getTemplateOutMap/getArgumentMap 中是否被引用
  3. 看生成的代码里是否有对应的 null 重置逻辑
  4. 用实测验证：设默认值表达式 + 传非空值，看结果
  → 四条全部完成才能下结论
```

### 6. 具体研究步骤
```
阶段 1（纯静态，无阻塞）
  1. 解压 tar 到工作目录
  2. 解析 _codegen_templates.json，产出 41 组 × 464 条完整表
  3. 从签名库提取 53 个实现 + 36 个 Template，建立候选映射
  4. 提取每个类的全部方法（不只 code/getTemplateOutMap）
  5. 交叉比对：Task 名 ↔ Template 名 ↔ 模板文件名的命名关联（仅作候选，不作结论）

阶段 2（需要反编译，若无法则降级）
  6. 反编译 AbstractUdcFreemarkerTemplate → 模板加载机制
  7. 反编译 EntityFileTemplate → 8 个 OutPath 拼接规则 + copyNeedResetNull 方法体
  8. 反编译 EntityRuleTask → 主子表聚合链路
  9. 反编译 ExpressionCodeGenerator → 表达式代码生成

阶段 3（需要实测，需单独批准）
  10. 建最小实体 → 触发生成 → 下载产物
  11. 比对产物路径与 OutPath 签名，验证 Q4
  12. 改一处手写代码 → 重新生成 → 看是否被覆盖（验证 Q5）
```

### 7. 预期产物
```
core/facts/platform-dev-system/02-codegen-system.md
  §1 生成主链（已证实部分 / 待证实部分 分开写）
  §2 CodeTask 全表（53 个，标注包、职责、已知/未知）
  §3 Template 全表（36 个，标注包、OutPath 方法）
  §4 ★ CodeTask → Template → 模板资源 → 产物 映射表（未证实项标 UNVERIFIED）
  §5 模板清单 464 条（41 组，4 版本）
  §6 输出路径与包名规则（有证据的 / 推断的 分开）
  §7 生成 vs 手写边界（gg_isOverride 实测结论）
  §8 表达式代码生成链路
  §9 copyNeedResetNull 专项调查（含"为什么 v3 结论不成立"）
```

### 8. 验收标准
- [ ] 53 个 CodeTask 全部列出，每个有包名 + 关键方法
- [ ] 36 个 Template 全部列出，每个有 OutPath 方法清单
- [ ] 映射表每一行标注证据等级；无证据的必须写 UNVERIFIED
- [ ] **禁止出现「CodeTask 与 Template 一一对应」这类未经证实的断言**
- [ ] `copyNeedResetNull` 结论必须基于四条验证，缺一条就写「未完成」
- [ ] 8 个 OutPath 的拼接规则：有证据写规则，无证据写「需实测」

### 9. 证据等级
`STATIC_RULE`（模板清单）+ `VERIFIED_STATIC_BYTECODE`（签名）
→ 目标：反编译后升 `VERIFIED_STATIC_BYTECODE`（含实现）；实测后升 `LIVE_RULE`

### 10. 阻塞与降级方案
| 阻塞 | 影响 | 降级 |
|---|---|---|
| 无 .ftl 内容 | 无法看模板语法 | 只做清单级，不推断模板内容 |
| 无 jar 本体 | 无法反编译 | **降级：用实测产物反推**（需批准） |
| 无 CFR 工具 | 同上 | 可尝试装 CFR（需批准） |
| `matches()` 无法获取 | 无法确定 Task 选中条件 | 标 UNVERIFIED，只描述存在 |

**降级路线（.ftl 和 jar 都没有时的最低可交付）：**
```
模板清单（464 条） + 签名（53 Task / 36 Template） + 实测产物（8 个文件）
→ 能回答：生成什么文件、输出到哪、包名是什么、三层各是什么
→ 不能回答：模板内部逻辑、Task 选中条件、版本选择算法
```

### 11. 是否需要动态环境
**阶段 1 不需要；阶段 3 需要**（触发生成 + 下载产物 + 覆盖测试）。
需单独批准，见 §九 审批项 B。

### 12. 依赖关系
- 依赖：专题 1（元数据输入）
- 被依赖：专题 3（生成物是持久化的前提）、专题 4（表达式代码生成）

---

## 四、专题三：生成物与持久化体系

### 1. 研究目标
1. 搞清 7 类生成物（Entity/DTO/AppService/Service/DAO/Mapper/XML）各自的职责、调用关系、生成来源。
2. 搞清持久化全链路：CRUD、主键、查询、批量、关联、单据、事务、隔离。

### 2. 已有证据
| 证据 | 位置 | 等级 |
|---|---|---|
| `AllInOneBaseDao` 41 方法 | `com.seeyon.boot.starter.mybatis.inone.dao.AllInOneBaseDao` | VERIFIED_STATIC_BYTECODE |
| `AbstractAllInOneBaseDao` 55 方法 | `com.seeyon.boot.starter.mybatis.AbstractAllInOneBaseDao` | VERIFIED_STATIC_BYTECODE |
| DAO 已有研究 | `core/facts/standard-product/dao-and-mybatis.md`（205 行） | 部分 LIVE |
| `preCreateBatch` + 闸门 | `core/facts/udc/microflow/node-insert-entity.md` | 部分 LIVE |
| 表达式覆盖坑 | `core/facts/udc/microflow/write-node-runtime-gap.md:215-245` | LIVE_RULE |
| 用户实测复盘 | `~/Desktop/自定义微流程对接外部接口-问题复盘.md` | LIVE_RULE |
| bill 七特性 | `stereotype/bill/config.json` | STATIC_RULE |

**已逐字核实的 41 个 DAO 方法（按用途分类）：**
```
写：create / createBatch / update / updateBatch / updateColumns
    updateColumnsIgnoreVersion / versionNoUpdateBatchIgnoreVersion / versionNoUpdateIgnoreVersion
删：deleteById / deleteByIds / deleteByCondition / deleteByConditions
    deleteByComplexConditions / deleteByDynamicConditions
读单：selectById / selectByIds / selectOneByCondition / selectOneByConditions
读列：selectListByCondition / selectListByConditions / selectListByComplexConditions
      selectListByDynamicConditions / selectListExcludeByConditions
      selectListPropertiesByConditions / selectPagePropertiesByConditions
      selectPageExcludeByConditions
读页：selectPageByCondition / selectPageByConditions
      selectPageByComplexConditions / selectPageByDynamicConditions
计数：selectCountByCondition / selectCountByConditions
      selectCountByComplexConditions / selectCountByDynamicConditions
聚合：selectListFuncByComplexConditions / selectListFuncByDynamicConditions
```

### 3. 现有资产与文件路径
```
core/facts/standard-product/dao-and-mybatis.md
core/facts/udc/microflow/node-insert-entity.md
core/facts/udc/microflow/write-node-runtime-gap.md
signatures.txt.gz                                      AllInOneBaseDao / AbstractAllInOneBaseDao
udc-biz-5.3.517/_codegen_templates.json                2.7/entity 19 条（含 dao/mybatis.xml）
udc-biz-5.3.517/resources/stereotype/bill/config.json
udc-biz-5.3.517/resources/feature/{approve,bill_basic,organization,
    termination,suspend,nullify}/config.json
```

### 4. 待研究类、方法和资源

**4.1 七类生成物**
| 类 | 模板 | OutPath 方法 | 待查 |
|---|---|---|---|
| Entity | `entity.java.ftl` | `getEntityOutPath()` | 包名、注解、字段映射 |
| DTO | `dto.java.ftl` | `getDtoOutPath()` | DTO↔Entity 转换 |
| AppService | `appservice.java.ftl` | `getAppServiceOutPath()` | 接口方法生成规则 |
| AppServiceImpl | `appserviceImpl.java.ftl` | `getAppServiceImplOutPath()` | 实现是否可改 |
| Service/BaseService | `baseservice.java.ftl` | `getBaseServiceOutPath()` | 业务逻辑写哪 |
| DAO | `dao.java.ftl` | `getDaoOutPath()` | 继承哪个基类 |
| Mapper XML | `mybatis.xml.ftl` | `getMybatisXmlOutPath()` | 动态 SQL 生成 |

**4.2 持久化待研究**
| # | 子项 | 待查 | 能否静态 |
|---|---|---|---|
| 1 | 通用 DAO 能力 | 41+55 方法场景 | ✅ |
| 2 | 单实体 CRUD | create/update/delete 实际行为 | 部分 |
| 3 | **主键生成** | 谁生成、何时生成、什么策略 | ❌ 需实测 |
| 4 | 查询/分页/动态 SQL | XML 生成规则 | 需产物 |
| 5 | 批量写入 | 分批阈值、事务 | ❌ 需实测 |
| 6 | **主子表关联写入** | 主表 ID → 子表外键回填 → 顺序 | ❌ 需实测 |
| 7 | **单据保存** | 与普通实体差异 | ❌ 需实测 |
| 8 | **单据提交与流转** | 谁驱动、状态谁维护 | ❌ 需实测 |
| 9 | 事务边界 | `@Transactional` 在哪层 | 部分 |
| 10 | 权限/租户/应用隔离 | 上下文怎么传 | 部分 |
| 11 | 逻辑删除 | 字段名、默认行为 | 部分 |
| 12 | 异常处理 | 抛什么、怎么包 | 部分 |

### 5. 待验证问题
| # | 问题 | 判定依据 |
|---|---|---|
| Q1 | 三层（AppService/Service/DAO）谁调谁 | 签名 + 反编译 |
| Q2 | 业务逻辑应该写哪层 | 生成物 + `gg_isOverride` |
| Q3 | 主键生成时机（insert 前/后） | **必须实测** |
| Q4 | 子表外键谁回填 | **必须实测** |
| Q5 | 主子表保存顺序 | **必须实测** |
| Q6 | 更新策略（全量 vs 增量） | **必须实测** |
| Q7 | 删除策略（级联 vs 手动） | **必须实测** |
| Q8 | 单据能否绕过 BPM 直接 DAO | **必须实测** |
| Q9 | 一次批量是否单事务 | **必须实测** |
| Q10 | 批量上限 | **必须实测** |
| Q11 | 逻辑删除是平台统一还是实体配置 | config 检查 |
| Q12 | 异常如何包装（统一异常？） | 反编译 |

### 6. 具体研究步骤
```
阶段 1（静态，无阻塞）
  1. 解析 2.7/entity 的 19 条模板，确认七类生成物
  2. 从签名库提取 AllInOneBaseDao + AbstractAllInOneBaseDao 全部方法签名
  3. 交叉 dao-and-mybatis.md，补齐「方法 → 场景」表
  4. 查逻辑删除相关（字段名/注解/配置）
  5. 查事务注解所在层
  6. 解析 bill/config.json + 6 个单据特性 config

阶段 2（需要生成产物，依赖专题 2 阶段 3）
  7. 拿到真实生成的 7 个文件 → 确认包名、命名、继承关系
  8. 从 Mapper XML 产物反推动态 SQL 生成规则

阶段 3（需要实测，需单独批准）
  9. 单实体：create → 查 DB → 确认主键生成时机
  10. 主子表：建主+子 → create → 查外键 → 确认回填时机
  11. 主子表：update → 确认更新策略
  12. 主子表：delete → 确认级联行为
  13. 单据：建 bill → 保存 → 提交 → 查状态流转
  14. 批量：插入 N 条 → 确认分批与事务
```

### 7. 预期产物
```
core/facts/platform-dev-system/03-generated-artifacts-and-persistence.md
  §1 七类生成物职责表（文件名/包名/继承/可改性）
  §2 三层调用关系图
  §3 平台预制 vs 生成代码 vs 开发者自定义（三色区分）
  §4 通用 DAO 能力（41+55 方法场景表）
  §5 单实体 CRUD 与主键生成
  §6 查询/分页/动态 SQL
  §7 批量写入
  §8 主子表关联写入（ID → 外键 → 顺序 → 事务）
  §9 单据保存与流转（含禁止直接 DAO 清单）
  §10 事务/权限/租户/逻辑删除/异常
  §11 陷阱汇总（含用户实测踩坑）
```

### 8. 验收标准
- [ ] 七类生成物每类都有：文件名、包名、模板名、继承关系、能否手改
- [ ] 三层调用关系有证据（不是按命名推断）
- [ ] 「平台预制 / 生成代码 / 开发者自定义」三色标注完整
- [ ] 持久化 12 个子项每个都有结论或明确的 UNVERIFIED
- [ ] 主子表：ID 生成、外键回填、顺序、更新、删除、事务 六项全部有实测证据
- [ ] 单据：保存 vs 提交的区别有实测证据
- [ ] 陷阱汇总每条都来自真实踩坑，不编造

### 9. 证据等级
`VERIFIED_STATIC_BYTECODE`（DAO 签名）→ 目标 `LIVE_RULE`（持久化行为）

### 10. 阻塞与降级方案
| 阻塞 | 降级 |
|---|---|
| 无法实测 | 主子表/单据/主键全部标 UNVERIFIED，只交付静态部分 |
| 无生成产物 | 七类生成物只写模板名和 OutPath 签名，不写实际包名 |
| 无 DB 权限 | 主键生成时机无法验证，标 BLOCKED |

### 11. 是否需要动态环境
**必须。** 主键生成、外键回填、保存顺序、事务、单据流转，静态无法确定。
审批项见 §九 C/D/E/F。

### 12. 依赖关系
- 依赖：专题 2（生成产物）、专题 1（实体结构）
- 被依赖：专题 4（表达式在写入中的作用）、专题 7（场景验证）

---

## 五、专题四：表达式与运行时能力

### 1. 研究目标
1. 还原表达式完整生命周期：定义 → 注册 → 解析 → 编译 → 执行。
2. **重点回答：表达式如何参与实际数据创建和更新**（不只是函数清单）。
3. 区分「平台自动执行」与「业务主动执行」。

### 2. 已有证据
| 证据 | 位置 | 等级 |
|---|---|---|
| design-time 编译 | `core/facts/udc/expression/engine.md`（421 行） | 部分 LIVE |
| 88 个函数 | `core/facts/udc/expression/functions.md`（800 行） | STATIC_RULE |
| 131 个系统变量 | `system-variables.md`（189 行） | STATIC_RULE |
| `executeExpression*` 覆盖坑 | `write-node-runtime-gap.md:215-245` | LIVE_RULE |
| 表达式代码生成器 | `ExpressionCodeGenerator` 签名 | VERIFIED_STATIC_BYTECODE |
| 函数注册表 | `resources/formula-functions.xml` | STATIC_RULE |

**★ v4 新发现（v3 未记录）：表达式有独立的代码生成子系统**

```java
com.seeyon.udc.expression.codegen.ExpressionCodeGenerator
  # getInstance(): ExpressionCodeGenerator
  # generateCode(ExpressionCodeGenConfig): CodeGenerateResult     ← ★ 主入口
  # doGenerateCode(ExpressionCodeGenConfig): CodeGenerateResult
  # getScriptBuildContext(ExpressionDesignDataDto, ...)
  # buildMethodBody(String, String, ExprCodeGenContext)
  # buildCodeFragment(ExprCodeGenContext, String)
  # resolveImports(Set<String>): Set<String>

com.seeyon.udc.expression.codegen.CodeGenerateResult
  # getMethodName(): String          ← ★ 生成的方法名（如 exp<雪花ID>）
  # getMethodBody(): String          ← ★ 方法体
  # getCodeFragment(): String        ← ★ 代码片段
  # getImportClasses(): Set<String>  ← ★ 需要 import 的类
  # getParamEntityMap(): List<Map<Long,Object>>

com.seeyon.udc.expression.codegen.ExpressionCodeGenConfig
  # getVariableType(): ExpressionVariableTypeEnum
  # getParamMapName(): String
  # getDecimalScale(): Integer
  # getUdcEnumFullNameMap(): Map<String,String>
  # getRefPath(): String
  # getSourceAppName(): String

com.seeyon.udc.expression.codegen.interpreter.Interpreter      ← 接口
  ├ BinaryInterpreter / UnaryInterpreter / ScalarInterpreter
  ├ VariableInterpreter / EntityVariableInterpreter
  ├ MicroFlowVariableInterpreter / SystemInterpreter
  └ function.FunctionInterpreter（+ 7 个具体函数解释器）

com.seeyon.udc.utils.Expression4EntityUtil        ← ★ 表达式 → 实体代码的桥
  # parseExpressionToken(List<AttributeDto>, Function<...>)
  # sortComputeExpression(LinkedHashMap<String, CodeGenerateResult>)
  # expressionImportPackages(LinkedHashMap<String, CodeGenerateResult>)
  # defaultValueIsChangeAttributeDtoList(EntityDto): List<String>
  # filterEntityDtoWithComputeAttributeDto(EntityDto)
  # resolveAggInfiniteLoop(EntityDto): void          ← ★ 聚合死循环保护
  # getValueScopeMethodExpression(EntityDto, String, ApplicationDto)
  # checkSystemVariable(AttributeDto): void
  # resolveExpressionParam(List<AttributeDto>, Map<String, Hutool...>)
```

**这条链路说明：表达式不是运行时解释执行，而是「编译成 Java 方法 + 注入实体代码」。**
这解释了 `executeExpression<实体名>` + `exp<雪花ID>` 的命名来源。

### 3. 现有资产与文件路径
```
core/facts/udc/expression/{engine,functions,README,system-variables}.md
core/facts/udc/microflow/write-node-runtime-gap.md
udc-biz-5.3.517/resources/formula-functions.xml
udc-biz-5.3.517/resources/microflow/macro/presetMacro.json
udc-biz-5.3.517/_codegen_templates.json  → 2.7/entityrule 10 条
    AssignValueActivity.ftl / AttributeRequiredActivity.ftl
    AttributeUniqueActivity.ftl / DefaultValueActivity.ftl
    ShowMessageActivity.ftl / common/EntityRuleTemplateUtil.ftl
    common/SetValueUtil.ftl / entityValueForRoot.ftl / ruleservice.java.ftl
udc-biz-5.3.517/_codegen_templates.json  → 2.7/common
    macro-formula-entity.ftl / formula-param-map.ftl
signatures.txt.gz  → udc.expression.codegen.* 全包
```

### 4. 待研究类、方法和资源
| # | 对象 | 待查 |
|---|---|---|
| 1 | `formula-functions.xml` | 函数注册结构（88 个函数怎么注册） |
| 2 | `ExpressionCodeGenerator#generateCode` | 完整生成流程 |
| 3 | `CodeGenerateResult` 6 字段 | 怎么注入实体代码 |
| 4 | `Expression4EntityUtil` 8 个公开方法 | 表达式 → 实体的桥接逻辑 |
| 5 | `Interpreter` 9 个实现 | 每类 AST 节点怎么转代码 |
| 6 | `FunctionInterpreterFactory` | 函数解释器怎么选 |
| 7 | **runtime 主动执行入口** | ★ 业务代码怎么执行表达式 |
| 8 | `executeExpression*` 生成规则 | 命名、参数、requireNull |
| 9 | `resolveAggInfiniteLoop` | 聚合表达式死循环保护 |
| 10 | `macro-formula-entity.ftl` | 实体代码里表达式部分的模板 |

### 5. 待验证问题
| # | 问题 | 依据 |
|---|---|---|
| Q1 | 表达式怎么注册（XML 结构） | 解析 formula-functions.xml |
| Q2 | 设计态编译产物 `executableExpr` 是什么 | engine.md + 实测 |
| Q3 | **表达式怎么变成 Java 方法** | ExpressionCodeGenerator 反编译 |
| Q4 | **业务代码怎么主动执行表达式** ★ | 查 formula 运行时包 |
| Q5 | 平台自动执行（preCreateBatch）触发点 | 已部分实测 |
| Q6 | 主动 vs 自动的上下文差异 | 对比 |
| Q7 | `requireNull` 语义与 `copyNeedResetNull` 的关系 | 需两边都反编译，**不得提前断言** |
| Q8 | 表达式异常怎么处理 | 反编译 |
| Q9 | 自定义函数怎么扩展 | ExtensionFunctionInterpreter |
| Q10 | 主子表表达式（聚合字段）怎么算 | resolveAggInfiniteLoop + 实测 |

### 6. 具体研究步骤
```
阶段 1（静态）
  1. 解析 formula-functions.xml → 88 函数注册表
  2. 提取 udc.expression.codegen.* 全包类与方法（已部分完成）
  3. 交叉 engine.md，补全 design-time 链路
  4. 提取 Expression4EntityUtil 8 个方法签名与调用关系
  5. 查 ExpressionVariableTypeEnum 取值

阶段 2（反编译，若可用）
  6. 反编译 ExpressionCodeGenerator#generateCode
  7. 反编译 CodeGenerateResult 的构造来源
  8. 反编译 Expression4EntityUtil#getValueScopeMethodExpression
  9. 反编译 copyNeedResetNull，与 requireNull 对照

阶段 3（实测，需批准）
  10. 建带默认值表达式的字段 → create → 看生成代码里的 exp 方法
  11. 传非空值 → 看是否被覆盖（验证 requireNull）
  12. 主子表聚合字段 → 看表达式怎么算
```

### 7. 预期产物
```
core/facts/platform-dev-system/04-expression-and-runtime.md
  §1 表达式生命周期（定义→注册→解析→编译→执行）
  §2 设计态：表达式定义与校验
  §3 ★ 编译态：ExpressionCodeGenerator 如何产出 Java 方法
  §4 ★ 注入态：Expression4EntityUtil 如何把方法注入实体
  §5 运行时 A：平台自动执行（preCreateBatch）
  §6 运行时 B：业务主动执行（若存在）
  §7 88 函数注册表
  §8 自定义函数扩展
  §9 主子表聚合表达式
  §10 requireNull vs copyNeedResetNull 对照（仅在有证据时下结论）
```

### 8. 验收标准
- [ ] 表达式生命周期五阶段每段有证据
- [ ] 能回答「表达式如何参与实际数据创建和更新」——不是函数清单
- [ ] `exp<雪花ID>` 命名来源有解释
- [ ] `Expression4EntityUtil` 8 个方法逐个说明用途
- [ ] requireNull 与 copyNeedResetNull 的关系：有证据才写结论，否则写「未验证」
- [ ] 主动执行入口：找到就写，找不到标 BLOCKED

### 9. 证据等级
`STATIC_RULE` + `VERIFIED_STATIC_BYTECODE`；运行时行为需 `LIVE_RULE`

### 10. 阻塞与降级方案
| 阻塞 | 降级 |
|---|---|
| runtime 主动执行入口找不到 | 标 BLOCKED，只交付自动执行路径 |
| 无 jar 无法反编译 | 只交付签名级 + 已有 facts |
| 无法实测 | requireNull 语义标 UNVERIFIED |

### 11. 是否需要动态环境
**部分需要。** 阶段 1-2 静态；阶段 3 需批准（审批项 G）。

### 12. 依赖关系
- 依赖：专题 2（代码生成）、专题 3（实体写入）
- 被依赖：专题 7（第三方集成场景）

---

## 六、专题五：接口调用体系

### 1. 研究目标
分清五种调用方式（Dubbo / @Autowired / 泛化 / 微流程 / 第三方），给出决策树。

### 2. 已有证据
| 证据 | 位置 | 等级 |
|---|---|---|
| `DubboFactory` 5 重载 | `core/facts/standard-product/dubbo-cross-service.md` | VERIFIED_STATIC_BYTECODE |
| `AppServiceProxy` 4 方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| AppService 830 类 / 9343 方法 | `svc-app-service.txt.gz` | STATIC_RULE |
| 接口→实现映射 | `surface-index.tar.gz: impl-map.json`（269） | STATIC_RULE |
| 接口→调用者 | `consumers.json`（183） | STATIC_RULE |
| 黑白名单 | `udc-biz-5.3.517/resources/microflow/*.json` | STATIC_RULE |

**已核实入口：**
```
com.seeyon.boot.dubbo.DubboFactory
  # getProxy(Class)
  # getProxy(Class, String group)
  # getProxy(Class, String group, String version)
  # getProxy(Class, String group, String version, int timeout)

AppServiceProxy
  # invokeAppService(...) / invokeAppServiceForList(...)
  # invokeAppServiceForPage(...) / reliableInvokeAppService(...)

AppServiceInvokeDto（18 字段）
GenericInvocationAuthService#invokeAppService(String, String, ...)
```

**黑白名单文件（三分类的直接依据）：**
```
microflow/appServiceMethodBlackList.json              禁止调用
microflow/bootStarterServiceWhiteList.json            允许调用
microflow/bootStarterWhiteList.json
microflow/entityEventWhiteList.json
microflow/otherEntityAppServiceMethodNameList.json
microflow/systemPackageWhiteList.json
microflow/microFlowNameBlackList.json
microflow/deprecatedEntityEventWhiteList.json
microflow/mqMetaDataBlackList.json
```

### 3. 现有资产与文件路径
```
core/facts/standard-product/dubbo-cross-service.md
core/facts/standard-product/appservice-invocation.md
core/facts/standard-product/extension-point-decision-table.md
docs/audit/reference/svc-app-service.txt.gz
surface-index.tar.gz: impl-map.json / consumers.json / domains/*.md
udc-biz-5.3.517/resources/microflow/*.json
```

### 4. 待研究类、方法和资源
| # | 对象 | 待查 |
|---|---|---|
| 1 | 830 个 AppService 按域分类 | domains 11 域 + 包名聚类 |
| 2 | 三分类判定规则 | 黑白名单 + 包路径 + 注解 |
| 3 | `@Autowired` vs `DubboFactory` 判定 | 从 consumers.json 反查真实用法 |
| 4 | `AppServiceInvokeDto` 18 字段 | 泛化调用参数 |
| 5 | 泛化完整链路 | GenericInvocationAuthService → 目标 |
| 6 | 微流程可调服务的约束 | 黑名单具体内容 |
| 7 | 权限机制 | 反编译或配置 |
| 8 | 异常机制 | 反编译 |
| 9 | 事务机制 | 反编译 |

### 5. 待验证问题
| # | 问题 |
|---|---|
| Q1 | 什么时候直接 `@Autowired`，什么时候必须 `DubboFactory.getProxy` |
| Q2 | 泛化调用 vs 直接调用的权限差异 |
| Q3 | 哪些接口禁止微流程调用（黑名单逐条） |
| Q4 | 跨应用调用的租户/权限上下文怎么传 |
| Q5 | 第三方集成（HTTP）该用哪个组件 |

### 6. 具体研究步骤
```
1. 解析 svc-app-service.txt.gz → 830 类按包分组
2. 交叉 domains/*.md → 按业务域归类
3. 解析 9 个黑白名单 → 三分类判定规则
4. 从 consumers.json 提取真实注入方式（@Autowired vs getProxy）
5. 提取 AppServiceInvokeDto 18 字段（签名库）
6. 串泛化调用链路（签名层）
7. 查权限/异常/事务（反编译或配置）
```

### 7. 预期产物
```
core/facts/platform-dev-system/05-api-invocation.md
  §1 AppService 830 类按域清单
  §2 三分类判定规则（公开/内部/扩展）
  §3 五种调用方式决策树
  §4 泛化调用完整链路（含代码）
  §5 黑白名单逐条
  §6 权限/异常/事务
```

### 8. 验收标准
- [ ] 830 类全部有归属域
- [ ] 三分类规则可机械判定（给出判定算法）
- [ ] 决策树覆盖五种方式，每个分支有依据
- [ ] 黑白名单逐条列出，不只写「有黑名单」

### 9. 证据等级
`VERIFIED_STATIC_BYTECODE`

### 10. 阻塞与降级方案
| 阻塞 | 降级 |
|---|---|
| 无方法体 | 权限/异常/事务标 UNVERIFIED |
| domains 覆盖不全 | 只按包名聚类，不强行归域 |

### 11. 是否需要动态环境
**不需要。**

### 12. 依赖关系
- 依赖：专题 3（AppService 生成物）
- 被依赖：专题 7

---

## 七、专题六：基础组件体系

### 1. 研究目标
在已有 2669 类索引基础上，补**使用知识**（不是补类名清单）。

### 2. 已有证据
| 证据 | 位置 | 等级 |
|---|---|---|
| 类索引 | `components/construction/platform_class_index.py`（2669 类 / 26235 方法） | 已建成 |
| 工具类事实 | `core/facts/standard-product/boot-core-utils-and-annotations.md`（176 行） | STATIC_RULE |
| 实测方法数 | 同上（JsonUtils 28 / DateUtils 61 / StringUtils 35） | VERIFIED |

### 3. 现有资产与文件路径
```
core/facts/standard-product/boot-core-utils-and-annotations.md
components/construction/platform_class_index.py
signatures.txt.gz                                   821 个工具类
```

### 4. 待研究类、方法和资源

**每个组件要补 9 项：** 业务用途 / 适用场景 / 调用方式 / 参数返回值 / 使用约束 / 副作用 / 异常处理 / 真实样例 / **不适用场景**

| # | 组件 | 已有 | 要补 |
|---|---|---|---|
| 1 | `JsonUtils`（28） | 签名 | `toMap` vs `toMapThrowError`；与 `license.JsonUtils` 同名坑 |
| 2 | `JsonNodeUtil`（56） | 签名 | 与 JsonUtils 分工 |
| 3 | `DateUtils`（61） | 签名 | 与表达式 `dateToString` 边界 |
| 4 | `DateTransformUtil`（19） | 签名 | 与 DateUtils 分工 |
| 5 | `StorageService` | 三桶 | 附件关联业务实体的正确姿势 |
| 6 | `OrgCommonAppService`（40） | 签名 | 查人的推荐路径 vs 备选 |
| 7 | `BpmAppService`（22） | 签名 | send vs submit vs start |
| 8 | `ExcelTemplateUtil`（70） | 签名 | 与平台导入导出模板关系 |
| 9 | `HttpClientUtil`（93） | 签名 | 微流程无 HTTP 节点时的用法 |
| 10 | `UserCacheUtils`（125）/ `OrgCacheUtils`（47） | 签名 | 缓存失效时机、与 DB 一致性 |
| 11 | 分布式锁 | **未查** | 类名、用法、续约机制 |
| 12 | 文件/附件 | 部分 | 上传、下载、删除、关联 |

### 5. 待验证问题
每类三问：**什么情况该用 / 什么情况不该用 / 有什么坑**。

### 6. 具体研究步骤
```
1. 从 821 个工具类中筛选与 12 个组件相关的类
2. 逐个提取全部方法签名
3. 从 consumers.json 找真实调用点（有则记 LIVE 样例）
4. 已有实测经验（用户复盘文档）直接引用
5. 每个类填满 9 项，缺证据的标 UNVERIFIED
```

### 7. 预期产物
```
core/facts/platform-dev-system/06-base-components.md
  §1 组件分类总览
  §2 每类 9 项完整说明
  §3 同名类冲突清单（JsonUtils 等）
  §4 组件选择决策表
```

### 8. 验收标准
- [ ] 12 个组件每个都有 9 项
- [ ] 「不适用场景」必须写，不能只写优点
- [ ] 真实样例至少 1 个/组件，有来源
- [ ] 同名类冲突单独成节

### 9. 证据等级
`VERIFIED_STATIC_BYTECODE` + 部分 `LIVE_RULE`（有实测样例的）

### 10. 阻塞与降级方案
| 阻塞 | 降级 |
|---|---|
| 无真实调用样例 | 「真实样例」列写「无」，不编造 |
| 无方法体 | 副作用/异常标 UNVERIFIED |

### 11. 是否需要动态环境
**不需要。**

### 12. 依赖关系
- 依赖：无
- 被依赖：专题 7
- **可与专题 5 并行**

---

## 八、专题七：业务能力关联体系

### 1. 研究目标
建立统一知识关系，并做四场景盲测验证。

### 2. 已有证据
```
components/construction/business_code_bridge.py     业务意图 → 域 → 动作 → 方法 → DTO → 实现 → 调用者
components/construction/platform_class_index.py     2669 类中文检索
components/construction/business_action_index.py    业务词 → 标品能力
surface-index.tar.gz: action-index.md               682 条业务动作
```

### 3. 关联模型（每条记录 6 个字段）

```
业务意图
  → 平台能力
  → 接口/类/方法
  → DTO/参数
  → 生成物/DAO
  → 执行流程
  → 副作用
  → 验证案例
```

**每条关系必须记录：**
| 字段 | 取值 |
|---|---|
| 来源 | 文件路径 + 行号 / 签名库行 / 实测响应 |
| 版本 | udc-platform-5.3.517 等 |
| 证据等级 | STATIC_RULE / VERIFIED_STATIC_BYTECODE / LIVE_RULE / UNVERIFIED |
| 适用范围 | 哪些实体类型 / 哪些场景可用 |
| 验证状态 | 已验证 / 部分验证 / 未验证 |
| 置信度 | 高 / 中 / 低（附理由） |

### 4. 检索评估集设计

**必须覆盖四类样本：**

| 类型 | 说明 | 示例 |
|---|---|---|
| 正例 | 直接命中 | 「查组织人员」→ `OrgCommonAppService` |
| 近义表达 | 同义不同词 | 「找人」/「按部门查用户」/「取人员列表」 |
| 负例 | 不应命中 | 「下载附件」**不应**命中 `deleteById` |
| 歧义 | 多解需澄清 | 「删除」→ 逻辑删除 or 物理删除？ |

**评估指标：**
```
Top-1 准确率
Top-5 准确率
召回率
错误类型统计（按类别归因）
```

**★ 已发生错误必须进回归集：**
```
错误案例：检索「下载」命中「删除」方法
根因（待确认）：字符相似 / 分词问题 / 索引未区分动词
回归要求：该 query 必须 Top-1 命中下载类方法，且 Top-5 不含 delete*
```

### 5. 待验证问题
| # | 问题 |
|---|---|
| Q1 | 业务意图 → 平台能力的映射准确率能到多少 |
| Q2 | 近义表达召回率如何 |
| Q3 | 负例（不该命中）能否挡住 |
| Q4 | 歧义 query 能否主动澄清而不是乱猜 |

### 6. 具体研究步骤
```
1. 从 action-index.md（682 条）抽取映射基础
2. 与专题 1-6 的产物对齐，补全能力侧
3. 设计评估集（正例/近义/负例/歧义，各 ≥20 条）
4. 跑基线，记录 Top-1 / Top-5 / 召回率
5. 归因错误类型
6. 加入已知错误回归用例（下载/删除）
7. 四场景盲测
```

### 7. 四场景盲测设计（严格规则）

| # | 场景 | 业务需求（只给这个） | 覆盖专题 |
|---|---|---|---|
| 1 | 普通实体 CRUD | 「建一个供应商档案，支持增删改查」 | 1、2、3 |
| 2 | 主子表 CRUD | 「做订单 + 订单明细，能一起保存」 | 1、2、3 |
| 3 | 单据保存提交流转 | 「做采购申请单，能提交审批」 | 1、2、3、4 |
| 4 | 第三方接口集成 | 「调外部 ERP 接口，数据落到本平台实体」 | 3、4、5、6 |

**盲测硬规则：**
```
① 只给业务需求，不给类名/方法名/接口名
② Agent 必须自己检索找能力
③ 每个方案必须带证据（文件路径/签名行/实测）
④ 找不到标 BLOCKED，不许编
⑤ 记录 Agent 的检索路径（证明是"找到"不是"猜到"）
```

### 8. 预期产物
```
core/facts/platform-dev-system/07-business-capability-map.md
  §1 业务意图 → 能力映射总表（含 6 字段）
  §2 检索评估集（正例/近义/负例/歧义）
  §3 评估结果（Top-1/Top-5/召回率/错误类型）
  §4 已知错误回归集（含下载/删除案例）
  §5 四场景盲测报告
  §6 未解决问题
```

### 9. 验收标准
- [ ] 映射表每条都有 6 字段，无空值
- [ ] 评估集四类各 ≥20 条
- [ ] Top-1/Top-5/召回率有实测数字
- [ ] 「下载命中删除」必须出现在回归集且已修复
- [ ] 四场景盲测每场景有完整检索路径记录
- [ ] 盲测方案中**不得出现**未在产物中定义的方法名

### 10. 证据等级
`LIVE_RULE`（评估集实测）+ `STATIC_RULE`（映射基础）

### 11. 阻塞与降级方案
| 阻塞 | 降级 |
|---|---|
| 前 6 专题未完成 | 盲测推迟，先交付评估集设计 |
| 评估集样本不足 | 说明样本量，不算通过 |

### 12. 依赖关系
- 依赖：专题 1-6 全部
- 被依赖：无（收口）

---

## 九、动态环境审批清单（逐项独立批准）

**⚠️ 以下每一项都是独立审批项。批准 A 不等于批准 B。**
**当前状态：全部未批准。本轮不执行任何写操作。**

---

### 审批项 A：创建测试应用

| 项 | 内容 |
|---|---|
| 写入范围 | test2 平台元数据库（应用表 + 关联配置） |
| 影响对象 | 新增 1 个应用记录，不触碰现有应用 |
| 风险 | 低。应用是逻辑隔离单元，不产生物理表 |
| 前置备份 | 导出当前应用列表（appId + 名称）快照 |
| 回滚方法 | 删除该应用记录 |
| 清理验证 | 应用列表与快照逐条比对，数量与内容一致 |
| 批准状态 | ☐ 未批准 |

---

### 审批项 B：生成代码

| 项 | 内容 |
|---|---|
| 写入范围 | 代码生成工作目录（文件系统）+ 可能的 schema 表 |
| 影响对象 | 生成物文件（entity/dto/appservice/impl/service/dao/xml/controller） |
| 风险 | 中。若误操作现有应用，可能覆盖手写代码（`gg_isOverride=true`） |
| 前置备份 | ① 确认目标 appId 是测试应用 ② 导出该应用现有 schema |
| 回滚方法 | 删除生成的产物目录；若覆盖了手写代码，从备份恢复 |
| 清理验证 | 产物目录不存在 / 文件数与预期一致 |
| 批准状态 | ☐ 未批准 |

---

### 审批项 C：创建普通实体

| 项 | 内容 |
|---|---|
| 写入范围 | 元数据库（udc_entity / udc_attribute）+ 生成后可能建物理表 |
| 影响对象 | 新增 1-2 个实体定义 |
| 风险 | 低-中。若触发建表，会新增物理表 |
| 前置备份 | 实体清单快照 + 表清单快照 |
| 回滚方法 | 删除实体定义；若已建表，DROP 该表 |
| 清理验证 | 实体数 / 表数与快照一致 |
| 批准状态 | ☐ 未批准 |

---

### 审批项 D：创建 Bill 实体

| 项 | 内容 |
|---|---|
| 写入范围 | 元数据库 + 可能触发 BPM 流程定义 |
| 影响对象 | 新增 1 个 bill 实体 + 可能的流程模板 |
| 风险 | **中-高**。bill 带 approve 特性，可能生成流程实例 |
| 前置备份 | 实体清单 + 流程定义清单 + 表清单 |
| 回滚方法 | 删除实体 + 删除关联流程定义 |
| 清理验证 | 三份清单全部回到快照 |
| 特别约束 | **不指定真实审批人，不发起真实审批** |
| 批准状态 | ☐ 未批准 |

---

### 审批项 E：执行持久化验证

| 项 | 内容 |
|---|---|
| 写入范围 | 测试实体对应的业务表（数据行） |
| 影响对象 | 新增/修改/删除测试数据行 |
| 风险 | 中。若表名搞错，可能污染真实业务表 |
| 前置备份 | ① 目标表结构 ② 现有行数 ③ 目标表名白名单（只允许 ZZRESEARCH_ 前缀表） |
| 回滚方法 | 按主键删除测试行；或从备份恢复 |
| 清理验证 | 行数与快照一致 |
| 特别约束 | 单表 ≤100 行，主子表各 ≤50 行 |
| 批准状态 | ☐ 未批准 |

---

### 审批项 F：批量数据测试

| 项 | 内容 |
|---|---|
| 写入范围 | 测试表 |
| 影响对象 | 批量插入数据行 |
| 风险 | 中。可能触发表锁、慢查询 |
| 前置备份 | 同 E |
| 回滚方法 | 按批次标识删除 |
| 清理验证 | 行数归零 |
| 特别约束 | **上限 1000 条**，分批插入（每批 ≤100） |
| 批准状态 | ☐ 未批准 |

---

### 审批项 G：表达式实测

| 项 | 内容 |
|---|---|
| 写入范围 | 测试实体的字段定义（默认值表达式）+ 测试数据 |
| 影响对象 | 字段配置 + 数据行 |
| 风险 | 低 |
| 前置备份 | 字段定义快照 |
| 回滚方法 | 删除表达式配置 |
| 清理验证 | 字段定义回到快照 |
| 批准状态 | ☐ 未批准 |

---

### 审批项 H：清理测试数据

| 项 | 内容 |
|---|---|
| 写入范围 | 删除测试应用/实体/表/数据 |
| 影响对象 | 所有测试期间产生的对象 |
| 风险 | **中-高**。误删会不可恢复 |
| 前置备份 | 清理前再导出一次全量清单 |
| 回滚方法 | 无（删除不可逆），因此清理前必须二次确认目标 |
| 清理验证 | ① 应用数 ② 实体数 ③ 表数 ④ 各表行数 四项全部回到测试前快照 |
| 特别约束 | **先列清单给人确认，再执行删除** |
| 批准状态 | ☐ 未批准 |

---

## 十、实施顺序与依赖图

### 10.1 依赖关系图

```
                    ┌──────────────────┐
                    │ 专题1 元数据体系  │  纯静态
                    └────────┬─────────┘
                             │ 元数据输入
                    ┌────────▼─────────┐
                    │ 专题2 代码生成    │  静态 + 需1次生成实测
                    └────────┬─────────┘
                             │ 生成产物
                    ┌────────▼─────────┐
                    │ 专题3 持久化      │  静态 + 必须实测
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───────┐ ┌────▼─────────┐ ┌─▼──────────────┐
     │ 专题4 表达式    │ │ 专题5 接口    │ │ 专题6 组件     │
     └────────┬───────┘ └────┬─────────┘ └─┬──────────────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼─────────┐
                    │ 专题7 业务关联    │  收口 + 盲测
                    └──────────────────┘
```

### 10.2 分阶段实施

```
阶段 1：元数据与生成器（专题 1 → 专题 2 阶段 1-2）
  纯静态，零阻塞，不需要任何批准
  产出：元数据全景 + 生成器候选映射表

阶段 2：持久化与表达式（专题 3 阶段 1、专题 4 阶段 1-2）
  纯静态，零阻塞
  产出：DAO 场景表 + 表达式编译链路

阶段 3：接口与组件（专题 5、专题 6）
  纯静态，可与阶段 2 并行
  产出：接口分类 + 组件使用知识

阶段 4：动态验证（专题 2 阶段 3、专题 3 阶段 3、专题 4 阶段 3）
  ⚠️ 需逐项批准（§九 A-H）
  产出：实测证据，把 UNVERIFIED 升级为 LIVE_RULE

阶段 5：业务关联与盲测（专题 7）
  产出：映射表 + 评估集 + 四场景盲测报告
```

### 10.3 并行规则
- 阶段 1、2、3 内可自由并行（纯静态，互不阻塞）
- **但必须标明依赖**：专题 2 依赖专题 1 的元数据结论
- 阶段 4 必须在阶段 1-3 完成后（需要静态结论作为实测假设）
- 阶段 5 必须在全部完成后

---

## 十一、现有资产与缺失证据清单

### 11.1 已有资产（可直接用）

| 资产 | 规模 | 路径 |
|---|---|---|
| 类/方法签名 | 245709 行 / 21389 类 / 224320 方法 | `docs/audit/signatures.txt.gz` |
| 表面索引 | 100+ 文件 | `docs/audit/reference/surface-index.tar.gz` |
| 平台资源包 | 404 条目 | `docs/audit/reference/udc-platform-5.3.517.tar.gz` |
| 模板清单 | 464 条 / 41 组 / 4 版本 | 上述包内 `_codegen_templates.json` |
| AppService 清单 | 830 类 / 9343 方法 | `docs/audit/reference/svc-app-service.txt.gz` |
| 反编译源码 | 212 .java | `docs/audit/modules/decompiled/` |
| 现有 facts | 228 md + 107 json | `core/facts/` |
| 类索引 | 2669 类 / 26235 方法 | `components/construction/platform_class_index.py` |

### 11.2 缺失证据（必须标 BLOCKED 或降级）

| 缺失项 | 影响专题 | 降级方案 | 能否补 |
|---|---|---|---|
| 平台 jar 本体 | 2、3、4、5 | 实测产物反推 | 需你提供路径 |
| .ftl 模板内容 | 2、4 | 只做清单级 | 需 jar |
| CFR 反编译工具 | 2、3、4 | 只做签名级 | 可安装（需批准） |
| Template 方法体 | 2 | 只做签名级 | 需 jar |
| 生成产物样本 | 2、3 | 无替代 | 需生成（审批 B） |
| 主子表写入行为 | 3 | 标 UNVERIFIED | 需实测（审批 E） |
| 单据流转行为 | 3 | 标 UNVERIFIED | 需实测（审批 D/E） |
| 主键生成机制 | 3 | 标 UNVERIFIED | 需实测（审批 E） |
| runtime 主动执行表达式入口 | 4 | 标 BLOCKED | 需查 jar |
| 平台内部架构文档 | 全部 | 五方向只作组织模型 | 无 |

---

## 十二、需要你审计确认的事项

**A. 五方向 + 七专题的组织模型**：是否认可「五方向是研究组织模型，不是平台真实架构」这个定性？

**B. 统计口径**（§0.1）：53 个 CodeTask / 36 个 Template / 464 条模板 / 830 个 AppService / 41+55 DAO 方法，这些数字和口径是否认可？如与你掌握的不一致，以哪个为准？

**C. `copyNeedResetNull` 的定性**：v4 改为「零调用者，不得认定为根因，需四条验证」，是否认可？

**D. 专题二降级路线**：.ftl 和 jar 都没有时，只交付「模板清单 + 签名 + 实测产物」三层，是否可接受？

**E. 动态环境审批**：§九 A-H 共 8 个独立审批项，格式是否满足要求？需要你逐项勾选。

**F. 盲测四场景**：普通实体 CRUD / 主子表 CRUD / 单据保存提交流转 / 第三方接口集成，是否就这四个？

**G. 检索评估集**：正例/近义/负例/歧义各 ≥20 条，Top-1/Top-5/召回率 + 错误类型统计，「下载命中删除」进回归集，是否满足？

**H. 产物落点**：`core/facts/platform-dev-system/01-07-*.md` 独立目录，不覆盖现有 `standard-product/`，是否可以？

**I. 实施顺序**：阶段 1-5 的划分与并行规则是否认可？

---

## 十三、本阶段禁止事项（对齐你的约束）

- ❌ 修改业务代码
- ❌ 修改 MCP 工具
- ❌ 修改现有 facts
- ❌ 执行 test2 写操作
- ❌ 创建测试应用或实体
- ❌ 触发代码生成
- ❌ 清理数据库
- ❌ 把未验证推断写成平台事实
- ❌ 把类索引当使用知识
- ❌ 把方法签名当运行行为
- ❌ 把模板清单当模板选择机制
- ❌ 宣称 CodeTask 与 Template 一一对应
- ❌ 把五方向说成平台真实架构
