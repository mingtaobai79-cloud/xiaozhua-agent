---
name: seeyon-agent-hermes
description: "Use when driving Seeyon UDC development tasks from Hermes: dispatch requirements, generate backend/frontend skeletons, generate from natural-language requirement, run readonly live probes against test2, and produce design-time deploy plans. Upgraded 5-capability Hermes skill (v2)."
version: 2.0.0
base: "skills/seeyon-agent/SKILL.md (v1 baseline, 1885 B, read-only reference)"
---

# Seeyon Agent（Hermes 宿主接入 · 升级版五能力）

Seeyon Agent 是**嵌入宿主的组件**，不是独立 agent（ROADMAP-v2 §一.2；HOST-INTEGRATION L3）。
通过 `seeyon_host_bootstrap.bootstrap()` 装配，宿主（Hermes/CC/Codex）注入 context/session/policy。

> 本件 = v1 skill（`skills/seeyon-agent/SKILL.md`，在盘 1885 B）的**升级**：能力面 4→5，
> 补 `generate_from_requirement`（bootstrap L71）；v1 基线保留不删。
> **本 skill = 宿主接入的声明级说明**（怎么在 Hermes 里用能力面）。
> **实现态（2026-11-08 实测）**：MCP 传输层**已实装 14 个 tool**——`adapters/mcp/server.py`，
> 协议 `protocolVersion=2024-11-05`。14 = 原有 5 个能力（dispatch / generate /
> generate_from_requirement / live_probe / deploy_plan）+ **9 个 metadata 构造器**
> （list_page_schema / detail_page_schema / microflow_create_body / index_body / enum_body /
> enum_item_body / dto_body / event_body / filter_plan_body）—— 后 9 个 `bootstrap()` 一直有，
> 但 2026-11-08 前没接进 MCP，宿主看不见。
> Hermes 侧 MCP **已注册**（`config.yaml` L776 `mcp_servers.seeyon`），本 skill `readiness_status: available`。
> **仍未实现** = v2 宿主专属 schema + 宿主注入三 Port（详见 `adapters/hermes/MCP-TOOL-MANIFEST.md`）。

## 初始化（一次）

（锚点 `docs/HOST-INTEGRATION.md` §1 L8–L14；bootstrap L25）

```python
import sys; sys.path.insert(0, r"<SEEYON_AGENT_ROOT>")
from seeyon_host_bootstrap import bootstrap
host = bootstrap()                                                        # 离线（默认 allow_network=False）
host = bootstrap(credential_file=r"<仓外凭据路径>", allow_network=True,  # 活体 test2
                 audit_dir=r"<UDC 本地审计目录>")
```

## 五个能力（v2，升级补 generate_from_requirement）

| 能力 | 用途 | 边界 |
|---|---|---|
| `host["dispatch"](intent, target)` | 需求→路由→组件→证据化结果 | 只读（bootstrap L133） |
| `host["generate"](app_id, entity, attrs)` | 后端 8 类 Java 骨架 + 前端页面定义 | 声明级，方法体 UNVERIFIED（L46/L48） |
| `host["generate_from_requirement"](text, app_id)` | 自然语言需求→实体模型（确定性解析）→骨架+页面 | **新增**；解析不可确定→`UNVERIFIED`+`unknowns`（L71/L74–L76） |
| `host["live_probe"](cred_file)` | test2 4 端点只读 POST 双发 | 默认关，`allow_network=True` 才联网（L95/L99–L100） |
| `host["deploy_plan"](app_id, entity, attrs, ...)` | 设计态 4 步部署方案 data（建实体→建属性→建页→RELEASE 构建） | 只出方案 data，宿主执行写步（L119/L122–L130） |
| `host["agent"]` | 原始 SeeyonAgent（宿主注入 context/session/policy） | 三 Port 协议（v1 L27；HOST-INTEGRATION §2 L21，保留兼容） |

> 说明：`agent` 为宿主可注入本体（v1 基线项），与 5 个能力闭包并行；
> 能力面 5 = dispatch/generate/generate_from_requirement/live_probe/deploy_plan（A8 §二 L40）。

## 红线（与 HOST-INTEGRATION §4 安全边界一致）

1. 写操作（create/update/delete/publish/deploy）一律 **DENIED**（policy gate），不绕过、不写生产（§4 L42）。
2. 凭据仅路径引用（`credential_mode="path-ref-only"`，bootstrap L147），token 明文 0 入产物/会话/git；凭据文件放仓外（§4 L43）。
3. STATIC/UNVERIFIED 结论不得报成 LIVE PASS；UNVERIFIED 方法体不臆造（§4 L44）。
4. `generate_from_requirement` 解析不可确定时须如实返回 `UNVERIFIED` + `unknowns`（bootstrap L74–L76），不臆造实体模型。
5. token 有时效（test2 operator token ~19h 窗口，v1 skill L34），临期从 HUMAN 处取新值刷新凭据文件（值不入库）。

## 测试

（锚点 `docs/HOST-INTEGRATION.md` §5 L48–L52）

```bash
cd <SEEYON_AGENT_ROOT>
python -m pytest tests -q          # 离线全绿（本机为 python，无 python3）
python scripts/run_live_readonly.py --credential-file <path> --allow-network   # 活体 4 端点
python scripts/run_multi_live_test.py --allow-network --credential-file <path>  # 三类多轮
```

> **测试通过数口径**：**禁把仓内文档里的裸通过数当契约**。一律以运行
> `python -m pytest tests -q` 的**实测输出**为准。当前在盘可引来源（不同时点/不同命令，
> **均非契约**）：`README.md` L30 记 `1512 passed`（文档现值，与本机实跑不符）；
> `docs/HOST-INTEGRATION.md` §5 L49 记 `361 passed`（`.venv` 口径，历史值）；
> 2026-09-26 本切片收口记录 `375 passed`；**2026-10-19 实测 `1490 passed / 1 failed / 21 skipped`**
> （失败项 = `tests/udc/test_dynamic_register_channel.py::test_evidence_is_recomputable_by_the_tool_byte_for_byte`，
> 根因 scratch 依赖 `sup_v2` 被 24h 清理，属 udc-semantics 线环境依赖，已登记 BLOCKED，
> 不在本切片可写路径）。通过数是环境指纹，不是契约。

> 本 skill 为**声明级文件**：复制/挂载到宿主 skills 目录后，宿主以 Python 调用能力面。
> **传输层** = `adapters/mcp/server.py` 已实装（可 stdio 直跑）。
> **【当前 2026-11-08 更正】宿主侧注册也已落地**：`~/.hermes/config.yaml` 顶层 `mcp_servers.seeyon`
> 已注册（stdio，`command` = 仓内 venv python，`args` = `adapters/mcp/server.py`），
> 五个 tool 在宿主侧可直接调用；Codex / Claude Code 侧由 `installer/install.py` 生成注册片段
> （`config.toml` / `.mcp.json`），本机实测两者均 `✔ Connected`。
> **仍未实现**（保持 UNVERIFIED）：v2 宿主专属 tool schema、policy/context/session 三 Port 注入。
> 判定口径：`adapters/hermes/MCP-TOOL-MANIFEST.md` §3 L1（已实装）/ L2（②③ 未实现，① 已落地）。
