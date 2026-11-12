# 构建/发布 REST 工作流 —— 端到端 LIVE 取证（2026-10-15）

> 链路：设计器点击「测试」→「立即构建」→ GraphQL REST 入队 → sandbox 构建 → 一致性检测 FAIL。
> 全程页面点击 + CDP 抓包（cdp_click.js / cdp_drive.js），无直改。证据：window.__cap 抓包原文 + build-info 日志 + udc_test2 三表对账。

## 1. 用户操作 → REST 的映射（点击构建，实测）

| 页面点击 | 发出的请求 |
|---|---|
| 应用列表行「测试」（数据迁移 8704025620829192834） | 无网络请求（纯前端弹「应用测试」对话框：预估时长、版本号、运行中测试版本 V1.0.7、按钮「取 消/立即构建」）|
| 「立即构建」 | ① `POST /service/udc/graphql?udcDeploymentAppReadyStatePost&udcSandboxBuildInfoAppGet`（就绪态+构建信息联合查询）② `POST /service/udc/runtime/expect-deploy-time`（预估秒数）③ `POST /service/udc/graphql?udcDeploymentLatestTestInfoPost` ④ **`POST /service/udc/graphql?udcRuntimeDeployNormalPost` ← 入队构建** |
| 应用列表行「发布」 | 弹「发布应用」对话框（推送到实施/生产 radio、锁定应用 switch、版本 checkbox）；未勾版本提交 → toast「请选择发布版本」；勾选后提交 → **toast「当前应用有修改,请先测试发布后再上线!」**（服务端/前端校验：必须先 TEST 发布成功才能 ON_ONLINE）|

### deploy-normal 请求原文（构建入队）

```
POST /service/udc/graphql?udcRuntimeDeployNormalPost
{"query":"query graphqlLoader ($params0: udcRuntimeDeployNormalPostInputBody) {
  data0: udcRuntimeDeployNormalPost(body: $params0) {
    code data { content{appId,deployId,deployType,projectType,terminalType} } message status } }",
 "variables":{"params0":{"deployDto":{
   "projectType":"ALL","terminalType":"ALL",
   "deployType":"RELEASE","appId":"8704025620829192834","generateLog":true}}}}
```
响应：`BOOT_0000 SUCCESS`，`content={appId, deployId:-2139846499842280759, deployType:RELEASE, projectType:ALL, terminalType:ALL}`

注意：设计器「测试」按钮发的 deployType 也是 **RELEASE**（DeployTypeEnum.RELEASE=测试发布；ON_ONLINE=上架，被「先测试后上线」闸门挡住；DELTA=增量）。

### 部署状态轮询（LIVE 证实读面）

```
POST /service/udc/graphql?udcRuntimeSearchDeployStatusDeployIdPost
variables.params0 = {deployId}
→ content[0] 全字段：validate,id,deployId,appId,appGuid,sourceType(NORMAL),appName,tag,flowId,buildId,
  projectType,terminalType,state(SUCCESS|FAIL|RUNNING),msg,appVersion,schemaStorageKey,sqlStorageKey,
  deployType,createTime,creator,schemaMd5,businessType(STANDARD),imageUrl,buildVersion,jarVersion,
  udcVersion,pushEnv,compileLogUrl
```
本次实测：`state=FAIL`，`buildVersion=20261015153648`，`jarVersion=1.0.8`，`udcVersion=5.3.517`，`creator=-2638952494757493308`（=sy_uid）
就绪态：`GET/POST udcDeploymentAppReadyStatePost` → `{state:RUNNING, msg:DEPLOY_SUCCESS}`（应用运行中但上次构建失败的状态语义）

## 2. 构建日志（build-info，FAIL 现场 9 行）

```
[2026-10-15 15:36:48] 任务开始(12ms) → 应用元数据准备(4s)
→ 一致性检测：PageDetectionTask 完成(3s)，检测完成(5s)
→ 生成后端代码：开始 →
[ERROR] 失败原因:业务异常[请点击链接:
  https://lowcode-test2.example.com/main/child-frame/udc/app-design/basic-info/page-by-id/1520098474917276520?appId=8704025620829192834，
  补全实体数据源错误：页面控件配置的字段不存在，udcDataGridView_xzh1->null]
[ERROR] 结束 发布失败: 业务异常[一致性检测未通过],报错位置:
  com.seeyon.udc.pipeline.AbstractDeployService.doParallel(AbstractDeployService.java:242)
```

**一致性检测是并行的**（doParallel: AbstractDeployService.java:242），PageDetectionTask 是其中一个检测任务；检测不过直接终止，不进编译。

## 3. FAIL 根因三方对账（页面 schema × 实体属性 × 报错）

- 报错控件：`udcDataGridView_xzh1`（「小爪实验表格」，页面 1520098474917276520 = SEARCH_LIST「小爪实验页面951440」，publish_state=1，schema_state=2，update_time 2026-10-14 13:52）
- 页面 schema（udc_test2.udc_page_schema.page_schema，3823B）：dataSource 绑定实体 474806313816300867（xzhExp950795），**`fields:[]`、`fieldBindMap:{}`**，columns=[expText(STRING), expEnum(CTPENUM)]
- 实体属性（udc_test2.udc_attribute，entity_id=474806313816300867，is_system=0）：expText/expEnum/expDate/expFlag/expMembers/expNum 等 9 个，**全部存在**
- 结论（FACT 级差异）：报错「页面控件配置的字段不存在，udcDataGridView_xzh1->null」**不是列字段缺失**（两列都在实体里），而是 **dataSource.fields 为空 + fieldBindMap 为空**——即「实体数据源未补全字段绑定」。`->null` 指的是 fields 绑定清单里取不到该控件需要的字段集。修复方向=设计器里打开该表格控件重新选择/补全字段（对应报错给的 page-by-id 链接），不是去实体加字段。
- `schema_state=2` + 页面 10-14 被保存过 + 构建 10-13 成功过（1.0.7）⇒ 10-14 的页面改动引入了空 fields 绑定，10-15 构建才首次撞上检测。

## 4. 状态机语义（本次实测归纳）

```
应用列表「测试」→ deploy-normal(RELEASE) → deployId
  → 轮询 search-deploy-status：RUNNING → SUCCESS（appVersion 升位，如 1.0.8）
  → FAIL（一致性检测/编译失败，msg 带定位链接）
测试发布 SUCCESS 后 → 「发布」→ deploy-normal 或 app-online（ON_ONLINE）
  → 有未测试修改时被闸门拦截："当前应用有修改,请先测试发布后再上线!"
「发布」对话框选项：推送到实施/推送到生产（pushEnv）、锁定应用（lock，设计态禁改）
预估时长：expect-deploy-time(deployParamDto{deployType,appId,projectType,terminalType}) → 秒数字符串（本次 292）
```

## 5. GraphQL 面的规律（复用要点）

设计器对 udc-web 的读/写**统一走 `/service/udc/graphql?<opName>`**，query 骨架固定：
`query graphqlLoader ($paramsN: <opName>Input<Path|Body>) { dataN: <opName>(path|body: $paramsN) { code data { content } message status } }`
操作名 = 控制器方法 camelCase 拼接（udcRuntimeDeployNormalPost = DeployController#deployNormal）。此前 REST 直发的 `/service/udc/runtime/deploy-normal` 路径同样存在（控制器有 @PostMapping），但前端实际走 GraphQL 聚合面。**复刻工作流时优先按前端真实形态（GraphQL）发。**

## 6. 下一步（已定位未执行）

1. 设计器打开页面 1520098474917276520，补全 udcDataGridView_xzh1 的字段绑定（点击操作），抓补全请求
2. 重新点「测试」构建至 SUCCESS，然后走「发布」→ ON_ONLINE 全链
3. 沉淀 BUILD-DEPLOY 状态机护栏测试进 xiaozhua-agent

## 6. ★★ GraphQL 状态查询的确切写法（2026-11-01 实测，三次失败才试对）

```
POST /service/udc/graphql?udcRuntimeSearchDeployStatusDeployIdPost

query g($p: udcRuntimeSearchDeployStatusDeployIdPostInputPath) {
  data0: udcRuntimeSearchDeployStatusDeployIdPost(path: $p) {
    code data { content } message
  }
}
variables = {"p": {"deployId": "<deployId>"}}
```

### 三个坑（全部实测踩过）

| 写法 | 结果 |
|---|---|
| `$p: udcRuntimeSearchDeployStatusDeployIdPostInputBody` + `body: $p` | `UnknownType` / `UnknownArgument body` |
| `$p: udcRuntimeSearchDeployStatusDeployIdPostInput` + `path: $p` | `UnknownType` |
| `$p: String!` + `path: $p` | `GraphQL_3000 java.lang.String cannot be cast to java.util.Map` |
| **`$p: ...PostInputPath` + `path: {deployId}`** | **BOOT_0000，content[0] 全字段** |

### 返回结构

```
{data:{data0:{code:"BOOT_0000", data:{content:[{
   validate, id, deployId, appId, appGuid, sourceType, appName, tag, flowId,
   buildId, projectType, terminalType, state, msg, appVersion, buildVersion,
   jarVersion, udcVersion, compileLogUrl, createTime, deployType
}]}}}}
```

★ content 在 `data0.data.content`，**不在 data0 顶层**（少解一层就拿到空）。

### ★★★ delta-build-info 不能用来轮询 RELEASE 构建

`GET /service/udc/sandbox/delta-build-info/{appId}` 只保留**最近一次完成的
delta 结果**。RELEASE 构建根本不写这里。

实测：RELEASE 触发后连查 10 分钟，`state` 一直是 10-31 的 `FAIL`、
`startTime=1793382828188` 一动不动；而 `search-deploy-status` 一查就是
`state=SUCCESS, buildVersion=20261101194735, jarVersion=1.0.89`。

后果：加了 `_is_stale` 之后会变成「永远 stale → 一直等到超时」，
看起来像构建卡住，实际早就成功了。

**正确做法**：按 deployId 查 search-deploy-status；delta-build-info 只在
没有 deployId 时作兜底。

### 构建前置：一致性检测 ERROR 必须为 0

本次构建一开始被挡，原因不是代码问题：

```
[ERROR] 查询数据源:实体属性已更改(ID)
  文档: UI最终化探测        | 元素: 查询数据源
  文档: 验收3-多字段-524500 | 元素: 查询数据源
```

两条旧测试流程引用的实体属性 ID 已失效。删掉后检测
`13 WARN → 11 WARN，ERROR=0`，构建才真正启动。

## 7. ★★ Cookie 端口：9222 有登录态，9333 没有（2026-11-01 踩坑）

`BOOT_1006 token黑名单` 出现时，**先确认连的是哪个 CDP 端口**，别急着判登录过期：

```
port 9222: cookies=88  SY_ACCESS_TOKEN = [.<SSO_DOMAIN>(311),
                                          <APP_HOST>(311),
                                          localhost(315)]     ← 有登录态
port 9333: cookies=75  SY_ACCESS_TOKEN = 无                   ← 没有
```

9333 上页面能打开（title 显示「数据迁移」），但**API 调用全是 BOOT_1006**。
只凭页面能开就判「登录有效」是错的。

取 cookie 的正确姿势（`document.cookie` 读不到 httpOnly，返回空串）：

```python
from providers.cdp import CdpClient
c = CdpClient(9222, allow_network=True, timeout=20); c.connect()
cs = (c.send('Network.getAllCookies') or {}).get('cookies') or []
ck = '; '.join('%s=%s' % (x['name'], x['value'])
               for x in cs if str(x.get('domain') or '').endswith('<SSO_DOMAIN>'))
```

9222 是 `localhost:3000` 前端，但 cookie 里带着 test2 的 SY_ACCESS_TOKEN
（`.<SSO_DOMAIN>` 共享域 + 手动注入），所以能直接调 test2 后端。
