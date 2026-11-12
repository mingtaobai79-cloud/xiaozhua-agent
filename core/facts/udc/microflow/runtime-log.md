# 微流程运行日志（RUNTIME 读侧）— 2026-11-01 LIVE 实测

> 证据等级 **LIVE**（真实返回 211 行，success=211/211）
> 应用 `<APP_NAME>`（test2；appId `<APP_ID>`）

## 1. ★★★ 前缀是应用名，不是 `udc`

```
POST /service/{appName}/udc-runtime/app-log/search/microflow
```

拼 `/service/udc-runtime/...` 会得到
`{"code":"server_404","message":"udc-runtime 服务不存在，请重启服务或重新发布应用后再试！"}`。

★ 这句报错极具误导性——它听起来像「运行时服务挂了」，
实际只是**前缀拼错**。运行态服务挂在应用专属网关下，每个应用一套。

实测对照：

| 路径 | 结果 |
|---|---|
| `/service/udc-runtime/app-log/search/microflow` | `server_404` udc-runtime 服务不存在 |
| `/service/udc/app-log/search/microflow` | Whitelabel 404（无映射） |
| `/service/{appName}/udc-runtime/app-log/search/microflow` | **BOOT_0000，211 行** |

## 2. 请求/响应

```jsonc
// 请求
{"pageInfo":{"needTotal":true,"pageNumber":1,"pageSize":20,"pages":0,"total":0},
 "params":{}}

// 响应
{"status":0,"code":"BOOT_0000",
 "data":{"pageInfo":{"pages":11,"total":211,"needMore":false},
         "content":[{ ...AppLogRow }]}}
```

`AppLogRow` 字段（实测全量）：

```
validate, id, traceId, requestId,
moduleType        = MICRO_FLOW
success           = true/false
logTime           = "2026-11-01 21:46:00"
subModuleType     = MICRO_FLOW_SCHEDULE / MICRO_FLOW_FRONTEND / ...
subModuleTypeName = 定时任务 / 前端触发 / ...
moduleId, caption, nodeId, microFlowCode,
logStartTime, logEndTime   ← 毫秒时间戳字符串，耗时 = end - start
sourceCaption, dataId, signatureUuid
```

## 3. 实测数据（2026-11-01 21:5x）

```
总数     : 211
success  : 211/211（100%），失败 0
触发类型 : 定时任务 211（全部）
时间跨度 : 2026-10-31 23:05:00 ~ 2026-11-01 21:46:00
单次耗时 : min 1ms / avg 188ms / max 1359ms
```

按流程分布：

| 流程 | 次数 |
|---|---|
| 定时-困难-退货信息复刻3109 | 69 |
| 定时-调用子流程与类型转换6676 | 55 |
| 定时-中等-采购同步复刻3091 | 46 |
| 定时-投递验收事件0822 | 39 |
| 1.4 数据迁移同步定时任务 | 1 |
| 定时-简单-保证金提示复刻3091 | 1 |

## 4. UI「暂无数据」≠ 没有日志

设计器「微流程运行日志」tab 打开时显示「暂无数据」，
点「查询」后仍为空 —— 但同一时刻接口返回 211 行。

**UI 的空结果不能当「没有执行」的证据。** 直接读接口。

## 5. 其他日志种类（同一族）

```
/service/{appName}/udc-runtime/app-log/search/microflow   微流程
/service/{appName}/udc-runtime/app-log/search/dataflow    生单规则
/service/{appName}/udc-runtime/app-log/search/deduction   扣减规则
```

body 结构相同（`{params, pageInfo}`），空列表是「无该类日志」而非失败。

## 6. 这条证据能证明什么、不能证明什么

**能证明**：微流程执行链路（调度 → 沙箱执行 → 日志落盘）真实工作，
6 条业务流程在 22 小时内跑了 211 次，全部成功。

**不能证明**：我方构造的流程能真实运行。
这 211 条全部是既有业务流程（`subModuleType=MICRO_FLOW_SCHEDULE`），
没有一条是生成器产出的流程。要证明后者，必须让生成器造的流程真跑一次并读到日志。

## 7. ★★★ RUNTIME_VERIFIED 实证：我方生成的流程真跑了一次（2026-11-01）

前 211 条日志全是既有业务流程，不能证明生成器产出的流程能运行。本节补上这一环。

### 做法

1. 造一条**只读**定时流程（不写业务数据，可安全复跑）：
   `create_variable(ok:BOOLEAN) → retrieve(条件 LIKE %) → change_variable(ok=true)`，
   出参 BOOLEAN。
2. trigger 写 `type=SCHEDULE` + `scheduleCronRule`：

```jsonc
{"jobCode": "<16位随机>", "jobCaption": "<name>",
 "cronRules": [{"cycleType": "SIMPLE", "startTime": "<ms>", "endTime": null,
                "rotationType": "MINUTE", "type": "FIRST", "value": "1"}]}
```

   `SIMPLE` / `DAY` 两种 cycleType 都实测可用（既有 6 条定时流程都是这形态）。
   ★ `value` 的语义**不是**「每 N 分钟」：`value=1` 实测只触发 1 次，
   6 条既有流程的 `value` 是 15/20/25/30/35，实际都按分钟粒度在跑。
   精确周期语义未确证，不要按字面理解。
3. `create` → `publish`（`state=RELEASE errors=0`）
4. **必须构建**：流程要进沙箱才会被调度器执行。
   `POST /service/udc/runtime/deploy-normal` `deployType=RELEASE`
   → `state=SUCCESS buildVersion=20261101215729`
5. 等触发，再按 §1 的接口查日志。

### 结果

```
流程    : rtprobe41422（生成器产出，mid=-5916431194283960544）
运行时间: 2026-11-01 22:03:00
success : true
耗时    : 6ms
触发    : 定时任务（subModuleType=MICRO_FLOW_SCHEDULE）
日志总数: 211 → 212（新增的就是这一条，可归因）
```

### 这条证据链完整覆盖

```
business graph → construct → create → publish(errors=0)
→ build(SUCCESS) → sandbox schedule → execute → log(success=true)
```

即 **BUILD_VERIFIED → RUNTIME_VERIFIED 打通**，且执行体是生成器产出的流程，
不是既有业务流程。

### 仍不能证明的

- **业务结果正确性**：只证明「跑通且平台判成功」，没验证执行后业务数据符合预期
  （只读流程没有可断言的业务副作用）。
- 其他触发方式（`MICRO_FLOW_FRONTEND` 前端触发、子流程调用）未验证。
- 未做并发/失败路径验证。

## 8. ★★★ 节点 output 是「流程结束时的对象快照」，不是该节点执行时刻的值

2026-11-02 实测（写节点验证时发现，代价是差点误判 CHANGE 生效时机）。

流程：`CREATE(123) → RETRIEVE → CHANGE(999) → RETRIEVE → DELETE`

日志里「查初始值」那个 RETRIEVE（在 CHANGE **之前**执行）的 output 显示
`lastOffset=999`。但同一份 output 里 `version=0`，而下一个 RETRIEVE 是 `version=1`。

原因：`CHANGE_ENTITY` **就地修改**了 RETRIEVE 返回的同一个 DTO 对象
（`setLastOffset(999)`），日志在**流程结束时**才序列化这些对象，
所以看到的是被改过的值。`version` 只在读库时刷新，因此没被内存修改影响，
留下 `version=0 + lastOffset=999` 这种自相矛盾的组合。

**判据修正：**

| 想证明 | ❌ 不能用 | ✅ 必须用 |
|---|---|---|
| CREATE 写入值 | 日志里 CREATE 的 output | 数据库行，或 INSERT 后的独立回读 |
| CHANGE 生效 | 日志里「更新成功」 | **数据库行**（改后值 + version + update_time） |
| 任何中间态 | 日志里任意节点 output | 独立快照（另起流程查 / 写入另一个变量） |

这条和 §7 的「只证明跑通」是同一条教训的两面：
**success=true 只说明没抛异常，日志里的数据也不能当中间态证据。**

## 9. ★★★ 流程是单事务：任一节点失败，整条流程的写入全部回滚

2026-11-02 实测，代价是丢掉一整轮证据。

一条 8 节点流程，前 7 个节点全 `success=True`（含 2 次 `CREATE_ENTITY` 返回了
真实 id、1 次 `CHANGE_ENTITY`、1 次 `CHANGE_BATCH_ENTITY` 返回「批量更新成功：2条数据」），
第 8 个 `CREATE_BATCH_ENTITY` 报「违反主键约束」。

流程整体 `success=False`。随后查库：

- 两个 `CREATE_ENTITY` 返回的 id → **0 行**
- `task_id` 前缀查 → **0 行**
- 同一张表其他数据 21 行（表是活的，不是查错表）

**结论：前面所有成功的写操作都被回滚了。流程级事务，不是节点级提交。**

**三条推论（都会影响验证设计）：**

1. **不能把「要取证的节点」和「可能失败的实验节点」放进同一条流程。**
   实验节点一失败，取证节点的数据就没了。这是本轮踩到的真实损失：
   第一次批量实验里 CHANGE_BATCH 明明成功，却因为后面的 CREATE_BATCH 失败而查无实据，
   只能另起一条流程重跑（多花一次 4 分钟构建）。
2. **日志里的节点 success 不等于数据已落库。** 节点可以在事务里成功、随后被整体回滚。
   判据仍然只能是「流程结束后去库里查」。
3. **失败后清理要谨慎**：既然全回滚，失败流程通常不留数据；
   但如果流程中调用了外部系统（接口/消息），那些副作用**不会**跟着回滚。

对应的工程做法：验证流程按「一个待证节点 + 只读铺垫」拆分，
把不确定的构造单独跑一条，先确认它能成功，再和取证链路合并。
