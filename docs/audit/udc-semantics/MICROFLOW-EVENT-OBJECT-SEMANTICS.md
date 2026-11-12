# 微流程「事件对象」语义闭合契约（B-5）

> 切片：B-5（P2 子片）｜ 环境：test2 ｜ 应用：`datamigration9000000000000000001`（appId `8704025620829192834`）
> 写授权：**0 写**（本轮纯读）｜ `/service` 调用：**0 次**（全部输入取自已落盘样本 + 本地反编译 + 只读 SQL）
> 证据等级：STATIC（CFR 0.152 反编译 udc-biz/udc-plugin-api 5.3.517）+ SAMPLE（已落盘 JSON）+ LIVE（MySQL 只读实测）
> 生成时间：2026-10-18

---

## 0. 一页结论（先看这里）

事件对象在本平台是**三条互不相同的链路**，共用 `EventSourceEnum` 的枚举名但**不共用同一张表**：

| 链 | 名称 | 载体 | 是否落 `udc_event` 表 |
|---|---|---|---|
| **A** | 订阅/触发（微流程作为监听方） | `udc_microflow_info.data_schema.trigger`（`type=BUSINESS_EVENT`） | **❌ 不落表**，整块存在微流程 JSON 里 |
| **B** | 投递（微流程作为发布方） | 节点 `args.actionType=PUBLISH_BUSINESS_EVENT` 的 `selectEvent` | **❌ 不落表**，靠 `fullName` 字符串引用 |
| **C** | **用户自定义业务事件对象（事件注册）** | `udc_event` + `udc_data_transfer_object`（DTO） | **✅ 唯一落表者** |

**最容易被误判为"实体事件注册表"的东西，其实不是表。**
`udcEventListEventsPost`（实体×9 事件）返回的是 `presetData/event/defaultevent.json` **模板按实体现推的虚拟事件**，一条 DB 行都不读（`EntityEventLoader.listEntityEvents()`，STATIC 已证）。全库 **1814 个实体**（LIVE `udc_entity` 计数；本应用 9 个）× 9 模板 = 约 16326 个"实体事件"，而 `udc_event` 里 `source=ENTITY(0)` 只有 **1 行**——这个 1:16326 的落差就是证据。（本应用口径：9 实体 × 9 = 81 个虚拟事件 vs 1 行落表）

**一句话语义**：`udc_event` 不是事件日志，也不是实体事件注册表；它是**自定义事件对象的元数据**（B 链投递目标的定义体），`event_data` 指向承载事件 payload 结构的 DTO 根。

---

## 1. 三链的字段级契约

### 1.1 链 A —— 订阅/触发（微流程监听外部事件）

载体：`udc_microflow_info.data_schema` 顶层 `trigger` 对象，`type = BUSINESS_EVENT`。

**SAMPLE（本应用 `xzhEvtAhN7` / id `-1516089433318810738`，LIVE DB 回读）**
```json
{
  "nodeId": "CUSTOM_AhN7Q2", "name": "CUSTOM_AhN7Q2", "caption": "事件监听",
  "type": "BUSINESS_EVENT",
  "output": { "id": "com.seeyon.bpm.dto.message.event.BpmStartEvent",
              "name": "_FLOW_OUTPUT_evt2", "javaType": "...", "dataType": "DTO",
              "type": "OBJECT", "desc": "事件数据", "appName": "bpm", "dtoType": "" },
  "messageInfo": {
    "caption": "流程发起消息",
    "messageSource": "MESSAGE",
    "eventDataFullName": "com.seeyon.bpm.dto.message.event.BpmStartEvent",
    "topic": "BPM",
    "currentId": "BPM.com.seeyon.bpm.dto.message.event.BpmStartEvent",
    "currentType": "bpm",
    "output": { "id": "...", "dataType": "DTO", "type": "OBJECT", "javaType": "...", "appName": "bpm" }
  },
  "expression": null, "title": "事件数据"
}
```

**`messageSource` 与 `topic` 严格互斥（LIVE 量化）**

**分母口径（D18 强制，唯一允许写法）**
`BUSINESS_EVENT` **trigger**（= `data_schema.trigger` 且 `type=BUSINESS_EVENT`，即微流程的监听触发节点）全库 **254 个**：
- **244 个具 `messageInfo`** —— 互斥断言的**唯一真实分母**
- **10 个为空壳监听节点（无 `messageInfo`）** —— 不参与互斥断言，单列形态（§1.1a）

| messageSource | 节点数 | topic 是否非空 | 语义 | 对应 `EventSourceEnum` |
|---|---|---|---|---|
| `EVENT` | 81 | **否（0/81）** | 应用内实体事件 | `ENTITY(0)` |
| `MICRO_FLOW_EVENT` | 33 | **否（0/33）** | 应用内微流程事件 | `MICRO_FLOW_EVENT(2)` |
| `MESSAGE` | 130 | **是（130/130）** | 跨应用 MQ 消息（BPM/组织/消息中心/连接器） | 无对应（MQ 世界） |

合计数 81+33+130 = **244**，与具 `messageInfo` 的节点数相符。

> **`None` 不是 `messageSource` 的枚举值**（重要区分，auditor R4 指出）：
> - 正确读法分两行：① `trigger` 节点 254 = **244 具 messageInfo** + **10 空壳（无 messageInfo）**；② 具 `messageInfo` 域内 `messageSource` = `{EVENT:81, MESSAGE:130, MICRO_FLOW_EVENT:33}`
> - 错误读法：把 `None:10` 和三个枚举值并列——会让人以为平台有 `None` 这个枚举值
> - 实质区别：空壳不是"`messageSource` 的值为 None"，而是**根本没有 `messageInfo` 字段**，`messageSource` 在该处不存在。前者暗示枚举缺值，后者只是结构缺失。

**唯一允许的表述**：
> 「`BUSINESS_EVENT` trigger 节点全库 **254** 个（每微流程 1 个，可一一对应）；其中 **244 个具 `messageInfo`**，互斥断言在这 244 条上成立（**违反 0 例**）；另 **10 个空壳节点**（无 `messageInfo`）不参与断言，形态 = `CUSTOM 1 + SERVICE 9`，跨 4 个应用。」

**分母争议留痕（255 / 254 / 244 三个数字必须分清）**
| 数字 | 含义 | 是否为断言分母 |
|---|---|---|
| **254** | `data_schema.trigger` 中 `type=BUSINESS_EVENT` 的**真实 trigger 节点数**（每微流程最多 1 个） | 形态统计的基数 |
| **244** | 上述 254 中**具 `messageInfo`** 者 | ✅ **互斥断言的唯一分母** |
| **10** | 254 中无 `messageInfo` 的空壳 | 不参与 |
| ~~255~~ | **错误数字，已废弃** | 由**遍历缺陷**产生：把 `nodes[0]/value/selectParam/nodeInfo` 里的 trigger **引用**（`{entityCaption,nodeId,type}` 三键）误计为独立 trigger 节点 |
| ~~11~~ | 同上，错误空壳数（10 真空壳 + 1 个 nodeInfo 引用） | — |
| ~~"occurrence vs unique 差 1"~~ | **不成立** | 254 本就一一对应，无重复键；所谓"重复"是 nodeInfo 引用与 trigger 共用同一 `nodeId` 造成的假象 |

> **根因（必须记住，防止复发）**：`data_schema` 里 `type=BUSINESS_EVENT` 的**对象**有两类——
> ① `data_schema.trigger`：真正的监听触发节点；
> ② `data_schema.nodes[*].value.selectParam.nodeInfo`：节点参数里对 trigger 的**引用快照**（键仅 `{entityCaption,nodeId,type}`）。
> 任何"全库 trigger 统计"都必须**只取 `data_schema.trigger`**，不能递归遍历全 `data_schema`——否则会把引用计入，多出 1 个。
> 早期版本（255/11）与 main D18 的 occurrence 口径（255，含"唯一重复键"）**均源于此遍历缺陷**；auditor 的 254/10 数字正确，但其 `messageSource` 表把 `None:10` 混入统计域（那 10 条无 `messageInfo`，不在域内）。
> **【D22 终裁】** main 已正式撤回 D18 的 occurrence=255 / unique=254 / 唯一重复键三项，并确认其 `main_b5_denom_v2.py` 的 `walk(ds)` 与本档早期遍历缺陷**同源**（所谓"独立取证"不独立）。权威计数 = **254 节点 / 244 具 messageInfo / 10 空壳**，一一对应，**不存在 occurrence/unique 之分**。口径纪律（以 `/trigger` 位为准、禁任意深度）已升级为平台级，进 B-3 取证模板。

> 组合计数 `(messageSource, 有topic)` = `{('EVENT',False):81, ('MESSAGE',True):130, ('MICRO_FLOW_EVENT',False):33}`，**零例外**。这是 B-5 里最硬的一条互斥断言。

`topic` 实际取值分布（130 条非空）：`BPM` 98、`UDC_ZNXMGLPT3289082814923688017_MQ` 16、`UDC_XIANGMUGUANLI1656355078954763084_MQ` 5、`UDC_ZNXMGLPTCOPY5791640252914287064_MQ` 5、`UDC_XIANGMUGUANLICOPY7001530513149673721_MQ` 3、`AFFAIR` 2、`UDC_YZNXMGL121386570299241515796755_MQ` 1。

**登记侧契约**（前端，见 `MICROFLOW-BUSINESS-EVENT-TRIGGERS.md` §2，已 FOCUSED VERIFIED）：
- 应用内 → `udcMicroflowFilterEventPost`，硬编码 `sourceTypes:["ENTITY"]` + `eventTypes:["ENTITY_EVENT"]`
- 应用间 → `udcMicroflowSearchAppsPost` → `udcMicroflowFilterMqPost`

### 1.1a 空壳监听节点（10 个，独立形态）

`data_schema.trigger.type=BUSINESS_EVENT` 但**无 `messageInfo`** 的节点，全库 **10 个**（占 254 中 4%）。它们是"监听节点已建、数据源未配置"的有效中间态，不是坏数据。

**键集合（10 个完全一致）**：`{caption, description, input, name, nodeId, output, type}`
```json
{"nodeId":"SERVICE_QnvTfh","name":"SERVICE_QnvTfh","caption":"事件监听",
 "description":"","type":"BUSINESS_EVENT","input":null,"output":null}
```
**分布**：`SERVICE` 9 个 + `CUSTOM` 1 个，跨 **4** 个应用（逐个可核）
- `3289082814923688017` — 6 个：`MFCUSTOM1NQOZa`(CUSTOM)、`MFSERVICE1UObFN`、`MFSERVICE4DfyMz`、`MFSERVICEKlp1Gn`、`MFSERVICEqcowKl`、`MFSERVICEK8q51U`
- `2378987216360786643` — 2 个：`MFSERVICEFNm5Ve`、`MFSERVICEsxTrIB`
- `1656355078954763084` — 1 个：`MFSERVICE3sfACo`
- `7001530513149673721` — 1 个：`MFSERVICEQKaa9b`

> 计数留痕：main D22 写「跨 5 应用」，实测为 **4**（6+2+1+1=10，逐 app 已列全）。以实测 4 为准。

**业务含义**：这 10 个节点在"事件订阅"维度是空绑定——微流程存在、节点占位，但既无 `messageSource` 也无 `topic`，运行时不会收到任何事件。做微流程事件覆盖率统计时**必须把这 10 个单独剔出分母**，否则会把"未配置"算成"已订阅"（覆盖率高估 10/254 ≈ 3.9%）。

#### 1.1a-附 易混淆项：`nodeInfo` 引用碎片（不是 trigger，1 个）

`data_schema.nodes[*].value.selectParam.nodeInfo` 里会出现 `{entityCaption, nodeId, type:"BUSINESS_EVENT"}` 三键对象 **1 个**：
```json
{"entityCaption":"bpm回退事件触发内容","nodeId":"SERVICE_sfEkP6","type":"BUSINESS_EVENT"}
```
位置：`MFSERVICEjpYUxQ`（mf id `1538454905995064000`），**路径 `nodes[0].value.selectParam.nodeInfo`**。

**它不是 trigger 节点，是服务节点参数里对 trigger 的引用元数据。三条排除判据**：
1. **路径**：位于 `nodes[]` 内，不在 `trigger` 位
2. **键集合**：无 trigger 形态必备的 `name`/`caption`/`input`/`output`/`messageInfo`，仅 3 键
3. **同一 nodeId 的 `/trigger` 位已存在且有 `messageInfo`**（`SERVICE_sfEkP6`，`has_message_info=True`），已在 244 里计入；再算一次 = **重复计数**

**两种统计口径的差值（A/B/C 对照，LIVE 实跑）**
| 口径 | 计数 | 是否正确 |
|---|---|---|
| **A** 只数 `/trigger` 位（`type==BUSINESS_EVENT` 且位于 `trigger` 键下） | **254** | ✅ **唯一正确口径** |
| **B** 任意深度求 `type==BUSINESS_EVENT` | 255 | ❌ 含 1 条引用碎片 |
| **C** B − A | 1 | 该差值完整路径 = `/nodes[0]/value/selectParam/nodeInfo` |

> **口径纪律（平台级，已进 B-3 取证模板）**：统计 trigger 节点**必须以 `/trigger` 位为准**；**禁用「对全 JSON 任意深度求 `type==BUSINESS_EVENT`」**——该口径会把 `selectParam.nodeInfo` 引用碎片计入（本实例 +1）。审此类数字改动时，不能只数 key，必须问「**这个 dict 在 JSON 树的哪个位置**」。

**两个后果（第二个更严重，必须写出来）**
1. §1.1a 说空壳「运行时不会收到任何事件」——对 10 个真空壳成立，但**对这条引用碎片不成立**：`SERVICE_sfEkP6` 的 `/trigger` 有 `messageInfo`，是**正常订阅节点**。
2. 若按 B 口径（255）剔分母，会把这个**已配置**的节点当成"未配置"剔掉——**正好造成 §1.1a 那条纪律想避免的错误**。即：用错误的遍历口径去做"防止高估覆盖率"的修正，反而制造了低估。

> 争议留痕：本文档早期误记为「空壳形态 B」；main D18 曾解读为「同微流程内重复出现 → occurrence 255 / unique 254」、D20 曾定性「同 nodeId 两形态并存」。经 D21（main 按 JSON 路径独立验证）与 D22（main 终裁撤回 occurrence 口径）确认：**三者同属一个遍历口径缺陷，实际只有 254 个 trigger 节点，一一对应，不存在 occurrence/unique 之分**。

### 1.2 链 B —— 投递（微流程发布事件/消息）

载体：节点 `args.actionType = "PUBLISH_BUSINESS_EVENT"`。

**SAMPLE（本应用 `PUBLISH_BUSINESS_EVENT_x17`）**
```json
{
  "actionType": "PUBLISH_BUSINESS_EVENT",
  "eventType": "IN_APP",
  "selectEvent": {
    "key": "com.seeyon.datamigration9000000000000000001.dto.microflow.event.XzhEntityEvent",
    "value": "<同 key>", "fullName": "<同 key>", "label": "小爪实体事件",
    "caption": "小爪实体事件", "source": "ENTITY", "dtoType": "CUSTOM", "udcApp": true
  },
  "mappingType": "attrs",
  "attrs": [ { "value": {"type":"SelectParam","selectParam":{...}}, "attrType":{...}, "desc":"实验文本 [文本]" } ]
}
```

**全库量化（4755 微流程，LIVE）**

| 维度 | 分布 |
|---|---|
| `PUBLISH_BUSINESS_EVENT` 节点总数 | **72** |
| `eventType` | `IN_APP` 35 / `AMONG_APP` 37 |
| `selectEvent.source` | `MICRO_FLOW` 34 / **`null` 37** / `ENTITY` 1 |
| `selectEvent.fullName` 去重 | 28（含 1 个 `null`） |

**关键结构事实**：`eventType` 与 `selectEvent.source` 不是正交的，而是**同源二选一**——
- `eventType=AMONG_APP`（37）⇔ `selectEvent=null`（37），构建期尚未选定跨应用目标
- `eventType=IN_APP`（35）⇔ `selectEvent` 非空（35）

> 即：`selectEvent` 缺失不代表坏数据，而是 `AMONG_APP` 态的正常表现。**把 `selectEvent=null` 判为脏数据是错的。**

**`selectEvent.fullName` 的两套包路径（易错点）**

| 引用对象 | 包路径 | 实例 |
|---|---|---|
| 实体事件（虚拟，链 A 侧） | `…dto.microflow.event.<Name>` | `…dto.microflow.event.XzhEntityEvent` |
| 微流程事件（真实 DTO） | `…dto.microflow.message.<Name>` | `…dto.microflow.message.Jiaqianshijian` |

`udcEventListPost_all.json` 49 条样本的 `eventDataFullName` **全部落在 `dto.microflow.message`**，无一条在 `dto.microflow.event`。`event` 包只出现在 `eventClassName`（见 §2.2）。

### 1.3 链 C —— 事件对象注册（`udc_event` 表）

**表结构（LIVE `SHOW COLUMNS`，25 列，全列）**

```
id bigint PK | create_time | tenant_id | update_time | version | guid | publish_state
action_type smallint NOT NULL        ← EventActionTypeEnum
app_id bigint NOT NULL MUL
caption varchar(255) | description varchar(255)
enabled tinyint NOT NULL             ← 是否启用
event_data bigint NOT NULL           ← → udc_data_transfer_object.id（DTO 根）
event_data_type smallint NOT NULL    ← ObjectTypeEnum (OBJECT/LIST)
exp_design_data longtext             ← 触发条件（表达式设计值）
exp_runtime_data longtext            ← 触发条件（表达式运行值）
message_tags varchar(127) | message_topic varchar(127)
name varchar(127) | number_fired_once varchar(20)
source smallint NOT NULL             ← EventSourceEnum
source_id bigint NOT NULL            ← 语义随 source 变化（见 §2.3）
owner_code | backup_code | message_type smallint NOT NULL | original_id
```

**唯一约束（STATIC，`@Table` 注解原文）**
```
uk_udc_event_aid_sid_name_tid = (app_id, source_id, name, tenant_id)
```

**表上没有的字段（重要否证）**：不存在 `event_class_name` / `event_data_full_name` / `event_mf_custom_dto_name`。
这三个名字只出现在**读接口返回 DTO**（`EventQueryResultDto`）里，是**运行时拼出来的**，不是存储列。任何"从 udc_event 读 eventClassName"的假设都不成立。

**实体事件类名的权威生成规则（STATIC）**
```java
// EventService.supplementEventData(...) L492
dto.setEventClassName(EVENT_PACKAGE + StringUtils.capitalize(dto.getName()));
// EVENT_PACKAGE = "com.seeyon.udc.common.event."
// EventDto.getClassName() L94-96
public String getClassName() { return StringUtils.capitalize(this.getName()) + "Event"; }
```

**校验（SAMPLE 49 条，零反例）**：`className == capitalize(name)+"Event"` → **49/49 命中，0 不符**。
（样本边界同 §2.1 D15 必写项：该 49 条 ≡ UPDATE 子集，但 `className` 派生规则是纯字符串函数（STATIC 字节码 `EventDto.getClassName()`），与 actionType 无关，规则本身不受切片影响。）

---

## 2. 字段语义逐条闭合

### 2.1 六个枚举（STATIC，CFR 反编译 `udc-plugin-api-5.3.517.jar`）

| 枚举 | 取值（code, name） | DB 列 |
|---|---|---|
| `EventSourceEnum` | `ENTITY(0,"实体")`, `MICRO_FLOW(1,"微流程消息")`, `MICRO_FLOW_EVENT(2,"微流程事件")` | `source` |
| `EventActionTypeEnum` | `CREATE(0,"create")`, `UPDATE(1,"update")`, `DELETE(2,"delete")`, `SELECT(3,"select")` | `action_type` |
| `ObjectTypeEnum` | `OBJECT(0)`, `LIST(1)` | `event_data_type` |
| `MessageTypeEnum` | `DEFAULT(0,"普通消息")`, `DELAY(1,"延时消息")` | `message_type` |
| `EventTriggerTypeEnum` | `BEFORE(0,"before")`, `AFTER(1,"after")`, `TRANSACTION_SUCCESS(2,"transactionSuccess")`, `TRANSACTION_EXCEPTION(3,"transactionException")` | **无列**（`triggerType`，事件实体级默认 AFTER） |
| `EventTypeEnum` | `ENTITY_EVENT(0,"实体事件")`, `BUSINESS_EVENT(1,"业务事件")` | **无列**（`type`，默认 BUSINESS_EVENT） |

**DB→API 枚举映射全量校验（LIVE，49 条 × 10 字段 = 490 断言）**
```
字段映射校验: ok=490 bad=0
```
10 个字段：`source / eventDataType / actionType / messageType / enabled / name / caption / eventData / numberFiredOnce / sourceId`。
**证据分级（auditor R3 建议，已采纳）**：
- **在 UPDATE 切片上**：10 字段 × 49 行 **零漂移**（LIVE 实测 `ok=490 bad=0`）
- **CREATE 不在该切片**：`action_type=0` 的 3 条全在快照外，**CREATE 的 DB↔API 映射不是这 490 条验出来的**，而是由字节码 `EventActionTypeEnum.<clinit>`（CREATE=0/UPDATE=1/DELETE=2/SELECT=3）**STATIC 确证**
- 故准确表述为「**在 UPDATE 切片上零漂移；CREATE/DELETE/SELECT 的映射为 STATIC 字节码确证，非 LIVE 验证**」——不可简化为「一一对应、零漂移」让下游误以为全枚举都 LIVE 验过
- 切片内字段覆盖明细：`source` 仅验 `{1}`（全库 `{0,1,2}`）、`action_type` 仅验 `{1}`（全库 `{0,1}`）、`event_data_type` 验 `{0,1}`、`message_type` 验 `{0}`（全覆盖）、`enabled` 验 `{0,1}`（全覆盖）

> **【D15 必写项】样本边界声明——该 49 条不是 DB 全集**
> `udcEventListPost_all.json`（REST 快照）已确证 ≡ DB `action_type=UPDATE(1)` 的**精确子集**：
> `|snapshot|=49 = |DB action_type=1|=49`，集合双向差为 0（auditor `b5_action_filter_proof.py`，CONFIRMED）。
> 全库 52 行按 action_type 分档：`UPDATE 49 全在快照` / **`CREATE 3 全不在快照`**（即本应用 3 条 CREATE 形态事件经快照**不可得**）。
> **快照结构性只含 UPDATE，CREATE/DELETE/SELECT 经快照不可得（行为已证，机制 UNVERIFIED——未抓请求体/Controller，过滤成因未知）。**
> 因此 490 断言的有效范围 = **UPDATE 形态事件的 DB↔API 映射**；CREATE 形态的字段映射靠本应用 4 条 DB 行 + auditor javap 字节码（`EventActionTypeEnum: CREATE=0/UPDATE=1/DELETE=2/SELECT=3`，**STATIC_BYTECODE**）钉死，不依赖快照。

### 2.2 `name` → `className`（不含 Event 后缀）

- 存储 `name`（如 `xzhEntityEvent`）→ 派生 `className = capitalize(name) + "Event"` = `XzhEntityEvent`
- 实体事件另有 `eventClassName = "com.seeyon.udc.common.event." + capitalize(name)`（**注意此处 name 不含 Event 后缀**，如 `AfterCreate` → `com.seeyon.udc.common.event.AfterCreate`）
- `eventDataFullName` 与 `className` **不是同一个东西**：前者是 DTO 全名，后者是事件类短名

### 2.3 `source_id` 语义随 `source` 变化（**最大语义陷阱**）

| source | source_id 指向 | 全库实测 |
|---|---|---|
| `ENTITY(0)` | `udc_entity.id` | 1 行，指向 `xzhExp950795`（`474806313816300867`）✅ |
| `MICRO_FLOW_EVENT(2)` | `udc_microflow_info.id` | 1 行，指向 `xzhEvtAhN7`（`-1516089433318810738`）✅ |
| `MICRO_FLOW(1)` | **`0`（无绑定）为主**，偶见实体 id | 50 行：**48 行 `source_id=0`**、1 行指向微流程、1 行指向实体 |

> **`source_id=0` 是合法值，不是脏数据。** 它表示"该业务事件对象未绑定到某个来源"，因为业务事件由用户在实体页手工定义、payload 走 `event_data` 的 DTO，不需要来源实体。
> 48/50 为 0 是本表最反直觉的地方——**用 `source_id != 0` 过滤会丢掉 92% 的业务事件**。

### 2.4 `event_data` —— 指向 DTO 根（服务端注入，非前端传入）

**STATIC 铁证（`EventWithDataAppServiceImpl.createWithEventData` L107-130）**
```java
// 1. 先建 DTO
dtoResp = this.dtoAppService.createDtoWithAttrs4EntityEvent(request);
if (!dtoResp.success() || isNull(dtoResp.getData().getContent()))
    throw new BusinessException("UDC_EVENT_0002", dtoResp.getMessage());
Long dtoId = (Long) dtoResp.getData().getContent();
// 2. 服务端回填 eventData
eventAndDataDto.setEventData(dtoId);
// 3. 再建事件
Long eventId = this.eventService.create((EventDto)eventAndDataDto);
```

**推论（重要）**：`eventData` **不是前端填的字段**，是服务端把刚建的 DTO id 回填进来的。所以：
- 前端传 `eventData` 无效（会被覆盖）
- 走 `udcEventCreateWithDataPost` 时**必须**带 `eventDataList`（否则 `UDC_EVENT_0002`），这个约束的根因就是上面这段代码
- 走不带数据的 `udcEventPost` 时，`eventData` 由调用方自己给，但后续 `selectWithEventData` 会按 `eventData` 去 DTO 表反查 root，查不到就是 `null`（本应用 `474806313816300867` 三个事件全部 MISS）

**DTO 侧交叉验证（LIVE）**：`event_data → udc_data_transfer_object` 命中 **49/52**，其中 **48 条 `dto.source=5`（业务事件 DTO）+ 1 条 `dto.source=1`**，`dto.source_type = 0` 全表恒定。
> 订正留痕：早期版本写「这 49 条的 dto.source = 5」，漏了那 1 条 `source=1`（auditor R3 指出）。实测分布 `{5:48, 1:1}`——`source=5` 是业务事件 DTO 的**主流**形态而非唯一形态，那 1 条例外未进一步追因（不影响 `event_data→DTO` 的指向结论）。
`event_data` 去重 **50 个不同值**，`udc_data_transfer_object` 全表 1425 行，`source` 分布 `{1:1316, 4:61, 5:48}`——**`source=5` 是业务事件专用 DTO**。

**3 个 MISS 的实证（避免把巧合当规律）**
本应用 `xzhEntityEvent` 的 `event_data = 474806313816300867`，解出来是 `udc_entity/xzhExp950795` 的 **id**，而该 id 在 `udc_data_transfer_object` 中**不存在**（`SELECT id FROM udc_data_transfer_object WHERE id=474806313816300867` → 空），该实体名下也**没有任何 DTO 行**（`WHERE source_id=474806313816300867` → 空）。
即本应用这 3 条事件的 `event_data` 全部**悬空**（`xzhBusListener` / `xzhMfEventListener` / `xzhEntityEvent` 同指 `474806313816300867`）。
> **不要因 `xzhEntityEvent` 的 `source_id == event_data` 就推断"二者同源"。** 这是手工造数据时把 entity id 填进 `event_data` 造成的巧合；正规路径（§2.4 代码）里 `event_data` 是**新建 DTO 的 id**，与 `source_id` 无等式关系。
> 影响面：这 3 条事件若走 `selectWithEventData`，`root` 反查为 `null`，事件数据树取不到。属**本实例数据缺陷**，非平台机制。

### 2.5 `enabled` / `publish_state` / `number_fired_once`

- `enabled`：`tinyint NOT NULL`，0/1。全库 52 行：**47 启用 / 5 停用**
- `number_fired_once`：**字符串**，正则 `ALL|(^[0-9]{1,9}$)`（STATIC `EventDto` `@Pattern` 原文），默认 `"1"`；语义="一次触发数量"，`ALL` 表示全部
- `publish_state`：52 行全为 `1`

### 2.6 `exp_design_data` / `exp_runtime_data` / `message_topic` / `message_tags`

**LIVE 全库量化：全部为 NULL/空**
```
有 exp_design_data 的行数: 0
有 message_topic   的行数: 0
```
→ 触发条件表达式与 MQ 主题在 `udc_event` 上**当前实例从未被使用**。这两个字段属于"表结构预留但业务未启用"形态，标 **UNVERIFIED（无样本可证使用语义）**。

---

## 3. 平台通用形态分层

| 层 | 内容 | 证据等级 |
|---|---|---|
| **平台级（跨应用恒定）** | 6 枚举取值与 code；`uk_udc_event_aid_sid_name_tid`；`className=capitalize(name)+"Event"`；`eventData` 服务端注入；`EVENT_PACKAGE` 常量 | **STATIC 确证**（反编译源码 + 49 样本零反例） |
| **平台级（强规律）** | `messageSource`↔`topic` 互斥（**244/244，定义域=trigger 中具 messageInfo 者**；254 中另 10 个空壳不在定义域）；`eventType=AMONG_APP ⇔ selectEvent=null`（37/37） | **LIVE 全库量化** |
| **平台级（倾向）** | `source_id=0` 是 MICRO_FLOW 事件常态（48/50） | **LIVE**（单实例，跨实例 UNVERIFIED） |
| **实例特异** | 本应用 4 条事件的具体 name/caption；`dto.source=5` 的具体 DTO 集合（48 条） | **LIVE 本应用** |
| **VACUUM（无样本）** | `exp_design_data`/`message_topic`/`message_tags` 的使用语义；`EventTriggerTypeEnum.TRANSACTION_EXCEPTION`；`EventActionTypeEnum.SELECT`；`EventSourceEnum` 全 3 值以外的组合 | **UNVERIFIED** |

---

## 4. 本应用 LIVE 断言（4 条事件，覆盖 source 全 3 值）

| id | name | caption | source | action_type | event_data_type | enabled | source_id |
|---|---|---|---|---|---|---|---|
| `-444632295362079470` | `xzhEntityEvent` | 小爪实体事件 | `0 ENTITY` | `0 CREATE` | `0 OBJECT` | 1 | `474806313816300867` → `udc_entity/xzhExp950795` ✅ |
| `-3437981976735970258` | `xzhBusListener` | 小爪事件总线监听 | `1 MICRO_FLOW` | `0 CREATE` | `0 OBJECT` | 1 | `-5161505652062878096` → `udc_microflow_info/xzhRestMf` ✅ |
| `-5205652932986844860` | `xzhMfEventListener` | 小爪微流程事件监听 | `2 MICRO_FLOW_EVENT` | `0 CREATE` | `1 LIST` | 1 | `-1516089433318810738` → `udc_microflow_info/xzhEvtAhN7` ✅ |
| `2806478477352020038` | `xzhEvtObj1` | 小爪应用内事件对象 | `1 MICRO_FLOW` | `1 UPDATE` | `1 LIST` | 1 | `474806313816300867` → `udc_entity/xzhExp950795` |

**这 4 条恰好覆盖 `EventSourceEnum` 全部 3 个值**，是本实例唯一能做的三值对照样本。
注意 `xzhEntityEvent` 是**全库 52 行里唯一的 `source=0`**——即本实例所有"实体事件"里真正落表的只有这一条手工造的事件对象。

> **【D15 必写项】覆盖性精确口径（禁写"覆盖全部枚举"）**
> - `source`：**3/3 全覆盖** ✅（ENTITY/MICRO_FLOW/MICRO_FLOW_EVENT 各 1 条以上）
> - `event_data_type`：**2/2 全覆盖** ✅（OBJECT/LIST 各 2 条）
> - `actionType`：**仅 2/4** ⚠️（`UPDATE` 1 条 + `CREATE` 3 条；**`DELETE`/`SELECT` 本应用与全库 52 行均无样本**）——任何"本应用覆盖全部枚举"的表述在 actionType 维度是错的
> - 每格样本量 1~3 条：只准写"本应用覆盖上述枚举"，**不准外推为"平台事件形态分布如此"**（平台口径用全实例 52 条，且必须标 **DB 口径**；API 口径仅 49 条且 ≡ UPDATE 子集）

**链 A/B 本应用实测（5 个节点）**
```
[订阅] xzhSvcEvtBpDA(1524985498115296151)     ms=EVENT             topic=None  evt=…dto.XzhExp950795Dto
[订阅] xzhMsgBusL1(3832725036227491834)        ms=MESSAGE           topic=BPM   evt=…bpm.dto.message.event.BpmStartEvent
[订阅] xzhEvtAhN7(-1516089433318810738)        ms=MESSAGE           topic=BPM   evt=…bpm.dto.message.event.BpmStartEvent
[投递] xzhStdReal31046(-3790333238868911627)   src=ENTITY           type=IN_APP  fn=…dto.microflow.event.XzhEntityEvent
[投递] xzhFinalAllNodes(-1014184770817921434)  src=MICRO_FLOW       type=IN_APP  fn=…dto.microflow.event.XzhEvtA1
```

---

## 5. 与链 C 对账的真实结果（**不要误读**）

把 72 个投递节点的 `selectEvent.fullName` 末段与 `udc_event.name` 对账：

```
命中 1 / 总 72
未命中 71 例：source 分布 {'MICRO_FLOW': 34, None: 37}；caption=None 37
```

**正确的解读**（这一步极易被判成"数据不一致"）：
- **37 例 `null`** = `AMONG_APP` 未选目标，不是缺失（见 §1.2）
- **34 例 `MICRO_FLOW`** = 引用的是**微流程事件 DTO**（`…dto.microflow.message.<Name>`），其定义体在 `udc_data_transfer_object` + `udc_microflow_info`，**本来就不该在 `udc_event` 里**
- **1 例命中** = `XzhEntityEvent` → `xzhEntityEvent`（本应用手工造的那条）

→ **结论：1/72 的命中率不是缺陷，是设计。链 B 的 `MICRO_FLOW` 分支与链 C 是两套注册体系。**
任何"用 udc_event 反查所有投递目标"的实现都会漏掉 71/72。

---

## 6. 可复现 SELF-CHECK

```bash
# 0) 环境（凭据只引用路径，不落 secret）
#    凭据: <COLLAB_ROOT>\agent-collaboration\shared-credentials\test2-web-credential.json
#    env loader: hermes skills/seeyon/01-platform/seeyon-low-code-environment/scripts/env.py
```

```python
# SELF-CHECK 1 —— 枚举映射 490 断言零错（LIVE，只读）
# 期望输出: 字段映射校验: ok=490 bad=0
python <SEEYON_AGENT_ROOT>/tools/audit/b5_map_check.py

# SELF-CHECK 2 —— 全库事件普查（LIVE，只读）
# 期望: udc_event 52 行；source {1:50, 2:1, 0:1}；enabled {1:47, 0:5}
#       action_type {1:49, 0:3}；event_data_type {0:50, 1:2}
#       exp_design_data 非空=0；message_topic 非空=0
python <SEEYON_AGENT_ROOT>/tools/audit/b5_scan.py

# SELF-CHECK 2a —— 三链量化 + trigger 分母 + §5 对账（LIVE，只读）
# 实跑输出（EXIT=0，tools/audit/b5_scan7.py）：
#   [分母三行 D22] total=254 / with_mi=244 / without=10
#   空壳(无 messageInfo)=10；分布 {3289082814923688017:6, 2378987216360786643:2,
#                                  1656355078954763084:1, 7001530513149673721:1}
#   空壳键集合 = {(caption,description,input,name,nodeId,output,type)}  ← 单一形态
#   CUSTOM/SERVICE = {CUSTOM:1, SERVICE:9}
#   messageSource(has_mi 域) {EVENT:81, MESSAGE:130, MICRO_FLOW_EVENT:33}；互斥违反数 = 0
#   [附] 口径 A/B/C：A) /trigger=254  B) 任意深度=255  C) 差=1
#        差值路径 = /nodes[0]/value/selectParam/nodeInfo（引用碎片，非 trigger）
#   PUBLISH_BUSINESS_EVENT 72；eventType {IN_APP:35, AMONG_APP:37}
#   selectEvent.source {MICRO_FLOW:34, None:37, ENTITY:1}
#   eventType×selectEvent为空 {('IN_APP',False):35, ('AMONG_APP',True):37}
#   对账 命中 1/72；未命中 71 = MICRO_FLOW 34 + None 37
python <SEEYON_AGENT_ROOT>/tools/audit/b5_scan7.py
# 修复留痕（D19/D21 要求的两处同根缺陷，一起修）：
#   L37 原 `if o.get('type')=='BUSINESS_EVENT' and 'messageInfo' in o` → 改为只读 data_schema.trigger，
#       空壳不再被过滤，nodeInfo 引用自然排除
#   L63 原 `n.endswith((... for x in evnames))` 传 generator → TypeError/exit 1 → 改为先建 dict 再判断

# SELF-CHECK 2a-2 —— 分母独立复核（三个独立实现，均只读 /trigger 位）
# 实跑（三脚本全部 EXIT=0，输出完全一致）:
#   b5_scan7.py            → total=254 / with_mi=244 / without=10
#   b5_verify_254.py       → total=254 / with_mi=244 / without=10
#   b5_recon_independent.py→ total=254 / with_mi=244 / without=10
#   *** 一致性判据：三脚本必须输出相同的 total/with_mi/without；任一不一致即视为「可复现性失效」，
#       该交付不可采信，必须先查口径再谈数字。***
#   有 trigger 的微流程数 = 254 → 一一对应，无 occurrence/unique 之分
#   空壳键集合单一；nodeId 前缀 {CUSTOM:1, SERVICE:9}；涉及 4 个应用
#   具 messageInfo 域内 messageSource: {EVENT:81, MESSAGE:130, MICRO_FLOW_EVENT:33}
#   ⚠ 空壳不是「messageSource=None」，而是**没有 messageInfo**——该字段不存在。
#     前者暗示平台有 None 枚举值，后者只是结构缺失。故分两行写，不并列。
#   [对照，禁用] 任意深度口径 = 255（= 254 + 1 个引用碎片）
python <SEEYON_AGENT_ROOT>/tools/audit/b5_scan7.py
python <SEEYON_AGENT_ROOT>/tools/audit/b5_verify_254.py
python <SEEYON_AGENT_ROOT>/tools/audit/b5_recon_independent.py

# SELF-CHECK 2a-3 —— 一致性闸门（把上面那条判据变成可执行断言，一步判定）
# 依次跑三个实现、解析 total/with_mi/without，任一脚本非 exit=0、数字缺失、
# 三者不一致、或 total != with_mi + without → GATE FAIL（exit 1）
# 实跑输出（EXIT=0）：
#   b5_scan7.py                exit=0   total=254  with_mi=244  without=10
#   b5_verify_254.py           exit=0   total=254  with_mi=244  without=10
#   b5_recon_independent.py    exit=0   total=254  with_mi=244  without=10
#   GATE PASS (total=254 / with_mi=244 / without=10)
python <SEEYON_AGENT_ROOT>/tools/audit/b5_denom_gate.py
# 这一步的意义：不是"我相信两个脚本等价"，而是"不一致就跑不过去"。
# 后来者改任一脚本口径（例如又回到任意深度遍历 → 255），闸门立刻 FAIL，无法静默交付。

# SELF-CHECK 2b —— 实体计数（LIVE，只读）
# 期望: udc_entity 全库 1814；本应用 9；udc_application 20
#       即"实体事件"是 1814×9≈16326 个虚拟对象，而 udc_event source=0 只有 1 行
python <SEEYON_AGENT_ROOT>/tools/audit/b5_ent.py

# SELF-CHECK 3 —— className 派生规则 49/49（SAMPLE，离线）
python - <<'PY'
import json
d=r"<SEEYON_AGENT_ROOT>\docs\audit\artifacts\udc-node-evidence\udcEventListPost_all.json"
sm=json.load(open(d,encoding="utf-8"))
bad=[e["name"] for e in sm if e.get("className")!=(e["name"][:1].upper()+e["name"][1:]+"Event")]
print("className 不符数:",len(bad),"/",len(sm))   # 期望 0 / 49
PY

# SELF-CHECK 4 —— event_data 是服务端注入（STATIC，看反编译源码）
grep -n "setEventData(dtoId)" \
  <SEEYON_AGENT_ROOT>/docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/appservice/EventWithDataAppServiceImpl.java
# 期望命中 L124 附近，且在 dtoAppService.createDtoWithAttrs4EntityEvent 之后

# SELF-CHECK 5 —— 实体事件不是表数据（STATIC，看模板推导）
grep -n "defaultevent.json\|setSource(EventSourceEnum.ENTITY)" \
  <SEEYON_AGENT_ROOT>/docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/common/utils/EntityEventLoader.java
# 期望: DEFAULT_EVENT_JSON_FILE_PATH = "presetData/event/defaultevent.json"

# SELF-CHECK 6 —— 6 枚举取值（STATIC，需已反编译 udc-plugin-api）
ls <HERMES_HOME>/cache/scratch/b5-cfr/com/seeyon/udc/common/enums/
# 期望含 EventSourceEnum / EventActionTypeEnum / ObjectTypeEnum /
#        MessageTypeEnum / EventTriggerTypeEnum / EventTypeEnum 的 .java
```

**反编译复现命令**（若 `b5-cfr` 目录已被清理）
```bash
java -jar "<PATH>" \
  "<MAVEN_REPO>/com/seeyon/udc-plugin-api/5.3.517/udc-plugin-api-5.3.517.jar" \
  --outputdir "<HERMES_HOME>/cache/scratch/b5-cfr"
```

---

## 7. 未覆盖 / UNVERIFIED（如实标注）

1. **跨实例的 `source_id=0` 规律**：仅 1 个实例的 50 行样本，不能断言"所有 MICRO_FLOW 事件都 source_id=0"。**UNVERIFIED**
2. **`exp_design_data` / `message_topic` / `message_tags` 的实际语义**：本实例全 NULL，无任何样本。**VACUUM**
3. **`EventTriggerTypeEnum.TRANSACTION_EXCEPTION` / `EventActionTypeEnum.SELECT`**：**升级为设计层缺失**（不再只是"本实例没数据"）。
   实测 `udc-biz-5.3.517.jar!/presetData/event/defaultevent.json`（2086 字节，9 条模板，已解包）：
   - `actionType` 集合 = `{CREATE, UPDATE, DELETE}` —— **不含 SELECT**
   - `triggerType` 集合 = `{BEFORE, AFTER, TRANSACTION_SUCCESS}` —— **不含 TRANSACTION_EXCEPTION**
   - 9 条模板 = `{Before,After,TransactionSuccess} × {Create,Update,Delete}Event`，本应用/全库 DB 也从未出现这两个值
   → 即 SELECT 与 TRANSACTION_EXCEPTION 是**平台预留枚举值，在模板层与数据层双缺失**。仍标 **VACUUM**，但成因强度从"本实例无样本"升为"设计层未启用"。
4. **`EventTypeEnum=ENTITY_EVENT` 的落表形态**：`udc_event` 无 `type` 列，`type` 只在 DTO 层默认 `BUSINESS_EVENT`。实体事件是否可能有独立落表形态 → **UNVERIFIED**
5. **`event_data` 3 个 MISS 的成因**：已实测——本应用 3 条事件同指 `474806313816300867`，该 id 是实体 id 而非 DTO id，在 `udc_data_transfer_object` 中不存在（详见 §2.4）。**成因已闭合**；但"该缺陷是否导致运行时报错"未验证（纯读不触发运行态）。**运行态影响 = UNVERIFIED**
6. **`udcEventListPost_all.json` 49 条样本的切片性质（D15 确证口径）**：快照 ≡ DB `action_type=UPDATE` 精确子集（见 §2.1 D15 必写项），同时 `sourceType` 全为 `PART`、`type` 全为 `BUSINESS_EVENT`、`triggerType` 全为 `AFTER`——**该切片无法验证 ENTITY / MICRO_FLOW_EVENT、CREATE 形态的 API 返回形态**，只能靠本应用 4 条 DB 行 + javap 字节码补齐（已补，但未走 API 回读）。**UNVERIFIED（API 侧多形态返回样本）**
7. **链 A `EVENT` 分支的实体事件来源**：本应用 `xzhSvcEvtBpDA` 的 `eventDataFullName = …dto.XzhExp950795Dto`，与 `EntityEventLoader` 的 9 个模板名（`BeforeCreate…` 等）不同；且该名在 `udc_data_transfer_object` 中**查无此 DTO**（`WHERE name LIKE '%XzhExp950795%'` → 空）。说明"应用内实体事件"的选取范围不止 9 个模板，且该配置可能是**手填的悬空引用**。**UNVERIFIED**（不扩查，避免偏移；留给映射/子流程切片或 B-1 节点采集）
8. **`searchEventList_own.json` 输入为空数组**（2 字节 `[]`，HANDOFF 列的 5 个输入之一）：本切片未使用该输入即完成闭合，但"为何为空"**原因 UNVERIFIED**——按 D14 如实标注，不静默跳过
9. **快照过滤的机制层**：快照 ≡ UPDATE 子集的**行为**已证（集合双向差 0）；但**机制**（请求侧过滤参数 vs 后端默认查询条件）未抓请求体/Controller，**成因 UNVERIFIED**。行为与机制两层分写，禁混用（D15 必写项，与 §2.1 呼应）
10. **LIST vs OBJECT 双视角（D14）**：本应用 `xzhEvtObj1` 的 `eventDataType=LIST`（事件数据形态，`eventDataList` 含子事件），而 `PUBLISH_BUSINESS_EVENT_panel_contract.json` 里同 DTO `Htxqcqrct7yk` 呈 OBJECT（`attributes` 字典：hetonghao/kehumingcheng/type）——**两视角不是矛盾**：前者是"事件数据形态"（`ObjectTypeEnum` 字节码背书），后者是"发布入参编辑面板"的属性字典。本文档分别标注、禁合并成一条"事件对象形态"断言
11. **`nodeInfo` 引用的语义与生命周期**：`nodes[*].value.selectParam.nodeInfo` 会存 trigger 的引用快照（`{entityCaption,nodeId,type}`，全库 1 条）。已验证它是**引用而非独立节点**（同一微流程存在同 nodeId 的真实 trigger），但**引用何时写入/何时清理、为何只有 1 条**未取证。**UNVERIFIED**（不扩查）
12. **空壳节点的运行时行为**：已断言其"不会收到任何事件"是基于无 `messageSource`/`topic` 的结构推断（STATIC 形态 + LIVE 数据），**未做运行态触发验证**。**UNVERIFIED（运行态）**

---

## 8. 对下游（映射/子流程切片）的交接要点

1. **查投递目标不要只查 `udc_event`**：`selectEvent.source=MICRO_FLOW` 的 34 例在 `udc_data_transfer_object` + `udc_microflow_info`，不在 `udc_event`
2. **`selectEvent=null` 不是脏数据**：先看 `eventType==AMONG_APP`
3. **`source_id=0` 不是脏数据**：MICRO_FLOW 业务事件的常态
4. **`event_data` 由服务端注入**：造事件对象必须先有 DTO，顺序不可反
5. **实体事件是虚拟的**：`udcEventListEventsPost` 不读表，别拿它当"已注册实体事件清单"去和 `udc_event` 对账
6. **类名派生**：短名 `capitalize(name)+"Event"`，全名 `com.seeyon.udc.common.event.` + `capitalize(name)`
7. **统计 trigger 只能读 `data_schema.trigger`**：`data_schema` 内 `type=BUSINESS_EVENT` 的对象有两类——`trigger`（真节点）与 `nodes[*].value.selectParam.nodeInfo`（引用快照，键仅 `{entityCaption,nodeId,type}`）。**递归遍历全 `data_schema` 会多算 1 个**，并伪造出"occurrence≠unique"的假象。任何全库事件统计先确认取的是 `trigger`。
8. **空壳节点要单列**：254 个 trigger 中 10 个无 `messageInfo`（CUSTOM 1 + SERVICE 9，跨 4 应用）。算事件覆盖率时必须剔除，否则高估约 3.9%。

---

## 9. 本轮变更纪律

- `/service` 调用：**0 次**（预计预算 3 次，未动用）
- DB：仅 `SELECT` / `SHOW`，**0 写**
- commit：本地（禁 push）
