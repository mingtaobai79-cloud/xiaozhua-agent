# CHANGE_ENTITY（更新数据）节点契约

取证：前端 addNode(更新数据) → 选择前序单条实体 → 动态配置字段赋值 → 提交保存 → 回读 dataSchema。
证据目录：`scratch/update_entity-evidence/`。

## 1. 默认必填

```
selectParam  请输入选择更新的数据
title        请输入节点出参名称
```
- `attrs`（字段赋值）在初始时非必填，未赋值的字段在更新时将保持原值不被覆盖。

## 2. 候选过滤规则（前端源码证实）

```javascript
filter: e => e.dataType === 'Dto' && e.dtoType === 'MASTER_ENTITY' && e.type !== 'Array' &&
             (appName === hostAppName || e.methodLegals?.UPDATE?.available === true)
```
- **候选对象**：必须是聚合根实体单条数据（`OBJECT` + `MASTER_ENTITY`），不能是数组。
- **实体能力**：所属实体必须具备更新权限（同应用或声明了 `UPDATE` 可用）。

## 3. 后端数据结构（已回读证实）

```json
{
  "actionType": "CHANGE_ENTITY",
  "caption": "更新数据(1)",
  "title": "更新结果_成功行数",
  "selectParam": {
    "id": "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto",
    "javaType": "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto",
    "dataType": "DTO",
    "type": "OBJECT",
    "desc": "查询结果",
    "dtoType": "MASTER_ENTITY",
    "outputName": "_RETRIEVE_MSwqDF",
    "nodeInfo": {
      "nodeId": "RETRIEVE_CRwMB9",
      "type": "ACTIVITY",
      "actionType": "RETRIEVE",
      "entityCaption": "小爪实验实体950795V2"
    }
  },
  "attrs": [
    {
      "value": {
        "type": "Simple",
        "simple": "小爪测试更新已修改文本",
        "desc": "小爪测试更新已修改文本"
      },
      "attrType": {
        "name": "expText",
        "id": "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto.expText",
        "fullName": "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto.expText",
        "javaType": "java.lang.String",
        "dataType": "STRING",
        "type": "OBJECT",
        "desc": "实验文本(已改)"
      }
    }
  ],
  "output": {
    "id": null,
    "name": "_CHANGE_ENTITY_yzZ42F",
    "dataType": "INTEGER",
    "type": "OBJECT",
    "javaType": "java.lang.Integer",
    "desc": "更新结果_成功行数"
  },
  "isCompleted": true
}
```

## 4. 关键认知与差异对比

1. **出参类型**：`CHANGE_ENTITY` 返回的是受影响记录数量 **`INTEGER` / `java.lang.Integer`**，并不是更新后的实体对象！
2. **局部更新**：未在 `attrs` 中配置的字段在数据库更新时不会被修改或置空。
