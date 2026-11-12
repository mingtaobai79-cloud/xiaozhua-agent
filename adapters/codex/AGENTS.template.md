# adapters/codex/AGENTS.md｜Codex CLI 宿主注册件（S3 · H-3）【STAGED · 待 main 放行 AGENTS.md 写保护】

> 声明级文档（Codex CLI 侧 AGENTS 指令文件）。全部锚点在盘可复核；未建/未实现/目标态项逐条标
> **UNVERIFIED / 未实现**，不写"已实现/已落地"。凭据 0 入件：只写路径引用/环境变量机制，不引任何 token/值。
> 本件 = Codex 侧宿主注册/调用约定；任务打法来源 `core/skills/udc-entity-dev.md`（B3，只读引用，不重写）。

## 1. 身份与铁律

- Seeyon Agent = **嵌入宿主（Codex）的组件，不是独立 agent**（`docs/HOST-INTEGRATION.md` L3 原文；
  ROADMAP-v2 §一.2 L12–L14："Seeyon Agent = 可安装的 **Agent 角色 + 能力包**…不自研 Agent Loop /
  记忆 / Planner / Agent OS"）。
- **Codex 提供 Loop / 记忆 / Planner，Seeyon 只出 data**（A8 `docs/capability/AGENT-ADAPTER.md`
  §一 L24–L25 定稿口径 + §三 L63 Codex 暴露形态；宿主 Loop/记忆/Planner 归宿主，不进 Seeyon 契约）。
- 三级定位同口径：`core/role/ROLE-CARD.md` §1（S1 已建）——两级兼容 + 不自研宿主能力。

## 2. 能力面（bootstrap 五能力 + CLI 面）

### 2.1 五能力（锚点 `seeyon_host_bootstrap.py`，返回 dict L136–L151）

| 能力 | 行号 | 入参 | 返回 / 边界 | 只读性 |
|---|---|---|---|---|
| `dispatch` | L133 | `intent, target=None` | 需求→路由→组件执行→证据化结果 | 只读 |
| `generate` | L46 | `application_id, entity_name, attributes=None, caption=None` | 后端 8 类 Java 骨架 + 前端页面定义；方法体 UNVERIFIED（L48） | 只读出数据 |
| `generate_from_requirement` | L71 | `text, application_id` | 自然语言需求→实体模型→骨架+页面；不可确定→`UNVERIFIED`+`unknowns`（L74–L76） | 只读出数据 |
| `live_probe` | L95 | `cred_file=None` | test2 4 端点只读 POST；`allow_network=False`→`BLOCKED`（L99–L100），开才实跑 | 只读活体 |
| `deploy_plan` | L119 | `application_id, entity_name, attributes, caption=None, stereotype="bill", deploy_type="RELEASE"` | 设计态 4 步部署方案 **data**（L122–L130），宿主执行写步 | 只出方案 data |

`capabilities` dict 实测键（L144–L150）：`components`（= registry 3 组件 `integration`/`runtime`/
`udc`）、`readonly_only=True`、`credential_mode="path-ref-only"`、
`deployment_plan="readonly data; host executes the write steps"`、`schema="seeyon-host-bootstrap.v1"`。

### 2.2 CLI 面（锚点 `seeyon_cli.py`，Codex 用 shell 调，HOST-INTEGRATION §3 Codex 段 L34–L37）

- `python -m seeyon_cli capabilities`（**L174**）— 列只读能力面。
- `python -m seeyon_cli op-execute`（**L185–L196**）— 只读 UDC 操作经 PlatformOperationLayer
  （离线默认）；参数：
  `--operation`（required，op id）/ `--application-id`（required）/ `--entity-id` / `--entity-name` /
  `--gateway-url` / `--credential-file`（JSON：`credential_ref`→HTTP headers 映射，default None）/
  `--credential-ref`（default `cli-default`）/ `--principal`（default `cli`）/ `--timeout`（default 15.0）/
  `--evidence-out`（落脱敏 OperationResult JSON）/ `--allow-network`（`store_true`，default 关 = 离线只读）。
- 写面（对照用）：`python -m seeyon_cli udc-execute`（**L183**，"writes are denied"，写一律 DENIED，
  退出码 2，`README.md` L96–L100 同口径）。

## 3. 调用方式（Codex 侧）

（锚点 `docs/HOST-INTEGRATION.md` §3 Codex 段 L34–L37 原文命令）
- **shell 调 CLI**：`python -m seeyon_cli op-execute --operation <op> --application-id <app>
  --credential-file <仓外路径> --allow-network`（L36 原文示意）；
- **Python 调 bootstrap**：`sys.path.insert(0, repo_root)` → `from seeyon_host_bootstrap import bootstrap`
  → `bootstrap(...)` 取五能力（HOST-INTEGRATION §1 L8–L14）。
- Codex 侧凭据同样走**环境变量/路径引用**（HOST-INTEGRATION §3 L37 原文："凭据走环境变量/路径引用"）。
- 长任务/多轮打法：交 `core/skills/udc-entity-dev.md`（B3，见 §5），宿主 shell 逐步执行。

## 4. config / 凭据约定（声明级，宿主实装=UNVERIFIED）

| 项 | 约定 | 机制锚点 |
|---|---|---|
| 凭据 | 仅**路径引用/环境变量**（`--credential-file <仓外 JSON>` + `--credential-ref`），token 明文 0 入仓/入会话/入产物 | `seeyon_cli.py` L191–L192；bootstrap `credential_mode="path-ref-only"`（L147）；HOST-INTEGRATION §4 L43 |
| 离线开关 | `--allow-network` 默认**关**（离线只读）；开才活体 GET | `seeyon_cli.py` L196（`store_true`）；bootstrap `allow_network` 默认 False（L25） |
| 证据落盘 | `--evidence-out` 落**脱敏** OperationResult JSON（不含凭据值） | `seeyon_cli.py` L195 |

> 实装状态：以上为 CLI/bootstrap **在盘已支持**的参数（签名实测）；Codex 宿主侧 config 注入实现
> = 目标态未建，**UNVERIFIED**（A8 §四 L93–L96）。

## 5. 与 B3 打法的关系（只读引用，不重写）

- `core/skills/udc-entity-dev.md`（**在盘 6936 B，B3 打法**，"在 UDC 建一个单据实体"5 段串联：
  需求解析→deploy_plan→宿主执行 4 步→回读验证→异常处置）是 Codex 侧**任务打法来源**；
  其对宿主解耦（B3 L7–L8 原文：适用宿主 `hermes/codex/claude-code` via adapter，"宿主不是映射终点"）。
- 本件（AGENTS.md）**只做宿主注册/调用约定**（身份/五能力/CLI/config/凭据/红线），
  **不重写打法**；打法逐段以 B3 为准（B3 内已逐段锚 LIVE/STATIC 实据 + UNVERIFIED 登记）。

## 6. 红线（与 HOST-INTEGRATION §4 安全边界一致）

1. 写操作（create/update/delete/publish/deploy）一律 **DENIED**（policy gate，`udc-execute` 返回退出码 2）；
   不绕过、不写生产（§4 L42；`README.md` L96–L100）。
2. token 明文 0 入产物/git/会话；凭据文件放仓外（§4 L43；本件只写 `credential_file` 路径引用机制，
   不写任何凭据值）。
3. STATIC/UNVERIFIED 不得报成 LIVE PASS；UNVERIFIED 方法体不臆造（§4 L44；`README.md` L28）。
4. 默认离线只读；活体需显式 `--allow-network` + 凭据路径引用（§4 L41）。
5. 不自研宿主 Loop/记忆/Planner（§1 铁律；ROADMAP-v2 §一.2 L14）。

## 7. 实现态声明（本件 S3）

- 本 2 文件 = 声明级（AGENTS 指令 + MCP 清单草案）；Codex 侧注册/挂载 = 目标态未建，**UNVERIFIED**。
- MCP server 传输层 / 宿主 config 实装 / 五能力真实暴露给 Codex = 未建，UNVERIFIED
  （A8 §三 L63、§四 L93–L96；`MCP-TOOL-MANIFEST.md` 标同）。
- 不改 `components/`、`core/`（含 `core/role/`/`core/facts/`/`core/skills/`）、`skills/`、
  `docs/capability/`、`tests/`、`seeyon_cli.py` 及仓库其他路径；凭据 0 入件；禁 `git push`。
