# 应用域写链与踩坑（依赖设置 + 沙箱构建）

> 全部 LIVE 实测（2026-10-22，test2）。本文件只记「怎么打、打完什么样、哪里会翻车」。
> 事实格摘要见同目录 `create.md`；全量操作表见 `docs/operation-contracts/udc/application/app-inner-contracts.md`。

## 一、依赖设置写链（应用依赖 SERVICE）

```
① 打开 dependentApp           POST udc/graphql?udcApplicationDependentApplicationSelectByConditionPost   读
② 点「添加依赖」               （无请求，候选应用走 ① 的兄弟接口 udcMetaDataSearchAvailableAppMultiVersionPost）
③ 勾选 + 确定                 POST udc/graphql?udcApplicationDependentApplicationCreateBatchPost     写
④ 页面自动串发                 POST udc/graphql?udcApplicationDependentApplicationSelectByConditionPost   读（重拉列表）
⑤ 点行内「移除」→ 确认         POST udc/graphql?udcApplicationDependentApplicationDeleteByIdPost       写
⑥ 页面自动串发                 POST udc/graphql?udcApplicationSearchDetectionPost                    写（一致性检测）
```

实测往返：2 行 →（加公告 5.3.98）3 行 →（移除）2 行，内置平台 / 集成平台两行全程未被误改。

### 请求体（真实抓包，字段名照抄）

添加：

```json
{"query":"mutation graphqlLoader ($params0: [udcApplicationDependentApplicationCreateBatchPostInputBody]) { ... }",
 "variables":{"params0":[{"appId":"9000000000000000001",
                          "depAppName":"<depAppName>",
                          "depAppCaption":"<depAppCaption>",
                          "depAppVersion":"5.3.98",
                          "depAppBasePackage":"com.seeyon",
                          "dependentAppType":"SERVICE"}]}}
```

移除：

```json
{"variables":{"params0":{"id":"<依赖行 id，纯数字，不等于 appId>"}}}
```

### 错误字典 / 翻车点

| 现象 | 根因 | 正确做法 |
|---|---|---|
| 移除点了没反应 | 传的是 appId 或 depAppName | 必须用依赖行 id（列表里该行的 `id`） |
| 加进去不生效 | 候选勾了但 `enableDependent=false` | 候选行的许可位决定能不能勾；页面上勾不动就是它 |
| 内置行点不了「移除」 | `enableDelete=false` | 平台 / 集成平台属内置依赖，设计如此 |
| 列表 `total=0` | 请求只带 `appId` | 必须带 `versionType` 与分页字段 |
| 列表取数 KeyError `'data0'` | 少剥一层 | 层级是 `raw["data"]["data0"]["data"]["content"]` |
| 空数组批量删 | antd 受控 checkbox 未真正勾上 | `scrollIntoView` 后按坐标点 `.ant-checkbox-inner`，勾完先断言 `selected` |

### 组件依赖（FRONTEND）与它的 REST 删口

- 列表、写口与应用依赖**共用**，靠 `dependentAppType=FRONTEND` 区分。
- 候选组件**不发请求**（86 行来自前端内置目录 `@seeyon/biz-*` / `@seeyon/mbiz-*`）。
- 删除走 **REST** `POST udc/application/dependent-application/delete-by-ids`，body `{"ids":["<行 id>"]}` ——
  与应用依赖的 GraphQL `DeleteByIdPost` **不是一条路**。
- 行内没有「移除」，入口是表格上方「批量删除依赖」；确认框按钮是「取消 / 确认」（不是「确定」）。
- 该 REST 请求用 CDP `requestWillBeSent` 常抓不到（事件被 `Runtime.evaluate` 往返吞掉），
  必须在页面内 hook `XMLHttpRequest`/`fetch` 记 `window.__CAP__`。

## 二、构建写链（工具栏「测试」→「立即构建」）

```
① POST udc/graphql?udcApplicationSearchDetectionPost      一致性检测（mutation）
② POST udc/graphql?udcRuntimeDeployNormalPost             构建+部署（声明 query，实为写）
③ POST udc/graphql?udcSandboxBuildInfoAppGet  × 44        约 6s 轮询
④ WS  udc_detection_channel / udc_deploy_channel           实时进度
⑤ WS  common-message {appName,status:SUCCESS}              完成通知
⑥ POST ctp-application/appcenter/search-app-edition        刷新版本列表
```

一次真实构建耗时：前端 PC 14s / 前端 MOBILE 8s / 后端编译 33s / 部署 124s，平台自报 `totalTime=224`。

### 关键结论

- **构建日志不需要抓流**。`udcSandboxBuildInfoAppGet` 一把返回
  `{state,progress,totalTime,buildVersion,logs[]}`，`logs` 就是「[展开沙箱日志]」全文。
  构建结束后仍可取（`state=SUCCESS`）。
- **进度是 WS 推的**，HTTP 侧只有轮询；`udc_detection_channel` 的字段名是 `seriouCount`（少个 s，照抄别改）。
- **别名是 `path:` 不是 `body:`**：`data0: udcSandboxBuildInfoAppGet(path: $params0)`。
- `udcRuntimeDeployNormalPost` 的 `query` 声明与实际写入语义不符，按写面处理。

## 三、日志面命名规则（证伪出来的，别再拼）

| 类型 | 路径 | 结果 |
|---|---|---|
| 微流程 | `POST /service/{appName}/udc-runtime/app-log/search/microflow` | LIVE PASS（10 行） |
| 生单规则 | 同上 `dataflow` | 200 + `content=[]` |
| 扣减规则 | 同上 `deduction` | 200 + `content=[]` |
| 其余候选 | `design-log` / `applog` / `operation` 等 7 种 | 全 404 |

应用日志前缀是 **`{appName}/udc-runtime/`**，不是 `/service/udc/...`；操作日志另有 GraphQL
`udcOperationLogSearchInitDataAppGet`（init）与 `udcOperationLogSearch`（mutation，不调用）。

## 四、仍未验证（不追认为契约）

1. 构建弹窗里「创建微流程」「从模板创建」两个入口 —— 未点，接口未知。
2. WebSocket 握手 URL —— 连接建在页面加载时，后开面板抓不到 `webSocketCreated`；
   需新开 tab 从加载起监听。
3. `udcApplicationSearchDetectionPost` 的错误字段含义（检测结果只观察到串发，未构造失败样本）。
