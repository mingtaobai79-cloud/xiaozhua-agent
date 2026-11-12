# STATUS｜adapters/mcp（mcp-server 实装线）

> ## 【当前 2026-11-08 更正】工具面 5 → **14**
>
> 本文下半部分（2026-09-28 时点）写的「五工具」是**当时**的实装面。此后发现：
> `xiaozhua_host_bootstrap.bootstrap()` 一直返回 **15 个能力**，而 `server.py` 的 `TOOL_KEYS`
> 只接了 5 个 —— **9 个 metadata 构造器在宿主侧完全看不见**：
>
> | 新增 tool | bootstrap 键 | 实测产出 |
> |---|---|---|
> | `xiaozhua_list_page_schema` | `list_page_schema` | 4,612 B（`pageType=SEARCH_LIST` + 列定义 + `unverified_fields`） |
> | `xiaozhua_detail_page_schema` | `detail_page_schema` | 2,966 B（`UdcForm SINGLE` + 子页） |
> | `xiaozhua_filter_plan_body` | `filter_plan_body` | 1,150 B（`body` + `note`） |
> | `xiaozhua_microflow_create_body` | `microflow_create_body` | 467 B（`dataSchema` 字符串化） |
> | `xiaozhua_dto_body` | `dto_body` | 402 B |
> | `xiaozhua_enum_body` | `enum_body` | 266 B |
> | `xiaozhua_event_body` | `event_body` | 206 B |
> | `xiaozhua_enum_item_body` | `enum_item_body` | 197 B（`itemValue`/`parentId` 槽位保留） |
> | `xiaozhua_index_body` | `index_body` | 57 B |
>
> schema 仍由 `_schema_from_callable()` 的 inspect 签名自动生成，**没有手抄**；
> 只对两处做 override：`microflow_create_body.data_schema`（`Any` 会被兜底成 `string`，实际吃 dict）、
> `index_body.field_ids`（声明 integer 数组）。
>
> 守它的测试：`tests/test_mcp_metadata_tools.py`（26 用例，含「逐个真调」参数化 +
> 「构造器不许声称已写入」）。`tests/test_mcp_server.py` 从 20 → 20（断言集改为
> `EXPECTED_TOOL_NAMES` 驱动，不再写死 5）。
>
> 变异验证（三条全红）：删一个 `TOOL_KEY` → 7 红；工具名重复 → 7 红；
> 去掉 `data_schema` override → 3 红。

> 更新：2026-09-28。设计件 S1（DESIGN.md，PASS dedupe mcp-s1-verdict）→ S2 实现本轮收口。
> 边界遵守：只写 `adapters/mcp/**` + `tests/test_mcp_server.py`；bootstrap 本体 0 改动；凭据 0 入件。

## 产出

| 文件 | 内容 |
|---|---|
| `server.py` | 手写最小 JSON-RPC 2.0 over stdio（零外部依赖，纯 stdlib）。method 白名单：`initialize`/`tools/list`/`tools/call`（+`notifications/initialized` 静默）；protocolVersion `2024-11-05`；错误码 -32601/-32602/-32700/-32603 |
| `DESIGN.md` | S1 设计件（182 行，四节齐全，S1 判据链在 collaboration.json events） |
| `tests/test_mcp_server.py` | 三层矩阵 19 用例（DESIGN §4）：工具列表 4 + 离线调用 7 + 错误路径 6 + 握手/通知/stdio 端到端 2 |

## 五工具（schema 自动生成，两条源：inspect 签名 + deployment.py 常量）

`xiaozhua_dispatch` / `xiaozhua_generate` / `xiaozhua_generate_from_requirement` / `xiaozhua_live_probe` / `xiaozhua_deploy_plan`
- 枚举非手抄：`stereotype←STEREO_TYPES`、`deploy_type←DEPLOY_TYPES`、`dataType←DATATYPES`（import 常量，非复制）
- `attributes[]` 元素 schema（name 必填/caption?/dataType? enum+推断说明）
- 离线默认传导：`XIAOZHUA_ALLOW_NETWORK` 未设=False → `bootstrap(allow_network=False)` → `live_probe` 返回 BLOCKED/SKIPPED（绝不 PASS）
- 凭据 path-ref-only：`XIAOZHUA_CRED_FILE` 环境变量或 `live_probe(cred_file=)` 参数，值 0 入件

## 验收证据（实测，非转述）

1. **测试绿**：`pytest tests/test_mcp_server.py -q` → **19 passed**；全仓 `pytest -q` → **395 passed**（376+19，文档计数已同步 8 文件，文档契约测试 PASS）
2. **server 可起**（stdio 实跑 3 帧）：initialize → protocolVersion=2024-11-05 + serverInfo xiaozhua-mcp/0.1.0；tools/list → 恰 5 工具名集正确；tools/call(xiaozhua_dispatch unknown) → `status=UNAVAILABLE`（离线路径，非崩溃）
3. **写门不破**：无任何写工具暴露；`deploy_plan` 只返回 `readonly_plan=True` 方案 data

## 设计偏差如实登记（实码语义优先于设计稿措辞）

- DESIGN §4.2 预写 `call_live_probe_offline_blocked` 断言无 cred 也 BLOCKED —— 实码 `bootstrap L96-98`：**无 cred 先返回 SKIPPED**（先于 allow_network 判断）。测试按实码改为双路径断言（SKIPPED≠PASS + cred+offline=BLOCKED），语义不变（0 网络、绝不 PASS）。
- `generate` 入参键 = `type`（NormalizedAttribute 签名），非 design 举例的 `dataType`；MCP schema 的 `attributes` 元素按实码 `type` 生成（DESIGN §2.1 的 inspect 反射路径自动保证，非手抄错）。
- 中文需求句无实体名 → `generate_from_requirement` 返回 `status=UNVERIFIED` + schema 标注（合法离线路径）。

## 未做 / 后续（不虚写完成）

- 宿主实接（Hermes/Claude Code/Codex 配 MCP server 指向本 stdio）未做 —— 属宿主配置面，代码侧可起证据已足。
- `resources`/`prompts`/`logging` 扩展未实现（DESIGN §1 兜底声明，本切片按 TASK-GOAL 最小协议面达标）。
