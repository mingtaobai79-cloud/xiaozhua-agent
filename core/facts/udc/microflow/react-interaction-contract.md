# UDC 微流程节点配置：React 受控组件交互契约

> 2026-10-28 LIVE 实测。任何通过 CDP/脚本操作 UDC 微流程编辑器的代码，都必须遵守本契约。

## 一、核心结论

**`el.click()` 会静默失败。** 不报错、不抛异常、UI 正常，但数据一条都不落库。

| 手法 | 抽屉「确定」结果 | store `attrs` | 后端 `dataSchema` |
|---|---|---|---|
| `el.click()` | 返回 `ok` | `[]` | 空 |
| `props.onClick()` | 返回 `ok` | 3 条 | 3 条 |

实测节点：`SUB_MICROFLOW_lXdXOJ`（子微流程），配置 `SyncNowDto` 的 3 个字段映射。

## 二、四个交互原语

模块：`components/udc/microflow/live/react_click.py`

### 2.1 `react_click(d, text, root=None)`

调 React `props.onClick`，而非 DOM click。

```python
react_click(d, '确定', root='aside.udc-microflow-editor-node-settings')
react_click(d, '添加字段', root=DRAWER)
```

查找顺序：
1. `__reactProps$xxx` 上的 `onClick`（优先）
2. `__reactFiber$xxx` 树向上最多 40 层找 `memoizedProps.onClick`

匹配规则：按钮文本**精确相等**（去空白），且 `getBoundingClientRect()` 宽高 > 0（排除隐藏按钮）。

### 2.2 `set_controlled_input(d, selector, value, root)`

绕过 React value tracker 给受控 input/textarea 赋值。

```python
set_controlled_input(d, 'input.ant-input', 'AUTO', DRAWER)
set_controlled_input(d, 'textarea', '未查询到记录，流程终止', DRAWER)
```

必须走原型 setter：

```javascript
Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(inp, val)
```

直接 `inp.value = val` 会被 React 的 value tracker 判定为「值未变」，不触发 onChange。
赋值后派发 `input` → `change` → `blur` 三个事件。

### 2.3 `open_antd_select(d, selector, root)`

antd Select 必须派发完整鼠标序列：

```javascript
['mousedown', 'mouseup', 'click'].forEach(t => sel.dispatchEvent(new MouseEvent(t, {...})))
```

单独 `click` 打不开下拉。

### 2.4 `pick_option(d, want=None, idx=0)`

选下拉项，兼容两种形态：

- `.ant-select-item-option`（普通下拉）
- `.ant-select-tree-treenode`（树形下拉）

必须过滤 `.ant-select-dropdown-hidden`，否则会拿到已关闭的旧下拉。

## 三、`microflow_save` 是「保存并提交」

```
点 microflow_save → 流程变 RELEASE（正式态）→ readonly=true
```

后果：所有节点不可编辑，抽屉打不开，`aside` 元素数量异常（会出现 2 个残留）。

恢复路径：

```python
react_click(d, '编辑')          # 转回 DRAFT
time.sleep(3)
d.eval('location.reload()')     # 必须重载，否则残留 aside 阻塞抽屉
time.sleep(15)
```

**节点级配置（抽屉「确定」）会即时落库**，不需要点保存按钮。

## 四、判据铁律

**唯一有效判据是 store 或后端回读**，不是脚本返回值。

```python
# 无效判据（会骗你）
r = react_click(d, '确定')
assert r['ok']          # ← 这只能证明点击发生了，不能证明数据进去了

# 有效判据
store = js(d, """(()=>{
  const n = appReduxStore.getState().appDesign.microflowEditorReducer
    .flowNodes['SUB_MICROFLOW_lXdXOJ'];
  return n.attrs.length;
})()""")
assert store == 3

# 更强判据：后端回读
meta, ds = env.read_schema_page(d, MID)
node = find_node(ds, 'SUB_MICROFLOW_lXdXOJ')
assert len(node['attrs']) == 3
```

## 五、`attrs` 的真实结构

`SUB_MICROFLOW` 的入参映射，每条形如：

```json
{
  "value": {
    "type": "Simple",
    "simple": 0,
    "desc": 0
  },
  "attrType": {
    "name": "days",
    "id": "com.seeyon.<app>.dto.microflow.SyncNowDto.days",
    "fullName": "com.seeyon.<app>.dto.microflow.SyncNowDto.days",
    "javaType": "java.lang.Integer",
    "dataType": "INTEGER",
    "type": "OBJECT",
    "desc": "天数",
    "relationApp": "<app>",
    "refApp": "<app>",
    "multiSelect": false,
    "filterDataType": "INTEGER",
    "filterType": "OBJECT",
    "filterFullName": "...",
    "dataI18n": false,
    "sort": 0
  }
}
```

关键点：

- `value.type` 恒为 `"Simple"`（常量赋值）
- `value.simple` 是实际值，类型跟随 `attrType.dataType`
- `attrType.id` / `fullName` 必须是 `<DTO全名>.<字段名>`
- `attrType.sort` 决定字段顺序

## 六、空白字符陷阱

`nullPromptMessage` 只有空白字符（如 `'\n\n\n\n\n\n'`）时：

- 前端判空用 truthy → `'\n'` 为真 → **保存放行**
- 运行时终止流程会弹出**空白提示框**

所以这类问题：

- 不是 `BLOCKING`（不拦保存）
- 是 `QUALITY`（质量问题，运行时可见）

体检脚本 `scratch/health_check_draft.py` 用三级分类：

| 级别 | 含义 | 判空方式 |
|---|---|---|
| `BLOCKING` | 会拦保存 | 前端 truthy（`''`/`null`/`[]`/`{}`） |
| `DANGLING` | 运行时炸 | 引用了不存在的出参 |
| `QUALITY` | 前端放行但语义没填 | `v != '' and v.strip() == ''` |

## 七、证据链

| 证据 | 路径 |
|---|---|
| 交互原语 | `components/udc/microflow/live/react_click.py` |
| 结构测试 | `tests/test_microflow_react_primitives.py`（6 项） |
| 体检脚本 | `scratch/health_check_draft.py` |
| 修复日志 | `scratch/draft-diagnosis/fix-log5.json` |
| Form 实例快照 | `scratch/draft-diagnosis/form-values.json` |
| 后端 schema | `scratch/draft-diagnosis/schema.json` |

**证据等级**：`el.click()` vs `props.onClick()` 对比 = `LIVE`（同节点同表单，只换点击手法）；
`attrs` 结构 = `LIVE`（后端 `dataSchema` 回读）。
