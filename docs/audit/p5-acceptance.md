# P5 总验收（节点级运行时语义验证）

> 2026-11-03 · appId `8704025620829192834`（数据迁移，test2）
> 语料：643 条 RELEASE 流程 / 5956 节点（其中 22 类活动节点 4599 个）

## 1. 等级分布

| 等级 | 类数 | 占比（按实例） | 节点 |
|---|---|---|---|
| **RUNTIME_VERIFIED** | 15 | **88.5%** | CHANGE_VARIABLE、CREATE_VARIABLE、RETRIEVE、LIST_OPERATION、CHANGE_LIST、SUB_MICROFLOW、RETRIEVE_ARRAY、CHANGE_ENTITY、CREATE_ENTITY、CHANGE_BATCH_ENTITY、DELETE_ENTITY、CREATE_BATCH_ENTITY、BREAK、CUSTOM_ERROR、CALL_DATA_FLOW |
| LIVE_EXECUTED | 1 | 0.5% | PUBLISH_BUSINESS_EVENT（无订阅者，投递未验） |
| SCHEMA_VERIFIED | 4 | 8.3% | CREATE_LIST、CONVERT_DATA、MAP_OPERATION、CREATE_MAP |
| CONSTRUCTED | 2 | 2.7% | CALL_APP_SERVICE、DATA_MAPPING |

## 2. 每类的范围限定（不能当成全形态通过）

- **SUB_MICROFLOW**：仅标量入参/标量出参；DTO 入参 112 条样本未验
- **RETRIEVE_ARRAY**：仅 CONDITION 单条件；IDS/COUNT/OTHERS、分页、排序、多条件 GROUP 未验
- **CHANGE_LIST**：四动作均验；ADD 的列表形态（52 条）、REMOVE 多字段 countAttrs、REPLACE 元素形态未验
- **LIST_OPERATION**：仅 SIZE / FIRST_ONE；其余 12 种操作未验
- **PUBLISH_BUSINESS_EVENT**：执行路径触发过，但**没有订阅者**，投递与消费未验

## 3. 剩余节点的真实对象依赖（不是构造能力缺失）

| 节点 | 卡点 | 需要什么才能推进 |
|---|---|---|
| CALL_APP_SERVICE | 需要真实方法签名；标品流水号类接口全是业务数据，不可占用 | 一个零副作用、可安全调用的应用服务方法 |
| DATA_MAPPING | mappingRows 结构复杂，本应用无真实映射对象 | 一个真实的源/目标字段映射配置 |

这两类**保持「缺真实平台对象」分类，不降级、不虚报**。

## 4. 本轮沉淀的平台机制（带证据分级）

| 机制 | 等级 | 要点 |
|---|---|---|
| SUB_MICROFLOW_SCHEMA_COMPATIBILITY_CHECK | VERIFIED + BYTECODE_VERIFIED | 子流程契约变更，单流程 publish 放行、**构建期**才拦（11 秒 FAIL） |
| DELETED_SCHEDULED_FLOW_MAY_EXECUTE_AGAIN | VERIFIED ×3 | 删流程后仍会跑 1–2 轮，必须重建才停 |
| CONDITION_RIGHT_VALUE_SILENT_FAILURE | VERIFIED | 右值槽不合规 → 条件失效、返回全表，success 仍为 true |
| TENANT_SCOPED_QUERY | VERIFIED | 查询带租户过滤，SQL 造的种子必须用应用租户 |
| NODE_ID_STABLE_BY_ALIAS | VERIFIED | 重发幂等，否则设计器报「所选 xxx 已变更」、外部引用断链 |
| FLOW_IS_SINGLE_TRANSACTION | VERIFIED | 任一节点失败整条回滚 → 取证节点必须与实验节点分流程 |

## 5. 闸门

G1–G40 全部落地并有文档（`generation-gates.md`），新增的：

- **G39** 条件右值必须带 type，CONSTANT 必须带 value
- **G40** CHANGE_LIST 四动作形态（action 枚举 / CLEAR 无 dataSource / REMOVE 要 countAttrs）

## 6. 回归

collect 2520；**2498 passed / 22 skipped**。

## 7. P5 结论

- 22 类节点中 15 类取得真实运行证据，覆盖 88.5% 的实例
- 剩余 7 类的卡点都已定位：4 类只需补运行时用例（不缺对象），2 类缺真实平台对象，1 类缺订阅者
- 平台机制事实 6 条入库，闸门 40 道
- **P5 可以收口，进入 P6 持续学习**
