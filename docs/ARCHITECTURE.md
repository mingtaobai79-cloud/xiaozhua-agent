# Seeyon Agent 架构

> 架构方向以 `capability/ROADMAP-v2.md` 为基线，目标架构见 `capability/ARCHITECTURE.md`。
> 本文是仓库实现与职责的视图；`REPO-LAYOUT.md`、`HOST-INTEGRATION.md` 和
> `KNOWLEDGE-LANDING-RULES.md` 分别保留目录、宿主接入和知识归位的专题说明。
> 本文涉及数量和实现状态的记录有时点性，使用前需对照代码及当前进度。
> 每一节标注【现状】= 已实现并验证 /【目标】= 规划中未落地 /【未实现】= 明确缺口。
> **不得把【目标】当作已实现的系统结构。**

---

## 1. 定位与总体目标

【现状】Seeyon Agent 是**嵌入宿主的专业能力组件，不是独立 agent**。宿主负责思考与规划，
Seeyon Agent 提供致远低代码平台（UDC/BPM/SPI/Integration/Runtime）的专业知识、平台工具、
执行能力和验证体系。

【目标】「一个 Seeyon Agent Core + 多个宿主适配器」——核心独立于宿主，宿主只是运行入口。
同一套 Facts / Skills / Components / MCP 工具，Codex / Claude Code / Cursor / Hermes 都能调用，
不各自复制一套业务实现。

## 2. 顶层目录职责

| 目录 | 层 | 职责 |
|---|---|---|
| `components/` | 实现层 | 九域约束模型、构造器、平台操作层（109 py） |
| `core/` | 装配壳 + 事实库 | `core/*.py` 薄内核；`core/facts/` 按域一目录的事实库 |
| `providers/` | 外部适配 | MySQL/CDP/HTTP/K8s/Redis/Nacos 只读客户端 |
| `adapters/` | 宿主接入 | Hermes/Claude Code/Codex/MCP 接入模板与清单 |
| `config/` | 环境常量 | 引用式配置（值走环境变量或仓外文件，永不入库） |
| `fixtures/` | 测试夹具 | 默认探针输入、微流程夹具 |
| `scripts/` | 可复用脚本 | 建实体/清理流程/闸门回归/构建验证等 |
| `tests/` | 契约测试 | 2628 个（离线只读为主） |
| `tools/` | 工具 | 审计/CDP/表达式/jar 分析 |
| `docs/` | 文档 | 架构/契约/审计证据/计划 |
| `skills/` | skill 源 | 可安装的 SKILL.md（版本化） |
| `_attic_pending/` | 一次性资产 | 正式业务案例 + 探针 + 历史快照（待分类） |
| `scratch/` | 临时区 | 不入 git，24h 清理 |

## 3. components 模块划分

【现状】

| 子目录 | 职责 |
|---|---|
| `construction/` | ★ 微流程构造器（节点构造器/逻辑图/表达式 DSL/需求编译/血缘审计/页面定义） |
| `udc/microflow/` | 微流程工具（gates G1-G40 / deploy / live_refs / expression_* / capability_registry） |
| `udc/expression/` | 表达式（dto/endpoints/operators/token/validation） |
| `udc/setting/` | 设置域约束（枚举/字段集/选项集/自定义对象/参数等 15 约束文件） |
| `udc/application/` | 应用内操作 + 依赖约束 |
| `platform_operations/` | 平台操作（部署/证据/GraphQL/写执行器/只读） |
| `gateway/` | 网关适配器/客户端/凭证/发现 |
| `integration/` `runtime/` `profiles/` | 集成/运行时/配置档案（多为只读骨架） |

【目标】`construction/` 按域重组为 `registry/ nodes/ expression/ logic_graph/ requirement/ lineage/ pipeline/`，
通过统一 Node Registry + Facade 提供调用。**不能先移动文件再修 import，按依赖审计逐步迁入。**

## 4. core 职责

【现状】`core/*.py` 是薄内核（agent 73 行）；`core/facts/` 是事实库；`core/role/` 是角色定义
（BEHAVIOR/EVIDENCE-DISCIPLINE/ROLE-CARD）；`core/skills/` 是内部知识入口；`core/tools/` 是工具契约。

**四层职责（不可混）：**

| 层 | 职责 | 权威来源 |
|---|---|---|
| Skills | 指导 Agent 怎么工作（步骤/纪律/决策规则） | `skills/`（仓库为源） |
| Facts | 告诉 Agent 平台真实是什么（事实/契约/限制） | `core/facts/` |
| Components | 真正执行（构造器/校验器/执行器） | `components/` |
| Tests | 证明实现正确（契约测试） | `tests/` |

## 5. facts 组织与引用规则

【现状】`core/facts/` 按域一目录：`udc/`（最大，含 microflow 61 文件已建 INDEX）、
`standard-product/`、`spi/`、`bpm/`、`connector/`、`gateway/`、`runtime/`、`deploy/`、`item-mgmt/`。

引用规则（三条硬规则，见 REPO-LAYOUT.md）：

1. **事实与代码分离**——结论写 `core/facts/<域>/`，可执行断言写 `components/udc/<域>_constraints.py`，测试防脱节。
2. **证据可复核**——每个 `path:line` 引用，文件必须在 `docs/audit/artifacts/` 有副本；指向 scratch 的引用失效。
3. **只读优先**——providers 默认只读，写操作需显式 WriteScope。

【现状】事实分级（KNOWLEDGE-LANDING-RULES）：LIVE PASS / LIVE / VERIFIED_STATIC_BYTECODE / UNVERIFIED / VACUUM。

## 6. providers 只读取证机制

【现状】`providers/` 是真实数据源只读客户端：

- `mysql_readonly.py` — MySQL 只读
- `cdp.py` — 浏览器 CDP 抓包
- `http_readonly.py` — HTTP 只读
- `redis_readonly.py` / `kubernetes_readonly.py` / `nacos_readonly.py` — Redis/K8s/Nacos 只读
- `registry.py` — provider 注册

默认离线只读；联网需显式 `allow_network=True` + 凭据路径引用。写操作一律 DENIED（policy gate）。

## 7. adapters 宿主集成

【现状】`seeyon_host_bootstrap.py` 的 `bootstrap()` 是**唯一宿主入口**，返回 4 能力：
`dispatch`（需求归一化→路由→证据化）、`generate`（后端骨架+前端页面）、`live_probe`（test2 只读）、`agent`（本体）。

`adapters/` 已实现：
- `mcp/server.py` — 手写 JSON-RPC 2.0 stdio，5 工具（dispatch/generate/generate_from_requirement/live_probe/deploy_plan），19 测试
- `claude-code/CLAUDE.template.md` `codex/AGENTS.template.md` `hermes/ADAPTER.md` — 宿主模板

【目标】MCP 工具分层（三类）：Knowledge（facts_search/capability_inspect）/ Planning（business_analyze/flow_plan/lineage_audit）/ Execution（apply_plan/build/run/verify）。**不让 Agent 面对 200 个底层接口**，暴露 12 个左右高层工具。

【未实现】`resources/prompts/logging` 扩展；宿主实接（MCP server 指向 stdio）未验证。

## 8. scripts / tools / tests / fixtures 职责

| 目录 | 职责 | 维护级别 |
|---|---|---|
| `scripts/` | 可复用脚本（entity_write_capability/cleanup_verify_flows/probe_nodes/regress_gates/verify_build_compile） | 维护 |
| `tools/core/` | 正式工具（被引用） | 维护 |
| `tools/audit/` | 审计脚本 | 维护 |
| `tools/one-off/` | 一次性取证脚本 | 不维护，仅参考 |
| `tests/` | 契约测试（offline/live/blocked/acceptance 分层） | 维护 |
| `fixtures/` | 测试夹具 | 维护 |

## 9. Skills 与 Roles 区别

| | Skills | Roles |
|---|---|---|
| 是什么 | 任务的工作流/步骤/决策规则 | Agent 的身份/行为/纪律 |
| 位置 | `skills/`（可安装 SKILL.md） | `core/role/`（BEHAVIOR/ROLE-CARD） |
| 粒度 | 按任务（建实体/建微流程/组装业务） | 按身份（专业 Agent 的通用行为） |

【现状】skill 有 15+ 个入仓（微流程生成/实体开发/业务组装/各域）；role 有 BEHAVIOR/EVIDENCE-DISCIPLINE/ROLE-CARD。

## 10. 数据从需求到平台执行的完整链路

```
需求（自然语言）
  → BusinessRequirementCompiler（理解业务 → 产出 IntentDraft）
  → LogicGraphRunner（逻辑图 → 平台 dataSchema）
  → 构造器（NodeBuilder → 各节点构造器 → 完整 schema）
  → 闸门（G1-G40 静态校验）
  → 保存（draft）→ 发布（RELEASE）→ checkSchema
  → 构建（deploy-normal，应用级一次编译所有 RELEASE 流程）
  → 运行（MANUAL 触发 / SCHEDULE / BUSINESS_EVENT）
  → 读侧断言（物理表回读，不认脚本返回值）
```

## 11. 证据与能力等级体系

能力五级（微流程）：CONSTRUCTED → SCHEMA_VERIFIED → UI_VERIFIED → BUILD_VERIFIED → RUNTIME_VERIFIED。

证据等级（facts）：LIVE PASS / LIVE / VERIFIED_STATIC_BYTECODE / UNVERIFIED / VACUUM。

**证据纪律**：断言只认读侧数据；STATIC/UNVERIFIED 不得报 LIVE PASS；每个能力声明对到证据源。

## 12. UDC / BPM / SPI / Integration 领域边界

| 域 | 覆盖 | 现状 |
|---|---|---|
| UDC | Entity/Setting/Page/Microflow（最完整） | 构造 + 验证 + 运行证据齐 |
| BPM | 流程版本映射/数据流 | 事实有，实现薄 |
| SPI | 扩展契约/注册/加载 | 事实有，实现薄 |
| Integration | Connector/DataFlow | 事实有，实现薄 |
| Standard Product | AppService/DTO/扩展点 API 使用 | 事实有（26+ md），未接构造器 |

## 13. 本地运行及宿主接入

【现状】`bootstrap()` 唯一入口；CLI `seeyon_cli.py`；MCP `server.py` stdio。

```bash
# 本地运行
python -m pytest tests -q          # 2628 passed（离线只读）
# 宿主接入
from seeyon_host_bootstrap import bootstrap
host = bootstrap()                 # 离线默认
host = bootstrap(credential_file=<path>, allow_network=True)  # 活体
```

【目标】`seeyon install --host codex --scope user` 统一安装；`seeyon doctor` 诊断；MCP stdio 为第一版传输。

## 14. 当前明确未完成 / 受限模块

| 项 | 状态 |
|---|---|
| MCP 工具分层（12 个高层工具） | 【未实现】现 5 个底层工具 |
| SeeyonAgentFacade 统一门面 | 【未实现】现 bootstrap 直接暴露底层 |
| Node Registry 统一节点发现 | 【目标】构造器分散 5 文件 |
| Skill 分发同步机制 | 【目标】三套目录无同步 |
| 三宿主实接验收 | 【未实现】MCP server 可起，宿主未实接 |
| 制造业 14 项业务断言 | 【待执行】BUILD_VERIFIED，未 BUSINESS_RESULT_VERIFIED |
| Runtime/Integration 实时连接 | 【未实现】仅本地 snapshot 读取 |
| SPI 组件 | 【未实现】仅路由占位 |

---

## 目标架构 vs 现状（汇总）

```
【现状】
bootstrap → dispatch/generate/live_probe（底层 4 能力）
MCP server → 5 工具（底层）
构造器 → 分散 5 文件
Skill → 三套目录无同步

【目标】
SeeyonAgentFacade → knowledge/planning/execution 三层 12 工具
MCP server → 暴露 Facade 同一套工具
Node Registry → 统一节点发现
仓库 skills = 源，Hermes skills = 安装副本（同步脚本）
```
