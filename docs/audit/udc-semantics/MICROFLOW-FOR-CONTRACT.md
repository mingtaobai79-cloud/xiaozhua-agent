# FOR（计数循环）节点契约

取证：CDP 真实建节点 → 空提交抓必填 → 后端 dataSchema 回读 → 前端 bundle `ea={group:"base",name:"计数循环"}` 权威定义交叉验证。
证据目录：`scratch/for-evidence/`。

## 1. 字段与必填（实测 + 权威定义一致）

| key | 标签 | 类型 | 必填 | 默认值 |
|---|---|---|---|---|
| `forStart` | 循环起始值 | valueComponent | ✅ | `{type:"Simple", simple:0, desc:0}` |
| `forEnd` | 循环终止值 | valueComponent | ✅ | `{type:"Simple", desc:0, simple:0}` |
| `forStep` | 步长 | inputNumber | ✅ | `1` |
| `operator` | 执行条件 | executionConditions | ❌ | `"<="` |
| `targetName` | 循环变量名称 | outputName | ✅ | `计数循环变量_1` |

权威定义（bundle）：
```javascript
{key:"forStart", label:"循环起始值", type:"valueComponent", required:!0,
 valueType:["CONSTANT","EXPRESSION","CONTEXT_VARIABLE"], enableDefaultValue:!1,
 dependency:{dataType:Integer, hideEmptyValue:!0}, businessProps:{max:99999999},
 defaultval:{type:"Simple", simple:0, desc:0}}
{key:"forEnd", label:"循环终止值", type:"valueComponent", required:!0,
 valueType:["CONSTANT","EXPRESSION","CONTEXT_VARIABLE"], businessProps:{max:99999999},
 defaultval:{type:"Simple", desc:0, simple:0}}
{key:"forStep", label:"步长", required:!0, defaultval:1, type:"inputNumber", props:{max:99999999}}
{key:"operator", label:"执行条件", required:!1, type:"executionConditions", defaultval:"<="}
{key:"targetName", label:"循环变量名称", required:!0, type:"outputName"}
```

## 2. 执行条件 (operator) 全集

UI 实测下拉 4 项：`['小于等于', '小于', '大于等于', '大于']`
后端枚举值：`"<="`（默认）、`"<"`、`">="`、`">"`

## 3. forStart / forEnd 三形态（valueType）

`["CONSTANT", "EXPRESSION", "CONTEXT_VARIABLE"]` —— 与 RETRIEVE 右值同构：
- `CONSTANT`：`{type:"Simple", simple:<整数>, desc:<整数>}`
- `EXPRESSION`：表达式编辑器产出，要求结果 `dataType=INTEGER`
- `CONTEXT_VARIABLE`：只能选 `Integer` 标量上下文变量

**取值范围上限**：`max: 99999999`（两个边界值相同）。

## 4. 后端数据结构（已回读证实）

```json
{
  "nodeId": "For_F9Jlvj",
  "type": "FOR",
  "caption": "计数循环(1)",
  "forStart": { "type": "Simple", "simple": 0, "desc": 0 },
  "forEnd":   { "type": "Simple", "desc": 0, "simple": 0 },
  "forStep": 1,
  "operator": "<=",
  "targetName": "计数循环变量_实测",
  "output": {
    "id": "",
    "dataType": "INTEGER",
    "type": "OBJECT",
    "desc": "计数循环变量_实测",
    "javaType": "java.lang.Integer",
    "name": "_FOR_g6XFlI"
  },
  "nodes": [],
  "isCompleted": true
}
```

## 5. 关键坑（实测踩到）

1. **零改动 = 不落库**。FOR 全部字段都有默认值（`0/0/1/<=/计数循环变量_1`），
   若一个字段都不改，`configChanged` 保持 `false`，点「确定」只关抽屉、
   不发 `udcMicroflowUpdatePost`，节点只活在 Redux store 里，后端零写入。
   **必须先真实修改任一字段（如循环变量名称）再提交**。
2. **根级节点卡片可能不渲染**。FOR 建在根级（不在 BRANCH/CONDITION 内）时，
   `flowFrame` 与后端 `dataSchema` 都有它，但画布 `.udc-microflow-editor-node-container`
   查不到对应 DOM，`open_node` 会返回 `empty drawer`。此时不能靠点击二次进入，
   需重载页面后从 `flowNodes` 直接读结构，或用 dispatch 打开。
3. **容器节点**：`FOR` 与 `FOR_EACH` 同构，都带 `nodes: []` 子链；
   `foreach: null`（计数循环不用 foreach）。

## 6. 与 FOR_EACH 的差异

| 维度 | FOR（计数循环） | FOR_EACH（列表循环） |
|---|---|---|
| 驱动源 | 整数区间 `forStart..forEnd` + `forStep` | 列表变量 `selectParam` |
| 迭代变量 | `targetName`，恒 `INTEGER/Integer` | `targetName`，类型随列表元素降维 |
| 终止条件 | `operator` 4 种比较符 | 列表耗尽 |
| 出参 | `OBJECT` + `dataType=INTEGER` | `OBJECT` + 列表元素 `dataType` |
| `foreach` | `null` | `{sourceItemes: []}` |

## 7. 平台提示（bundle 原文）

SERVICE 型：`请尽量避免在循环中使用插入数据、更新数据、自定义服务、子微流程等节点。`
非 SERVICE 型：`请尽量避免在循环中使用值操作、微流程等节点。`
