# 微流程写链 REST 全链 LIVE 取证（2026-10-15）

> 主路径 **REST**（`/service/udc/microflow/*`），非 GraphQL、非 CDP。
> 应用 datamigration9000000000000000001（test2）| 证据等级 **LIVE**

## 1. 端点面（字节码权威，udc-web 5.3.517 `MicroFlowController`，类级 `udc/microflow`）

| # | 方法 | 路径 | 说明 |
|---|---|---|---|
| 1.1 | GET | `findById/{id}` | 按 id 取微流程（返回完整 DTO，含 dataSchema） |
| 1.2 | POST | `search` | 分页列表 |
| 1.3 | POST | `search-no-page` | 非分页列表 |
| 1.4 | POST | `checkSchema` | **浅校验**（见 §4） |
| 1.5 | POST | `checkSchema/update` | 校验并更新 |
| 1.6 | POST | `create` | 新建（**强制草稿态**） |
| 1.7 | POST | `update` | 更新（**强制草稿态**） |
| 2.2 | POST | `delete` | 按 id 删除 |
| 6.3 | POST | `find/node-schema` | 节点 Schema |
| 6.4 | POST | `select-by-condition-for-deploy` | 全量（仅取 dataSchema，供前端生成代码） |

> ⚠️ 与 GraphQL op（`udcMicroflowCreatePost` / `udcMicroflowUpdatePost`，数字枚举）是**两套契约**：
> REST 走**字符串枚举**（`type=CUSTOM` / `triggerType=MANUAL`），不要互套。
> 前端设计器实际调用的是 **GraphQL op**（`saveMicroflowSchema` → `udcMicroflowCreatePost`），REST 是同能力的服务端面。

## 2. 实测链路（新增微流程 id=`-5161505652062878096`，name=`xzhRestMf`）

### 2.1 create —— body 是**扁平 DTO**，不是 graphql 包裹

```
POST /service/udc/microflow/create
{"appId":"8704025620829192834","name":"xzhRestMf","caption":"小爪REST微流程",
 "type":"CUSTOM","triggerType":"MANUAL","groupType":"DEFAULT",
 "description":"REST 写链验证","nodes":[],"sourceType":"PAGE"}
→ {"code":"BOOT_0000","data":{"content":"-5161505652062878096"}}   # 返回 id 字符串
```
落库（MySQL `udc_microflow_info`）：`type=3`（CUSTOM）、`trigger_type=2`（MANUAL）、`publish_state=1`、**`data_schema=NULL`**。

**关键事实：新建微流程时 dataSchema 为 null**（骨架不在 create 里生成），必须随后 update 写入。

### 2.2 checkSchema + update —— 任意顺序安全，落库可回读

```
dto = GET /service/udc/microflow/findById/-5161505652062878096   → data.content = 完整 DTO
dto["dataSchema"] = json.dumps(完整 schema)
POST /service/udc/microflow/checkSchema  (body = DTO) → {"check":true,"errors":0,"errorMessage":null}
POST /service/udc/microflow/update       (body = DTO) → {"content":1}
GET  /service/udc/microflow/findById/... → 回读一致
```

回读实测：`nodes` 3 个（`RETRIEVE_ARRAY_aaa111` / `DATA_MAPPING_bbb222` / `DELETE_ENTITY_ccc333`），
`trigger.type=MANUAL`、`trigger.paramType=BASIC`、`trigger.basic=STRING`、`input.name=_FLOW_INPUT_xzhR1`、`output.desc=执行结果`；DB `LENGTH(data_schema)=6561`。

**节点 schema 来源 = `components/udc` 权威约束从零构造**（`tests/udc/test_author_from_constraints.py::_authored_schema`），
即：**不依赖任何在线样本或前端抓包，仅凭反编译约束即可造出平台接受并落库的微流程**。

## 3. dataSchema 契约（实测坐实）

最小完整骨架（新建后从零构造，平台接受）：

```jsonc
{
  "input":  {"id":null,"javaType":"java.lang.String","inApp":null,"appName":"<appName>",
             "dataType":"STRING","type":"OBJECT","desc":"入参名","dtoType":null,"udcApp":null,
             "hasPagination":null,"name":"_FLOW_INPUT_xxxx"},
  "output": {…同上，name:"_FLOW_OUTPUT_xxxx"},
  "endNode": {"type":"END","actionType":"END_NODE","nodeId":"MFEndNode","caption":"结束",
              "output":{…},"paramType":"BASIC","basic":"STRING"},
  "sourceType": "PAGE",
  "trigger": {"nodeId":"MFStartNode","type":"MANUAL","output":{…},"paramType":"BASIC",
              "basic":"STRING","desc":"入参名"},
  "nodes": [ …活动节点，见 microflow_constraints … ]
}
```

顶层键域（真实样本）：`input, output, endNode, sourceType, trigger, nodes`（+ 部分含 `scheduleRule`）。

## 4. ★ checkSchema 是**浅校验**（本轮负向对照实测）

对同一 DTO 注入 4 类**明确非法**内容，`checkSchema` **全部返回 `check:true, errors:0`**：

| 注入 | 结果 |
|---|---|
| `nodes[0].actionType = "NOT_A_TYPE"` | check:true（未报） |
| `conditions[0].operator.name = "BADOP"` | check:true（未报） |
| `trigger.paramType = "BOGUS"` | check:true（未报） |
| `nodes = []` | check:true（未报） |

**结论：`checkSchema` 不能当深度校验器用**——它不校验节点 actionType/操作符/paramType 值域，也不校验空流程。
真正的结构/值域约束由 **`components/udc/microflow_constraints.py` + `microflow_model.py`**（反编译权威）承担；
**生成前置校验必须在本地模型做，不能依赖 checkSchema 兜底**（"形状对、约束错"会静默通过）。

## 5. ★ 一致性检测面读的是**缓存快照**，落后于 DB（重要机制）

实测：`udcApplicationSearchDetectionPost` 报 `UDC_MICRO_FLOW_04004` 的文档名一直是
`micro flow [小爪实验微流程953182-已更新]`。而：
- 该微流程经 REST `update` 把 caption 改为 `小爪实验微流程953182-CAPTEST` → DB 确认 `update_time=2026-10-15 18:16:55`、caption 已变；
- 检测面**仍报旧 caption**；改回原名后仍报同一内容。

⇒ **检测面（构建流水线 doParallel 阶段的同一读面）消费的是元数据缓存/发布镜像，而非 `udc_microflow_info` 实时行。**
含义：
1. 改 DB/调 update 后**不能立刻**用检测面结果判成败，需等缓存刷新或走发布链路；
2. 之前"fields 修复后 03108 消失"是**部分刷新**（或该校验走实时面）→ 检测面各校验器的读源**不统一**，属 **UNVERIFIED** 具体机制，勿一概而论。

## 6. 04004「微流程入参:依赖应用已删除」的处置

- 现象：`xzhMf953182` 的 trigger 入参 `paramType=BASIC`（基础类型）却带 `output.appName=<本应用>`。
- 本轮动作：把 `input/output/trigger.output` 的 `appName/inApp/udcApp` 置 null → REST `checkSchema` + `update` 均成功、DB 回读三处已为 null。
- 检测面**未随之变化**（符合 §5 缓存结论）⇒ 该 ERROR 的**真实修复效果需在缓存刷新后复验**，本轮标 **UNVERIFIED-待复验**，不宣布已修。

## 7. 本轮产物

- `scratch/mf_rest_create.py`（create 面）、`mf_rest_update2.py`（从零 schema 构造 + checkSchema）、
  `mf_rest_write.py`（update + 回读 + 检测对账）
- 新实验对象：微流程 `xzhRestMf`（id `-5161505652062878096`，xzh 前缀，可清理）

## 8. ★★ update 时 type/triggerType 必须从 DB 原值回读，禁止硬编码（2026-10-16 事故）

**事故**：用 `mf_ops.py update`（GraphQL `udcMicroflowUpdatePost`）把标准微流程
`小爪标准微流程-全节点流转(最终)`（`-1014184770817921434`）的 `type` 从 `SERVICE(0)`
硬编码成 `CUSTOM(3)`，同一操作把 `state` 从 `10(DRAFT)` 改成 `20(RELEASE)`
→ 标准微流程被误改成自定义微流程（用户立刻发现："你又改成了自定义微流程了？"）。

**根因**：脚本 body 里写了常量 `'type':'CUSTOM'`、`'state':'RELEASE'`、`'triggerType':'MANUAL'`。

**铁律**：
1. `type` / `triggerType` / `state` / `sourceId` / `serviceInterface` / `microFlowGroupId` / `versionCode`
   **一律从 DB 原行 SELECT 回读**，绝不在 body 里写死；
2. `type` 枚举映射（GraphQL 字符串枚举）：`0→SERVICE / 1→FRONTEND / 2→ENTITY_RULE / 3→CUSTOM / 4→FUNCTION`；
   `trigger_type`：`0→BUSINESS_EVENT / 1→SCHEDULE / 2→MANUAL / 3→FRONTEND_PARAM`；
3. `state`：`10=DRAFT（草稿）`、`20=RELEASE（正式）`；DB 里 `10/20` 是**整型**；
4. 标准微流程判定：`type=0` + `service_interface='CustomMicroFlowAppService'`；
5. 若必须改类型，用显式覆盖开关（`--type=SERVICE --trg=MANUAL --state=10`），并在落库后**回读 DB 对账**。

**验证**：恢复 `type=0/state=10` 后回读一致，真机「检查」= **0阻断 / 0严重**（此前 1 阻断）。

## 9. 下一步

1. 活动节点**逐类**经 REST 写链验证（本轮到 RETRIEVE_ARRAY/DATA_MAPPING/DELETE_ENTITY 三类；余 44 类）；
2. `find/node-schema`（6.3）读面接入，用于**生成前置**的节点字段模板自证；
3. 缓存刷新窗口复验（§5/§6），把"检测面读源"从 UNVERIFIED 升到 LIVE；
4. 微流程 → 页面规则（`type=FRONTEND`，依赖 pageSchema/pageInfo/pageLayout）的差异化校验链。
