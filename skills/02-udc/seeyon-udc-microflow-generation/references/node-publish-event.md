# PUBLISH_BUSINESS_EVENT（事件投递）运行时证据

> 2026-11-02 实测于 test2。结论：**代码已生成并编译、运行无异常，但没有订阅者 → 投递本身观测不到**。
> 所以只能升到 LIVE_EXECUTED，不能升 RUNTIME_VERIFIED。

## 1. 节点形态（语料 9 个样本裁决）

| 键 | 值 | 样本数 |
|---|---|---|
| `eventType` | `IN_APP`（应用内，走 EventBus） | 7 |
| `eventType` | `AMONG_APP`（应用间，走 MQ，用 `selectMq` + `messageType`） | 1 |
| `selectEvent` | 应用内事件对象（来自 `udcMicroflowSearchEventListPost`） | 7 |
| `selectMq` | 应用间 topic + contentDto | 1 |
| `mappingType` | `attrs` | 8 |

仓库构造器 `microflow_nodes_extra.publish_business_event` 走的是 **IN_APP**
（`selectEvent` + `eventType=IN_APP`），与 7/9 样本一致。跨应用的 `selectMq` 形态**未实现**。

## 2. 代码生成语义（模板证据）

`BusinessEventActivity.java.ftl`：

```ftl
<#if activityNode.eventType == "IN_APP">
    ${mfEvent.fullName} dto = new ${mfEvent.fullName}();
    <@setValueForMessageOrEvent activityNode dtoName />      ← 逐字段 set
    eventPublisherHelper.publishEntityEvent(dto, EventPublisher.EventPhase.TRANSACTION_COMMIT_SUCCESS);
```

两个关键点：

1. **事件在事务提交成功后投递**（`TRANSACTION_COMMIT_SUCCESS`）。
   所以流程回滚时事件不会发出；流程失败也不会留下「事件已发但数据没落」的残留。
2. **应用内事件走进程内 EventBus，不写 `ctp_mq` 表**。
   没有订阅者时，投递成功也只意味着「总线上没人收」——**任何表都不会有记录**。

## 3. 本轮实测

事件对象：`com.seeyon.<APP>.dto.microflow.event.XzhVerifyEvent`
（「小爪验收事件」，字段 `eventCode` STRING / `bizKey` BIGINTEGER / `remark` STRING）

流程：`CREATE_VARIABLE(载荷) → PUBLISH_BUSINESS_EVENT(attrs 三个字段)`

```
publish: True
构建: SUCCESS 269s
执行: 2026-11-02 18:19:00 success=True
```

投递前后对照：

| 表 | 投递前 | 投递后 |
|---|---|---|
| `ctp_mq` | 0 | 0 |
| `ctp_eventbus_dynamic_subscribe` | 0 | 0 |
| `ctp_mq_dynamic_subscribe` | 0 | 0 |

**能证明的**：构建能把事件 DTO 全类名 + 3 个字段映射渲染成合法 Java 并编译通过
（名字错一个就编译失败），运行期也没抛异常 → 节点配置是真实生效的。
**不能证明的**：事件真的被谁收到了（没有订阅者，EventBus 无痕）。

## 4. 要升 RUNTIME_VERIFIED 还缺什么

需要一个**订阅方**，把「收到事件」变成可读侧数据：

```
流程 A：PUBLISH_BUSINESS_EVENT(XzhVerifyEvent, eventCode=MARK)
流程 B：触发器 = MICRO_FLOW_EVENT / XzhVerifyEvent → CREATE_ENTITY(task_id=MARK+'R')
判据   ：库内出现 task_id=MARK+'R' 的行
```

模板侧已确认可行（`BusinessEventListener.java.ftl` 支持 `messageSource` 为
`EVENT` / `MICRO_FLOW_EVENT`，用 `@EventHandler @EventSubscribe`）。

但语料里 56 个事件触发器样本**全是实体 CRUD 事件**（`AfterUpdateEvent` 这类，
`messageSource=EVENT`），**没有任何 `MICRO_FLOW_EVENT` 触发器的真实样本**。
自己拼触发器的 messageInfo 字段属于猜测，所以本轮没做。

## 5. 跨应用形态（未实现）

`AMONG_APP` 用 `selectMq`：

```json
{"eventType": "AMONG_APP",
 "selectMq": {"key": "UDC_<APPNAME>_MQ.<dto>", "topic": "UDC_<APPNAME>_MQ",
              "contentDto": {"type": "<dto full>"},
              "customs": {"from": "udc", "eventDataType": "OBJECT", "source": "MICRO_FLOW"}},
 "messageType": "DEFAULT"}
```

还要 `app` 和延迟消息的 `executeTime`。构造器目前不支持，需要真实跨应用事件对象才能验。

---

## 5. 补验（2026-11-03）：自建订阅者，载荷级证明

上一轮结论是「没有订阅者 → 只能 LIVE_EXECUTED」。本轮自建订阅者补上。

### 5.1 订阅者形态

触发器 `type=BUSINESS_EVENT` + `messageInfo.messageSource=MICRO_FLOW_EVENT`：

```json
{"caption":"小爪验收事件","messageSource":"MICRO_FLOW_EVENT","eventFullName":null,
 "eventDataFullName":"com.seeyon.<app>.dto.microflow.event.XzhVerifyEvent",
 "eventMfCustomDtoName":"<同上>","eventName":"xzhverifyevent","currentId":"xzhverifyevent",
 "currentType":"microflow",
 "output":{"id":"<同上>","dataType":"DTO","type":"OBJECT","javaType":"<同上>","appName":"<app>"}}
```

订阅端引用事件字段（21 条真实样本的形态）：

```
position="children"
key="<触发output名>_<dto全名>.<字段>"
path="<dto去点>.<字段>"
dtoType="CUSTOM", udcApp=false
```

直接按普通节点字段引用会报「引用了尚未执行的节点」。

### 5.2 实测

发布端 `p6svc6sv01` 投 `eventCode=P6SV01 / bizKey=20261103 / remark=p6-svc`；
订阅端 `p6evt6sv01` 把收到的 `eventCode`、`remark` 写进库。

```
09:56:00  task_id=HT2026113  source_table=SN        ← 同一次执行里的流水号
09:56:00  task_id=P6SV01     source_table=p6-svc    ← 订阅端收到的载荷，逐字相等
```

**载荷级证明**：不是「有个事件触发了」，而是「订阅端收到的字段值就是发布端投的那些值」。

### 5.3 等级

`PUBLISH_BUSINESS_EVENT`：LIVE_EXECUTED → **RUNTIME_VERIFIED（应用内 IN_APP）**。
应用间 `AMONG_APP`/MQ 形态、延迟投递仍未验。
