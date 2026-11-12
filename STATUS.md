# STATUS — 仓库状态索引

> 历史会话收口台账已归档至 [docs/ledger/STATUS-2026H2.md](docs/ledger/STATUS-2026H2.md)（只追加，不回改）。
> 本文件只保留当前指针：最新收口记录看台账末尾。

## 当前快照（2026-10-19，S7 声明件对齐后实测）

- HEAD 基线：`b7ea61a`（本切片 S7 只改文档，未提交；工作树含并行会话脏改，见协作 ROUTE §0.2 方法）
- registry：51 条 UdcOperationContract
- **测试（如实记录，不再以"全绿"为唯一门槛）**：`.venv/Scripts/python.exe -m pytest tests -q` →
  **1490 passed / 1 failed / 21 skipped**，RC=1（2026-10-19 实测，一次运行 ≈47s；`--tb=no` 复跑同结果）。
  失败项 `tests/udc/test_dynamic_register_channel.py::test_evidence_is_recomputable_by_the_tool_byte_for_byte`
  ——依赖 `<HERMES_HOME>/cache/scratch/sup_v2`（scratch 24h 清理，jar 成员清单 94 jar / 1170 class
  无在盘可复现来源，证据件按字节判等 ⇒ 不可重建），属 **udc-semantics 线环境依赖 BLOCKED**，
  已定位到本切片之外的独立分支并登记，**不在本切片可写路径**（禁改 `tests/`、禁改 components/tools）。
- **通过数不是契约**：此前本文件写 "395 tests 全绿"、`README.md` L30 写 `1512 passed`、
  `docs/HOST-INTEGRATION.md` §5 L49 写 `361 passed`、协作侧 2026-09-26 记录 `375 passed`——
  四者是不同时点的环境指纹，均不作契约；**一律以实测为准**（同型教训见 `docs/ledger/LOG-udc-semantics-PROGRESS-20261014-20261016.md` 第十八轮）。
- registry / UDC 契约域：12/13 已扫（runtime 差分扫描待做）
- 客户证据：仓库外 `<EVIDENCE_ROOT>/xiaozhua-customer-evidence/`（见 config/environments.yaml customer_evidence_root）

## S7 声明件与在盘实现对齐（2026-10-19，implementer 自证记录）

**动机**：三份 `adapters/*/MCP-TOOL-MANIFEST.md` 仍写"MCP server 传输层未实现 = UNVERIFIED"，
而 `adapters/mcp/server.py` 已在盘可运行（19 passed）⇒ 声明件与仓内事实相反（**欠报已实现部分**，
同属证据纪律缺陷，双向）。另有三处把 `README.md` L30 的裸通过数当契约。

**本轮实测基线（implementer 独立复算，非转述）**

- `adapters/mcp/server.py`：12835 B，sha256 `d20b47e8635b8fb0639902fb311e18549c87b03d2edcf38f97ce03798a5e179e`，
  commit `3595d7e`（2026-09-28 22:54:34 +0800）。
- `pytest tests/test_mcp_server.py -q` → **19 passed**，RC=0。
- stdio 实跑（`python adapters/mcp/server.py < frames`，RC=0）：`initialize` → `protocolVersion=2024-11-05`
  + `serverInfo xiaozhua-mcp/0.1.0`；`tools/list` → 恰 5 工具；`tools/call(xiaozhua_dispatch)` → 离线
  `status=UNVERIFIED`；`tools/call(xiaozhua_live_probe)` 无凭据 → `status=SKIPPED`（≠ PASS）。
- 全量 `pytest tests -q` → 1490 passed / 1 failed / 21 skipped（见上）。

**改动（6 文件，全部允许写路径内）**

| 文件 | 改动要点 |
|---|---|
| `adapters/hermes/MCP-TOOL-MANIFEST.md` | 新增 §3 实现态分层（L1 已实装事实表 + L2 三项未实现）、§4 已知未实现/环境依赖、§5 边界自证；§0/§2 口径同步 |
| `adapters/codex/MCP-TOOL-MANIFEST.md` | 同上（L1 段落与另两份逐字一致；L2 ① 换 Codex 宿主入口） |
| `adapters/claude-code/MCP-TOOL-MANIFEST.md` | 同上；另更正 `XIAOZHUA_CRED_FILE` 旧表述（"无 Python 代码读取"已作废，实为 `server.py` L178 读取） |
| `adapters/hermes/Hermes-SKILL.md` | 头注与末节改为分层事实；通过数口径改为"以实测为准"+四来源并列 |
| `adapters/claude-code/CLAUDE.template.md` | §3 测试口径去 395；§4 凭据行更正；§8 分层重写（已实装/未实现/环境依赖三块） |
| `core/role/EVIDENCE-DISCIPLINE.md` | §2 VERIFIED 行去 395；§3 增"双向纪律"（禁欠报）；新增 §3.1"测试通过数不得当契约" |

**未触碰自证**：`adapters/mcp/**`（只引用）、`adapters/codex/AGENTS.template.md`（sha256 仍
`90b2ae54e62c7a292fdfc6f6c67f38e2c9a06f015df6f60740ee2938f70e14dd`）、`components/`、
`core/facts/`、`core/tools/`、`core/skills/`、`docs/capability/`、`tests/`。凭据 0 入件；未连网；未 push。

## 纪律

- 新收口记录追加到 docs/ledger/ 下按月分文件，不再堆本文件
- 客户场景内容禁止回填本仓库
