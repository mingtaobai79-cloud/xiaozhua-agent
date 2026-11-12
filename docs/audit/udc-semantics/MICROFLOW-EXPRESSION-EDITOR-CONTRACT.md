# 微流程表达式编辑器（真实操作契约）

## 结论：`executableExpr` 前缀固定，不可手写

```
executableExpr = "93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ="
               + "+%28+" + <URL编码后的表达式翻译> + "+%29+"
```

服务端固定产物 + `( 表达式 )` 的 URL 编码拼装。**手拼必错**，只能走
`POST /service/udc/expression/transform`（由页面「确定」自动调用）。

## 表达式设置面板结构

点开方式：分支节点 → ifBranch 卡片上的「条件设置」；或各节点字段旁的表达式按钮。

```
.ant-modal  标题=表达式设置  宽 1000
├── 顶部按钮：全量复制 / 部分复制 / 粘贴 / 清空 / 验证
├── 运算符区（y=354 一带，一字排开）
│     + - × ÷ mod = != > < >= <= and or not true false ( )
│     为空 不为空 包含(全部) 属于 可选范围
├── .optionalScope   左：变量树（antd Tree）
├── .funcScope       中：函数树（antd Tree）
├── .explainScope    右：函数说明
├── [data-elm=editor-wrapper]  编辑区（contenteditable 自研编辑器）
│     └── [data-elm=cursor] 游标
│     └── [data-elm=token-wrapper] 已插入的 token
└── 底部：.verifyMessage / 取消 / 确定
```

## 变量树结构

`.optionalScope .ant-tree-list-holder-inner` 的直接子元素就是行：

```
系统变量（open）
  组织机构 / 日期 / 环境变量（closed）
插件 / 应用参数（open）
  附件文本 / 接口基地址文本 / 分页大小整数
微流程（open）
  入参对象(长整数) [入参对象(长整数)]
  变量_1文本
  查询结果 [小爪实验实体950795V2]（closed）
```

展开「查询结果」后**不回显子行**（antd 虚拟列表 + 懒渲染）。
用 **搜索框** 过滤字段最可靠：

```js
const inp = modal.querySelector('.optionalScope input[placeholder="请输入搜索关键词"]');
const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
setter.call(inp, '实验数量');
inp.dispatchEvent(new Event('input', {bubbles:true}));
```

搜索后树里直接出现目标字段行（含父级路径行）。

## 关键坑：插入变量必须点两次

| 次数 | 效果 |
|---|---|
| 第 1 次点击 | 只是选中树节点，**不插入** |
| 第 2 次点击 | 真正插入到编辑器 |

必须先点编辑器区（约 `x=395, y=285`）让编辑器拿到焦点，否则两次点击都可能空转。

## 运算符顺序严格

`变量 [运算符] 变量`。先点 `+` 再点变量 → 变成 `+变量`，验证报
`操作符:+ , 输入错误!`。

正确顺序：**编辑器聚焦 → 插变量 → 点运算符 → 再插变量**。

## 数字字面量不要用键盘

`Input.insertText` 插入的数字落到游标位置不可控（会跑到表达式最前面）。
两种替代：
1. 全部用变量（`变量 > 变量`），不掺字面量
2. 插完最后一个 token 后，先点编辑器末尾游标再 insertText

## 验证返回

| 消息 | 含义 |
|---|---|
| `验证成功` | 语法合法 + 类型匹配 |
| `操作符:X , 输入错误!` | 运算符位置错了（通常缺左操作数） |
| `变量: X 后只能拼接操作符` | 变量后面跟了不合法的东西 |
| `计算结果为: 整数 类型, 无法赋值给: 布尔 类型` | 语法对，但目标类型不匹配 |

最后一类说明**表达式本身合法**，只是挂错了地方。

## 分支节点真实结构（确认后）

```json
BRANCH_uCjtD5 = {
  "nodeId": "BRANCH_uCjtD5",
  "name": "userBranch",
  "type": "BRANCH",
  "caption": "分支(1)",
  "description": "",
  "runAfter": null
}

CONDITION_CXlLY5 = {
  "nodeId": "CONDITION_CXlLY5",
  "name": "ifBranch",                      // 默认分支是 elseBranch
  "type": "CONDITION",
  "caption": "符合条件即进入该分支",
  "description": "<表达式明文>",
  "runAfter": null,
  "expression": {
    "title": "<表达式明文>",
    "schema": "<JSON 字符串（二次编码）>"
  },
  "isCompleted": true
}
```

`expression.schema` 解一次 JSON 得到：

```json
{
  "designData": {
    "expressionTranslation": "微流程.查询单条数据(1).查询结果 [小爪实验实体950795V2].实验数量 > ...",
    "resultTypeInfo": "BOOLEAN",
    "resultTypeFullName": null,
    "terminalType": "BACKEND",
    "isMultiSelect": false,
    "context": [ { "name":"_RETRIEVE_Ltqgzz", "type":"OBJECT", "properties":[...] } ],
    "tokens": [
      {"uid":"...","type":"VARIABLE","value":"_RETRIEVE_Ltqgzz._RETRIEVE_Ltqgzz.expNum","desc":"微流程....实验数量"},
      {"uid":"...","type":"OPERATOR","value":">","desc":">"},
      {"uid":"...","type":"VARIABLE","value":"_RETRIEVE_Ltqgzz._RETRIEVE_Ltqgzz.expNum","desc":"..."}
    ],
    "sourceAppName": null
  },
  "runtimeData": {
    "executableExpr": "93gDaq3/...+%28+<expr>+%29+"
  }
}
```

要点：
- `context` 是**前序节点出参的三级变量树**，由页面向 `POST /expression/schema` 要
- `tokens` 里 VARIABLE 的 `value` 形如 `_RETRIEVE_x._RETRIEVE_x.字段`（节点id 出现两次）
- `resultTypeInfo` 必须等于目标位置的期望类型（分支=BOOLEAN）
- `uniformityParams.paramId` = `com.seeyon.<app>.dto.<Dto>.<field>`

## 分支节点的画布内联结构

分支没有配置抽屉，DOM 是：

```
.udc-microflow-editor-node-container.branch-main     分支主卡片
.udc-microflow-editor-node-container                 条件卡片（含「条件设置」按钮）
.udc-microflow-editor-node-container                 默认分支卡片
```

`flowFrame` 里：

```json
{"nodeId":"BRANCH_uCjtD5","nodeType":"BRANCH","children":[
  {"nodeId":"CONDITION_CXlLY5","nodeType":"CONDITION","children":[]},
  {"nodeId":"CONDITION_LAZ7O6","nodeType":"CONDITION","children":[]}
]}
```

## 接口

| 端点 | 用途 |
|---|---|
| `POST /service/udc/expression/check` | 点「验证」，读 `data.content === true` |
| `POST /service/udc/expression/transform` | 点「确定」，产出 designData + runtimeData |
| `POST /service/udc/expression/schema` | 请求 context 变量树 |
| `POST /service/udc/expression/preset/list` | body `{terminalSupportType:"BACKEND"}` |
| `GET /service/udc/expression/operator/list` | 运算符清单（POST 405） |
