# 表达式（必须走 transform）

## P2 主线：统一中间模型（新代码一律走 AST，不再各自拼 tokens）

**构造器/业务图禁止再直接手拼 tokens/context JSON**。统一入口是 `components/udc/microflow/expression_model.py`：

- AST 八类：`Const / NodeField / SysVar / Compare / Logic / Arithmetic / Func / Cond`，每个节点带 `dtype`（期望结果类型）。
- `check_types(ast)` 静态类型检查（Logic 子项须 BOOLEAN、比较两侧同族、算术须数值），构造期拦截，不花请求。
- `ExpressionCompiler(result_type).compile(ast)` → tokens（VARIABLE 三级、运算符、FUNCTION、常量全按真实样本形态）+ `register_node_output(ref)` 累积 context 三级树。产出喂 `expression_api` 远端链（check → transform），与下方手写 token 的形态约束完全一致。
- 兼容层不删：`expression_build.py`（context 树/token 原语）、`expression_fill.py`（值槽三态+变量池）、`expression_audit.py`（反向审计）继续工作，新代码优先走 AST。

**表达式能力矩阵**（哪些槽位能放什么、期望什么类型）：`core/facts/udc/microflow/expression-capability-matrix.json`，扫描器 `tools/core/expression/scan_capability_matrix.py`（重跑即可从 pmp_schemas 语料再生成）。裁决摘要：33 个值槽 Simple/SelectParam 两态为主（Expression 发布语料仅 END_NODE.value 1 条）；条件右值三态 CONSTANT/CONTEXT_VARIABLE/EXPRESSION；FOR.forStart 恒 Simple；路径归一规则=槽位归属最内层宿主节点、路径相对宿主重算。

## 批量生成时：表达式走 HTTP 直连，不要用 Driver.attach
`Driver.attach()` 在批量跑时可能**永不返回**（实测卡死在第二条流程，日志停在同一行）。
正确做法是只替换底层 `_post`，`check/transform` 的封装（designData / executableExpr 抽取）保持不动：

```python
import components.udc.microflow.expression_api as EA
def _http_expr_post(path, body):
    q = urllib.request.Request(HOST + EA.EXPRESSION_PREFIX + path,
        data=json.dumps(body, ensure_ascii=False).encode(), method="POST",
        headers={"Content-Type": "application/json;charset=UTF-8", "Cookie": ck})
    return {"status": 200, "json": json.loads(urllib.request.urlopen(q, timeout=60).read().decode())}
EA._post = lambda d, path, body: _http_expr_post(path, body)   # d 可以传 None
```

**不要**把 `check_expression_remote / transform_expression_remote` 整个替换成 `_verdict(...)`：
那会把 `data.content.designData` 与 `runtimeData.executableExpr` 的抽取丢掉，
`make_expression` 报「transform 未返回 executableExpr」。

> 由 SKILL.md 拆分而来，按需读取。

## ★ 表达式生成：expression_build.py（绝不手写 executableExpr）

BRANCH 条件等表达式必须走服务端：`expression_build.make_expression()` 内部真调
`/expression/check` + `/expression/transform`，返回的 `{title, schema}` 可直接落库。

- context 树：`node_context_entry(node, entity_model)` 从节点出参造三级变量树
- VARIABLE token value 是**三级**：`_<节点>._<节点>.<字段>`
- 常用构造：`field_equals(node, field, True)` / `text_contains(node, field, "mysql")`
- ★ `/expression/*` 是普通 REST，**可以带 cookie 直连，不必走浏览器**（推荐）：
  ```python
  import components.udc.microflow.expression_api as EA
  EA._post = lambda d, path, body: _http_expr_post(path, body)   # POST {HOST}/service/udc/expression{path}
  EB.make_expression(None, toks, ctx, "BOOLEAN")                  # d 传 None 即可
  ```
  - **只替换 `EA._post`**。把 `check_expression_remote` / `transform_expression_remote` 整个换掉会丢掉
    `designData` / `executableExpr` 的抽取（它们在 `transform_expression_remote` 里从 `data.content` 取），
    报错长相是「transform 未返回 executableExpr」，看着像服务端没返回，其实是自己的包装被覆盖了。
  - 直连不需要 Driver，批量生成多条流程时不会因为 `Driver.attach()` 卡死而挂住整个脚本。
  - 用浏览器 Driver 也能做，但 `Driver.attach()` 在没有可 attach 的编辑器 tab 时会阻塞不返回；
    真要走向量少的单次调用，先确认目标 tab 存在再 attach。
- BASIC 变量的 context 是标量形态（properties 直挂 type=STRING），与 DTO 的三级树不同

## 表达式必须走 transform 接口（禁止手写 executableExpr）

`executableExpr` 的 base64 前缀（`93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=`）是**服务端产物，客户端不可造，只能整份照抄**。手写表达式（如分支放 `true`、修改变量放常量）会导致前端表达式编辑器里看不到真实表达式、被用户判定「糊 check」。

正确链路（REST，5 端点）：
- `GET /service/udc/expression/operator/list` —— 运算符清单（POST 会 405）
- `POST /service/udc/expression/preset/list` body `{terminalSupportType:"BACKEND"}` —— 返回 `presetVariableInfo`（系统变量）+ `functionInfo`（函数树，88 个函数/8 大类）
- `POST /service/udc/expression/schema` —— 取可选范围（应用参数 paramType=CONFIG_PARAM / 实体字段 paramType=ENTITY + ids=[实体id]，带 appId 报 BOOT_3000）
- `POST /service/udc/expression/check` —— 校验（**读 data.content===true**）
- `POST /service/udc/expression/transform` —— 产出 `{designData, runtimeData}`，两列都必须落库

**tokens 必须按书写顺序排：`[左值, 算子, 右值]`。** 把 `OPERATOR` 放到数组第一位（`[==, 1, 1]`）时后端 `/check`、`/transform` 全绿、`executableExpr` 也生成得出来，但前端表达式面板渲染成 **`1 1`** 并红字报「变量: 1 后只能拼接操作符」——用户一眼看出「你会用表达式吗」。判据：回读 `designData.tokens` 的 type 序列，`OPERATOR` 不能出现在首尾。同理**手拼 `EXPR_PREFIX + 表达式串` 也不行**：前缀照抄对了但后缀拼接是错的，`executableExpr` 必须整份由 `/transform` 产出。条件表达式要有业务语义（`序号 <= 2`），不要放 `1 == 1` 这类恒真占位。

函数 token 形状（5 个 type：CONSTANT/VARIABLE/SYSTEM/FUNCTION/OPERATOR）：`FUNCTION` 带 `subOps`（二维数组，外层=参数位置）。布尔字面量用 `OPERATOR`（value="true"），用 CONSTANT "true" 报 FORMULA_6901。`resultTypeInfo` 必须等于目标字段 dataType（否则 FORMULA_6901）。

**表达式 tokens 数与 translation 必须对齐（G1 闸门，否则 `ArrayList.rangeCheck`/04000），但不要自己推段数公式。**
`tokens` 是**中序平铺**的，括号 `(` `)` 各占一个 OPERATOR token，中文「包含」是 FUNCTION 不是中缀，`&`/`|` 是单字符。
按运算符数推段数的老公式（`2*运算符数+1`、或「含括号就 return 1」）在真实生产语料上误报率 40%+，已废。
正确算法与三条结构判据见下文「G1 段数判据的正确算法」——**直接用 `components/udc/microflow/gates.py` 的 `run_gates`，不要另写一份**。

**FUNCTION 表达式的 designData 里存的是 `context`（参数变量的变量树），不是 `schemas`**——`schemas` 是 `/check`/`/transform` 的 dto 字段，由 `build_save_dto` 里的 `context_to_schemas()` 从 context 裁剪（每层加 `skip:true`）。实测 `roundOffFloor(变量/999)` 的 designData：`resultTypeInfo=INTEGER`、`context=[参数变量三级树]`、`tokens=[FUNCTION token]`、`subOps=[[VARIABLE,OPERATOR,CONSTANT]]`。闸门层（validate/gates）不查 schemas、构造时可 None；提交层 `/transform` 必须传参数变量的 context 裁剪结果，否则参数变量解析失败。

**函数签名清单已落成可复用资产 `components/udc/microflow/function_catalog.json`（88 个函数：name/desc/paramCount/argDescs），配套构造器在 `components/udc/microflow/expression_fill.py`：`build_function_token(func_name, arg_token_groups)` + `build_function_expression_dto(func_name, arg_token_groups, want, result_type_full_name=None)`**。函数名不在 88 个里报 KeyError；参数类型/返回类型动工前先 `preset/list` 抄 argTypes，别按中文描述猜。

**常用函数（argTypes 实测）**：`textToDecimal(文本)→小数`、`textToInt(文本)→整数`、`textToLong(文本)→长整数`、`substring(文本,整数,整数)→文本`（第2参=起始位，第3参=截取长度）、`substringByIndex(文本,整数,整数)`（起止下标）、`round/roundOff/roundOffFloor/roundOffCeiling`、`join(集合,文本)`。**动工前先 `preset/list` 抄 argTypes 再组 token**，别按描述猜（join 不是文本、textToLong 只吃文本）。

**前端 UI 手工写表达式（在页面表达式面板里点选，不走 REST）**：面板 DOM、变量树/函数树操作、点两次才插入、参数占位符填法、函数中文名清单，见 `references/expression-editor-ui.md`。要证明表达式真通了，最终必须回读节点的 `expression.schema`，确认 `designData.resultTypeInfo` 等于目标类型且 `runtimeData.executableExpr` 是服务端产物。

### 表达式引用前序节点字段（schemas 必须传节点出参变量树，否则 FORMULA_6058）

表达式里要引用**前序节点的字段**（如 `textToDecimal(查询单条.expText)+5`）时，`check`/`transform` 的 `schemas` 参数**不能传空数组、也不能传裸实体字段**，必须传「该前序节点的出参变量树」——否则报 `FORMULA_6058 CVariable :xxx does not exist in context`。

schemas 元素是**三级嵌套 context**（照活体 `expression.sample.json` 的 `designData.context`）：
```
{ name: <节点出参名>, description: <节点标题>, type:"OBJECT", selectable:false,
  properties: [ { name:<同节点出参名>, type:"OBJECT", selectable:true,
    properties: [ 每个字段 {name, description, type, uniformityParams:{paramId,paramCategory,extensionProperties}} ],
    uniformityParams: {paramId:<DTO fullName>, paramCategory:"OBJECT", extensionProperties:{"id":<DTO>}} } ],
  uniformityParams: {paramId:<DTO fullName>, paramCategory:"DTO", extensionProperties:{"id":<DTO>,"javaType":<DTO>}} }
```

对应的 VARIABLE token 的 `value` 是**三级**：`<节点出参名>.<节点出参名>.<字段名>`（如 `_RETRIEVE_xxx._RETRIEVE_xxx.expText`，不是 `_RETRIEVE_xxx.expText`）。字段的 `uniformityParams.paramId` = `DTO fullName.字段名`，`paramCategory` = 字段 dataType，`extensionProperties` = JSON 字符串 `{"id":"DTO.字段","relationType":"NONE","javaType":"java类型"}`。

### LIST_OPERATION SIZE 无出参（计数结果不能做后续引用源）

`LIST_OPERATION` 的 `operationType:SIZE` **output 恒为 null**（平台设计，SIZE 计数不产生独立出参变量）。所以「列表计数」的结果**不能**作为后续节点（如 FOR 循环终止值）的引用源。循环终止值要引用别的有出参的前序节点（如实体变量的 INTEGER 字段，或专门建一个 INTEGER BASIC 变量）。FOR 的 forEnd 用 `{type:"Expression", expression:<走 transform 生成>}` 引用，VARIABLE value 三级 `_节点._节点.字段`。

### FOR_EACH（列表循环）：模板已补，契约双证

仓库模板目录 `fixtures/microflow/node_templates/` 下 `FOR_EACH` 和 `END` 两个模板现已存在（FOR_EACH 取自一条 LIVE 发布流程、END 取自生产母版 `backup/xzhAllNodesV16`），`load_templates()` 共 26 个。结构与前端 `src_redux_store_ts` bundle 一致：

```js
{nodeId:"ForEach_"+nanoid(6), type:"FOR_EACH", caption:"列表循环",
 description:"", runAfter:null, nodes:[], foreach:{sourceItemes:[]}, isCompleted:false}
```

必填两项：`selectParam`（选择列表，`type:"ARRAY"` **且带 `dtoType:"MASTER_ENTITY"`**）+ `targetName`（循环对象名称）。`foreach` 必须是 `{sourceItemes:[]}` 而不是 `null`。

**FOR 与 FOR_EACH 同构但不通用**：两者都有 `nodes` 子链；FOR 有 `forStart/forEnd/forStep/operator` + `foreach:null`，FOR_EACH 反过来要 `foreach` 对象、**没有**那四个计数循环字段。用 FOR 模板打底时必须 `pop` 掉它们，再把 `type`/`actionType` 改成 `FOR_EACH`、`nodeId` 前缀改成 `ForEach_`。漏 `selectParam.dtoType` 报 `PROPERTY_IS_REQUIRED [列表循环]:必填参数未配置`。

**画布显示文本是「循环列表：<targetName>」**（FOR 是「计数循环：<targetName>」），DOM 容器 class 含 `branches loop`。**按「列表循环」去 DOM 里找会一个都命中不到**，误判成没渲染。

**只会计数循环 = 覆盖不全。** 一条流程里两种循环都要出现：计数循环遍历序号，列表循环遍历查询结果（`RETRIEVE_ARRAY` 产出的实体列表），循环体里放真实取值节点（如 `CHANGE_VARIABLE` 引用当前实体的字段），不要留空 `nodes:[]`。

