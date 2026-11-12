# BEHAVIOR｜2小爪 Agent 行为规范

> 声明级文档。锚点全部在盘可复核；未建/未实现项逐条标 UNVERIFIED 或"未实现"。

## 1. CONFIG / CODE 能力二分

ROADMAP-v2 §三（`docs/capability/ROADMAP-v2.md` L40–L45 原文）：
- **CONFIG 能力**：Agent 产结构化声明（`{"capability":"udc.entity.create","input":{...}}`），
  平台执行。例：建实体/建字段/建页面/配权限/配路由/配菜单。
- **CODE 能力**：配置表达不了的（复杂规则/校验/转换/三方调用），必须走
  **Sandbox → Compile → Test → Validate → Execute**，禁止 Agent 直出 Java 直跑。

本切片现状：目标态 `core/capabilities/`（Capability 契约，CONFIG 型声明 + CODE 型入口，
ROADMAP-v2 §二 L25）在盘**未建 = UNVERIFIED**；`sandbox/` Global 级目录（L37）同样
**未建 = UNVERIFIED**。在盘已有的只读规划面为 registry 组件 `udc` 的 `dry_run`
能力（本轮实测，见 ROLE-CARD §2.2）与 `README.md` L83–L84 CLI dry-run
（"只生成计划，不执行写操作"）。

## 2. 只读与写门纪律

- **默认离线只读**：`bootstrap()` 默认 `allow_network=False`
  （`seeyon_host_bootstrap.py` L25 签名；L99–L100 `allow_network` 关时
  live_probe 返回 `BLOCKED`）；
- **只出数据、不出写**：`capabilities.readonly_only = True`（L146 实测）；
  五个宿主能力均"只出数据/只读，不出写"（AGENT-ADAPTER §二 L51）；
- **写步由宿主执行**：`capabilities.deployment_plan =
  "readonly data; host executes the write steps"`（L148 实测）——写方案 data，
  宿主按 steps 顺序调真实端点执行并 verify（bootstrap L122–L125 docstring）；
- **写操作一律 DENIED**：`README.md` L28（"写操作必须返回 `DENIED`，规划只能是
  `dry-run` 且不产生写操作"）与 L96–L100（写命令被拒，退出码 2）；
  当前未实现项（创建应用/修改实体/数据库/Redis/发布/部署/GraphQL 写）
  见 `README.md` L106；
- **凭据纪律**：`capabilities.credential_mode = "path-ref-only"`（L147 实测）——
  凭据仅路径引用、值 0 入仓（AGENT-ADAPTER §六 L122 同口径；本规范只写机制，
  不写任何凭据值）。

## 3. 意图路由 / 单步执行

- **意图路由**：`dispatch(intent, target)`（bootstrap L133–L134）——需求 → 路由 →
  组件执行 → 证据化结果；未注册组件/能力返回 `{"status": "UNAVAILABLE", ...}`
  （`core/registry.py` L36–L52 dispatch 边界，实测在盘）；
- **单步执行**：每个宿主可调用能力 = 单动作，产出结构化 data（含 status 字段），
  不串联多步写操作；多步部署以 `deploy_plan` 方案 data 形式整包输出、
  由宿主逐步执行（L119–L131）；
- **离线/活体分界**：任何离线输出都不能被解读为 LIVE PASS（`README.md` L28 原文）；
  活体探测需 `allow_network=True` 显式开启（L95–L116）。

## 4. 边界不扩散

- 模块推进 Module Inventory 驱动、"第一批只做 UDC 样板跑通全链，不扩散"
  （ROADMAP-v2 §五 L55–L61 原文）；
- 本角色包不实现宿主 Loop/记忆/Planner（ROADMAP-v2 §一.2 L14，见 ROLE-CARD §1）；
- 本切片只写 `core/role/` 文档，不改 `components/`、`core/facts/`、`core/tools/`、
  `core/skills/`、`docs/capability/`、`tests/` 及仓库其他路径（main ROUTE §2
  实施边界）；
- 目标态 `adapters/`、`installer/`、MCP 传输层 = 未建，UNVERIFIED
  （AGENT-ADAPTER §三 L62–L68、§五 L108–L109），本规范不代为实现。
