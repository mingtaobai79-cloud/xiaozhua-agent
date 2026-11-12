# Seeyon Agent — Agent-Host Integration Guide

Seeyon Agent 是嵌入宿主（Hermes / Claude Code / Codex）的组件，不是独立 agent。
宿主通过一个初始化脚本获得四个能力；本文是所有宿主接入的唯一契约。

## 1. 初始化脚本（唯一入口）

```python
sys.path.insert(0, r"<SEEYON_AGENT_ROOT>")
from seeyon_host_bootstrap import bootstrap

host = bootstrap()                                   # 离线（默认）
host = bootstrap(credential_file=<path>, allow_network=True)  # 活体 test2
```

## 2. 能力面（bootstrap 返回 dict）

当前范围提醒：`bootstrap()` 未暴露 `MicroflowPipeline`；MCP 工具白名单也不含该流程。
因此 P5 构造阶段的 `advisories` 虽可在本地报告中序列化，不能认为已由宿主展示。
P5 包含保存、发布、构建等有副作用的阶段，不得直接作为只读入口注册或自动运行；
如需对外暴露，须先拆出无副作用的调用边界并实测授权与结果透传。

以下为部分能力（完整键以实际 `bootstrap()` 返回值为准）：

`microflow_create_body` 仅生成本地请求体，不代表节点受支持。未收录的节点会在本地
`unknowns` 中标记 UNVERIFIED；`check_schema_body` 会移除该字段，调用方必须在转换前读取。
该提示不阻断提交，也不是写入授权；矩阵不完整、版本不匹配和运行兼容性仍需单独验证。

- `dispatch(intent, target)` — 需求归一化 → 组件路由 → **组件内只读 action** → 证据化结果
- `generate(app_id, entity_name, attributes, caption)` — 后端 8 类 Java 骨架 + 前端页面定义
- `live_probe(cred_file?)` — test2 只读 POST 4 端点双发（默认 BLOCKED）
- `agent` — SeeyonAgent 本体；宿主可用自有 context/session/policy 重建（三 Port 协议）

### 2.1 任务路由与发现（`core/intent_actions.py`）

`dispatch` 现在分两步：域路由（`SeeyonAgent.route`）之后按意图表在**组件已登记能力**
里选 action，未命中才用域默认（udc → `inspect_application`，其他 → `inspect`）。
因此「微流程节点怎么配」命中 `inspect_microflow` 而不是笼统的应用级报告。
返回 dict 的 `action` 字段即路由决策（组件未自带时由入口补上）。

宿主发现面：`host["agent"].intent_index()` → `{组件: {action: [关键词]}}`，
只列组件 `capabilities()` 里真实存在的 action，空 dict 表示该域暂无细分意图。

边界：意图表是白名单不是 NLU；混合域请求仍返回 `unknown` / `UNAVAILABLE`（不猜）；
关键词边界对 ASCII 生效（`microflows` 不命中 `microflow`）；中文按子串。
当前仅 udc 域登记了细分 action，runtime / integration 仍只有域默认。

## 3. 各宿主接入要点

### Hermes（本机）
- 复制 `skills/seeyon-agent/SKILL.md` 到 `<HERMES_HOME>\skills\`（或仓库内直接 skill_view）；
- 宿主工具里用 terminal/execute_code 跑 bootstrap + 能力调用；
- 长任务交给三 Agent 文件协作（seeyon-old session），仓库只做能力面。

### Claude Code
- CC 在仓库根自动读取本文件；tool use 用 Bash 跑 pytest / scripts/run_live_readonly.py / scripts/run_multi_live_test.py；
- CC 侧凭据：环境变量 `SEEYON_CRED_FILE` 指向仓外凭据 JSON，**绝不把 token 写进 CLAUDE.md/代码**。

### Codex（OpenAI）
- Codex 用 shell 调 CLI 面即可：
  `python -m seeyon_cli op-execute --operation udc.page_info.select_host_and_only_page --application-id <app> --credential-file <path> --allow-network`
- Codex 侧同样凭据走环境变量/路径引用。

## 4. 安全边界（全宿主一致）

1. 默认离线只读；联网需显式 allow_network=True + 凭据路径引用
2. 写操作（create/update/delete/publish/deploy）一律 DENIED —— policy gate 拒绝，非提示性
3. token 明文 0 入产物/git/会话；凭据文件放仓外（gitignore 已加 *_credential.json 防线）
4. STATIC/UNVERIFIED 不得报成 LIVE PASS；UNVERIFIED 方法体不臆造

## 5. 验收命令（三宿主通用）

```bash
.venv\Scripts\python.exe -m pytest tests -q   # 361 passed
.venv\Scripts\python.exe run_live_readonly.py --credential-file <path> --allow-network
.venv\Scripts\python.exe run_multi_live_test.py --allow-network --credential-file <path>
```
