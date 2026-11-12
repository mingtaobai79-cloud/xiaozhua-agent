# 表达式引擎（P2）：AST 中间模型 + 传输 + 引用 + 保存链

> 全部结论来自真实平台（`/service/udc/expression/check|transform`）或 643 条发布语料。
> 代码：`components/udc/microflow/expression_model.py` / `expression_transport.py` /
> `expression_refs.py` / `save_pipeline.py`；事实：`core/facts/udc/microflow/expression-engine.md`。

## ⛔ 先读这段：远端 check/transform 对「字段引用」不可用

**含 VARIABLE token 的表达式，`/expression/check` 和 `/expression/transform` 都会失败**，
哪怕 context 和 tokens 完全正确：

```
FORMULA_6058 CVariable :微流程.查询单条数据(1).X_1 [X].字段 does not exist in context
```

判据来自实验而非推理：把**平台自己保存过的真实表达式**（语料 designData.context + tokens）
原样重发 check/transform，同样报这个错，而它的 `executableExpr` 明明是
`entityIsNotNull(_RETRIEVE_x._RETRIEVE_x.field)` —— 结构一点没错。

机制：这两个接口按 context 里的**显示路径**（`微流程.查询单条数据(1).xxx`）解析，
该路径由**设计器运行期**按完整流程树生成，离线拼不出来。

| 表达式内容 | check/transform |
|---|---|
| 纯常量/算术/函数（无 VARIABLE） | 可用 —— P2 六个「已验证」场景全属这类 |
| 含任一 VARIABLE 字段引用 | **必失败** |

后果，两条都要照做：

1. **不要**拿 check/transform 当「字段引用是否正确」的校验。字段引用的真校验只有：
   本地 `ExpressionCompiler` 静态类型检查 + **落库后 `checkSchema`**（平台按真实流程树解析）。
2. `build_remote` 遇含 VARIABLE 的表达式**跳过远端**，本地生成 designData
   （translation / resultTypeInfo / context / tokens / sourceAppName 八个键），
   `executableExpr` 填占位串，返回里带 `needs_ui_finalize=True`。

### executableExpr 平台绝不自动补

| 提交内容 | checkSchema | 回读 executableExpr |
|---|---|---|
| designData + runtimeData{executableExpr: 真值} | PASS | 原样保留 |
| designData + runtimeData{}
（缺） | **BOOT_3000 拒绝** | — |
| 只有 designData（无 runtimeData） | PROPERTY_IS_REQUIRED | — |
| designData + runtimeData{executableExpr: "PLACEHOLDER"} | **PASS** | PLACEHOLDER 原样保留 |
| designData + runtimeData{executableExpr: ""} | **PASS** | 空 |

**checkSchema 不校验 executableExpr 内容**（占位串、空串都过），但它是**运行时真正执行的代码**。
语料 1040/1040 表达式全部带它是 transform 产物。

所以含字段引用的节点生成完必须**显式标记 `needs_ui_finalize`** 并告知用户：
进设计器把该节点点一次「确定」，由平台重算 executableExpr。**没这一步，运行期表达式是空的**。
不要把它当成"全自动已完成"交付。

## 铁律：不许在构造器里拼 tokens

新代码一律走 `ExpressionCompiler`：

```python
from components.udc.microflow.expression_model import (
    Const, NodeField, Compare, Logic, Arithmetic, Func, ExpressionCompiler)
from components.udc.microflow.expression_transport import CurlBackend
from components.udc.microflow.expression_refs import ReferenceResolver

res = ReferenceResolver(app_id, app_name, live_refs=lr)
nf  = res.field_ref_from_node(ret_node, "expNum")          # 静态：前序出参
ast = Logic("AND",
            Compare("GT", nf, Const(0, "INTEGER")),
            Compare("LT", nf, Const(9, "INTEGER")))
expr = ExpressionCompiler(result_type="BOOLEAN").build_remote(ast, CurlBackend(host, ck))
# expr = {title, schema} → 构造器 value 位置直接传，_as_slot 自动包 value 槽
```

## 五个必踩的坑（都实测过）

### 1. 传输：curl，不是 urllib，也不是页面 fetch

| 通路 | 结果 |
|---|---|
| urllib POST | `SSL: UNEXPECTED_EOF_WHILE_READING`（改 UA 无效，是 TLS/ALPN 指纹） |
| 页面 fetch + CDP awaitPromise | 前台 tab 可以；**后台 tab 节流 → 挂死 300s** |
| curl（HTTP/2） | 稳 |

`deploy._req` 与 `LiveRefs._gql` 都已改走 curl（urllib 只在没有 curl 时回退）。

### 2. context 字段层 type = dataType，不是 DTO

自拼 context 把字段 `type` 写成 `DTO` → `FORMULA_6033 Unsupported data type: DTO`。
**不要自己拼层级**：`ExpressionCompiler.register_node_output()` 复用
`expression_build.node_context_entry`（真实活体样本照抄的唯一实现）。

### 3. FUNCTION token 用 subOps，不是平铺

```json
{"type":"FUNCTION","value":"len","desc":"...","subOps":[[{VARIABLE...}]]}
```

平铺进顶层 tokens → `BOOT_3000`（无 message，最难定位的一种）。
函数名必须命中 88 目录（`len` ✓ / `stringLength` ✗）。

### 4. 嵌套必须显式括号（语义静默漂移）

平台只做 token 平铺翻译，不还原 AST：

```
AST  Logic("AND", A, Logic("OR", B, C))
无括号 → "A && B || C"      = (A&&B)||C   ← 错，而且 check 是绿的
带括号 → "A && ( B || C )"  ← 对
```

规则：复合子项 op 不同 → 括号；op 相同但不满足结合律（SUB/DIV）且非首项 → 括号。

### 5. 值槽包装三层

```json
{"type":"Expression","simple":null,"desc":"...",
 "expression":{"title":"...","schema":"<JSON字符串>"}}
```

直接塞 `{title, schema}` → `value.type PROPERTY_IS_REQUIRED` + `DATA_INVALID`。
用 `to_value_slot(expr)`；构造器入口已用 `_as_slot()` 自动归一。

## 引用解析：两条路严格分开

- **静态**：前序节点出参 → `index_before(nodes, current_node_id)` 裁决顺序 → 本地推导字段元数据（零接口）。
  ★ 引用**后序**节点平台 check 会过、运行期取不到值 —— 必须在解析期拦。
- **动态**：LiveRefs 查询，缓存 key 含 `app_id`（跨应用同名实体 id 不同，串了生成指向错误 DTO 的表达式且 check 仍绿）。
- BASIC 变量（`paramType=BASIC`）字段就是自身 `dataType`，**不要**按 structure 查实体。

## 保存链（顺序不可颠倒）

```
save(create → deploy.publish) → readback(DP.get → dataSchema) →
  expression_verify(仅常量表达式；含 VARIABLE 跳过) → l2_check → 异常才 L3
```

`components/udc/microflow/save_pipeline.py::run_pipeline(...)`，状态机
`CONSTRUCTED → SCHEMA_VERIFIED → UI_VERIFIED`。

- **save 只能走 `deploy.publish`**（唯一实现）。自拼 update body 少一个键就是
  `BOOT_1001 Parameter Error` 且不给明细，二分半天发现是 body 而非 schema。
- **只认回读**：平台保存会归一（casing/默认值），本地 delta ≠ 库里对象。
- **expression_verify 只校验无 VARIABLE 的表达式**；含字段引用的交给 checkSchema。
- **roundtrip**：库里 `executableExpr` 与本次 transform 不一致 = 表达式已变质。
  例外：库里是占位串（`__NEEDS_UI_FINALIZE__`）时不算变质，那是等设计器重算的正常状态。
- 表达式校验只扫**节点自身**（`iter_expressions` 会递归子节点，外层再 walk 会重复计数）。
- L2 正确入口：`/main/child-frame/udc/app-design/rule?appId=<app>&id=<mid>`；
  开 `.../rule/microflow/editor/<mid>` 必落 `chrome-error://chromewebdata/`。

## 能力矩阵与回归

- 槽位矩阵：`core/facts/udc/microflow/expression-capability-matrix.json`（38 槽位）
  重扫：`python tools/core/expression/scan_capability_matrix.py`（宿主=最内层节点，路径相对宿主）
- 单测：`tests/test_expression_model.py`（形态+语义）、`tests/test_expression_refs.py`（引用）、
  `tests/test_save_pipeline.py`（链路）、`tests/test_expression_injection.py`（17 类错误注入）

## 数据形态补充（构造器陷阱）

- `create_variable` BASIC 的 `structure` 必须 `None`（语料 429/429；模板残留 `PageInfo` 会让引用解析走错实体）。
- `branch()` 接受 `{expression, nodes}`；旧实现把整个 dict 当表达式 → `PROPERTY_IS_REQUIRED`。
- 变量名（`title`）是引用标识，中文显示名只能放 `caption`；改 title 会让你自己的引用解析对不上。
