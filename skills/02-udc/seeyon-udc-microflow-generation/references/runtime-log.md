# 运行验证（RUNTIME_VERIFIED）

> 代码：`components/udc/microflow/live/runtime_log.py`
> 事实：`core/facts/udc/microflow/runtime-log.md`（LIVE，211→217 行实测）

## ★★★ 路径前缀是应用名，不是 `udc`

```
POST /service/{appName}/udc-runtime/app-log/search/microflow   ✅
POST /service/udc-runtime/app-log/search/microflow             ❌
```

拼错时返回：

```json
{"code":"server_404","message":"udc-runtime 服务不存在，请重启服务或重新发布应用后再试！"}
```

**这句话误导性极强**——听起来像运行时服务挂了，实际只是前缀错。
运行态服务挂在应用专属网关下，每个应用一套。

★ **用 appId 当前缀（`/service/<appId>/…`）会报同一句「服务不存在」，但用应用名就正常**——
两条路径只认应用名。探活判断「运行时是否活着」必须用应用名路径，用 appId 路径探出来的
「服务挂了」是假信号（实测一次假信号浪费了一整轮排查，实际调度一直在跑）。

实测：拼错查 3 次全 404，改对一次就拿到 211 行。

## 三种日志只差最后一段

```
/service/{appName}/udc-runtime/app-log/search/microflow   微流程
/service/{appName}/udc-runtime/app-log/search/dataflow    生单规则
/service/{appName}/udc-runtime/app-log/search/deduction   扣减规则
```

body 相同：`{"pageInfo":{...},"params":{}}`

★ **微流程日志的过滤键是 `code`（流程名）**：`params:{"code":"p5xxx123"}` 才真过滤。
传 `microFlowId` / `microFlowCode` 都会被忽略并原样返回一批旧记录（看着像「查到了」）。
拿到一批记录先核对每条的 `microFlowCode` 是否就是你那条，否则整批证据都作废。

## AppLogRow 关键字段

```
moduleType        = MICRO_FLOW
success           = true / false
logTime           = "2026-11-01 21:46:00"
subModuleType     = MICRO_FLOW_SCHEDULE（定时）/ MICRO_FLOW_FRONTEND（前端）
subModuleTypeName = 定时任务
caption / microFlowCode / nodeId
logStartTime, logEndTime   ← 毫秒时间戳字符串，耗时 = end - start
traceId / requestId / dataId / signatureUuid
```

## 失败要看步骤详情，不只看 success=false

```
POST /service/{appName}/udc-runtime/app-log/search-details/microflow
{"params":{"traceId":"<traceId>"},
 "pageInfo":{"needTotal":true,"pageNumber":1,"pageSize":50,"pages":0,"total":0}}
```

返回按 `stepNum` 排的逐步记录：`activityType` / `activityCaption` / `success` /
`input` / `output` / `errorMsg`。失败步骤的 `errorMsg` 带平台异常全文，
能直接定位到字段级校验失败。

- ★ **traceId 在一次调度批次里被多条流程共享**：按 traceId 查会捞到同批次其它流程的
  步骤（`microFlowCode` 不同），必须再用 `microFlowCode` / `nodeId` 过滤，
  否则会把别人的失败算到自己头上。
- `params.logId` 查不到（返回空 content），用 `traceId`。

## ★★★ 「这个接口为什么返回 null」：三步定位到节点

被问「这个 URL / 接口为什么 null」时，不要从参数猜起。固定三步：

```
① 定流程  search/microflow 按 microFlowCode 找行，统计 success
② 定节点  flowLog 按 traceId 拉整条链，找第一个 success=false
③ 定分支  udc-runtime/data/query 读业务行，用状态字段解释为什么走那条分支
```

### flowLog：一次拿整条链（不分页、不串味）

```
POST /service/{appName}/udc-runtime/app-log/search-details/microflow/flowLog
{"microFlowCode":"mFSERVICE…","subModuleType":"MICRO_FLOW_MANUAL","traceId":"<traceId>"}
```

- **三个键都必填**：缺 `microFlowCode` → `BOOT_1001 microFlowCode must not be null`；
  缺 `subModuleType` → `BOOT_1001 subModuleType must not be null`（值照抄日志行的 `subModuleType`）。
- ★ **只有 `traceId` 能命中**。`id` / `logId` / `dataId` / `signatureUuid` / `moduleId` 全部返回
  `BOOT_0000 + content:null`——看着像成功，其实是没匹配到。别拿它们当过滤键。
- 返回 `data.content.flowLogs[]`，按 `stepNum` 排：`activityType` / `activityCaption` / `nodeId` /
  `success` / `input` / `output` / `errorMsg`。
- 读法：`START` 的 `input` 就是调用方真实传的参；**第一个 `success=false` 的步骤就是根因节点**，
  `nodeId`（如 `CHANGE_VARIABLE_akcoXT`）可直接拿去设计器定位。
- 同族的 `search-details/microflow`（分页版）按 `params.traceId` 也能查，但会混入同批次其它流程，
  需要再按 `microFlowCode` 过滤；只想看一条流程的完整链路就用 flowLog。

### 判据：判「服务是否成功」只认它自己的日志行

前端微流程（`MICRO_FLOW_FRONTEND`）调服务失败时，它自己那行**仍可能 `success=true`**——
它只表示规则跑完了，不表示被调服务成功。实测同一时段前端规则 9 次里 2 次 success，
而它调的服务 11 次全失败。**两个 `microFlowCode` 分开统计**，别用前端的成功掩盖服务的失败。

### `BOOT_3000` + `message:null` + `data:null` 的含义

流程内抛异常时平台回的就是这个壳：流程没加「自定义错误」节点，异常没被兜住，
`message` 自然是空的，真实文案只在节点级 `errorMsg` 里。
**「BOOT_3000」不等于「参数没传对」**——空 body 照样进流程（START 里字段全 null）然后在某节点炸。
要让它变成可读错误，得在流程里补 `CUSTOM_ERROR`。

### 分支走向用业务数据反推

```
POST /service/{appName}/udc-runtime/data/query
{"appName":"<appName>","dataId":"<主键>",
 "entityFullName":"com.seeyon.<appName>.domain.entity.<Entity>"}
```

→ 单条业务记录全文。拿状态字段（`statusType` / `terminateStatusType` / `nullifyStatusType` 之类）
就能解释「为什么条件判 false、走了 else 分支」，比猜表达式快得多。缺 `dataId` 时报错文案直接点名缺哪个键。

### 设计态查不到 = 改不了，先确认再谈修

运行态还活着但设计态记录不在时，三个接口同向给出：

```
udcMicroflowSearch(appId=<appId>)     → UDC_APP_0001 The application is not exist
udcMicroflowSearchAppsPost(appId=…)   → BOOT_3000 源对象不能为空
udcMicroflowFindByIdGet(id=<flowId>)  → BOOT_4002 Data does not exist or has no permission
```

对照组：同应用下另一个真实 flow id 调 `FindByIdGet` 会 `BOOT_0000`，证明查询形态没问题、
是目标对象真不在。含义是「应用被 copy 后删除」或「当前账号无权限」。
此时 `dataSchema` 拿不到，**具体哪个字段空指针只能停在「节点 id + errorMsg」这一层**：
汇报里明确标未验证，下一步是恢复/重建流程或要设计权限，**不要继续猜表达式**。

### 取会话：页面内 fetch 优先，必要时内存取 cookie 走 curl

页面上下文 `fetch(..., {credentials:'include'})` 是首选。要连着打几十次日志查询时，
也可以 `Network.getCookies(urls=["https://<host>/"])` 从**任意已开 target** 取一份会话
（只内存、不落盘、不重登），用 curl 发只读 POST。**绝不为了拿会话重新登录**——
一次登录会让同身份旧 token 全部作废。

## 判据：不许用「没输出」当「没问题」

`assert_ran(host, cookie, app_name, code)`：

| 情形 | 行为 |
|---|---|
| 日志里没有该流程的记录 | **抛错**（不能判 RUNTIME_VERIFIED）|
| 有记录但 `success != true` | **抛错**，带上失败行 |
| 存在且全成功 | 返回 `{runs, latest}` |

`return []` 是「没数据」，不是「没问题」——这个坑在 UI 复测上已经踩过两次。

## UI「暂无数据」≠ 没有日志

设计器「微流程运行日志」tab 显示「暂无数据」，点「查询」仍为空，
但**同一时刻接口返回 211 行**。UI 的空结果不能当「没执行」的证据，直接读接口。

## 怎么让我方流程真跑一次（RUNTIME_VERIFIED 完整链路）

```
business graph → construct → create → publish(errors=0)
→ build(SUCCESS) → sandbox schedule → execute → log(success=true)
```

1. **造只读流程**（不写业务数据，可反复跑）：
   `create_variable(ok:BOOLEAN) → retrieve(条件 LIKE %) → change_variable(ok=true)`
2. **trigger 写 SCHEDULE**：

```jsonc
{"type":"SCHEDULE","caption":"定时任务",
 "scheduleCronRule":{"jobCode":"<16位随机>","jobCaption":"<name>",
   "cronRules":[{"cycleType":"SIMPLE","startTime":"<ms>","endTime":null,
                  "rotationType":"MINUTE","type":"FIRST","value":"1"}]}}
```

3. `create` → `publish`
4. **必须构建**（流程不进沙箱就不会被调度器执行）
5. 等触发 → `assert_ran(...)`

### ★ `value` 不是「每 N 分钟」

`value=1` 实测**只触发 1 次**，不是每分钟。既有 6 条定时流程的 value 是
15/20/25/30/35，实际都按分钟粒度在跑。精确周期语义未确证，别按字面理解——
**要验证就用「至少跑一次」作为判据，不要等 N 次**。

## ★★ 写路径怎么断言「数据真的写进去了」

读路径能靠 `success=true` 交差，写路径不行——流程可能「执行成功」而数据是错的。

### 先做一件事：查目标实体有没有「默认值表达式」

**这是写验证的前提检查，跳过它所有结论都不可信。**

```bash
# 在构建产物 zip 的源码里查（见 references/build.md）
grep -c 'executeExpression' backend/*-biz/**/domain/service/<Entity>Service.java
```

非 0 就要看 `preCreateBatch` 里每个调用的第二个参数：

```java
executeExpressionXxx(list, false, Dto::getF05dec, this::exp…, Dto::setF05dec, null);
//                    ↑ requireNull
```

| `requireNull` | 行为 | 能不能用来做写验证 |
|---|---|---|
| `true` | 字段为空时才填 | ✅ 可以，传了值就不会被盖 |
| `false` | **无条件覆盖** | ❌ **你传的值会被完全丢弃** |

表达式常见形态是 `DateFunction.currentYear()` / `currentDateTime()`（→ 当年 / 当前时间）。
若字段还配了约束（如 `≤100`、`≤999.99`），表达式结果可能**天然违反实体自己的约束**，
导致该实体**永远插入不了任何数据**，传什么值都一样。

选实体优先级：**表达式数 = 0** > 只有 `getUpdater` > 有业务字段表达式（不能用）。
还要叠加一条：AppService 必须有 `create`（`CREATE_ENTITY` 生成的是
`xxxAppService.create(SingleRequest)`，没这个方法构建就报「找不到符号」）——
两者同时满足的实体的很少，别随便挑一个就开始跑。

### 判据：两个条件同时成立才算 RUNTIME_VERIFIED

```jsonc
// 节点详情（search-details/microflow）里的 CREATE_ENTITY 步骤
input : {"id":4526324842265571554,        // ← 平台生成的 ID（= 真 INSERT 了）
         "taskId":"P5VFY…",                  // ← 逐个对上你传的值
         "lastOffset":123, "processedRows":456, …}
output: 插入成功返回ID：4526324842265571554   // ← 平台明确返回了入库 ID
```

1. **`input` 里每个字段的真实取值逐个对上你传的值** ⇒ attrs 生效
2. **`output` 含「插入成功返回ID：<id>」且 `id` 是平台生成的** ⇒ 真入库

两条缺一不可。只看 `success=true` 不够（可能被默认值表达式盖成别的值照样成功），
只看 `input` 也不够（那是 insert 前快照）。

### ⛔ 已废弃的判据（别再用）

曾记过「用实体校验当断言：默认值违规 → INSERT 失败 ⇒ attrs 没生效」。**这条是错的**，
因为它默认了「平台只在字段为空时才填默认值」，而实际可能是无条件覆盖。实测后果：
同一个错误判据得出「attrs 不生效」的结论，把方向带偏一整轮。

判据的通用教训见 SKILL.md「铁律零 §5 判据不能依赖被测对象自己的配置」。

### 没找到干净实体时怎么办

不硬凑判据，直接降级取证：拉构建产物 zip 看 `Rtv…Service.java` 里
`assignValue2JavaBean…` 生成的 `javaBean.setXxx(值)` —— 那是编译期事实，
比任何运行时推断都硬。但注意它只能证明「值传到了 create()」，
**不能证明「落库没被改」**，两者是不同层级的结论，报告时要分开说。

## ★★★ 写路径的最终判据是物理表：怎么找表 + 必须带对照组

运行日志的节点 `output` **不能当中间态证据**（原因见 SKILL.md 铁律零 §4.1：
CHANGE 就地改了 RETRIEVE 返回的同一个 DTO，日志在流程末尾才序列化）。
写节点的结论只能落到数据库行。

### 先找对表：实体名 ≠ 表名

同一应用库里常有多张“看着像”的表（`migration_checkpoint` 与 `migration_1962…`
就是两个不同实体）。**先筛候选、再用历史数据证表是活的：**

```sql
-- ① 按业务字段名找候选表
SELECT table_name, column_name FROM information_schema.columns
 WHERE table_schema='<appDb>' AND column_name IN ('task_id','taskid');

-- ② 逐表确认哪张才有数据（非 0 的那张才是）
SELECT COUNT(*) FROM <appDb>.<表> WHERE task_id LIKE '<你的标记>%';

-- ③ 看表里有没有逻辑删除列
SELECT column_name FROM information_schema.columns
 WHERE table_schema='<appDb>' AND table_name='<表>' AND column_name LIKE '%del%';
```

**只查「删后 0 行」不算证据——表本身可能就是空的。** 必须同时拿到
一条已知存在的对照行（本例：目标 id 查 0 行，另一个 id 查 1 行），
否则“0 行”只证明你查错了表。

### 删除语义：先看列，再下结论

| 表里有 `deleted` / `is_deleted` / `del_flag` | 判据 |
|---|---|
| 无 | 物理删除：目标 id 查 **0 行** + 对照 id 查 **1 行** |
| 有 | 逻辑删除：目标 id 仍在但该列为真；不能只看“查不到” |

**逐表确认，不许外推**——不同实体的删除实现不一样。

### 改值类节点分两条流程跑

因为日志不能证明中间态，`CREATE → RETRIEVE → CHANGE → RETRIEVE → DELETE`
这种链路拿不到“改前值”。正确拆法：

1. **流程 A（不删）**：`CREATE(旧值) → RETRIEVE → CHANGE(新值) → RETRIEVE`，
   跑完直接查库：新值 + `version` 递增 + `update_time` 晚于 `create_time` ⇒ 更新已持久化。
2. **流程 B（含删）**：在同一条链尾部加 `DELETE`，验证删除与全链路串联。

两条都要构建（沙箱才会执行），各自保留证据；不要用“整条流程最终成功”代替单节点证据。

## 能证明 / 不能证明

**能证明**：流程从生成到沙箱执行的整条链打通，执行成功有日志可归因。

**已证到 RUNTIME_VERIFIED 的**：
- 只读定时流程：`publish → build(SUCCESS) → 定时触发 → log(success=true)`
- **`CREATE_ENTITY` 写节点**：字段逐个对上 + `output` 返插入 ID（前提：无默认值表达式且有 `create`）
- **`CHANGE_ENTITY`**：库内两字段变更 + `version` 0→1 + `update_time` 变化
- **`DELETE_ENTITY`**（SELECT_PARAM 模式）：目标 id 查 0 行 + 对照 id 查 1 行 + 表无逻辑删除列
- **`CREATE_BATCH_ENTITY` / `CHANGE_BATCH_ENTITY`**：999 被批量写回 111、两行 `update_time` 同毫秒
- **`BREAK`**：同一条流程内双循环对照（对照 3 行 / 实验 1 行）——控制节点也能用「读侧行数」作证
- **`CALL_DATA_FLOW`**（CONDITION 形态）：`udc_rt_data_flow_log` 记 `dataflow_mapping_id=<行 id>`、`is_success=1`

**不能证明**：
- `PUBLISH_BUSINESS_EVENT`：应用内事件走进程内 EventBus，无订阅者时投递无痕（只到 LIVE_EXECUTED）
- `CALL_DATA_FLOW` 的 `SELECT_PARAM` 形态；源实体有数据时目标实体的写入形态
- `CALL_APP_SERVICE` / `DATA_MAPPING`：停在 CONSTRUCTED（缺零副作用的真实对象）
- `DELETE_ENTITY` 的 `IDS` 模式未实测；`CONDITION` 模式只能常量右值（见 SKILL.md §4.2）
- 前端触发（`MICRO_FLOW_FRONTEND`）、子流程调用
- 并发、失败路径、超时
- **BUILD_VERIFIED ≠ RUNTIME_VERIFIED**，反之亦然
