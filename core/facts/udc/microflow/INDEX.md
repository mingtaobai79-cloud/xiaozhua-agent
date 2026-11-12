# 微流程知识地图（INDEX）

> 本目录顶层 62 个 .md（当前工作树统计），按主题分层。找东西先看这里，别平铺 grep。
> 领域总览与三套域模型：`README.md`。

## 1. 接口契约（怎么调平台接口）

| 文件 | 内容 |
|---|---|
| `api-catalog.md` | ★ 微流程接口总清单（udc GraphQL，建单/发布/检查/查询全在这） |
| `api-map.md` | 节点 → 接口 → 数据 映射（抓取记录） |
| `graphql-op-naming.md` | GraphQL op 名与类型名的生成规则 |
| `read-api.md` | 接口读取（不靠数据库） |
| `custom-service-api.md` | 自定义服务节点接口链路（用户贴 body） |
| `custom-service-candidates.md` | 自定义服务：可选应用与可调接口来源 |
| `dataflow-api.md` | 执行生单规则节点接口链路 |

## 2. 节点契约（每个节点怎么构造/验证）

| 文件 | 内容 |
|---|---|
| `node-catalog.md` | 画布节点定义清单（前端 bundle 提取） |
| `node-authoring-contract.md` | 节点正确生成契约（前端驱动，不拼 JSON） |
| `node-contract-vs-template.md` | 真实保存态 vs 前端新建态 |
| `node-field-shape-contract.md` | 节点字段形态契约（LIVE） |
| `node-modal-and-value-editor.md` | 节点弹窗 + 值编辑器 + 表达式编辑器（用户逐节点口述，权威） |
| `node-ui-contracts-22.md` | 22 类节点 UI 实测契约 |
| `node-variants.md` | 节点子模式切换动态验证 |
| `node-data-flow.md` | 节点关联模型：谁能产出/消费数据 |
| `node-insert-entity.md` | 数据活动 vs 自定义服务（活体验证） |
| `all-nodes-coverage.md` | 20 种节点类型全覆盖实测 |
| `three-nodes-live-evidence.md` | 三个节点真机实证（643 条 RELEASE） |
| `drawer-locator-rootcause.md` | Drawer Locator 根因 + CREATE_ENTITY 规范化 |
| **单节点运行时契约** | |
| `node-retrieve-array.md` | RETRIEVE_ARRAY（查询多条，fetchType×出参） |
| `node-batch-entity.md` | CREATE_BATCH / CHANGE_BATCH（批量写） |
| `node-change-delete-entity.md` | CHANGE_ENTITY / DELETE_ENTITY |
| `node-change-list.md` | CHANGE_LIST（修改列表四动作） |
| `node-list-operation.md` | LIST_OPERATION（14 种操作） |
| `node-sub-microflow.md` | SUB_MICROFLOW（调用子流程） |
| `node-call-app-service.md` | CALL_APP_SERVICE（自定义服务） |
| `node-publish-event.md` | PUBLISH_BUSINESS_EVENT（事件投递） |
| `node-break.md` | BREAK（跳出循环） |
| `node-id-stability.md` | 重发幂等（id 由别名派生） |

## 3. 表达式（表达式引擎）

| 文件 | 内容 |
|---|---|
| `expression-engine.md` | 表达式中间模型与传输链（P2） |
| `expression-layer-contract.md` | 三层不一致与保存链路 |
| `expression-fill-all-nodes.md` | 全节点表达式填充方法 |
| `expression-basic-scalar-context-gap.md` | BASIC 标量变量 context 注册（已修） |
| `value-literal-contexts.md` | 常量字面量两个语境不能混 |
| `ref-and-condition-contract.md` | 变量引用/查询条件真实结构 |
| `PROMPT-MICROFLOW-EXPRESSION-FACTS.md` | 表达式权威事实提示词（FACTS ONLY） |

## 4. 触发器与状态（MANUAL/SCHEDULE/BUSINESS_EVENT）

| 文件 | 内容 |
|---|---|
| `trigger-and-type-mapping.md` | 类型×触发方式字段映射（反编译证实） |
| `event-listener-structure.md` | 事件监听（BUSINESS_EVENT）结构（CDP 抓包） |
| `schedule-structure.md` | 定时任务（SCHEDULE）结构（CDP 抓包） |
| `state-lifecycle.md` | 草稿态/发布态（state 生命周期） |
| `deleted-scheduled-flow-lifecycle.md` | 删流程后定时任务仍会跑 |
| `sub-microflow-schema-compatibility.md` | 子流程契约变更的构建期检测 |

## 5. 生成器与闸门（生成链路 + 拦截规则）

| 文件 | 内容 |
|---|---|
| `build-chain.md` | 声明式 spec → dataSchema → 提交 |
| `test-build-chain.md` | 测试→构建→运行前端真实接口链 |
| `generation-gates.md` | 生成闸门：错误 → 规则 → 拦截 |
| `generator-redesign.md` | 生成器重写方案（链路顺序 + 定义驱动） |
| `frontend-validation.md` | 前端校验清单（闸门输入） |
| `react-interaction-contract.md` | React 受控组件交互契约 |
| `p5-preflight.md` | P5 前置审计 |

## 6. 业务流程（业务数据流 + 端到端）

| 文件 | 内容 |
|---|---|
| `business-data-flow.md` | 业务数据流构造：值编辑器三态 + 字段引用 RETRIEVE 中转 |
| `field-assignment-source-strategy.md` | 字段赋值来源策略 + 数据血缘审计 |
| `business-skeletons-from-643.md` | 真实业务微流程骨架（643 条） |
| `business-plan-datasource-check.md` | 校验数据源是否有效 |
| `p7-e2e2-llm-draft.md` | 宿主 LLM 生成草稿 → 业务结果闭环 |
| `p7-e2e-business-flow.md` | 端到端业务闭环实证 |
| `full-node-generation-plan.md` | 全量节点业务测试生成计划 |

## 7. 能力矩阵（能力分级 + 数据流矩阵）

| 文件 | 内容 |
|---|---|
| `capability-matrix.md` | ★ 能力矩阵（四档状态判定 + 当前基线） |
| `dataflow-and-node-matrix.md` | 数据流设计 + 节点能力矩阵 |

## 8. 运行时（运行日志 + 写节点行为）

| 文件 | 内容 |
|---|---|
| `runtime-log.md` | 运行日志（RUNTIME 读侧，接口排障） |
| `write-node-runtime-gap.md` | 写节点运行时行为（字段不生效根因） |

## JSON 数据文件

| 文件 | 内容 | 谁消费 |
|---|---|---|
| `node-catalog.json` | 节点定义清单 | 构造器 |
| `node-contract-from-samples.json` | 每节点键级 MUST/OPT（样本数） | 闸门 G23 |
| `node-settings-capability.json` | 节点配置项能力矩阵 | 构造器 |
| `app-service-catalog.json` | 自定义服务目录 | CALL_APP_SERVICE |
| `entity-write-capability.json` | 实体可写性（有无 create） | 闸门 G34 |
| `expression-capability-matrix.json` | 表达式能力矩阵 | 表达式引擎 |
| `domain-node-sets.json` | 域节点集合 | — |

## evidence/（原始证据，豁免脱敏）

运行日志、反编译证据、样本快照的原始响应，不放结论区。

## 关联（本目录之外）

- 构造器：`components/construction/`（生成节点）
- 闸门：`components/udc/microflow/gates.py`
- 技能：`skills/`（跨会话加载的 SKILL.md，与 facts 双轨）
- 一次性脚本：`_attic_pending/`
