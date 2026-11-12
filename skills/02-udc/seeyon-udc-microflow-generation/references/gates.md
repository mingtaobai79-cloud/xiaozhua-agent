# 闸门体系（G1–G40）与校准

> 本文件由 SKILL.md 拆分而来，按需读取；主文件只保留每次都执行的铁律。

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
| G26 | CALL_APP_SERVICE 的 selectMethod 缺 md5/parameter/returnValue/fullName（签名必须原样取自 SearchMethodByNamePost，剥掉后 checkSchema 照绿） | 设计器「参数」页签取不到出入参 |
| G27 | CHANGE_VARIABLE(mappingType=attrs) 的 attrType 缺引用四键（同 G25 机制；G25 只查 CREATE_VARIABLE 会漏它） | 字段映射红字「所选数据已失效」 |
| G28 | DATA_MAPPING mappingRows 为空或缺 targetField/mappingMode/value（G4 只查顶层，查不到行级） | 映射行变空映射 |
| G29 | DATA_MAPPING 上游为单对象主实体（selectParam dtoType=MASTER_ENTITY 且 position=parent） | **构建编译失败**：生成器把输出声明成 `List<Dto>` 再取字段（`找不到符号 getName()`），只有 backBuild.log 暴露 |
| G30 | 赋值方式硬校验：实体型变量（ENTITY_OBJECT/DEFAULT_OBJECT/OTHER）mappingType 必须 attrs/value/mapping 三选一显式；BASIC 引用 DTO 字段（id=\<Dto\>.\<field\>）必带 selectParam.path（语料 25/25）；CHANGE_VARIABLE 模式与载荷必须匹配（attrs↔非空 attrs / value↔非空 value / 二者全空拦） | 赋值方式不选 → 前端不知道生成什么类型代码，依赖配置不出现，构建必炸 |
| G31 | 引用链类型校验：引用槽（selectParam/selectMap/dataSource/value）的 outputName 必须来自前序节点出参/入参；dataType 与 ARRAY/OBJECT 必须与出参声明一致 | 悬空引用 04004；List 接单对象 → `List<Dto> 无法转换为 Dto` 编译失败 |
| G34 | `CREATE_ENTITY` 的实体在 facade api 无 `SingleResponse<Long> create(SingleRequest)` | 构建 40s FAIL：`找不到符号: 方法 create(SingleRequest<…Dto>)` |
| G35 | 实体业务字段配了默认值表达式且 `requireNull=false`（create 时无条件覆盖传入值） | 运行时 `UdcEntityCheckException`，传入值看不见效果 |
| G36 | `DELETE_ENTITY` 模式与字段自洽：CONDITION 模式的条件右值**不能**是节点引用（SelectParam）；SELECT_PARAM 模式不能混带 `app`/`structure`/`condition`/`methodLegal` | publish 被拒 `BOOT_1001 Parameter Error`，**响应 data=null 无字段级提示**，只能二分定位 |
| G37 | 引用槽 `outputName` 不能为空、`nodeInfo.nodeId` 不能悬空（典型：引用 `CHANGE_LIST`——它 output 恒为 null、原地改列表） | publish 被拒 `check=false errors=[(…, '….selectParam.outputName', 'PROPERTY_IS_REQUIRED')]` |
| G38 | 逻辑节点 `type` 必须等于 `actionType`（`BREAK`/`CUSTOM_ERROR`）。解析器按 `MicroFlowNodeTypeEnum.valueOf(type)` 选解析器，代码生成模板按 `node.type` 分发 | **零报错**：构建 SUCCESS、publish 通过、运行 success=true，但节点被静默丢弃（BREAK 实测循环照跑 3/3） |
| G39 | 查询条件 `rightParams` 必须带 `type`（典型错法：把 DSL 的 `{"const":x}` 原样塞进去），`CONSTANT` 还必须带 `value` | **零报错**：条件静默失效，RETRIEVE_ARRAY 返回整张表，多个 SIZE 返回同一个数；只有读侧数据不对 |
| G40 | `CHANGE_LIST.action` 必须在 `ADD/REPLACE/CLEAR/REMOVE` 内（**没有 DELETE**）；CLEAR 不得有 `dataSource`；ADD/REPLACE 必须有；REMOVE 还必须有非空 `countAttrs` | 动作语义不对：CLEAR 带非法 dataSource、REMOVE 删不掉任何元素，构建与运行都绿 |

**G30/G31 判据细节（别再放宽/收错）**：G30 的 path 要求仅限「DTO 字段引用」（id 含 `.`）；
引用 BASIC 标量出参（id 空串，G17 形态）无字段可指，豁免。G31 的出参登记按 walk 顺序，
后续节点才能引用前序；入参名 `_FLOW_INPUT_` 前缀跳过悬空检查（G18 已管前缀）。
★ G31 字段级引用：`position=="children"`（CONVERT_DATA 的 selectParam、字段映射右值）
的 dataType 是**字段**类型，不是出参（DTO 容器）类型，不参与 dataType 比对——
只查 outputName 存在性。见「引用 dataType=STRING 与出参 DTO 不一致」先看是不是字段级引用。

### G32 CONVERT_DATA 五子模式形态（构造器 `microflow_nodes_v2.convert_data`）
convertType.value 枚举：Split/multiAssociation2List/List2multiAssociation/String2Long/BasicData2String；
校验源形态 + 目标形态（convertType 与 output 三处一致）+ regex 规则（仅 Split 必带，
枚举 COMMA/DIVLINE/SLASH/PERIOD/MIDLINE；其余子模式带 regex 即拦）。
相关 casing 事实：保存态 output.dataType 恒大写，回读态首字母大写，校验按 `.upper()` 归一。

★ **出参三件套必须一起改：`type` / `dataType` / `javaType`。**
只改前两个、留着模板的 `javaType=java.lang.String` 时，代码生成按 String 声明变量，
运行期赋 Long → **构建 41 秒编译失败**：`不兼容的类型: java.lang.Long无法转换为java.lang.String`。
各子模式的 javaType（114 条语料）：Split / List2multiAssociation / BasicData2String → `java.lang.String`；
multiAssociation2List / String2Long → `java.lang.Long`。G32 已把 javaType 纳入校验。

### G34/G35 写实体可写性（能力表 `core/facts/udc/microflow/entity-write-capability.json`）

这两条拒的是「选错实体」，不是「构造器写错」，靠试跑永远定位不到：
G34 在编译期炸（构建 40s FAIL），G35 在运行时静默盖值（错误看起来像构造器 bug）。

能力表由 `scripts/entity_write_capability.py <metadata.zip>` 从构建产物扫出。
**缺表时两条闸门必须静默跳过**（`_ENTITY_CAPS is None`），不能因为缺证据就把全量流程拦掉。

★★ **能力表产出后必须做阳性对照，否则扫描口径错会静默给出一张全错的表。**
扫错的形态不是报错，而是「所有实体 `has_create=false`」或「所有实体表达式数 0」——
看起来完全合理，后果是 G34 拦掉全部流程（或一条不拦），而且没人会怀疑闸门。
实测踩过两次，都是路径匹配口径问题：

```
glob('**\\facade\\**\\*AppService.java')   Windows 下多段 ** 匹配不到 → has_create 恒空
glob('**\\*AppService.java') 再判 '\\facade\\'   目录名其实是 <app>-facade，判不到 → 同样恒空
```

正确口径：先粗匹配 `**/*AppService.java`，再按**路径子串 `-facade`** 过滤（模块目录叫
`<app>-facade`，不是 `facade`）；domain service 同理按 `/domain/service/` 子串过滤，
且必须先归一化分隔符（`p.replace(os.sep, "/")`）。

扫描脚本必须自带三档自检，不通过就以非零退出码报出来：

```
① 有 create 的实体数 > 0          ← 为 0 一定是口径错，不是真的一个都没有
② 已知有 create 的实体在集合里      ← 拿一个确定挂过写节点的实体做阳性样本
③ 已知被覆盖的字段出现在 fields 里  ← 否则 G35 永远不报
```

⚠ **能力表是构建产物快照，会过期**：实体新增字段 / 新增默认值表达式 / 新建实体后，
表里还是旧数据，G34/G35 拿旧表判新流程等于没判。触发重扫的时机：
**新建或改过实体之后、给新应用写第一批写节点之前**。表里 `source` 字段只写口径，
不写构建版本，所以无法从表自身判断新旧——靠人工记住这个时机，或比对实体数与当前应用实体数。

★★ **G35 必须豁免系统字段。** `updater` / `creator` / `createTime` / `updateTime` /
`creatorInstitution` / `creatorDepartment` / `creatorPost` / `draft` / `id` 上的表达式是平台惯例
（修改人=当前用户），业务本来就不该给它们赋值。不豁免的后果很实际：
**有 `create` 且业务字段干净、恰恰最适合拿来做写验证的实体（表达式只剩 `getUpdater`）
会被自己的闸门拦掉** —— 实测这类实体占多数，误报等于把可用候选清空。
白名单位于 `gates._SYSTEM_EXPR_FIELDS`。

闸门自检四档（改这两条后必跑）：无 create → G34 拦；业务字段被覆盖 → G35 拦；
只剩系统字段表达式 → 放行；两者都没有 → 放行。
已固化为 `tests/test_gates_entity_write.py`，六条测试覆盖四档 + 能力表完整性。

### G33 CALL_DATA_FLOW（构造器 `microflow_nodes_extra.call_data_flow`）

dataFlow.id 与 dataFlowMappingId 一致、dataSourceType 仅 CONDITION（选择数据形态无样本不放行）、
condition 非空、structure 必带、output 恒平台固定 CallDataFlowResultDto。
规则列表必须经 `LiveRefs.data_flow_candidates`（按 sourceEntityId 动态查），不许硬编码规则 id。

**两个 id 到底填哪个 —— 三个证据同向，别再发明第三种写法：**

1. 设计器保存时的 `merge` 规则（前端 bundle）：`merge:{dataFlowMappingId:"dataFlow.id"}`
   → 平台自己保存的节点里两者**必然相等**；「dataFlow.id 放规则 id、mappingId 放行 id」这种分离写法
   平台产生不出来。
2. 运行时 `CallDataFlowActivity.parseActivityNode` **只读 `dataFlowMappingId`**（再加
   `structure.entityId` / `dataSourceType` / CONDITION 模式的 `condition` / `output`），
   `dataFlow` 整个对象不参与解析，是纯 UI 字段。
3. 存在性校验集合的元数据键名是 `data-flow-mapping-id-used-by-micro-flow`，由
   `DataFlowMappingDto.getId()` 填充 → 值必须 = **DataFlowMapping 主键**，
   即 `udcDataFlowListManuallyMappingPost` 列表行的 `id`（不是 `dataFlowId`）。

读书侧：`udc_rt_data_flow_log`（`dataflow_id` / `dataflow_mapping_id` / `is_success` /
`node_input` / `node_output` / `trace_id`）—— 平台自己会把 mapping id 记在 `dataflow_mapping_id` 里，
这是判「id 选对了没有」最快的依据。

★ **G33 曾被复制进 `run_gates` / `run_end_gate` / `run_leak_gate.scan` 三处**，同一违规报 3 次
（「G33 拦 6 项」其实是 2 条 × 3 份）。看到某闸门一次报多条相同内容，先查它是不是被复制进了别的 gate 函数；
`tests/test_gates_g33_data_flow.py` 已守住「同一违规只报一次」。

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

- 定位：先 `grep -n '^def '` 列出**全部函数边界**，确认 `run_gates` 的起止行号，再按行号区间放；
  只在脑海里有「G33 之后」这个概念就动文字锚点，必然插到隔壁函数。
  `gates.py` 里有 5~6 处一模一样的 `    return problems`，文本锚点天然不唯一。
- 精确定位：`ast.parse` 取目标函数节点的 `lineno/end_lineno`，插在它最后一个 `ast.Return` 之前。
- 复验：写盘后再 `ast.parse`，断言每个 G 编号出现在 `ast.get_source_segment(全文件, 目标函数)` 里。

  ```python
  import ast
  src = open("components/udc/microflow/gates.py", encoding="utf-8").read()
  tree = ast.parse(src)
  fn = next(n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "run_gates")
  body = ast.get_source_segment(src, fn)
  for g in ("G34", "G35"):           # ← 本次新增的编号全部列上
      assert g in body, "%s 插到了 %s 外面，规则永不执行" % (g, "run_gates")
  ```

  这段不是形式主义：**只凭「grep 到 G33 之后」就插，实测会落进 `run_leak_gate`**，
  而 import 正常、py_compile 正常、AST 里也能搜到规则文本，4/4 注入回归全 MISS，
  现象长得像「判据写错了」。跑完断言再调一次 `run_gates` 拿一个应当被拦的样本实测，
  两重都能过才算插对了。
- **`_walk_nodes()` 收的是节点 LIST，不是 schema dict。** 写成 `_walk_nodes(schema)` 时
  迭代出的是字典的键（字符串），全被 `isinstance(n, dict)` 跳过——规则**静默 0 命中**，
  测试全绿、注入样本也不报，现象和「判据写错」完全一样。正确写法 `_walk_nodes(schema.get("nodes"))`。
  新增规则的验收口径因此必须是：**手工拼一个该被拦的 schema 跑 `run_gates`，必须报出该 G 编号**，
  不能只看「没报错」。
- 排障次序：注入全 MISS 时**先查「规则是否在该函数体内」**，再查「遍历有没有真走到节点」，最后查判据逻辑。
- 剪走代码块后要补回被剪函数的 `return`——否则该函数返回 None，调用处抛
  `'NoneType' object is not iterable`（组装器 `finish()` 会连带失败）。
- **gates.py 与 node_contracts.py 是内容高度相近的近亲文件**（前者 G1–G31 主闸门，
  后者契约表 + check_contracts）。patch 前用 `s.count(old)==1` 确认锚点在目标文件唯一
  （不许只判 `in`），写盘后 `git status --short` 必须只出现目标文件——
  这对文件发生过整文件互相覆盖，py_compile 与运行时都不报错，只有测试或 git 才暴露。

### ★ 闸门必须用真实生产流程校准，否则误报会挡住业务

**只拿「结构正确的样本」验证闸门是不够的：样本太少时误报发现不了。用整个真实应用的全量已发布流程回归。**

取证命令（只读，不写不改不删）：

```python

### G1 段数判据的正确算法（别再按「2*运算符+1」写）

```python

### 遍历必须 yield CONDITION 自身，不只是它的子节点

```python
for c in n.get("conditions") or []:
    yield c                            # ← 漏这行，所有条件类校验永不执行
    yield from _walk_nodes(c.get("nodes") or [])
```

漏这行的后果：G12（分支条件校验）看着写了、跑起来 0 命中，注入 `name="wrongBranch"` 也检不出来——**假通过比报错更危险**。判据：往样本里注入一个非法条件，闸门必须报；报不出来就是遍历漏层。

### 引用有两类载体，只扫值槽位会漏一半

```python

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

### 契约表 required/present 语义与出参 type 按语料裁决

夹具/闸门和语料冲突时改闸门（或夹具），别给语料没见过的形态立规矩：

- **键可空但必须在**（契约表用 `present` 不是 `required`）：CREATE_LIST 的 structure/value
  （BASIC 731 条 structure=null）。判成 required 会让合法形态永远过不了闸门。
  ★ 但**不要把这个语义套到 DELETE_ENTITY 的 selectParam 上**：曾经写 `present=["selectParam"]`
  并注「CONDITION 8/8 selectParam=null（键在即可）」，实测全量 fixtures 的 8 个 DELETE_ENTITY
  样本**含该键的是 0 个**——注释与语料自相矛盾，照它生成会被自己的闸门拦死。
  查「键可空但必须在」时，判据是**键存在但值为 null**，不是**样本里根本没有这个键**；
  两者差一个字，后果是全部删除节点无法发布。
- **出参 type**：CREATE_LIST 恒 ARRAY（237 条无例外）；LIST_OPERATION 按操作
  （SIZE 计数出标量 OBJECT，过滤/去重出 ARRAY）。
- **触发节点（start_node）必须带 `paramType`**（无入参 NONE / 有入参 CUSTOM，语料 MANUAL
  全带此键）**和 `desc`**（入参显示名）——缺键 C-触发拦，设计器「参数名称」空黄框。

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

