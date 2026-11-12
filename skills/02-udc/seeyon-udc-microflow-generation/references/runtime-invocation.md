# 微流程怎么被真正触发：三类入口、路由判读、子流程调用

只讲「流程跑起来」这条线。生成/发布/编译见 SKILL.md。

## 1. 三类触发方式的真实形态

| 触发 | trigger.type | trigger.isCompleted | 顶层 input | 真实触发源 |
|---|---|---|---|---|
| 手动/服务 | `MANUAL` | true | 与 `trigger.output` 同体 | 页面规则、服务定义对外接口、子流程调用 |
| 定时 | `SCHEDULE` | true | null | 平台调度器 |
| 业务事件 | `BUSINESS_EVENT` | true | `= trigger.output`（事件数据入参） | 实体增删改事件、应用消息 |

`isCompleted` 漏了 → 设计器里触发节点是**红色未完成态**，而 publish/checkSchema/编译全绿。真实语料 100% 带。

## 2. 定时任务的最小周期

`scheduleCronRule.cronRules[0]`：

```json
{"cycleType":"SIMPLE","rotationType":"MINUTE","value":"1",
 "type":"FIRST","startTime":"<毫秒时间戳字符串>","endTime":null}
```

`cycleType ∈ SIMPLE/HOUR/MINUTE/DAY/WEEK/MONTH/YEAR`；SIMPLE 时也带 `type=FIRST`。
要验证「定时真的会跑」，用 SIMPLE+MINUTE+1，不要用天/周级周期等不起。

## 3. 业务事件：直接吃事件对象，不回查

事件载荷里实体挂在子节点 `info`：

```
name=info   id=<eventMfCustomDto>.info   path=<eventMfCustomDto 去点>.info
```

直接 `CHANGE_ENTITY(selectParam=该 info 引用)`。**不要**先按 id 查单条再改 —— 事件对象里根本没有 ids 列表，
`IDS` 集合查询的参数必然是空的，设计器里那格显示为空的黄色必填，部署阶段直接「一致性检测未通过」。

选完事件前端会发 `POST /service/udc/graphql?udcMicroflowFindCustomDtoPost`（`dtoFullName=eventMfCustomDtoName`）
做一次确认；不发则事件节点显示异常。

**事件被某条流程监听后，就不再出现在 `udcMicroflowFilterEventPost` 的候选列表里**（列表里消失 = 已被占用）。
要复用就改现有流程，不要新建一条监听同一事件 —— 否则会互相触发/冲突。

## 4. 子微流程（SUB_MICROFLOW）节点形态

```json
{"actionType":"SUB_MICROFLOW","type":"ACTIVITY","caption":"子微流程(1)","isCompleted":true,
 "mfService":{"id":"<被调流程 id>","appId":"...","caption":"...","hasInput":true,"hasOutput":true,
   "input":{DTO 入参（含 javaType/dtoType/CUSTOM 等）},
   "output":{"dataType":"BOOLEAN","javaType":"java.lang.Boolean",...},
   "method":"POST","name":"MFSERVICExxxxxx","path":"/microflow/MFSERVICExxxxxx",
   "triggerType":"MANUAL","type":"SERVICE","restType":...}}
```

要点：**入参/出参必须从目标流程的真实定义拉**（`DP.get(target)` 的 trigger.output / endNode），手搓 DTO 类型过不了编译。
`mfService.path` 恒为 `/microflow/{serviceName}`，`serviceName` 不等于流程 caption，也不等于 flow `name` —— 不要拿 caption 拼。

## 5. 运行态路由判读表（别再重复试）

| 请求 | 响应 | 含义 |
|---|---|---|
| `POST /service/{appName}/udc-runtime/data/query` | JSON，缺参时给 `appName 应用编码; dataId 数据id; entityFullName 实体FullName` | 应用 runtime 网关**通**，这是可用的读路径 |
| `POST /service/{appName}/dynamic-rest/com-seeyon/{appName}/{任意}` | `BOOT_4002 应用坐标数据不存在` | 第一段是**页面坐标**，微流程没有坐标；换后缀无效 |
| `POST /service/{appName}/udc-runtime/udc/{XxxAppService}/{name}` | 404 Whitelabel | 该控制器没注册到这个应用的 runtime |
| `POST /service/udc-runtime/udc/CustomMicroFlowAppService/{name}` | JSON `udc-runtime 服务不存在，请重启服务或重新发布应用` | 控制器族存在，但挂在**平台级 app**，不是本应用 |
| `GET` 同一个 dynamic-rest 前缀 | 与 POST 同样 4002 | 该前缀不分方法，别靠换 HTTP 方法绕 |

## 5.1 ★★★ 服务定义流程的对外调用 URL（已打通）

```
POST /service/{appName}/{hostPath段}/microflow/{serviceName}
例：/service/<appName>/<页面url段>/microflow/MFSERVICEM50Ue3
```

- **中间那一段（hostPath）不能省**：省掉直接 404 Whitelabel。它取自 mfService 的
  `hostPath`/页面 url 段，不是流程名、也不是分组名，**照抄用户给的 URL 最稳**。
- 入参 = 流程 `trigger.output` 的字段（本例 `{"zuofeiyuanyin":"…","hetongID":1306575606616940162}`），
  平台自己补 `validate:true`。

★ **URL 三段怎么拼（2026-11-04 从构建产物 controller 逆向确认）**：

1. **serviceName = 流程 `name`**（不是 caption，也不是平台加的前缀——那些 `MFSERVICExxxxxx`
   是用户建流程时自己起的 name）。构建产物里 `name=Xxx` 生成 `XxxService.java` +
   AppService 方法 `xxx(...)`，URL 里最后那段就是流程 name。
2. **hostPath = `@RestApi` 的 value**（页面 url 段）。构建产物 controller 里
   `@RequestMapping("appName")` + `@PostMapping("{hostPath}/microflow/{serviceName}")`，
   例 hostPath=`qyfapzlb`（`@RestApi(value="qyfapzlb")`）。
3. **只有「关联页面」的流程才有 REST controller**：controller 方法带
   `@ResourcePermission(pageInfo=..., resourceInfo="<页面id>_udcToolBar_xxx")`（页面控件事件
   关联了该流程）。纯服务定义流程（无页面关联）只有 `@AppService` 方法、没有 `@PostMapping`
   controller，同结构 URL POST 是 404 Whitelabel（实测 mftestman01）。

判据：`POST /service/{appName}/{hostPath}/microflow/{serviceName}` 空 body →
`BOOT_3000`=路由存在且流程真跑了；404 Whitelabel=该流程无 controller（未关联页面）。
批量验证要 MANUAL 秒触发，流程得先关联页面控件事件（生成 controller），或走 AppService
框架的调用路由（该路由仍未确认）。

### 判读表（一条请求就能定性，别再枚举后缀）

| 请求 | 响应 | 含义 |
|---|---|---|
| `GET` 该 URL | 405 Whitelabel `Method Not Allowed` | 路由**存在**，只收 POST |
| `POST` + 任意 body | 200 + `BOOT_3000 message:null data:null` | 路由存在且**流程真的跑了**，流程内抛异常（不是参数校验）|
| 应用名换成不存在的 | 200 + `server_404 "<name> 服务不存在，请重启服务或重新发布应用后再试！"` | 应用服务**没部署** |
| `serviceName` 换成不存在的 | 404 Whitelabel | 该应用下没有这条服务 |
| 去掉中间 hostPath 段 | 404 Whitelabel | 段不能省 |

★ **空 body 不会被绑定层拒绝**：它照样进流程，`START` 的 input 里字段全是 `null`，
然后在某个节点炸掉。所以「BOOT_3000」不等于「参数没传对」，**要按流程异常去查**
（见 `references/runtime-log.md`「接口返回 null」）。

★ 诊断线上**写类**流程（作废/更新/删除）时**不要拿真实业务主键去试**——流程一旦真的跑通就改了业务数据。
用空 body 观察失败路径，或用日志里已有的失败 traceId 复现。

## 6. 页面侧写路径（验证写库要用）

写：`POST /service/{APP}/dynamic-rest/com-seeyon/{APP}/{pageUrl}/{APP}/{entityName}/{controlId}/create`
—— 路由来自**页面注册**；没有 CRUD/DETAIL 页就恒 `BOOT_4002`。
GraphQL 数据面 mutation 不存在（`udcFormDataSave/udcDataSave/udcEntityDataCreate` 等全 FieldUndefined）。
验证「写库效果」前先确认应用里有能写的页面，否则先做入口，不要先怀疑流程逻辑。

## 7. 抓真实请求的姿势

`CdpClient.install_fetch_recorder()` + `read_captured()` 能拿到 `{kind,url,method,reqBody,status,respBody}`，
适合确认「某个按钮到底发了什么」。注意：页面 `document.hidden=true` 时 `innerText` 恒空，读文本一律 `textContent`。
