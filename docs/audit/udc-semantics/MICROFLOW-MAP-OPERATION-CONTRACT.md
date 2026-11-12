# MAP_OPERATION（映射操作）节点契约

取证：CDP 真实建节点 → 4 种操作类型全枚举切换 → GET 完整提交 → 后端 dataSchema 回读 → 前端 bundle `eR={group:"base",name:"映射操作",type:"mapOpration"}` 权威定义交叉验证。
证据目录：`scratch/map_operation-evidence/`。

## 1. 操作类型 (operationType) 4 种及联动字段（实测）

| 操作类型 UI | operationType | 触发字段 | 出参 |
|---|---|---|---|
| **获取** | `"GET"` | 该值的映射键、映射值类型、数据类型、是否列表、节点出参名称、未获取到数据时、提示内容 | 映射值本身 |
| **赋值** | `"PUT"` | 添加映射 | 无出参 |
| **删除** | `"REMOVE"` | 要删除的键 | 无出参 |
| **获取键列表** | `"KEY_SET"` | 节点出参名称 | 键组成的列表 |

权威定义：
```javascript
eD = [{label:"获取",value:"GET"},{label:"赋值",value:"PUT"},
      {label:"删除",value:"REMOVE"},{label:"获取键列表",value:"KEY_SET"}]
```

## 2. GET 模式全字段

| key | 标签 | 类型 | 必填 | 默认值 | 显示条件 |
|---|---|---|---|---|---|
| `selectMap` | 选择映射 | outputSelector | ✅ | — | 恒显示，filter `dataType=="MAP" && type=="OBJECT"` |
| `operationType` | 操作类型 | select | ✅ | `"GET"` | 恒显示 |
| `theKey` | 该值的映射键 | valueComponent | ✅ | — | `operationType=="GET"` |
| `paramType` | 映射值类型 | radio(button) | ✅ | `"BASIC"` | `operationType=="GET"` |
| `basic` | 数据类型 | treeListSelector | ✅ | `{key:"STRING",dataType:"STRING"}` | GET + `paramType=="BASIC"` |
| `app` | 选择应用 | applicationSelector | ✅ | — | GET + paramType∈{ENTITY_OBJECT,DEFAULT_OBJECT,ENUM} |
| `structure` | 实体对象/自定义对象/选项集 | treeListSelector | ✅ | — | GET + paramType∈{ENTITY_OBJECT,DEFAULT_OBJECT,ENUM} |
| `arrayOrObject` | 是否列表 | radio | ✅ | `"OBJECT"` | `operationType=="GET"`，paramType=="MAP" 时列表禁用 |
| `title` | 节点出参名称 | outputName | ✅ | — | `operationType=="GET"` |
| `nullHandling` | 未获取到数据时 | select | ❌ | `"TERMINATION"` | `operationType=="GET"` |
| `nullPromptMessage` | 提示内容 | valueComponent | ✅ | — | 未获取到数据时=终止流程 |

映射值类型 (`paramType`) 5 种：
```javascript
[{label:"基本类型",value:"BASIC"},{label:"实体对象",value:"ENTITY_OBJECT"},
 {label:"自定义对象",value:"DEFAULT_OBJECT"},{label:"选项集",value:"ENUM"},
 {label:"映射",value:"MAP"}]
```

## 3. 后端数据结构（GET + BASIC + STRING，已回读证实）

```json
{
  "nodeId": "MAP_OPERATION_byvldO",
  "type": "ACTIVITY",
  "actionType": "MAP_OPERATION",
  "caption": "映射操作(1)",
  "input": null,
  "output": {
    "javaType": "java.lang.String",
    "dataType": "STRING",
    "type": "OBJECT",
    "desc": "映射值结果",
    "generics": {
      "keyType": { "dataType": "String" },
      "valueType": { "dataType": "Object", "javaType": "java.lang.Object" }
    },
    "name": "_MAP_OPERATION_ThCnMw"
  },
  "isCompleted": true,
  "paramType": "BASIC",
  "title": "映射值结果",
  "basic": { "key": "STRING", "dataType": "STRING" },
  "selectMap": {
    "description": "映射组实测", "dataType": "MAP", "javaType": "java.util.Map",
    "id": null, "type": "OBJECT", "desc": "映射组实测",
    "appName": null, "dtoType": null, "udcApp": null,
    "generics": { "keyType": {"dataType":"String"},
                  "valueType": {"dataType":"Object","javaType":"java.lang.Object"} },
    "name": "_CREATE_MAP_5fqvVc",
    "position": "parent", "outputName": "_CREATE_MAP_5fqvVc",
    "nodeInfo": { "nodeId": "CREATE_MAP_bGqjaj", "type": "ACTIVITY",
                  "actionType": "CREATE_MAP" },
    "key": "_CREATE_MAP_5fqvVc_CREATE_MAP_5fqvVc",
    "iconKey": "LinedCreateBar", "parentLabel": "", "disabled": false
  },
  "operationType": "GET",
  "theKey": { "type": "Simple", "simple": "key1", "desc": "key1" },
  "arrayOrObject": "OBJECT",
  "nullHandling": "TERMINATION",
  "nullPromptMessage": "\n",
  "generics": { "keyType": {"dataType":"String"},
                "valueType": {"dataType":"Object","javaType":"java.lang.Object"} },
  "dataType": "STRING",
  "structure": { "key": "STRING", "dataType": "STRING", "fullName": "java.lang.String" }
}
```

## 4. 关键认知

1. **`type` 恒为 `ACTIVITY`**，回读必须用 `actionType == 'MAP_OPERATION'`。
2. **`selectMap` 只能选 `dataType=="MAP" && type=="OBJECT"`** 的前序出参，
   即上游必须是 `CREATE_MAP` 或另一个返回 MAP 的节点。
3. **`output` 随 `paramType` 变化**：
   - `BASIC` → 输出 `basic` 指定的标量类型（如 `STRING` / `java.lang.String`）
   - `ENTITY_OBJECT` / `DEFAULT_OBJECT` → 输出对应 DTO 对象
   - `ENUM` → 输出选项集
   - `MAP` → 输出嵌套 MAP
4. **`generics` 恒存在**：即使输出是 String，也带着 `{keyType:String, valueType:Object}`，
   这是从上游 MAP 继承的泛型签名。
5. **`nullHandling` / `nullPromptMessage`**：未取到映射键时的行为，
   默认 `TERMINATION`（终止流程），需要配 `提示内容`。
