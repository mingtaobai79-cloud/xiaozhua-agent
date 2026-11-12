# 微流程节点域：数据活动 vs 自定义服务（活体验证 2026-10-24）

## 1. 分类口径（用户拍板，实测一致）

| 域 | actionType | 用途 |
|---|---|---|
| 数据活动 | CREATE_ENTITY / CHANGE_ENTITY / DELETE_ENTITY / CREATE_BATCH_ENTITY / RETRIEVE / RETRIEVE_ARRAY | 应用内实体 CRUD。**建档写库用这里** |
| 数据加工 | CONVERT_DATA / DATA_MAPPING | 类型转换、字段映射 |
| 基础服务 | CALL_APP_SERVICE / SUB_MICROFLOW / CALL_DATA_FLOW / EVENT_DISPATCH | 自定义服务 = 对外开放的 dubbo / 基础组件接口 |

结论：拿 `XxxAppService.create` 当"建档"用是错的——面板能选中，但参数映射/出参契约对不上
（出参显示"未命名的参数 / 长整数"）。正确做法是 CREATE_ENTITY 节点。

## 2. CREATE_ENTITY 节点权威模板

`fixtures/microflow/create_entity_node.sample.json` = test2 活体节点 `CREATE_ENTITY_UuKpNp`
（小爪全节点24-V16）。构造器：`components/construction/microflow_nodes.py::create_entity_node`。

关键字段：
- `structure.entityId` / `structure.relationEntity` = 实体 id（字符串）
- `output.name = _CREATE_ENTITY_<nodeId 尾段>`，`output.id = <app>.dto.<Cap>Dto`
- `attrs[].attrType.customs.id` = udc_attribute.id（校验会查这个）
- `mappingType = "attrs"`

## 3. 踩坑（每条都有活体报错佐证）

1. **Expression 的 tokens 段数必须与 translation 解析段数一致**。
   否则 `MicroFlowComponentUtils.checkExpressionNode:1716` 里 `tokens.get(i)` 越界，
   报 `UDC_CE_MICRO_FLOW_04000 未知异常 java.util.ArrayList.rangeCheck`。
   实测：`查询单条数据(1).文本字段+当前用户姓名` 3 token 会被判越界；
   同一节点的字段值改成 **SelectParam 引用** 后 04000 立即消失。
2. **表达式 context 必带 `uniformityParams`**（详见 udc-microflow-expression-nodes skill）。
3. **布尔字段用 Simple 值**：`{"type":"Simple","simple":true}`。用 Expression 写 `true` 会报
   "计算结果为 文本 类型，无法赋值给 布尔 类型"。
4. **节点替换要保留 nodeId**：`lines` 按 nodeId 关联，换 id 会断连线；就地改 actionType 最稳。

## 4. 生成面产物

- 构造器：`components/construction/microflow_nodes.py`
- 驱动脚本：`scripts/flow_fix_v17_nodes.py`（dry-run / `--apply`）

## 5. ★ RUNTIME_VERIFIED + 实体可写性前置条件（2026-11-02）

### 运行时已验证通过

`迁移断点 (MigrationCheckpoint)` 上的实测（p5vfy592031，2026-11-02 12:06:00）：

```
CREATE_ENTITY 插入-验证  success=True
  input : {"taskId":"P5VFY592031", "sourceTable":"t_src",
           "lastOffset":123, "processedRows":456, "lastPk":"pk-592031", ...}
  output: 插入成功返回ID：4526324842265571554
```

5 个字段逐个对上、平台生成 id、output 明确「插入成功返回ID」。
**`attrs` + `Simple` 字面量完全生效**，不需要 SelectParam 或变量引用。

### 两条选实体硬约束（源码级）

平台把 CREATE_ENTITY 编译成 `xxxAppService.create(SingleRequest.from(dto))`，
并在 service 层 `preCreateBatch` 里执行默认值表达式。

**① 实体必须有 `create()`**
facade api 无 `SingleResponse<Long> create(SingleRequest)` → 构建期
「找不到符号: 方法 create(...)」。本应用 24 个实体里有 6 个没有：

```
Asongda / Asongdaasongda / MigrationBatchItem /
MigrationLog / MigrationPlanField / MigrationPlanJoin
```

**② 实体字段的默认值表达式会无条件覆盖传入值**
`executeExpression*` 第二参数 `requireNull=false` 时直接 `set`，不判空：

```java
} else {
    T expressionResultValue = expressionFunction.apply(expressionMap);
    setFunction.accept(dto, expressionResultValue);   // ← 无条件覆盖
}
```

`YsFull6956`（小爪验收实体全量）有 **20 个**字段配了 `currentYear()`，
而字段约束是 `f03int≤100` / `f05dec≤999.99` —— **2026 天然违反自身约束，
这个实体永远插不进任何数据**，传什么值都一样。

### 已有闸门

`gates.py` G34（无 create 拦）/ G35（业务字段被表达式覆盖拦，系统字段豁免）。
能力表：`core/facts/udc/microflow/entity-write-capability.json`（构建产物扫描产出）。

### 教训

做写节点运行时验证，**先扫实体的 `executeExpression` 调用**。
用配了默认值表达式且撞自身约束的实体，判据从建立那一刻就是坏的。

---

- 证据：`core/facts/udc/microflow/evidence/flow-v17-node-swap.json`
  + UI 逐节点面板采集 `scratch/audit_all.json`

## 5. 检查面口径

平台"检查"按钮（UI）与 `udcMicroflowCheckSchemaUpdatePost` 不是同一层：
前者跑 `CheckUtils.parseNodes → ActivityNode.nodeLogicCheck`，能报
`UDC_MICRO_FLOW_04004`（前序节点变更 / 依赖应用已删除 / 生单规则已被删除）。
`checkSchema` 返回 check:true 不代表 UI 检查通过，两个都要看。
