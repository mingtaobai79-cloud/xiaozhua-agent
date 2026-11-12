# 交付模型：构造器 / 事实 / 工具边界

> 由 SKILL.md 拆分而来，按需读取。

## ★ 交付物形态：可复用工具 + 事实，不是写死的一次性脚本

用户明确要求：**不要出现写死或客户信息等固定内容，要的是事实和可复用工具，而不是固定生成工具。**

- appId / appName / 实体名 / 字段名 / 流程 id **一律运行时发现**，不写进脚本常量：
  - appId：编辑器 URL 的 `?appId=`；mid：URL `/microflow/editor/<mid>` 末段
  - appName：平台所有 UDC 全名都是 `com.seeyon.<appName>.<...>`，从流程 dataSchema 里正则反推（`re.search(r"com\.seeyon\.([A-Za-z0-9_]+)\.")`），不要额外找 application 查询接口
  - 实体：`udcMicroflowSearchTreeEntityPost` 现查（返回键 `caption` / `dtoFullName` / `fullName`(domain) / `relationEntity`）
  - 字段：`udcMicroflowFindDtoByEntityPost` 现查 `content.attributes`
  - cookie：CDP 现取，不读外部凭据文件
- 探测脚本按「实体/字段从节点已有配置或接口反查」组织，命令行只传中文标题这类**语义参数**；报告里写「本环境实测值」而不是把值编进代码。
- 机器相关但必须记录的（URL、端口）走环境变量：`UDC_BASE`（默认 `http://localhost:3000`）、`UDC_CDP`（默认 `http://127.0.0.1:9222`）、`UDC_COOKIE_FILE`。
- 提炼出的**可复用库要落进 git 正式位置**（如 `components/udc/microflow/live/`），不要留在被 `.gitignore` 挡住的 `scratch/` 临时目录——临时目录不进版本管理、随时丢。一次性探测脚本（probe_*/diag_*）留在 scratch 无所谓，但库必须提升进正式路径并 commit。
- 构造器/生成器函数（make_create_body / make_update_body / event_trigger 等）**参数化 appId/实体名**（`app_id=` 显式传参，实体名从 ref_node.output 推导），不能模块级写死 `APP_ID="..."` 常量——写死客户值的构造器是「固定生成工具」而非「可复用工具」。

具体反推方法与 GraphQL 调用形状见 `references/zero-hardcode-environment-discovery.md`。

### 外部引用也必须运行时拉活（不只 appId / 实体名）

模板或母版里的**子微流程 id、服务方法签名、生单规则 id** 同样会过期——母版制作时还存在的对象，发布时可能已被删。整份复刻旧 schema = 带着死引用发布：后端 `checkSchema` 照样全绿，用户在画布上一点才发现「引用的子流程不存在」。

生成任何带外部引用的节点前先过引用存活闸门（**拉不到就不生成**，不要跳过或写占位 id）：

| 引用 | 实时来源 | 判据 |
|---|---|---|
| 实体（含 methodLegal） | `udcMicroflowSearchTreeEntityPost` | 按 caption / dtoFullName 命中，children 递归拍平 |
| 字段 + md5 | `udcMicroflowFindCustomDtoPost` | `content.attributes` 逐字段带 md5 |
| 子微流程 | `udcMicroflowSearch` | **只收 `state=RELEASE`**（DRAFT 不可被引用） |
| 服务方法 | `udcMicroflowSearchMethodByNamePost` | body `{appId,appName,dtoFullName:<方法全名>,methodFullName:<同>}`，返回含 md5 / parameter / returnValue |
| 生单规则 | `udcDataFlowListManuallyMappingPost` | 按 sourceEntityId 查，空 = 该实体没配规则 |

实现见 `components/udc/microflow/live_refs.py`（实体 / 子流程 / 服务方法三个解析器 + 进程内缓存），查不到抛 `LookupError`。

**「模板结构 + 参数替换」只解决结构正确，不解决引用存活，两者是两件事**：模板保证字段齐全不缺胳膊少腿，闸门保证指向的对象还在。只做前者就复刻出「结构完整但引用全死」的流程。

**整份复刻活体母版不构成交付物。** 把一条已存在的流程 schema 原样复制、只改 name/caption 发布出去，用户会直接判定为「写死」——问一句「我要换需求呢」就露底：换实体/换子流程/换服务全得手工改 JSON。复刻最多当**结构取证**（拿来比对字段形态），交付必须是「模板骨架 + 活引用解析 + 语义参数」，改需求时只改参数。

### ★ 模板内部引用泄漏：`base(模板)` 出来的节点必须重写指向兄弟节点的引用

从 `fixtures/microflow/node_templates/<ACTION>.json` 复制模板再改字段，**模板里指向它自己那份 schema 兄弟节点的引用会原样留下来**——那些 nodeId 在本流程里根本不存在。

| 节点字段 | 模板残留 | 前端表现 |
|---|---|---|
| `CHANGE_LIST.dataSource` | `_CREATE_VARIABLE_3eLmAb` | 顶部红条「节点"追加列表"引用的参数"vText"已失效，请重新配置！」+ 卡片红框 |
| `MAP_OPERATION.selectMap` | `_CREATE_MAP_QhLDSd` | 抽屉「选择映射」空着（黄色空块），而后端字段里明明有值 |

**这类问题 `checkSchema` 完全查不出**（结构合法、必填齐全、errors=0），只有打开 UI 才看得见。发布前必须过闸门：

```python
def _collect_ids(ns, acc):          # 本流程全部 nodeId
    for n in ns or []:
        acc.add(n.get("nodeId")); _collect_ids(n.get("nodes"), acc)
        for c in n.get("conditions") or []:
            acc.add(c.get("nodeId")); _collect_ids(c.get("nodes"), acc)
    return acc

def _collect_refs(obj, out):        # 全部 SelectParam 引用
    if isinstance(obj, dict):
        if obj.get("type") == "SelectParam":
            nid = ((obj.get("selectParam") or {}).get("nodeInfo") or {}).get("nodeId")
            if nid: out.append(nid)
        for v in obj.values(): _collect_refs(v, out)
    elif isinstance(obj, list):
        for v in obj: _collect_refs(v, out)

known = _collect_ids(nodes, set()) | {"MFStartNode", "MFEndNode"}
leaks = [r for r in refs if r not in known]
if leaks: raise SystemExit("闸门拦截：存在指向不存在节点的引用，禁止发布")
```

值槽位（`attrs[].value`、`theKey`）与节点顶层字段（`selectParam`/`selectMap`/`dataSource`）**两类载体都要扫**。改模板节点时逐个显式重指：`n5["dataSource"] = dict(out_select_param(n1))`、`n14["selectMap"] = dict(out_select_param(n13))`——不要指望模板里的值能对上。

**外部引用与内部引用是两道闸门，缺一不可**：外部（子流程 / 服务方法 / 生单规则 id 过期）查接口现拉，内部（模板自带的兄弟节点名）查本地节点表。只做外部闸门会放出「引用了不存在的 vText」这种整条流程都存不下的错误。

### ★ 发布前闸门已产品化：直接调 `components/udc/microflow/gates.py`

不要每次在生成脚本里现写校验循环——仓库里已有成品，四道闸门 + 26 个节点的字段形态校验：

```python
from components.udc.microflow.gates import (
    run_gates, run_end_gate, run_leak_gate, run_order_gate)

problems = run_gates(schema) + run_end_gate(schema) + run_leak_gate(schema) + run_order_gate(schema)
if problems:
    for p in problems: print(p)
    raise SystemExit("闸门拦截")
```

| 闸门 | 拦什么 | 对应用户报错 |
|---|---|---|
| G1 | 表达式 translation 段数 ≠ tokens 数 | `ArrayList.rangeCheck` / 04000 |
| G2 | SelectParam 引用悬空 | 04004「前序节点发生变更」 |
| G3 | 类型不匹配（实体/文本） | 「不是根实体对象」「不是文本类型」 |
| G7 | `pageSearch=true` 但 pageInfo 空 | 「必填参数未配置」 |
| G9 | **字段形态**（见下） | 抽屉里显示空占位 |
| G10 | 模板引用泄漏（nodeInfo.nodeId 不在本流程） | 「引用的参数已失效」 |
| G11 | 顶层 endNode 缺失/字段错 | 画布「节点开发中...」 |
| G12 | 分支条件：name 非 ifBranch/elseBranch/elseIfBranch、ifBranch 无表达式或 resultTypeInfo≠BOOLEAN、elseBranch 带表达式 | 分支条件配不上/画布标签空 |
| G13 | 事件投递 IN_APP 用错 `selectEvent`/`selectMq`、AMONG_APP 缺 app、attrs 空 | 事件选不上 / 消息无载荷 |
| G14 | CONNECTOR 缺 app（该节点无生产样本） | 「连接器依赖已移除」 |
| G15 | condition[0].type 必须 GROUP（写 CONDITION → BOOT_3000，checkSchema 不报） | 发布拒「源对象不能为空」 |
| G16 | 活动节点（RETRIEVE/CHANGE_* 等 23 类）type 必须 ACTIVITY | checkSchema DATA_INVALID |
| G17 | 引用 BASIC 变量的 selectParam 不得带 id/dtoType（PageInfo 模板残留） | 前端「变量 xxx. 在上下文中不存在」 |
| G18 | MANUAL 入参/出参 name 必须 _FLOW_INPUT_/_FLOW_OUTPUT_ 前缀（业务名在 desc） | 前端变量表不认→表达式悬空 |
| G19 | 写操作节点出参必须是行数标量（INTEGER/BIGINTEGER，dtoType 空） | SingleResponse<Integer> 无法转 Dto，Java 编译失败 |
| G20 | 写操作的操作对象必须引 ACTIVITY 出参，不能直引 FOR_EACH/BRANCH | 生码把循环下标(int)当 Dto，int→Dto 编译失败 |

**G19/G20 是最贵的一课（2026-10-30 用户贴 backBuild.log 才发现）**：
checkSchema 绿、发布 RELEASE、UI 逐节点无红字 —— 全过，但平台构建时生成的 Java 编译失败。
因为**发布 ≠ 编译**：发布只写元数据，Java 代码在应用构建（deploy-normal）时才生成编译。
所以「写完流程」必须再走一次构建才算真验证；否则你以为交付了。
两条铁事实（643 条真实语料 100%，附编译报错原文）：
1. 写操作出参 = 影响行数标量，不是实体 DTO：CHANGE_ENTITY 103/103 INTEGER、
   CHANGE_BATCH_ENTITY 41/41、DELETE_ENTITY 13/13、CREATE_BATCH_ENTITY 6/6 均 INTEGER，
   CREATE_ENTITY 32/32 BIGINTEGER。写成 DTO 就报
   `SingleResponse<java.lang.Integer> 无法转换为 SingleResponse<...Dto>`。
2. 写操作的操作对象 103/103 引活动节点出参（RETRIEVE 95 / CREATE_VARIABLE 4 /
   FLOW 3 / BUSINESS 1），**0 例直引 FOR_EACH**。直引循环项报
   `int 无法转换为 ...Dto`（生码把循环下标当对象传）。
   循环内改数据走：FOR_EACH → RETRIEVE(IDS, 引循环项.id) → CHANGE_ENTITY(引该 RETRIEVE)。
   循环项字段引用形态：key=`出参名+DTO全名+"."+字段`（DTO 带点）、path=`DTO去点+"."+字段`、
   dtoType=CUSTOM、customs 沿用属性块；循环项整体引用：key=`出参名+DTO全名`、dtoType=SUB_ENTITY。

### 改 gates.py 的插入纪律（插错函数 = 新规则永不执行）

往 gates.py 加规则时，靠文本定位插入点会**插进别的函数**：`run_end_gate` / `run_order_gate` 里
也有 `    return problems` 这一行，`src.rfind("    return problems")` 命中的往往不是 `run_gates`。
结果是编译过、import 过、AST 里能看到规则文本，但规则根本不在被调用的那个函数里——
注入缺陷回归全 MISS，看起来像「判据写错了」，实际是**代码没执行**。

- 定位：`ast.parse` 取目标函数节点的 `lineno/end_lineno`，插在它最后一个 `ast.Return` 之前。
- 复验：写盘后再 `ast.parse`，断言每个 G 编号出现在 `ast.get_source_segment(全文件, 目标函数)` 里。
- 排障次序：注入全 MISS 时**先查「规则是否在该函数体内」**，再查判据逻辑。
- 剪走代码块后要补回被剪函数的 `return`——否则该函数返回 None，调用处抛
  `'NoneType' object is not iterable`（组装器 `finish()` 会连带失败）。

### ★ 闸门必须用真实生产流程校准，否则误报会挡住业务

**只拿「结构正确的样本」验证闸门是不够的：样本太少时误报发现不了。用整个真实应用的全量已发布流程回归。**

取证命令（只读，不写不改不删）：

```python
# 1. 列某应用全部微流程（结构是 pageInfo/params 两个嵌套对象，不是扁平字段！）
V = {"p": {"pageInfo": {"needTotal": True, "pageNumber": 1, "pageSize": 999,
                        "pages": 0, "total": 0},
           "params": {"appId": APP_NUM, "IN_type": ["SERVICE", "CUSTOM"]}}}
# 2. 逐条 FindByIdGet 拿 dataSchema，存成 json
# 3. 对每条的 dataSchema 跑闸门，统计「有问题的流程数 / 总流程数」
```

实测校准结果（智能项目管理平台 643 条 RELEASE）：

| 阶段 | 误报流程数 | 说明 |
|---|---|---|
| 初版闸门 | 419 / 643 (65.2%) | 1048 个问题，闸门基本不可用 |
| 修 G10/G11 trigger 出参与 endNode | 91 / 643 (14.2%) | |
| 重写 G1 段数判据 | 52 / 643 (8.1%) | |
| 修 G2 系统变量 | 13 / 643 (2.0%) | |
| 降级 G9 nullPromptMessage | 5 / 643 (0.8%) | |
| 补 G10 裸引用字段扫描（发现真缺陷） | 14 / 643 (2.2%) | 75 个全是真死引用 |

**每一条过严判据都对应一个真实误报模式，别凭直觉定阈值：**

| 误报 | 表现 | 真实事实 |
|---|---|---|
| G10 引用 `_BUSINESS_EVENT_xxx` | 事件监听流程必中 | trigger 出参不在 `nodes` 里，是合法引用源 |
| G11 endNode.value 空 | 事件/定时流程必中 | `paramType=NONE` 或事件流程本身无出参，合法 |
| G1 段数不匹配 | 含函数的表达式全中 | tokens 是中序平铺，**括号各占一个 OPERATOR token** |
| G2 表达式引用悬空 | 用了应用配置参数就中 | `__SYSTEM_PARAMS.xxx` / `system.currentUserId` 是系统变量 |
| G9 nullPromptMessage 空 | 存量 MAP_OPERATION 全中 | 生产 24 个全部为空仍正常运行，是 UI 新增强校验 |
| G8 引用后序节点 | 母版就中 | 平台不强制引用顺序，改 `strict=False` 默认不报 |

### G1 段数判据的正确算法（别再按「2*运算符+1」写）

```python
# 错：只要含括号就 return 1  → `f(a)&&f(b)` 判成 1 段，实际 5 段，误报 442 次
# 错：2*运算符数+1         → 漏掉括号 token，`(a==b)&&c` 判成 5，实际 7
# 对：tokens 数 = 2*二元运算符数 + 1 + 2*括号对数；布尔字面量 true/false 单 token 合法
```

更稳的做法是只查结构性错误，别算总数：
- 首 token 不能是二元运算符（`==` `>` `&` `|` `+` …）——那是错位，渲染成「1 1」
- `(` 与 `)` 数量必须相等
- `OPERATOR` 的 value 实测全量只有：`== != > < >= <= + - * / & | ( ) true false`
  注意 `&`/`|` 是**单字符**（不是 `&&`/`||`）

### 遍历必须 yield CONDITION 自身，不只是它的子节点

```python
for c in n.get("conditions") or []:
    yield c                            # ← 漏这行，所有条件类校验永不执行
    yield from _walk_nodes(c.get("nodes") or [])
```

漏这行的后果：G12（分支条件校验）看着写了、跑起来 0 命中，注入 `name="wrongBranch"` 也检不出来——**假通过比报错更危险**。判据：往样本里注入一个非法条件，闸门必须报；报不出来就是遍历漏层。

### 引用有两类载体，只扫值槽位会漏一半

```python
# ① 值槽位：{type:"SelectParam", selectParam:{outputName, nodeInfo}}
# ② 节点顶层裸引用字段（无 type 外壳）：
#    node.selectParam / node.selectMap / node.dataSource
#    CHANGE_VARIABLE.selectParam、MAP_OPERATION.selectMap、CHANGE_LIST.dataSource 都是这类
BARE_REF_FIELDS = ("selectParam", "selectMap", "dataSource")
```

只扫 ① 时：注入到 `node.selectParam` 的悬空引用检不出来（实测漏报），而这类恰恰是「引用的参数已失效」红条的主因。

### 闸门回归必须双向验证

```
A. 误报基线：全量真实生产流程 → 有问题的流程数必须接近 0
              剩下的每一条都要能解释成「生产本身的真实缺陷」
B. 漏报检测：往真实样本里注入每类缺陷 → 命中率必须 6/6
```

只做 A 会写出「什么都不报」的空闸门；只做 B 会写出「什么都报」的废闸门。

两段都已封装成 `scripts/regress_gates.py`，**改完闸门就跑它，不要手搭脚本**：

```bash
python scripts/regress_gates.py --app <纯数字appId> --app-name <udc应用名> \
                                --save /tmp/gate-samples.json
python scripts/regress_gates.py --app <id> --no-inject      # 只看误报
```

它自带三件容易错的事：`udcMicroflowSearch` 用 `pageInfo`+`params` 嵌套（不是扁平）、`FindByIdGet` 用 `path:` 不是 `body:`、注入基底自动选覆盖 actionType 最多的一条。

### ★ 模板 ≠ 保存态：生成前必须按真实契约归一化

`fixtures/microflow/node_templates/` 是前端 `addNode` 的**新建态**，不是保存态。
真实 643 条生产流程（7937 节点）对照，25 个模板有 11 处不一致：

| 类型 | 节点 | 差异 |
|---|---|---|
| 模板多（必剥） | `CUSTOM_ERROR`/`FOR_EACH` | 带 `actionType`，真实 25/384 条全无 |
| | `CREATE_MAP` | 带 `paramType`+`dataType`，真实 4 条全无 |
| | `SUB_MICROFLOW` | 带 `pageInfo`，真实 251 条全无 |
| | `CALL_DATA_FLOW` | 带 `selectParam`，真实用 `condition` |
| 模板缺（必补） | `CREATE_LIST` | 缺 `value`，且必须是**数组** `[]` 不是 Simple 对象 |
| | `CALL_DATA_FLOW` | 缺 `condition`（`[GROUP{conditions:[CONDITION]}]`）|
| 值形态错 | `FOR_EACH.foreach` | 模板 `{sourceItemes:[]}` → 真实 **`null`**（384/384）|
| | `LIST_OPERATION.output` | 模板 `null` → 真实**对象**（654/654）|
| | `SUB_MICROFLOW.outputName` | 模板 `null` → 真实**字符串**（215/251）|

**判据只看键名不够，值形态也要对。** `FOR_EACH.foreach` 最容易踩：
`{sourceItemes:[]}` 只是新建占位，保存后落 `null`，真正的循环源是 `selectParam`。

### 保证正确生成的四个机制（缺一不可）

```
1. 契约表   core/facts/udc/microflow/node-contract-from-samples.json
            26 类节点 MUST/USUAL/OPT + 每种值的出现次数
2. normalize_node()   components/udc/microflow/contract_gate.py
            剥掉「真实样本从未出现」的键，已挂在 NodeBuilder.build() 自动生效
3. check_schema()     同一文件
            缺 MUST / 多字段 / 控制节点写 actionType / 值形态错
4. tests/test_constructor_contract.py
            22 个构造器逐个造节点跑契约，必须 22/22 通过
```

再加一道发布前闸门：生成脚本里调 `contract_gate.check_schema(schema)`，
非空就 `SystemExit`。四道合用才叫保证——只有文档没人执行，
只有 normalize 会静默改数据，只有 check 不阻发布，只有测试盖不住新节点。

### 控制节点的 actionType 恒为 null

`BRANCH`(941) / `CONDITION`(1981) / `FOR`(32) / `FOR_EACH`(384) / `CUSTOM_ERROR`(25)
**全部样本都没有 `actionType` 键**，只能靠 `type` 取。写了会被契约闸门判污染。
唯一例外是 `BREAK`（8/8 都有）。

### 跨应用：结构可复用，值不可复用

两个独立应用对照（643 条 vs 9 条真实流程）：共有 9 类节点**契约冲突 0 个**；
但每个字段的值都带应用专有信息（`appName`/`id`/`javaType`/`relationEntity`/`md5`/`path`），
必须运行时走 `LiveRefs`。

**判据**：生成代码里出现任何 `com.seeyon.<应用名>` 字面量、任何裸数字 id，就是写死了。

**做跨应用对照前必须剔除自己的产物。** 本轮把助手自己生成的测试流程当成真实样本，
得出「18 个契约冲突」，清洗后真实冲突是 0——拿生成器跟生成器比，结论会完全反向。

### 证据薄弱节点（样本量 <10，契约不当完备用）

`CALL_DATA_FLOW`(1) / `CREATE_MAP`(4) / `CREATE_BATCH_ENTITY`(6) / `CONNECTOR`(0)。
`CONNECTOR` 在 `cip-connector` 无已注册服务，需先进集成平台配连接器再生成。

### ★ 常量字面量两个语境不能混用（组装路径必踩）

同一个「常量」在两个位置是两种类型：

| 位置 | 正确类型 | 生产次数 |
|---|---|---|
| 值槽位 `value`/`attrs[].value`/`entries[].value` | `{"type":"Simple","simple":...}` | 322 |
| 查询条件 `rightParams[]` | `{"type":"CONSTANT","value":...}` | 193 |

**`CONSTANT` 在值槽位出现 0 次。** 用错的表现：`checkSchema` 返回
`check=false` + `value.type DATA_INVALID`（节点能建、闸门旧判据放行、只有真发布才暴露）。

代码约定：`microflow_fields.constant()` 只用于查询条件，`simple()` 只用于值槽位。
契约闸门扫 `value`/`attrs`/`entries`/`mappingRule` 四个槽位发现 CONSTANT 即报。

### ★ dtoType 只在实体列表上必需

`LIST_OPERATION`/`CHANGE_LIST` 的 `selectParam`：

| dtoType | 数量 | 特征 |
|---|---|---|
| 有 | 803 | 全是实体/DTO：SUB_ENTITY 527 / MASTER_ENTITY 200 / CUSTOM 76 |
| 无 | 168 | 全是**基础类型列表**：BIGINTEGER 92 / STRING 70 / DECIMAL 6 |

判据必须是 `is_entity_list and not dtoType`，一刀切「必须有」会误报 168 次。

### ★ 模板残留引用：构造器必须主动清

节点模板里带着录制那条流程的节点引用（`SUB_MICROFLOW.json` 含 `_RETRIEVE_KNCEzh`），
换流程后该节点不在本流程，G2 直接拦。

**规则**：凡是「有默认值的存在引用字段」，构造时必须显式覆盖或清空，不继承模板值。
排查：`tests/test_template_residue.py`（22 个构造器机械扫，不许有残留）。

### ★ 真实业务的靶子：46% 是 1-3 节点（643 条实测）

**别拿「能拼出 20 节点的复杂流程」当能力证明——那不是真实业务的主流形。**
643 条 RELEASE 实测分布：

| 规模 | 条数 | 占比 |
|---|---|---|
| **1-3 节点** | **294** | **46%** |
| 4-8 节点 | 153 | 24% |
| 9-15 节点 | 82 | 13% |
| 16-30 节点 | 75 | 12% |
| 31+ 节点 | 39 | 6% |

节点数：中位数 **4**，平均 9.3。含分支 51%、含循环 32%、含子流程 24%。

**高频顶层骨架（70% 业务的真身）**：

| 次数 | 骨架 | 业务含义 |
|---|---|---|
| 56 | `RETRIEVE` | 查单条 |
| 40 | `RETRIEVE → CREATE_VARIABLE → BRANCH` | 查出→取字段→判空 |
| 38 | `SUB_MICROFLOW` | 调子流程 |
| 33 | `RETRIEVE → BRANCH` | 查出→判空 |
| 10 | `CREATE_LIST → LIST_OPERATION → CREATE_LIST → FOR_EACH → CHANGE_BATCH_ENTITY` | 列表加工→循环改 |

**业务名字就是需求描述**：「根据 X 查询 Y」「根据 X 更新 Y」「X 后删除 Y」——
生成器应该能从这类单句直接推出骨架，不需要用户描述成完整流程图。

**零节点不是残废**：128 条零节点中 **122 条是 `type=CUSTOM`**（纯出入参无节点链），
是本文件「类型×触发 6 组合矩阵」里的合法形态。CUSTOM 的入参出参类型可以不同
（BASIC 入 / DEFAULT_OBJECT 出 25 条）。**生成器必须能造 CUSTOM 型**，现在做不到。

详见 `core/facts/udc/microflow/business-skeletons-from-643.md`。

## ★ 需求 → 节点方案：先出方案让用户拍板，再写代码

用户给的常常是**一句业务话**（「校验数据源是不是有效的，入参是 id，查到数据判断启用状态…」），
不是 schema。**不要直接开始拼节点**——先产出节点方案，列出歧义点，等用户确认后再生成。
跳过这步的后果更贵：形态全对、能发布、后端 errors=0，但业务语义是错的。

**拆解步骤（按序）**：

0. **先写伪代码，再拼节点（用户严令：想象你在写代码，每个节点就是一句预制的语法）**。
   节点形态全对 ≠ 业务组合对。先把业务写成一段伪代码，控制流（嵌套、顺序、排除）在伪代码里定清楚，再逐句映射节点。
   伪代码错了，生成出来的流程「能发布、errors=0、逐节点无红字，但业务是错的」——
   典型翻车：该嵌套的分支拼成平级（未启用也去判 mysql）、排除条件没进查询、为中转值多建变量。
   写完伪代码先自查三问：这个判断真的依赖上一个判断吗（→ 嵌套）？「其他」排不排除自己（→ 进查询条件）？
   这个中间值有下游消费者吗（没有就不建变量）？
1. **逐句切动作**：一句业务话里每个动词是一个动作（查询 / 判断 / 修改 / 赋值 / 出参）。
2. **动作 → 节点类型**，照下表落，不要凭感觉选：

   | 业务动作 | 节点 |
   |---|---|
   | 按 ID 取一条 | `RETRIEVE`（`fetchType=IDS`）|
   | 按条件查一条 / 多条 | `RETRIEVE`（`CONDITION`）/ `RETRIEVE_ARRAY` |
   | 判断 X 是不是 Y | `BRANCH`（条件表达式走 `/expression/transform`）|
   | 遍历一批逐条处理 | `RETRIEVE_ARRAY` → `FOR_EACH` → 循环体内写操作节点 |
   | 改字段 / 改状态 | `CHANGE_ENTITY`（`attrs[]`）或 `CHANGE_VARIABLE`（改变量）|
   | 存中间值 | `CREATE_VARIABLE`（按值类型选 paramType）|
   | 算出布尔/文本结果给出参 | 前置 `CREATE_VARIABLE` 给默认值 + 分支内 `CHANGE_VARIABLE` 覆盖 |
   | 对外返回 | `END`（`paramType=BASIC` + `basic=<类型>`）|
   | 复用一段已有逻辑 | `SUB_MICROFLOW`（只收 RELEASE）|

3. **实体名不能凭业务名猜**。用户说「数据源」，实体可能叫「数据源配置信息」——
   直接 `find_entity(label="数据源")` 精确匹配会落空。先 `LiveRefs.entity(app_id, app_name)`
   拉全量实体，按关键词过滤 `caption`/`dtoFullName` 拿到候选，再 `entity_model()` 取字段表。
4. **字段必须活取，中文名靠 caption 反查**：「是否启用」→ `enabled` BOOLEAN、
   「JDBC URL」→ `jdbcUrl` STRING。这些映射只能从 `entity_model()["attributes"][name]["caption"]` 反查，
   不能按拼音/英文习惯猜（猜错 `checkSchema` 能过，前端显示成完整路径）。
5. **「A 则 X，否则 Y」不要在两个分支各建同名变量**——平台报重名（`UDC_DTO_0001`）。
   正确形态：**前置 `CREATE_VARIABLE` 给默认值 → if 分支 `CHANGE_VARIABLE` 覆盖 → else 分支留空 → END 引用该变量**。
6. **方案里必须写明「哪些节点不用、为什么不用」**。这证明是按业务选节点，不是照 26 类清单凑数；
   用户据此判断你懂不懂业务。
7. **歧义点必须列出来让用户拍板，不要替他选**。典型三类：
   - 「其他记录」= 排除自己 / 同类型同角色 / 全部？（选错直接把不该停用的停掉）
   - 「然后修改数据」是只改状态，还是也改 updateTime / 备注？
   - 判断依据取当前这条，还是查出来的那一批？
   每个歧义给候选方案 + 各自的**业务后果**，让他一句话就能选。

拆解范例（需求原话 → 伪代码 → 节点方案 → 歧义点）见 `references/business-to-node-plan.md`。

### ★ 组合层三条铁律（形态全对也会栽在这里）

- **「其他/别的」= 在查询条件里排除自己**（`id != 入参`，NEQ + CONTEXT_VARIABLE 引 `_FLOW_INPUT_*`），
  不是查完再过滤——查询条件写错范围，停用的就是不该停的数据。
- **依赖性判断必须嵌套**：内层 BRANCH 挂在外层 BRANCH 的 `conditions[ifBranch].nodes` 里（真实生产十余处嵌套 BRANCH），
  不是拼在顶层平级——平级的第二个分支在外层条件不成立时也会执行。
- **不为中转值建变量**：要判上游查询出的字段，表达式 context 直接挂那个查询节点的出参变量树、
  token 直接引 `_RETRIEVE_xxx._RETRIEVE_xxx.<字段>`。为中转值建 CREATE_VARIABLE 是多出来的节点，
  用户一眼看出「你创建变量做什么」，且引用形态稍有差异就断成 `文本包含(vJdbc., mysql)` 这种悬空。

## ★ 构造器只造 1 种形态 = 缺胳膊少腿（覆盖率 11%）

同一 actionType 在真实业务里有多种**子形态**，用判别字段区分。构造器通常只实现最直白那一种：

| 节点 | 真实形态 | 构造器 | 最高频缺失形态 |
|---|---|---|---|
| CHANGE_VARIABLE | 23 | 1 | `attrs[N]` 字段级映射（335 次）vs `value{}` 整体赋值（717 次） |
| SUB_MICROFLOW | 16 | 1 | `attrs[N]+mappingType` 参数映射（56 次） |
| RETRIEVE_ARRAY | 8 | 1 | `pageSearch+sortParams`（133 次） |
| CREATE_ENTITY | 8 | 1 | `mappingType+value` 整体对象引用（16 次） |
| CALL_APP_SERVICE | 6 | 1 | `mappingType+attrs[N]` DTO 多参数（68 次） |
| BRANCH | 5 | 1 | 3/4/5/6 分支（58 次） |
| CREATE_VARIABLE | 4 | 1 | 实体型 `structure`（247 次） |
| RETRIEVE | 4 | 1 | `value{}` ID 查询（246 次） |

**判别字段就是形态指纹**，生成前先看真实样本用的是哪个值：

| 节点 | 判别字段 | 取值与含义 |
|---|---|---|
| RETRIEVE | `fetchType` | `CONDITION`（375，有 condition）/ `IDS`（246，**无 condition**，ID 入顶层 `value`）|
| CREATE_VARIABLE | `paramType` | `BASIC`（429，有 value）/ `ENTITY_OBJECT`（177）/ `DEFAULT_OBJECT`（75）/ `OTHER`（31，`otherType=SYSTEM_PAGE_INFO`）|
| CHANGE_VARIABLE | `mappingType` | 无（717，`value{}`）/ `attrs`（335，`attrs[{attrType,value}]`）|

**非 BASIC 型的 CREATE_VARIABLE 没有 `value` 键**，值是走 `attrs[].value`。
给实体型塞 `value` 会让抽屉里「默认值」和字段映射打架。

**`CHANGE_VARIABLE.output` 恒为 null（1053/1053）**，它不能当引用源。
可做 endNode 引用源的末节点类型（真实统计）：`CREATE_*` 88 / `RETRIEVE` 32 /
`LIST_*` 10 / `SUB_MICROFLOW` 3。

形态统计工具：`scratch/form_coverage.py`（改前先跑，看清真实形态分布）。

