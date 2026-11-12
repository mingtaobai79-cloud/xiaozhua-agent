# EVIDENCE-DISCIPLINE｜xiaozhua Agent 证据纪律

> 声明级文档。锚点全部在盘可复核；未建/未实现项逐条标 UNVERIFIED 或"未实现"。

## 1. 四层事实体系（STATIC → VERIFIED → LIVE → GENERATED）

ROADMAP-v2 §四（`docs/capability/ROADMAP-v2.md` L47–L53 原文）：

```
STATIC（源码/javap）→ VERIFIED（测试/调用）→ LIVE（真实环境）→ GENERATED（仅假设）
```

- **防 Agent 胡编的机制核心**（§四 标题原文，L47）；
- **GENERATED_HYPOTHESIS 永不进入 VERIFIED_RULE**（L52 原文）；
- 现有 registry 的 VERIFIED_STATIC_BYTECODE / OBSERVED / UNVERIFIED 体系直接归并
  （L53 原文）——registry 在盘（`core/registry.py`），其证据标签体系归并方向已定。

## 2. 层级判定纪律

| 层级 | 含义 | 判定纪律 |
|---|---|---|
| STATIC | 源码/javap 静态证据 | 须给文件+行号锚点（本包 4 文档引用均按此） |
| VERIFIED | 测试/调用实证 | 测试结论以 `python -m pytest tests -q` **实测**为准；**禁把仓内文档里的裸通过数当契约**（当前实测 1490 passed / 1 failed / 21 skipped，见 §3.1）；只读调用输出须可复跑 |
| LIVE | 真实环境 | `README.md` L24–L28：live 测试默认不执行；活体探测需 `allow_network=True`
  显式开启（bootstrap L25/L95–L116）；"任何离线输出都不能被解读为 LIVE PASS"（L28） |
| GENERATED | 仅假设 | 一律标 GENERATED_HYPOTHESIS，**永不进 VERIFIED_RULE**（§四 L52） |

`README.md` L14 同口径：Runtime/Integration 的 `FACT` 只表示本地 snapshot/provider
读取成功，不代表 test2、Pod、HTTP、数据库等真实系统已验证。

## 3. 声明 ≠ 实现

- 声明级文档（如本包 4 文件、ROADMAP-v2、AGENT-ADAPTER 各节）描述的是
  **目标态规范**；在盘是否存在须 `ls`/脚本实测，不凭文档转述；
- **双向纪律（2026-10-19 补，S7）**：声明必须与在盘事实一致——既禁"虚写已实现"，也禁"欠报已实现"。
  实例：本包早期文本写"MCP 传输层未建 UNVERIFIED"，而 `adapters/mcp/server.py`（12835 B，
  sha256 `d20b47e8…`，commit `3595d7e`）已在盘且 `tests/test_mcp_server.py` **19 passed**；
  该表述已按 S7 更正为分层事实（传输层已实装 / 宿主接入未实现）。**欠报同样违反证据纪律。**
- 未实现项逐条标 **UNVERIFIED 或"未实现"**，禁写"已实现/已落地"：
  - 三宿主 **MCP 注册/接入配置**、**v2 宿主专属 tool schema**、**宿主注入 policy/context/session
    三 Port** = 未实现（A8 §四 L83/L85；S7 §3 L2）；
  - 目标态 `installer/` 安装脚本、`core/capabilities/`、`sandbox/` = 未实现，UNVERIFIED
    （`installer/` 仅目录约定件在盘）；
  - `generate` 方法体 UNVERIFIED（bootstrap L48 docstring 原文）；
  - 写面全部未实现（`README.md` L106）；
- 凭据 0 入件：本纪律只写凭据机制（`credential_mode="path-ref-only"`，
  bootstrap L147 实测），不引任何 token/密码/值（AGENT-ADAPTER §六 L122）。

### 3.1 测试通过数不得当契约（2026-10-19 S7 更正）

- **旧表述作废**：本节早期把 `README.md` L30 的**裸通过数当成测试契约**——那只是某个时点的环境指纹，
  与实测不符（**同型错**记于归档 `docs/ledger/LOG-udc-semantics-PROGRESS-20261014-20261016.md` 第十八轮）。
- **正确口径**：一律写"以 `python -m pytest tests -q` 实测为准"，或如实并列来源（不同时点 /
  不同命令，**均非契约**）：
  - `README.md` L30 现记 `1512 passed`（仓内文档现值，与本机实跑不符）；
  - `docs/HOST-INTEGRATION.md` §5 L49 记 `361 passed`（`.venv` 口径，历史值）；
  - 2026-09-26 本切片收口记录 `375 passed`；
  - **2026-10-19 实测 `1490 passed / 1 failed / 21 skipped`**（失败项
    `tests/udc/test_dynamic_register_channel.py::test_evidence_is_recomputable_by_the_tool_byte_for_byte`
    依赖 `<HERMES_HOME>/cache/scratch/sup_v2`，scratch 24h 清理后不可复现、不可重建；
    属 udc-semantics 线环境依赖 BLOCKED，不在本切片可写路径）。
- 判据：**通过数是环境指纹（时点/命令/依赖态），不是契约**；契约只能是"当前实测 + 失败项归属登记"。

## 4. 本包（core/role/）实现态声明

- 本包 4 文档 = **声明级文档**（STATIC 级在盘证据，可 `ls`/`wc`/哈希复核）；
- 本包描述的宿主暴露、adapter 目录、installer 安装脚本全部为**目标态未实现**；
  （注：`adapters/mcp/` 传输层已实装，属另一条独立线，非本包的产物与主张范围，见 §3 双向纪律实例）；
- 本包未新造定位/阶段/验收，全部引在盘锚点（ROADMAP-v2 §一~§四、
  AGENT-ADAPTER §一/§二/§三/§四、`xiaozhua_host_bootstrap.py`、
  `core/registry.py`、`README.md`）。
