# CUSTOM_ERROR（自定义错误）节点契约

取证：CDP 真实建节点 → 两种错误提示方式（GLOBAL / POSITION）全字段实测 → 后端 dataSchema 回读 → 前端 bundle `ep={group:"base",name:"自定义错误"}` 权威定义交叉验证。
证据目录：`scratch/custom_error-evidence/`。

## 0. 类型名陷阱

- **节点面板显示**：「自定义错误」
- **前端 nodeTypeList 的 actionType**：`FRONT_CUSTOM_ERROR`
- **后端 dataSchema 的实际 type**：**`CUSTOM_ERROR`**（无 `FRONT_` 前缀）

按 `FRONT_CUSTOM_ERROR` 去回读会永远命中 0 条。这是最容易踩的坑。

## 1. 字段与联动

| key | 标签 | 类型 | 必填 | 显示条件 |
|---|---|---|---|---|
| `errorType` | 错误提示方式 | radio | ❌ | 恒显示，默认 `GLOBAL` |
| `sourceData` | 原始数据 | outputSelector | ✅ | `errorType == "POSITION"` |
| `selectParam` | 错误数据 | sourceDataSelector | ✅ | `errorType == "POSITION"` |
| `attrType` | 定位字段 | attrsFieldSelector（多选） | ✅ | `errorType == "POSITION"` |
| `error` | 填写错误 | valueComponent | ✅ | `errorType == "GLOBAL"` |
| `attrError` | 填写错误 | valueComponent | ✅ | `errorType == "POSITION"` |

注意：**`error` 和 `attrError` 标签都叫「填写错误」**，但 key 不同，
按 label 定位时一定要结合当前 `errorType` 判断。

权威定义（bundle）：
```javascript
ep = {group:"base", name:"自定义错误", type:"customError", settings:[{items:e=>[
  {type:"descriptionInfo", value:"微流程执行到本节点后，将终止当前微流程的执行。..."},
  {key:"errorType", label:"错误提示方式", type:"radio",
   options:[{label:"全局提示",value:"GLOBAL"},{label:"定位到页面元素",value:"POSITION"}],
   defaultval:"GLOBAL",
   setEmptyBeforeChanged:["sourceData","selectParam","attrType","error","attrError"]},
  {key:"sourceData", label:"原始数据", required:!0, type:"outputSelector",
   newFilter: 只允许 dtoType==="MASTER_ENTITY" && udcApp,
   ishidden: errorType!=="POSITION", setEmptyBeforeChanged:["selectParam","attrType"]},
  {key:"selectParam", label:"错误数据", required:!0, type:"sourceDataSelector",
   newFilter: 只允许 dtoType∈["MASTER_ENTITY","SUB_ENTITY"] && udcApp,
   ishidden: errorType!=="POSITION", setEmptyBeforeChanged:["attrType"]},
  {key:"attrType", label:"定位字段", required:!0, type:"attrsFieldSelector", isMultiple:!0,
   dataTypes:[Integer,BigInteger,Float,Double,Long,Decimal,Currency,String,Entity],
   ishidden: errorType!=="POSITION"},
  {key:"error", label:"填写错误", required:!0, type:"valueComponent",
   dependency:{dataType:String, hideEmptyValue:!0}, ishidden: errorType!=="GLOBAL"},
  {key:"attrError", label:"填写错误", required:!0, type:"valueComponent",
   dependency:{dataType:String, hideEmptyValue:!0}, ishidden: errorType!=="POSITION"}
]}]}
```

## 2. 两种模式后端结构（均已回读证实）

### A. GLOBAL（全局提示）
```json
{
  "nodeId": "CUSTOM_ERROR_PaMs96",
  "type": "CUSTOM_ERROR",
  "caption": "自定义错误(1)",
  "input": null,
  "output": null,
  "isCompleted": true,
  "errorType": "GLOBAL",
  "error": { "type": "Simple", "simple": "自定义错误提示实测", "desc": "自定义错误提示实测" }
}
```

### B. POSITION（定位到页面元素）
```json
{
  "nodeId": "CUSTOM_ERROR_PaMs96",
  "type": "CUSTOM_ERROR",
  "caption": "自定义错误(1)",
  "input": null,
  "output": null,
  "isCompleted": true,
  "errorType": "POSITION",
  "error": null,
  "sourceData": { "description": "查询结果", "dataType": "DTO", "dtoType": "MASTER_ENTITY",
                  "outputName": "_RETRIEVE_MSwqDF", "nodeInfo": {...} },
  "selectParam": { "description": "查询结果", "dataType": "DTO", "dtoType": "MASTER_ENTITY", ... },
  "attrType": [{
    "id": "...XzhExp950795Dto.expText",
    "fullName": "...XzhExp950795Dto.expText",
    "name": "expText",
    "javaType": "java.lang.String",
    "dataType": "STRING",
    "type": "OBJECT",
    "desc": "实验文本(已改)",
    "relationApp": "datamigration9000000000000000001",
    "refApp": "datamigration9000000000000000001",
    "multiSelect": false,
    "dtoType": "CUSTOM",
    "label": "实验文本(已改) [文本]"
  }],
  "attrError": { "type": "Simple", "simple": "定位到字段的错误", "desc": "定位到字段的错误" }
}
```

## 3. 零出参

`output: null`、`input: null`、`name: null` —— 自定义错误只终止流程，
不产出任何数据给下游。

## 4. 关键坑（实测踩到）

1. **type 名不一致**：面板 `FRONT_CUSTOM_ERROR`，后端 `CUSTOM_ERROR`。回读用错名字命中 0。
2. **`errorType` 切换会清空所有相关字段**：
   `setEmptyBeforeChanged:["sourceData","selectParam","attrType","error","attrError"]`
   → 从 GLOBAL 切到 POSITION 再切回 GLOBAL，`error` 已被清空，必须重新填。
   → 从 POSITION 切回 GLOBAL 时，`sourceData` 等虽隐藏但**可能仍残留必填校验**，
   实测报 `值不能为空`，必须先确认字段已收拢再填。
3. **`填写错误` 是 valueComponent，不是普通 input**：
   DOM 结构是「`input.ant-input` + `lined-plus` 按钮」组合。
   - `ui.set_input()` 用原生 setter 写入**不会**让 React 受控组件更新（提交报 `值不能为空`）
   - 正确做法：`input.focus()` + CDP `Input.insertText`（走真实输入路径）
   ```python
   d.eval("... fi.querySelector('input.ant-input').focus() ...")
   d.cmd("Input.insertText", text="错误文案")
   ```
4. **查看模式弹窗会叠多层**：`readonly: false` 但 DOM 里有 3 层
   `.ant-modal-wrap`（「您现在处于查看模式，所有的修改都无法被保存」）。
   必须循环点「进行编辑」直到 `.ant-modal-wrap` 数为 0，否则所有点击都被遮挡，
   `open_node` 返回 `empty drawer`、`nodeConfigObj` 为空。
   ```python
   while document.querySelectorAll('.ant-modal-wrap').length:
       [...w.querySelectorAll('button')].find(b=>b.textContent.trim()==='进行编辑').click()
   ```
