# 画布与表达式：三套域的统一模型

微流程（MICROFLOW）、页面规则（FRONTEND_RULE）、实体规则（ENTITY_RULE）
**共用同一套画布组件和表达式引擎**，但节点定义按域分成三套，同名不同结构。

> `node-catalog.json` / `node-catalog.md` 由
> `python tools/audit/extract_microflow_nodes.py` 从 bundle 自动生成，勿手改。

## 1. 节点定义分布（bundle `src_redux_store_ts.*.js`）

| 域 | 节点数 | 定义所在偏移 | 说明 |
|---|---|---|---|
| 实体规则 ENTITY_RULE | 26 | @1197xxx–@1219xxx | 实体级动作：默认值/计算值/校验/更新数据 |
| 页面规则 FRONTEND_RULE | 20 | @1137xxx–@1153xxx | 页面控件动作：设置值/可见/必填/打开页面 |
| 微流程 MICROFLOW | 5 | @1062xxx–@1129xxx | 通用：调用服务/类型转换/子微流程 |

另有 **26 项基础节点总表**（同文件模块 1198，JSON）：
分支/列表循环/计数循环/自定义错误/跳出循环/创建变量/修改变量/创建映射组/
映射操作/创建列表/修改列表/列表操作/查询单条数据/查询多条数据/插入数据/
批量插入数据/更新数据/批量更新数据/删除数据/自定义服务/事件投递/连接器/
子微流程/执行生单规则/类型转换/数据转换

★ **「设置值」不在总表里** —— 它是按规则类型动态附加的（`tag=ATTRIBUTE` 参数操作）。
  所以从数据库样本里搜 `SET_VALUE` 在实体规则中永远搜不到。

## 2. 必填校验：两套判据

前端「保存并提交」前的校验函数（bundle 内 `W`）：

```js
let d = cfg.filter(e => e?.required).map(e => e?.key);   // 只认 setting 项【顶层】required
console.log(nodeId, "的所有必填属性=>", d);
d.forEach(k => { if (node[k] == null) errors.push(node) });
```

| 概念 | 是否阻断保存 | 例子 |
|---|---|---|
| 顶层 `required:!0` | ✅ 阻断 | `ASSIGN_VALUE.value`、`SUB_MICROFLOW.mfService` |
| `rules:[{required:!0}]` 里 | ❌ 不阻断，但页面槽位为空 | `ASSIGN_VALUE.param`、`ATTRIBUTE_UNIQUE.params` |

`cfg` 的取法：`configMap[node.actionType || node.type]` —— **actionType 优先，回退 type**。

实体规则里带顶层必填的节点（12 个）：
调用后端服务 outputName / 类型转换 convertType,selectParam,regex,title /
附件上传 outputName / 扫码 outputName / 抛出页面事件 event /
自定义错误 error / 实体操作 outputName / 唯一 value / 默认值 attrs /
**设置值 value** / 必填 value / 显示信息 level,value

## 3. 表达式：按引用来源分两种形态

同一个表达式引擎，`designData.context` 的根节点**取决于表达式挂在哪**：

| 场景 | context 根 name | token.value | token.paramId |
|---|---|---|---|
| 字段默认值/计算值 | 实体 name（如 `ysFull6956`） | `<实体>.<字段>`（一层） | **有** |
| 规则条件 | 前序节点输出名（`_FLOW_INPUT_xxx` / `_RETRIEVE_xxx` / `_BUSINESS_EVENT_xxx`） | `<根>.<根>.<字段>`（**两层**） | **无** |

规则条件实测（`-9207748144528243587`）：
```
context[0].name        = _BUSINESS_EVENT_uTREKP
context[0].description = 事件监听
context[0].properties[0].name = _BUSINESS_EVENT_uTREKP   ← 同名再嵌一层
token.value            = _BUSINESS_EVENT_uTREKP._BUSINESS_EVENT_uTREKP.info...
token.desc             = 微流程.事件监听.销售数据[...].应收填报-销售更新后.应收填报-销售状态
```

★ `designData` 只应有 7 个键：
  `context / expressionTranslation / resultTypeInfo / resultTypeFullName /
   isMultiSelect / sourceAppName / tokens`
  transform 会多返回 `terminalType` / `version`，写入前要裁掉。

## 4. 已知未解（如实记）

1. **UDC_MICRO_FLOW_04007（警告）**
   `历史版本表达式数据异常，请尝试修改`
   —— 从 DB 直写的表达式会被判为历史版本；在页面上打开「条件设置」点确定可消。
   不阻塞发布。

2. **UDC_CE_MICRO_FLOW_04000（后端异常）**
   `NumberFormatException.forInputString`
   —— transform 返回的 `runtimeData.executableExpr` 前面带一段固定 base64
   （`93gD...=`），字段计算值也有同样前缀且运行正常，但规则条件该后端环节解析失败。
   尚未找到前端调用 transform 时的确切参数差异。

3. **UDC_MICRO_FLOW_04006（已解决）**
   `前序节点发生变更请重新选择`
   —— 根因：`input` 写成 `{dataType:"ENTITY", name:"dto", id:<实体id>}`，
   条件表达式的 context 根对不上任何节点输出。
   修法：`input` 用 DTO 完整形态且 `name` 必须是 `_FLOW_INPUT_xxxxxx`，
   context 根取 `input.name`。

## 5. 画布怎么加载数据（前端机制）

表达式编辑器左栏「可选范围」不是写死的，是**按当前节点位置动态算出来的**：

```js
// 1) 按图结构算出「当前节点的前序节点集合」
let B = y.zH({nodeId, flowPaths, flowFrame, flowNodes, flowBasicInfo});
// 2) 把前序节点的 output + outputCache 组成可选范围树
let k = s.nQ(B, outputCache, {appParameters});
// 3) 交给表达式组件
{ExpressionComponent, config:{initialState:{customSchema: k}}}
```

要点：

- 每个节点带的 `output` 就是它的**出参声明**，`output.desc` 直接变成可选范围里的标签。
  例：`SUB_MICROFLOW` 的 output.desc = "迁移json数据_1"，画布上就在
  「微流程」分类下显示这一项。
- 开始节点的出参 = 规则顶层 `input`，标签用 `input.desc`（= 实体标题）。
- 所以**同一个表达式组件，在不同位置看到的可选范围完全不同**：
  实体字段默认值看到的是实体字段树；设置值/条件看到的是「前序节点出参」。
- 想让后续节点引用某个节点的结果，该节点必须有合法 `output`
  （`ASSIGN_VALUE` 这类无出参的节点 `output: null` 即可）。

## 6. 前端保存后的权威形态（2026-10-23 实测）

在页面上点「保存并提交」成功后回读，前端对 schema 做了这些收敛：

| 字段 | 我写的 | 前端保存后 |
|---|---|---|
| 顶层键 | 含 id/appId/name/caption/version… | `['endNode','output','input','sourceType','trigger','nodes']` |
| `trigger` | 完整 MFStartNode 对象 | **`{}`（清空）** |
| 条件节点 `runAfter` | null | **移除** |
| `designData` | 9 键（含 terminalType/version） | 7 键（已裁掉） |
| `runtimeData.executableExpr` | 带 base64 前缀 | **保留前缀**（说明前缀本身不是错误） |
| 动作节点 `output` | null | null（无出参节点正常） |

★ 结论：**`trigger` 不必写**；`input` 的 `name` 必须是合法前缀；`runAfter` 写了也会被去掉。
