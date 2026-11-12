# AGENT-ADAPTER｜宿主适配规范（A8）

> 基线：`docs/capability/ROADMAP-v2.md` @ git `d76f7af`（本文件是 §一.2"Agent Host 兼容"与 §二
> 目录骨架 `adapters/`、`installer/` 的展开，不新增定位/阶段/验收）。引 ROADMAP 章节限 **§一~§七**
> （§七即"本文件即路线基线"结尾节，无 §八/§九/§十二——同 A5/A7 更正口径）。
> 配套：`ARCHITECTURE.md`（§二 宿主层 + §三 Adapter）、`TOOL-SKILL-MODULE.md`（§四 已给
> Tool→MCP/Skill 文件/角色包**占位接口**，本文细化这些占位，不重复定义 Tool/Skill 本身）。
> 铁律：**不自研 Agent Loop / 记忆 / Planner / Agent OS**（ROADMAP §一.2 原文）；本文件只写规范与
> 在盘锚点，不实现代码；**2026-11-07 更正**：`adapters/{hermes,codex,claude-code,mcp}/`、`installer/`
> 与 `core/{role,facts,skills,tools}` 目录现已存在（原文「在盘未建」作废）；仍未建的是
> `core/capabilities/`、`modules/`、`sandbox/` 与实际宿主传输层。凭据 0 入仓
> （v1 adapter `credential_mode="path-ref-only"`，不引 token/凭据值）。

---

## 一、三层兼容模型定稿（对齐 ROADMAP-v2 §一 + §二）

ROADMAP-v2 §一 两级兼容 + §一.2 明令"不自研 Agent Loop/记忆/Planner/Agent OS"，据此定三层：

| 层 | 语义 | 在盘锚点 | 现状 |
|---|---|---|---|
| **2小爪 版本兼容（对内）** | 客户当前仓库 = Canonical，能力定义稳定；差异走 **Version Adapter**（adapter-5.3 / 5.4 / …），Agent 不自行判版本分支 | A5 已定 Canonical=5.3.517；`registry.py` 全 5.3.517 锚点 | 目标态（Version Adapter 未建，UNVERIFIED）|
| **Agent 角色 + 能力包** | 可安装单元 = **Role + Facts + Skills + Tools + Code + Sandbox**（§二 目录骨架 `core/{role,facts,skills,tools,capabilities}` + `sandbox/`） | `core/registry.py`（ComponentRegistry，在盘）；`components/platform_operations/`（契约/写门，在盘）；`core/{role,facts,skills,tools}` 已在盘，`core/capabilities/` 仍未建 | 部分在盘（registry/契约/role/facts/skills/tools 在），`core/capabilities/` 未建（UNVERIFIED）|
| **Agent Host 兼容（对外）** | 角色包经 **Adapter** 进入已有宿主（Hermes / Codex / Claude Code），暴露形态=MCP tool 清单 / Skill 文件 / 角色提示词包；**宿主只提供 Loop/记忆/Planner，2小爪 Agent 不自研** | ROADMAP §二 `adapters/{hermes,codex,claude-code}/`（**目录已在盘**，内容为声明级模板/清单）；**v1 adapter = `seeyon_host_bootstrap.py` 在盘**（见 §三） | 目录在盘；v1 bootstrap 在盘 |

**定稿口径**：2小爪 Agent 是"可安装角色+能力包"，宿主是"提供 Agent Loop/记忆/Planner 的既有系统"，
二者经 Adapter 解耦——宿主可换，能力包定义稳定。

---

## 二、v1 adapter 实例：`seeyon_host_bootstrap`（在盘实测，非转述）

**位置**：仓库根 `seeyon_host_bootstrap.py`，入口 `bootstrap(*, credential_file=None, allow_network=False, …)`
（L25）。这是 ROADMAP §一.2 "可安装角色+能力包经 Adapter 进宿主"的**在盘 v1 实例**，宿主（Hermes/CC/Codex）
拿到它即可调 2小爪 能力。

**`bootstrap()` 返回 dict（实测 L136–L149，main 已在 ROUTE L21-25 独立复核一致）**：

| 键 | 实测值 | 语义 |
|---|---|---|
| `agent` | ComponentRegistry 实例 | 组件注册/派发边界 |
| `dispatch` / `generate` / `generate_from_requirement` / `live_probe` / `deploy_plan` | 5 个宿主可调用能力（闭包） | 见下 |
| `allow_network` | `False`（默认离线） | 活体回读需显式开 |
| `capabilities.components` | `sorted(agent.registry.names())` → 实测 3 组件（`integration`/`runtime`/`udc`） | 宿主可见能力面 |
| `capabilities.readonly_only` | `True` | 只读纪律 |
| `capabilities.credential_mode` | `"path-ref-only"` | **凭据仅路径引用，值 0 入仓** |
| `capabilities.deployment_plan` | `"readonly data; host executes the write steps"` | 写方案 data，宿主执行 |
| `capabilities.schema` | `"seeyon-host-bootstrap.v1"` | v1 adapter schema 标识 |

**五宿主能力 → 底层契约映射（在盘）**：
`dispatch`（意图路由）/ `generate`（建实体方案 data）/ `generate_from_requirement`（需求→实体方案）/
`live_probe`（活体只读探测，`allow_network` 开才实跑）/ `deploy_plan`（设计态 4 步部署方案 data，
引 A3 §三）。五个均**只出数据/只读，不出写**（`readonly_only=True`，写门 DENIED——A1 §六）。

---

## 三、v1 五能力 → 三宿主暴露形态映射（A7 §四 占位细化）

`TOOL-SKILL-MODULE.md` §四 已给"Tool 清单→MCP / Skill 文件 / 角色提示词包"占位接口，全标 UNVERIFIED（A8）。
本表把占位**细化为具体暴露形态**（规范定义，非实现）：

| 宿主 | 输入形态 | v1 adapter 如何暴露 | 现状 |
|---|---|---|---|
| **Hermes**（宿主=本主控链路） | **MCP tool 清单** + 能力包 | `bootstrap()` 返回的 5 能力 + `capabilities.components` 直接作 tool 面；宿主以 Python 调用（非 MCP 传输） | **v1 在盘**（Python-native），MCP 传输层 **UNVERIFIED（未建）** |
| **Codex** | **Skill 文件**（任务打法） | deploy_plan 4 步"建单据实体"打法（A7 §三）落成 Skill 文件供 Codex Agent 调 | 目标态，**UNVERIFIED（未建）** |
| **Claude Code** | **角色提示词包**（Role 行为规范） | Role 定义 + 能力包清单注入 CC 系统提示词 | 目标态，**UNVERIFIED（未建）** |

> 暴露解耦（§一定稿）：同一能力包可向三宿主暴露不同形态（MCP/Skill/提示词包），宿主 Loop/记忆/Planner
> 各异，能力定义不变。当前**仅 Hermes Python-native 在盘（v1）**；MCP 传输层、Skill 文件、提示词包、
> 三宿主 `adapters/{hermes,codex,claude-code}/` 目录**已在盘**（`Hermes-SKILL.md` / `AGENTS.template.md` /
> `CLAUDE.template.md` + 各自 `MCP-TOOL-MANIFEST.md`），但安装器与真实宿主加载仍未验收。

---

## 四、v1 → v2 适配契约（字段映射：可复用 vs UNVERIFIED）

**从 v1 `bootstrap()` dict（§二，L136–L149 实测）到目标态 adapter（`adapters/{hermes,codex,claude-code}/`）
的字段映射**。与 A7 §四 留接口对齐，**不重复定义 Tool/Skill 本体**（Tool/Skill 定义在 A7 §一/§三/§四）；
本表只给"v1 dict 哪个字段承接进 v2 adapter 暴露面"，并标注**可复用（在盘实测）/ UNVERIFIED（未建）**。

| v1 dict 字段（§二 在盘实测） | v2 adapter 承接面 | 复用判定 | 依据 |
|---|---|---|---|
| `capabilities.components`（registry 3 组件 integration 3/runtime 4/udc 12） | 各宿主 **Tool 清单**来源（A7 §四 占位） | **可复用**（数据源在盘） | registry 契约族已实证（A1 §五） |
| `dispatch` / `generate` / `generate_from_requirement` / `live_probe` / `deploy_plan`（5 能力） | 各宿主 **Tool 动作**（MCP tool / Skill 内调用） | **可复用**（动作语义在盘）；但宿主**传输层（MCP 传输 / Skill 文件 / 角色提示词包）未建 = UNVERIFIED** | 5 能力语义在盘；传输层目标态（§三） |
| `capabilities.readonly_only=True` | 宿主侧 **readonly 门禁**（写步由宿主执行） | **可复用** | 写门 `layer.py:22`（A1 §六） |
| `capabilities.credential_mode="path-ref-only"` | 宿主 **凭据注入机制**（仅路径引用，值 0 入仓） | **可复用**（机制不变）；各宿主**凭据注入实现方式 = UNVERIFIED** | 本文只描述机制，不引凭据值 |
| `capabilities.deployment_plan="readonly data; host executes the write steps"` | 宿主**执行写步契约**（v2 保留 agent 出 data、宿主执行） | **可复用** | deploy_plan 4 步（A3 §三 / A7 §三） |
| `capabilities.schema="seeyon-host-bootstrap.v1"` | v2 各宿主 adapter 的 **schema 锚** | v1 schema **可复用为锚**；**v2 宿主专属 schema（hermes/codex/cc）未定义 = UNVERIFIED** | 目标态未建 |
| `agent`（ComponentRegistry 实例） | 宿主可调的**能力注册/派发面** | **可复用** | `core/registry.py` 在盘 |
| `allow_network`（默认 False） | 宿主**活体探测开关**（开才实跑） | **可复用** | §二 在盘 |

**复用小结（可复用 = 在盘 8 项全实测）**：5 能力 + `readonly_only` + `credential_mode` +
`deployment_plan` + `components` + `agent` + `allow_network` + v1 `schema`（作锚）——即 v1 adapter 的
**能力面与只读/凭据纪律可直接承接进 v2 暴露面**，无需重造。

**UNVERIFIED（未建 = 目标态）**：各宿主**传输层**（MCP 传输 / Skill 文件 / 角色提示词包）、
**v2 宿主专属 schema**、各宿主传输层实现、`installer/` **打包面实现**——仍未建，标 UNVERIFIED，不写成已实现。
（**目录**已在盘：`adapters/{hermes,codex,claude-code,mcp}/`、`installer/` 均存在；
建的是目录，没建的是其中的实现。见 §三/§五 与 L9 头注。）**本映射只定义"字段承接关系"，
不实现任何 adapter 代码（禁改 components/ core/）。**

---

## 五、installer 目标态（目录约定，实现标未实现）

ROADMAP §二 目标态 `installer/`（**目录已在盘，安装器未实现** —— 见本节末「现状」）。本文只做**目录约定**，不实现：

- **约定**：`installer/` 承载"角色+能力包"的打包/安装面（把 `core/{role,facts,skills,tools,capabilities}`
  + 目标 `adapters/<host>/` 暴露形态 打包为可安装单元）。
- **依赖**：打包须带 `capabilities` 清单（registry 契约族）+ 证据等级标注（A4 四层）+ Canonical 版本锚
  （A5，=5.3.517），使宿主安装后可校验"能力定义稳定、差异走 Version Adapter"。
- **现状（2026-11-07 更正）**：`installer/` 目录**已存在**，内含 `README.md` 与
  `INSTALL-MANIFEST.md`（声明级清单，自述「无在盘可运行安装脚本」）；即目录在、安装器未实现。
  原文「`ls installer/` = No such file/directory」作废。
  本节仅目标态约定，UNVERIFIED。

---

## 六、边界与铁律自证

- **不自研 Agent Loop/记忆/Planner/Agent OS**（§一定稿引 ROADMAP §一.2 原文）：本文件只定义
  "角色包 + Adapter + 暴露形态"，不写宿主 Loop；宿主能力（Loop/记忆/Planner）归宿主，不进本契约。
- **不实现代码 / 目标态未建全标 UNVERIFIED**：各宿主传输层、`installer/` 的**实现**（目录已存在）、
  MCP 传输层、Skill 文件、角色提示词包——在盘均不存在，本节全标"目标态/未建"，不写成已实现。
- **v1 只引在盘实测**：`seeyon_host_bootstrap.py` 返回 dict（L136–L149）与 5 能力、registry 3 组件
  全部本轮脚本/行号实测，非转述；main 已在 ROUTE L21-25 独立复核。
- **不新增定位/阶段/验收**：三层模型引 ROADMAP §一/§二；占位细化承接 A7 §四；写门/readonly 引 A1 §六。
- **凭据 0 入仓**：v1 `credential_mode="path-ref-only"`（实测值），本文不引任何 token/凭据值。
- **引 ROADMAP 限 §一~§七**：本文仅引 §一（.1/.2）/§二；伪件误引"§十二"不作判据（ROUTE L33-34）。

---

## 七、与 ROADMAP-v2 / 前件的对应

| 内容 | 来源（实测） |
|---|---|
| 两级兼容 + "不自研 Agent Loop/记忆/Planner/Agent OS" | ROADMAP-v2 §一.1/§一.2 |
| 角色包（Role/Facts/Skills/Tools/Code/Sandbox）目录骨架 + `adapters/`、`installer/` | ROADMAP-v2 §二（实测 2026-11-07：`adapters/`、`installer/` **目录在盘**；其中的实现未建） |
| v1 adapter 返回 dict + 5 宿主能力 + readonly/credential_mode 实测 | `seeyon_host_bootstrap.py` L25/L46/L119/L133/L136–L149 |
| registry 3 组件（integration 3 / runtime 4 / udc 12 capabilities） | `core/registry.py` ComponentRegistry（本轮脚本实测） |
| Tool 清单→MCP / Skill 文件 / 角色提示词包 占位 | `TOOL-SKILL-MODULE.md` §四（本文细化） |
| v1→v2 字段映射（可复用 8 项 + UNVERIFIED 未建项） | 本文 §四（v1 dict 字段引 L136–L149 实测，对齐 A7 §四 占位） |
| 写方案 data、宿主执行写 | `seeyon_host_bootstrap.py` `capabilities.deployment_plan` + `layer.py:22` 写门（A1 §六） |
