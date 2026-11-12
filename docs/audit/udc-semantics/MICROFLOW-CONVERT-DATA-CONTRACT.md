# CONVERT_DATA（类型转换）节点契约

取证：CDP 真实建节点 → 9 种 convertType 全枚举联动 → Form 实例注入完成落库 → 后端 dataSchema 回读 → 前端 bundle `eC={group:"base",name:"类型转换",type:"CONVERT_DATA"}` 权威定义交叉验证。
证据目录：`scratch/convert_data-evidence/`。

## 1. 固定字段

| key | 标签 | 类型 | 必填 | 默认值 |
|---|---|---|---|---|
| `convertType` | 变量类型 | convertTypeSelector | ✅ | — |
| `selectParam` | 选择数据 | outputSelector（带 filter + asyncFilter） | ✅ | — |
| `regex` | 指定拆分符号 | symbolSelector | ✅ | `COMMA` |
| `title` | 节点出参名称 | outputName | ✅ | `类型转换的结果_1` |

## 2. convertType 九种及数据源过滤规则（实测全集）

| # | UI 文案 | value | selectParam filter |
|---|---|---|---|
| 1 | 多选数据拆分为长整数列表 | `multiAssociation2List` | `dataType=="Entity" && type=="Object" && multiSelect==true` 或 `dataType=="CtpEnum"` 同理 |
| 2 | 长整数列表拼接为多选数据 | `List2multiAssociation` | `javaType=="java.lang.Long" && type=="Array"` |
| 3 | 文本转长整数【ID】 | `String2Long` | `dataType=="String" && type=="Object"` |
| 4 | 文本转整数 | `String2Integer` | 同上 |
| 5 | 文本转小数 | `String2Decimal` | 同上 |
| 6 | 基础类型转文本 | `BasicData2String` | `dataType!="Dto" && !="Entity" && !="Enum" && !="String" && type=="Object"`，**或** `dataType=="Entity" && type=="Object"` |
| 7 | 获取选项值编码 | `GetEnumCode` | `dataType=="Enum" && type=="Object"` |
| 8 | 获取选项值 | `GetEnumName` | 同上 |
| 9 | 指定符号拆分文本 | `Split` | `dataType=="String" && type=="Object"` 或 `javaType=="java.lang.String" && type=="Object"` |

**只有 `Split` 额外显示「指定拆分符号」**（`ishidden: convertType.value !== "Split"`）。

拆分符号 10 种：`COMMA ,` / `PERIOD .` / `UNDERSCORE _` / `MIDLINE -` / `DIVLINE |` / `QUSMARK ?` / `AND &` / `START *` / `SLASH /` / `BACKSLASH \`

## 3. 后端数据结构（已回读证实）

```json
{
  "nodeId": "CONVERT_DATA_qYvHBI",
  "type": "ACTIVITY",
  "actionType": "CONVERT_DATA",
  "caption": "类型转换(1)",
  "input": null,
  "output": {
    "name": "_CONVERT_DATA_kQ8HsT",
    "dataType": "String",
    "type": "Object",
    "desc": "转换结果",
    "javaType": ""
  },
  "isCompleted": true,
  "convertType": {
    "value": "BasicData2String",
    "key": "BasicData2String",
    "dataType": "String",
    "type": "Object",
    "desc": "基础类型转文本"
  },
  "selectParam": {
    "description": "映射值结果",
    "dataType": "STRING",
    "javaType": "java.lang.String",
    "type": "OBJECT",
    "name": "_MAP_OPERATION_ThCnMw",
    "outputName": "_MAP_OPERATION_ThCnMw",
    "position": "parent",
    "nodeInfo": { "nodeId": "MAP_OPERATION_byvldO", "type": "ACTIVITY", "actionType": "MAP_OPERATION" },
    "key": "_MAP_OPERATION_ThCnMw_MAP_OPERATION",
    "iconKey": "LinedSearch",
    "parentLabel": "",
    "disabled": false,
    "isLeaf": true
  },
  "title": "转换结果"
}
```

## 4. 关键坑（实测踩到，这是最难的一个节点）

### 4.1 `convertType` 必须是 `{value: ...}` 结构

`selectParam` 的 filter 读的是 **`e.convertType.value`**：
```javascript
switch (e?.convertType?.value) { case "BasicData2String": ... }
```
但 UI 真实选中后 Form 里存的是 `{key, dataType, type, desc}`（**没有 `value`**）。
→ **`switch` 走不到任何分支，`n` 为 `null`，`selectParam` 候选恒为空。**

### 4.2 filter 是渲染期闭包，`setFieldsValue` 不会刷新候选

`filter` 在组件 render 时求值并作为 prop 传给 `outputSelector`。
`form.setFieldsValue({convertType})` 只改 Form store，**不触发重新渲染**，
所以下拉候选仍是旧的空数组。

### 4.3 正确路径：一次性同时写入 `convertType` + `selectParam`

绕开 filter，直接把两个字段一起 setFieldsValue：

```javascript
// 1) 从 drawer DOM 的 react fiber 找到 antd Form 实例
function findFormInstance(drawer) {
  const key = Object.keys(drawer).find(k =>
    k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$'));
  // BFS 遍历 fiber 树，命中 stateNode/ref/memoizedProps.form
  // 判定条件：typeof x.getFieldsValue === 'function'
}

// 2) 同时写入（selectParam 结构照抄其他节点的 output 引用形态）
form.setFieldsValue({
  convertType: { value:'BasicData2String', key:'BasicData2String',
                 dataType:'String', type:'Object', desc:'基础类型转文本' },
  selectParam: {
    description, dataType, javaType, type, name, outputName,
    position:'parent',
    nodeInfo:{ nodeId, type, actionType },
    key: name + '_' + actionType,
    iconKey:'LinedSearch', parentLabel:'', disabled:false, isLeaf:true
  }
});
```

`selectParam` 可从 store 里同类型输出节点直接构造：
```javascript
Object.values(flowNodes).filter(n => n.output && n.output.dataType === 'STRING')
```

### 4.4 `submit()` 三级兜底都失效时用 `click_el` + 确认

本节点有多个下拉，`ui.submit()` 的 Enter 路径会命中错误输入框。
用 `ui.click_el(d, '.compid_node-config-submit-btn')` 直接点提交按钮更稳。

### 4.5 出参 `javaType` 为空串

`output.javaType` 实测为 `""`（不是 `java.lang.String`），
`dataType` 是 **`String`**（首字母大写），与其他节点的 `STRING`（全大写）不同。
