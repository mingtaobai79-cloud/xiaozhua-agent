# adapters/claude-code/CLAUDE.template.md｜Claude Code 宿主注册件（S4 · H-5）

> 声明级文档（CC 侧注册/指令文件）。**安装态物化为 `<target-repo>/CLAUDE.md`**（由 installer S5 落，
> 见 ROUTE §0.3 / §3；本件模板件名 `CLAUDE.template.md`，规范名 `CLAUDE.md` 被 Hermes 写保护
> fail-closed 拦截故此处不可直接产出）。全部锚点在盘可复核；未建/未实现/目标态项逐条标
> **UNVERIFIED / 未实现**，不写"已实现/已落地"。凭据 0 入件：只写路径引用机制，不引任何 token/值。

## 1. 身份与铁律

- 2小爪 Agent = **嵌入宿主（Claude Code）的组件，不是独立 agent**（`docs/HOST-INTEGRATION.md` L3
  原文；ROADMAP-v2 §一.2 L12–L14："2小爪 Agent = 可安装的 **Agent 角色 + 能力包**…不自研 Agent
  Loop / 记忆 / Planner / Agent OS"）。
- **CC 提供 Loop（在仓库根自动读 CLAUDE.md + tool use Bash），2小爪 只出 data**（A8
  `docs/capability/AGENT-ADAPTER.md` §一 L24–L25 定稿口径 + §三 CC 暴露形态 L64；
  HOST-INTEGRATION §3 CC 段 L31："CC 在仓库根自动读取本文件；tool use 用 Bash…"）。
- 三级定位同口径：`core/role/ROLE-CARD.md` §1（S1 已建）。

## 2. 能力面（bootstrap 五能力 + capabilities）

（锚点 `seeyon_host_bootstrap.py`，返回 dict L136–L151；`capabilities` L144–L150）

| 能力 | 行号 | 入参 | 返回 / 边界 | 只读性 |
|---|---|---|---|---|
| `dispatch` | L133 | `intent, target=None` | 需求→路由→组件执行→证据化结果 | 只读 |
| `generate` | L46 | `application_id, entity_name, attributes=None, caption=None` | 后端 8 类 Java 骨架 + 前端页面定义；方法体 UNVERIFIED（L48） | 只读出数据 |
| `generate_from_requirement` | L71 | `text, application_id` | 自然语言需求→实体模型→骨架+页面；不可确定→`UNVERIFIED`+`unknowns`（L74–L76） | 只读出数据 |
| `live_probe` | L95 | `cred_file=None`（否则用 bootstrap `credential_file`） | test2 4 端点只读 POST；`allow_network=False`→`BLOCKED`（L99–L100），开才实跑 | 只读活体 |
| `deploy_plan` | L119 | `application_id, entity_name, attributes, caption=None, stereotype="bill", deploy_type="RELEASE"` | 设计态 4 步部署方案 **data**（L122–L130），宿主执行写步 | 只出方案 data |

`capabilities` dict 实测键（L144–L150）：`components`（= registry 3 组件 `integration`/`runtime`/
`udc`）、`readonly_only=True`、`credential_mode="path-ref-only"`、
`deployment_plan="readonly data; host executes the write steps"`、`schema="seeyon-host-bootstrap.v1"`。
组件面来源 = `core/registry.py` ComponentRegistry（在盘）。

## 3. 调用方式（CC 特有，区别于 Codex 的 shell 调 op-execute）

（锚点 `docs/HOST-INTEGRATION.md` §3 CC 段 L30–L33 原文；三脚本在盘实测）
- **CC 在仓库根自动读取本指令文件**（L31 原文）；**tool use 用 Bash 跑**：
  - `pytest`（离线验收，`python -m pytest tests -q`；**通过数以实测为准，禁把仓内文档裸数当契约**，
    当前实测 1490 passed / 1 failed / 21 skipped，红项属 scratch 依赖的环境项，见 §8）；
  - `scripts/run_live_readonly.py --credential-file <path> --allow-network`（活体 4 端点，脚本在盘 **3851 B**）；
  - `scripts/run_multi_live_test.py --allow-network --credential-file <path>`（三类多轮，脚本在盘 **7455 B**）。
- **不是** Codex 那套 shell 调 `seeyon_cli op-execute`（那属 HOST-INTEGRATION §3 Codex 段 L34–L37，
  S4 不取；两段为并列的两个宿主接入要点）。
- 长任务/多轮打法：交 `core/skills/udc-entity-dev.md`（B3，见 §6），宿主 Bash 逐步执行。

> 实装状态：上述调用面为**在盘脚本 + 声明级约定**；**CC 侧真实挂载/注册 = 未实现**
> （A8 §三 L64、§四 L93–L96；§8）。注意区分：**MCP 传输层本身已实装**（`adapters/mcp/server.py`，
> 19 passed），未实现的仅是 CC 侧把它注册进 `.mcp.json`/`claude mcp add` 的接入配置。

## 4. config / 凭据约定（CC 特有，精确声明，禁虚写）

| 项 | 精确约定 | 机制锚点 |
|---|---|---|
| 凭据载体 | **CC 宿主侧**用环境变量 `SEEYON_CRED_FILE` 指向仓外凭据 JSON（HOST-INTEGRATION L32 原文） | 机制原文 = `docs/HOST-INTEGRATION.md` L32；**传输层已读取该 env**（`adapters/mcp/server.py` L178 `os.environ.get("SEEYON_CRED_FILE")`），仅作路径载体、值 0 入件 |
| 凭据传递 | **CC 宿主据 `SEEYON_CRED_FILE` 定位仓外凭据文件路径，再把该路径传给能力面 `credential_file`（bootstrap 入参）/ `--credential-file`（CLI 入参）——`path-ref-only`** | bootstrap L25/L96（`credential_file` 入参）；`credential_mode="path-ref-only"`（L147）；seeyon_cli.py L191；MCP 侧 `server.py` L178 |
| 关键澄清（2026-10-19 更正） | **旧表述"2小爪 能力面不直接读该 env / 全仓仅 L32 一处、无 Python 代码读取"已作废**——实测 `adapters/mcp/server.py` L178 确有读取（作为 MCP 传输层凭据路径载体）。**仍未实现的是**：CC 宿主侧自己把该 env 落到 `credential_file` 的注入工序 | `grep -rn SEEYON_CRED_FILE` 实测命中：`docs/HOST-INTEGRATION.md` L32、`adapters/mcp/server.py` L178、`adapters/mcp/DESIGN.md` L107/L174、`adapters/mcp/STATUS.md` L20 |
| token 纪律 | token 明文 0 入 CLAUDE.md/代码/仓/会话；凭据文件放仓外（`*_credential.json` gitignore 防线） | HOST-INTEGRATION §4 L43 |
| 离线开关 | 活体需显式 `--allow-network`（默认关=离线只读） | seeyon_cli.py L196；bootstrap `allow_network` 默认 False（L25） |

> 实装状态：`SEEYON_CRED_FILE` **传输层读取已实装**（`server.py` L178）；**CC 宿主侧注入工序未实现**
> （§8）；本件只写机制描述，不引值。

## 5. 红线（与 HOST-INTEGRATION §4 安全边界 L39–L45 一致）

1. 写操作（create/update/delete/publish/deploy）一律 **DENIED**——policy gate **拒绝，非提示性**
   （§4 L42 原文；`seeyon_cli.py` L183 `udc-execute` "writes are denied"，退出码 2，`README.md` L96–L100）。
2. token 明文 0 入产物/git/会话；凭据文件放仓外（§4 L43；本件只写 `SEEYON_CRED_FILE`/`credential_file`
   路径引用机制，不写任何凭据值）。
3. STATIC/UNVERIFIED 不得报成 LIVE PASS；UNVERIFIED 方法体不臆造（§4 L44；`README.md` L28）。
4. 默认离线只读；活体需显式 `--allow-network` + 凭据路径引用（§4 L41）。
5. 不自研宿主 Loop/记忆/Planner（§1 铁律；ROADMAP-v2 §一.2 L14）。

## 6. 与 B3 打法的关系（只读引用，不重写）

- `core/skills/udc-entity-dev.md`（**在盘 6936 B，B3 打法**，"在 UDC 建一个单据实体"5 段串联，
  宿主解耦 A7 §一 L7–L8 原文"适用宿主 hermes/codex/claude-code via adapter"）是 CC 侧**任务打法来源**；
  本件**只做宿主注册/调用约定**（身份/五能力/CC 调用/凭据/红线），**不重写打法**；打法逐段以 B3 为准。
  B3 sha `45a05379…`（只读引用，未改写）。

## 7. v1 基线声明（禁虚写）

- **CC 无在盘 v1 基线**：`skills/` 下只有 Hermes（`seeyon-agent/SKILL.md`，1885 B）；`core/skills/`
  只有 B3 打法（`udc-entity-dev.md`）。本件 = **CC 宿主首个注册件（从零建）**，不是 S2 那种"v1 升级"；
  **不写"CC 已有 v1 基线/已存在"**。

## 8. 实现态声明（本件 S4；S7 分层更正）

- 本 2 文件（`CLAUDE.template.md` + `MCP-TOOL-MANIFEST.md`）= 声明级。
- **已实装（非本件产物，只引用）**：`adapters/mcp/server.py` MCP stdio 传输层（12835 B，
  sha256 `d20b47e8…`，commit `3595d7e`，`pytest tests/test_mcp_server.py -q` = **19 passed**，
  `protocolVersion=2024-11-05`，五 tool，凭据 path-ref-only，默认离线）。
- **仍未实现**：① CC 侧 MCP 注册/接入配置（`.mcp.json` / `claude mcp add` + `CLAUDE.md` 装载）
  ② v2 CC 专属 tool schema ③ 宿主注入 policy/context/session 三 Port ④ `SEEYON_CRED_FILE`
  → `credential_file` 的 CC 宿主侧注入工序。
- **环境依赖（BLOCKED，不在本切片可写路径）**：全量 `pytest tests -q` 实测
  **1490 passed / 1 failed / 21 skipped**；失败项
  `tests/udc/test_dynamic_register_channel.py::test_evidence_is_recomputable_by_the_tool_byte_for_byte`
  依赖 `<HERMES_HOME>/cache/scratch/sup_v2`（scratch 24h 清理，jar 成员清单 94 jar / 1170 class
  无在盘可复现来源，证据件按字节判等 ⇒ 不可重建），属 udc-semantics 线，已登记 BLOCKED。
- 不改 `components/`、`core/`（含 `core/role/`/`core/facts/`/`core/skills/`）、`skills/`、
  `docs/capability/`、`tests/`、`seeyon_cli.py`、`seeyon_host_bootstrap.py`、`adapters/mcp/**`、
  已交付的 `adapters/hermes/`、`adapters/codex/`；凭据 0 入件；禁 `git push`；不写可运行 MCP server 代码。
