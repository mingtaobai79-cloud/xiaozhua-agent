# 交付编排（P5）：状态机、闸门、表达式最终化

> 代码：`components/construction/p5_pipeline.py`（编排器）、`p5_finalizer.py`（最终化，**兜底**）、
> `p5_cdp_driver.py`（唯一碰 DOM 的适配器）。
> 前置事实：`references/expression-engine.md` §十五——**含 VARIABLE 的表达式
> check/transform 完全可用**，全自动交付成立，CDP 不是必经路径。

## 总原则：能走接口的走接口，只认设计器的交给设计器

不为「纯 API 自动化」去逆向平台私有的运行时代码生成逻辑。
CDP 有版本漂移风险，所以把它**限制在一个独立适配器里**，不让整条流水线依赖页面操作。

## 阶段状态机（11 态，迁移表显式）

```
DRAFT_READY → GRAPH_VALIDATED → CONSTRUCTED → SAVED
→ PLATFORM_VALIDATED → [NEEDS_UI_FINALIZE → UI_FINALIZED]
→ READBACK_VERIFIED → PUBLISHED → BUILD_SUCCESS
任意态 → FAILED / BLOCKED（终态，无出边）
```

- 迁移用**显式 `ALLOWED` 表**，跳阶段直接抛错；不要写「想跳就跳」的 if 链。
- 失败**一律进 FAILED 终态**，不许停留在 `NEEDS_UI_FINALIZE` 这种半完成状态。
- `resume_from(saved)` 只算「下一步该做什么」，**不代替平台状态核对**。
  返回值四选一：`DONE` / `NEED_HUMAN` / `RESTART` / 某个阶段名。
  失败态（FAILED/BLOCKED）返回 `NEED_HUMAN`，不自动重试。

### 交付成功口径（用户定的铁律）

- **只有 `BUILD_SUCCESS` 算交付成功**。
- `SAVED` / `PLATFORM_VALIDATED` / `NEEDS_UI_FINALIZE` / `PUBLISHED` 都**不是**成功态。
- 「保存成功」「checkSchema 绿」「构建成功」三件事各自独立，不能互相代替。
- 构建成功也**不等于**运行成功（RUNTIME 是另一个维度）。

### 五道硬闸门（每条都要有对应单测）

| 闸门 | 行为 |
|---|---|
| 编译 `BLOCKED` / `AMBIGUOUS` | 禁止继续构造，`graph` 不落地 |
| 有 `needs_ui_finalize` 但没注入 finalizer | 阻断，不假装成功 |
| 没注入构建器 | 阻断，不把构建当已完成 |
| 回读发现 `executableExpr` 仍是占位/空 | 阻断 |
| 别名映射不到平台 nodeId | 阻断，绝不按顺序猜 |

编排器只决定「什么时候调、调完怎么判、失败了怎么记」，**一行都不重实现**已有能力：

| 能力 | 复用 |
|---|---|
| 需求→图 | `BusinessRequirementCompiler` |
| 图校验/执行 | `logic_graph.validate_graph` / `LogicGraphRunner` |
| 保存+校验 | `save_pipeline.run_pipeline` / `l2_check` |
| 发布/回读 | `deploy.publish` / `deploy.get` |
| 页面操作 | `live/ui.py`（`open_node` / `confirm_node` / `close_drawer`） |

## ExpressionFinalizer：怎么判「真的最终化成功了」

### 判据是「executableExpr 是占位」，不是「含 VARIABLE」

```python
def needs_finalize(expression_obj) -> bool:
    ee = json.loads(expression_obj["schema"])["runtimeData"]["executableExpr"]
    return is_placeholder(ee)          # 空串 或 PLACEHOLDER 标记
```

已由平台生成过 `executableExpr` 的表达式**不需要重做**——按「含 VARIABLE」判会把
平台已完成的节点又点一遍，白跑还可能触发意外保存。

### driver 是接口，CDP 只是其中一种实现

`ExpressionFinalizer(driver=..., read_schema=...)`，driver 只需实现：
`open_node(node_id)` / `open_expression(i)` / `read_expression()` / `confirm()` / `close()`。

**CDP 操作不许写进 NodeBuilder / Expression DSL / 编排器**——它们不该知道设计器存在。
好处：最终化逻辑能用假 driver 全量单测（零浏览器），CDP 只是最后一层薄适配。

### 四道 UI 层闸门

| 闸门 | 为什么 |
|---|---|
| 抽屉 caption 必须含目标 caption | 点错节点会改坏别的节点，不能盲点「确定」 |
| 表达式编辑器文本为空 → 阻断 | 定位错或还没加载完 |
| 点「确定」失败只重试 `MAX_ATTEMPTS=2` | 不无限重试页面操作 |
| **点成功但回读仍占位 → 失败** | 平台没生成 ≠ 完成 |

最后一条是核心：`confirm_node` 返回 `saved=True` 只说明 UpdatePost 发出去了，
必须重新 `deploy.get(mid)` 读 dataSchema，确认目标节点 `executableExpr` 已不是占位。

### 别名 → nodeId 不许按顺序猜

按 `alias` / `caption` 精确匹配，递归进 `nodes`；匹配不到就返回空并失败。
靠页面顺序猜节点身份，一改顺序就点到别的节点上。

## P5.3 构建验证（`p5_builder.py`）

三个接口，形态固定，写错都是无明细报错：

| 用途 | 接口 | 关键点 |
|---|---|---|
| 触发构建 | `POST /service/udc/runtime/deploy-normal` | body **必须包成** `{"deployDto": {...}}`（形参注 `@MultiRequestBody`）。平铺即 DTO=null → `EL1007E`；`deployType` 必须 `RELEASE`（`TEST` 不会启动构建）|
| **轮询（唯一正确）** | `POST /service/udc/graphql?udcRuntimeSearchDeployStatusDeployIdPost` | 按 deployId 精确查，见下方 |
| ~~轮询~~（只对 delta 有效） | `GET /service/udc/sandbox/delta-build-info/{appId}` | 路径**必须带 `/service`**；响应两层包裹 |

### ★★★ delta-build-info 不能用来轮询 RELEASE 构建（2026-11-01 实测）

它只保留**最近一次完成的 delta 结果**，RELEASE 构建根本不写这里。

实测：RELEASE 触发后连查 10 分钟，`state` 一直是上一次的 `FAIL`、
`startTime` 一动不动；而 `search-deploy-status` 一查就是
`state=SUCCESS, buildVersion=20261101194735, jarVersion=1.0.89`。

后果：加了陈旧判定后变成「永远 stale → 一直等到超时」，
看起来像构建卡住，实际早就成功了。**有 deployId 就按 id 查。**

### 状态查询的确切写法（三个坑都踩过）

```
POST /service/udc/graphql?udcRuntimeSearchDeployStatusDeployIdPost

query g($p: udcRuntimeSearchDeployStatusDeployIdPostInputPath) {
  data0: udcRuntimeSearchDeployStatusDeployIdPost(path: $p) {
    code data { content } message
  }
}
variables = {"p": {"deployId": "<deployId>"}}
```

| 写法 | 结果 |
|---|---|
| `...PostInputBody` + `body:` | UnknownType / UnknownArgument |
| `...PostInput` + `path:` | UnknownType |
| `String!` + `path: "<str>"` | `GraphQL_3000 java.lang.String cannot be cast to java.util.Map` |
| **`...PostInputPath` + `path: {deployId}`** | **BOOT_0000，全字段** |

返回：`{data:{data0:{code, data:{content:[{state,msg,buildVersion,jarVersion,...}]}}}}`
★ content 在 `data0.data.content`，**不在 data0 顶层**（少解一层拿到空，就会误判成「还在构建」）。

### 状态语义

- `state` ∈ `RUNNING` / `SUCCESS` / `FAIL`（平台用 `FAIL` 不是 `FAILED`，两者都认）。
- **`RUNNING` / `BUILDING` 不是终态**，超时也**不算成功**——轮询要有上界（默认 900s）。
- **读不到 ≠ 还在构建**：连续读不到要有上界（`UNREADABLE`），
  否则 sleep 很快的实现会空转到超时，看起来像「一直在构建」。
- 按 deployId 查到的结果属于本次构建，**不需要判陈旧**；
  只有回退到 delta-build-info 时才需要 `_is_stale`。
- 一致性检测未过时整单失败，**没有部分成功**，必须原样反映。
- 失败要保留 `logs` 尾部含 ERROR/失败字样的行作为证据。
- 构建结果必须挂一句语义声明：**构建成功不代表微流程真实运行成功**。

### 构建前置：一致性检测 ERROR 必须为 0

被挡时日志形如：

```
[ERROR] 查询数据源:实体属性已更改(ID)
```

这通常是旧流程引用了已变更的实体属性，删掉旧流程即可，不是代码问题。
实测：删掉 2 条旧流程后 `13 WARN → 11 WARN，ERROR=0`，构建才真正启动。

## P5.4 断点恢复（`p5_report.py`）

核心口径：**平台真实状态 > 本地记录**。冲突时不猜，交人工。

| 情形 | 动作 |
|---|---|
| `BUILD_SUCCESS` | `DONE` |
| 本地 mid 在平台上已不存在 | `RESTART`（记录作废） |
| `FAILED` / `BLOCKED` | `NEED_HUMAN`，不自动重试 |
| 已到 `SAVED` 及之后，却读不到平台 state | `NEED_HUMAN`，**不盲目前进** |
| 本地已 `PUBLISHED`，平台实际是 `DRAFT` | `NEED_HUMAN`（平台回退了） |
| 无记录 / 未知阶段 | `RESTART` |

- 报告落盘用**原子写**（先写 `.tmp` 再 `os.replace`），避免半截 JSON 让恢复逻辑读到残缺状态。
- 报告要能出人读摘要：阶段列表 + 每阶段耗时 + 失败原因 + 待最终化节点 + 构建语义声明。

## 工程节奏：分层写、逐文件提交、不碰无关脏改动

这一阶段会同时存在多条研究线，工作区常常已经是脏的（几十个与本任务无关的改动）。

```
① 开工前先审计：git status --porcelain + 全量 pytest，拿到基线
   —— 分清哪些脏改动是本任务的、哪些不是，写进前置审计文档
② 只 add 自己改的文件，禁止 git add -A
   （git status --porcelain --cached 不存在，要看暂存用 git diff --cached --stat）
③ 一个子模块一个 commit：代码 + 测试 + 文档计数一起提
④ 每次提交前跑全量 pytest，不靠子集
```

⚠ **漏提文件很常见**：小改动（如一个常量表）容易被落在工作区，下一轮审计才发现。
提交后立刻 `git status --porcelain <本任务目录>` 确认为空，比事后补交干净。

⚠ **文档计数测试断言的是 collected 总数**（passed + failed + skipped），不是 passed。
新增测试后取 `pytest tests --collect-only -q` 末行数字，不要用 passed + skipped 自己加
（有失败项时那几条不在 passed 里，加出来会少）。改完 README 重跑一次，
按报错路径把它点名的其它文档（audit 等）一起改，直到绿。

## 未验证部分（写代码前先实测）

★ 2026-11-01 实测已补齐（设计器真实 DOM）：

| 元素 | 真实选择器 |
|---|---|
| 节点抽屉 | `.ant-drawer`（width>200 的最上层），确定按钮 `.compid_node-config-submit-btn` |
| **条件表达式编辑器** | **`ant-modal`（标题「表达式设置」，宽 1000），不是 drawer** |
| 表达式「确定」 | `[...document.querySelectorAll('.ant-modal button')].filter(b=>b.innerText.trim()==='确定')[0]` |
| 编辑器容器 | `.index-module_editorContent__ss8FH` |

坑：`BRANCH` / `条件设置` 的 `.node-body` 用 `click_react` 点不开 drawer，
它开的是 **modal**；只查 `.ant-drawer` 会误判成「没反应」。

★ 但现在这些只用于**兜底路径**——正常交付不需要碰 DOM。

## 研究支线：已结案（2026-11-01）

**结论：`executableExpr` 是后端 `/expression/transform` 生成的，前端只负责发请求。**

抓包结果：点条件表达式「确定」→ 依次发 4 个请求
`/expression/schema` → `/expression/operator/list` → `/expression/preset/list` →
`/expression/transform`（请求 2472 字节，响应 3223 字节，`BOOT_0000`）。

把 transform 的请求体**原样离线重放** → 成功，返回的 `executableExpr` 与设计器**逐字节一致**。

→ 所以「设计器才能生成」是错的；不需要 CDP，也不需要逆向。
详见 `references/expression-engine.md` §十五。

## 验收场景（至少这些）

| 场景 | 考察 | 状态 |
|---|---|---|
| 无字段引用 | 正常构建 | 待跑 |
| 单字段引用 | transform 直出 executableExpr | 待跑 |
| 同节点多字段引用 | context 完整性（见 `expression-token-pitfalls.md` 第二节） | **已验**（端到端） |
| 分支内 / 循环体内引用 | 节点定位与嵌套上下文 | 待跑 |
| 嵌套循环+分支 | 作用域隔离、节点映射 | 待跑 |
| UI 会话中断 | 识别阶段状态并安全恢复 | 待跑 |
| 构建失败 | 不误报成功，保留错误证据 | **已验**（真实 FAIL + 一致性检测日志） |
| `AMBIGUOUS` / `BLOCKED` | 禁止越过编译闸门 | 单测覆盖 |
