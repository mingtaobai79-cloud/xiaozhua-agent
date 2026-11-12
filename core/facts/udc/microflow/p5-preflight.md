# P5 前置审计（2026-11-01）

## 工作区状态

- 分支 `master`，HEAD `3fcf24ec`（含 P4 补提交）
- 未提交改动 49 项，**与 P5 无关**：标准品事实研究（`core/facts/standard-product/*`）、
  scratch 清理、`tests/test_constructor_contract.py`（**该测试已于 `9fa07b76` 删除**，本行是 2026-11-01 的当时状态，保留原文不改）删除等。**不要动**。
- 全量测试 `2267 passed, 22 skipped`（collect 2289）

## 已具备的 P5 前置资产

| 能力 | 位置 | 状态 |
|---|---|---|
| 需求→逻辑图编译 | `components/construction/requirement_compiler.py` | 8/8 业务 PASS |
| 逻辑图执行 | `components/construction/logic_graph.py` | 平台 save PASS |
| 表达式 AST/传输 | `components/udc/microflow/expression_model.py` | 含 VARIABLE 走本地 |
| 保存链 | `components/udc/microflow/save_pipeline.py` | SCHEMA_VERIFIED |
| 发布 | `components/udc/microflow/deploy.py` | RELEASE 回读确认 |
| **CDP 浏览器驱动** | `components/udc/microflow/live/cdp.py` | 9333 可用（Edg/156） |
| **UI 节点操作** | `components/udc/microflow/live/ui.py`（595 行） | 见下表 |
| 构建验证 | GraphQL `udcRuntimeDeployNormalPost` + `udcSandboxBuildInfoAppGet` | BUILD SUCCESS 已验 |

### `live/ui.py` 已有函数（P5.2 直接复用，不要重写）

```
open_node(d, keyword, tries)       打开节点抽屉（按关键字定位）
ensure_node_drawer(d, keyword)     确保抽屉是目标节点
drawer / drawer_info(d)            抽屉状态与信息
confirm_node(d, expect, wait)      点「确定」+ 等 UpdatePost
save_and_wait(d, timeout)          画布保存
close_drawer(d, timeout)           关抽屉
click_el(d, js, verify)            按选择器点击（带校验）
submit(d, expect, wait, strategy)  提交（多种策略）
_net(d) / form_values(d)           网络记录 / 表单值
```

## 环境实测（本轮）

- CDP `http://127.0.0.1:9333` → `Browser: Edg/156.0.4314.50`，可用
- `<测试环境域名>` → HTTP 301，0.08s，通路正常
- 11 个页面已打开，**含设计器页面**：
  `/main/child-frame/udc/app-design/rule?appId=8704025620829192834`
- 登录态仍在（无需重新登录）

## 关键结论

1. **P5.2 不是从零建设**：节点定位、抽屉、点确定、保存等待全都有现成实现，
   `ExpressionFinalizer` 要做的是「编排 + 身份校验 + 回读判真」，不是重写 UI 驱动。
2. **L2/UI 通路本轮已恢复**（此前 BLOCKED 的 `net::ERR_TIMED_OUT` 不再出现），
   意味着 P5 可以真跑，不必等环境。
3. 工作区那 49 项脏改动必须在 P5 提交时**逐文件排除**，禁止 `git add -A`。
