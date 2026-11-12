# 应用内功能页接口地图（UDC 应用设计器 · 左侧菜单 / 底部日志）

> 口径：只读。所有结论来自「点击录制 + 会话 cookie 重放」的实测回包，不是按方法名推断。
> 环境：test2，网关前缀 `/service`；示例应用 `appId=9000000000000000001`、`appName=datamigration9000000000000000001`。
> 证据：`core/facts/udc/application/evidence/app-inner-pages-2026-10-22/*.json`（含真实 id 与回包原文）。

## 0. 抓法（三层，缺一层就会漏）

1. **点击录制**：`tools/core/application/cdp_click_capture.py` —— CDP `Network.enable` 被动记录，再用
   `Runtime.evaluate` 点左侧菜单/底部 tab 的文本节点，让页面自己发请求。不注入 cookie、不构造请求。
2. **重放取证**：`tools/core/application/replay_read_probe.py` —— 用 `Network.getCookies` 取同源会话 cookie，
   Python 直发同一 `method+path+body`，拿真实回包形状。遇到 `mutation ` 一律跳过并标 `SKIPPED`。
3. **路由扫描**：直接 `Page.navigate` 到每条子路由，用来发现「点击没触发但首次加载会触发」的请求。
   单路由加载会被品牌页/主题页的公共请求淹没，需按「页面独有」筛。

为什么不在页面里 fetch：设计器 tab 内 `window.fetch('/service/...')` 稳定失败
（`Network.loadingFailed = net::ERR_CONNECTION_CLOSED`、`TypeError: Failed to fetch`），同 URL 由 Python 直发 200。

## 1. 子路由表（与左侧菜单一一对应）

| 菜单项 | 子路由（`/main/child-frame/udc/app-design/app-basic-info/`） |
|---|---|
| 页面测试 | `testPage` |
| 沙箱测试 | `testVersion` |
| 发布版本 | `version` |
| 应用依赖 | `dependentApp` |
| 组件依赖 | `dependentCmp` |
| 团队设置 | `team` |
| 应用主题 | `appTheme` |

菜单文本 → 路由由点击后读 `location.href` 确认，不是猜的。

## 2. 每页取数接口

### 2.1 页面测试（`testPage`）
- `POST /service/udc/deployment/latest-test-info`，body `{appId}` → 最近一次测试版本/成功位/测试人
- `POST /service/udc/graphql?udcDeploymentAppReadyStatePost` → 运行态：`state=RUNNING`、`msg=DEPLOY_SUCCESS`
- 页内「检查」结果面板（检查通过/重新检查）：数据来自应用级检测接口族，非本页独有；
  「重新检查」是**写面动作**（会重跑全量检测），本轮未点。

### 2.2 沙箱测试（`testVersion`）与构建链路（实测全程）

页面本身只发 `udcDeploymentAppReadyStatePost`（就绪态）。真正的**构建**由设计器工具栏
「测试」→ 弹窗「立即构建」触发，链路是六段：

```
① POST udc/graphql?udcApplicationSearchDetectionPost        一致性检测（mutation，声明正确）
② POST udc/graphql?udcRuntimeDeployNormalPost               部署=构建（声明成 query，实为写）
③ POST udc/graphql?udcSandboxBuildInfoAppGet  × 44          约 6s 一次轮询，state/progress/logs
④ WS  udc_detection_channel / udc_deploy_channel            实时状态推送
⑤ WS  common-message {appName,status:SUCCESS}               完成通知
⑥ POST ctp-application/appcenter/search-app-edition         刷新「发布版本」列表
```

一次真实构建（2026-10-22）：前端 PC 编译 14s / 前端 MOBILE 8s / 后端编译 33s / 部署 124s，
平台自报 `totalTime=224`；结束后页面显示「测试启动完成 应用启动完成」。

关键结论：
- **构建日志不用抓流**。`udcSandboxBuildInfoAppGet` 一把返回
  `{state,progress,totalTime,logs:[...]}`，`logs` 就是「[展开沙箱日志]」的内容 ——
  之前把「沙箱构建日志接口」记成挂账，其实早就有，只是没找到取数口。
- **进度是 WS 推的，HTTP 只是轮询**。`udc_detection_channel` 的字段名是 `seriouCount`（少个 s，照抄别改）。
- **`udcRuntimeDeployNormalPost` 声明成 `query`**，与 REST 版 `udc.deploy.normal` 不是一个入口。

`search-app-edition` 是「发布版本」页的列表取数口，`IN_appId` 传的是 **appName**（字符串），
不是数字 appId —— 传错返回空数组。

### 2.3 发布版本（`version`）
- 仅 `POST /service/udc/deployment/latest-test-info`
- 页面本体（版本列表）取数未在点击/路由扫描中出现 → 与依赖页同源，见 §2.4 判读
- 发布动作 `app-delta-deploy` / `app-online` / `deploy-normal`：写面，全部未发

### 2.4 依赖设置 · 应用依赖（`dependentApp`）
依赖清单**有独立取数接口**，但它藏在「数据变更后的重拉」里，不是切 tab 时发：

| 动作 | 接口 | 类型 |
|---|---|---|
| 打开「添加依赖」弹窗 | `POST udc/graphql?udcMetaDataSearchAvailableAppMultiVersionPost` | 声明 mutation，语义查询 |
| 列表取数 | `POST udc/graphql?udcApplicationDependentApplicationSelectByConditionPost` | 声明 mutation，语义查询 |
| 点「确定」加依赖 | `POST udc/graphql?udcApplicationDependentApplicationCreateBatchPost` | **写** |
| 点「移除」→ popconfirm 确定 | `POST udc/graphql?udcApplicationDependentApplicationDeleteByIdPost` | **写** |
| 增删成功后平台自动串发 | `POST udc/graphql?udcApplicationSearchDetectionPost` | 检测（写缓存） |

关键字段语义：
- 可选应用列表里 `enableDependent=false` 的行 checkbox 必 disabled ——「通讯录」选不了是后端许可位，不是前端 bug
- 依赖行 `enableDelete=false` 表示内置依赖不可删（平台 / 集成平台两行虽然有「移除」按钮）
- 添加请求 `params0` 是**数组**（可一次加多个），每项
  `{appId, depAppName, depAppCaption, depAppVersion, depAppBasePackage, dependentAppType}`
- 移除请求 `params0={id}`，这个 `id` 是依赖行 id，不是 appId

为什么上一轮记成 UNVERIFIED：切 tab 复用缓存不重发请求（点「应用依赖」0 请求是真的），
只有发生写操作之后才重拉列表。这个坑值得记住 —— **0 请求不等于没有接口**。

### 2.5 团队设置（`team`）
- `POST /service/udc/graphql?udcCollaborationAppGet`，body `{variables:{path:{appId}}}` → 成员数组
- 行字段：`appId, guid, id, isCreator, memberId, memberName, role`
- `role` 是应用内角色名（如「应用设计师」），不是平台角色 id；所有者靠 `isCreator=true` 判定
- 「添加成员」「移交应用」= 写面，未点

### 2.6 应用主题（`appTheme`）
- 打开该页**自动**发 `POST /service/app-common/graphql?appCommonThemeSelectDefaultBrandPost`
  （`mutation`，选择默认品牌）——平台自动写，非人工动作，本仓库禁止重放
- 只读替身：`app-common/graphql?appCommonThemeSelectDefaultGet`（路由扫描中已录到）

### 2.7 组件依赖（`dependentCmp`）

和应用依赖是**同一个写口**，靠 `dependentAppType` 区分（`FRONTEND`=组件 / `SERVICE`=应用）。

| 动作 | 接口 | 说明 |
|---|---|---|
| 打开页面 / 加删后 | `POST udc/graphql?udcApplicationDependentApplicationSelectByConditionPost` | 同一列表接口，返回 44 行（SERVICE 11 + FRONTEND 33） |
| 点「添加依赖」 | 无请求 | **候选组件是前端内置目录**（86 行：`@seeyon/biz-*` / `@seeyon/mbiz-*`），不查后端 |
| 勾选 + 确定 | `POST udc/graphql?udcApplicationDependentApplicationCreateBatchPost` | 同写口，`dependentAppType=FRONTEND` |
| 勾选行 + 「批量删除依赖」→ 确认 | `POST udc/application/dependent-application/delete-by-ids` | **REST 批量删**，body `{ids:[...]}`，不是 GraphQL |

组件行比应用行多 9 个字段：`description`、`dynamicModuleGroup`、`dynamicService`、`enableDelete`、
`needGenerate`、`sort`、`supportUpgrade`、`terminalType`、`sourceType`、`packageType`。
实测一条：`packageType=CONTROL`、`sourceType=CUSTOMIZE`、`terminalType=PC`、`dynamicService=true`。

两个坑：
- 组件依赖行内**没有「移除」按钮**，只有表格上方的「批量删除依赖」；确认框按钮是「取消 / 确认」（不是 确定）。
- 批量删除的 REST 请求用 CDP `requestWillBeSent` 常抓不到（事件被 `Runtime.evaluate` 往返吞掉），
  要在页面里 hook `XMLHttpRequest`/`fetch` 记到 `window.__CAP__` 才稳。

## 3. 日志面（四类 tab）

### 3.1 设计日志
- `POST /service/udc/graphql?udcOperationLogSearchInitDataAppGet` —— 取筛选字典
  - 返回 `subModuleMap`：`ALL / DATAFLOW / DEDUCTION / FUNCTION_NODE / WIDGET / PORTLET /
    PORTLET_GROUP / PAGE / LAYOUT / ENTITY_GROUP / ENTITY ...` + `moduleMap` + `members`
  - 含义：筛选选项由后端下发，前端不写死；`members` 决定「操作人」下拉可选项
- `POST /service/udc/graphql?udcOperationLogSearch` —— 分页查询
  - body：`{pageInfo:{needTotal,pageNumber,pageSize}, params:{appId,startTime,endTime,operatorId,module,subModule},
    sort:{orders:[{direction:DESC,property:createTime}]}}`
  - 行字段：`operatorId,operatorCaption,module,subModule,moduleCaption,subModuleCaption,logElement,
    elementsSize,recordVersion,logPath,actionType,domainId,storageKey,createTime,operations,traceId,
    publishState,originalId,id,guid,extraJson`
  - **注意**：语义是查询，但平台声明成 `mutation` → 按纪律未重放，等级 `UNVERIFIED`

### 3.2 运行态日志（微流程 / 生单规则 / 扣减规则）
统一前缀：`/service/{appName}/udc-runtime/app-log/search/{kind}`（**应用名，不是 udc**）

| tab | kind | 实测 |
|---|---|---|
| 微流程运行日志 | `microflow` | LIVE PASS，返回 10 行 |
| 生单规则运行日志 | `dataflow` | 200 + `content=[]`（无数据，非失败） |
| 扣减规则运行日志 | `deduction` | 200 + `content=[]`（无数据，非失败） |

请求体：`{params:{appName,appId,logType}, pageInfo:{pageNumber:1,pageSize:10,needTotal:true,total:0}}`

微流程日志行字段：`validate, id, traceId, requestId, moduleType(MICRO_FLOW), success, logTime,
subModuleType(MICRO_FLOW_FRONTEND), subModuleTypeName, ...`

### 3.3 命名规则（证伪出来的，别再拼）
`design / page / bizrule / sandbox / build / compile / deployment` 七个候选全部 **404 非 JSON**。
→ 该族只存在 `microflow / dataflow / deduction` 三种；
→ 「设计日志」不在这里，走 §3.1 的 GraphQL。

## 4. GraphQL 封装契约（应用内功能页的通用形态）

- 端点：`POST /service/{service}/graphql?<operationName>`，operation 名**同时**出现在 URL query 上
- 请求体：`{"query": "<文本>", "variables": {...}}`，query 统一是 `graphqlLoader` 外壳，内层一个别名（`data0` 或 op 名）
- 回包信封：`{ "<alias>": { "code": "BOOT_0000", "data": { "content": ... }, "message": "SUCCESS", "status": ... } }`
- 判读：不能套 REST 的 `{code,data.content}` 顶层判据，要下钻到 alias 层
- 服务归属：`/service/udc/graphql`（应用域）、`/service/app-common/graphql`（主题/品牌等公共域）

## 5. 写面清单（页面自己会发，本仓库一律不发）

| op | 触发时机 | 处置 |
|---|---|---|
| `appCommonThemeSelectDefaultBrandPost` | 打开「应用主题」页即自动发 | DENIED，不重放 |
| `udcOperationLogSearch` | 设计日志查询（声明成 mutation） | UNVERIFIED，未发 |
| 检查/重新检查 | 人工点 | 未点（重跑全量检测） |
| 清除应用数据 | 人工点 | 未点 |
| 添加成员 / 移交应用 / 添加依赖 / 移除 | 人工点 | 未点 |
| 发布（app-delta-deploy / app-online / deploy-normal） | 人工点 | 未发 |

## 6. 未解项（明确记录，不粉饰）

1. ~~沙箱构建日志接口~~ —— 已解：`udcSandboxBuildInfoAppGet` 的 `logs[]`（见 2.2）。
2. ~~组件依赖（`dependentCmp`）~~ —— 已解：同写口 + REST `delete-by-ids`（见 2.7）。
3. ~~发布版本页版本列表~~ —— 已解：`ctp-application/appcenter/search-app-edition`（见 2.2）。
4. **「检查」结果的服务端来源** —— 最强候选是 `udcApplicationSearchDetectionPost`
   （依赖增删后由平台自动串发，返回 `detectionType/moduleType/path/route/interpolatedMessage`），
   但它是写面且未主动触发，**未取得回包**，所以仍不能断言「检查通过」由它判定；
   REST `front-detection`（计数全 0、`appId=null`）依旧不可当证据。
