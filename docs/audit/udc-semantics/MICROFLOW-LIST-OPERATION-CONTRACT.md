# LIST_OPERATION（列表操作）节点契约

取证：前端 addNode(列表操作) → 验证 7 种操作类型枚举 → 选择计数 (SIZE) → 提交保存 → 回读 dataSchema。
证据目录：`scratch/list_operation-evidence/`。

## 1. 默认必填

```
selectParam    请输入选择列表
operationType  请输入操作类型
operationParam 请输入操作数据（仅特定操作类型时必填，计数时不显示）
title          请输入节点出参名称
```
- 出参名字段名是 **`title`**。

## 2. 7 种常用列表操作类型及底层代码

| 操作类型 UI | operationType 底层代码 | 联动字段 | 出参类型 (output) |
|---|---|---|---|
| **计数** | `{"type": "SIZE"}` | 隐藏 `operationParam` | `INTEGER` / `java.lang.Integer` |
| **求和** | `{"type": "SUM"}` | 必填 `countAttrs` / 计算字段 | 随字段数值类型或 `DECIMAL` |
| **最大值** | `{"type": "MAX"}` | 必填计算字段 | 随字段数值/日期类型 |
| **最小值** | `{"type": "MIN"}` | 必填计算字段 | 随字段数值/日期类型 |
| **字段收集** | `{"type": "COLLECT"}` | 字段选择器 | `ARRAY` (基本类型列表) |
| **过滤** | `{"type": "FILTER"}` | 过滤条件弹窗 | `ARRAY` (过滤后的新列表) |
| **排序** | `{"type": "SORT"}` | 排序规则配置 | `ARRAY` (排序后的新列表) |

## 3. 后端数据结构（已回读证实）

```json
{
  "actionType": "LIST_OPERATION",
  "caption": "列表操作(1)",
  "title": "列表操作结果",
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
  "operationType": {
    "type": "SIZE"
  },
  "output": {
    "id": "",
    "name": "_LIST_OPERATION_ue10F4",
    "dataType": "INTEGER",
    "type": "OBJECT",
    "javaType": "java.lang.Integer",
    "desc": "列表操作结果",
    "dtoType": "MASTER_ENTITY",
    "appName": "datamigration9000000000000000001"
  },
  "isCompleted": true
}
```

## 4. 关键认知与差异对比

1. **出参多态性**：与 `CHANGE_LIST`（原地修改目标列表、`output: null`）截然不同，`LIST_OPERATION` 产生独立的全新出参。当进行计数或聚合时输出标量（如 `INTEGER`），当进行过滤/排序时输出全新的 `ARRAY` 列表。
2. **底层映射契约**：界面显示的“计数”在 GraphQL 和 dataSchema 中的枚举是 **`SIZE`**。
