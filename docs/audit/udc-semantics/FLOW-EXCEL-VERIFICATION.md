# Flow/Excel 离线契约验收记录

## 本轮交付

- `flow-excel-source-audit.md`：DataFlow/Deduction/Excel 的保存、生成、触发、输入输出、落表和副作用证据。
- `flow-excel-contracts.json`：从真实本地源码抽取的契约候选清单；不加载到运行 registry。
- `tools/core/audit_udc_flow_excel.py`（**已移入 `_attic_pending/one-off/unsorted/audit_udc_flow_excel.py`**，仓库内已无此路径）：离线提取、哈希与内容回放核验。
- `tools/core/check_udc_flow_excel_cli.py`（**已移入 `_attic_pending/one-off/unsorted/check_udc_flow_excel_cli.py`**，仓库内已无此路径）：独立工具 CLI 验收；使用本机真实源码/reference jar，缺失时直接失败，不合成平台数据。
- `config/udc-semantics-evidence.example.json`：可迁移配置模板。实际路径只存在于 git 忽略的 local 配置。

## 实际执行结果

离线 extraction/replay：PASS。

```text
source_files: 48
claims: 31
operations: 70
  dataflow.design: 24
  deduction.design: 16
  deduction.runtime.management: 9
  excel.component: 21
dto_types: 13
dto_fields: 125
tables: 7
confirmed_side_effect_operations: 10
side_effect_unreviewed_operations: 60
live_pass: 0
network_calls: 0
platform_writes: 0
```

独立工具检查：6/6 通过（实际 public CLI subprocess）。

```text
真实清单回放通过
篡改 Controller 路由被拒绝
将 Excel check 伪装只读被拒绝
把静态 operation 标为可执行被拒绝
显式配置文件缺失返回结构化 FAIL + 非零退出码
源码根缺失返回结构化 FAIL + 非零退出码
```

错误处理 RED→GREEN 证据：新增“缺配置/缺源码”CLI 断言时，4 项中 2 项因 traceback 失败；加入只捕获证据/输入异常的结构化处理后 4 项全通过；持久化完整检查后 6 项通过。这里的验证器不是平台 schema validator，不将它的 PASS 提升为页面、微流程、生单、扣减或 Excel 业务通过。

仓库离线回归：`399 passed in 9.43s`（exit 0）。此回归不包含独立工具的 6 项检查；两组结果分别报告，不把总测试基线改成 405。

Python AST/syntax：两个工具通过。

git diff --check：通过。local 证据配置：git check-ignore 命中。

新工具/清单/专门报告的作用域扫描：未发现 token/private-key 模式、机器绝对路径或网络 URL。旧报告历史绝对路径未在本轮整体清理，不能把作用域检查称全仓库扫描。

## 重跑

在仓库根选择当前 Python 解释器：

```text
python tools/core/audit_udc_flow_excel.py verify --config config/udc-semantics-evidence.local.json --manifest docs/audit/udc-semantics/flow-excel-contracts.json
python tools/core/check_udc_flow_excel_cli.py --repo <repo-root> --python <python-path> --scratch <local-scratch-root>
python -m pytest tests -q -p no:cacheprovider
```

首次使用先把 example 配置复制为 local 配置并填写真实源码根与 reference jar 路径。reference jar 的 artifact/version/hash 必须对应清单，不靠任意替代版本凑通过。

## 未完成门槛

- 旧源码/reference jar/目标部署版本没有完整绑定。
- Gateway 前缀与真实前端调用未抓包确认。
- 目标应用实体/页面/微流程/生单/扣减/Excel 业务数据未验收。
- seeyon-agent 尚未实现这些协议模型、payload/schema validator 和完整 dry-run planner。
- 页面构建按钮真实请求与生成物回读未完成。
- 当前所有契约候选 can_execute=false；未发平台请求、未修改 test2、未生成客户业务记录。

因此本轮结论为 OFFLINE EVIDENCE PASS / LIVE UNVERIFIED，静态审计子任务完成不等于订单应用任务完成。
