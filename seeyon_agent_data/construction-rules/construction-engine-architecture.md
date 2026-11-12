# Construction Engine Architecture Review

更新时间：2026-09-04

## 1. Review scope

本轮纠偏：Construction Engine 的目标不是仿照 UDC 生成 Java 源码，而是理解并操作 UDC 这类低代码平台。Agent 应以用户身份，经由前端用户路径或后端接口提交需求，由 UDC 平台自身负责实体/页面/微流程等产物生成。源码生成实验已移出活动实现范围。

本次评审不继续扩大 Attribute 样本，不重新调查 P0-3B Resolver，也不实现平台源码 Generator。

实际检查目录：

```text
<SEEYON_AGENT_ROOT>/
  docs/construction-rules/
  docs/audit/
  components/
  core/
  providers/
  tests/
  seeyon_cli.py
```

## 2. 当前真实架构

当前项目不是 Generator 工程，而是一个离线、只读、证据审计与组件路由骨架。

```text
CLI: seeyon_cli.py
    ↓
SeeyonAgent / AgentRequest
    ↓
ComponentRegistry
    ↓
UdcComponent
    ├── UdcEvidenceCatalog
    ├── UdcAnalyzer
    ├── UdcPlanner
    └── UDC models: ApplicationSpec / EntitySpec / FieldSpec

Evidence / Reports
    ├── JSON audit fixtures and audit documents
    ├── report_schema.py
    └── artifact_inventory.py
```

已经存在的具体代码入口：

```text
components/udc/models.py
  FieldSpec
  EntitySpec
  ApplicationSpec
  PageSpec
  MicroFlowSpec

components/udc/planner.py
  UdcPlanner.plan()
  UdcPlanner.plan_application()

components/udc/catalog.py
  UdcEvidenceCatalog

components/udc/analyzers.py
  UdcAnalyzer

components/udc/component.py
  UdcComponent
  UdcRequest

core/registry.py
  ComponentRegistry

core/agent.py
  AgentRequest
  SeeyonAgent.route()
  SeeyonAgent.dispatch()

components/artifact_inventory.py
  scan_repository()
  write_manifest()
```

当前不存在可执行的：

```text
RuleLoader
RuleRegistry（Construction Rules 专用）
NormalizedEntityModel
ConstructionResult
ArtifactPlan
SourceCodeGenerator
TemplateEngine
CompilerAdapter
GoldenDiff Engine
Construction Validation Pipeline
```

`core.registry.ComponentRegistry` 是通用 Agent 组件注册/路由，不应直接承担 Construction Rule Registry 的职责。

## 3. 当前规则层真实状态

机器规则已存在，但仍是证据投影文件，不是运行时可执行规则对象：

```text
docs/construction-rules/entity/naming.json
docs/construction-rules/entity/package.json
docs/construction-rules/entity/attribute-propagation-cross-sample.json
docs/construction-rules/entity/attribute-java-type-rule.json
docs/construction-rules/entity/entity-relation-rule.json
docs/construction-rules/entity/entity-child-rule.json
docs/construction-rules/entity/entity-index-rule.json
docs/construction-rules/entity/entity-rule-flag-mapping.json
docs/construction-rules/generation/facade.json
docs/construction-rules/generation/biz.json
docs/construction-rules/generation/web.json
docs/construction-rules/entity-generation-contract.json
docs/construction-rules/confidence.json
docs/construction-rules/index.json
```

这些 JSON 的主要作用目前是：

```text
记录观察到的输出结构
记录证据等级与限制
保存审计统计
支持人工/脚本复核
```

不能直接视为：

```text
可执行的输入校验器
可执行的命名器
可执行的 Artifact Plan builder
Generator implementation
```

## 4. 推荐架构（操作型 Construction Engine）

推荐先做一个小型、确定性的 Construction Engine，不将审计 JSON 直接散落在各个生成函数中。

```text
                         AI Agent / CLI / Future UDC Adapter
                                      │
                                      ▼
                              Construction Task
                                      │
                                      ▼
                         NormalizedEntityModel (IR)
                                      │
                                      ▼
                            ConstructionRuleRegistry
                                      │
             ┌────────────────────────┼────────────────────────┐
             ▼                        ▼                        ▼
       NamingEvaluator          PackageEvaluator         OutputContractEvaluator
             │                        │                        │
             └────────────────────────┼────────────────────────┘
                                      ▼
                             OperationPlan
                                      │
                                      ▼
                         Source Generator / Templates
                                      │
                                      ▼
                              Generated Source
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                     ▼
             CompilerAdapter                         GoldenDiff
                   │                                     │
                   └──────────────────┬──────────────────┘
                                      ▼
                               ValidationReport
```

当前正确的第一阶段是：

```text
ConstructionTask
    → input normalization
    → operation planning
    → platform API invocation
    → readback verification
    → OperationResult
```

UDC 平台负责低代码产物生成；本项目不复制其源码 Generator。

## 5. Normalized Construction Intent 是否必要

结论：必要，但它描述的是“用户想让平台完成什么”，不是待生成 Java 源码的 IR。不要复制完整 `EntityDto`。

理由：

```text
1. 当前 EntitySpec 只有 name + fields，无法表达 EntityDto 的 parent/children/indexes/events/features。
2. 规则 JSON 的字段命名来自不同证据层，不能让每个 Rule 直接读取原始 GraphQL/EntityDto 形态。
3. 未来 GraphQL、文件、CLI、LLM 都应成为输入适配器，核心 Rule Engine 不应感知输入来源。
4. Artifact Plan 需要稳定的 application/entity/attribute 语义，而不是自由形态 dict。
5. UNKNOWN 字段必须能够保留，不能在归一化时静默丢失。
```

推荐最小 IR：

```text
NormalizedConstructionIntent
├── application
│   ├── id: str
│   ├── package_root: str | UNKNOWN
│   └── display_name: str | UNKNOWN
├── entity
│   ├── name: str
│   ├── caption: str | UNKNOWN
│   ├── description: str | UNKNOWN
│   ├── features: dict
│   └── source_ref: EvidenceRef | UNKNOWN
├── attributes[]
│   ├── name: str
│   ├── type: normalized type token | UNKNOWN
│   ├── caption: str | UNKNOWN
│   ├── required: bool | UNKNOWN
│   ├── default_value: Any | UNKNOWN
│   ├── relation: RelationSpec | UNKNOWN
│   ├── nested: bool | UNKNOWN
│   └── source_ref: EvidenceRef | UNKNOWN
├── children[]: NormalizedEntityModel | reference
├── indexes[]: IndexSpec | UNKNOWN
├── events[]: EventSpec | UNKNOWN
├── rule_flags: dict[str, bool | UNKNOWN]
└── evidence[]: EvidenceRef
```

操作型 MVP 实际只消费：

```text
application.id
application.package_root（若缺失则报告 UNKNOWN，不猜）
entity.name
attributes[].name
attributes[].type（仅用于保留和验证，不生成类型映射）
```

parent、children、relations、indexes、events、flags 先保留结构，但默认不进入第一版 Artifact Plan。

## 6. Rule Registry 是否必要

结论：需要，但它应是 Platform Capability / Operation Registry，不是源码生成规则注册表。

建议职责：

```text
ConstructionRuleRegistry
├── load declarative JSON rules
├── validate rule schema/version/status
├── resolve rule by ruleId
├── expose evidence and limitations
└── dispatch executable evaluators only for supported rules
```

建议分类：

```text
Declarative platform contracts:
  package templates
  output artifact templates
  required/optional artifact declarations

Executable operation logic:
  Java identifier validation
  entity stem validation
  deterministic artifact naming
  package rendering
  duplicate artifact detection
  unknown/blocked rule gate

Constraint-only rules:
  relation metadata
  child metadata
  indexes
  rule flags
  @DtoAttribute mapping
```

当前不应进入可执行生成器的内容：

```text
Generation causality UNKNOWN
UDC datatype → Java type 的未验证输入映射
AttributeDto → @DtoAttribute 的因果映射
Relation → associated Entity/AppService 的推断
Index → DDL 的推断
Rule flag → generated method/class 的推断
```

`core.registry.ComponentRegistry` 保持 Agent 组件路由；Construction Registry 应位于未来的 `components/construction/` 或独立 construction package，避免职责污染。

## 7. Operation Plan 是否必要

结论：需要，但对象应改为 OperationPlan；不是源码 ArtifactPlan。

Rule Engine 负责：

```text
输入模型
    → 规则评估
    → 生成哪些 artifact
    → artifact 的 module/type/package/className
    → required/optional
    → evidence/confidence/unknown blockers
```

Platform Operation Adapter 负责：

```text
ArtifactPlan
    → 选择 template
    → 渲染源代码
    → 写入明确输出目录
```

推荐最小对象：

```text
OperationPlan
├── schema
├── application_id
├── entity_name
├── artifacts[]
│   ├── module
│   ├── type
│   ├── package
│   ├── class_name
│   ├── relative_path
│   ├── required
│   ├── rule_id
│   └── confidence
├── unknown[]
├── blocked[]
├── warnings[]
└── evidence[]
```

第一版只计划：

```text
facade / dto / XDto
facade / appservice / XAppService
biz / entity / X
biz / service / XService
biz / appservice / XAppServiceImpl
biz / dao / <ApplicationStem>XDao
web / abstract_controller / AbstractXController
web / controller / XController
```

`ArtifactPlan` 不是源代码，不应包含模板渲染细节。

## 8. Golden Diff 的架构位置

当前 Golden Diff 是静态 JSON 结果：

```text
docs/construction-rules/synthetic-entity-golden-diff.json
docs/construction-rules/entity/synthetic-attribute-golden-diff.json
```

它们目前更接近：

```text
offline audit validation artifact
```

推荐演进为：

```text
Construction Engine
    ├── plan(intent)
    ├── execute(operation_plan)
    └── validate(expected_state, observed_state)
                              │
                              ▼
                         GoldenDiffResult
```

当前最小演进不是实现完整源码 diff，而是先把既有 synthetic diff 的语义抽象为：

```text
planned operations
observed platform state
missing
unexpected
ambiguous
status
```

这样未来可以复用同一验证接口，而不是继续生成一次性审计 JSON。

## 9. P0-3B 的正确位置

`P0-3B GraphQL Resolver` 不属于核心 Construction Rule Engine。

它应属于：

```text
UDC Integration Adapter / Input Adapter
```

未来结构：

```text
UDC Frontend
    ↓
UDC Frontend / GraphQL Adapter
    ↓
Raw payload / user operation
    ↓
Input Normalizer
    ↓
NormalizedConstructionIntent
    ↓
UDC Operation Engine
```

这样恢复 P0-3B 时，只需补：

```text
udcEntityPost → GraphQL schema/resolver → raw input adapter
```

核心规则引擎不需要知道：

```text
GraphQL field name
Resolver class
HTTP endpoint
UDC frontend loader
```

这可以避免设计态集成缺口污染核心生成规则。

## 10. AI Agent 的正确位置

AI Agent 位于 Operation Engine 之上，不应绕过平台接口自己生成平台源码。

```text
AI Agent
    ↓
ConstructionTask
    ↓
NormalizedConstructionIntent
    ↓
UDC / Platform Operation Engine
    ↓
OperationPlan
    ↓
Platform Adapter / Readback Validator
```

LLM 负责：

```text
需求理解
实体边界识别
字段/关系建模
缺失信息识别
构造任务规划
规则解释
```

Construction Engine 负责：

```text
确定性命名
确定性 package
Artifact Plan
规则约束
模板选择
生成结构
Golden Diff
Validation
```

LLM 不负责：

```text
Java class naming
DAO naming
AppService naming
package naming
required artifact decision
```

## 11. Current → Missing → Next

### Current

```text
已有：
- EntitySpec / FieldSpec 最小模型
- UdcPlanner 只读 dry-run 计划器
- ComponentRegistry（通用 Agent 组件 registry）
- 15 个 Construction Rules JSON/index 文件
- Golden Sample 与跨样本统计
- synthetic Golden Diff JSON
- audit/report schema 与离线测试
```

### Missing

```text
- NormalizedEntityModel / IR
- ConstructionRuleRegistry
- Rule schema loader/validator
- executable naming/package evaluators
- OperationPlan
- plan validation
- source generator port
- compiler adapter port
- reusable GoldenDiffResult
- construction-specific tests
- Agent → ConstructionTask adapter
```

### Next

```text
1. 在 components/construction/ 增加最小 IR dataclasses。
2. 增加 ConstructionRuleRegistry，只加载 naming/package/generation contract。
3. 增加 deterministic RuleEvaluator，先输出命名和 package。
4. 增加 OperationPlan，不写源码。
5. 用 synthetic entity 运行 plan，并与 Golden Sample artifact names 做 diff。
6. 之后再增加 Source Generator；不提前实现 Compiler/GraphQL/Agent。
```

## 12. Construction Operation Engine MVP boundary

MVP 输入：

```text
NormalizedEntityModel
```

MVP 输出：

```text
OperationPlan
```

MVP 支持：

```text
一个真实 UDC 用户操作：创建或修改 Entity
请求 payload 规划
平台接口调用边界
结果 readback
操作证据记录
```

MVP 不支持：

```text
GraphQL
Relation Runtime
Child Runtime
Index DDL
Rule Flag Generator
Source compilation
Deployment
AI Agent
Generation causality
```

MVP 的成功标准：

```text
虚拟 Entity 输入
    → 生成稳定 ArtifactPlan
    → 命名/package 与规则 JSON 一致
    → 与 Golden Sample 核心 artifact 集合可做无歧义 diff
    → UNKNOWN / BLOCKED 不被静默吞掉
    → 不执行外部写操作
```

## 13. Concrete file-level recommendation

已有文件继续保留：

```text
components/udc/models.py
  继续兼容既有 EntitySpec/FieldSpec；不要立即破坏旧测试。

components/udc/planner.py
  保持 UDC read-only inspection planner；不要把 Construction Engine 塞进 UdcPlanner。

core/registry.py
  保持通用 ComponentRegistry；不要改造成 ConstructionRuleRegistry。
```

建议新增但本轮不实现的最小包：

```text
components/construction/
  __init__.py
  models.py          # NormalizedEntityModel / OperationPlan
  rules.py           # rule loading + registry
  evaluator.py       # deterministic naming/package/plan evaluation
  validation.py      # plan validation + GoldenDiffResult port
```

未来 UDC Adapter 位置：

```text
components/udc/adapters/construction_input.py
```

未来 AI Adapter 位置：

```text
components/construction/agent_adapter.py
```

本轮不创建这些代码文件，避免在架构边界尚未经过 MVP 验证前扩大实现面。

## 14. Architecture verdict

```text
NormalizedEntityModel = REQUIRED
ConstructionRuleRegistry = REQUIRED, lightweight
OperationPlan = REQUIRED
Source Generator = next after plan MVP, not yet present
Compiler Adapter = extension point, not MVP
Golden Diff = evolve from static JSON to reusable validation result
P0-3B GraphQL = UDC Input Adapter, outside core engine
AI Agent = orchestration/modeling layer above engine
```

当前项目最合理的下一步不是继续审计，也不是直接写 Generator，而是实现：

```text
NormalizedEntityModel
    → ConstructionRuleRegistry
    → OperationPlan
```


## 15. 方向纠偏：不是仿造 UDC，而是使用 UDC

本项目的目标应明确为：

```text
用户需求
    ↓
AI 理解用户意图
    ↓
模拟用户选择页面/调用后端接口
    ↓
UDC 低代码平台执行实体、页面、微流程等生成
    ↓
Agent 读取平台返回和页面状态
    ↓
验证需求是否完成
```

因此：

```text
UDC = 被操作的平台
Construction Operation Engine = 平台操作与验证层
AI Agent = 用户意图理解与操作编排层
``

SPI 不套用这条链。SPI 是扩展机制，核心是：

```text
SPI Contract
    ↓
Extension Point
    ↓
Plugin Implementation
    ↓
Registration / Loading
    ↓
Invocation / Verification
```

## 16. Current → Missing → Next（纠偏后）

### Current

```text
已有：
- UDC 前端调用证据
- Entity/Attribute/页面/微流程审计证据
- 部分 DTO/后端接口契约
- UDC Runtime CRUD 边界
- 规则与 Golden Sample（作为平台行为知识，不作为源码模板）
- 只读 Agent/UDC 组件骨架
```

### Missing

```text
- ConstructionTask / NormalizedConstructionIntent
- UDC Input Adapter
- UDC Operation Registry
- Payload Builder
- Browser/API Operation Executor
- Readback Verifier
- Operation Evidence / Result
- 用户操作安全闸门与确认机制
```

### Next

```text
1. 停止并隔离 source-generator 实验。
2. 建立一个真实 UDC Entity 操作的 Input/Operation contract。
3. 将前端 createEntity 证据转换为用户操作模型。
4. 在明确授权和可回读的前提下，实现最小真实操作闭环。
5. 将 Page、MicroFlow、BPM、Connector 分别接入各自 Adapter。
6. SPI 单独建立 Extension Contract Engine。
```


## 15. 方向纠偏：目标是使用 UDC，不是仿造 UDC

本项目的 Construction Engine 不是 Java Source Generator。UDC 本身就是低代码生成平台，平台负责实体、页面、微流程等产物生成；Agent 的职责是理解需求并像用户一样，通过前端操作或后端接口调用平台。

```text
用户需求
    ↓
AI Agent 理解意图
    ↓
ConstructionTask / NormalizedConstructionIntent
    ↓
UDC Frontend Adapter 或 UDC API Adapter
    ↓
平台执行低代码操作
    ↓
页面状态 / API 返回 / 资源状态 readback
    ↓
OperationResult
```

因此已有 `GeneratedArtifactPlan` 和 Source Generator 实验不再是主线，应视为已隔离的错误方向，不继续扩展。

### UDC、BPM、Connector 等模块

这些模块原则相同：

```text
Agent 作为用户
    ↓
理解模块操作语义
    ↓
选择前端用户路径或后端接口
    ↓
提交真实操作
    ↓
读取结果并验证
```

### SPI 是例外

SPI 不是低代码用户操作入口，而是扩展契约：

```text
SPI Contract
    ↓
Extension Point
    ↓
Plugin Implementation
    ↓
Registration / Loading
    ↓
Invocation / Verification
```

SPI 必须单独建模，不能套用 UDC 的用户操作链。

## 16. 纠偏后的 Current → Missing → Next

### Current

```text
已有：
- UDC 前端 createEntity 等操作证据
- 部分后端接口/DTO/Runtime CRUD 契约
- Entity、Page、MicroFlow 等平台对象审计证据
- Construction Rules 作为平台行为知识
- Agent/UDC 只读组件骨架
```

### Missing

```text
- ConstructionTask / NormalizedConstructionIntent
- UDC Input Adapter
- UDC Operation Registry
- 前端操作与后端 API 的统一能力描述
- Payload Builder
- Browser/API Operation Executor
- Readback Verifier
- Operation Evidence / OperationResult
- 写操作授权、确认、幂等与回读边界
```

### Next

```text
1. 不再扩展 Source Generator；保留为 deferred。
2. 建立 UDC 用户操作模型，而不是源码生成模型。
3. 用已确认的前端/接口证据实现一个最小 Entity 操作闭环。
4. 先支持 dry-run 和 readback，再在明确授权后执行真实写操作。
5. Page、MicroFlow、BPM、Connector 分别接入各自 Operation Adapter。
6. SPI 单独建设 Extension Contract Engine。
```
