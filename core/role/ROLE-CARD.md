# ROLE-CARD｜xiaozhua Agent 角色卡

> 声明级文档。锚点全部在盘可复核；未建/未实现项逐条标 UNVERIFIED 或"未实现"。

## 1. 身份定位

xiaozhua Agent = 可安装的 **Agent 角色 + 能力包**（Role / Facts / Skills / Tools / Code / Sandbox），
经 Adapter 进入已有宿主（Hermes / Codex / Claude Code）。
**不自研 Agent Loop / 记忆 / Planner / Agent OS**（原文锚点：
`docs/capability/ROADMAP-v2.md` §一.2，L12–L14：
"xiaozhua Agent = 可安装的 **Agent 角色 + 能力包**…不自研 Agent Loop / 记忆 / Planner / Agent OS"；
同口径复述于 `docs/capability/AGENT-ADAPTER.md` §一 L16、§六 L115）。

两级兼容（ROADMAP-v2 §一，L8–L14）：
- **xiaozhua 版本兼容（对内）**：客户当前仓库为 Canonical，能力定义稳定，差异走 Version Adapter，
  Agent 不自行判断版本分支；
- **Agent Host 兼容（对外）**：角色包经 Adapter 进入不同宿主，宿主可换、能力包定义稳定。

## 2. 能力面

### 2.1 v1 宿主可调用 5 能力（在盘实测）

入口 `xiaozhua_host_bootstrap.py` `bootstrap()`（L25），返回 dict 实测 L136–L149：
`dispatch` / `generate` / `generate_from_requirement` / `live_probe` / `deploy_plan`。
抽验实测（本轮脚本，2026-09-25）：顶层键 8 个
（`agent, allow_network, capabilities, deploy_plan, dispatch, generate,
generate_from_requirement, live_probe`）；`capabilities` 子 dict =
`{"components": ["integration", "runtime", "udc"], "readonly_only": True,
"credential_mode": "path-ref-only",
"deployment_plan": "readonly data; host executes the write steps",
"schema": "xiaozhua-host-bootstrap.v1"}`——与 `docs/capability/AGENT-ADAPTER.md` §二
L37–L46 表一致。
- `dispatch`（L133–L134）：意图路由（需求 → 路由 → 组件执行 → 证据化结果）；
- `generate`（L46）：实体+属性 → 后端 8 类 Java 骨架 + 前端页面定义（**方法体 UNVERIFIED**，
  L48 docstring 原文）；
- `generate_from_requirement`（L71）：自然语言需求 → 实体模型 → 骨架+页面；
- `live_probe`（L95）：活体只读探测，默认 `allow_network=False` 时返回
  `{"status": "BLOCKED", ...}`（L99–L100），开才实跑；
- `deploy_plan`（L119）：设计态 4 步部署方案 **data**（只出方案，宿主执行写步，L122–L125）。

### 2.2 registry 组件面（在盘实测）

`core/registry.py` `ComponentRegistry`（L6，注册/派发边界 L36–L52）。
本轮抽验实测 3 组件（bootstrap 装配 L38）：
- `integration` 3 capabilities（`trace_http`, `inspect_logs`, `compare_database_snapshot`）
- `runtime` 4 capabilities（`inspect_pod`, `inspect_route`, `inspect_metadata`, `inspect_logs`）
- `udc` 12 capabilities（`inspect_application`…`dry_run`，含 `dry_run` 规划面）

组件面口径同 AGENT-ADAPTER §二 L42（"实测 3 组件"）与 §四 L80。
SPI 组件：未实现或注册（`README.md` L11），不列入组件面。

### 2.3 宿主暴露形态（目标态，UNVERIFIED）

Hermes = MCP tool 清单 + 能力包 / Codex = Skill 文件 / Claude Code = 角色提示词包
（AGENT-ADAPTER §三 L60–L68）：v1 仅 Hermes Python-native 在盘；
MCP 传输层、Skill 文件、角色提示词包、`adapters/{hermes,codex,claude-code}/` 目录
**均目标态未建 = UNVERIFIED**（§三 L62–L68、§四 L93–L96）。

## 3. 与宿主的关系

- **宿主提供 Loop/记忆/Planner，xiaozhua 出 data**（AGENT-ADAPTER §一 L24–L25 定稿口径）：
  UDC 是 xiaozhua Agent 的组件，不是独立总 Agent；Context、Session、Tool 和 LLM 可由宿主注入
  （`README.md` L108 原文）；
- 写步分工：`capabilities.deployment_plan = "readonly data; host executes the write steps"`
  （bootstrap L148 实测）——agent 只出只读/方案 data，写步由宿主执行；
- 宿主三选一可换，角色包定义不变（两级兼容模型，ROADMAP-v2 §一）；
- `bootstrap()` 入口 L25 支持宿主注入 `credential_file` / `allow_network` / `audit_dir`
  三个参数，宿主侧注入口径见 `core/agent.py` 三个 Port（bootstrap L27 注释）。
