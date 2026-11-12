# 存量草稿微流程的节点体检

用户说「这条流程是草稿，你看看节点是不是都有问题」时的做法。

与「生成节点」不同：这里不新建、不改写，只**读回 dataSchema 逐节点判定**，产出「哪些节点有问题、问题属于哪一层」。

## 0. 三层分级，不要笼统报「有问题」

| 层 | 判据 | 后果 |
|---|---|---|
| **BLOCKING** | 前端 truthy 判空为真（`null` / `''` / `[]` / `{}`），或 `isCompleted=false` | 点「保存并提交」被拦，零请求 |
| **QUALITY** | 值非空但只有空白字符（`'\n'`、`'  '`） | 保存放行，运行时弹空白提示框 / 写入空白数据 |
| **RUNTIME** | 必填都填了、能保存，但语义上跑不通（入参映射空、引用指向空壳） | 保存 200，执行时才炸或拿 null |
| **EXPR** | 表达式 `tokens` 引用的变量根不在本流程输出里，或左右同源恒等式 | 保存 200、画布卡片正常显示，运行时分支永远走不进去 |

**分级必须实测确认，不能推断。** 标成 BLOCKING 之前先真点一次保存：

```python
d.eval("(()=>{window.__clog=[];return 1})()")
ui.click_react(d, "document.getElementById('microflow_save')")
time.sleep(10)
# 判据：有 udcMicroflowCheckSchemaUpdatePost 200 且 console 无 firstErrorNode → 保存通过
```

`console.log("firstErrorNode", e)` 出现才是真拦截。凭「字段看起来空」就断言「保存会失败」，会在用户面前被一次点击拆穿。

## 1. 前端用 truthy 判空，不是 trim

这是 QUALITY 层存在的根因：

```python
def truthy_empty(v):      # 前端口径
    if v is None: return True
    if isinstance(v, str): return v == ''      # 注意：不 strip
    if isinstance(v, (list, dict)): return len(v) == 0
    return False

def blank_only(v):        # 只有空白 → 前端放行，运行时是空白框
    return isinstance(v, str) and v != '' and v.strip() == ''
```

`nullPromptMessage: "\n\n\n\n\n\n"` 能通过保存校验，因为 `'\n'` 是 truthy。用户看到的是「流程终止了但提示框一片空白」。用 `strip()` 判空会把它误报成 BLOCKING。

## 2. 必守的防误报 / 防漏检规则

存量流程里误报一次，用户就会怀疑整份报告；**漏检一次，整份报告都是废的**。下面每条都是实测踩出来的。

### 2.1 控制节点的位置必须带父链判断

`BREAK` 只有在 `FOR_EACH` / `FOR` 循环体内才合法。遍历时只记直接父节点会漏掉深层嵌套，判成「根级 BREAK」误报。

```python
def walk(nodes, chain=None, out=None):
    """chain = 祖先 actionType 列表（不是单个父节点）"""
    if out is None: out = []
    chain = chain or []
    for n in nodes or []:
        out.append((n, list(chain)))
        a = n.get('actionType') or n.get('type')
        walk(n.get('nodes'), chain + [a], out)
        for c in n.get('conditions') or []:
            walk(c.get('nodes'), chain + [a], out)   # 分支子节点同样继承
    return out
```

### 2.2 条件必填必须按实际配置判定，不能按并集

`SAVE_REQUIRED_FIELDS` 是**并集**，直接拿它当无条件必填会大批误报：

```python
def cond_triggered(action, field, n):
    if action == 'RETRIEVE' and field == 'nullPromptMessage':
        return n.get('nullHandling') == 'TERMINATION'
    if action == 'MAP_OPERATION':
        if field == 'nullPromptMessage': return n.get('nullHandling') == 'TERMINATION'
        if field == 'theKey':            return n.get('operationType') == 'GET'
        if field == 'basic':             return n.get('paramType') == 'BASIC'
    if action == 'CREATE_VARIABLE' and field == 'otherType':
        return n.get('paramType') == 'OTHER'
    if action == 'CUSTOM_ERROR' and field in ('attrError','attrType','selectParam','sourceData'):
        return n.get('errorType') == 'POSITION'
    return False

# 用法：条件字段单独判，恒需字段 = 清单减去条件字段
cond = SAVE_CONDITIONAL_FIELDS.get(a, {})
hard = [f for f in SAVE_REQUIRED_FIELDS.get(a, ()) if f not in cond]
```

典型误报：`CREATE_VARIABLE` 的 `paramType=BASIC` 时要求 `otherType`、`RETRIEVE` 的 `nullHandling=CONTINUE` 时要求 `nullPromptMessage`。

### 2.3 子微流程的 `mfService` 整棵子树不是出参引用

扫悬空引用时，`SUB_MICROFLOW.mfService.input.name` / `.output.name` 里也有 `_FLOW_INPUT_xxx` / `_FLOW_OUTPUT_xxx`，长得和本流程出参一模一样，但它们是**被调子流程自己声明的形参名**，不是对本流程出参的引用。整棵 `mfService` 跳过：

```python
def find_refs(obj, acc=None, depth=0, skip_keys=('mfService',)):
    if acc is None: acc = []
    if depth > 12: return acc
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in skip_keys:
                continue
            if k in ('outputName', 'name') and isinstance(v, str) and v.startswith('_'):
                # 只收有 nodeInfo 指向某节点的真引用
                if isinstance(obj.get('nodeInfo'), dict) or obj.get('position') == 'parent':
                    acc.append(v)
                continue
            find_refs(v, acc, depth + 1, skip_keys)
    elif isinstance(obj, list):
        for x in obj:
            find_refs(x, acc, depth + 1, skip_keys)
    return acc
```

对照判据：本流程顶层 `input.name`（如 `_FLOW_INPUT_x1W2U3`）才是当前流程的入参名；子流程那几个只出现在 `mfService` 里。

### 2.4 表达式层必须单独扫，靠字段名匹配会整层跳过

**`expression` 不是字符串，是 `{title, schema}` 对象**，而 `schema` 又是一个 JSON 字符串，里面才是 `designData`（`context` 变量树 + `tokens` 真实引用 + `expressionTranslation`）和 `runtimeData.executableExpr`。

按 `outputName` / `name` 这类**字段名**去找引用的 `find_refs` 对它是完全空转——一条都扫不到，于是体检报「全部健康」。这是最危险的漏检形态：报告看起来干净，用户一打开表达式面板就看到红字。

判据要用**结构特征**，不要用字段名：

```python
def is_expr_obj(obj):
    """表达式结构判定：dict 且 schema 里含 designData / expressionTranslation"""
    if not isinstance(obj, dict) or 'schema' not in obj:
        return False
    s = obj.get('schema')
    if isinstance(s, str):
        return 'designData' in s or 'expressionTranslation' in s
    if isinstance(s, dict):
        return 'designData' in s or 'expressionTranslation' in s
    return False

def find_exprs(obj, path='', out=None, depth=0):
    if out is None: out = []
    if depth > 16: return out
    if isinstance(obj, dict):
        if is_expr_obj(obj):
            out.append((path, obj)); return out      # 命中后不再下钻
        for k, v in obj.items():
            find_exprs(v, '%s.%s' % (path, k) if path else k, out, depth + 1)
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            find_exprs(x, '%s[%d]' % (path, i), out, depth + 1)
    return out
```

已知落点：`BRANCH.conditions[].expression`、`CONDITION.expression`、`FOR.forEnd`、`CUSTOM_ERROR.error`、各类节点的 `value`。用结构特征扫可以一次覆盖，不用逐个背字段名。

**BRANCH 和它的 CONDITION 是同一个表达式对象，遍历时会被数两次。** 汇报时按 `nodeId` 去重，否则「1 个缺陷」会被报成「6 条问题」。

#### 两类必查缺陷

```python
for ep, ev in find_exprs(n, ''):
    sch = ev.get('schema')
    if isinstance(sch, str):
        try: sch = json.loads(sch)
        except Exception: sch = {}
    tokens = ((sch or {}).get('designData') or {}).get('tokens') or []
    vars_used = [t.get('value') for t in tokens if t.get('type') == 'VARIABLE']

    # ① 变量根失效：tokens 里的根名必须是本流程某个节点的 output.name
    for v in vars_used:
        root = (v or '').split('.')[0]
        if root not in outputs:
            report('EXPR', '%s 引用不存在的变量 %r' % (ep, root))

    # ② 恒等式：左右同一变量 → 表达式恒 false，分支永远进不去
    if len(vars_used) == 2 and vars_used[0] == vars_used[1]:
        report('EXPR', '%s 左右同一变量，恒等式（x op x）' % ep)
```

① 的典型成因是**节点重建后出参名变了**（如 `_RETRIEVE_Ltqgzz` → `_RETRIEVE_MSwqDF`），`selectParam` 那批可能已同步，但 `expression.tokens` 里的旧名没人管。快速定位：把整个 `dataSchema` 序列化成字符串，数字符串里各候选出参名的出现次数——失效名往往还在多处残留，而当前名只出现在节点自己身上。

② 在 UI 上完全看不出来：卡片正常显示「实验数量 > 实验数量」，保存也不拦，但运行时分支持久为假。

#### 表达式缺陷的修法：走 REST transform，不要跟变量树 UI 较劲

表达式面板里的变量树是懒加载的。当某个节点同时带 `ant-tree-treenode-leaf-last`（被判成叶子）和 `ant-tree-switcher_close`（却显示展开箭头）时，前端状态自相矛盾：真实鼠标点箭头、`dispatchEvent(MouseEvent)`、键盘 `ArrowRight` 全部无法展开，子字段点不到。

**判据：连续两种展开手法都失败就立刻停止**，改走 `references/expression-4-types-landed.md` + SKILL.md「表达式必须走 transform 接口」的 REST 链路（`/expression/preset/list` → `/expression/schema` → `/expression/check` → `/expression/transform`）。手写 `executableExpr` 不行，但走 transform 生成是正规路径。

清空（点「清空」）后红字会立刻消失——**别把这个当成修好了**，那是把表达式清空了，不是改对了。判据唯一定义为：后端回读 `expression.schema` 里 `tokens` 的变量根全部命中本流程输出。

## 3. 真实缺陷模式（保存能过、运行会坏）

### 3.1 子微流程入参映射空

```
SUB_MICROFLOW: mfService.hasInput=true
               mappingType="attrs"
               attrs=[]              ← 一条映射都没配
```

保存校验不查 `attrs` 内容（`SAVE_REQUIRED_FIELDS['SUB_MICROFLOW']` 只要 `mappingType/mfService/outputName`），所以 200 通过。运行时子流程拿到全 null 的入参 DTO。

判据：`mfService.hasInput and mappingType == 'attrs' and not attrs`。

**修复手法（UI 路径，实测落库）**：`SUB_MICROFLOW` 抽屉里「参数映射」区初始只有「添加字段」按钮，没有任何行。每点一次「添加字段」追加一个 `.form-list-item`，行内是 `[字段选择器 .ant-select] + [值 input]` 两个子项。

- 行容器类是 **`.form-list-item`**，不是 `setting-config-item-container`（后者是别的节点用的）。用错类名会一路返回 `no row`，误判成「加不上行」。
- 字段下拉的选项文本是 `caption [dataType]`（如 `天数 [整数]`），按 caption 匹配，不按字段名。
- 值输入：整数型是 `input.ant-input-number-input`，文本型是 `input.ant-input`。两种都要试，只匹配一种会得到 `no inp`。
- 每次改完必须 `react_click(d, '确定', root=DRAWER)`（见 `references/frontend-node-authoring-cdp.md` 的 el.click 静默失败节），然后读 store 的 `attrs.length` 确认。

落库后的 `attrs` 元素结构（照抄形态，不要自己拼）：

```json
{"value": {"type": "Simple", "simple": 0, "desc": 0},
 "attrType": {"name": "days",
   "id": "<DtoFullName>.days", "fullName": "<DtoFullName>.days",
   "javaType": "java.lang.Integer", "dataType": "INTEGER", "type": "OBJECT",
   "desc": "天数", "relationApp": "<app>", "refApp": "<app>",
   "multiSelect": false, "filterDataType": "INTEGER", "filterType": "OBJECT",
   "filterFullName": "<DtoFullName>.days", "dataI18n": false, "sort": 0}}
```

要点：`value.type` 恒为 `"Simple"`（常量赋值），`value.simple` 的类型跟随 `attrType.dataType`；`attrType.sort` 决定字段顺序。

**配之前先查子流程真实入参**：`env.read_schema_page(d, 子流程mid)` 读它的 `input`（DTO 全名）与 `nodes`。若子流程 `nodes=[]`（空流程体），映射什么都不会影响执行，但仍要配——空 `attrs` 是明确的缺陷信号，且用户会问。字段清单从抽屉下拉现取（caption + dataType），不要凭 DTO 名猜。

### 3.2 空值提示只有空白字符

见 §1。`nullHandling=TERMINATION` 的 RETRIEVE / MAP_OPERATION 尤其常见——用户点了「终止流程并显示提示」，但提示框里什么都没写。

## 4. 读回与产出

```python
meta, ds = env.read_schema_page(d, MID)      # MID 从编辑器 URL 末段取
flat = walk(ds.get('nodes'))                 # [(node, 祖先链), ...]
outputs = collect_outputs(ds.get('nodes'))   # 全部节点 output.name / outputName
```

- 节点数用 `flat` 长度，不要用 `len(ds['nodes'])`（只算根级）。
- 流程状态在 store 里，不在 dataSchema：`appDesign.microflowEditorReducer.flowBasicInfo` 的 `publishState`（`UNPUBLISH`=草稿）/ `state`（`RELEASE`）/ `lastVersionMetadataState`。`meta` 只回 `id` 和 `dataSchema`。
- 产出分三档列出，每条附 `nodeId` + `caption` + 祖先链，便于用户定位到画布上的那张卡片。

## 5. 汇报口径

用户问「节点是不是都有问题」时，回答必须包含：

1. 总数 / 有问题数 / 完全健康数——三个数一起给，避免只报坏消息显得流程全废。
2. 每条问题标层级（BLOCKING / QUALITY / RUNTIME）+ 会不会拦保存 + 运行时后果。
3. **主动交代自己修正过的误报**。体检脚本第一版几乎必然误报（父链没传、条件必填当恒需、子流程形参当引用），修完再报；把修掉的误报也说一句，比藏起来可信。
4. 修不修先问。子微流程入参映射要业务意图（从哪个前序出参映射到哪个子流程入参），不能自己编。
