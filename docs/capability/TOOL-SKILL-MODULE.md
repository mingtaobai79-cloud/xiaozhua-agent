# TOOL-SKILL-MODULE｜Tool / Skill / Module 三者定义与映射（A7）

> 基线：`docs/capability/ROADMAP-v2.md` @ git `d76f7af`（本文件是 §三能力模型 + §五模块推进 + §六
> 生产线职责中"Tool/Skill/Module"三层的定义与映射，不新增定位/阶段）。引 ROADMAP 章节限 **§一~§七**
> （实测范围内；§七即"本文件即路线基线"结尾节，无 §八/§九——同 A5 更正口径）。
> 配套：`CAPABILITY-MODEL.md`（§2.1 CONFIG 声明 schema / §2.2 CODE 三要素）、`ARCHITECTURE.md`（§五
> Registry 实测口径）、`EVIDENCE-MODEL.md`（§二 OperationStatus 归并口径）。
> 铁律：**一个 registry 契约 = 一个 Tool 候选**；registry 外候选一律 **UNVERIFIED 登记，不新增**；
> 只写定义/清单/映射，不实现代码；不展开 02–12 模块正文；凭据 0 入仓；本文件只给 Skill 定义与首例，
> **不写 B 件**（`core/skills/udc-entity-dev.md` 另派单）。

---

## 一、三者定义与边界（对齐 ROADMAP-v2 §三 / §六）

ROADMAP-v2 §六 原文：*"每个审计回合的产出 = Capability Contract + Fact 文档 + Test + 证据等级"*；
§五 模块流水线：*Module → Capability Inventory → CONFIG/CODE 分型 → 事实证据 → Tool Contract →
Skill → Test → Sandbox 需求 → Agent Adapter 暴露*。据此定三层：

| 层 | 定义 | 判据 | 在盘锚点 |
|---|---|---|---|
| **Module（能力域）** | 一个 Seeyon 模块域，含若干 Capability（01–12 编号，见 `MODULE-INVENTORY.md`） | 有专属 capability 契约族 / 事实域 | 01 UDC = 唯一 P0 样板（A2） |
| **Capability（能力契约）** | 一条在盘 registry `operation_id`（CONFIG 型声明，A3 §2.1），携证据等级 + 写门 | registry 已登记 = 实证；未登记 = UNVERIFIED | `UdcOperationRegistry` 64 条（A1 §五） |
| **Tool（单动作执行）** | **一个 Capability 契约 = 一个 Tool 候选**：宿主可调用的一步原子动作（method+path+input） | 有在盘契约 = Tool 候选；registry 外 = UNVERIFIED | 见 §二逐条映射 |
| **Skill（一类任务打法）** | 组合多 Tool + 回读/验证步的"任务打法"（怎么做一件事） | 有在盘实证链路 = Skill 首例；否则 UNVERIFIED | 见 §三 deploy_plan 4 步 |
| **宿主（Agent Host）** | 不自研；Tool/Skill 经 Adapter 暴露到 Hermes/Codex/CC（A8 细化，本文留接口不重复定义） | — | 见 §四 |

**映射规则（不强绑定宿主）**：`Module → Capability → Tool → Skill → 宿主`。
一条链路：某 Module 的 Capability 契约群 → 逐条成 Tool 候选 → 组合成 Skill 打法 → 经 Adapter 暴露给宿主。
**宿主不是映射终点**：同一 Skill 可暴露给多个宿主（ROADMAP §一.2 "可安装角色+能力包"），
故 Tool/Skill 与宿主解耦（A8 定义暴露形态）。

---

## 二、现存 registry 契约 → Tool 候选映射（UdcOperationRegistry，实测 64 条）

**口径（沿用 A1 §五）**：registry 实位 `components/platform_operations/registry.py`，
`UdcOperationRegistry.default()` = **64 裸** = **59 基础 + 2 R18 部署 + 3 别名**；
去 3 别名后 = **61（59 基础 + 2 R18）** 为域映射基数。本表按域列 64 条全量，并**显式标注 3 别名**，
每条 Tool 候选标**在盘 status**（`registry.py` 实值）+ **A4 归并等级** + 读写属性。
**读 57 / 写 7**（全 64 口径；写 7 全走写门 DENIED，宿主执行——A1 §六）。

### 2.1 域映射汇总（64 裸，按域；status 引 registry.py 实值，等级按 A4 归并）

| 域 | 契约数 | 写/读 | status 分布（registry.py 实值） | A4 归并等级 | Tool 候选 |
|---|---|---|---|---|---|
| **entity** | 27 | W6/R21 | VERIFIED_STATIC_BYTECODE 18 + UNKNOWN 9 | VSB→STATIC / UNKNOWN→待证 | 27 候选（9 条 UNKNOWN 标 UNVERIFIED 候选） |
| **flow** | 8 | R8 | VSB 8 | STATIC | 8 候选 |
| **application** | 6 | R6 | VSB 6 | STATIC | 6 候选 |
| **applog** | 6 | R6 | VSB 6 | STATIC | 6 候选 |
| **deploy（R18）** | 2 | W1/R1 | OBSERVED 2（deploy.normal / deploy.search_status） | OBSERVED→LIVE | 2 候选（deploy.normal=LIVE 已实证；search_status=UNVERIFIED） |
| **metadata** | 2 | R2 | VSB 2 | STATIC（POST 执行层 DENIED，A1 §四 已知边界） | 2 候选 |
| **page_info** | 2 | R2 | VSB 2 | STATIC | 2 候选 |
| **page_log** | 2 | R2 | VSB 2 | STATIC | 2 候选 |
| **serial** | 2 | R2 | VSB 2 | STATIC | 2 候选 |
| **appinfo / attribute / database / datatype / entity_data / microflow / role** | 各 1 | R | VSB | STATIC | 各 1 候选 |

> **去别名基数 61 = 59 基础 + 2 R18**：上表 64 中 3 条为别名（`udc.entity.get` / `udc.entity.list` /
> `udc.attribute.list`，`registry.py` 经 `replace(..., operation_id=…)` 复制），非独立契约，
> 列全量时标 [别名]，域映射基数按 61 计。

### 2.2 写 7 条 Tool 候选（全走写门 DENIED，宿主授权执行；A1 §六）

| Tool 候选（op） | 域 | status（registry 实值） | 写门 | 备注 |
|---|---|---|---|---|
| `udc.entity.create` | entity | VSB | DENIED/POLICY_DENIED | deploy_plan step1（A3 §三 真例） |
| `udc.entity.attribute.create` | entity | UNKNOWN | DENIED | deploy_plan step2 |
| `udc.entity.attribute.create_batch` | entity | UNKNOWN | DENIED | 批量建属性 |
| `udc.entity.attribute.update` | entity | UNKNOWN | DENIED | |
| `udc.entity.attribute.delete` | entity | UNKNOWN | DENIED | |
| `udc.entity.update` | entity | UNKNOWN | DENIED | |
| `udc.deploy.normal` | deploy(R18) | OBSERVED | DENIED（写契约） | deploy_plan step4，LIVE 实证（A6 §三） |

> **读 57 条** = 全 64 减写 7。读面里 **UNKNOWN 9 条全在 entity 域**（attribute.search / search.term /
> 等）；status=UNKNOWN 的 9 条 Tool 候选**登记为"未取证候选"**（A4 §二 不可归并项），宿主执行须先
> 活体回读确证，不臆造已生效。

---

## 三、Skill 首例：deploy_plan 4 步「建单据实体」打法

**Skill = 组合多 Tool + 回读/验证步的任务打法**。首例取 A3 §三 已核定的 deploy_plan 4 步
（`deployment.py:115` `build_deployment_plan()`），构成"建一个单据实体"的端到端打法：

| Skill 步 | 组合的 Tool 候选（registry op） | 动作 | 回读验证（step `verify`，在盘原值） |
|---|---|---|---|
| ① 建实体 | `udc.entity.create` | 建单据实体（stereotype=bill） | `GET /service/udc/entity/{id}` → publishState/tableName |
| ② 建属性 | `udc.entity.attribute.create` | 批量建业务字段 | `GET .../attribute/select-all-by-entity-id/{entityId}` |
| ③ 建页 | `udc.page.create`（deploy_plan step3，`page-info/base-info/create`） | 建 LIST+DETAIL 页 | `GET /service/udc/page-info/select-by-appId/{appId}` 回读 caption+relationGroupId |
| ④ 构建 | `udc.deploy.normal` | 触发 RELEASE 构建（构建即部署） | RDS `udc_test2.udc_deploy_record` 最新行（deploy_type=2 state=1）+ 应用库 SHOW TABLES |

**打法要点（组合 + 回读）**：
- **配置化组合**：4 步全是 CONFIG 型声明（A3 §三），agent 出方案 data，宿主授权执行；
  每步带 `verify` 回读断言（"建了→读回确证"），失败即停（失败回流边界见 A6 §一 五阶段）。
- **LIVE 实证**：该打法全链已 test2 活体确证（`docs/audit/udc-design-time-deploy-write-contracts.md`
  §一：建实体 BOOT_0000 / 建属性×4 / 建页×2 / RELEASE 构建 state=1 / 物理表落应用库）。
- **规格锚点（B 件，本文不写）**：本 Skill 打法对应 B 样板链 `core/skills/udc-entity-dev.md`
  （"建一个单据实体"九段式打法）的规格来源——**B 件由 main 另派单**，本文只定义 Skill + 给首例，
  不产出 B 文件（边界铁律）。

---

## 四、与 A8 AGENT-ADAPTER 留接口（不重复定义宿主）

Tool/Skill 到宿主的暴露形态**只留占位接口，细则归 A8**：

| Tool/Skill 资产 | 宿主暴露形态（A8 细化，本文占位） | 现状 |
|---|---|---|
| Tool 候选（64 契约） | MCP tool 清单（每 op → 一个 tool：name/method/path/input） | UNVERIFIED（A8） |
| Skill 打法（deploy_plan 4 步） | Skill 文件（组合 4 Tool + 回读步，供宿主 Agent 调） | UNVERIFIED（A8 / B 件） |
| 角色能力包 | 角色提示词包（Role 行为规范） | UNVERIFIED（A8） |

> 暴露形态 = ROADMAP §一.2 "可安装角色+能力包经 Adapter 进入不同宿主"；本文只定义"Tool 清单 →
> 宿主暴露"的**映射规则占位**，不定义 Adapter 本体、不重复 A8。

---

## 五、边界与铁律自证

- **registry 外 = UNVERIFIED 登记，不新增**：本文 Tool 候选**全部**源自在盘 `UdcOperationRegistry`
  64 条（`registry.py` 实值），无一条臆造；UNKNOWN 9 条与 deploy.search_status 明确标"未取证候选"。
- **只写定义/清单/映射，不实现代码**：未改 `components/`（git 核实零改动）；Skill 首例只描述打法，
  不产出可执行 Tool/Skill 代码或 B 文件。
- **不展开 02–12 模块正文**：映射只针对 01 UDC（唯一 P0 样板，A2）；其余模块 Tool 候选归后续批次。
- **不新增定位/阶段/验收**：三者定义引 ROADMAP §三/§六；契约逐值引 A1 §五；等级引 A4 §二；
  4 步真例引 A3 §三；写门/构建链路引 A1 §六 + A6 §三 + `layer.py:22`。
- **凭据 0 入仓**：本文只列 op/method/path/status，不含 token/凭据值。
- **UNVERIFIED 清单**：3 别名为复制非独立契约（域基数按 61）；UNKNOWN 9 条未取证候选；
  `deploy.search_status` 完整路由；宿主暴露形态（A8）。

---

## 六、与 ROADMAP-v2 / 前件的对应

| 内容 | 来源（实测） |
|---|---|
| 三者定义 + 映射规则 + 模块流水线 | ROADMAP-v2 §三 / §五 / §六 |
| 64 裸 = 59 基础 + 2 R18 + 3 别名；读 57 / 写 7；域分布 | `registry.py`（本轮 `implementer/map_a7.py` 实测） |
| 各契约 status 实值（VSB/OBSERVED/UNVERIFIED/UNKNOWN） | `registry.py` UdcOperationRegistry（本轮脚本逐条打印） |
| 写门 DENIED/POLICY_DENIED | `components/platform_operations/layer.py:22`（A4 已核） |
| Skill 首例 4 步 + 回读 | A3 §三 + `deployment.py:115` + `docs/audit/udc-design-time-deploy-write-contracts.md` |
| 归并等级口径 | A4 §二（OperationStatus → 四层） |
