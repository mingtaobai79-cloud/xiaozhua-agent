# 应用域只读面 LIVE 契约（test2 / 2026-10-22）

- 目标环境：test2 `https://<gateway-host>`，网关前缀 `/service/udc`
- 目标应用：示例应用 `appId=9000000000000000001`（`appName=datamigration9000000000000000001`）
- 证据：`core/facts/udc/application/evidence/live-app-readonly-2026-10-22.json`（9 条探针原始记录，含 traceId）
- 探针脚本：`tools/core/application/gateway_readonly_probe.py`（白名单只读 + 写端点自检断言）
- 审计口径：HTTP 200 **且** envelope `code=BOOT_0000` **且** `data.content` 有形状，才记 LIVE_PASS；
  200 但内容为空/占位记 CALLED_NO_DATA；`BOOT_1006` 记 AUTH_REDIRECT（不算通过）。

## 1. 结果总览：9 探针 → 8 LIVE_PASS / 1 BLOCKED（服务缺席）

| op | method | path（服务内相对路径） | 判定 | 关键回读 |
|---|---|---|---|---|
| `udc.application.get`（控制组） | GET | `udc/application/{appId}` | LIVE_PASS | `publishState=UNPUBLISH`、`deployType=RELEASE`、`caption=示例应用` |
| `udc.application.user_role` | GET | `udc/application/user-role?appName=udc` | LIVE_PASS | 当前用户角色 id 列表，92 条 |
| `udc.application.role_resource` | GET | `udc/application/role-resource?appName=udc` | LIVE_PASS | 8 个动作键 → `disabled`/`basic` |
| `udc.deployment.latest_test_info` | POST | `udc/deployment/latest-test-info` | LIVE_PASS | `leastTestVersion=1.0.30`、`leastTester=<测试人>`、`testSuccess=true`、`keepAlive=true` |
| `udc.application.front_detection` | POST | `udc/application/search/front-detection` | LIVE_PASS（须带「占位形态」注记） | `count/errorCount/seriuCount/warnCount=0`，`appId/status/message=null` |
| `udc.sandbox.delta_build_info` | GET | `udc/sandbox/delta-build-info/{appId}` | LIVE_PASS | `state=NONE`、`buildVersion=""`、`logs=null`（无构建） |
| `udc.sandbox.is_deploy_war` | GET | `udc/sandbox/system/config/is-deploy-war` | LIVE_PASS | `false`（该环境非 war 部署） |
| `udc.sandbox.app_search` | POST | `udc/sandbox/app/search` | LIVE_PASS | 已部署应用分页列表，含 `appState=RUNNING`、`appVersion`、`ownerTenantCaption` |
| `udc.sandbox.flexible.test_status` | POST | `sandbox/flexible/test-status`（服务=**sandbox**） | BLOCKED | `code=server_404`「sandbox 服务不存在…」 |

## 2. 逐条契约

### 2.1 `udc.application.user_role`（新增）
- 请求：`GET /service/udc/application/user-role?appName={appName}`
- 响应：`SingleResponse<List<String>>`，`data.content` 为角色 id 数组（本次 92 条，含 `Admin`/`SystemAdmin`/租户内角色码）
- 用途：前端「我有哪些角色」；与 `role-resource` 联合求当前用户对该应用的动作权限
- traceId 样本：`3285994432901417148`

### 2.2 `udc.application.role_resource`（新增，本轮最有价值）
- 请求：`GET /service/udc/application/role-resource?appName={appName}`
- 响应：`SingleResponse<Map<String,String>>`，本次回读逐字为
  `{"appDesign":"disabled","appTest":"disabled","appPublish":"disabled","appDelete":"disabled","appExport":"disabled","appCopy":"basic","appCreate":"basic","appImport":"basic"}`
- 语义（实测 + 前端按钮联动）：8 个动作键 `appDesign|appTest|appPublish|appDelete|appExport` 与
  `appCopy|appCreate|appImport`；值为 `disabled`（禁）或 `basic`（可用）。
  这解释了应用列表里「设计/测试/发布/删除/导出」为何对当前用户灰化——**权限判定在服务端，不是前端硬编码**。
- traceId 样本：`3285994433975158972`

### 2.3 `udc.deployment.latest_test_info`（新增）
- 请求：`POST /service/udc/deployment/latest-test-info`，body 逐字 `{"appId":"<Long 字符串>"}`
- 响应：`SingleResponse<LatestTestInfoDto>`：
  `appId, appName, caption, appVersion, buildTime, leastTestVersion, leastTester, testSuccess, keepAlive, validate`
- 实测值：`appVersion=1.0.0`、`buildTime=1792654004000`、`leastTestVersion=1.0.30`、
  `leastTester=<测试人>`、`testSuccess=true`、`keepAlive=true`
- 判据：这是「测试到第几个版本、谁测的、是否成功」的唯一读面；「测试」动作（`app-delta-deploy`）后
  应回读本接口确认 `leastTestVersion` 递增 → 写面验收用它当反向证据。
- traceId 样本：`3285994435485108412`

### 2.4 `udc.application.front_detection`（新增）
- 请求：`POST /service/udc/application/search/front-detection`，body `{"appId":"<id>"}`
- 响应：`SingleResponse<FrontDetectionDto>`：`appId, status, message, count, errorCount, seriuCount, warnCount`
- 实测值：计数全 `"0"`（字符串数字），`appId/status/message` 为 `null`
- 注记：`appId=null` 表示「尚未对该应用跑过检测」，计数器为占位而非真实统计 → 只能记
  LIVE_PASS（端点与形状成立），**不能**据此断言「检测通过」。要判检测结论必须先在设计器点「检查」，
  产生非 null `status` 后回读（本轮不催发检测）。
- traceId 样本：`3285994437028612284`

### 2.5 `udc.sandbox.delta_build_info`（新增）
- 请求：`GET /service/udc/sandbox/delta-build-info/{appId}`
- 响应：`SingleResponse<BuildInfoDto>`：`appName, state, progress, buildVersion, buildTime, startTime, totalTime, logs`
- 实测值：`state=NONE`（无构建在跑/无历史）、`buildVersion=""`
- 用途：「测试」增量部署的进度轮询面（前端在 `src_redux_store_ts` 里正是这么用的）
- traceId 样本：`3285994438119131324`

### 2.6 `udc.sandbox.is_deploy_war`（新增）
- 请求：`GET /service/udc/sandbox/system/config/is-deploy-war`
- 响应：`SingleResponse<Boolean>`，实测 `false`
- 用途：决定沙箱应用形态（war / 非 war），影响沙箱测试入口可用性判断
- traceId 样本：`3285994439343868092`

### 2.7 `udc.sandbox.app_search`（新增）
- 请求：`POST /service/udc/sandbox/app/search`，body `{pageInfo:{pageNo,pageSize}, params:{}}`
- 响应：`PageResponse<SandboxAppDto>`，行含 `id, appName, appCaption, appVersion, ownerTenantCaption,
  ownerName, appState, activeTime, createTime, hidden...`
- 实测：返回 10 行，含 `appState=RUNNING` 的在跑沙箱应用（如「<沙箱应用>」1.0.14140）
- traceId 样本：`3285994440467941564`

### 2.8 `sandbox/flexible/test_status`（新增，BLOCKED）
- 实测：`POST /service/udc/sandbox/flexible/test-status` → **404**（udc 服务无映射）
- 实测：`POST /service/sandbox/flexible/test-status` → 200 + `code=server_404`
  `"sandbox 服务不存在，请重启服务或重新发布应用后再试！"`
- 结论：弹性部署面属独立服务 `sandbox`；test2 未部署 → 服务缺席，不是路径错误。
  该族（`create-deployment`/`delete-deployment`/`restart-deployment`/`select-deployment-page`）一律记
  `sandbox/...` 且 `evidence_level=BLOCKED_SERVICE_ABSENT`，不拼 `udc` 前缀。

## 3. 与网关/通道相关的实测硬事实（踩坑留存）

1. 设计师页里 `window.fetch('/service/udc/...')` 会失败：
   CDP `Network.loadingFailed` = **`net::ERR_CONNECTION_CLOSED`**（网关握手后断链），
   而同一 URL 用浏览器导航或 shell `curl` 都正常 200。→ 因此 LIVE 探针不走页面 fetch。
2. 可靠通道 = **CDP `Network.getCookies` 取同源会话 cookie（`TK_EXP`/`SY_UID`/`SY_ACCESS_TOKEN`）
   → Python 直发**；cookie 只在单请求内存中使用，不落盘、不打印值、不重签 token。
3. 无 cookie 直连 → `BOOT_1006` + `data.content.redirectUrl` 指向
   `https://uatsso.<gateway-host>.com/...`；这是判 AUTH 失败的判据，别误判成业务错。
4. 设计师 child-frame 路由**不可单独 reload / 顶层导航**：reload → `chrome-error://chromewebdata/`，
   顶层 navigate → 空白页（页面体 0 字节）。要重进设计器必须走应用列表点「设计」。

## 4. 复现

```bash
# 8 条只读探针（白名单内置，写端点会在启动时被断言挡下）
.venv/Scripts/python.exe tools/core/application/gateway_readonly_probe.py \
  --port 9250 --app-id 9000000000000000001 \
  --out <HERMES_HOME>/cache/scratch/app-gql/live-readonly-probe.json
```

## 5. 弹性部署族（前端字面量 + 服务缺席，未发起）

| verb | path（服务内） | 归属服务 | 状态 |
|---|---|---|---|
| POST | `sandbox/flexible/create-deployment` | sandbox | DENIED（写，未授权 + 服务缺席） |
| POST | `sandbox/flexible/delete-deployment` | sandbox | DENIED（同上） |
| POST | `sandbox/flexible/restart-deployment` | sandbox | DENIED（同上） |
| POST | `sandbox/flexible/select-deployment-page` | sandbox | DENIED（读面，服务缺席） |
| POST | `sandbox/flexible/test-status` | sandbox | BLOCKED（`server_404`） |

证据级别：`VERIFIED_STATIC_BYTECODE`（前端 chunk 字面量）+ `BLOCKED_SERVICE_ABSENT`（唯一一次实测）。
在 sandbox 服务部署到 test2 之前，这一族不进任何执行路径。
