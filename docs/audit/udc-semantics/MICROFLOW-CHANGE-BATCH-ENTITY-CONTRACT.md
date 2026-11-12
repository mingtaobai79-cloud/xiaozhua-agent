# CHANGE_BATCH_ENTITY（批量修改/批量更新数据）节点契约

取证：前端 addNode(批量更新数据) → 选择前序聚合根实体列表 → 提交保存 → 回读 dataSchema。
证据目录：`scratch/batch_update-evidence/`。

## 1. 默认必填

```
selectParam  请输入选择更新的记录列表
title        请输入节点出参名称
```
- 出参名字段名是 **`title`**。

## 2. 候选过滤规则（前端源码证实）

```javascript
filter: "type == 'ARRAY' && dtoType == 'MASTER_ENTITY'"
methodLegalsFilter: e => (0,s.J6)({treeData: e, childrenKey: "properties"}, e => {
    return e.dataType === i.pe.Dto && "MASTER_ENTITY" === e.dtoType &&
           (h.FU.appName === e?.appName || e?.methodLegals?.UPDATE_BATCH?.available === !0)
})
```
- **候选对象**：必须是聚合根实体列表（`ARRAY` + `MASTER_ENTITY`），不能是单条对象。
- **实体能力**：所属实体必须属于当前应用，或声明了 `UPDATE_BATCH` 批量更新能力。

## 3. 后端数据结构（已回读证实）

```json
{
  "actionType": "CHANGE_BATCH_ENTITY",
  "caption": "批量更新数据(1)",
  "title": "批量更新成功行数",
  "selectParam": {
    "description": "查询列表_ASC",
    "dataType": "DTO",
    "type": "ARRAY",
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
    "name": "_CHANGE_BATCH_ENTITY_q8kCdC",
    "dataType": "INTEGER",
    "type": "OBJECT",
    "javaType": "java.lang.Integer",
    "desc": "批量更新成功行数"
  },
  "isCompleted": true
}
```

## 4. 关键认知与差异对比

1. **出参类型**：`CHANGE_BATCH_ENTITY` 输出的是批量更新成功的记录数量 **`INTEGER` / `java.lang.Integer`**。
2. **拓扑依赖**：该节点不提供独立的实体选择下拉，目标实体由输入的 `selectParam` 决定，因此必须建在已有实体列表的拓扑下游。
