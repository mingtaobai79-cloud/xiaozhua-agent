# DELETE_ENTITY（删除数据）节点契约

取证：前端 addNode(删除数据) → 穷尽 3 种删除模式（指定删除、过滤条件删除、ID集合删除）→ 提交保存 → 回读 dataSchema。
证据目录：`scratch/delete_entity-evidence/`。

## 1. 默认必填

```
selectParam  请输入选择节点（当 deleteType=SELECT_PARAM 时）
structure    请输入选择实体（当 deleteType 为 CONDITION 或 IDS 时）
value        选择该记录的ID集合（当 deleteType=IDS 时）
title        请输入节点出参名称
```
- 出参名字段名是 **`title`**。

## 2. 3 种删除规则 (deleteType) 及其联动

| 删除规则 UI | deleteType 枚举 | 联动展示字段 | 说明 |
|---|---|---|---|
| **指定删除** | `"SELECT_PARAM"` | `selectParam` (选择节点) | 选择前序已查出的单条实体或列表直接删除 |
| **过滤条件删除** | `"CONDITION"` | `structure` (选择实体), `condition` (过滤条件) | 根据条件过滤删除，单次上限 999 条 |
| **ID集合删除** | `"IDS"` | `structure` (选择实体), `value` (选择该记录的ID集合) | 依赖前序 `ARRAY` + `BIGINTEGER` 参数 |

## 3. 后端数据结构（已回读证实）

### A. 指定删除 (`deleteType: "SELECT_PARAM"`)
```json
{
  "actionType": "DELETE_ENTITY",
  "caption": "删除数据(1)",
  "title": "删除成功行数_指定删除",
  "deleteType": "SELECT_PARAM",
  "selectParam": {
    "description": "查询结果",
    "dataType": "DTO",
    "type": "OBJECT",
    "dtoType": "MASTER_ENTITY",
    "outputName": "_RETRIEVE_MSwqDF",
    "nodeInfo": {
      "nodeId": "RETRIEVE_CRwMB9",
      "type": "ACTIVITY",
      "actionType": "RETRIEVE"
    }
  },
  "output": {
    "id": null,
    "name": "_DELETE_ENTITY_P6qbIu",
    "dataType": "INTEGER",
    "type": "OBJECT",
    "javaType": "java.lang.Integer",
    "desc": "删除成功行数_指定删除"
  },
  "isCompleted": true
}
```

### B. ID集合删除 (`deleteType: "IDS"`)
```json
{
  "actionType": "DELETE_ENTITY",
  "caption": "删除数据(1)",
  "title": "删除成功行数_IDS",
  "deleteType": "IDS",
  "structure": {
    "id": "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto",
    "entity": "com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795",
    "label": "小爪实验实体950795V2",
    "dataType": "DTO",
    "dtoType": "MASTER_ENTITY"
  },
  "value": {
    "type": "SelectParam",
    "selectParam": {
      "id": "",
      "javaType": "java.lang.Long",
      "dataType": "BIGINTEGER",
      "type": "ARRAY",
      "desc": "ID集合",
      "nodeInfo": {
        "nodeId": "CREATE_LIST_76bxTE",
        "actionType": "CREATE_LIST"
      }
    }
  },
  "output": {
    "id": null,
    "name": "_DELETE_ENTITY_P6qbIu",
    "dataType": "INTEGER",
    "type": "OBJECT",
    "javaType": "java.lang.Integer",
    "desc": "删除成功行数_IDS"
  },
  "isCompleted": true
}
```

## 4. 关键认知与差异对比

1. **出参类型**：`DELETE_ENTITY` 返回的是删除受影响记录数量 **`INTEGER` / `java.lang.Integer`**。
2. **多源删除**：在 `SELECT_PARAM` 模式下，既允许传入单条实体 `[单条]`，也允许传入实体列表 `[多条数据]`，统一执行物理/逻辑删除并返回成功行数。
