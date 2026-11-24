# 客户 / 本机环境标识清单（发行边界盘点）

**结论先说：这个仓库有两条用途，之前混在一起了。**

1. **装到别人机器上的工具** —— `git clone` / `irm|iex` 那一份。它只该有机制、骨架、占位符。
2. **我们自己的工作区** —— 联调环境、客户证据、反编译产物、一次性脚本。

盘点时间：2026-11-24。判定口径：真实域名、真实 appId、凭据、kubeconfig 名、本机目录。

## 三个桶

| 桶 | 路径 | 现状 | 规则 |
|---|---|---|---|
| **A 装机执行面** | `adapters/ components/ config/ installer/ providers/ core/config_env.py scripts→(见B)` + README/INSTALL/CHANGELOG | **0 命中** | 零容忍，`tests/test_distribution_hygiene.py` 守住 |
| **B 知识库与开发资产** | `core/facts/`、`docs/`、`definitions/`、`scripts/` | **216 个文件**含 LIVE 环境细节 | 只准减不准增（测试卡基线） |
| **C 本机覆盖层** | `config/environments.local.yaml`、`~/.xiaozhua/logs.yaml`、`.hermes/` | 已在 `.gitignore`，且 `git rm --cached` | 永不进 git |

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
| `docs/` | ~110 | 审计报告里的真域名、pod 名、跳板机命令 | 拆「平台机制文档（可发行）」与「客户现场报告（仓外）」 |
| `core/facts/` | ~92 | LIVE 证据格直接贴 appId、`kubectl --kubeconfig=configtest2`、pod 名 | 事实库只留机制与结论，LIVE 明细引用仓外 `customer-evidence` |
| `definitions/` | 8 | 客户 DTO 定义（`com.seeyon.datamigration<appId>.…`） | 移到仓外样例库，仓库只留 1 份脱敏示例 |
| `scripts/` | 5 | 一次性脚本把真 appId 写成 `default=` | 参数化（必须传 `--app-id`），或移进 `.hermes/dev-scripts/` |

这 216 个文件不静默放过：`tests/test_distribution_hygiene.py::test_facts_evidence_hits_do_not_grow`
把 216 当基线，新增一个就红。

## 为什么要分桶，而不是一把清完

`components/udc/event_listener_constraints.py`、`menu_constraints.py` 这类模块把真 appId 当
**功能数据键**（连接器默认值、菜单对照），删了会改行为 —— 它们需要先迁成
`config/` 引用键再脱敏，属于功能改造，不是改文档。所以先进 `LEGACY` 白名单并登记在案，
不许再新增。

## 自检

```bash
pytest tests/test_distribution_hygiene.py -q     # 4 passed
pytest tests/test_logs_loki.py -q                # 10 passed（全离线）
```

规则一句话：**代码只认引用键，值只有两种去处 —— 本机 local 覆盖层，或仓外证据根。**