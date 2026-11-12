# 表达式引擎：前端调用链与组成（反编译分析）

> 分析对象：`udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js`
> 方法：定位模块定义 → 解导出表 → 逐层展开被调函数
> 未使用的信息：运行时行为推断；本文件只记可从源码确认的结构。

## 1. 引擎核心是同名冲突的模块 `91118`

画布各处的 `(0,s.xxx)` 都指向模块 `91118`（bundle @1431208，约 60KB）。
它的导出表（`n.d(t,{...})`）共 12 项：

| 导出 | 内部名 | 已知职责 |
|---|---|---|
| `nQ` | `B` | **可选范围总入口**：前序节点数组 → context 树 |
| `J6` | `X` | 按谓词过滤树 |
| `ZC` | `en` | 类型可赋值判断 |
| `f0` | `er` | 字段匹配 |
| `SN` / `xY` / `xF` / `Uu` / `qJ` / `Qj` / `9` / `DS` | `ea` / `J` / `h` / `b` / `z` / `V` / `k` / `T` | 待逐个展开 |

★ 注意 `s.Xj` / `s.OR` / `s.Gk` **不在这张表里** —— 它们来自其它模块，
  调用点混用了多个 `s.*`，不能假设同一模块。

## 2. 三层调用链

```
画布节点双击
   │
   ├─ y.zH({nodeId, flowPaths, flowFrame, flowNodes, flowBasicInfo})
   │     └─ 算出「当前节点可引用的前序节点集合」（数组）      ← 未展开
   │
   ├─ s.nQ(前序节点数组, outputCache, {appParameters})
   │     └─ B = (nodes, outputCache, opts) =>
   │            nodes.reduce((acc, node) => {
   │              let one = M(node, outputCache, opts);
   │              return Array.isArray(one) ? acc.concat(one) : acc.push(one), acc;
   │            }, []).filter(Boolean)
   │
   └─ M(node, outputCache, opts)   ← 单个节点 → 可选范围条目
```

### 2.1 `M`：节点 → 可选范围条目

按 `node.output.dataType` 分派，共四个分支：

| 条件 | 处理 |
|---|---|
| `output.dataType === "UIModel"` | 页面出参：从 UIModel 构建控件树（`a.HN` + `l.BF`） |
| `output.dataType === Map` / `METADATA` | 空处理 |
| `node.actionType === "SCAN_CODE"` | 枚举 + `codeInfo` 子项 |
| `output.coustomNodeType === "ATTACHMENT_UPLOAD"` | 附件：`properties = 枚举字段 + fileList` |
| `output.outType === "OPEN_PAGE_COUSTOM" && version !== "2.0.0"` | 打开页面：`outputParams` 转树 |
| **否则（默认分支）** | 普通节点出参 |

默认分支的完整构造（这是最常用的一条）：

```js
description: nodeId === "MFStartNode" ? "开始" : node.caption,
name:        output.name,
selectable:  false,
skip:        true,
uniformityParams: {
  paramId:     output.id,
  paramCategory: output.dataType.toUpperCase(),        // "ENTITY" / "STRING" / "DTO"…
  extensionProperties: JSON.stringify({id: output.id, javaType: output.javaType}),
},
properties: R({nodeId, item: node, outputCache}),      // 字段树
```

★ **开始节点的标签固定是「开始」**，不取节点 caption；
  且若 `properties[0].name !== output.name`，会被强制改成 `output.name`。

### 2.2 `R`：按出参类型取字段树

```js
R({nodeId, item, outputCache}) {
  const {output, selectParam} = item;
  if (!output) return [];
  const u = D(output, outputCache);          // 按 output.name 查 outputCache
  switch (output.dataType.toUpperCase()) {
    case "ENTITY":  return nodeId && u ? N(u) : [];               // 实体字段树
    case "DTO":     return b({dtoInfo, outputInfo});              // DTO 字段树
    case "ENUM":    return O(output, u || output.enums);
    case "CTPENUM": return P(output, selectParam);
    case "ARRAY":   return _(…);
    case "MAP": case "METADATA": return [];
    default:        return _(output);
  }
}
```

**`outputCache` 是出参的数据源**：`outputCache[name]` 存着该出参的字段定义。
页面出参的键形如 `"UIModel_" + sourceId`。

## 3. 与实测样本的对照

### 3.1 校验规则（`-1423060900604263009`，groupType=1）

```jsonc
input:  {"dataType":"ENTITY","type":"OBJECT","name":"dto","id":"<实体id>"}
trigger: {}
context[0] = {
  "name": "dto", "description": "开始", "selectable": false,
  "uniformityParams": {"paramId":"<实体id>","paramCategory":"ENTITY",
                       "extensionProperties":"{\"id\":\"<实体id>\",...}"},
  "properties": [{"name":"dto","description":"小爪验收实体全量","type":"OBJECT", ...}]
}
token.VARIABLE: value="dto.dto.f01text", desc="实体规则.开始.小爪验收实体全量.文本字段"
```

逐项对得上 `M` 的默认公式：`description` 取「开始」、`name` 取 `output.name`（=`dto`）、
`paramId` 取 `output.id`（=`input.id`=实体 id）、`paramCategory` 取 `output.dataType`。

### 3.2 默认值规则（`-412839993779275673`，groupType=3）

```jsonc
input:  {"dataType":"ENTITY","type":"OBJECT","name":"dto","id":"<实体id>"}   // 相同
context[0] = {"name":"_SUB_MICROFLOW_cdUroc","description":"子微流程(1)", ...}
token: FUNCTION isNull → subOps [[ VARIABLE _SUB_MICROFLOW_cdUroc._SUB_MICROFLOW_cdUroc ]]
```

其前序链是 `MFStartNode → SUB_MICROFLOW → BRANCH → (分支内) 动作节点`。
条件/动作能看到的出参只有子微流程那一个。

## 4. 待展开（下一步的入口）

| 符号 | 位置 | 作用 | 为什么重要 |
|---|---|---|---|
| `y.zH` | 模块 37302 @603561 | 算前序节点集合 | **决定「能看到哪些出参」**，是两种规则可选范围差异的根 |
| `D` | 模块 91118 内部 | 按 output 名查 outputCache | 决定字段树从哪来 |
| `N` | 模块 91118 内部 | ENTITY → 字段树 | 实体字段列表的最终形态 |
| `b` | 模块 91118 内部 | DTO → 字段树 | 引用 DTO 时的形态 |
| `s.Gk` | 其它模块 | 生成 `expressionUiModelSchema` | 表达式组件的完整配置 |
| `s.Xj` / `s.OR` | 其它模块 | 树展开 / 常量包装 | 生成 token 时的辅助 |

## 5. 已确认的工程约束

1. `input.name` 在实体规则里固定是 **`dto`**（不是自造的 `_FLOW_INPUT_xxx`）。
2. `trigger` 前端保存后恒为 `{}`，写多也没用。
3. `designData` 必须保留 `terminalType`（裁掉会报 `04007 历史版本表达式数据异常`）；
   `version` 则可以没有。
4. `token.uid` 是 UUID，不是自增编号。
5. 规则条件里 VARIABLE token **不带 `paramId`**。
6. `executableExpr` 前面的 `93gD...=` 是正常形态（合法样本同样有）。
7. `token.desc` 前缀是 **`实体规则.`**，后面跟 `<输入节点标签>.<实体标题>.<字段标题>`。

## 6. `zH`：决定「能看到哪些数据」的总开关（模块 37302 导出 `zH`）

```js
zH({nodeId, flowPaths, flowFrame, flowNodes, flowBasicInfo, useUimodel = true}) {
  if (!flowPaths[nodeId]) return [];          // ★ 节点不在任何路径上 → 可选范围为空
  const path = [...flowPaths[nodeId], nodeId]; // 当前节点从根到自己的完整路径
  const output = [];
  // 沿路径走，把【路径上以及之前的兄弟节点】的 output 收进来
  walk({nodePath: path, index: path[0] ? 0 : 1,
        nodesFrame: [{nodeId: flowBasicInfo.id, nodeType: "ROOT", children: flowFrame}],
        flowNodes, output});
  // 页面规则额外插入页面出参
  if (flowBasicInfo.type === "FRONTEND" && useUimodel)
    output.unshift({nodeId: sourceId, output: {dataType: "UIModel", ...}});
  return output;
}
```

### 收集时跳过哪些节点

```
actionType === "CHANGE_VARIABLE"    （修改变量，不产出新数据）
actionType === "CHANGE_LIST"        （修改列表）
nodeType   === "FOR_EACH" / "FOR"   （循环容器）
nodeId === "MFStartNode" 且 output.dataType === "UIModel"（页面规则的开始节点）
```

其余节点只要**有 `output`** 就会被收集，交给 `M` 转成可选范围条目。

### 由此得出「为什么两种规则可选范围不同」

`zH` 只看**图结构**（`flowPaths` + `flowFrame` + `flowNodes`），不看规则类型。
所以同一条规则里，不同位置的节点看到的出参数量不同：

- 节点在**分支内** → 路径经过 BRANCH，能收到 BRANCH 之前所有节点的 output
- 节点在**分支之前** → 只能收到更前面节点的 output
- 节点**没有 flowPaths 记录** → 可选范围直接为空

「默认值规则没有实体字段可选」若成立，只可能是三种情况之一：
① 该节点 `flowPaths` 为空；② 开始节点 `output` 缺失；
③ 前端在 `filterConditionDic` 里按 `groupType` 过滤掉了 ENTITY 类出参。
这三条都需要运行时打点确认，静态分析无法进一步区分。

## 7. 完整链路一句话总结

```
flowPaths + flowFrame + flowNodes
   └─ zH ──→ 前序节点数组（过滤掉 CHANGE_VARIABLE/CHANGE_LIST/FOR 等）
        └─ nQ ──→ 每个节点 map M
             └─ M ──→ {description, name: output.name, uniformityParams, properties: R(node)}
                  └─ R ──→ 按 output.dataType 从 outputCache 取字段树
                       └─ ENTITY→N / DTO→b / ENUM→O / CTPENUM→P / ARRAY→_ / 默认→_
```

## 8. 闭环：字段树的最后一层

### 8.1 `D`：按 output 从 outputCache 取树

```js
D(output, cache) {
  const {dataType, id, javaType, outType, name} = output;
  if (dataType === Dto)
    return (outType === "OPEN_PAGE_COUSTOM" && output.version !== "2.0.0")
      ? cache[`${dataType}_${name}`]
      : cache[`${dataType}_${javaType}`];
  return cache[`${dataType}_${id}`];
}
```

**缓存键格式**（自己造 outputCache 时按这个来）：

```
普通出参   <dataType>_<id>          例：ENTITY_-2537349473285092530
DTO 出参   DTO_<javaType>           例：DTO_com.seeyon.x.dto.YDto
页面出参   UIModel_<sourceId>
```

### 8.2 `N`：ENTITY → 字段树（递归）

```js
N(fields = []) => fields.filter(A).map(f => {
  const type = f.dataType === Entity ? Object : f.dataType;
  let node = {
    name: f.name,
    description: f.caption,
    type,
    uniformityParams: {
      paramId: f.id,
      paramCategory: type,
      extensionProperties: JSON.stringify({
        id: f.id, relationType: f.relationType || null,
        relationEntity: f.relationEntity || null, javaType: f.javaType || null
      })
    }
  };
  const children = Array.isArray(f.attributes) ? N(f.attributes) : [];   // 递归
  if (f.dataType === Entity && f.relationType === "Many2OneAssociation")
    node = {...node,
      type: f.multiSelect === true ? String : BigInteger,                // ★ 关联转 ID 类型
      linkageControlData: {controlType: "REFERENCE",
                           controlProperties: JSON.stringify({appName: f.relationApp || "udc",
                                                              fullName: f.relationEntity,
                                                              multi: f.multiSelect})}};
  if (f.dataType === CtpEnum) { /* 追加枚举 linkageControlData: ENUM */ }
  node.properties = children;
  return node;
}).sort((a, b) => a.sort - b.sort)
```

### 8.3 `A`：★ 域相关的字段过滤（「三个域同一画布、选项不同」的总开关）

```js
A = field => {
  const info = store.appDesign.microflowEditorReducer.flowBasicInfo;

  if (info?.type === "ENTITY_RULE" && info?.groupType === "DEFAULT_VALUE")
    return field.dataType !== Map &&
           !(field.dataType === Entity &&
             ["ONE2ONE", "ONE2MANY"].includes(field.relationType));

  if (info?.type === "ENTITY_RULE")
    return field.dataType !== Map;                       // 校验：最宽松

  return field.dataType !== Map &&
         field.relationType !== "ONE2MANY" &&
         field.relationType !== "ONE2ONE";               // 页面规则/微流程
}
```

| 域 | 过滤规则 |
|---|---|
| 实体规则 · 校验（groupType=VALIDATE） | 只排除 `Map` —— **最宽松，实体字段全在** |
| 实体规则 · 默认值（groupType=DEFAULT_VALUE） | 排除 `Map` + 关联类型为 `ONE2ONE`/`ONE2MANY` 的实体字段 |
| 页面规则 / 微流程 | 排除 `Map` + `ONE2ONE`/`ONE2MANY` 关联字段 |

★ 这就是「为什么校验规则能选实体字段、默认值规则感觉少了一块」的代码位置。
  注意默认值规则**不是完全排除实体字段**，只是额外挡掉一对一/一对多关联；
  若实际体验「完全看不到」，需检查 `flowBasicInfo.groupType` 是否真的传成
  `"DEFAULT_VALUE"`（字符串），传错会走 else 分支。

### 8.4 `b`：DTO → 字段树

```js
b({dtoInfo, outputInfo}) => {
  const {fullName, dataType, javaType, caption, attributes} = dtoInfo;
  const {name, type, desc} = outputInfo;
  const p = name || fullName.replace(/\./g, "");
  let m = {
    name: p,
    description: desc ? `${desc} [${caption}]` : caption,
    type: type || Object,
    uniformityParams: {paramId: fullName, paramCategory: Object,
                       extensionProperties: JSON.stringify({id: fullName, javaType})}
  };
  const y = attributes ? C(attributes) : undefined;
  return [type === Array ? {...m, items: {type: dataType, properties: y}}
                         : {...m, properties: y}];
}
```

`C` 过滤 rules：排除 `Map`；`Array` 类型必须带 `enumItemObjects`。

### 8.5 `_`：其余类型（STRING/INTEGER/…）→ 单节点

```js
_(output) => [{
  name: output.name,
  type: output.dataType,
  description: output.desc || output.name,
  uniformityParams: {paramId: output.id, paramCategory: output.dataType,
                     extensionProperties: JSON.stringify({id, javaType})}
}]
```

## 9. 完整引擎模型（可直接用于生成）

```
可用数据集合 = zH(flowPaths, flowFrame, flowNodes, flowBasicInfo)
                 ↓ 每个前序节点
              M(node) = {
                description: nodeId === "MFStartNode" ? "开始" : node.caption,
                name:        node.output.name,
                selectable:  false, skip: true,
                uniformityParams: {
                  paramId: output.id,
                  paramCategory: output.dataType.toUpperCase(),
                  extensionProperties: JSON.stringify({id: output.id, javaType: output.javaType})
                },
                properties: R(node)
              }
                 ↓
              R(node) 按 output.dataType 分派：
                 ENTITY  → N(cache[`ENTITY_${output.id}`])      ← 内含 A 的域过滤
                 DTO     → b({dtoInfo, outputInfo})
                 ENUM    → O(...)
                 CTPENUM → P(...)
                 ARRAY   → _(...)
                 default → _(output)
```

**要生成一个表达式的 context，只需三样输入**：
1. 当前节点在图中的位置（`flowPaths`）
2. 各节点的 `output` 声明
3. 该规则域的 `flowBasicInfo.type` + `groupType`（决定 `A` 的过滤分支）

## 10. ★ 主要分层：三域的可选范围差异（源码级定论）

`A`（字段过滤）只是**字段级**的一层。**域级**的差异由三处调用点的
`shift` / `unshift` 决定，这才是「实体规则默认值看不到实体字段」的真正原因。

### 10.1 三处等价的剔除逻辑

```js
// ① selector：filterPreOutputList（bundle @1099023）
if (flowBasicInfo?.groupType === "DEFAULT_VALUE" && list[0]?.nodeId === "MFStartNode")
  list.shift();

// ② 组件 useMemo（bundle @1286183）
if (info?.type === "ENTITY_RULE" && info?.groupType === "DEFAULT_VALUE"
    && list.length > 0 && list[0]?.output?.dataType === "ENTITY")
  list.shift();

// ③ 条件编辑弹窗（bundle @1401184）
let a = nQ(zH({...}), outputCache, {appParameters});
if (info?.groupType === "DEFAULT_VALUE"
    && a[0]?.uniformityParams?.paramCategory === "ENTITY")
  a.shift();
```

★ **`DEFAULT_VALUE` 规则把「开始节点」（= 实体本体）整个从可选范围里移除**，
  所以看不到任何实体字段。这不是 `A` 做的，`A` 只管字段级排除。

### 10.2 页面规则额外注入页面变量

```js
if (info?.type === "FUNCTION") {                 // 页面规则
  const ui = tP.I(appParameters);                // 取页面 UI 模型
  const t  = tO.BF({uimodel: [ui]}) || [];
  a.unshift(...t);                               // ★ 插到可选范围最前面
}
```

所以页面规则的可选范围 = **页面控件变量（最前） + 前序节点出参**。

### 10.3 分类名（决定了 token.desc 的前缀）

```js
const catOf = type => {
  switch (type) {
    case "ENTITY_RULE":                return ["实体规则", "EntityRule"];
    case "FRONTEND": case "FUNCTION":  return ["页面规则", "FrontEnd"];
    default:                           return ["微流程", "MicroFlow"];
  }
}
```

`token.desc` 的第一段就是这里的 `categoryName`：
`实体规则.开始.小爪验收实体全量.文本字段`。

### 10.4 分层总表（源码 + 实测一致）

| 位置 | flowBasicInfo.type / groupType | 可选范围 | 实体字段 |
|---|---|---|---|
| 实体 → 字段 → 默认值/计算值 | 独立表达式域（非画布） | 实体字段树 + 系统变量 + 应用参数 + 函数 | ✅ |
| 实体规则 · 校验 | `ENTITY_RULE` / `VALIDATE` | 开始节点(实体) + 前序节点出参 | ✅ 全量（`A` 只排 Map） |
| 实体规则 · 默认值 | `ENTITY_RULE` / `DEFAULT_VALUE` | **开始节点被 shift 移除** + 前序节点出参 | ❌ 完全不可见 |
| 实体规则 · 赋值 | `ENTITY_RULE` / `ASSIGN_VALUE` | 同上（走 `td` 分支，待核） | 待核 |
| 页面规则 | `FRONTEND` / `FUNCTION` | **页面控件变量(unshift 最前)** + 前序节点出参 | 视页面控件 |
| 微流程 / 自定义(服务定义·事件监听·定时任务) | 其他 | 前序节点出参 | 仅当开始节点声明实体 |
| 字段集 | 设置域 | 系统变量 + 应用参数 + 函数 | ❌ 无字段 |

★ 三个域共用同一个画布组件、同一套表达式组件，差异全在：
  1. `A` 的字段过滤（字段级）
  2. `DEFAULT_VALUE` 的 shift（域级）
  3. `FUNCTION` 的 unshift 页面变量（域级）
  4. `catOf` 的分类名（展示 + token.desc 前缀）
