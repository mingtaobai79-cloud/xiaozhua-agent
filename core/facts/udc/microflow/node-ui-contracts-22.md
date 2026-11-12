# 微流程节点 UI 实测契约（22 类，2026-10-28）

> 证据等级：**LIVE** —— 每类节点均在 test2 真实画布「添加 → 配置 → 确定 → 保存并提交 →
> 后端 dataSchema 回读」完整走通（PUBLISH_BUSINESS_EVENT 除外，标注 UNVERIFIED）。
> 本文补的是**前端交互层事实**：字段联动、DOM 结构、值域、提交路径坑。
> 结构层必填已由 `components/udc/microflow_constraints.py` 的 `REQUIRED_FIELDS` 覆盖，不重复。
>
> 逐节点完整契约见 `docs/audit/udc-semantics/MICROFLOW-<ACTION>-CONTRACT.md`；
> 原始证据见 `scratch/<node>-evidence/`。

## 零、跨节点通用坑（22 类全部踩过，必读）

### 0.1 提交后抽屉卸载 → 必须重载页面重做

提交失败（校验不通过）后抽屉会被卸载，`drawer_info()` 返回 `items: []`。
此时**不要试图继续操作**，`location.reload()` + 等 `appReduxStore` 就绪后从头做。

```python
def wait_ready(d, timeout=70):
    t0 = time.time()
    while time.time() - t0 < timeout:
        ok = d.eval("(()=>{try{return typeof appReduxStore==='object' && "
                    "!!appReduxStore.getState().appDesign.microflowEditorReducer.flowNodes}"
                    "catch(e){return false}})()")
        if ok:
            n = d.eval("(()=>Object.keys(appReduxStore.getState().appDesign"
                       ".microflowEditorReducer.flowNodes||{}).length)()")
            if isinstance(n, int) and n > 5:
                return True
        time.sleep(2)
    return False
```

### 0.2 查看模式弹窗会叠多层

`readonly: false` 但 DOM 里有 N 层 `.ant-modal-wrap`
（文案「您现在处于查看模式，所有的修改都无法被保存」）。
**所有点击都会被遮挡**，表现为 `open_node` 返回 `empty drawer`、`nodeConfigObj` 为空。

必须循环点「进行编辑」直到 `.ant-modal-wrap` 数为 0：
```python
for _ in range(8):
    n = d.eval("(()=>document.querySelectorAll('.ant-modal-wrap').length)()")
    if not n: break
    d.eval("""(()=>{const ws=[...document.querySelectorAll('.ant-modal-wrap')]
      .filter(w=>w.getBoundingClientRect().width>0);
      if(!ws.length)return;
      const b=[...ws[ws.length-1].querySelectorAll('button')]
        .find(b=>(b.textContent||'').trim()==='进行编辑');
      if(b)b.click();})()""")
    time.sleep(2.8)
```
若弹窗清完 `readonly` 仍为 `True`，点顶部「编辑」按钮（`button` 文本 === '编辑'，y<120）。

### 0.3 全流程保存被**别的节点**阻塞时，报错只在 console/message

点「保存并提交」后**静默无请求**，真实原因往往是流程里另一个节点有悬空引用。
校验函数 `W()` 走 `console.log("firstErrorNode", e)` + `message.error(...)`，
**不抛异常、不发请求**。只监听 `Runtime.exceptionThrown` 或只看网络会完全看不到。

必须注入 console 捕获：
```javascript
window.__clog=[];
['log','warn','error'].forEach(k=>{const o=console[k];console[k]=function(){
  try{window.__clog.push({k,a:[...arguments].map(x=>{
    try{return typeof x==='object'?JSON.stringify(x).slice(0,250):String(x)}catch(e){return '?'}})});}catch(e){}
  return o.apply(this,arguments);};});
```
实测捕获到的阻塞文案：`节点"修改变量(1)"引用的参数"变量_1"已失效，请重新配置！`

### 0.4 `type` 恒为 `ACTIVITY`，回读必须用 `actionType`

除控制节点（BRANCH/CONDITION/FOR/FOR_EACH/BREAK/CUSTOM_ERROR/END）外，
所有活动节点 `type` 都是 `ACTIVITY`，真实类型在 `actionType`。
**用 `type == 'CONVERT_DATA'` 回读会永远命中 0 条。**

### 0.5 卡片的点击必须居中，否则被视口裁切

画布是横向滚动的 `.udc-microflow-editor-node.branch.flex1`（scrollWidth 约 4900）。
卡片右边缘超过 1699 时点击无效。需先滚到卡片中心 x 落在 300~1400 再点：
```python
for sl in range(3000, 5000, 150):
    d.eval("""(()=>{const el=document.querySelector(
      '.udc-microflow-editor-node.branch.flex1');if(el)el.scrollLeft=%d;})()""" % sl)
    time.sleep(0.55)
    r = d.eval("""(()=>{const c=[...document.querySelectorAll(
      '.udc-microflow-editor-node-container')].find(c=>(c.textContent||'').includes(KW));
      if(!c)return null; const q=c.getBoundingClientRect(); if(q.width<20)return null;
      return JSON.stringify({x:Math.round(q.x+q.width/2),y:Math.round(q.y+q.height/2)});})()""")
    if r:
        j = json.loads(r)
        if 300 < j['x'] < 1400:
            d.click_mouse(j['x'], j['y']); time.sleep(4); break
```

### 0.6 下拉选中：`dispatchEvent(click)` 无效，必须真实鼠标 + 键盘

自定义受控 select（`treeListSelector` / `mfServiceSelector` / `convertTypeSelector` 等）
**不接受 JS 派发的 click 事件**。正确路径：

```python
# 1) 取 select 中心坐标，真实鼠标点击
d.click_mouse(cx, cy)
time.sleep(2.5)
# 2) 键盘 ArrowDown + Enter 选中第一项
for k, code in [("ArrowDown", 40), ("Enter", 13)]:
    d.cmd("Input.dispatchKeyEvent", type="keyDown", key=k, code=k,
          windowsVirtualKeyCode=code)
    d.cmd("Input.dispatchKeyEvent", type="keyUp", key=k, code=k,
          windowsVirtualKeyCode=code)
    time.sleep(1.4)
```
若需选指定项，等选项渲染后取选项坐标用 `click_mouse` 点：
```javascript
const dd=[...document.querySelectorAll(
  '.ant-select-dropdown:not(.ant-select-dropdown-hidden)')][0];
[...dd.querySelectorAll('.ant-select-item-option, .ant-select-tree-treenode')]
  .map(o=>{const q=o.getBoundingClientRect(); const t=o.querySelector('.ant-select-tree-title')||o;
    return {t:(t.textContent||'').trim(),x:Math.round(q.x+q.width/2),
            y:Math.round(q.y+q.height/2),w:Math.round(q.width),
            dis:o.className.includes('disabled')};})
  .filter(o=>o.w>0&&!o.dis&&o.t);
```
**tree 型下拉（实体/事件）用 `.ant-select-tree-treenode`，不是 `.ant-select-item-option`**，
两个选择器都要匹配。

### 0.7 `valueComponent` 必须 focus + `Input.insertText`

`valueComponent` 是「`input.ant-input` + `lined-plus` 按钮」组合。
`ui.set_input()` 用原生 setter 写入**不会**让 React 受控组件更新
（提交报 `值不能为空`）。正确做法：
```python
d.eval("... fi.querySelector('input.ant-input').focus() ...")
d.cmd("Input.insertText", text="错误文案")
```

### 0.8 过滤器是渲染期闭包 → `setFieldsValue` 不刷新候选

带 `filter` / `asyncFilter` 的下拉（CONVERT_DATA.selectParam、DATA_MAPPING.selectParam）
在组件 render 时求值并作为 prop 传下去。
`form.setFieldsValue({convertType})` 只改 Form store，**不触发重新渲染**，
下拉候选仍是旧的空数组。

**突破方法**：从 drawer DOM 的 react fiber 找到 antd Form 实例，一次性写入
所有相互依赖的字段（详见 §21 CONVERT_DATA）：

```javascript
function findFormInstance(drawer) {
  const key = Object.keys(drawer).find(k =>
    k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$'));
  if (!key) return null;
  const seen = new Set(); const stack = [drawer[key]]; let guard = 0;
  while (stack.length && guard++ < 20000) {
    const f = stack.pop();
    if (!f || seen.has(f)) continue;
    seen.add(f);
    try {
      if (f.stateNode && typeof f.stateNode.getStateNode === 'object' &&
          typeof f.stateNode.getFieldsValue === 'function') return f.stateNode;
      if (f.ref && f.ref.current &&
          typeof f.ref.current.getFieldsValue === 'function') return f.ref.current;
      const mp = f.memoizedProps;
      if (mp && mp.form && typeof mp.form.getFieldsValue === 'function') return mp.form;
      if (mp && mp.formRef && mp.formRef.current &&
          typeof mp.formRef.current.getFieldsValue === 'function') return mp.formRef.current;
      let st = f.memoizedState, g = 0;
      while (st && g++ < 30) {
        const v = st.memoizedState;
        if (v && typeof v === 'object') {
          if (typeof v.getFieldsValue === 'function') return v;
          if (v.current && typeof v.current.getFieldsValue === 'function') return v.current;
        }
        st = st.next;
      }
    } catch (e) {}
    if (f.child) stack.push(f.child);
    if (f.sibling) stack.push(f.sibling);
  }
  return null;
}
```

### 0.9 无表单节点（BREAK）不能用 `submit()`

`submit()` 的三级兜底都要聚焦 `input.ant-input`，BREAK 抽屉一个输入框都没有，
结果 `{'via': 'FAILED'}` 什么都不发生。直接点抽屉里的「确定」按钮：
```javascript
[...drawer.querySelectorAll('button')]
  .find(b => (b.textContent||'').trim() === '确定')
```

---

## 一、逐节点 UI 契约

### 1. FOR（计数循环）

| key | 标签 | 类型 | 必填 | 默认值 |
|---|---|---|---|---|
| `forStart` | 循环起始值 | valueComponent | ✅ | `{type:"Simple",simple:0,desc:0}` |
| `forEnd` | 循环终止值 | valueComponent | ✅ | `{type:"Simple",desc:0,simple:0}` |
| `forStep` | 步长 | inputNumber | ✅ | `1` |
| `operator` | 执行条件 | executionConditions | ❌ | `"<="` |
| `targetName` | 循环变量名称 | outputName | ✅ | `计数循环变量_1` |

- `operator` 4 值：`<=` / `<` / `>=` / `>`（UI 文案：小于等于/小于/大于等于/大于）
- `forStart`/`forEnd` valueType：`["CONSTANT","EXPRESSION","CONTEXT_VARIABLE"]`，
  要求结果 `dataType=INTEGER`；取值范围 `max: 99999999`
- **坑：全字段都有默认值 → 一个字段都不改时 `configChanged` 保持 `false`，
  点「确定」只关抽屉、不发 `udcMicroflowUpdatePost`，节点只活在 Redux store 里。
  必须先真实修改任一字段（如循环变量名称）再提交。**
- **坑：根级 FOR 卡片可能不渲染**（`flowFrame` 与后端都有，但画布
  `.udc-microflow-editor-node-container` 查不到），此时 `open_node` 返回 `empty drawer`。
- 容器节点：`FOR` 与 `FOR_EACH` 同构，都带 `nodes: []` 子链；计数循环 `foreach: null`。

### 2. BREAK（跳出循环）

**只能在 `FOR_EACH` / `FOR` 的循环体容器内添加。**
根级节点面板 24 项不含「跳出循环」；循环体容器 DOM 是 `.branches.loop`，
其内点加号面板才会出现。前端旁证：
```javascript
ej = ["CUSTOM_ERROR","BREAK","FRONT_CUSTOM_ERROR","CLOSE_PAGE","CONFIRM_CLOSE_PAGE"]
```

- **零表单项、零出参**：`items: []`，`output/input/name` 全 `null`
- **`noCompleted: true`**：前端创建时直接 `isCompleted = true`
  ```javascript
  (t?.noCompleted)===!0 && (n.isCompleted=!0)
  ```
- 后端结构：`{nodeId, type:"BREAK", actionType:"BREAK", caption, input:null, output:null, isCompleted:true, name:null}`
- **坑：`submit()` 不适用**（无输入框），必须直接点「确定」
- **坑：BREAK 自身不发保存请求**，靠流程级「保存并提交」随流程落库

### 3. CUSTOM_ERROR（自定义错误）

**类型名陷阱**：面板 actionType 是 `FRONT_CUSTOM_ERROR`，
**后端 dataSchema 的实际 `type` 是 `CUSTOM_ERROR`**（无 `FRONT_` 前缀）。
按 `FRONT_CUSTOM_ERROR` 回读永远命中 0。

| key | 标签 | 必填 | 显示条件 |
|---|---|---|---|
| `errorType` | 错误提示方式 | ❌ | 恒显示，默认 `GLOBAL` |
| `sourceData` | 原始数据 | ✅ | `errorType=="POSITION"` |
| `selectParam` | 错误数据 | ✅ | `errorType=="POSITION"` |
| `attrType` | 定位字段（多选） | ✅ | `errorType=="POSITION"` |
| `error` | 填写错误 | ✅ | `errorType=="GLOBAL"` |
| `attrError` | 填写错误 | ✅ | `errorType=="POSITION"` |

- `errorType` 2 值：`GLOBAL`（全局提示）/ `POSITION`（定位到页面元素）
- **坑：`error` 和 `attrError` 标签都叫「填写错误」**，key 不同，按 label 定位要结合 `errorType`
- **坑：切 `errorType` 会清空全部相关字段**（`setEmptyBeforeChanged` 含
  `sourceData/selectParam/attrType/error/attrError`）
- **坑：切回 GLOBAL 时残留的 POSITION 必填校验会报 `值不能为空`**，需先确认字段已收拢
- **坑：`填写错误` 是 valueComponent，必须 focus + `Input.insertText`**
- 后端：`output/input/name` 全 `null`；GLOBAL 时 `error` 有值、POSITION 时 `error:null` 且
  `sourceData/selectParam/attrType/attrError` 有值

### 4. CREATE_MAP（创建映射组）

| key | 标签 | 必填 | 默认值 |
|---|---|---|---|
| `entries` | 添加映射 | ❌ | `null` |
| `title` | 节点出参名称 | ✅ | `映射组_1` |

- 按钮文本是 **「添加键值对」**（不是「添加映射」，后者是 form-item 的 label）
- 每行两个 valueComponent：`input[placeholder="请输入映射的键(key)"]` + 值输入框
- **键只能是 String 类型**，值支持任意类型
- 后端 `output`：`{dataType:"MAP", javaType:"java.util.Map", generics:{keyType:{dataType:"String"}, valueType:{dataType:"Object", javaType:"java.lang.Object"}}, name:"_CREATE_MAP_xxx"}`
- `generics` 同时出现在 `output` 内和节点顶层
- `entries` 结构：`[{key:{type:"Simple",simple:"key1",desc:"key1"}, value:{type:"Simple",simple:"value1",desc:"value1"}}]`

### 5. MAP_OPERATION（映射操作）

**4 种操作类型及联动字段（实测）**：

| UI | operationType | 触发字段 | 出参 |
|---|---|---|---|
| 获取 | `GET` | 该值的映射键 / 映射值类型 / 数据类型 / 是否列表 / 节点出参名称 / 未获取到数据时 / 提示内容 | 映射值本身 |
| 赋值 | `PUT` | 添加映射 | 无 |
| 删除 | `REMOVE` | 要删除的键 | 无 |
| 获取键列表 | `KEY_SET` | 节点出参名称 | 键组成的列表 |

```javascript
eD = [{label:"获取",value:"GET"},{label:"赋值",value:"PUT"},
      {label:"删除",value:"REMOVE"},{label:"获取键列表",value:"KEY_SET"}]
```

- `selectMap` 只能选 `dataType=="MAP" && type=="OBJECT"` 的前序出参
- `paramType` 5 值：`BASIC`（基本类型）/ `ENTITY_OBJECT`（实体对象）/
  `DEFAULT_OBJECT`（自定义对象）/ `ENUM`（选项集）/ `MAP`（映射）
- `output` 随 `paramType` 变化；**`generics` 恒存在**（继承上游 MAP 泛型签名）
- `nullHandling` 默认 `TERMINATION`（未取到键时终止流程），需配 `nullPromptMessage`
- `arrayOrObject`：`OBJECT`（单条）/ `ARRAY`（列表），`paramType=="MAP"` 时列表禁用

### 6. CALL_APP_SERVICE（自定义服务）

| key | 标签 | 必填 |
|---|---|---|
| `app` | 选择应用 | ✅ |
| `selectMethod` | 选择服务 | ✅ |
| `outputName` | 节点出参名称 | ✅ |

空提交报错：`selectMethod 请输入选择服务` / `outputName 请输入节点出参名称`

**入参三形态（由服务签名决定，实测 9 个服务）**：

| 形态 | 触发字段 |
|---|---|
| 无入参 | 直接配出参名 |
| 单参（非 DTO） | `参数`（valueComponent，必填） |
| DTO 入参 | `赋值方式`（必填）+ `参数映射`（选填） |
| 列表入参 | `赋值方式` + `参数`（选填） |

- `selectMethod` 存**完整方法元数据**：`fullName / implClass / md5 / parameter / returnValue / isCondition`
- `returnValue` 是 `SingleResponse<T>` 包装，`item.itemType` 才是真实返回 DTO
- **出参名字段是 `outputName`**（不是其他节点的 `title`）
- **`outPutDesc` 大小写陷阱**：P 大写
- 可选应用 = 当前应用 + 所有依赖应用

### 7. SUB_MICROFLOW（子微流程）

| key | 标签 | 必填 |
|---|---|---|
| `mfService` | 选择微流程服务 | ✅ |
| `value` / `mappingType` / `attrs` | 参数 / 赋值方式 / 参数映射 | 视服务签名 |
| `outPutDesc` | 出参描述 | ❌ |
| `outputName` | 节点出参名称 | ✅ |

- **数据源是 `fetchMicroflowServiceListSubMf`**（与 `CALL_MICRO_FLOW` 的
  `fetchMicroflowServiceList` 不同）
- 只列**当前应用下正式态（RELEASE）的服务定义类型（SERVICE）微流程**；
  `DRAFT` 项显示 `[未保存]` 且 `disabled`
- 实测下拉分组「数据迁移」，8 个可用项 + 1 个 DRAFT 禁用项
- **坑：必须真实鼠标点开 + ArrowDown/Enter 键盘选中**，`dispatchEvent(click)` 无效
- `mfService` 存完整服务元数据（含 `input`/`output`/`path`/`method`/`restType`/`hasInput`/`hasOutput`）

### 8. CONVERT_DATA（类型转换）

**9 种 convertType 及 selectParam 过滤规则（实测全集）**：

| # | UI 文案 | value | selectParam filter |
|---|---|---|---|
| 1 | 多选数据拆分为长整数列表 | `multiAssociation2List` | Entity/CtpEnum 且 multiSelect==true |
| 2 | 长整数列表拼接为多选数据 | `List2multiAssociation` | `javaType=="java.lang.Long" && type=="Array"` |
| 3 | 文本转长整数【ID】 | `String2Long` | `dataType=="String" && type=="Object"` |
| 4 | 文本转整数 | `String2Integer` | 同上 |
| 5 | 文本转小数 | `String2Decimal` | 同上 |
| 6 | 基础类型转文本 | `BasicData2String` | 非 Dto/Entity/Enum/String 的 Object，或 Entity |
| 7 | 获取选项值编码 | `GetEnumCode` | `dataType=="Enum" && type=="Object"` |
| 8 | 获取选项值 | `GetEnumName` | 同上 |
| 9 | 指定符号拆分文本 | `Split` | String 或 `java.lang.String` |

- **只有 `Split` 额外显示「指定拆分符号」**（`ishidden: convertType.value !== "Split"`）
- 拆分符号 10 值：`COMMA` / `PERIOD` / `UNDERSCORE` / `MIDLINE` / `DIVLINE` /
  `QUSMARK` / `AND` / `START` / `SLASH` / `BACKSLASH`

**★ 本节点最难的三个坑（必须按序处理）**：

1. **`convertType` 必须是 `{value: ...}` 结构**
   `selectParam` 的 filter 读的是 `e?.convertType?.value`，
   但 UI 真实选中后 Form 里存的是 `{key, dataType, type, desc}`（**没有 `value`**）。
   → `switch` 走不到任何分支，`selectParam` 候选恒为空。

2. **filter 是渲染期闭包**，`setFieldsValue({convertType})` 不会刷新候选。

3. **正确路径：一次性同时写入 `convertType` + `selectParam`**
   ```javascript
   form.setFieldsValue({
     convertType: { value:'BasicData2String', key:'BasicData2String',
                    dataType:'String', type:'Object', desc:'基础类型转文本' },
     selectParam: { description, dataType, javaType, type, name, outputName,
                    position:'parent',
                    nodeInfo:{ nodeId, type, actionType },
                    key: name + '_' + actionType,
                    iconKey:'LinedSearch', parentLabel:'', disabled:false, isLeaf:true }
   });
   ```
   `selectParam` 可从 store 同类型输出节点构造：
   `Object.values(flowNodes).filter(n => n.output && n.output.dataType === 'STRING')`

- **出参 `javaType` 为空串 `""`**（不是 `java.lang.String`）；
  `output.dataType` 是 **`String`**（首字母大写），与其他节点的 `STRING`（全大写）不同
- `output.type`：`BasicData2String` 时为 `Object`，`Split` 时为 `Array`

### 9. DATA_MAPPING（数据转换）

6 字段全必填：`selectParam` / `targetType` / `app` / `structure` / `mappingRule` / `title`

- `targetType` 2 值：`ENTITY`（实体对象）/ `DTO`（自定义对象）
- **映射关系弹窗**（点「未配置」→ 标题「映射关系配置」，1050×381）三下拉：
  | 字段 | 选项来源 |
  |---|---|
  | 目标对象 | 目标实体字段列表（实测 10 项） |
  | 映射方式 | **固定 2 种：`值拷贝` / `常量`** |
  | 值 | 来源数据字段列表（实测 6 项） |
- 映射方式 → 后端 `mappingMode`：`值拷贝` → `REFERENCE`；`常量` → `CONSTANT`
- 后端 `mappingRule`：
  ```json
  {"uuid":"...", "id":"<目标DTO全名>", "caption":"...", "type":"ARRAY",
   "javaType":"...", "mappingRows":[{"uuid":"...",
     "targetField":{id,path,name,desc,dataType,type,javaType},
     "mappingMode":"REFERENCE",
     "value":{"reference":{同 targetField 结构}}}],
   "subobjects":[]}
  ```
- **`output.type` 是 `ARRAY`**（产出列表），`output.dataType` 是 `DTO`
- **实体下拉是 tree 结构**：`.ant-select-tree-treenode`，不是 `.ant-select-item-option`
- `structure`（目标实体，含 `entity` 域类全名）与 `selectParam`（来源节点输出，
  含 `nodeInfo`/`position`）是**两套独立引用**

### 10. PUBLISH_BUSINESS_EVENT（事件投递）—— UNVERIFIED

> **落库状态 UNVERIFIED**：当前测试应用无可投递的 MQ 消息定义，两个事件下拉均为空
> （下拉显示「暂无数据 新建」），无法完成完整提交。
> 已用 `udcMicroflowSearchEventListPost`（**body 必须传 `appId`**，不是 `appName`）
> 验证事件列表接口可用，返回 `XzhVerifyEvent`（小爪验收事件）。
> **落库前置条件**：应用需先配置 MQ 消息定义（应用设计 → 消息定义）。

**双「事件类型」标签陷阱**（抽屉里有两个 label 都叫「事件类型」的 form-item）：

| form-item 索引 | DOM id | key | 选项 |
|---|---|---|---|
| 第 1 个 | `#eventType` | `eventType` | 应用间(异步) `AMONG_APP` / 应用内(同步) `IN_APP` |
| 第 2 个 | `#messageType` | `messageType` | 普通事件 `DEFAULT` / 延迟事件 `DELAY` |

- `eventType` 用 `ant-radio-button-wrapper`（button 型），
  `messageType` 用 `ant-radio-wrapper`（圆点型）→ **按 `.ant-radio-wrapper` 找
  `eventType` 会拿到空文本，两个类名都要匹配**
- 联动：`IN_APP` 隐藏「选择应用」与 `messageType`；`DELAY` 触发「发送时间」必填
- **两种「可投递的事件」字段名不同**：`AMONG_APP` → `selectMq`；`IN_APP` → `selectEvent`
- 数据源（反编译证实）：
  ```javascript
  // AMONG_APP
  fetchSendMqList({appId, appName})   // 返回 {fullName, caption, topic, contentDto, customs}
  // IN_APP
  fetchMicroFlowEventDtoList({appId, appName})  // 返回 {fullName, caption, source, dtoType, udcApp}
  ```
- `selectMq` 选项**必须带 `contentDto`**，否则后续「赋值方式/参数」不显示
- **`type` 是 `BusinessEvent`（首字母大写）**，回读用 `actionType == 'PUBLISH_BUSINESS_EVENT'`

---

## 二、22 类落库统计（test2 / -6371737850148111694 / 2026-10-28）

后端 `dataSchema` 回读确认已落库的 actionType：

```
CREATE_VARIABLE     2    RETRIEVE            1    CHANGE_ENTITY      1
CREATE_ENTITY       1    CREATE_LIST         1    RETRIEVE_ARRAY     1
CREATE_BATCH_ENTITY 1    CHANGE_BATCH_ENTITY 1    DELETE_ENTITY      1
FOR_EACH            1    BREAK               1    LIST_OPERATION     1
CHANGE_LIST         1    CHANGE_VARIABLE     1    FOR                1
CREATE_MAP          3    MAP_OPERATION       1    CALL_APP_SERVICE   1
SUB_MICROFLOW       2    CONVERT_DATA        1    DATA_MAPPING       1
CUSTOM_ERROR        1    BRANCH              1
```

**PUBLISH_BUSINESS_EVENT = 0（UNVERIFIED，环境依赖缺失）**

## 三、尚未实测的节点

以下 actionType 在 `ACTIVITY_NODE_TYPES` 里有定义，但本次未做 UI 实测：

`CONNECTOR` / `ATTRIBUTE_REQUIRED` / `ASSIGN_VALUE` / `SHOW_MESSAGE` /
`ATTRIBUTE_UNIQUE` / `CALL_MICRO_FLOW` / `CALL_DATA_FLOW` /
`CALL_DATA_FLOW_FRONT` / `EXTEND_ACTION` / `SET_DATASOURCE` / `DEFAULT_VALUE`

其中 `CALL_MICRO_FLOW`（调用微流程）与 `SUB_MICROFLOW` 同源但数据源不同
（`fetchMicroflowServiceList` vs `fetchMicroflowServiceListSubMf`），
`CALL_DATA_FLOW`（执行生单规则）与 `CONVERT_DATA` 在面板上并列。
