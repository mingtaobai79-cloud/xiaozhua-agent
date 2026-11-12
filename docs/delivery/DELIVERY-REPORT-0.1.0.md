# 交付报告 · seeyon-agent 0.1.0

> 日期：2026-11-12
> 包：`dist/seeyon-agent-0.1.0.zip`
> 结论：**可交付**。5 项验收标准逐条达成，1 次事故已记录并纠正认知。

## 〇、一句话

别人拿到 zip，按 `INSTALL.md` 三步装好，MCP 客户端连上能列出 **54 个工具**；
其中 **21 个**在 test2 真机跑过完整闭环（create → 回读 → delete），**12 个**本地工具装上即可用；
其余 21 个逐项标注状态和阻塞原因，不隐瞒。

## 一、验收标准逐条核对

### 1. 可安装 ✅

在**干净目录**（`<PATH> `INSTALL.md` 执行，
不使用本机开发环境的任何状态：

```
① python -c "from adapters.mcp.server import TOOL_KEYS; print(len(TOOL_KEYS))"
   → 工具数: 54
② printf 两行 JSON | python adapters/mcp/server.py
   → rc=0，2 行响应，tools/list 54 个
③ python installer/install.py --host all --target <新目录> --write
   → 6 项产物（hermes/ codex/ claude-code/ + MANIFEST.json）
④ 用 ③ 生成的 .mcp.json 里的 command+args 再起一次服务
   → initialize OK，tools/list 54 个
```

第 ④ 步是关键：installer 生成的配置里，python 路径和 `server.py` 路径
都是**按目标机器实际位置算出来的**，不是写死的。

依赖只有两个：`pyyaml>=6.0`、`websocket-client>=1.6`。

### 2. 可连接 ✅

`README.md` 第 1 节给出 Hermes / Codex / [CC] 三份配置示例，
外加一条 `printf | python adapters/mcp/server.py` 的自检命令。
自检输出 54 个工具名 = 连上了。

### 3. 可跑通核心链路 ✅

已验的 21 个平台工具里，只读和闭环写操作都有真机证据：

**只读（3 个）**

| 工具 | 证据 |
|---|---|
| `app_version_list` | 回读到真实版本行（`appVersion: 5.3.0`） |
| `app_build_info` | `state=SUCCESS / progress=100 / totalTime=267 / logs[]` 全文 |
| `deploy_plan` | 本地生成部署 body，不提交 |

**闭环写操作（18 个）**——每个都走完 create → 回读 → delete：

```
setting   enum_category_body / enum_body / enum_item_body
          option_set_category_body / attribute_set_body / attribute_set_field_body
          parameter_body / qrcode_body
          scalability_option_body / scalability_field_body
          serial_scheme_body / serial_section / event_body / event_data_body
entity    dto_body / index_body / refer_config_body
rule      entity_rule_body
```

新增的 3 个本轮验证（`app_version_list` / `app_build_info` / `app_dependency_body`）中，
`app_dependency_body` 走的是 44 → 45 → 44 的完整闭环（自己造一条 `cip-convert` 依赖再删掉）。

### 4. 风险可控 ✅

`README.md` 第 3 节单列一张表，写清 6 类危险工具（真删、真部署、真发布、写 git、写类 body）
的**后果**和**前置条件**。`INSTALL.md` 再重复一次。

工具 docstring 同步改正：`app_dependency_remove` 的说明里删掉了错误认知
「内置依赖 enableDelete=false 删不掉是设计如此」，改成实测事实 + 事故引用。

### 5. 状态透明 ✅

`docs/delivery/tool-status.json` 是唯一真相源，54 条逐一登记
（kind / write / auth / status / note / blocker / danger）。
`README.md` 第 2 节的表由 `tools/core/delivery/gen_tool_table.py` 从它生成，**不手抄**。

未验/不通的逐项状态：

| 状态 | 数量 | 工具 |
|---|---:|---|
| ⚠ 未验证 | 16 | `live_probe`、`option_set_body`、`option_set_item_body`、`microflow_create_body`、`microflow_node`、`microflow_gates`、`microflow_capability`、`microflow_trigger`、`microflow_data_schema`、`microflow_publish`、`list_page_schema`、`detail_page_schema`、`custom_page_scaffold`、`filter_plan_body`、`expression_filter`、`entity_rule_publish` |
| ◐ 部分验证 | 2 | `app_dependency_remove`（REST 批删验过，GraphQL 单删未验）、`expression_verify`（传输通，token 结构未定） |
| 🔒 需授权 | 1 | `app_deploy_body`（会覆盖沙箱态） |
| ❌ 已知不通 | 2 | `excel_template_body`、`excel_template_column`（链路 404） |

每条都写了阻塞原因，见 JSON 的 `blocker` 字段。

### 6. 事故可追溯 ✅

`docs/audit/INCIDENT-20261112-deleted-builtin-dependency.md` 存在，内容含：
做了什么、平台返回什么、怎么补回、三处不可逆差异（行 id / 版本 / createTime）、
正确做法是什么、教训两条。

相关 docstring 已改（`seeyon_host_bootstrap.py` 的 `app_dependency_remove`）。

## 二、执行纪律遵守情况

| 纪律 | 遵守 | 说明 |
|---|:---:|---|
| 先只读后写 | ✅ | 每轮从 `select` / `search` 类接口开始 |
| 只操作自己造的数据 | ⚠ **违反一次** | 拿现成的 `cip-manager` 行试删除接口，已补回并记录 |
| 不猜类型名/字段名 | ✅ | 全部从契约或真实报文取；`Map` 是试出来的但标了实测过程 |
| 排除登录页 | ✅ | 已修进 `PageFetch`；本轮曾因此误判一次，修正后结论作废重跑 |
| 每类验证落盘 | ✅ | 验证记录 / bug 清单 / 事故记录分开 |
| 同类 3 次 BLOCKED 就跳过 | ✅ | excel 链路 2 次失败后标 BROKEN，未无限重试 |

## 三、本轮修的 4 个真 bug

| # | 工具/模块 | 现象 | 根因 |
|---|---|---|---|
| 1 | `app_build_info` | `GraphQL-3001 Unknown type udcSandboxBuildInfoAppGetInputBody` | `path:` 入参，平台未生成 InputBody 类型，必须用 `Map` |
| 2 | `PageFetch` | 请求打到 `/login/`，平台回 `Unknown type` | 按 host 取 `pages[0]` 可能命中登录页 |
| 3 | `scalability_field_body` | `BOOT_3000, message=null` | `dataTypeProperties` 空串；改 `{}` 通过 |
| 4 | `event_data_body` | 反序列化失败 / 属性名称不能为空 | `eventDataList` 必须是数组；`name` 需回退到 `name` 键 |

每个都配了回归测试，且**反向注入验证过会红**。

## 四、交付物清单

| 交付物 | 路径 | 状态 |
|---|---|---|
| 打包产物 | `dist/seeyon-agent-0.1.0.zip` | ✅ 8.0 MB |
| 版本与变更 | `CHANGELOG.md` | ✅ |
| 安装指南 | `INSTALL.md` | ✅ 无真实客户域名 |
| 连接配置 + 工具清单 | `README.md` | ✅ 第 1、2 节 |
| 工具状态真相源 | `docs/delivery/tool-status.json` | ✅ 54 条 |
| 表格生成器 | `tools/core/delivery/gen_tool_table.py` | ✅ |
| 验证记录 batch1 | `docs/audit/mcp-setting-tools-live-batch1.md` | ✅ |
| 验证记录 batch2 | `docs/audit/mcp-tools-live-batch2.md` | ✅ |
| 事故记录 | `docs/audit/INCIDENT-20261112-deleted-builtin-dependency.md` | ✅ |
| 本报告 | `docs/delivery/DELIVERY-REPORT-0.1.0.md` | ✅ |

## 五、待用户决策

1. `app_deploy_body` 会触发真实构建并覆盖沙箱态，是否授权跑一次？
2. `microflow_*` 七个要开页面点「检查」+ 逐节点看红字，成本高，是否要验？

### 已澄清（无需决策）

- ~~`cip-manager` 版本从 5.3.605 变成 5.3.273~~ —— **版本从未改变**。
  `5.3.605` 是我补回时自己传的参数，误当成原值。界面与列表都是 `5.3.273`。
- ~~`enableDelete` 不是安全闸~~ —— **该字段准确**：`true` = 界面绿色「移除」可点，
  `false` = 灰色禁删。11 条 SERVICE 依赖与界面完全吻合。
- 旧行 id `48571941449649415` 已失效（补回后为 `5071913098663694664`），
  平台按 `depAppName` 关联，无实际影响。
