# FOR_EACH（列表循环）节点契约

取证：前端 addNode(列表循环) → 选择前序实体列表 → 设置循环对象名称 → 提交保存 → 回读 dataSchema。
证据目录：`scratch/for_each-evidence/`。

## 1. 默认必填与字段定义

```
selectParam  请输入选择列表
targetName   循环对象名称（默认预填“列表循环变量_1”）
```
- 表单项标签：`["选择列表", "循环对象名称"]`。
- 必填项：仅 `selectParam`。

## 2. 候选列表过滤规则

```javascript
filter: "type == 'ARRAY'"
```
- 允许选择任何类型的列表变量（包括实体列表 `DTO`，基本类型列表 `BIGINTEGER`, `STRING` 等）。

## 3. 后端数据结构（已回读证实）

```json
{
  "nodeId": "ForEach_TpOIwr",
  "type": "FOR_EACH",
  "caption": "列表循环(1)",
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
  "targetName": "当前遍历项",
  "output": {
    "id": "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto",
    "desc": "当前遍历项",
    "type": "OBJECT",
    "dataType": "DTO",
    "javaType": "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto",
    "appName": "datamigration9000000000000000001",
    "dtoType": "MASTER_ENTITY",
    "udcApp": true,
    "name": "_FOR_EACH_liEItj"
  },
  "nodes": [],
  "isCompleted": true
}
```

## 4. 关键认知与差异对比

1. **自动降维解包**：输入列表如果是 `type: "ARRAY"`，`FOR_EACH` 输出的迭代变量 `output` 会自动降维为 **`type: "OBJECT"`**，保持相同的 `dataType` 与 `javaType`，供循环体内部子节点直接消费。
2. **容器节点属性**：与 `BRANCH` 类似，`FOR_EACH` 是结构型容器节点，拥有独立的 `nodes: []` 子节点链。
