# adapters/hermes/ADAPTER.md｜Hermes 宿主注册件说明（S2 · H-2）

> 声明级文档。全部锚点在盘可复核；未建/未实现/目标态项逐条标 **UNVERIFIED / 未实现**，不写"已实现/已落地"。
> 凭据 0 入件：只写 `credential_file` 路径引用机制，不引任何 token/密码/值。

## 0. 本件在 A8 三层模型中的位置

- Hermes 宿主暴露形态 = **MCP tool 清单 + Skill 文件**（`docs/capability/AGENT-ADAPTER.md` §三 L60–L62：
  "Hermes（宿主=本主控链路）… `bootstrap()` 返回的 5 能力 + `capabilities.components` 直接作 tool 面；
  宿主以 Python 调用（非 MCP 传输）｜**v1 在盘（Python-native），MCP 传输层 UNVERIFIED（未建）**"）。
- 本包 3 文件 = 该暴露形态的**注册件**：
  - `Hermes-SKILL.md` = Skill 文件（升级版 v1）；
  - `MCP-TOOL-MANIFEST.md` = MCP tool 清单（声明文件，非可运行 server）；
  - 本 `ADAPTER.md` = 宿主 config 约定 + 消费方式。
- 占位细化承接 `docs/capability/TOOL-SKILL-MODULE.md` §四 L107–L111（"MCP tool 清单"占位，
  全文标 UNVERIFIED；A8 细化）。

## 1. Hermes 宿主如何消费本 adapter

（锚点 `docs/HOST-INTEGRATION.md` §3 Hermes 段 L25–L28）

1. **复制 skill**：把 `adapters/hermes/Hermes-SKILL.md` 复制到宿主 skills 目录
   （HOST-INTEGRATION §3 L26：`<HERMES_HOME>\skills\` 或仓库内直接 skill_view）。
   复制即声明级装配动作，未跑通实测 = **UNVERIFIED**。
2. **宿主工具跑 bootstrap**：宿主（Hermes）用 `terminal` / `execute_code` 跑
   `seeyon_host_bootstrap.bootstrap()`（HOST-INTEGRATION §3 L27；§1 L8–L14 初始化脚本），
   再调返回 dict 的五能力。
3. 长任务交三 Agent 文件协作，仓库只做能力面（HOST-INTEGRATION §3 L28）。

> 实现态：以上消费流程为**声明级**；MCP 传输层 / 宿主 config 实装 / 五能力真实暴露
> = 目标态未建（UNVERIFIED，AGENT-ADAPTER §三 L62、§四 L93–L96）。

## 2. 五能力逐条映射（→ Hermes tool 动作）

锚点 `seeyon_host_bootstrap.py`（返回 dict L136–L151；`capabilities` L144–L150）：

| # | Hermes tool 动作 | bootstrap 键（闭包） | 行号锚点 | 入参（签名） | 返回 / 边界 | 只读性 |
|---|---|---|---|---|---|---|
| 1 | `seeyon_dispatch` | `dispatch` | L133 | `intent, target=None` | dict：需求→路由→组件执行→证据化结果 | 只读；未注册组件/能力→`UNAVAILABLE`（registry L36–L52） |
| 2 | `seeyon_generate` | `generate` | L46 | `application_id, entity_name, attributes=None, caption=None` | dict：后端 8 类 Java 骨架 + 前端页面定义；**方法体 UNVERIFIED**（L48 docstring 原文） | 声明级、只出数据 |
| 3 | `seeyon_generate_from_requirement` | `generate_from_requirement` | L71 | `text, application_id` | dict：自然语言需求→实体模型（确定性解析）→骨架+页面；解析不可确定→`UNVERIFIED`+`unknowns`（L74–L76） | 声明级、只出数据 |
| 4 | `seeyon_live_probe` | `live_probe` | L95 | `cred_file=None`（否则用 bootstrap 的 `credential_file`） | dict：test2 只读 POST 4 端点；默认 `allow_network=False`→`BLOCKED`（L99–L100），开才实跑 | 只读；活体 |
| 5 | `seeyon_deploy_plan` | `deploy_plan` | L119 | `application_id, entity_name, attributes, caption=None, stereotype="bill", deploy_type="RELEASE"` | dict：设计态 4 步部署方案 **data**（`readonly_plan=True`，L122–L130），宿主执行写步 | 只出方案 data、不出写 |

- `capabilities` dict 实测键（bootstrap L144–L150）：
  `components`（= `sorted(agent.registry.names())`）、`readonly_only=True`、
  `credential_mode="path-ref-only"`、
  `deployment_plan="readonly data; host executes the write steps"`、
  `schema="seeyon-host-bootstrap.v1"`。
- 组件面来源（`capabilities.components`）= registry 3 组件
  `integration`/`runtime`/`udc`（`core/registry.py` ComponentRegistry；本轮 S1 抽验实测
  integration 3 / runtime 4 / udc 12 capabilities）。

## 3. 宿主 config 约定（声明级，未实装=UNVERIFIED）

| 配置项 | 约定 | 机制锚点 |
|---|---|---|
| `credential_file` | 凭据**仅路径引用**（指向仓外 JSON），值 0 入件/入仓 | bootstrap L25 签名 + L147 `credential_mode="path-ref-only"`；HOST-INTEGRATION §4 安全边界 L43 |
| `allow_network` | 活体探测开关，**默认 False（离线）**；开才实跑 | bootstrap L25（`allow_network: bool = False`）+ L99–L100；v1 dict 键 `allow_network`（L143） |
| `audit_dir` | UDC 本地审计目录（读证据面），宿主注入 | bootstrap L25 签名 + L38 装配 `UdcComponent(audit_dir=audit_dir)` |

> 实装状态：三者为 bootstrap 已支持的**声明级参数**（在盘实测签名 L25）；
> 宿主侧 config 注入实现（宿主 config 实装）= 目标态未建，**UNVERIFIED**。

## 4. 与 v1 skill 的差异 / 升级兼容口径

- 现有 `skills/seeyon-agent/SKILL.md`（**在盘 1885 B，v1 Hermes 基线**）四能力表
  （L20–L27）仅列：`dispatch` / `generate` / `live_probe` / `agent`。
- 本件 `Hermes-SKILL.md` 升级补 `generate_from_requirement`（bootstrap L71），
  构成**五能力**（A8 §二 L40 口径："5 个宿主可调用能力"）。
- 口径：
  - **升级**：能力面 4→5（补语义层入口 L71），v1 基线保留不删（不覆写原文件，只读引用）；
  - **兼容**：`agent`（原始 SeeyonAgent，三 Port 协议）保留在 skill 初始化段（v1 L27、
    HOST-INTEGRATION §2 L21）；五能力仍全部"只出数据/只读，不出写"（A8 §二 L51）；
  - 差异仅"**新增 1 个能力** + 目标态 MCP 清单"，未改任何在盘运行代码。

## 5. 边界自证（本 S2）

- 只写 `adapters/hermes/`；未改 `components/`、`core/`（含 S1 `core/role/`）、
  `skills/`（v1 只读引用）、`docs/capability/`、`tests/` 及仓库其他路径。
- 不连网、不连真实环境；凭据 0 入件（只写 `credential_file` 机制）。
- 未做真实 MCP server（`MCP-TOOL-MANIFEST.md` = 声明文件）；禁 `git push`。
