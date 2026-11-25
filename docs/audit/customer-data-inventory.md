# 客户 / 本机环境标识清单（发行边界盘点）

**结论先说：这个仓库有两条用途，之前混在一起了。**

1. **装到别人机器上的工具** —— `git clone` / `irm|iex` 那一份。它只该有机制、骨架、占位符。
2. **我们自己的工作区** —— 联调环境、客户证据、反编译产物、一次性脚本。

盘点时间：2026-11-24。判定口径：真实域名、真实 appId、凭据、kubeconfig 名、本机目录。

## 三个桶

| 桶 | 路径 | 现状 | 规则 |
|---|---|---|---|
| **A 装机执行面** | `adapters/ components/ config/ installer/ providers/ core/config_env.py scripts→(见B)` + README/INSTALL/CHANGELOG | **0 命中** | 零容忍，`tests/test_distribution_hygiene.py` 守住 |
| **B 知识库与开发资产** | `core/facts/`、`docs/`、`definitions/`、`scripts/` | **133 个文件**含 LIVE 环境细节 | 只准减不准增（测试卡基线） |
| **C 本机覆盖层** | `config/environments.local.yaml`、`~/.xiaozhua/logs.yaml`、`.hermes/` | 已在 `.gitignore`，且 `git rm --cached` | 永不进 git |

## 口径（2026-11-24 定）

**历史资产留着没问题，前提是它不参与发行/执行。** 判据两条：

1. **可执行代码**（被 import、被安装、被脚本调用）→ 换环境必须不出错 → 代码里零环境标识，
   AST 级测试 `test_no_hard_identifiers_in_executable_code` 守住（docstring 不算代码）。
2. **纯引用资产**（审计报告、事实库证据、样例 JSON）→ 可以留，但登记在案、只准减。

## A 桶：这次真正修掉的

| 问题 | 处理 |
|---|---|
| `components/logs/loki.py` 文档串写死客户 datasource 名、`search()` 默认 `namespace="lowcode-test"` | 默认值全部清空，文档改 `<env-name>`；工具不认识任何具体环境 |
| `xiaozhua_host_bootstrap.logs_search` 默认 `env="test2"`、`namespace` 默认客户命名空间 | 默认空串，缺 env 时报「必须指定 env」并列出本机已配置的键 |
| MCP 工具描述里写 test2/uat/prod | 改成「使用时自定的环境名」 |
| `config/logs.example.yaml` 带客户 datasource 名 | 全占位符 |
| CHANGELOG 0.2.6 写了真实主机/命名空间/pod/日志样例 | 重写为通用口径 |
| `config/environments.yaml` 含真实本地凭据路径、appId、租户、桶名、k8s namespace | 拆成 **骨架**（入库）+ **`environments.local.yaml`**（本机、gitignore）；读取时深合并（`core/config_env.py`） |
| `.hermes/plans/*`（研发笔记，含 configtest2 等） | `git rm --cached` + gitignore，文件留在本机 |
| `config/udc-semantics-evidence.local.json`（名字就写 local） | 同上 |

## B 桶：还没动，需要单独立项

| 目录 | 命中文件 | 典型内容 | 建议 |
|---|---|---|---|
| `docs/` | 110 → **98** | 审计报告里的真域名、pod 名、跳板机命令 | 净迁出 35 份零引用现场报告（第 1 批 47 份中 entity-field-matrix 20 份回仓；第 2 批再迁 8 份，契约/规则 2 份回仓）（见 `_attic_pending/README.md` 台账）；剩余 98 份先留（被文档/代码引用，需逐处标「已迁出至」再动） |
| `core/facts/` | ~92 | LIVE 证据格直接贴 appId、`kubectl --kubeconfig=configtest2`、pod 名 | 事实库只留机制与结论，LIVE 明细引用仓外 `customer-evidence` |
| `definitions/` | 8 | 客户 DTO 定义（`com.seeyon.datamigration<appId>.…`） | 移到仓外样例库，仓库只留 1 份脱敏示例 |
| `scripts/` | 5 → **0** | 脚本把真 appId 写成 `default=` | 已改为 `--app-id required` / `XIAOZHUA_APP_ID`；生成物 `random-biz-evidence/` 移出仓库 |

### 已迁出运行代码的两处

* `components/udc/event_listener_constraints.py` 的 `FILTER_MQ_PLANE_LIVE` /
  `CONNECTOR_DTO_REGISTRY_DB` / `CONNECTOR_DTO_REGISTRY_LIVE` —— 三个 LIVE 证据常量只在测试里用，
  已搬到 `core/facts/udc/event-listener/connector-live-evidence.json`，模块只留机制常量 +
  `live_evidence()` 读接口。
* 4 个一次性脚本的 `default=<真appId>` —— 改成必填参数/环境变量，缺了直接报错，
  换环境不会静默打到我们自己的租户。

这 133 个文件不静默放过：`tests/test_distribution_hygiene.py::test_facts_evidence_hits_do_not_grow`
把 133 当基线（2026-11-25 收紧，原 200/216），新增一个就红。

## 为什么要分桶，而不是一把清完

### 分桶结论（2026-11-25 收敛）

原先的 `LEGACY` 六条收敛到两条例外：

- `components/udc/{event_listener,attribute_expression,menu}_constraints.py`、
  `components/udc/microflow/gates.py` 的命中**全在注释/docstring 里**（`LIVE（test2, app=…）`），
  已改成占位 id，不涉及可执行字符串，行为零变化；
- `core/facts/batch-modules-20260925.md` 已无命中；
- `components/udc/attribute_expression_constraints.py` **保留原值**：它的 docstring 是
  `test_module_records_the_live_app_id_and_entity` 断言的 LIVE 证据锚点（模块必须记录自己对哪个
  应用实测过），换占位就失去可复核性；
- 本盘点表自身（必须写清「哪些标识曾在哪个文件」）。

真正需要 `config/` 引用键改造的（连接器默认值这类**可执行**常量）此前已改完，
见上面「已迁出运行代码的两处」。

## 自检

```bash
pytest tests/test_distribution_hygiene.py -q     # 4 passed
pytest tests/test_logs_loki.py -q                # 10 passed（全离线）
```

规则一句话：**代码只认引用键，值只有两种去处 —— 本机 local 覆盖层，或仓外证据根。**