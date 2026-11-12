# CREATE_BATCH_ENTITY（批量插入数据）节点契约

取证：前端 addNode(批量插入数据) → 调整拓扑至实体列表下游 → 选择前序实体列表 → 提交保存 → 回读 dataSchema。
证据目录：`scratch/batch_insert-evidence/`。

## 1. 默认必填

```
selectParam  请输入选择插入的记录列表
title        请输入节点出参名称
```
- 出参名字段名是 **`title`**。

## 2. 拓扑与候选过滤规则（前端源码证实）

```javascript
filter: "type == 'ARRAY' && dtoType == 'MASTER_ENTITY'"
methodLegalsFilter: e => e.dataType === 'Dto' && e.dtoType === 'MASTER_ENTITY' && (appName === hostAppName || e.methodLegals?.CREATE_BATCH?.available === true)
```
- **拓扑铁律**：必须位于提供聚合根实体列表（`ARRAY` + `MASTER_ENTITY`）的节点下游（如 `RETRIEVE_ARRAY`）。若插在开头，前序无匹配参数，下拉列表为空。
- **候选对象**：不仅要求类型是 `ARRAY`，还必须是聚合根实体 `MASTER_ENTITY`，且具备批量创建能力。

## 3. 后端数据结构（已回读证实）

```json
{
  "actionType": "CREATE_BATCH_ENTITY",
  "caption": "批量插入数据(1)",
  "title": "批量新增主键列表",
  "selectParam": {
    "id": "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto",
    "javaType": "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto",
    "dataType": "DTO",
    "type": "ARRAY",
    "desc": "查询列表_ASC",
    "dtoType": "MASTER_ENTITY",
    "outputName": "_RETRIEVE_ARRAY_c8driw",
    "nodeInfo": {
      "nodeId": "RETRIEVE_ARRAY_JbrOMi",
      "type": "ACTIVITY",
      "actionType": "RETRIEVE_ARRAY",
      "entityCaption": "小爪实验实体950795V2"
    }
  },
  "output": {
    "id": null,
    "name": "_CREATE_BATCH_ENTITY_CG2MZO",
    "dataType": "INTEGER",
    "type": "OBJECT",
    "javaType": "java.lang.Integer",
    "desc": "批量新增主键列表"
  },
  "isCompleted": true
}
```

## 4. 关键认知与差异对比

1. **出参类型**：`CREATE_BATCH_ENTITY` 输出的是插入成功的记录数量 **`INTEGER` / `java.lang.Integer`**，而不是 ID 集合！
2. **无需指定实体**：与单条插入不同，批量插入节点没有 `structure`（选择实体）表单项，其目标实体完全由所选前序列表 `selectParam` 的 DTO 类型隐式推导。
