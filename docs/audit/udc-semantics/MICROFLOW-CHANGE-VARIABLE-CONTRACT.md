# 修改变量节点 value 落库契约 + hidden 状态解法

## 一、hidden 状态的根治办法（重大）

页面被遮挡/最小化时 `document.hidden === true`，后果：
- CSS 动画卡死
- 下拉菜单 `opacity:0`、坐标 `-9999`
- **抽屉底部按钮不渲染**（如「确定」按钮消失，只剩「关闭」）
- 编辑器 `contenteditable` 拿不到焦点

以前靠 `Page.bringToFront` / 激活 tab / Win32 置顶窗口，都不稳定。

**正解：**

```python
d.cmd("Emulation.setFocusEmulationEnabled", enabled=True)
```

一行搞定，不需要窗口在前台，`document.hidden` 立刻变 `false`。
已封装为 `flow_ops.ensure_visible(d)`，**每次进入页面、每次开抽屉前都调一次**。

## 二、窗口尺寸会影响 DOM 渲染

窗口从 maximized 变 normal 后，`innerWidth` 从 1699 → 1488，
抽屉布局正常化，**「确定」按钮才出现**。

排查命令：`flow_ops.drawer_buttons(d)` 打印抽屉全部按钮 + 坐标 + 是否可见。

症状对照：

| 现象 | 原因 |
|---|---|
| 只有「关闭」没「确定」 | 窗口尺寸异常 / 视口过窄 |
| `wrapper.x = 1699`（等于 vw） | 抽屉在视口外，坐标点击全部落空 |
| `body.textContent.length = 0~40` | 抽屉内容未渲染完，等 2-3 秒 |

## 三、修改变量 value 的真实落库路径

```
修改变量抽屉
├── 变量 [树选择]               必填
└── 变量值 [输入框] [+ 按钮]
        ↓ 点 + （React onClick 直调）
    ant-popover（宽 630）
    ├── 搜索框
    ├── 变量树：入参 / 变量_1 / 查询结果 / 空值[系统预制]
    └── [高级模式] 按钮
        ↓ 点「高级模式」
    表达式设置面板（与分支同一个组件）
        ↓ 写表达式 → 验证 → 确定
    输入框显示 {微流程....A + 微流程....B}
    form.value = {type:"Expression", expression:{schema:...}}
        ↓ 点抽屉底部「确定」（关键！）
    POST udcMicroflowUpdatePost → store.flowNodes[id].value 立即更新
```

**关键点：抽屉底部「确定」按钮才是节点级保存入口。**

之前踩的坑：以为抽屉是「即时保存/关闭即保存」，点了「关闭」、触发了 `onValuesChange`、
调了 `blur`、按了 Enter —— store 全都不动，`configChanged` 一直挂 true。
真相是必须点「确定」。

`onValuesChange = (changedValues, allValues) => B(allValues)`，
B 只更新局部 state，**不写 store**。所以直调 `onValuesChange` 无效。

## 四、抽屉按钮语义对照

| 按钮 | 行为 |
|---|---|
| `ant-drawer-close`（右上 ×） | 直接丢弃，不保存 |
| 「取消」 | 丢弃，不保存 |
| **「确定」** | `udcMicroflowUpdatePost` + 写 store |
| 「关闭」 | 只在某些只读态出现 |

## 五、两种 expression 的 executableExpr 形态

```
单变量（无运算符）:
  93gDaq3/...GvQ=_RETRIEVE_Ltqgzz._RETRIEVE_Ltqgzz.expText
  → 前缀直接拼变量路径，无括号

复合表达式:
  93gDaq3/...GvQ=+%28+_RETRIEVE_x._RETRIEVE_x.expNum+%2B+..._expNum+%29+
  → 前缀 + "+%28+" + 表达式 + "+%29+"
```

前缀 `93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=` 是服务端固定产物。

## 六、实测通过的表达式（后端回读确认）

### 分支条件（BOOLEAN）
```json
{
  "nodeId": "CONDITION_MMPEJO",
  "name": "ifBranch",
  "expression": {
    "title": "微流程.查询单条数据(1).查询结果 [小爪实验实体950795V2].实验数量 > ...实验数量 ",
    "schema": "{...}"
  }
}
// designData.resultTypeInfo = "BOOLEAN", tokens = 3
```

### 修改变量值（STRING）
```json
{
  "nodeId": "CHANGE_VARIABLE_PBZj6Z",
  "actionType": "CHANGE_VARIABLE",
  "selectParam": { "name": "_CREATE_VARIABLE_d3ZScR", "dataType": "STRING", ... },
  "value": {
    "type": "Expression",
    "expression": {
      "title": "{微流程.查询单条数据(1).查询结果 [小爪实验实体950795V2].实验数量 + ...实验数量}",
      "schema": "{...}"
    }
  }
}
// designData.resultTypeInfo = "STRING", tokens = 3
```

注意 `value.expression.title` 外面**包了一层花括号** `{...}`（表示这是表达式占位），
而 `node.expression.title`（分支条件）没有花括号。

## 七、操作节奏（重要）

```
1. ensure_visible(d)           ← 解决 hidden
2. ensure_editable(d)          ← 解决 readonly（每次保存后都会变回 RELEASE）
3. 开抽屉
4. 填字段
5. 点「确定」                  ← 节点级保存，走 udcMicroflowUpdatePost
6. 保存并提交                  ← 流程级保存，会重新置 RELEASE
7. 回读后端比对
```

漏掉第 2 步 → 所有编辑静默丢弃。
漏掉第 5 步 → store 不更新，保存并提交写的是旧值。
