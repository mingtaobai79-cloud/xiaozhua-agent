# BREAK（跳出循环）节点契约

取证：CDP 真实建节点（循环体内）→ 后端 dataSchema 回读 → 前端 bundle `el={group:"base",name:"跳出循环"}` 权威定义交叉验证。
证据目录：`scratch/break-evidence/`。

## 1. 关键约束：只能在循环体内添加

**根级/分支级节点面板里没有「跳出循环」**。实测根级面板 24 项：
`分支 / 列表循环 / 计数循环 / 自定义错误 / 创建变量 / 修改变量 / 创建映射组 / 映射操作 / 创建列表 / 修改列表 / 列表操作 / 查询单条数据 / 查询多条数据 / 插入数据 / 批量插入数据 / 更新数据 / 批量更新数据 / 删除数据 / 自定义服务 / 事件投递 / 子微流程 / 执行生单规则 / 类型转换 / 数据转换`
—— **不含 BREAK**。

只有在 `FOR_EACH` / `FOR` 的循环体容器（DOM `.branches.loop`）内点加号，
面板才会出现「跳出循环」。前端源码旁证：

```javascript
ej = ["CUSTOM_ERROR","BREAK","FRONT_CUSTOM_ERROR","CLOSE_PAGE","CONFIRM_CLOSE_PAGE"]
```

## 2. 无表单、无出参

权威定义（bundle）：
```javascript
el = {group:"base", name:"跳出循环", type:"break", settings:[
  {items:()=>[{type:"descriptionInfo",
    value:"立即终止当前循环，进入循环节点的下一个节点。"}]}]}
```

- **零表单项**：抽屉只有「取消」「确定」两个按钮，`items: []`
- **零出参**：`output: null`，`input: null`，`name: null`
- **`noCompleted: true`**：创建时前端直接把 `isCompleted` 置为 `true`
  ```javascript
  (t?.noCompleted)===!0 && (n.isCompleted=!0)
  ```
  所以它不需要「配置完成」这一步。

## 3. 后端数据结构（已回读证实）

```json
{
  "nodeId": "BREAK_gc9rcq",
  "type": "BREAK",
  "actionType": "BREAK",
  "caption": "跳出循环(1)",
  "input": null,
  "output": null,
  "isCompleted": true,
  "name": null
}
```

挂在循环容器内：
```json
{
  "nodeId": "ForEach_TpOIwr",
  "type": "FOR_EACH",
  "caption": "列表循环(1)",
  "isCompleted": true,
  "nodes": [
    {
      "nodeId": "BREAK_gc9rcq",
      "type": "BREAK",
      "caption": "跳出循环(1)",
      "isCompleted": true,
      "output": null,
      "name": null,
      "input": null
    }
  ]
}
```

## 4. 提交路径（与普通节点不同）

普通节点走 `submit()`（Enter → 确定 → onFinish），**BREAK 不行**：
- `submit()` 的 A 级兜底要聚焦最后一个 `input.ant-input`，BREAK 抽屉没有输入框
- 结果：`{'via': 'FAILED'}`，什么都不发生

正确做法：直接点抽屉里的「确定」按钮
```javascript
[...drawer.querySelectorAll('button')]
  .find(b => (b.textContent||'').trim() === '确定')
```

## 5. 完整流程（实测可用）

1. 滚动画布到 `FOR_EACH` 循环体加号（`.branches.loop .anticon.add-button`）
2. 点击加号 → 面板选「跳出循环」
3. 抽屉打开（无表单）→ 点「确定」
4. **流程级「保存并提交」**才会真正写库（BREAK 自身不发 `udcMicroflowUpdatePost`）

## 6. 关键坑（实测踩到）

1. **循环体外不可添加**：根级面板没有 BREAK 项，`pick_node_type('跳出循环')` 会返回
   `{'err': 'not found'}`。
2. **`submit()` 不适用**：无输入框导致三级兜底全失效，必须直接点确定。
3. **保存被全流程校验阻塞**：BREAK 建好后点「保存并提交」如果静默无请求，
   真实原因往往是**别的节点有悬空引用**，报错只在 `message.error` 和 `console.log` 里，
   网络面板什么都没有。本次实测阻塞信息：
   `节点"修改变量(1)"引用的参数"变量_1"已失效，请重新配置！`
   → 必须先修好悬空引用，BREAK 才能随流程一起落库。
4. **验证要抓 console**：`W()` 校验失败走 `console.log("firstErrorNode", e)` +
   `message.error(...)`，不抛异常、不发请求。只监听 `Runtime.exceptionThrown`
   或只看网络会完全看不到。
