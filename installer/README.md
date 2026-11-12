# installer/README.md｜安装目标态设计·目录约定（S5 · H-6）

> 声明级设计文档。把 2小爪"角色 + 能力包"的**打包/安装面**固化为目录约定；
> **只做目录约定与安装清单，不产出安装脚本、不产出 build/package 代码**（TASK-GOAL 第 5 项口径；
> 全部实现项标 **UNVERIFIED / 未实现**，不写"已实现/已落地"）。全部锚点在盘可复核；
> 凭据 0 入件（只写路径引用机制，不引任何 token/值）；不连网、不连真实环境。

## 1. 定位

- `installer/` 承载"角色 + 能力包"的**打包/安装面**：把 `core/{role,facts,skills,tools,capabilities}`
  + 目标 `adapters/<host>/` 暴露形态打包为**可安装单元**（锚点 A8 `docs/capability/AGENT-ADAPTER.md`
  §五 L104–L105 原文）。
- 与 ROADMAP-v2 §二 目录骨架（L16–L38）的关系：`installer/` 在同级骨架 **L36**；`sandbox/` 全局级
  **L37**；暴露形态来源 = `adapters/{hermes,codex,claude-code}`（**L32–L35**）；角色/能力包核心 =
  `core/{role,facts,skills,tools,capabilities}`（**L20–L25**）；模块域 = `modules/`（L26–L31）。
  即 installer 把 `core/*`（能力包）+ 目标 `adapters/<host>/`（宿主暴露形态）打包成可安装单元。

## 2. 打包依赖（A8 §五 L106–L107）

安装单元须带三项，使宿主安装后可校验"能力定义稳定、差异走 Version Adapter"：

| 依赖 | 锚点 | 口径 |
|---|---|---|
| ① capabilities 清单 | `core/registry.py` `ComponentRegistry`（在盘；组件面 `integration`/`runtime`/`udc`） | registry 契约族（A8 §七 L134"registry 3 组件 integration 3 / runtime 4 / udc 12 capabilities"） |
| ② 证据等级标注 | A4 四层（STATIC→VERIFIED→LIVE→GENERATED，ROADMAP-v2 §四） | 逐条证据等级随件落盘（本切片各 adapter 件已标注 UNVERIFIED/未实现项） |
| ③ Canonical 版本锚 | A5 = **5.3.517**（A8 §五 L106–L107 原文 "=5.3.517"） | 版本差异走 Version Adapter，宿主不判分支（ROADMAP-v2 §一.1） |

## 3. 红线（全宿主一致，与 A8 §六 L113–L123 / HOST-INTEGRATION §4 L39–L45 同口径）

- **不自研 Agent Loop / 记忆 / Planner / Agent OS**（归宿主；ROADMAP-v2 §一.2；A8 §一 L24–L25 定稿
  口径 + §六 L115–L116）。installer 只打包/安装"角色 + 能力包"，不引入宿主 Loop。
- **凭据 0 入件**：安装面只走 `credential_file` / `--credential-file` 路径引用机制
  （`credential_mode="path-ref-only"`，bootstrap L147），**不写任何 token/密码/值**（A8 §六 L122）。
- **不连网**：打包/安装均为离线目标态动作（§五 L102"在盘未建"；活体探测另需显式开关）。

## 4. 现状声明（实现态纪律，禁虚写）

- `installer/` 目录在盘**原不存在（本件 S5 从零建）**（A8 §五 L108 实测口径"在盘不存在
  No such file/directory"；本会话本轮 `ls installer/` 实测 absent，HEAD 16a384c）。
- **【当前 2026-11-08 更正】安装实现已落地**：`installer/install.py`（12.2 KB，纯 stdlib、
  离线、幂等）已能按三宿主物化安装件。上文 §1–§3 的目标态约定由此脚本兑现；
  `INSTALL-MANIFEST.md` §2/§4 里标 UNVERIFIED 的「物化动作 / 安装后校验」两项**已实现并有测试守**。
- 仍未实现（保持 UNVERIFIED）：**宿主侧注入** —— policy / context / session 三 Port
  （`MCP-TOOL-MANIFEST.md` §3 L2③），以及 v2 宿主专属 tool schema（L2②）。
  这两项不是打包问题，是宿主运行时契约，installer 不做。

## 4.1 用法

```bash
# 只看计划，不落盘（默认行为）
python installer/install.py --host all --target <dir-outside-repo> --dry-run

# 真正物化
python installer/install.py --host all --target <dir-outside-repo> --write

# 跨机器分发：MCP 片段用 <SEEYON_AGENT_ROOT> 占位符，不写本机绝对路径
python installer/install.py --host codex --target <dir> --portable --write
```

产物（每宿主 2 件，另加 `MANIFEST.json` 记录字节 + sha256）：

| 宿主 | 指令件 | MCP 注册片段 |
|---|---|---|
| hermes | `skills/seeyon-agent-hermes/SKILL.md` | `mcp_servers.yaml`（贴进 `~/.hermes/config.yaml` 顶层 `mcp_servers:`） |
| codex | `AGENTS.md`（H1 按 §3 重写） | `config.toml`（`[mcp_servers.seeyon]`） |
| claude-code | `CLAUDE.md`（H1 按 §3 重写） | `.mcp.json`（`{"mcpServers": {...}}`） |

> **为什么 Hermes 装到 `seeyon-agent-hermes/` 而不是 `seeyon-agent/`**（2026-11-08 实测踩到）：
> 仓库里 `skills/seeyon-agent/SKILL.md` 是**另一个 skill**（v1 `name: seeyon-agent` / `1.0.0`），
> 而 `adapters/hermes/Hermes-SKILL.md` 的 frontmatter 是 `name: seeyon-agent-hermes` / `2.0.0`，
> 且用 `base:` 显式声明 v1 为「read-only reference」。两者是**两个 skill，不是两个版本**。
> 早先把 v2 物化进 `skills/seeyon-agent/`，到宿主侧就变成「目录叫 A、skill 叫 B」，
> 并和仓库同名目录撞车（Hermes `skill_view` 直接报 `Ambiguous skill name`）。
> 现由 `test_skill_目录名必须等于_frontmatter_name` 守住。

安全边界（`tests/test_installer.py` 12 用例守）：拒绝在仓库内物化（撞写保护清单）；
默认 dry-run；覆盖非本工具产物需 `--force`；过程态标签不随安装件传播；凭据 0 入件。

## 5. 边界自证（本件 S5）

- 只新增 `installer/`（2 文件）；未改 `components/`、`core/`（含 `core/role/`/`core/facts/`/
  `core/skills/`）、`skills/`、`docs/capability/`（只读引用 A8 §五/§六/§七、ROADMAP §二）、`tests/`、
  `seeyon_cli.py`、`seeyon_host_bootstrap.py`、已交付的 `adapters/{hermes,codex,claude-code}/`
  （全部只读，含 S3 件 H1 残留——按 INSTALL-MANIFEST 安装态规则归一，**不就地改**）。
- 未写任何 basename ∈ {`agents.md`,`claude.md`,`soul.md`,`.cursorrules`} 的文件（§0.3）；
  未旁路写规范名；凭据 0 入件；禁 `git push`。
