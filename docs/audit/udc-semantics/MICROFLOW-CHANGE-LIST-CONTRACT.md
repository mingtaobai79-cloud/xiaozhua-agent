# CHANGE_LIST（修改列表）节点契约

取证：前端 addNode(修改列表) → 验证 4 种操作类型（增加、全量替换、删除、清空）联动 → 提交保存 → 回读 dataSchema。
证据目录：`scratch/change_list-evidence/`。

## 1. 默认必填

```
selectParam  请输入选择列表
dataSource   请输入列表/对象（当 action != CLEAR 时）
countAttrs   删除凭据字段（当 action == REMOVE 且列表为 DTO 时）
```
- **注意**：`CHANGE_LIST` 没有 `title`（节点出参名称）字段！`output` 为 `null`，原地修改目标列表。

## 2. 操作类型 (action) 4 种枚举与联动

| 操作类型 UI | action 枚举 | 联动字段 | 说明 |
|---|---|---|---|
| **增加** | `"ADD"` | `dataSource` (列表/对象) | 向列表末尾追加单条对象或同类型列表 |
| **全量替换** | `"REPLACE"` | `dataSource` (列表/对象) | 用新列表整体替换原列表内容 |
| **删除** | `"REMOVE"` | `countAttrs` (删除凭据字段), `dataSource` | 根据匹配凭据从列表中移除匹配项 |
| **清空** | `"CLEAR"` | 无（`dataSource` 自动隐藏） | 直接清空列表所有元素 |

## 3. 后端数据结构（已回读证实）

```json
{
  "actionType": "CHANGE_LIST",
  "caption": "修改列表(1)",
  "action": "CLEAR",
  "selectParam": {
    "description": "ID集合",
    "dataType": "BIGINTEGER",
    "type": "ARRAY",
    "nodeInfo": {
      "nodeId": "CREATE_LIST_76bxTE",
      "actionType": "CREATE_LIST"
    }
  },
  "dataSource": null,
  "output": null,
  "isCompleted": true
}
```

## 4. 关键认知与差异对比

1. **零出参设计**：与创建类节点不同，`CHANGE_LIST` 的 `output` 恒为 `null`，它通过直接作用于前序 `selectParam` 变量引用生效，不会在变量树中生成多余的新别名。
2. **CLEAR 模式简化**：切换到 `CLEAR` 时，不需要任何输入数据源，只用指定要清空的列表变量。
