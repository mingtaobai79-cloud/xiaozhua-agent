# Seeyon Agent 目录约定

> 2026-10-20 清理后确立。目的是让"这是资产还是垃圾"一眼可判。

## 根目录（21 项）

### 库（源码，不含文档）

| 目录 | 职责 | 说明 |
|---|---|---|
| `components/` | **实现层** | 九域的约束模型、构造器、平台操作层。109 py |
| `core/` | 装配壳 + 事实库 | `core/*.py` 是薄内核（agent 73 行）；`core/facts/` 是按域一目录一格的事实库（106 md） |
| `providers/` | 外部适配 | MySQL 真实只读客户端、CDP 客户端、HTTP 只读、K8s 快照 |
| `adapters/` | 宿主接入 | Hermes / Claude Code / Codex / MCP 的接入模板与清单 |
| `config/` | 环境常量 | 引用式配置（值走环境变量或仓外文件，永不入库） |
| `fixtures/` | 测试夹具 | 默认探针输入 |

### 入口

| 文件 | 用途 |
|---|---|
| `seeyon_cli.py` | CLI 主入口（capabilities / op-execute / generate 等） |
| `seeyon_host_bootstrap.py` | 宿主装配（`bootstrap()`） |
| `scripts/run_live_readonly.py` | 活体只读 4 端点 |
| `scripts/run_multi_live_test.py` | 三类多轮活体 |
| `http.json` `integration.json` `runtime.json` | 运行时配置（被代码读取） |
| `artifact-inventory.manifest.json` | 产物清单 |

### 文档

| 路径 | 职责 |
|---|---|
| `README.md` `STATUS.md` | 工程说明与状态 |
| **`docs/README.md`** | **文档树根入口**：顶层 10 份规则文档 + 7 个子目录 + 「我要找 X 该去哪」查找表 |
| `docs/capability/README.md` | **目标架构入口**：ROADMAP-v2 + A1–A8 八件套 + STATUS 的索引（10 份 / 103,894 B） |
| `docs/operation-contracts/udc/<域>/` | **九域操作契约**（应用/实体/菜单/规则/流程/BI/栏目/设置/角色）。`microflow/` 与 `setting/` 已有子目录入口 |
| `docs/audit/artifacts/` | **权威证据归档**——反编译产物、字节码、活体抓包。**只增不删** |
| `docs/audit/<专题>/` | 审计报告 |
| `docs/plans/hermes/` | 计划文档 |
| `docs/audit/deferred/_deferred/` | 暂缓实现（v0.2 才启用） |
| `skills/seeyon-agent/SKILL.md` | 宿主侧 skill 定义 |
| `installer/` | 对外发布说明 |

### 工具

| 目录 | 职责 | 维护级别 |
|---|---|---|
| `tools/core/` | 正式工具（被代码/文档引用） | 维护 |
| `tools/audit/` | 审计脚本（原 `aud/` 合并而来） | 维护 |
| `tools/one-off/` | 一次性取证脚本（589 个） | **不维护**，仅作取证方法参考 |
| `tools/cdp/` `tools/jars/` `tools/expression/` | 专项工具与资源 | 维护 |
| `_attic_pending/mfdump-root/` | 原 `tools/_mfdump/`（8 份真实 dataSchema 抓包）。零代码引用，含客户流程实例 → 2026-11-07 移入收容区，见该目录 README | 待清理 |
| `_attic_pending/acceptance-suite-root/` | 原仓库根 `验收/` + `验收_min/`（41 份客户流程 schema）。索引已抽到 `docs/audit/microflow-acceptance-suite/` | 待清理 |

### 临时区

| 路径 | 规则 |
|---|---|
| `scratch/` | **临时区，不入 git**。内容 24h 会被清理。需要长期保留的证据必须先归档到 `docs/audit/artifacts/` |
| `node_modules/` `.venv/` `__pycache__/` | 本地产物 |

## 三条硬规则

1. **事实与代码分离**
   结论写在 `core/facts/<域>/`（九段式事实格）或 `docs/operation-contracts/udc/<域>/`；
   可执行断言写在 `components/udc/<域>_constraints.py`。
   两者必须互相引用——`tests/udc/test_enum_domain_registration.py` 这类测试就是防它们脱节的闸门。

2. **证据必须可复核**
   文档里写的每一行 `path:line` 引用，其文件必须在 `docs/audit/artifacts/` 里有副本。
   指向 `scratch/` 的引用视为**失效引用**——scratch 会清空，证据不能放在那里。

3. **只读优先，写需显式授权**
   `providers/` 的数据库与浏览器通道默认只读；平台写操作必须显式传
   `WriteScope`（应用白名单 + 操作白名单 + 次数上限），失败即停不重试。
   见 `components/platform_operations/write_scope.py`。

## 判断新文件该放哪

```
是平台行为的事实/契约？   → core/facts/<域>/ 或 docs/operation-contracts/udc/<域>/
是可执行的约束/断言？       → components/udc/<域>_constraints.py
是可复用的取证工具？       → tools/core/
是一次性的探针脚本？       → tools/one-off/
是活体抓包/字节码证据？     → docs/audit/artifacts/
是临时中间产物？           → scratch/（别提交）
```
