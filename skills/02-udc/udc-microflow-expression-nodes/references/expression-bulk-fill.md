# 批量把值槽位升级为表达式（全节点覆盖，LIVE PASS）

目标：微流程里**每个**「值」字段都变成表达式，一个不漏。
不依赖 UI（抽屉在窄视口/只读态下必失败），走 `/check` + `/transform` 生成、GraphQL 全量写回。

## 0. 先确认这条路线是否适用

本文件描述的是**直写 `dataSchema`** 的批量路线。它能让 `/check` 全绿、后端回读正确，
但**绕过了前端的控件绑定**——值槽位变成 `Expression` 后，节点抽屉里对应的必填项
会显示为空（控件不会渲染 Expression 回显）。

用不用它，看交付要求：

| 要求 | 选哪条 |
|---|---|
| 用户要在编辑器里看到值、要能再改 | **走 UI**（开抽屉→填→确定→暂存草稿），不用本文件 |
| 批量造流程 / 不关心面板回显 | 用本文件 |
| 用户明确说「填完就点确定，看后台校验接口」 | **一律走 UI**，直写等于没按要求做 |

面板回显失败时别当成「数据没存上」去重做——先 `read_schema_page` 回读，
如果后端 `type=="Expression"` 且 `/check` 通过，就是回显问题，不是数据问题。

**先做一个、在 UI 里看一眼，再做剩下的。** 值槽位改成 `Expression` 是不可逆的面板退化：
一旦写入，那个字段在抽屉里就再也无法正常编辑。批量前先用**单个**槽位跑完整链路
（写库 → 刷新编辑器 → 开抽屉看这个字段），确认面板能正常显示且无红字，再扩到全部。
反过来做（先改 24 个再去看）只能整包回滚重来。

回滚要备好干净备份：改动前的 `dataSchema` 存盘（实测 45KB 量级），恢复时用
`udcMicroflowFindByIdGet` 取全量 DTO → 换回旧 `dataSchema` → `udcMicroflowUpdatePost`，
恢复后刷新编辑器确认 `flowNodes` 数量与 `flowChanged=false`。

## 1. 值槽位是什么

schema 里每个「值」都是一个值包装对象，只有三种形态：

```jsonc
{"type":"Simple","simple":0,"desc":0}                     常量
{"type":"SelectParam","selectParam":{...}}                  选变量
{"type":"Expression","expression":{"title","schema"}}     表达式
```

枚举槽位时**必须跳过 `output` / `input` / `mfService`** —— 它们内部也有 `type` 字段，
按「有 type 就是值」扫会把节点出参误判成值槽位。

```python
def iter_value_slots(node):
    found = []
    def rec(obj, path, depth=0):
        if depth > 12: return
        if isinstance(obj, dict):
            if obj.get("type") in ("Simple", "SelectParam") and any(
                    k in obj for k in ("simple", "selectParam")):
                found.append((path, obj)); return          # 命中即止，不再下钻
            for k, v in obj.items():
                if k in ("output", "input", "mfService"): continue
                rec(v, f"{path}.{k}" if path else k, depth + 1)
        elif isinstance(obj, list):
            for i, x in enumerate(obj):
                rec(x, f"{path}[{i}]", depth + 1)
    rec(node, "")
    return found
```

典型槽位：`attrs[i].value`、`entries[i].key/value`、`forStart/forEnd`、`value`、`theKey`、
`attrError`、`conditions[i].nodes[j].*`。

## 2. 四条决定「能不能填」的硬约束

### 2.1 执行顺序：只能引用**前面**节点的输出

表达式在节点执行时求值，引用后面节点的出参运行时拿不到值。

```python
def available_vars(ordered, idx, sysvars=()):
    pool = []
    for j in range(idx):                      # ★ 只到 idx，不含自己
        o = ordered[j].get("output")
        if isinstance(o, dict) and o.get("name"):
            pool.append({"name": o["name"],
                         "dataType": norm_type(o.get("dataType")),
                         "desc": o.get("desc") or "",
                         "paramId": o.get("id") or o.get("javaType")})
    return pool + list(sysvars)
```

`ordered` 要按执行顺序生成：**条件分支内的 nodes 先于后续兄弟节点**。

```python
def walk_ordered(nodes, out=None):
    out = [] if out is None else out
    for n in nodes or []:
        out.append(n)
        for c in n.get("conditions") or []:
            walk_ordered(c.get("nodes"), out)
        walk_ordered(n.get("nodes"), out)
    return out
```

### 2.2 系统变量不受顺序限制 —— 解开「前置没有合适变量」的死局

`system.*` 走全局表，**任何节点位置都能用**。这是让「前面根本没有 STRING 变量」的字段
也能填上表达式的唯一办法。

```jsonc
{"uid":"...","type":"SYSTEM","value":"system.currentUserName","desc":"登录人员姓名"}
```

- token 类型是 **`SYSTEM`**，不是 `VARIABLE`
- `schemas` 可以是**空数组**（不进变量树）
- 值的引用形态是 `system.currentUserName`（全名），不是短名

取列表：`GET /service/udc/expression/system-variable/list`，
遍历 `data.content[].items[]`，跳过 `hidden:true`，取 `name` / `resultType` / `description`。

常用：`currentUserId`(BIGINTEGER) `currentUserName`(STRING) `currentUserCode`(STRING)
`currentOrgName`(STRING) `currentDateTime`(DATETIME)。

### 2.3 `resultTypeInfo` 只有 15 个合法值，DTO 必须 ENTITY + fullName

```
INTEGER BIGINTEGER DECIMAL STRING MULTILINESTRING
DATETIME DATE TIME BOOLEAN CURRENCY ATTACHMENT
ARRAY ENTITY CTPENUM ENUM
```

- `OBJECT` **不在值域** → `FORMULA_6003`（RESULT_TYPE_ERROR）
- DTO 场景用 `ENTITY`，且**必须带 `resultTypeFullName`** → 缺则 `FORMULA_6901`
- `resultTypeFullName` 取该 DTO 变量的 `output.id`（如 `com.x.dto.XDto`），不是变量名

### 2.4 后端类型名必须归一化

同一概念有多种写法，不归一会「明明有变量却匹配不到」：

```python
def norm_type(dt):
    t = (dt or "").strip().upper()
    return {"LONG": "BIGINTEGER", "OBJECT": "DTO", "DTO": "DTO"}.get(
        t, t or "STRING")
```

- `String`（小写 s）与 `STRING` 是同一个类型 —— 按 `STRING` 比对会漏掉 `String`，
  一处漏配就是十几个字段被误判成「无可用变量」
- `Long` ≡ `BIGINTEGER`
- `Object` / `Dto` ≡ `DTO`

## 3. 构造 DTO

```python
def build_expression_dto(var, want):
    name, u = var["name"], lambda: str(uuid.uuid4())
    if var.get("system"):                                   # 系统变量分支
        sym = {"uid": u(), "type": "SYSTEM", "value": name, "desc": var["desc"]}
        if want in NUMERIC:
            return dto([sym, op("+"), const("0")], want, schemas=[])
        if want == "BOOLEAN":
            return dto([sym, op("="), const("true")], "BOOLEAN", schemas=[])
        return dto([sym], want if want in DATE_TYPES else "STRING", schemas=[])

    if want in NUMERIC:                                     # 标量：三段式点路径
        return dto([var_tok(f"{name}.{name}.value"), op("+"), const("0")],
                   want, schemas=scalar_schemas(name, want))
    if want == "BOOLEAN":
        return dto([var_tok(f"{name}.{name}.value"), op("="), const("true")],
                   "BOOLEAN", schemas=scalar_schemas(name, "BOOLEAN"))
    if want == "DTO":
        pid = var.get("paramId") or name
        return dto([var_tok(f"{name}.{name}")], "ENTITY",
                   full=pid, schemas=dto_schemas(name, pid))
    return dto([var_tok(f"{name}.{name}.value")], "STRING",
               schemas=scalar_schemas(name, "STRING"))
```

`scalar_schemas` 是三层树：根 OBJECT(selectable:false) → 自身 OBJECT(selectable:true) →
`value` 叶子(该类型)；每层都带 `skip:true` 与 `uniformityParams.paramId`。

`var_tok(v)` = `{"uid":..., "type":"VARIABLE", "value":v, "desc":...}`。

## 4. 有些槽位**不该**表达式化

不是所有 `SelectParam` 都是「值」，有些是**结构选择器**：

- `RETRIEVE_ARRAY.pageInfo` → 指向 `com.seeyon.boot.transport.PageInfo` 实例，
  是分页参数对象，不是可求值标量。强行表达式化必报 `FORMULA_6901`。
- 同类：任何 `selectParam.id` 与字段自身期望类型不一致的结构引用。

判定：**字段自带的 `selectParam.id` 与候选变量类型不同 ⇒ 保留 SelectParam**。
这类残留是正确结果，不算漏填——报告时要单独列出并说明原因。

## 5. 写回链路

```
1  read_schema_page → {id, dataSchema}                    ← 只有这两个字段
2  逐槽位替换 {type:"Expression", expression:{title, schema}}
3  结构自检：nodeId 列表长度与集合都不变，否则中止
4  udcMicroflowFindByIdGet → 取全量 DTO（实测 34 字段）    ← ★ 必须重取
5  DTO.dataSchema = json.dumps(new_schema)
6  udcMicroflowUpdatePost（变量名 body）
7  后端回读 → 逐槽位确认 type == "Expression"
8  每条表达式 /check + /transform 复验
```

### 5.1 两个必踩的接口细节

**`read_schema_page` 只返回 `{id, dataSchema}`**，不是全量 DTO。直接把它的返回值当提交体
会报 `BOOT_1001 微流程名称所属应用ID 不能为null`。提交前必须再调一次
`udcMicroflowFindByIdGet` 拿完整记录（`appId` / `caption` 等都在里面）。

**GraphQL 变量名是 `body`，不是 `p`**。仓库里的 `gql_page()` 把变量名固定成 `{p: 变量}`，
只适配 `...FindByIdGet(path: $p)` 这类；`udcMicroflowUpdatePost` 的签名是
`update(body: $body)`，必须自定义请求：

```javascript
fetch('/service/udc/graphql?udcMicroflowUpdatePost', {
  method:'POST', headers:{'Content-Type':'application/json'},
  body: JSON.stringify({query, variables: {body: dto}})
})
```

### 5.2 结构自检不可省

替换是就地写嵌套路径（`attrs[0].value`、`entries[0].key`），路径解析错会静默改错位置。
提交前比对 nodeId 列表：

```python
old_ids = [n.get("nodeId") for n in walk(ds["nodes"])]
new_ids = [n.get("nodeId") for n in walk(new_ds["nodes"])]
assert set(old_ids) == set(new_ids) and len(old_ids) == len(new_ids)
```

## 6. 验收（六档，缺一不可）

| 判据 | 可信度 | 说明 |
|---|---|---|
| 本地替换成功 | 低 | 只说明内存改了 |
| 结构自检（节点/ID 不变） | 中 | 防路径写错 |
| update 返回 `BOOT_0000` | 中 | 不等于字段留下了 |
| **后端回读 `type=="Expression"`** | **高** | 逐个槽位比对 |
| **每条 `/check` = `content:true`** | **高** | 5 段 Filter 链 |
| **每条 `/transform` = `BOOT_0000`** | **高** | 能产出运行态 |

最后再跑一次全字段审计（`SAVE_REQUIRED_FIELDS` + 表达式层 + 悬空引用），确认无回归。

**这六档全部看不见面板。** 交付前若用户要在编辑器里使用，必须再补一次 UI 验收：
开抽屉 → 确认字段有值、无红字 → 点确定 → 点暂存草稿 → 回读。

## 7. 实现落点

`components/udc/microflow/expression_fill.py`：

```
norm_type(dt)                     String→STRING / Long→BIGINTEGER / Object,Dt→DTO
iter_value_slots(node)            (path, slot) 枚举，跳过 output/input/mfService
slot_want_type(slot)              槽位期望的结果类型
build_expression_dto(var, want)   构造 ExpressionSaveDto（含系统变量分支）
pick_variable(pool, want)         按类型挑第一个匹配
walk_ordered(nodes)               按执行顺序遍历
available_vars(ordered, idx, sys) 前置输出 + 系统变量
```

配套：`components/udc/microflow/expression_api.py`（check/transform/roundtrip）、
`components/udc/microflow/expression_audit.py`（静态层：变量根、恒等式、token 五型）。
