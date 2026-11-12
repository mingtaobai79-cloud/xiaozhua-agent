# 应用内功能页只读契约（LIVE 实测 2026-10-22）

范围：UDC 应用设计器内部的功能页 —— 页面测试 / 沙箱测试 / 发布版本 / 依赖设置 / 团队设置 / 应用主题，
以及底部四类日志 tab（检查 / 设计日志 / 微流程运行日志 / 生单规则运行日志 / 扣减规则运行日志）。

环境：`https://<gateway-host>`（test2），示例应用 `appId=9000000000000000001`、
`appName=datamigration9000000000000000001`。断言口径：HTTP 200 **且** 信封 `code=BOOT_0000` **且**
`data.content` 有形状（GraphQL 需下钻 alias 层）才记 LIVE_PASS。

## 1. 结果总表

| op_id | method | path | 判定 |
|---|---|---|---|
| `udc.applog.search.microflow` | POST | `{app_name}/udc-runtime/app-log/search/microflow` | LIVE_PASS（10 行） |
| `udc.applog.search.dataflow` | POST | `{app_name}/udc-runtime/app-log/search/dataflow` | 200 + `content=[]` |
| `udc.applog.search.deduction` | POST | `{app_name}/udc-runtime/app-log/search/deduction` | 200 + `content=[]` |
| `udc.applog.search.absent_kinds` | POST | 同上 `/{design,page,bizrule,sandbox,build,compile,deployment}` | 404 非 JSON（DENIED） |
| `udc.operation_log.init_data` | POST | `udc/graphql?udcOperationLogSearchInitDataAppGet` | LIVE_PASS |
| `udc.operation_log.search` | POST | `udc/graphql?udcOperationLogSearch` | UNVERIFIED（mutation 声明，未重放） |
| `udc.collaboration.app_get` | POST | `udc/graphql?udcCollaborationAppGet` | LIVE_PASS |
| `udc.deployment.app_ready_state` | POST | `udc/graphql?udcDeploymentAppReadyStatePost` | LIVE_PASS |
| `app_common.theme.select_default_brand` | POST | `app-common/graphql?appCommonThemeSelectDefaultBrandPost` | DENIED（mutation，页面自动发） |
| `udc.dependency.available_apps` | POST | `udc/graphql?udcMetaDataSearchAvailableAppMultiVersionPost` | LIVE（弹窗一开即发） |
| `udc.dependency.list` | POST | `udc/graphql?udcApplicationDependentApplicationSelectByConditionPost` | LIVE_PASS |
| `udc.dependency.create_batch` | POST | `udc/graphql?udcApplicationDependentApplicationCreateBatchPost` | DENIED（已实测一次，随后复原） |
| `udc.dependency.delete_by_id` | POST | `udc/graphql?udcApplicationDependentApplicationDeleteByIdPost` | DENIED（已实测一次，复原） |
| `udc.application.detection` | POST | `udc/graphql?udcApplicationSearchDetectionPost` | DENIED（已录到真实形状） |
| `udc.deploy.deploy_normal` | POST | `udc/graphql?udcRuntimeDeployNormalPost` | DENIED（已实测一次真实构建） |
| `udc.sandbox.build_info` | POST | `udc/graphql?udcSandboxBuildInfoAppGet` | LIVE_PASS |
| `ctp.version.list` | POST | `ctp-application/appcenter/search-app-edition` | LIVE_PASS |
| `udc.ws.business_channels` | WS | 会话 WebSocket，`{operate,data}` | LIVE（三通道） |
| `udc.dependency.component_create` | POST | `udc/graphql?udcApplicationDependentApplicationCreateBatchPost` | DENIED（已实测，已复原） |
| `udc.dependency.delete_by_ids` | POST | `udc/application/dependent-application/delete-by-ids` | DENIED（已实测，已复原） |

计数：LIVE_PASS 8 / 存活空结果 2 / 404 证伪族 1 / 未重放 1 / DENIED 8。

## 2. 五个必须记住的形状

### 2.1 日志族前缀是「应用名」
`/service/datamigration9000000000000000001/udc-runtime/app-log/search/microflow` ✅
`/service/udc/udc-runtime/...`、`/service/udc/sandbox/build-log/search` ❌ 404
→ 运行态接口按应用隔离部署在 `{appName}` 服务下，与 `/service/udc` 是两个服务。

### 2.2 日志族只有三种 kind
`microflow` / `dataflow` / `deduction`。按语义去猜 `design`、`page`、`bizrule`、`build`、`compile`、
`sandbox`、`deployment` 全 404 —— 命名规则已用 7 次失败证伪，别再拼。
「设计日志」不在 REST 族，走 GraphQL。

### 2.3 GraphQL 判读要下钻 alias
```json
{"data0": {"code": "BOOT_0000",
           "data": {"content": {...}},
           "message": "SUCCESS", "status": ...}}
```
alias 可能是 `data0`，也可能是 operation 名本身（`udcCollaborationAppGet`）。
拿 REST 的顶层 `code` 判会被误判为失败（首轮就踩过一次，7 条全 FAIL，实际是解析口径错）。

### 2.4 operation 名也在 URL 上
`POST /service/udc/graphql?udcCollaborationAppGet` —— 便于按 URL 索引，但服务端仍以 body 里的 query 为准。

### 2.5 空列表 ≠ 通过
`dataflow` / `deduction` 返回 `content=[]` 只证明接口存活；示例应用没有这两类日志。
同理 `front-detection` 计数全 0 + `appId=null` 是未检测占位，不能当「检测通过」。

## 3. 复现命令

```bash
# 1) 点击录制（只点左侧菜单 / 底部 tab，不发业务请求）
python tools/core/application/cdp_click_capture.py --port 9250 \
  --match "app-basic-info/testPage" \
  --labels 页面测试 发布版本 团队设置 设计日志 微流程运行日志 生单规则运行日志 扣减规则运行日志 \
  --seconds 6 --out <capture-dir>

# 2) 重放取证（mutation 自动跳过；cookie 不落盘）
python tools/core/application/replay_read_probe.py --port 9250 \
  --base https://<gateway-host> --plan <capture-dir>/replay-plan.json \
  --app-name datamigration9000000000000000001 --app-id 9000000000000000001 \
  --with-applog --out <capture-dir>/replay-probe.json
```

## 4. 依赖设置全链路（用户授权实测，已复原）

以示例应用为宿主，加一条外部应用依赖再移除，五步全部录到：

```
1) 点「添加依赖」      POST udc/graphql?udcMetaDataSearchAvailableAppMultiVersionPost
2) 勾选 + 点「确定」    POST udc/graphql?udcApplicationDependentApplicationCreateBatchPost   ← 写
3) 平台自动重拉列表     POST udc/graphql?udcApplicationDependentApplicationSelectByConditionPost
4) 点「移除」→ 确认     POST udc/graphql?udcApplicationDependentApplicationDeleteByIdPost     ← 写
5) 平台自动重跑检测     POST udc/graphql?udcApplicationSearchDetectionPost                    ← 写缓存
```

添加请求体（脱敏示例）：

```json
{"variables": {"params0": [{
  "appId": "9000000000000000001",
  "depAppName": "<依赖应用编码>",
  "depAppCaption": "<依赖应用名>",
  "depAppVersion": "<版本号>",
  "depAppBasePackage": "com.seeyon",
  "dependentAppType": "SERVICE"
}]}}
```

移除请求体：`{"variables": {"params0": {"id": "<依赖行 id，不是 appId>"}}}`

三个必须知道的坑：

1. **勾选不生效会发空数组写**：`params0: []` 照样发请求，只是什么都没加。判断勾选是否生效要看
   `tr.ant-table-row-selected` 与 `input.checked`，不能看点击是否返回 ok。
2. **点「移除」本身零请求**：真正发请求的是 popconfirm 里的「确定」。
3. **checkbox disabled 是后端许可位**：可选应用列表里 `enableDependent=false` 的行（如无版本的 `addressBook`）
   一律 disabled；依赖行 `enableDelete=false` 表示内置依赖不可删（平台 / 集成平台两行虽有「移除」按钮）。

复原验证：加依赖后列表 3 行，移除后回到 2 行（平台 + 集成平台），与操作前一致。

## 5. 沙箱构建全链路（实测一次完整构建，2026-10-22）

```
① POST udc/graphql?udcApplicationSearchDetectionPost      一致性检测（mutation）
② POST udc/graphql?udcRuntimeDeployNormalPost             构建+部署（声明成 query，实为写）
③ POST udc/graphql?udcSandboxBuildInfoAppGet   × 44       约 6s 轮询，state/progress/logs
④ WS  udc_detection_channel / udc_deploy_channel           实时状态
⑤ WS  common-message {appName,status:SUCCESS}              完成通知
⑥ POST ctp-application/appcenter/search-app-edition        刷新版本列表
```

触发方式：设计器工具栏「测试」→ 弹窗「立即构建」（弹窗还有「创建微流程」「从模板创建」入口）。

请求体：

```json
{"query":"query graphqlLoader ($params0: udcRuntimeDeployNormalPostInputBody) { data0: udcRuntimeDeployNormalPost(body: $params0) { code data { content{appId,deployId,deployType,projectType,terminalType} } message status } }",
 "variables":{"params0":{"deployDto":{"projectType":"ALL","terminalType":"ALL","deployType":"RELEASE","appId":"9000000000000000001","generateLog":true}}}}
```

构建信息（`udcSandboxBuildInfoAppGet`，body `{params0:{appId}}`）回包要点：

```
state=SUCCESS  progress=100  totalTime=224  buildVersion=""
logs=["[INFO]【…】[低代码平台] [任务开始] [完成] [耗时:9毫秒]", "…[应用元数据准备] 开始", …]
```

这就是「[展开沙箱日志]」的数据源 —— **构建日志不需要在构建窗口内抓流，一把取全量**。

版本列表（`search-app-edition`，REST 裸数组）：

```json
{"pageInfo":{"needTotal":false,"pageNumber":1,"pageSize":20},
 "params":{"IN_appId":["<appName>"],"clientType":"PC"}}
```

⚠ `IN_appId` 传 **appName**（`datamigration…` 字符串），不是数字 appId；回包不套 code 信封。

WebSocket 帧信封 `{"operate":"<channel>","data":"<json 字符串>"}`：

| operate | 关键字段 |
|---|---|
| `udc_detection_channel` | `status(EXECUTING/SUCCESS)`, `count`, `errorCount`, `seriouCount`, `warnCount` |
| `udc_deploy_channel` | `deployId`, `appName`, `deployType`, `status`, `errorMsg[]` |
| `common-message` | `appName`, `status` |

客户端回帧 `{"businessKey":"ack-business-service"}`。连接在页面加载时建立，后开的面板在 CDP 里
抓不到 `webSocketCreated`。

## 6. 组件依赖（`dependentCmp`，实测加一条再删除复原）

| 动作 | 接口 | 类型 |
|---|---|---|
| 列表 | `POST udc/graphql?udcApplicationDependentApplicationSelectByConditionPost` | 与应用依赖同一口 |
| 候选组件 | 无请求（前端内置 86 行目录） | — |
| 添加 | `POST udc/graphql?udcApplicationDependentApplicationCreateBatchPost`，`dependentAppType=FRONTEND` | 写 |
| 删除 | `POST udc/application/dependent-application/delete-by-ids`，`{"ids":["<行 id>"]}` | 写（REST，非 GraphQL） |

组件行额外字段：`description,dynamicModuleGroup,dynamicService,enableDelete,needGenerate,sort,
supportUpgrade,terminalType,sourceType,packageType`；实测 `packageType=CONTROL`、`sourceType=CUSTOMIZE`、
`terminalType=PC`、`dynamicService=true`。

三个坑：
1. 行内没有「移除」，删除入口在表格上方「批量删除依赖」。
2. 确认框按钮是「取消 / **确认**」，文案「删除后不可恢复! 确定删除吗」。
3. 该 REST 请求用 CDP `requestWillBeSent` 抓不到（事件被 `Runtime.evaluate` 往返吞掉），
   必须在页面里 hook `XMLHttpRequest`/`fetch` 记 `window.__CAP__`。

复原验证：加一条 `@seeyon/biz-lock-sign`（5.3.1，电子签章，web 端）→ 列表 45 行 → 批量删除 → 回到 44 行，
`biz-lock-sign` 不再出现；`SERVICE` 类 11 条（含 `cip-manager`）与 `FRONTEND` 33 条全程未被误改。

## 7. 未验证项（不追认为契约）

1. ~~沙箱构建日志接口~~ —— 已解，`udcSandboxBuildInfoAppGet.logs[]`。
2. ~~组件依赖接口~~ —— 已解，同写口 + REST `delete-by-ids`。
3. 构建弹窗里「创建微流程」「从模板创建」两个入口 —— 未点，接口未知。
4. WebSocket 握手 URL —— 连接建在页面加载时，后开面板抓不到；需新开 tab 从头监听才知道完整地址与鉴权参数。
3. 发布版本列表取数 —— 页面仅发 `latest-test-info`。
4. 「检查通过」的服务端依据 —— 最强候选 `udcApplicationSearchDetectionPost`（依赖增删后自动串发），
   但未取得它的回包，不能断言；禁止用 REST `front-detection`（计数全 0 + `appId=null`）顶替。
5. `udcOperationLogSearch` 的 LIVE 回包 —— 需授权重放一次 mutation 语义的查询。
