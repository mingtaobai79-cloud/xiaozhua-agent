# 微流程表达式：三层不一致与保存链路（LIVE 实证）

> 2026-10-28。起因：分支条件表达式报「变量在上下文中不存在」，
> 且 UI 已改好但后端数据未更新。本文记录真实机制。

## 一、三层数据模型

微流程编辑器里，同一个表达式存在于**三个互不同步的层**：

| 层 | 位置 | 谁维护 | 何时更新 |
|---|---|---|---|
| L1 | `store.flowNodes[id].expression` | 前端编辑态 | 抽屉点「确定」立即更新 |
| L2 | `store.oldFlowSchema.flowNodes[id]` | 上次加载的基线 | 加载/保存时 |
| L3 | 后端 `dataSchema` | 服务端 | **只在「暂存草稿」/「保存并提交」时** |

**关键事实：点「确定」只写 L1，不写 L3。**

实测（`CONDITION_MMPEJO`）：

```
点确定后：
  L1 store          = 实验数量 > 0
  L3 后端 dataSchema = 实验数量 > 实验数量   ← 完全没变
  flowChanged       = True                   ← 前端知道有未保存改动
```

这就是「元数据被更新了，但用的是更新前的节点」的真实机制 ——
不是元数据被覆盖，而是**两个层根本没有同步**。

## 二、三个保存按钮语义完全不同

工具栏实测有三个入口等：

| 按钮 | DOM 特征 | 语义 | 后果 |
|---|---|---|---|
| `暂存草稿` | 文本「暂存草稿」 | 只存草稿 | `state=DRAFT`、`publish=UNPUBLISH`、`readonly=false` |
| `保存并提交` | `id=microflow_save` | 保存 + 发布 | `state=RELEASE`、`readonly=true`，节点不可编辑 |
| `编辑` | 文本「编辑」 | RELEASE → DRAFT | 转回草稿态，**必须 reload 才生效** |

**正确做法：只用「暂存草稿」。**

```python
react_click(d, '暂存草稿')     # ★ 从 props.onClick 调
time.sleep(10)
```

用错 `microflow_save` 的代价：流程变正式态，`readonly=true`，
之后所有节点操作全部失败，需要「编辑」+`location.reload()` 才能恢复。

## 三、表达式对象的真实结构

`expression` **不是字符串**，是对象：

```json
{
  "title": "微流程.查询单条数据(1).查询结果 [实体].实验数量 > 0",
  "schema": "{\"designData\":{...},\"runtimeData\":{...}}"
}
```

`schema` 是 JSON 字符串，内含：

```json
{
  "designData": {
    "expressionTranslation": "微流程...实验数量 > 0",
    "resultTypeInfo": "BOOLEAN",
    "terminalType": "BACKEND",
    "context": [
      {"name": "_RETRIEVE_MSwqDF", "type": "OBJECT",
       "properties": [{"name": "_RETRIEVE_MSwqDF", "type": "OBJECT",
                       "properties": [{"name": "expNum", "type": "INTEGER"}]}]}
    ],
    "tokens": [
      {"type": "VARIABLE", "value": "_RETRIEVE_MSwqDF._RETRIEVE_MSwqDF.expNum",
       "desc": "微流程.查询单条数据(1).查询结果 [实体].实验数量"},
      {"type": "OPERATOR", "value": ">"},
      {"type": "CONSTANT", "value": "0"}
    ]
  },
  "runtimeData": {
    "executableExpr": "93gDaq3/nXB1+C8j4AjYNEVRRY...+%28+_RETRIEVE_MSwqDF...%29+"
  }
}
```

**陷阱**：`expression` 是 dict 不是 str。
用 `find_refs` 只匹配字符串字段的扫描器会**完全跳过整个表达式层**，
从而给出「全部健康」的假绿结论。必须用「含 `title` + `schema`」的特征识别。

## 四、变量失效的真因

```
错：_RETRIEVE_Ltqgzz._RETRIEVE_Ltqgzz.expNum
对：_RETRIEVE_MSwqDF._RETRIEVE_MSwqDF.expNum
```

`_RETRIEVE_Ltqgzz` 是**节点被删除重建后残留的旧输出名**。
节点重建时 `nodeId` 保留（`RETRIEVE_CRwMB9`），但 `output.name` 换新，
而表达式里写死的 token 路径不会跟着变 → 悬空引用。

判定方法：拿 `tokens[].value` 的**第一段**去比对本流程所有节点的
`output.name`。不在其中就是悬空。

## 五、恒等式检测

```python
if len(var_tokens) == 2 and var_tokens[0] == var_tokens[1]:
    # x > x 恒为 false，分支永远进不去
```

这是「配了表达式但语义无效」的典型形态 —— 校验能过、保存能过、
但运行时不报错也不进分支，最难发现。

## 六、表达式接口完全可用 —— `/check` 与 `/transform`（★ 2026-10-28 更正）

### 6.1 先更正一个错误结论

本文早期版本写过「微流程用不了表达式接口，只能走 UI」。**这是错的。**

前端从不调 `/expression/schema`，它直接：

```
1. schemas  ← 从主流程节点元数据自己拼（dataSchema 里就有）
2. tokens   ← 表达式里现成的
3. POST /service/udc/expression/check      → 校验
4. POST /service/udc/expression/transform  → 设计态转运行态
```

`/expression/schema` 对 `paramType=MICROFLOW` 确实返回 `BOOT_3000`（未注册），
但这**不影响** `/check` 和 `/transform` —— 它们只要 `schemas`，不要 `paramType`。

### 6.2 LIVE 实证（2026-10-28，test2）

```
POST /service/udc/expression/check
  → 200 {"status":0,"code":"BOOT_0000","message":"SUCCESS","data":{"content":true}}

POST /service/udc/expression/transform
  → 200 {"status":0,"code":"BOOT_0000","data":{"content":{
          "designData":{...context 树 + tokens...},
          "runtimeData":{"executableExpr":"93gDaq3/...%28+...%3E+0+%29+"}}}}
```

### 6.3 `ExpressionSaveDto` 的 `schemas` 从哪来

**直接从主流程 `dataSchema` 里该节点的 `expression.schema` 里取 `designData.context`**，
转成 `schemas` 只需两处差异：

| context 节点 | schemas 节点 |
|---|---|
| `enableDataI18n` | 保留 |
| `uniformityParams` | 保留（含 `paramId`） |
| — | **`skip: true`**（每层都要加） |
| `uniformityParams.pageNodeExtension` | schemas 里不带或为 null |

```python
SCHEMA_KEYS = ("name", "description", "type", "selectable",
               "enableDataI18n", "uniformityParams", "properties")

def context_to_schemas(context):
    def conv(node):
        out = {k: node[k] for k in SCHEMA_KEYS if k in node}
        out["skip"] = True
        if node.get("properties"):
            out["properties"] = [conv(c) for c in node["properties"]]
        return out
    return [conv(c) for c in context]
```

### 6.4 `executableExpr` 的前缀不是逐表达式签名

```
93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=+%28+_RETRIEVE_MSwqDF...%3E+0+%29+
```

实测：对该表达式调 `/transform`，返回的 `executableExpr`
**与库里已存的完全一致**（`与库中一致: True`）。

⇒ 这个前缀是服务端固定产物，不是每次不同的签名。
⇒ 因此 **`/transform` 可以离线生成正确的 `executableExpr`**，不必依赖 UI。

### 6.5 完整可用的校验流水线

```python
from components.udc.microflow.expression_audit import (
    iter_expressions, parse_expression,
)

# 1) 从 dataSchema 抽出表达式
expr = next(e for _, e in iter_expressions(branch_node))

# 2) 装配 DTO
info = parse_expression(expr)
dto = {
    "resultTypeInfo": info["resultType"],
    "schemas": context_to_schemas(info["context"]),
    "tokens": info["tokens"],
    "isMultiSelect": False,
    "terminalSupportType": info["terminalType"],
}

# 3) 页面内发（带会话 cookie，必须 await_promise=True）
check    = post(d, "/expression/check", dto)      # → content: true
transform = post(d, "/expression/transform", dto) # → designData + runtimeData
```

实现见 `scratch/check_expressions_api.py`。

### 6.6 判据升级

有了 `/check` + `/transform`，表达式校验不再需要「UI 点验证」：

| 判据 | 可信度 | 说明 |
|---|---|---|
| 静态审计（变量根/恒等式） | 中 | 能抓悬空和 x>x，但抓不到类型不匹配 |
| **`/check` = `content:true`** | **高** | 走 5 段 Filter 链，与 UI 验证同源 |
| **`/transform` = `BOOT_0000`** | **高** | 能生成运行态，说明结构完整 |
| `/transform` 产物 == 库中值 | **最高** | 证明库里的就是正确产物 |

## 七、正确的修复路径

### 7.1 API 路径（推荐 一 可批量、可复验）

```
1. 从 dataSchema 取该节点的 expression（含 context 与 tokens）
2. context_to_schemas() 装配 ExpressionSaveDto（每层加 skip:true）
3. POST /expression/check      → 必须 content:true
4. POST /expression/transform  → 必须 BOOT_0000，拿到新 executableExpr
5. 写回微流程节点（GraphQL 或 UI 暂存草稿）
6. 后端回读 + 再跑 /check 复验
```

优点：不依赖 UI、可批量、不碰「正式态 / 只读」问题。

### 7.2 UI 路径（只能单条，但能验证渲染）

```
1. 双击条件卡片打开表达式设置
2. react_click '清空'
3. 真实鼠标点变量树插入变量（click_mouse，不是 dispatchEvent）
4. click 编辑区 + cmd Input.insertText 输入常量
5. react_click '验证' → 确认「验证成功」、无红色错误
6. react_click '确定' → 只写 L1（store）
7. ★ react_click '暂存草稿' → 写 L3（后端）
8. 后端回读 dataSchema 复验
```

第 7 步不可省。少了它，UI 一切正常、store 也正确，但后端永远是旧值。

## 八、验收判据

| 判据 | 可信度 |
|---|---|
| UI 显示无红色错误 | 低（只说明前端解析通过） |
| 点「验证」返回「验证成功」 | 中（前端校验器过了） |
| `store.flowNodes[id].expression` | 中（只证明 L1） |
| **后端 `dataSchema` 回读 tokens** | **高（唯一真判据）** |

必须做最后一项。前三项全绿而后端仍旧的情况，本次已实测遇到。

## 九、证据

| 项 | 路径 |
|---|---|
| 逐字段审计脚本 | `scratch/audit_all_fields.py` |
| 三层对比诊断 | `scratch/diag_layers.py` |
| 暂存草稿保存 | `scratch/save_draft.py` |
| 后端 schema 快照 | `scratch/expr-evidence/schema.json` |
| 保存网络抓包 | `scratch/expr-evidence/draft-save.json` |

**证据等级**：三层不一致 = `LIVE`（同一次操作前后对比）；
保存语义 = `LIVE`（`暂存草稿` vs `microflow_save` 状态变化对照）；
`paramType` 注册表 = `VERIFIED_STATIC`（facts）+ `LIVE`（`BOOT_3000` 实测）。
