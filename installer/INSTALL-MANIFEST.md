# installer/INSTALL-MANIFEST.md｜安装清单（S5 · H-6）

> 声明级清单（目标态设计）。**全部安装动作 = 目标态设计，无在盘可运行安装脚本；
> 实现一律 UNVERIFIED / 未实现**（A8 §五 L108–L109"仅目标态约定，UNVERIFIED"、§六 L117–L118）。
> 每项列 [源件 → 安装态目标 → 校验]；锚点在盘可复核；凭据 0 入件；不写可运行安装/打包代码。

## 1. 安装项清单（三宿主，源件在盘字节 = 本轮实测值）

| 宿主 | 源件（adapters/ 在盘） | 安装态目标 | 校验 |
|---|---|---|---|
| **Hermes** | `adapters/hermes/Hermes-SKILL.md`（4425 B，`747e95e5…`） | `<hermes-home>/skills/xiaozhua-agent-hermes/SKILL.md`（宿主 skills 目录；本机示例路径 `<HERMES_HOME>\skills\`，锚 HOST-INTEGRATION §3 Hermes 段 L25–L28） | v1 基线 `skills/xiaozhua-agent/SKILL.md`（1885 B，`在盘在仓`）为对照；安装件=v1 升级版五能力 skill |
| **Hermes（随附）** | `adapters/hermes/ADAPTER.md`（6199 B，`5280920a…`）、`adapters/hermes/MCP-TOOL-MANIFEST.md`（4252 B，`5f9934a9…`） | 随 Hermes 注册件分发（声明件，非宿主加载件） | 声明级内容可复核；MCP 传输层 UNVERIFIED |
| **Codex** | `adapters/codex/AGENTS.template.md`（6968 B，`90b2ae54…`） | `<target-repo>/AGENTS.md`（安装态规范名，§2 物化） | 物化后目标目录出现 `AGENTS.md`；H1 按 §3 安装态生成规则 |
| **Codex（随附）** | `adapters/codex/MCP-TOOL-MANIFEST.md`（5389 B，`4c4aeba1…`） | 随 Codex 注册件分发（声明件） | 声明级内容可复核；MCP 传输层 UNVERIFIED |
| **Claude Code** | `adapters/claude-code/CLAUDE.template.md`（7367 B，`890ca675…`） | `<target-repo>/CLAUDE.md`（安装态规范名，§2 物化） | 物化后目标目录出现 `CLAUDE.md`；H1 按 §3 安装态生成规则 |
| **Claude Code（随附）** | `adapters/claude-code/MCP-TOOL-MANIFEST.md`（5142 B，`19739d5e…`） | 随 CC 注册件分发（声明件） | 声明级内容可复核；MCP 传输层 UNVERIFIED |

> 角色包核心（安装件内携带的 capabilities 清单/证据等级/版本锚）= `core/{role,facts,skills,tools,
> capabilities}` + `core/registry.py` ComponentRegistry（ROADMAP-v2 §二 L20–L25、A8 §五 L104–L107，
> 见 `installer/README.md` §1/§2）。

## 2. 模板 → 规范名物化映射表（§0.3 裁决落地，必含）

| 模板件（适配器内，在盘） | 安装态规范名（物化目标） | 物化动作 | 实现态 |
|---|---|---|---|
| `adapters/codex/AGENTS.template.md` | `<target-repo>/AGENTS.md` | installer 按模板内容写出规范名文件 + 生成安装态 H1（§3 规则） | **【当前 2026-11-08】已实现**：`installer/install.py`，`tests/test_installer.py::test_H1_按安装态规则重写` |
| `adapters/claude-code/CLAUDE.template.md` | `<target-repo>/CLAUDE.md` | 同上 | **【当前 2026-11-08】已实现**：同上 |

**为何用模板件名（登记，非静默替换）**：宿主指令件规范名 `AGENTS.md` / `CLAUDE.md` 命中 Hermes
写保护 fail-closed 清单 `{agents.md, claude.md, soul.md, .cursorrules}`（basename 大小写不敏感、
任意目录；无人批准通道即拒——ROUTE §0.3 读守卫源码实证）。故**适配器内只存 `.template.md`；
适配器内不得存在规范名文件**（本清单交付时实测：`find adapters -iname AGENTS.md -o -iname
CLAUDE.md …` 全空）。规范名只在安装态由 installer 物化到目标仓库，模板件不落在宿主指令加载
路径上，无"静默植入未来会话指令"的持久化风险。

## 3. H1 标注口径归一（承 ROUTE §0.3 H1 残留观察，必含；不就地改 S3 件）

**统一写法（宿主指令件 H1 模板作者期）**：标**模板件路径** + 说明**安装态物化目标名**；
**不得含 STAGED/待放行等过程态标签**。
**安装态 H1 生成规则**：物化时按规范名重写 H1 = 规范名（如 `<target-repo>/AGENTS.md`）+
Canonical 版本锚（5.3.517）+ schema 锚（`xiaozhua-host-bootstrap.v1`），**覆盖模板作者期 H1**。

据此归一既有件（对照事实 = 本轮实测首行）：
- **S3 反例**：`adapters/codex/AGENTS.template.md` 首行现含"【STAGED · 待 main 放行 AGENTS.md
  写保护】"过程态标签（H-3 暂存语境残留，ROUTE §0.3 已登记）。**处置 = 以本条"安装态 H1 生成规则"
  归一句径：物化出 `<target-repo>/AGENTS.md` 时 H1 按规范名 + 版本锚重写，STAGED 残留仅存于
  模板作者期件、不随安装态传播**；**不就地改写 S3 已 PASS 件**（保其已记录 sha 绑定 `90b2ae54…` 不破）。
- **S4 合规对照**：`adapters/claude-code/CLAUDE.template.md` 首行 =
  `# adapters/claude-code/CLAUDE.template.md｜Claude Code 宿主注册件（S4 · H-5）`——直接合规
  （标模板件路径、无过程态标签；auditor H-5 VERDICT 正向记录），S3 件为其反例。

## 4. 安装后校验项（目标态设计，执行 UNVERIFIED）

1. **capabilities 清单一致**：安装单元携带的 `capabilities.components`（registry 契约族
   `integration`/`runtime`/`udc`，bootstrap L145 实测）与源 registry 一致。
2. **证据等级标注齐全**：随件 UNVERIFIED/未实现项标注不缺（A4 四层口径）。
3. **Canonical 版本锚**：安装单元版本锚 = **5.3.517**（A8 §五 L106–L107；差异走 Version Adapter）。
4. **规范名指令件落地**：安装后目标目录内出现规范名指令件（`AGENTS.md` / `CLAUDE.md`），
   且目标目录**无 `.template` 残留副本**（模板件不随安装落地）；H1 符合 §3 安装态生成规则。
5. 凭据面校验：安装面只含 `credential_file` 路径引用机制（`path-ref-only`），0 凭据值
   （A8 §六 L122 同口径）。

## 5. 现状声明（实现态纪律，禁虚写）

- ~~本清单 = **目标态设计（声明级）**：无任何可运行安装脚本~~ **【当前 2026-11-08 更正】**
  `installer/install.py` 已在盘（12.2 KB，纯 stdlib、离线、幂等），§2 的物化动作与 §4 的
  5 项校验均已实现，由 `tests/test_installer.py` 12 用例守。上文原始结论保留作历史。
- 仍未实现（保持 UNVERIFIED）：**宿主侧注入** —— policy / context / session 三 Port
  （`MCP-TOOL-MANIFEST.md` §3 L2③）与 v2 宿主专属 tool schema（L2②）。
  这两项属宿主运行时契约，不在打包面内。
- 未改任何禁改路径（含 S1–S4 产物与 `core/facts/`）；本清单新增文件 = `installer/README.md` +
  `installer/INSTALL-MANIFEST.md` 共 2 件。
