# UDC 规则域的作用域约束（可执行版）

权威来源：设计器前端 `ty()`（`chunks/src_redux_store_ts.*.js`）

```js
ty = ({type, groupType}) => {
  let l = [];
  "ENTITY_RULE" === type && (l = "VALIDATE" === groupType ? tc
        : "ASSIGN_VALUE" === groupType ? td
        : "DEFAULT_VALUE" === groupType ? tu : n(47118));
  "FRONTEND" === type && (l = e7.A);
  ("SERVICE" === type || "CUSTOM" === type) && (l = ts);
  "FUNCTION" === type && (l = tp.A);
  return l;
}
// 模块变量：td = n(82800), tu = n(2372), tc = n(6036), ts = n(1198)
```

★ 变量名与模块号是错位的（`td` 指向 82800、`tu` 指向 2372），
  按模块号读会把 ASSIGN_VALUE / DEFAULT_VALUE 两域对调 —— 这是最容易踩的坑。

## 1. 实体规则三域 → 允许的节点集合

| 域 | group_type | 模块 | 允许节点（actionType） |
| --- | --- | --- | --- |
| VALIDATE | 1 | n(6036) | BRANCH / ATTRIBUTE_UNIQUE / ATTRIBUTE_REQUIRED / SHOW_MESSAGE / SUB_MICROFLOW |
| DEFAULT_VALUE | 3 | n(2372) | BRANCH / **DEFAULT_VALUE** / SUB_MICROFLOW |
| ASSIGN_VALUE | 2（推断，本环境无样本） | n(82800) | BRANCH / **ASSIGN_VALUE** / SUB_MICROFLOW |
| 其他/兜底 | — | n(47118) | BRANCH / ATTRIBUTE_UNIQUE / ASSIGN_VALUE / ATTRIBUTE_REQUIRED / SHOW_MESSAGE |

**★ 默认值域没有「设置值」，设置值域没有「默认值」** —— 名字反直觉，按表来。

## 2. 域 → 可选变量范围

| 域 | 开始节点（实体本体）可见 |
| --- | --- |
| VALIDATE | 可见（token `dto.dto.<字段>`） |
| DEFAULT_VALUE | **不可见**（`filterPreOutputList` 与组件 useMemo 两处 `shift()`） |
| ASSIGN_VALUE | 未验证 |

默认值规则的可选范围只有：系统变量 / 应用参数 / 函数 / 前序节点出参（子微流程）。

**★ 因此「判断实体字段 == 1」在默认值域无法表达** —— 需要改为在子微流程内部判断，
或把该判断挪到校验域。

## 3. 子微流程可调用对象

`udcMicroflowFilterNotVirtualPost`（body = id 数组）返回可调用集合。
`mfService.type` 取值：

| 被调用微流程 type | mfService.type |
| --- | --- |
| 0（服务定义） | `SERVICE` |
| 3（自定义服务） | `CUSTOM` |
| 1（前端微流程） | 不可被规则引用 |

## 4. 表达式运算符

分支条件用单等号 `=`（前端拼接 `文本 == 1` 会被判非法）。
