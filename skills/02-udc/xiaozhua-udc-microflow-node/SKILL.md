---
name: xiaozhua-udc-microflow-node
description: "Use when 在 UDC 微流程里生成/校验节点（22 类已 LIVE 实测）。按节点类型取真实字段、过 UI 层闸门、走前端驱动提交。"
version: 1.0.0
---

# 微流程节点生成（22 类 LIVE 实测）

适用：分析或校验 UDC 微流程节点的前端交互约束；经明确授权后，可按下述方式操作编辑器。
不适用：Java 扩展开发、运行态故障诊断，或未经授权的流程修改、提交与发布。

> 整包 POST `dataSchema` 可能绕过前端「逐节点添加 + 确定」的回填与校验；历史缺字段样例见
> `core/facts/udc/microflow/node-authoring-contract.md`。这不证明所有 API 生成方式必然失败。

## 一、能力边界（先说清楚）

分发状态：BLOCKED。下面的节点模板来自真实流程，有限扫描已发现客户标识命中；
禁止直接打包。其他事实、代码和证据的依赖闭包及脱敏审查也尚未完成。

| 层 | 资产 | 覆盖 |
|---|---|---|
| 结构层必填/值域 | `components/udc/microflow_constraints.py` | 反编译 udc-biz 5.3.517 + 全库 3000 条真实节点统计 |
| **UI 交互层** | `components/udc/microflow_ui_constraints.py` | **22 类节点 LIVE 实测**（本文档配套） |
| 节点模板 | `fixtures/microflow/node_templates/<ACTION>.json` | 25 类真实流程抽取 |
| 逐节点契约 | `docs/audit/udc-semantics/MICROFLOW-<ACTION>-CONTRACT.md` | 22 份 |
| 汇总事实 | `core/facts/udc/microflow/node-ui-contracts-22.md` | 联动/坑/值域 |

**已 LIVE 实测（22 类）**：
`CREATE_VARIABLE` `RETRIEVE` `RETRIEVE_ARRAY` `CREATE_ENTITY` `CHANGE_ENTITY`
`CREATE_BATCH_ENTITY` `CHANGE_BATCH_ENTITY` `DELETE_ENTITY` `CREATE_LIST` `CHANGE_LIST`
`LIST_OPERATION` `CREATE_MAP` `MAP_OPERATION` `FOR_EACH` `FOR` `BREAK`
`CUSTOM_ERROR` `CONVERT_DATA` `DATA_MAPPING` `CALL_APP_SERVICE` `SUB_MICROFLOW`
`CHANGE_VARIABLE`

**UNVERIFIED（1 类）**：`PUBLISH_BUSINESS_EVENT` —— 需要应用侧先配 MQ 消息定义，
当前测试应用无可投递事件，下拉恒为空。契约有但**未落库证实**。

**未实测**：`CONNECTOR` `ATTRIBUTE_REQUIRED` `ASSIGN_VALUE` `SHOW_MESSAGE`
`ATTRIBUTE_UNIQUE` `CALL_MICRO_FLOW` `CALL_DATA_FLOW` `CALL_DATA_FLOW_FRONT`
`EXTEND_ACTION` `SET_DATASOURCE` `DEFAULT_VALUE`

## 二、生成流程（5 步）

```
① 定 actionType → ② 查契约拿字段/值域 → ③ 过 UI 闸门 → ④ 前端驱动落库 → ⑤ 后端回读复验
```

### ① 定 actionType

活动节点 `type` 恒为 `ACTIVITY`，真实类型在 **`actionType`**。
控制节点（`BRANCH`/`CONDITION`/`FOR_EACH`/`FOR`/`BREAK`/`CUSTOM_ERROR`/`END`）的 `type` 就是本身。

> 回读时用 `type == 'CONVERT_DATA'` 会永远命中 0 条。

### ② 查契约

```python
from components.udc.microflow_ui_constraints import (
    CONVERT_TYPES, CONVERT_TYPE_LABELS, SPLIT_SYMBOLS,
    MAP_OPERATION_TYPES, MAP_PARAM_TYPES,
    CUSTOM_ERROR_FIELDS_BY_TYPE,
    DATA_MAPPING_TARGET_TYPES, DATA_MAPPING_MODES,
    EVENT_TYPES, EVENT_SELECT_FIELD,
    FOR_OPERATORS, FOR_DEFAULT_OPERATOR,
)
```

逐节点完整字段表见 `docs/audit/udc-semantics/MICROFLOW-<ACTION>-CONTRACT.md`。

### ③ 过 UI 闸门（生成前必跑）

```python
from components.udc.microflow_ui_constraints import validate_node_ui, validate_schema_ui

problems = validate_node_ui(node, parent_chain=["FOR_EACH"])   # 单节点
problems = validate_schema_ui(data_schema)                      # 整链
```

`validate_node_fields` 已自动叠加这层校验，走既有入口也会生效。
**空问题列表不代表节点已知或受支持**：未知 action 可能未执行专用校验。
使用 `components.udc.microflow.capability_registry.advisory(schema)` 核对能力矩阵，
遇到 `UNVERIFIED` 或矩阵不可用不得宣称支持；该 advisory 只是提示，不是执行阻断。

### ④ 前端驱动落库

以下为已观察到的 CDP 画布路径，不排除其他经验证的路径。操作前必须明确授权目标流程和写入范围；
节点确认可能即时写库，流程级「保存并提交」可能转为 RELEASE，须单独获得明确授权。

```python
from components.udc.microflow.live import cdp, env, ui

d = cdp.Driver(); d.attach(); ui.ensure_visible(d)

# 0) 清查看模式弹窗（会叠多层）
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

# 1) 滚到画布最右，点加号
d.eval("""(()=>{const el=document.querySelector(
  '.udc-microflow-editor-node.branch.flex1');if(el)el.scrollLeft=el.scrollWidth;})()""")
time.sleep(2.5)
plus = json.loads(d.eval("""JSON.stringify([...document.querySelectorAll('.anticon.add-button')]
  .map(el=>{const q=el.getBoundingClientRect();
    return {x:Math.round(q.x+q.width/2),y:Math.round(q.y+q.height/2)};})
  .filter(b=>b.x>150&&b.x<1680&&b.y>250&&b.y<520))"""))
d.click_mouse(plus[-1]['x'], plus[-1]['y']); time.sleep(2.5)

# 2) 选节点类型
d.pick_node_type('类型转换'); time.sleep(4.5)

# 3) 填字段（见下方「填写手法」）
# 4) 提交
res = ui.submit(d, wait=14.0)
# 5) 流程级保存
ui.click_react(d, "document.getElementById('microflow_save')")
```

### ⑤ 后端回读复验

```python
meta, ds = env.read_schema_page(d, MID)
# 用 actionType 递归找节点，不要用 type
```

**HTTP 200 / 「操作成功」不算通过**，必须回读到节点且 `isCompleted: true`。

## 三、填写手法（按控件类型选，选错就白填）

| 控件 | 正确手法 | 错误手法 |
|---|---|---|
| `valueComponent` | `input.focus()` + `d.cmd("Input.insertText", text=...)` | 原生 setter 写 `input.value`（React 不更新，报 `值不能为空`） |
| 自定义 select（`treeListSelector`/`mfServiceSelector`/`convertTypeSelector`） | **真实鼠标 `click_mouse(cx,cy)` 打开 + 键盘 `ArrowDown`+`Enter`**，或鼠标点选项坐标 | `dispatchEvent(new MouseEvent('click'))`（无效） |
| tree 型下拉（实体/事件） | 选项选择器同时匹配 `.ant-select-item-option` 和 `.ant-select-tree-treenode` | 只匹配前者（拿不到） |
| 普通 `input.ant-input` | `ui.set_input()` | — |
| 无表单节点（`BREAK`） | 直接点抽屉「确定」按钮 | `ui.submit()`（三级兜底全失效） |
| **抽屉「确定」/「添加字段」等 React 按钮** | **`react_click(d, text, root)`（调 props.onClick）** | **`el.click()`（不触发 React onClick，数据不落库）** |
| **受控 input / textarea** | **`set_controlled_input(d, sel, val, root)`** | `el.value = x`（React value tracker 拦截） |
| **antd Select 打开** | **`open_antd_select(d, sel, root)`**（mousedown+mouseup+click） | 单独 `click`（下拉不展开） |

### ★ 最关键的一条：`el.click()` 会静默失败

实测（2026-10-28，SUB_MICROFLOW attrs 落库）：

```
el.click()  → attrs 表单已填 3 行 → 点「确定」→ store attrCount 仍是 0
props.onClick() → 同样 3 行 → 点「确定」→ store attrCount = 3，flowChanged=true
```

**症状**：UI 上一切正常（字段选好、值填好、无报错），但点确定后
`store.flowNodes[id].attrs` 仍是 `[]`，后端 `dataSchema` 也读不到。
**误判风险极高**：脚本会打印「picked 成功 / set 成功 / 确定 ok」，
但数据一条没进。必须**每次都以 store 或后端回读为唯一判据**。

统一用 `components/udc/microflow/live/react_click.py` 的四个原语：

```python
from components.udc.microflow.live.react_click import (
    react_click, set_controlled_input, open_antd_select, pick_option,
)

DRAWER = 'aside.udc-microflow-editor-node-settings'
react_click(d, '确定', root=DRAWER)          # 不用 el.click()
react_click(d, '添加字段', root=DRAWER)
set_controlled_input(d, 'input.ant-input', 'AUTO', DRAWER)
open_antd_select(d, '.form-list-item .ant-select-selector', DRAWER)
pick_option(d, want='方案编码')
```

### ★ 第二个：`microflow_save` 是「保存并提交」，不是保存草稿

```
点 microflow_save → 流程变 RELEASE（正式态）→ readonly=true → 所有节点不可编辑
```

后续任何节点操作都会因为 `readonly` 失败（抽屉打不开、`aside` 数量异常）。
恢复路径：点工具栏「编辑」转回 `DRAFT`，**然后必须 `location.reload()`**，
否则残留的 `aside` 会让抽屉打不开。

节点级配置（抽屉「确定」）本身会即时落库，不需要点保存。

**带 `filter`/`asyncFilter` 的下拉**（`CONVERT_DATA.selectParam`、`DATA_MAPPING.selectParam`）：
filter 是渲染期闭包，`setFieldsValue` 不刷新候选。必须从 drawer DOM 的 react fiber
找到 antd Form 实例，**一次性同时写入相互依赖的字段**：

```python
FIND_FORM_JS = r"""
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
      if (f.stateNode && typeof f.stateNode.getFieldsValue === 'function') return f.stateNode;
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
"""
```

## 四、五个必踩的坑（22 类全部踩过）

### 4.1 提交失败后抽屉卸载 → 必须重载页面重做

`drawer_info()` 返回 `items: []` 就是卸载了。**不要继续操作**，
`location.reload()` + 轮询等 `appReduxStore` 就绪后从头做。

### 4.2 全流程保存静默无请求 → 是别的节点有悬空引用

校验函数 `W()` 走 `console.log("firstErrorNode", e)` + `message.error(...)`，
**不抛异常、不发请求**。必须注入 console 捕获：

```javascript
window.__clog=[];
['log','warn','error'].forEach(k=>{const o=console[k];console[k]=function(){
  try{window.__clog.push({k,a:[...arguments].map(x=>{
    try{return typeof x==='object'?JSON.stringify(x).slice(0,250):String(x)}catch(e){return '?'}})});}catch(e){}
  return o.apply(this,arguments);};});
```

实测捕获过：`节点"修改变量(1)"引用的参数"变量_1"已失效，请重新配置！`

### 4.3 卡片点击必须居中

画布 `scrollWidth` 约 4900，卡片右边缘超过 1699 时点击无效。
先滚到卡片中心 x 落在 300~1400 再点。

### 4.4 `CONVERT_DATA` 的 `convertType` 必须是 `{value:...}`

filter 读 `e?.convertType?.value`，但 UI 选中只存 `{key, dataType, type, desc}`（**无 `value`**）
→ `switch` 走不到任何分支，`selectParam` 候选恒为空。

### 4.5 `BREAK` 只能在循环体内添加

根级面板 24 项不含「跳出循环」。必须在 `FOR_EACH`/`FOR` 的 `.branches.loop` 容器内点加号。

## 五、自证（改约束后）

在源仓库运行离线回归：

```bash
python -m pytest tests/test_microflow_ui_constraints.py -q -rs
```

该测试包含合成正反例，也包含依赖本机历史 scratch 样本的测试；样本缺失时后者会跳过，
必须报告 passed 和 skipped；缺样本时 pytest 仍可能退出 0，不能仅凭退出码或其他测试通过
宣称历史样本已验证，更不得将离线结果称为 LIVE。安装包未携带这些测试或历史样本时，
该命令不可用，须标记 UNVERIFIED；不能通过复制客户数据来补齐。

历史 scratch 验证脚本仅供源环境另行审查后使用，不是分发依赖或替代验收。平台修改经授权后，
仍须执行前端「检查」、逐节点核查抽屉错误与后端回读；草稿状态和发布操作分别按授权处理。
脚本必须有可验证退出码；反向验证必须重放同一注入，量退出码勿接管道。

## 六、红线

- 只读优先；写操作必须先确认目标流程与影响面
- 客户真实 appId / 组织名**不入结论区**（`scratch/` 不在 PII 豁免区），用保留段
  `datamigration9000000000000000001` 代号
- UNVERIFIED 结论不得报成 LIVE PASS
- `HTTP 200` / 「操作成功」≠ 落库成功，必须后端回读
