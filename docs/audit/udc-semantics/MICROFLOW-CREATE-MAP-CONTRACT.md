# CREATE_MAP（创建映射组）节点契约

取证：CDP 真实建节点 → 添加键值对 → 后端 dataSchema 回读 → 前端 bundle `e_={group:"base",name:"创建映射组"}` 权威定义交叉验证。
证据目录：`scratch/create_map-evidence/`。

## 1. 字段与必填

| key | 标签 | 类型 | 必填 | 默认值 |
|---|---|---|---|---|
| `entries` | 添加映射 | attrsField（动态行） | ❌ | `null` |
| `title` | 节点出参名称 | outputName | ✅ | `映射组_1` |

权威定义（bundle）：
```javascript
e_ = {group:"base", name:"创建映射组", type:"createMap", settings:[{items:()=>[
  {type:"descriptionInfo",
   value:"创建一个包含多个映射键值对的映射组，可在创建时直接增加映射键值对。（映射键只允许为文本类型，映射值支持任意数据类型）"},
  {key:"entries", label:"添加映射", type:"attrsField", required:!1,
   filterContextNode: 只允许 dataType===String, hideEmptyValue:!0},
  {key:"title", label:"节点出参名称", required:!0, type:"outputName",
   dependency:{nodeType:CREATE_MAP}, rules:[{whitespace:!0}]}
]}],
 fix:{generics:{keyType:{dataType:"String"},
                valueType:{dataType:"Object", javaType:"java.lang.Object"}}},
 output:e=>{let{title:t,generics:n}=e;
   return{dataType:"MAP", javaType:"java.util.Map", id:null, type:Object,
          desc:t, appName:null, dtoType:null, udcApp:null, generics:n}}}
```

## 2. 动态行操作

- 按钮文本是 **「添加键值对」**（不是「添加映射」，后者是 form-item 的 label）
- 点一次生成一行：`input[placeholder="请输入映射的键(key)"]` + 值输入框
- 键**只能是 String 类型**；值支持任意类型（`valueComponent`，可选常量/表达式/上下文变量）

## 3. 后端数据结构（已回读证实）

```json
{
  "nodeId": "CREATE_MAP_9aw6G8",
  "type": "ACTIVITY",
  "actionType": "CREATE_MAP",
  "caption": "创建映射组(3)",
  "input": null,
  "output": {
    "dataType": "MAP",
    "javaType": "java.util.Map",
    "id": null,
    "type": "OBJECT",
    "desc": "映射组实测",
    "appName": null,
    "dtoType": null,
    "udcApp": null,
    "generics": {
      "keyType": { "dataType": "String" },
      "valueType": { "dataType": "Object", "javaType": "java.lang.Object" }
    },
    "name": "_CREATE_MAP_XqRVE0"
  },
  "isCompleted": true,
  "entries": [
    { "key":   { "type": "Simple", "simple": "key1",   "desc": "key1" },
      "value": { "type": "Simple", "simple": "value1", "desc": "value1" } }
  ],
  "title": "映射组实测",
  "generics": {
    "keyType": { "dataType": "String" },
    "valueType": { "dataType": "Object", "javaType": "java.lang.Object" }
  }
}
```

## 4. 关键认知

1. **`type` 是 `ACTIVITY`，不是 `CREATE_MAP`**：
   回读时若用 `type == 'CREATE_MAP'` 会命中 0 条。必须用 **`actionType == 'CREATE_MAP'`**。
   这是所有 `ACTIVITY` 类节点的通用规律（CREATE_VARIABLE / CHANGE_VARIABLE /
   CREATE_LIST / CHANGE_LIST / LIST_OPERATION / RETRIEVE / CREATE_ENTITY / ... 同理）。
2. **出参是 MAP 类型**：`dataType: "MAP"`、`javaType: "java.util.Map"`，
   并携带 `generics` 泛型信息（key=String，value=Object）。
   `generics` 同时出现在 `output` 内和节点顶层。
3. **`entries` 是数组**，每项 `{key: valueComponent, value: valueComponent}`。
   两者都是 `{type:"Simple", simple:..., desc:...}` 形态。
