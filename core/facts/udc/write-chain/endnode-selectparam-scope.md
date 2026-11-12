# 微流程结束节点 SelectParam 作用域解析（04004 最后一条真因）

> 领域：UDC 微流程 `dataSchema.endNode.value.selectParam` 的**变量作用域查表**
> 状态：**LIVE PASS**（test2）+ **VERIFIED_STATIC_BYTECODE**（udc-biz 5.3.517 CFR）
> 代码：`components/udc/microflow_constraints.py`（`trigger_output_context_key` / `validate_end_node_scope`）
> 护栏：`tests/udc/test_draft_warn_masking.py`（本族 6 项）
> 关联：`draft-warn-masking-mechanism.md`（04003 掩蔽）、`holder-javatype-contract.md`（04004 同族其它根因）

## 0. 一句话

`endNode.value.selectParam` 里**只有一个字段参与查表**：`outputName`；
它必须等于 `trigger.output.javaType` 的**去点全串**（`replace(".","")`），
**不是** `output.name`（`_FLOW_OUTPUT_evt1` / `_BUSINESS_EVENT_xxxxxx`）。
填错即 RELEASE 报 `UDC_MICRO_FLOW_04004` / route `MFEndNode_&_value`（「前序节点发生变更请重新选择」）。
`name` / `path` / `key` 三键在本判据里**既不参与查表也不被校验**（可留占位值）。

## 1. 权威字节码（CFR，udc-biz / udc-common 5.3.517）

| 类 | 行 | 事实 |
|---|---|---|
| `CheckUtils.detectionTrigger` | 1461-1471 | `BusinessEventTrigger` 分支：`variableBo.setName(output.getJavaType().replace(".",""))`（:1468）→ `context.put(output.getJavaType().replace(".",""), variableBo)`（:1471） |
| `CheckUtils.checkScope` | 1266-1284 | `MicroFlowVariableBo v = context.get(selectParamOutputName)`；`v == null` **立即 return false**；否则按 `v.getNodeIds()` 与 `nodeInfo.getNodePath()` 做 contains |
| `MicroFlowComponentUtils.checkSelectParam` | 902-915 | 只把 `selectParam.getOutputName()` 交给 `checkScope`；false ⇒ `OUT_OF_SCOPE`（= `MicroFlowParseErrorEnum` code 0） |
| `CheckUtils.detectionTrigger` | 1463 | trigger 侧注册的 `nodeId` 字面量是 `"root"` |
| `NodeUtils.getNodePath` | 234-241 | `nodePath` 是 **parse 期**写进 schema 的 `"root.MFEndNode"`，**不是** RequestBody 字段 |
| `MicroFlowOutputValueBo.checkEndNodeValue` | 98-113 | 结束节点取值的三分派（SelectParam / Constant / Expression） |

**由 CFR 直接推出的两条推论**（LIVE 均证实）：
1. trigger 注册 nodeId = `"root"`，endNode 的 `nodePath` 也以 `root` 开头 ⇒ contains 判据**恒真**
   ⇒ 通过与否**只取决于 `outputName` 能否命中 context 键**。
2. 键名公式是 `javaType.replace(".","")`（去点全串），与 `output.name`（UI 侧变量名）**是两个不同的量**。

## 2. ★ LIVE 隔离实验（决定性，逐臂 REST + MySQL 双面确认 state=20/RELEASE）

微流程 `1524985498115296151`「小爪标品事件监听」（type=SERVICE，trigger=BUSINESS_EVENT），
统一 `POST /udc/microflow/checkSchema/update`（DTO 自带 `state=RELEASE`）发布，
只改 `endNode.value.selectParam` 的四个字符串字段：

| 臂 | `outputName` | `name`/`path`/`key` | 发布结果 | 检测面（该微流程） |
|---|---|---|---|---|
| **A（正）** | `xzhExp950795comseeyonudccommoneventAfterUpdateEvent` | `_FLOW_OUTPUT_evt1`（占位） | `check:true, errors:0` ⇒ `state=20` | **该微流程从检测面消失**（total 仅剩 2 条 04003 WARN） |
| **B（负控）** | `_FLOW_OUTPUT_evt1` | `_FLOW_OUTPUT_evt1` | `check:true, errors:0` ⇒ `state=20` | **ERROR=1**：`UDC_MICRO_FLOW_04004`，route `MFEndNode_&_value`，msg「结束:前序节点发生变更请重新选择(事件数据)」 |

- `trigger.output.javaType` = `xzhExp950795.com.seeyon.udc.common.event.AfterUpdateEvent`。
- **A 臂证明**：`name`/`path`/`key` 全为占位值时**仍然全绿** ⇒ 三键不参与判据。
- **B 臂证明**：唯一改动的字段就是 `outputName`，ERROR 由 0 → 1 ⇒ **一元判据成立**。
- ⇒ **本件更正**「需要四键一致」（那是 A/B 之前的猜测，A 臂把它证伪）。

`checkSchema` 在两臂都返回 `check:true, errors:0` ⇒ **浅校验不覆盖本判据**，
必须走 RELEASE + 检测面才能观测（与 `draft-warn-masking-mechanism.md` 的 04003 掩蔽结论一致）。

## 3. 复算片段

```python
def trigger_output_context_key(java_type: str) -> str:
    return (java_type or "").replace(".", "")     # CFR CheckUtils:1471
```

## 4. 与 04004 同族其它根因的分工（四条 holder 不变量见姊妹件）

| 判据 | 触发点 | 本件覆盖 |
|---|---|---|
| `messageInfo.eventDataFullName` = DTO fullName | `CheckUtils.check:1427-1431` | ✗（事件监听侧） |
| `messageInfo.eventMfCustomDtoName` = `<实体短名>.<eventClassName>` | `CheckUtils.check:1433-1435` | ✗ |
| `DATA_MAPPING` holder `name` 不可占位 / `id` = `<DTOFQN>.<attr>` | `DataMappingActivity.checkTargetFieldList` | ✗ |
| `mappingRule.javaType` = 目标 DTO FQN | `DataMappingActivity:173` | ✗ |
| **`endNode.value.selectParam.outputName` = 去点 FQN** | `checkSelectParam:912` → `checkScope:1266` | ✔ **本件** |

## 5. 边界（诚实记账）

- 公式经 CFR 取证的分支**只有 `BusinessEventTrigger`**；其它 trigger 类型（MANUAL / TIMER 等）
  的 context 键约定**未取证** ⇒ `validate_end_node_scope` 对非 BUSINESS_EVENT **不报错也不外推**。
- 本件只断言「查表通过与否」，**不**断言运行时变量在业务上取到了正确数据（那属于执行期，未测）。
