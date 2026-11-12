# 微流程「真跑一次」的现实边界

生成 → 发布 → 编译通过，都不代表流程跑过。真跑需要一条能落库/能回读的链路，
而这三种能力在 UDC 上是分开的，不能互相替代。

## 1. 三个面各自有什么

| 面 | 端点 | 状态 |
|---|---|---|
| 读 | `POST /service/{APP}/udc-runtime/data/query` body `{"data":{appName, entityFullName, dataId}}` | 可用，BOOT_0000 回读同一条数据 |
| 写 | `POST /service/{APP}/dynamic-rest/com-seeyon/{APP}/{pageUrl}/{APP}/{entityName}/{controlId}/create` | **路由由页面注册**；应用里没有 CRUD/DETAIL 页面时恒定 `BOOT_4002 应用坐标数据不存在` |
| 数据 mutation | `POST /service/udc/graphql` 与 `/service/{APP}/udc-runtime/graphql-proxy/graphql` | `udcFormDataSave/udcDataSave/udcEntityDataCreate` 等候选全 FieldUndefined，**不存在** |

推论：
- 想验证「写库效果」，先得有页面；没页面时不要反复试写接口，那是一条恒 BOOT_4002 的死路。
- 想验证「流程能跑」但手头没写路径，用**定时触发 + 回读/日志**，或**事件触发 + 页面提交一条测试数据**。
- 大字段/多行回读用 dataId 单条查，需要批量条件时另找列表页的路由，不要拼 `/data/query` 的条件参数。

## 2. 设计器按钮语义（两个都是构建入口，不是执行器）

| 按钮 | 实际行为 |
|---|---|
| 测试 | 弹「应用测试 / 本次发布预估时长 / 立即构建」= 构建测试版本 |
| 页面调试(beta) | 弹「会建构页面和页面规则…不适用涉及调用后端服务的更改」= 构建对话框 |

两个对话框点「立即构建」都会占用构建通道（同应用不能并发构建），验证流程时只用来看一眼就点「取消」。

## 3. 定时任务：最小周期可到每分钟

```json
"scheduleCronRule": {"jobCode":"<16字符>","jobCaption":"<任务名>",
  "cronRules":[{"cycleType":"SIMPLE","rotationType":"MINUTE","value":"1",
                 "type":"FIRST","startTime":"<毫秒时间戳字符串>","endTime":null}]}
```

`cycleType` 取值 `SIMPLE/HOUR/MINUTE/DAY/WEEK/MONTH/YEAR`；`SIMPLE` 也带 `type=FIRST`。
把探针流程设成每 1 分钟，等 2–3 个周期即可观察是否真触发——但**不要拿用户真实数据的写流程当探针**
（例如「把草稿全部停用」类），探针必须是无副作用或只写测试行。

## 4. 事件触发的前置条件

事件流程要真跑，前提是「能造出一条数据」。能造数据的路径只有：页面表单提交、或已有写路由。
所以事件流程的验证顺序是：先解决写路径 → 提交带 `ZZ-TEST-<时间戳>` 的测试记录 → 回读该记录
看事件流程改的字段（如 enabled/draft）是否已变 → 清掉测试记录。

## 5. 子微流程（SUB_MICROFLOW）节点形态

```json
{"nodeId":"SUB_MICROFLOW_xxxxxx","type":"ACTIVITY","actionType":"SUB_MICROFLOW",
 "isCompleted":true,
 "output":{"name":"_SUB_MICROFLOW_xxxxxx","type":"OBJECT","dataType":"BOOLEAN",
           "javaType":"java.lang.Boolean","desc":"结果","udcApp":true},
 "mfService":{"id":"<目标流程id>","appId":"<应用id>","caption":"<流程名>",
               "hasInput":true,"hasOutput":true,
               "input":{DTO 入参定义},"output":{出参定义},
               "method":"POST","name":"MFSERVICE<6位>",
               "path":"/microflow/MFSERVICE<6位>","triggerType":"MANUAL","type":"SERVICE"}}
```

`mfService.input/output` 不是手写的，要从目标流程的真实出入参取（它的 trigger.output / endNode）。
`path` 恒 `/microflow/{name}`，说明服务定义自带一个 path 位；但**对外执行路由未验证**，
不要凭这个 path 直接拼 URL 当结论。

## 6. 探针脚本套路

要确认某个按钮/交互到底发了什么请求：

```python
c = CdpClient(9333, allow_network=True); c.connect(url_substr=MID)
c.send("Emulation.setFocusEmulationEnabled", enabled=True)
c.install_fetch_recorder()
# 点按钮（优先直调 fiber onClick）
for it in c.read_captured()[-15:]: print(it["method"], it["url"], it["reqBody"][:200])
```

同一 mid 可能开着多个标签页，`connect(url_substr=…)` 会命中第一个；
先 `list_pages()` 数一遍，多于一个就关掉重开，否则会挂到已经跑偏的旧标签上
（表现为读到的是构建弹窗残留、或 `document.body.textContent` 里是脚本源码）。

## 7. 执行入口在沙箱侧，udc 网关上没有（已实测，别再枚举）

微流程**不在 udc 网关上执行**，跑在每个应用独立的沙箱容器里
（构建产物形如 `chit-acr-registry…/<app>:<version>`，部署进度在「测试」按钮的沙箱面板）。

以下路径已实测，全部没有执行入口：

```
POST /service/udc/microflow/execute          → Whitelabel Error（无路由）
POST /service/udc-runtime/microflow/execute  → server_404「udc-runtime 服务不存在」
POST /service/udc/sandbox/microflow/execute  → Whitelabel Error（无路由）
```

微流程运行日志也不在主站：`POST /service/udc-runtime/app-log/search/microflow`
同样回「udc-runtime 服务不存在」。**运行日志与执行面同在沙箱侧。**

设计器里能打开「微流程运行日志」页（列：名称 / 编码 / 类型 / 所属页面 / 执行状态 / 执行时间），
没有记录时显示「暂无数据」。

★ **「暂无数据」不是验证通过**，它只说明这条流程还没跑过。把它当 RUNTIME 证据，
和「create 当 publish」「空 nodes 当无问题」是同一类错误（见 SKILL.md 铁律零 §4）。

结论：RUNTIME_VERIFIED 的前置是摸清沙箱地址 / 鉴权 / 调用协议。
在那之前只报到 BUILD_VERIFIED，**不许写 RUNTIME**。
