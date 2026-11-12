# 节点关联模型：谁能产出数据、谁能消费数据

> 状态：LIVE（节点目录 51 项全量扫描 + 前端 bundle 可选范围机制 + 真实微流程样本）
> 生成物：`node-catalog.json`（勿手改，改 `tools/audit/extract_microflow_nodes.py`）

## 铁律

- 51 个节点里**只有 10 个有出参**（`outputName` 必填），能作为后续节点的数据源；其余 41 个是纯动作终点
- 执行顺序 = `nodes` 数组顺序，**不是** `runAfter`（该字段全库恒 null）
- 后续节点能引用什么，由「**前序节点的 output 树**」决定，不是全量节点
- 开始节点的出参 = 规则顶层 `input`，名字必须 `_FLOW_INPUT_<6位>`
- 想被引用就必须有合法 `output`（含 `desc`，它直接变成可选范围的标签）
- 节点在哪个域能用、能调什么，另有域约束（`components/udc/rule_domain_scope.py`），跟出参是两回事

## 1. 51 个节点的出参分布（全量扫描）

| 域 | 定义数 | 有出参 |
|---|---|---|
| MICROFLOW | 5 | 2 |
| FRONTEND_RULE | 20 | 4 |
| ENTITY_RULE | 26 | 4 |
| **合计** | **51** | **10** |

### 有出参的 10 个（可被后续节点引用）

| 域 | type | 名称 | 出参说明 |
|---|---|---|---|
| MICROFLOW | `CALL_APP_SERVICE` | 自定义服务 | 调应用/依赖应用的 AppService 或 REST，出参 = 接口返回 |
| MICROFLOW | `SUB_MICROFLOW` | 子微流程 | 出参 = 子流程 output |
| FRONTEND_RULE | `OPEN_PAGE` | 打开页面 | 出参 = 页面 |
| FRONTEND_RULE | `OTHER_CONTROL` | 控件动作 | 出参 = 控件 |
| FRONTEND_RULE | `CALL_MICRO_FLOW` | 调用微流程 | 出参 = 微流程返回 |
| FRONTEND_RULE | `CALL_FRONT_FLOW` | 调用页面规则 | 出参 = 规则返回 |
| ENTITY_RULE | `CALL_SERVICE` | 调用后端服务 | 出参 = 服务返回 |
| ENTITY_RULE | `ATTACHMENT_UPLOAD` | 附件上传 | 出参 = 附件 |
| ENTITY_RULE | `SCAN_CODE` | 扫码 | 出参 = 扫码结果 |
| ENTITY_RULE | `ENTITY` | 实体操作 | 出参 = 实体记录 |

★ 剩下 41 个（`ASSIGN_VALUE` / `DEFAULT_VALUE` / `SHOW_MESSAGE` / `VISIBLE` /
  `ATTRIBUTE_REQUIRED` / `CUSTOM_ERROR` / `THROW_EVENT` / `CONVERT_DATA` / `DIALOG` …）
  **没有出参**。它们只能消费前序节点的数据，不能被后序节点引用。

## 2. 引用是怎么算出来的（前端机制，bundle 逐字）

```js
// 1) 按图结构算出「当前节点的前序节点集合」
let B = y.zH({nodeId, flowPaths, flowFrame, flowNodes, flowBasicInfo});
// 2) 把前序节点的 output + outputCache 组成可选范围树
let k = s.nQ(B, outputCache, {appParameters});
// 3) 交给表达式组件
{ExpressionComponent, config:{initialState:{customSchema: k}}}
```

⇒ **同一个表达式组件，在不同节点位置看到的可选范围完全不同**：

```
开始节点之后（无前序）      → 只有顶层 input（实体字段 / 入参）
查询节点之后               → _RETRIEVE_xxx 的输出树
分支 ifBranch 内           → 分支之前的全部节点 + 分支条件用到的节点
子流程节点之后             → 该节点 output.desc 变成分类标签
```

## 3. 出参命名与引用路径

```
节点出参    output.name = _<actionType>_<6位>      如 _RETRIEVE_x7jPXO
开始出参    input.name  = _FLOW_INPUT_<6位>        如 _FLOW_INPUT_IkLj4T
表达式 token.value = <根name>.<根name>.<字段>      两层重复是常态
```

★ 两层重复的根因：`context[0].name` 与 `context[0].properties[0].name` 同名，
  所以 token 路径写成 `_BUSINESS_EVENT_xxx._BUSINESS_EVENT_xxx.info...`。
  这不是 bug，照抄真实样本即可。

## 4. 三种「调用关系」别混

| 关系 | 载体 | 说明 |
|---|---|---|
| 画布内串联 | `nodes` 数组顺序 + `conditions[].nodes` | 同一条微流程内 |
| 跨流程调用 | `SUB_MICROFLOW.mfService` | 被调方 `type` 必须 0(SERVICE)/3(CUSTOM)，`type=1` 前端微流程不可引用 |
| 外部/服务调用 | `CALL_APP_SERVICE.selectMethod` | 候选集见 `custom-service-candidates.md` |

另有两个调用关系查询接口（用于反查谁调了我）：

```
udcMicroflowFindCallInfoUpstreamPost    上游（谁调用了本微流程）
udcMicroflowFindCallInfoDownstreamPost  下游（本微流程调了谁）
```

## 5. 对生成器的含义

- 构造 `branch` 的条件表达式前，必须确认被引用的节点**有出参且在它之前**
- 生成器给节点塞 `output` 时，`desc` 不能空 —— 它就是用户看到的标签
- 无出参节点写 `output: null`，不要造假的 output
- 域限制（哪些节点能出现在哪个域）由 `rule_domain_scope.validate_rule_scope` 管，
  出参关系由本文档管，**两者都不能省**

## 6. 未解

- `DIALOG` 有两个同名定义（`title/showInfo/outPutName` 与 `showInfo`），
  哪一份在哪个上下文生效未验证（UNVERIFIED）。
- `READ_ONLY` / `CONTROL_STATUS` 无任何必填字段，其实际语义未取证。

---

## ★★★ 2026-11-02 定案：`dataFlow.id` 存的是**列表行 id**，不是 dataFlowId

### 证据链（前端 + 运行时，双证）

**① 设计器保存时强制等值**（`udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js`）：

```js
merge:{dataFlowMappingId:"dataFlow.id"}
```

→ 平台自己保存的节点里，`dataFlowMappingId` 与 `dataFlow.id` **必然相等**。
以前「dataFlow.id 放规则 id、dataFlowMappingId 放行 id」的分离写法，
平台根本不可能产生，是我们自己发明的。

**② 运行时只读 `dataFlowMappingId`**（`CallDataFlowActivity.java:46-66`）：

```java
callDataFlowActivity.setDataFlowMappingId(NodeUtils.getString("dataFlowMappingId", node, true, ...));
Structure structure = MicroFlowComponentUtils.buildStructure(node, result, location, true);
structure.setEntityId(NodeUtils.getString("entityId", structureNode, true, ...));
DataSourceTypeEnum dataSourceType = NodeUtils.getEnum("dataSourceType", node, false, ...);
if (SELECT_PARAM.equals(dataSourceType)) { buildSelectParam("selectParam", ..., true); }
else { buildConditionInfo(node, result, location, true); }   // ← CONDITION 模式 condition 必填
buildOutPut(node, result, location, true, true);
```

**`dataFlow` 整个对象不参与解析**——纯 UI 字段。

**③ 存在性校验用的是 mapping 主键**：

```java
if (nodeContext.isRealGlobalDetection() && !nodeContext.getDataFlowIds().contains(this.dataFlowMappingId))
    CheckUtils.error(..., MicroFlowParseErrorEnum.DATA_FLOW_NOT_EXIST, null);
```

集合来源 `MetadataUtils.getDataFlowIdSet()` 读的元数据键名是
**`data-flow-mapping-id-used-by-micro-flow`**，由 `DataFlowMappingDto.getId()` 填充
（`PageForDataFlowPartDetectionTask:87` 用 `String.valueOf(dto.getId())`）。
→ `dataFlowMappingId` = **DataFlowMapping 主键** = `udcDataFlowListManuallyMappingPost` 的列表行 `id`。

### 结论

| 字段 | 正确取值 | 我方旧实现 |
|---|---|---|
| `dataFlowMappingId` | 列表行 `id`（mapping 主键） | ✓ 本来就对 |
| `dataFlow.id` | **同上（必须相等）** | ✗ 误用 `dataFlowId` |
| `dataFlow.dataFlowId` | 行内 FK，保留可追溯 | 未保存 |
| `condition`（CONDITION 模式） | **必填**，空数组会被 `buildConditionInfo(required=true)` 拒 | ✗ 允许空 |

前端 modal 也印证：`dataFlow`（生单规则）required、`dataSourceType` required
（`SELECT_PARAM` 选数据 / `CONDITION` 查询数据，默认 CONDITION）、
`condition`（过滤条件）`required: !0`。

### 顺带修掉：G33 重复报 3 次

G33 曾被复制进 `run_end_gate` 与 `run_leak_gate` 的 `scan`，
同一违规重复报（实际见过「G33 拦 6 项」= 2 条 × 3 份）。已删多余两份，
`tests/test_gates_g33_data_flow.py` 用 8 条断言守住（含前端 merge 与解析器静态契约）。

### 唯一语料为什么不可信

`xzhAllNodesV16` 里的 CALL_DATA_FLOW 样本 `condition=[]`——但它是**手工搭的验收流**，
同一条流里 BREAK / CUSTOM_ERROR 的 `type` 也写错（见 `node-break.md`）。
语料只能证明「字段存在」，不能证明「字段取值正确」。
## ★★★ 2026-11-02 运行时实测：CALL_DATA_FLOW 升 RUNTIME_VERIFIED

修正后的节点形态跑通了，平台自己写下读侧证据。

### 实测

```
来源实体：小爪验收实体全量（entityId=-2537349473285092530，当前 0 行）
生单规则：id=5304545611384242198（mapping 主键）  dataFlowId=7621688506670924729
条件    ：createTime != '0'（CONDITION 模式必填）
流程    ：p5df616979（定时 5 分钟）
构建    ：ok=True state=SUCCESS 233s
执行    ：19:02 / 19:07 两次，均 success=True
```

`udc_rt_data_flow_log` 读侧：

| 字段 | 值 |
|---|---|
| `dataflow_id` | 7621688506670924729（真规则 id） |
| `dataflow_mapping_id` | **5304545611384242198（我们传的列表行 id）** |
| `is_success` | 1 |
| 条数 | 每次执行 3 条（19:02 ×3、19:07 ×3） |

**平台自己把 `dataflow_mapping_id` 记成列表行 id** —— 这是对「用 mapping id 还是 dataFlowId」
的最终裁决，和前端 `merge` 规则、运行时 `getDataFlowIds().contains(...)` 三方一致。

### 为什么这次能跑通

| 修前 | 修后 |
|---|---|
| `dataFlow.id = dataFlowId`（7621…） | `dataFlow.id = 列表行 id`（5304…），与 mappingId 相等 |
| `condition = []` | 用 `condition_group()` 造真条件（`createTime != '0'`） |

### 安全边界

该规则来源实体是**测试实体且 0 行**，所以规则执行时没有记录可处理，
不会生成任何业务单据；`migration_*` 表全程 0 行。日志里 3 条 `is_success=1` 是
「跑完但无事可做」的正常结果。

### 仍未覆盖

- `dataSourceType = SELECT_PARAM`（选数据）形态**无样本、未验**（G33 暂不放行）
- 规则真的产出单据（源实体有数据）时，目标实体的写入形态未验
- 上述两点都需要一条**有数据**的测试生单规则，得从设计器建
