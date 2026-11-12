# 微流程映射类节点语义契约（B-6）

> 切片：B-6（P2 子片）｜ 环境：test2 ｜ 应用参照：`datamigration9000000000000000001`（appId `8704025620829192834`）
> 写授权：**0 写** ｜ `/service` 调用：**0 次**（全部取自 DB 只读 + 已落盘样本 + CFR 反编译）
> 证据分级：SAMPLE / STATIC_BYTECODE / LIVE / UNVERIFIED（严格区分，禁混用）
> 基准 commit：见 §9「版本与状态锚点」（引用行号前请先核对 HEAD 与 `git status`）

---

## 0. 一页结论

微流程里的"映射"是**三种不同节点**，不是一个功能：

| actionType | 中文名 | 角色 | 关键字段 | 落表 |
|---|---|---|---|---|
| `CREATE_MAP` | 创建映射组 | **造**一个 Map（键值对集合） | `output.dataType=MAP` + `generics{keyType,valueType}` + `entries[]` | 不落表，存 `data_schema.nodes[*]` |
| `MAP_OPERATION` | 映射操作 | **读/写** Map（按 key 取值/放值） | `operationType` + `selectMap`（指向来源 Map）+ `theKey` | 同上 |
| `DATA_MAPPING` | 数据转换 | **DTO/实体级字段映射**（源字段→目标字段） | `mappingRule.mappingRows[]` + `structure` + `targetType` | 同上 |

**三个最容易踩的坑（本文档主要价值）**

1. **分母口径有三层，不是一层**（本切片最重要的产出）：
   - **第 0 层 · 应用范围**：先问「**哪个应用**」。本应用 `8704025620829192834` 只有 **9 个**映射节点；全库 4755 行微流程有 **42 个**。混用会差 4.7 倍。
   - **第 1 层 · 遍历位置**：只读 `data_schema.nodes[*]`；任意深度求 `actionType` 会把引用碎片算进来。本应用 9 → 10（差 1，与 B-5 同量级）；全库 42 → 244（差 202）。
   - **第 2 层 · 去重主键**：主键必须是 `(微流程 id, nodeId)`。全库有 **848 个名称**对应 1811 行同名不同 id 的微流程，按 name 去重会把 42 掉到 37；**本应用 0 个同名组，按 name 去重仍是 9**。
2. **`mappingType` 不属于映射节点**：本应用 9 个 + 全库对照（R3）131 个映射节点中**含该字段的 0 个**（R1 的 42 集合上同样是 0/42，两口径均否证成立）。它是**变量/调用类节点**的参数装配方式枚举（`attrs`/`value`/`mapping`）。拿它去描述映射节点是错的。
3. **`mappingMode` 有两套完全不同的取值域**：微流程 `DATA_MAPPING.mappingRule.mappingRows[].mappingMode` = `REFERENCE`/`CONSTANT`；数据流 `dataflow.mappingRow[].mappingMode` = `FieldCopy`/`Formula`/`Sum`… 共 11 种。**同名不同义，不可互换**。

---

## 1. 分母口径（先说死，全文唯一）

### 1.0 【首要】三层口径，按顺序写死

> **纪律**：报任何映射节点数字前，必须同时声明三件事：**哪个应用 / 只读哪个位置 / 用什么主键去重**。
> 只写一个数字不说这三项，等于没写。

| 层 | 问题 | 本应用 `8704025620829192834` | 全库 4755 行 | 差 |
|---|---|---|---|---|
| **0 应用范围** | 哪个 `app_id`？ | **9** | 42 | 4.7× |
| **1 遍历位置** | 只读 `nodes[*]` 还是任意深度？ | 9 vs **10**（差 1） | 42 vs **244**（差 202） | — |
| **2 去重主键** | `(mf id, nodeId)` 还是 `(name, nodeId)`？ | 9 vs **9**（无同名组） | 42 vs **37**（848 名称同名） | — |

**本文档的权威分母 = 9（本应用，主键 `(mf id, nodeId)`）**。
下文的 131 / 244 / 37 / 42 一律是**全库对照**，不是本应用事实。凡引用本应用数字，只能用 9。

### 1.1 唯一正确口径（D37 定稿三层）

**映射类节点 = `WHERE app_id = 8704025620829192834` 下、递归遍历 node 容器（含 `nodes[i].conditions[j].nodes[k]` 分支内嵌套）、跳过引用位 `REF_SLOTS={nodeInfo, selectParam, selectMap, selectEvent}`，主键 `(udc_microflow_info.id, node.nodeId)`。**

> **口径修正留痕（main D37 指出，我独立复现确认）**：我初版只读 `nodes[*]` 顶层，**会漏掉分支条件里嵌套的节点**。
> 全库 R3（递归跳REF）= 131 vs 我 R1 = 42：**有 89 个真节点嵌在 `nodes[i].conditions[j].nodes[k]`**，我全漏了。
> **本应用 R1 与 R3 恰好都是 9** —— 本应用 47 行微流程中没有分支内嵌套映射节点，所以本应用数字没受影响（复现：`_attic_pending/legacy-audit/b6_r3check.py`（**已移入 `_attic_pending/legacy-audit/b6_r3check.py`**，仓库内已无此路径））。
> **教训**：「只读 nodes[*]」和「任意深度」都不对；正确位置是"递归 node 容器但跳过引用位"。引用位（`selectParam` 等）里的 `actionType` 是引用快照的碎片，不是节点。

#### 为什么要排除 REF_SLOTS —— 三条实证（不只是"看起来像引用"）

**① 壳里存的是"指针 + 上下文快照"，不是纯指针**（113 个壳的键数分布）
```
3 键 89 个:  ['actionType','nodeId','type']
4 键 24 个:  ['actionType','entityCaption','nodeId','type']   ← 多一个 entityCaption
```
4 键壳多带 `entityCaption`（实体标题快照），说明写入时把"上下文"一起抄了进去。

**② 113 个壳的直接父键 100% 是 `nodeInfo`**
```
直接父键分布: {'nodeInfo': 113}
```
`selectMap` / `selectParam` / `dataSource` 只是外层容器，壳本体永远挂在 `nodeInfo` 下。

**③ 关键实证：10 个壳指向的节点已不存在（悬空引用）**
```
孤儿（用真映射节点 id 集判定）  = 10
孤儿（用真节点任意类型 id 集）  = 10
```
**如果壳是活指针，平台不会允许它指向不存在的节点。壳能悬空 → 壳是写入时刻的快照，源节点被删后不会同步清理。**

> **这条比"3 键还是 4 键"重要得多**：它是"引用快照"论点的实证，不是推测。
> 也正是 REF_SLOTS 必须排除的根本理由 —— 一个连目标都可能已不存在的壳，怎么可能是一个"节点"？

### 1.2 A/B/C 对照

**本应用（LIVE，47 行微流程）—— 权威口径**
```
A 口径 occurrence = 9
  按 actionType: {DATA_MAPPING: 6, MAP_OPERATION: 2, CREATE_MAP: 1}
  唯一 (mf id, nodeId) = 9   ← 无重复，occurrence == unique
  覆盖微流程 id = 6 / 本应用微流程行数 47
  宿主 state: {10: 7, 20: 2}
  同名不同 id 组: 0（按 name 去重仍 9）
B 口径（任意深度）occurrence = 10
  → 差 1，与 B-5 的 255 vs 254 同量级
```

**全库（LIVE，4755 行）—— 仅作对照，不适用于本应用**
```
R1 顶层 nodes[*]      occ= 42 uniq= 42 {DATA_MAPPING:12, MAP_OPERATION:18, CREATE_MAP:12}   ← R1 口径（已废弃，仅对照）
R2 任意深度           occ=244 uniq=139 {CREATE_MAP:101, MAP_OPERATION:93, DATA_MAPPING:50}
R3 递归+跳REF（D37定稿）occ=131 uniq=131 {CREATE_MAP:30, MAP_OPERATION:75, DATA_MAPPING:26}
按 (name, nodeId) 去重 = 37（848 个名称同名，掉 5）
```

| 口径 | 做法 | 本应用 | 全库 | 判定 |
|---|---|---|---|---|
| **R3** | 递归 node 容器（含 conditions 嵌套）+ 跳过 REF_SLOTS 引用位 | **9** | **131** | ✅ **唯一正确（D37 定稿）** |
| R1 | 只读 `nodes[*]` 顶层 | 9（本应用恰好无嵌套） | 42 | ❌ **漏分支内嵌套节点**（全库漏 89 个） |
| R2 | 对全 `data_schema` 任意深度求 `actionType` | 10 | 244 | ❌ 含引用碎片 |
| C | 按 `(name, nodeId)` 去重 | 9 | 37 | ❌ 跨版本重复计 |
| D | 不限 app_id（把全库当本应用） | — | 42/131 | ❌ **错 4.7~14 倍（我初稿犯的错）** |

> **R1 为什么在本应用"恰好对"**：本应用 47 行微流程没有分支内嵌套映射节点（R1=R3=9），但这**不能推广**——全库 R1 漏 89 个真节点。
> 本切片的 SELF-CHECK `_attic_pending/legacy-audit/b6_r3check.py`（**已移入 `_attic_pending/legacy-audit/b6_r3check.py`**，仓库内已无此路径） 同时输出 R1/R2/R3 三口径，读者可自行验证。

#### 1.2c 对 auditor「本应用漏 68%」质疑的正式回应（main D39 裁定：9 正确）

**质疑原文**：auditor REVIEW_FEEDBACK（202006）主张本应用应为 131、我漏了 89 个真节点，
决定性证据是微流程 `MFSERVICERD1uB6` 的 `BRANCH_9Np2J1` 分支臂内嵌两个映射节点。

**我的核实（`_attic_pending/legacy-audit/b6_auditor_claim.py`（**已移入 `_attic_pending/legacy-audit/b6_auditor_claim.py`**，仓库内已无此路径）（**已移入 `_attic_pending/legacy-audit/b6_auditor_claim.py`**，仓库内已无此路径），LIVE）**：
```
MFSERVICERD1uB6  id=-9063453479472505266  app_id=3289082814923688017  state=20
                                        ↑ 不是本应用 8704025620829192834
全库 89 个内层节点按 app_id 分布：
  3289082814923688017: 25 / 5791640252914287064: 35 / 1656355078954763084: 2
  2378987216360786643: 21 / 6570299241515796755: 5 / 7001530513149673721: 1
  8704025620829192834: 0        ← 本应用零个
```
→ **89 个分支臂内节点全部属于其他 6 个应用，本应用一个都没有。**
→ 本应用 R1=9 与 R3=9 完全一致，不是"恰好"，是**确实没有嵌套**。
→ 「漏 68%」在全库成立、在本应用是**漏 0 个**。

**结论**：本应用权威值 = **9** 不变；131 是全库对照值，不可当本应用结论。
（这是「第 0 层应用范围」第二次证明自己的必要性——auditor 的取证技术上完全正确，
只是取证对象是别的应用。他的 `MFSERVICERD1uB6` 属于全库 1788 行的大应用。）

#### 1.2d R3 的内部构成（我的独立实测，与 auditor 预取证有三处细节不一致）

131 = 42（顶层）+ 89（分支臂内），113 = 引用壳。**总量三项与 auditor 完全一致**，但内部分布我实测不同：

| 项 | auditor 预取证 | 我的实测（`_attic_pending/legacy-audit/b6_auditor_claim.py` + `_attic_pending/legacy-audit/b6_refshell.py`（**已移入 `_attic_pending/legacy-audit/b6_refshell.py`**，仓库内已无此路径）） |
|---|---|---|
| 引用壳宿主键名 | selectMap 54 / selectParam 47 / nodeInfo 12 | **nodeInfo 113（100%）** ← 双方已确认此项我对 |
| 引用壳键数 | 3 键壳 | **3 键 89 + 4 键 24** ← 双方已确认此项我对 |
| 孤儿引用 | **10 个** | ~~0 个~~ ← **此项 auditor 对、我错，见下方订正** |
| 内层节点 `runAfter` | deep 0/89（值口径） | **键 75/89 / 值非 None 0/89** ← 两者都对，口径不同 |

**差异不影响 131/113/89 三个总量**，故 §1.1 的 R3 口径与权威值 9 均不受影响。
**但分布表不可照抄**：本契约一律用我实测值，并保留此对照，供 auditor 复核时定位分歧。

**关于 `runAfter`（main D43 最终裁定：auditor 对，我按键判定会误导）**
```
全库 deep（89 个内层映射节点）：
  含 runAfter 键     = 75 / 89
  runAfter 非 None   =  0 / 89      ← 89 个值全是 None
  含 input 键        = 75 / 89
  含 name 键         = 75 / 89
顶层 42 个（R1 口径）：有 runAfter 键 35/42，值同样全部为 None
```
→ 这 75 个是「**带完整编排字段骨架**」的节点（`input`/`name`/`runAfter` 三键同批出现），**字段骨架被写入、值未填**。
→ 75 是这批节点的计数，**不是 runAfter 特有**。
→ **定序不依赖 `runAfter`，分支臂内按 `nodes[]` 数组顺序执行**（顶层同理：runAfter 也全 None）。
→ **不可用「`runAfter` 有键」证明平台使用该字段定序；判据必须是值非 None。**

> **main D43 撤销了他 D42 的判定**：D42 曾据此说「auditor 的推论不成立」，D43 更正为「auditor 的推论成立，是我判错」。
> 我保留这段留痕，因为**"按键 vs 按值"这个分歧本身**就是 §11.6 那条方法论的来源。

**关于孤儿引用（此项 auditor 对、我错，已订正）**
我上版报「0 个孤儿」，**那是循环论证的产物**。根因在我的 `_attic_pending/legacy-audit/b6_refshell.py`（**已移入 `_attic_pending/legacy-audit/b6_refshell.py`**，仓库内已无此路径）：
```python
def collect(o):
    if isinstance(o, dict):
        if 'nodeId' in o: allids.add(o['nodeId'])   # ← 把引用壳自身的 nodeId 也收进去了
```
判定 `if o['nodeId'] not in allids` 时，壳自己的 nodeId 就在 `allids` 里 → **orphans 恒为 0**。

**正确口径实测（`_attic_pending/legacy-audit/b6_orphan_truth.py` + `_attic_pending/legacy-audit/b6_orphan_3ways.py`（**已移入 `_attic_pending/legacy-audit/b6_orphan_3ways.py`**，仓库内已无此路径））**
三种口径全部跑过，这是澄清 main D42 与 auditor 分歧的关键：

| 口径 | 参照集合 | 规模 | 孤儿 |
|---|---|---|---|
| **A** | 全库**任意 dict** 的 `nodeId`（**含引用壳自身**）← 我的 bug | 32928 | **0**（恒为假） |
| **B** | 全库**真节点**（`type=ACTIVITY` 且非引用位） | 18447 | **10** |
| **C** | **同一微流程内**的真节点 | 按流程分 | **10**（涉及 7 个微流程） |

**B 与 C 是同一个集合**（`setB == setC` 为 True，双向差集皆空）：
```
真【映射类】节点 nodeId = 101
孤儿 = 10（B、C 两口径逐条相同）
```

> **对 main D42 推定的一处更正**：D42 认为「按全库 nodeId 全局集合匹配 → 0；按微流程内匹配 → 10」，
> 并据此说我的 0 是因为"用了全局集合、而同名 nodeId 跨微流程指向不同节点"。
> **实测不是这样**：全局匹配用**真节点**集合（B）同样得 10，与微流程内（C）完全一致。
> 我的 0 只有一个原因——**参照集合混进了壳自身**（A 口径 32928 个）。
> 结论不变（孤儿 = 10），但**根因要写对**：这是循环论证，不是"全局 vs 局部"的口径选择问题。
>
> **业务上仍建议按微流程内判定**（与 §1.4 第 2 层主键 `(mf_id, nodeId)` 同一道理）：
> 引用壳的语义是"本流程节点引用了本流程内的一个节点"。只是在本数据集里两种口径恰好同解。

**这 10 个孤儿的业务意义（比"3 键还是 4 键"大得多）**：
**如果壳是活指针，平台不会允许它指向不存在的节点。壳能悬空 → 壳是写入时刻的快照，源节点被删后不会同步清理。**
这是「引用快照」论点的**实证**，不是推测。已写入 §1.1 作为 REF_SLOTS 排除逻辑的业务依据。

### 1.2b 本应用 9 个映射节点全景（权威清单，LIVE 逐条）

| # | 微流程（name / id / state） | nodeId | actionType | 关键字段实值 |
|---|---|---|---|---|
| 1 | `xzhFinalAllNodes` / `-1014184770817921434` / 10 | `CREATE_MAP_n6a` | CREATE_MAP | `output.dataType=MAP`、`javaType=java.util.Map`、`key=String/value=Object`、`entries=len 1` |
| 2 | 同上 | `MAP_OPERATION_n7` | MAP_OPERATION | `operationType=GET`、`theKey=SelectParam`（**动态键**）、`output=STRING` |
| 3 | 同上 | `DATA_MAPPING_n8` | DATA_MAPPING | `targetType=ENTITY`、**`node.structure.dataType=DTO`**、3 行全 REFERENCE |
| 4 | `xzhStdReal31046` / `-3790333238868911627` / 10 | `MAP_OPERATION_x7` | MAP_OPERATION | `operationType=GET`、`theKey="expText"`（**字面量键**）、`output=STRING` |
| 5 | 同上 | `DATA_MAPPING_x8` | DATA_MAPPING | `targetType=ENTITY`、**`node.structure.dataType=DTO`**（非 None）、`mappingRule.javaType` 缺键（见 §4.2b）、1 行 `mappingMode=None` |
| 6 | `xzhSvcEvtBpDA` / `1524985498115296151` / 10 | `DATA_MAPPING_b3OtRj` | DATA_MAPPING | 3 行全 REFERENCE |
| 7 | `xzhSvcDefK4Ge` / `862673936068342178` / 10 | `DATA_MAPPING_8EZQEb` | DATA_MAPPING | 3 行全 REFERENCE |
| 8 | `xzhSvcSchcHXa` / `-8675485534859429311` / 20 | `DATA_MAPPING_zNjd5K` | DATA_MAPPING | 3 行全 REFERENCE |
| 9 | `xzhRestMf` / `-5161505652062878096` / 20 | `DATA_MAPPING_bbb222` | DATA_MAPPING | 2 行：REFERENCE + **CONSTANT** |

> **本应用唯一同时含 CREATE_MAP + MAP_OPERATION 的微流程是 `xzhFinalAllNodes`**（节点 1/2 成对：造 Map 再取 key）。这是全应用唯一的"造-取"完整链路，也是本切片唯一的端到端样本。
> `DATA_MAPPING` 有 6 个，**与 CREATE_MAP/MAP_OPERATION 无任何数据依赖**（§6 结论在本应用同样成立：`xzhFinalAllNodes` 里的 `DATA_MAPPING_n8` 与同流程的 CREATE_MAP 不共用 Map）。

### 1.3 用错各层口径的具体业务后果

**第 0 层用错（不限 app_id）—— 我初稿就是这个错**
本应用真实 9 个，我按全库报 42，**虚高 4.7 倍**。后果：把别的应用（`3289082814923688017` 独占 1788 行）的节点算成本应用覆盖率，工作量估算和"还剩多少没闭合"的判断全错。**这是本切片最该记住的一条**（我自己犯了）。

**第 1 层用错（任意深度）**
- 本应用：9 → 10（多 1 条）。量级小，但**结论会错**——多出的那条是引用碎片，被当成独立节点会得出"本应用有 2 个 CREATE_MAP"，实际只有 1 个。
- 全库：42 → 244（虚高 5.8 倍）。
多出的都是别的节点在 `selectParam`/`nodeInfo`/`mappingRow.source` 处对映射节点的**引用快照**（键少、无 `entries`、无 `output`）。

**第 2 层用错（按 name 去重）**
全库：42 → 37，且**同一逻辑节点被算两次**（同名组两版本各有同一 nodeId）。本应用因无同名组，此层恰好不影响（9→9）——**这正是"错口径在本应用看不出问题、换应用就爆"的典型**。

3. **与 B-5 同型**：B-5 的 255 vs 254 也是这个病根——**递归全树求 `type`**。本应用这一层只差 1（与 B-5 完全同量级），全库差 202。

> **口径纪律（沿用 B-5 沉淀，已进模板并加两层）**：统计某类节点前必须按顺序问三句——
> ① 「**哪个应用**？」（app_id 过滤了吗）
> ② 「**这个 dict 在 JSON 树的哪个位置**？」（`nodes[*]` 还是任意深度）
> ③ 「**用什么主键去重**？」（`(id,nodeId)` 还是 `(name,nodeId)`）
> B-5 只沉淀了第 ②。本切片补 ①③。

### 1.4 第 2 层陷阱详解：主键是 `微流程 id`，不是 `名称`（**本应用不触发，全库触发**）

> **重要限定**：本节全部数据是**全库**口径，用于说明机制。**本应用 0 个同名组**，按 name 去重仍是 9。
> **本节底座为 R1（顶层 42 个）**：主键层（第 2 层）与遍历位置层（第 1 层）正交，为隔离变量、清晰演示主键陷阱，本节固定 R1 底座。R3=131 口径下的主键影响未单独统计（本应用 0 同名组，此层不触发，故不补）。

> **⚠️ 另注｜本节 `state 10 vs 20` 的「疑为草稿/发布态」已撤回**：state 与 `publish_state` 正交（state=10 的 289 行 publish_state 100%=1；未发布的 21 行全在 state=20），故 **state 不是发布态**。state 真实语义 → UNVERIFIED，转 B-7 专项。
> **→ 已于 B-7 解出（2026-10-18）**：`MicroFlowDataStateEnum{DRAFT=10, RELEASE=20}`（字节码 `bipush` 实证，无第三常量）。详见 `state-semantics.contract.md`。

**LIVE 事实（全库 4755 行）**
```
id 唯一性：COUNT(*)=4755，COUNT(DISTINCT id)=4755，重复 id=0  ✅
但同名多行（不同 id）：848 个名称、涉及 1811 行
  top: SendEmail×6, findDivisionPlaceEmp×5, MFFRONTENDPZCldG×4, zVAAJupL×4, getProgressByPlan×4
微流程 state 分布（全库）：{10: 289, 20: 4466}
本应用 47 行 state 分布：{10: 5, 20: 42}
```

即：**名字相同、id 不同、`state` 不同的多行并存**（`state` 10 vs 20，**语义 UNVERIFIED**；见上方另注：state 不是发布态）。

**对映射节点分母的实际影响（全库）**
```
全库 R1 顶层 42 个映射节点分布在 28 个微流程 id 上（R1 已废弃，仅作主键陷阱示例）
其中 8 个 id 属于「同名不同 id」组
映射节点按宿主 state：{20: 28, 10: 14}
按 (name,nodeId) 去重 = 37（掉 5）
```

具体重复例（同名组内各版本的 nodeId 相同）：
| 名称 | 行1 (id/state) | 行2 (id/state) | 重复的映射节点 |
|---|---|---|---|
| `MFSERVICEvmSOMc` | `572045621955740633` / 20 | `3797473186029205522` / 10 | `CREATE_MAP_4X4hvH` ×2 |
| `DVrcsWim` | `702356282473990443` / 10 | `5926205502586948111` / 20 | `CREATE_MAP_aqyeRf` ×2 |
| `MFSERVICE8ZJ0fl` | `7324760583848674536` / 20 | `7878379418393967590` / 10 | `MAP_OPERATION_5PI8Id` ×2、`MAP_OPERATION_AoEBJU` ×2 |

**用错主键的后果**（示例用 R1 顶层口径的 12/18 说明机制，R3 全量下同理）：若以"微流程名称"为 key 去重，`CREATE_MAP` 会从 12 掉到 10、`MAP_OPERATION` 从 18 掉到 16，且**同一逻辑节点被算两次**（两版本各有同一 nodeId）。
**正确做法**：以 `(微流程 id, nodeId)` 为主键计数；若业务上要"每个逻辑微流程只算一次"，必须先定义**取哪个 state 版本**（本切片不定义，标 UNVERIFIED）。

> **与 B-5 的区别**：B-5 的 255 是"**位置**错"（把引用当节点）；B-6 这里多出的是"**主键**错"（把同名不同 id 当同一个/或重复计）。两种都会让分母漂移，但修法不同：前者改遍历位置，后者改去重键。

---

## 2. CREATE_MAP —— 创建映射组

### 2.1 字段结构（SAMPLE，`CREATE_MAP_n6a`）

```json
{
  "nodeId": "CREATE_MAP_n6a", "type": "ACTIVITY", "caption": "创建映射组(1)",
  "actionType": "CREATE_MAP",
  "title": "映射组_1",
  "output": {
    "dataType": "MAP", "javaType": "java.util.Map", "type": "OBJECT",
    "name": "_CREATE_MAP_n6a", "desc": "实体属性映射",
    "generics": {
      "keyType":   { "dataType": "String" },
      "valueType": { "dataType": "Object", "javaType": "java.lang.Object" }
    }
  },
  "generics": { "keyType": {"dataType":"String"}, "valueType": {"dataType":"Object","javaType":"java.lang.Object"} },
  "entries": [
    { "key":   { "type": "Simple", "simple": "expText", "desc": "expText" },
      "value": { "type": "SelectParam",
                 "selectParam": { "key": "_RETRIEVE_n2…XzhExp950795Dto.expText", "name": "expText",
                                  "id": "…XzhExp950795Dto.expText", "appName": "datamigration…",
                                  "dataType": "STRING", "javaType": "java.lang.String",
                                  "path": "_RETRIEVE_n2", "outputName": "_RETRIEVE_n2",
                                  "position": "children", "dtoType": "MASTER_ENTITY" } } }
  ]
}
```

### 2.2 `output.dataType=MAP` 与 `generics` 的关系（LIVE 定量）

**本应用（权威，1 个 CREATE_MAP）**
| 观测项 | 本应用 | 全库对照（R3，30 个） | 证据 |
|---|---|---|---|
| `output.dataType` | `MAP` × **1/1** | **30/30** | LIVE |
| `output.javaType` | `java.util.Map` × 1/1 | 30/30 | LIVE |
| `output.generics.keyType.dataType` | `String` × **1/1** | 30/30 | LIVE |
| `output.generics.valueType.dataType` | `Object` × **1/1** | 30/30 | LIVE |
| 节点级 `generics`（与 output 平级） | 1/1 存在，内容同 | 30/30 | LIVE |

> **样本量警示**：本应用只有 1 个 CREATE_MAP，`1/1` 不构成"分布"证据，只能证明"存在这种形态"。**凡"恒为"类断言，本应用样本不足以支撑**——下表 30/30 是**全库**结果，仅在"跨应用一致"意义上可参考，**不可说成"本应用已验证"**。

**语义**：
- `output.dataType = MAP` 声明"本节点产出是一个 Map 对象"（`javaType = java.util.Map`）
- `generics.keyType` / `valueType` 是 Java 泛型参数的**类型标注**：本实例恒为 `Map<String, Object>`
- **`generics` 在节点级和 `output` 级各存一份，内容一致** → 双写冗余。写侧只需保证两处一致；读侧任取其一均可，但**不要假设只改一处会生效**（未验证，见 §7-2）

> **注意**：`output.generics` 的 `keyType.dataType="String"`（大写 S）、`valueType.dataType="Object"`（大写 O），而 `output.dataType="MAP"`（全大写）。**大小写不统一是平台原样，不是笔误**——引用时必须保持原值（B-5 教训：`ObjectTypeEnum.Object` 报 `No enum constant`）。

### 2.3 `entries` 结构与何时非空（LIVE 定量）

| actionType | 本应用节点数 | 本应用有 `entries` | 本应用非空 | 全库(R3) 有/非空 |
|---|---|---|---|---|
| `CREATE_MAP` | **1** | **1** | **1** | 30 / **22** |
| `DATA_MAPPING` | **6** | **0** | 0 | 0 / 0 |
| `MAP_OPERATION` | **2** | **0** | 0 | 0 / 0 |

**结论**：`entries` 是 **CREATE_MAP 专属字段**，另外两类节点根本没有这个键（本应用 8/8 无、全库 30/30 无，两口径一致）。
**本应用唯一的 CREATE_MAP（`CREATE_MAP_n6a`）entries 非空（len=1）**；全库（R3）30 个中有 **8 个**为**空数组 `[]`**（30 个里有 entries 键 22 个非空、8 个空）。

> **订正留痕**：初稿写「5 个 `entries` 为 `null`」，实跑为**空 list `[]`**（`entries == []` 而非 `None`）。二者对下游校验器行为可能不同——`[]` 可迭代、`null` 会 NPE。本文档以实跑为准：**空值形态 = `[]`，全库 30 个 CREATE_MAP 中无一个是 `null`**。

**本应用唯一 CREATE_MAP 的 entries（LIVE）**
```
CREATE_MAP_n6a  (mf=xzhFinalAllNodes id=-1014184770817921434 state=10)  entries=len 1
  entry[0].key.type   = "Simple"       (simple="expText")
  entry[0].value.type = "SelectParam"  (_RETRIEVE_n2 … XzhExp950795Dto.expText)
```

**全库空值形态精确分布（LIVE，R1 顶层 12 个 CREATE_MAP 逐条；非本应用口径、非 R3 全量）**
```
MFSERVICEPPfchB   idx=8  list[15]
xzhFinalAllNodes  idx=6  list[1]
MFSERVICEYRTwx1   idx=2  list[1]
MFSERVICEvmSOMc   idx=2  空list[]      ← 同名组 id=572045621955740633
DVrcsWim          idx=6  list[10]      ← 同名组 id=702356282473990443
MFSERVICEMOEGed   idx=0  list[2]
yTQrbKTP          idx=1  空list[]
MFSERVICEvmSOMc   idx=2  空list[]      ← 同名组 id=3797473186029205522
MFSERVICE3kgGx9   idx=2  空list[]
DVrcsWim          idx=6  list[10]      ← 同名组 id=5926205502586948111
MFSERVICEmss9VD   idx=1  list[1]
EtQbJWYQ          idx=1  空list[]
```
（12 条 = 10 个不同微流程，2 个因同名组各出现两次，见 §1.4）

**entry 内部结构（40 条条目全量统计）**
```
含非空 entries 的节点数: 7   条目总数: 40
  key.type:   {Simple: 40}                    ← 键侧恒为字面量
  value.type: {SelectParam: 38, Simple: 2}    ← 值侧 95% 引用变量，5% 字面量
```

- `key.type = "Simple"` → 键是**字面量字符串**（`simple` 字段存值），40/40 无例外
- `value.type = "SelectParam"` → 值是**对上游节点输出的引用**（`selectParam` 内含 `outputName` + `path` + 完整类型信息）
- `value.type = "Simple"` → 值是字面量（2 条，如 `{"simple":"1111"}`）

> **业务读法**：CREATE_MAP 就是"手工拼一个字典"。键写死，值多数取自上游（`_RETRIEVE_*`、`_CALL_APP_SERVICE_*`、`_FLOW_INPUT_*`），少数写死。

---

## 3. MAP_OPERATION —— 映射操作

### 3.1 权威枚举（STATIC_BYTECODE，`MapOperationTypeEnum`）

来源 `udc-plugin-api-5.3.517.jar` / CFR 反编译 `com/seeyon/udc/enums/microflow/MapOperationTypeEnum.java`：

```java
public enum MapOperationTypeEnum implements Messageable {
    GET(0), PUT(1), REMOVE(2), KEY_SET(3);
}
```

| 常量 | code | 语义（按 Java Map 接口） |
|---|---|---|
| `GET` | 0 | 按 key 取值（`map.get(k)`） |
| `PUT` | 1 | 放键值对（`map.put(k,v)`） |
| `REMOVE` | 2 | 删键（`map.remove(k)`） |
| `KEY_SET` | 3 | 取键集合（`map.keySet()`） |

### 3.2 LIVE 分布

**本应用（权威，2 个 MAP_OPERATION）**
| 字段 | 本应用 | 说明 |
|---|---|---|
| `operationType` | **`GET` 2/2** | `PUT`/`REMOVE`/`KEY_SET` **本应用 0 样本** |
| `output.dataType` | **`STRING` 2/2** | 取自 Map 的单值 |
| `paramType` | **`BASIC` 2/2** | — |
| `nullHandling` | **`CONTINUE` 2/2** | 取不到 key 时继续 |
| `selectMap` 存在 | **2/2** | 必填，指向被操作的 Map |
| `selectMap.dataType` | **`MAP` 2/2** | — |

**全库对照（R3，75 个节点，仅作形态参考）**
| 字段 | 分布 |
|---|---|
| `operationType` | **`GET` 40 / `PUT` 24 / `KEY_SET` 11**（`REMOVE` **全库 0 样本** → VACUUM，但模板定义了 4 值，不可称非法） |
| `output.dataType` | `STRING` 39 / `None` 24 / `DECIMAL` 7 / `BIGINTEGER` 2 / `ENUM` 1 / `DATE` 1 / `MAP` 1 |
| `selectMap.dataType` | `MAP` × 75/75 |

### 3.2b `theKey` 有两种形态（本应用实跑才发现，全库统计会掩盖）

| 形态 | 本应用样本 | 含义 |
|---|---|---|
| **字符串字面量** | `MAP_OPERATION_x7` → `"expText"` | 键写死，取 `map.get("expText")` |
| **`SelectParam` 对象** | `MAP_OPERATION_n7` → `{"type":"SelectParam","selectParam":{…XzhExp950795Dto.id}}` | **键由上游变量决定**，运行时才知道取哪个键 |

> **业务含义差异很大**：字面量键是静态可分析的（能静态推出读的是哪个字段）；`SelectParam` 键是**运行态动态键**，任何"静态推导映射关系"的工具遇到这种形态都无法闭合，必须标 `UNVERIFIED`。
> **为什么全库统计会漏**：全库 `theKey` 我只统计了"是否存在"，没区分形态。本应用 2 个样本里就有 1 个是动态键 —— **这说明 50% 的动态键比例不能外推，但足以证明"必须区分形态"**。

### 3.3 `selectMap` 结构（SAMPLE）

```json
"selectMap": {
  "dataType": "MAP", "javaType": "java.util.Map", "type": "OBJECT",
  "name": "_CREATE_MAP_UuoUjz", "desc": "节点名称-处理人",
  "generics": { "keyType": {"dataType":"String"}, "valueType": {"dataType":"Object","javaType":"java.lang.Object"} },
  "position": "parent", "outputName": "_CREATE_MAP_UuoUjz",
  "nodeInfo": { "nodeId": "CREATE_MAP_ZIXM76", "type": "ACTIVITY", "actionType": "CREATE_MAP" },
  "key": "_CREATE_MAP_UuoUjz_CREATE_MAP_UuoUjz"
}
```

**`selectMap` 是"引用"，不是"定义"**——注意它带 `nodeInfo{nodeId, actionType}` 指回源 CREATE_MAP 节点，且**没有 `entries`**。
> **这正是 §1 分母口径的关键**：`selectMap` 里也含 `actionType: "CREATE_MAP"`，B 口径遍历会把它算成又一个 CREATE_MAP 节点。

### 3.4 `operationType` 与 `output.dataType` 的对应（LIVE 交叉）

| operationType | 观测到的 output.dataType |
|---|---|
| `GET` | `STRING` / `BIGINTEGER`（取出的单值类型） |
| `KEY_SET` | 未见 `MAP` 以外的组合样本；1 个 `MAP` 出现在 `KEY_SET` 之外的形态（见 §7-3） |

> **UNVERIFIED**：`GET` 的 output 类型是否恒等于 map 的 `valueType` 的实际数据类型，样本不足以断言（全库 40 个 GET 里 output 类型有 STRING/BIGINTEGER 等几种，但 `valueType` 声明恒为 `Object`，无法从声明推出实际类型）。

---

## 4. DATA_MAPPING —— 数据转换（DTO/实体级字段映射）

### 4.1 字段结构（SAMPLE）

```json
{
  "actionType": "DATA_MAPPING",
  "targetType": "ENTITY",
  "app": { "appId":"8704025620829192834", "appName":"datamigration…", "caption":"数据迁移", "inApp":true, "udcApp":true },
  "structure": {
    "key": "com.seeyon…domain.entity.XzhExp950795",
    "id": "com.seeyon…dto.XzhExp950795Dto",
    "label": "小爪实验实体950795V2", "dataType": "DTO",
    "entity": "com.seeyon…domain.entity.XzhExp950795",
    "dtoType": "MASTER_ENTITY", "fullName": "com.seeyon…dto.XzhExp950795Dto",
    "relationEntity": "474806313816300867"
  },
  "title": "小爪实验实体950795V2转换",
  "selectParam": { "description":"小爪实验实体950795V2列表", "dataType":"DTO",
                   "outputName":"_RETRIEVE_ARRAY_1", "position":"parent",
                   "dtoType":"MASTER_ENTITY", "appName":"datamigration…" },
  "mappingRule": {
    "uuid": "6730ec9355a840d6aa6d762c0c52f855",
    "targetType": "ENTITY",
    "mappingRows": [
      { "uuid": "b7eefdc8771f427386b0914fe2309ec7",
        "targetField": { "path":["expText"], "name":"expText", "type":"OBJECT",
                         "dataType":"STRING", "javaType":"java.lang.String",
                         "id":"…XzhExp950795Dto.expText", "desc":"expText" },
        "mappingMode": "REFERENCE",
        "value": { "reference": { "path":[], "name":"expText", "type":"OBJECT",
                                  "dataType":"STRING", "javaType":"java.lang.String",
                                  "id":"…XzhExp950795Dto.expText" } } }
    ]
  }
}
```

### 4.2 LIVE 定量

**本应用（权威，6 个 DATA_MAPPING）**
| 字段 | 本应用 | 全库对照（R3，26 个） |
|---|---|---|
| `targetType` | **`ENTITY` 6/6** | `ENTITY` 6 / **`None` 20** ← 应用差异（见下注） |
| `node.structure.dataType` | **`DTO` 6/6** | `DTO` **26/26** — **两口径一致，无差异** |
| `mappingRule.javaType` | **缺键 3/6**（x8/8EZQEb/bbb222） | 缺键 3/26（同 3 个）← **硬约束，见 §4.2b** |
| `mappingRule` 存在 | 6/6 | 26/26 |
| `mappingRows[].mappingMode` | **`REFERENCE` 13 / `CONSTANT` 1 / `null` 1（共 15 行）** | `REFERENCE` 264 / `CONSTANT` 1 / `null` 1（共 266 行） |
| `mappingType` 在 `mappingRule` 上 | **`<缺>` 6/6** | `<缺>` 26/26 |

> **注｜`targetType` 的真实应用差异（这是本轮换出来的、有证据的差异）**：本应用 6/6 全为 `ENTITY`；
> 全库 26 个中只有 6 个为 `ENTITY`、**其余 20 个 `mappingRule` 内无 `targetType` 键**（键缺失，非 null）。
> 成因未查（可能是不同版本/不同入口创建的 DATA_MAPPING）→ **UNVERIFIED**。
> 这条与已删的假事实性质不同：它是**先断言路径存在、再读值**得到的（`mappingRule` 里确实有/没有 `targetType` 键，逐条可核）。

> **✅ 订正（原"应用级差异"是假事实，已删）**：本应用 `node.structure.dataType = DTO` **6/6**，全库 `DTO` **26/26**，**两口径一致，无应用级差异**。
> 原先此处写「本应用 6/6 全为 `None`、全库 12/12 为 `DTO`」并附一条"用 `==DTO` 校验会把 6 个全判无效"的禁令 —— **该禁令与事实相反，已删除。**
> **真实成因（这才是值得留的教训）**：
> 我取的是 `(node['mappingRule'].get('structure') or {}).get('dataType')`，而 **`mappingRule` 根本没有 `structure` 键**（本应用 0/6、全库 0/26，一次都没有）。
> 链式 `.get()` 在路径不存在时返回 `None`，我把它当成了"字段值就是 None"写进契约。
> 节点**顶层** `node.structure.dataType` 才恒为 `DTO`（`node.structure.id` 如 `...dto.XzhExp950795Dto`）。
>
> **方法论（已写入 §11）**：**链式 `.get().get()` 得到的 `None` 既可能是"字段为 null"，也可能是"路径不存在"，两者业务含义完全不同——必须先断言父键存在。**
> 我这条假事实的危险性在于它被标成「必读」「比数字重要」：保守地陈述一个假事实，仍然是假事实，而且因为标了「保守」反而更容易被信。

### 4.2b UNVERIFIED-RISK：`mappingRule.javaType` 缺失（模板硬约束）

| 口径 | `mappingRule.javaType` |
|---|---|
| 本应用（6 个 DATA_MAPPING） | **present 3 / 键缺失 3** |
| 全库（26 个 DATA_MAPPING） | **present 23 / 键缺失 3** |
| 缺失的是哪几个 | `DATA_MAPPING_x8` / `DATA_MAPPING_8EZQEb` / `DATA_MAPPING_bbb222`（两口径同一批） |

**为什么这是硬约束（STATIC_BYTECODE，`DataMappingActivity.java.ftl`）**：
```freemarker
<#assign newMappingRuleJavaType = fullNameTransformer.transform(node.mappingRule.javaType, ...)>
<#assign singleRootDtoName = ...getDtoNameByFullName(node.mappingRule.javaType)>
<#local targetJavaType = fullNameTransformer.transform(mappingRule.javaType, ...)>
```
模板**直接读 `node.mappingRule.javaType`** 做全名转换与 DTO 名推导。
→ `javaType` 缺失时，生成代码拿 `null` 去做转换，属「**用错就生成不出代码**」的硬性分支，**生成器必须显式处理**。

> **注意区分**：模板全文**不读** `node.structure`，也不读 `mappingRule.structure`（后者在 2.9 模板树出现 0 次）。
> `node.structure` 只被其他 actionType 使用（`CreateEntity`/`Retrieve`/`RetrieveArray`/`CreateVariable`，都用 `${node.structure.id}`）。
> 故：**判断 DATA_MAPPING 的 DTO 目标类型应读 `mappingRule.javaType`（而非 `node.structure.dataType`）**——这是我原文档搞反的一处。
>
> **状态**：`javaType` 缺失的 3 个节点在运行态是否真会生成失败，**未做活体验证 → UNVERIFIED-RISK**（0 次 /service 约束下不可证）。

### 4.3 字段映射（源→目标）如何表达

`mappingRows[]` 每个元素是一行映射：

| 字段 | 语义 |
|---|---|
| `targetField` | **目标字段**（含 `path[]` + `id`(全名) + `dataType`/`javaType`） |
| `mappingMode` | 映射方式：`REFERENCE`（引用上游值）/ `CONSTANT`（常量） |
| `value` | 值来源。`REFERENCE` 时是 `value.reference{...}`；`CONSTANT` 时是常量 |

**即：一行 = 一个目标字段 + 一个取值方式 + 一个值来源。** 源侧信息在 `value.reference` 里（`id`/`path`/`outputName` 指向上游节点输出）。

### 4.4 关键否证：`mappingType` 不属于映射节点（LIVE 双口径）

主任务问"`mappingType` 取值与语义"。实测答案是**它不在这三个节点上**：

```
本应用：映射类节点 9 个（R3），含 mappingType 的 0 个
全库：  映射类节点 131 个（R3），含 mappingType 的 0 个   ← 另在 R1 顶层 42 集合上同样 0/42，两口径均否证成立
```

**两个口径都是 0，且本应用 9/9 的 `mappingRule` 里也没有 `mappingType` 键**——否证不依赖样本量。

而 `mappingType` 在全库确实大量存在（1723 个微流程含该键，共 4730 处），但其宿主 actionType 是：

| actionType | mappingType 出现次数 |
|---|---|
| `CHANGE_VARIABLE` | ~1066 |
| `CREATE_VARIABLE` | ~1071 |
| `CALL_MICRO_FLOW` | 929 |
| `SUB_MICROFLOW` | 367 |
| `CREATE_VARIABLE_FRONT` | 318 |
| `END_NODE` | 240 |
| `CREATE_ENTITY` | 218 |
| `CALL_APP_SERVICE` | 189 |
| `CHANGE_VARIABLE_FRONT` | 156 |
| `RETRIEVE_ARRAY` | 85 |
| `PUBLISH_BUSINESS_EVENT` | 72 |
| `CALL_FRONT_FLOW` | 19 |

**取值分布**：`attrs` 3415 / `value` 837 / `mapping` 287 / `null` 191（共 4730）

**语义（STATIC 推断 + 分布佐证）**：这是**参数装配方式**的枚举，描述"该节点的入参是按属性字典给(attrs)、按单值给(value)、还是按映射关系给(mapping)"。典型如 `CALL_MICRO_FLOW.mappingType="attrs"` 表示按目标微流程的入参属性逐项装配。

> **对本切片的结论**：主任务把 `mappingType` 与映射节点并列提问，是个**前置假设错误**（不是提问者的错——B-5 的 `PUBLISH_BUSINESS_EVENT` 确实有 `mappingType`，容易类推）。**映射节点的"映射方式"字段是 `mappingRule.mappingRows[].mappingMode`（DATA_MAPPING）或 `entries[].value.type`（CREATE_MAP），不是 `mappingType`。**

---

## 5. 两套 `mappingMode` 必须分开（最易混淆点）

| 归属 | 字段路径 | 取值域 | 权威来源 |
|---|---|---|---|
| **微流程** | `DATA_MAPPING.mappingRule.mappingRows[].mappingMode` | `REFERENCE` / `CONSTANT` | LIVE（本应用 13/1/1 共15行；全库 264/1/1 共266行） |
| **数据流** | `dataflow.rules[].mappingArea[].mappingRow[].mappingMode` | `FieldCopy` / `Formula` / `Sum` / `Average` / `Count` / `Max` / `Min` / `Splicing` / `FirstLine` / `LastLine` / `FixedValue` | **STATIC_BYTECODE** `com.seeyon.udc.common.mappingmode.MappingMode` 接口常量 |

`MappingMode` 接口常量原文（CFR，`udc` 5.3.517）：
```java
String MAPPING_MODE_FIELD_COPY = "FieldCopy";
String MAPPING_MODE_FORMULA = "Formula";
String MAPPING_MODE_SUM_FUNCTION = "Sum";
String MAPPING_MODE_AVERAGE_FUNCTION = "Average";
String MAPPING_MODE_COUNT_FUNCTION = "Count";
String MAPPING_MODE_MAX_FUNCTION = "Max";
String MAPPING_MODE_MIN_FUNCTION = "Min";
String MAPPING_MODE_SPLICING_FUNCTION = "Splicing";
String MAPPING_MODE_FIRST_FUNCTION = "FirstLine";
String MAPPING_MODE_LAST_FUNCTION = "LastLine";
String MAPPING_MODE_FIXED_VALUE = "FixedValue";
```

**决定性证据**：微流程侧（本应用 15 行 / 全库 266 行）里 `REFERENCE` 占绝大多数 + `CONSTANT` 1，**没有一个**落在上面 11 个常量里；数据流侧 2 行全是 `FieldCopy`。
→ **同名不同义**：微流程的 `REFERENCE/CONSTANT` 是"值从哪来"，数据流的 `FieldCopy/Formula/…` 是"怎么算"。**不可互相套用、不可共用校验器。**

### 5.1 数据流映射结构（SAMPLE，供对照）

> **✅ 输入漂移事件（已处置，D36=B：还原+存档）**
> 本切片引用的两份 `dataflow_mapping_*.json` 是 **main 指定的输入**，曾在 2026-10-17 23:39:25 +0800
> 被写链测试（0043 UPDATE 的 udcDataFlowMappingUpdatePost 请求体）覆盖（git status 变 M、
> 归一化 JSON 与 c3ccb8a 版差异 get=11 / 770…936=10 个叶子，targetEntity 从 `XzhExp950795` 变 `XzhVerifyEntity` 等）。
>
> **处置（按 main D36 裁定，已完成）**：
> 1. 覆盖版已存档：`writechain-captures/dataflow_mapping_get.update-request-20261017T2339.json`（及 770…936 对应）——它们是**写链实测请求体**，不是 0043 取证快照
> 2. 工作文件已还原至 c3ccb8a 版本（`git checkout c3ccb8a -- <两文件>`，还原后 target=`XzhExp950795.expText`、`description="REST 实测"` 已核）
>
> **对本契约的影响**：下面这段结构示例与全部依赖断言**均基于还原后的 c3ccb8a 版本**。
> **不受影响的结论**：`mappingRow` 的**键集合**（`validate/source/mappingMode/target/personalization/uuid`）与 `mappingMode=FieldCopy` 在覆盖前后两版一致，§5"两套 mappingMode 取值域不同义"不依赖漂移字段，结论不受事件影响。

```json
{ "rules": [ { "operationType": "CREATE", "keyAttribute": [], "autoProcess": false,
    "entityMappingRelation": [ { "targetEntity": {...XzhExp950795}, "sourceEntity": [ {...XzhExp950795} ] } ],
    "mappingArea": [ { "entityId": 474806313816300867, "entityFullName": "...XzhExp950795",
      "mappingRow": [ { "source": { "validate": true, "entityId": 474806313816300867,
                                   "attributeId": 8016904624316689195,
                                   "attributeFullName": "...XzhExp950795.expText" },
                        "mappingMode": "FieldCopy",
                        "target": { "validate": true, "entityId": 474806313816300867,
                                    "attributeId": 8016904624316689195,
                                    "attributeFullName": "...XzhExp950795.expText" },
                        "personalization": false, "uuid": "row-1" } ] } ] }
```

`mappingRow` 键：`validate / source / mappingMode / target / personalization / uuid`（**6 键**，比微流程侧精简）。
（注：本例 source 与 target 同为 `expText` 是 c3ccb8a 原始样本的真实形态——该行是 0043 当时的映射配置原样。）

---

## 6. 三节点协作关系（一句话链）

```
CREATE_MAP ──(output.dataType=MAP)──► 一个 Map 对象（键固定、值多来自上游）
     ▲                                        │
     │ selectMap.nodeInfo 指回源节点            │ selectMap 引用
     │                                        ▼
MAP_OPERATION ──(operationType=GET/KEY_SET/PUT/REMOVE)──► 取出/写入某个值

DATA_MAPPING ──(mappingRule.mappingRows[])──► DTO/实体字段级转换（与上面两者无数据依赖）
```

- **CREATE_MAP ↔ MAP_OPERATION 是配对的**：前者造 Map，后者通过 `selectMap` 引用它做操作。`selectMap.nodeInfo.actionType` 恒指向 `CREATE_MAP`。本应用 2/2、全库 75/75 的 `selectMap.dataType=MAP` 均一致。
- **DATA_MAPPING 是独立支线**：它做 DTO/实体字段转换，与 Map 无直接数据流。
  **本应用与全库一致**：`node.structure.dataType=DTO` 本应用 6/6、全库 26/26（见 §4.2 订正）。故"DATA_MAPPING 输出 DTO"在两个口径下都成立。
  但**判断目标 DTO 类型的权威字段是 `mappingRule.javaType`**，不是 `node.structure.dataType`（模板只读前者，见 §4.2b）；而 `javaType` 在本应用 3/6 缺键 → 该分支为 UNVERIFIED-RISK。
- 三类节点**不构成一条流水线**，只是都叫"映射"。

---

## 7. 未覆盖 / UNVERIFIED（如实标注）

1. **`REMOVE` 无样本**：`MapOperationTypeEnum` 有 4 值（STATIC_BYTECODE 确证），本应用只见 `GET`(2/2)，全库见 `GET` 40 / `PUT` 24 / `KEY_SET` 11，**`REMOVE` 全库 0 例 → VACUUM（不可称非法值，模板定义了它）**。`REMOVE` 的 `theKey`/`output` 形态 → **VACUUM**
2. **节点级 `generics` 与 `output.generics` 双写的同步机制**：两处内容恒相同（本应用 1/1、全库 30/30），但"改一处是否会同步另一处"未验证。**UNVERIFIED**
3. **1 个 `output.dataType=MAP` 的 MAP_OPERATION 节点**：与"GET 出单值 / KEY_SET 出键集合"的直觉不符，未逐个核其 `operationType`。**UNVERIFIED**（样本 1 条，不外推）
4. **`dataType` 大小写规范**：`generics.keyType.dataType="String"`（首字母大写）与 `output.dataType="MAP"`（全大写）并存。是否有校验器强制，**UNVERIFIED**（引用时按原值）
5. **`entries` 为 `[]` 的 5 个 CREATE_MAP**：是"未配置"还是"合法空映射组"，未做运行态验证。**UNVERIFIED**
6. **`DATA_MAPPING` 的 `selectParam` 作用**：本应用 6/6 存在，指向 DTO 列表输出（`position:parent`），疑为映射的输入源；但 `mappingRows[].value.reference` 已各自带源信息，两者关系**未闭合**。**UNVERIFIED**
7. **`mappingType` 的精确语义**：分布（attrs/value/mapping）与宿主节点类型已量化，但**平台是否用它做校验/分支**未反编译到消费点。**STATIC 推断，未到消费点 → UNVERIFIED**
8. **`dataflow` 侧 11 种 `mappingMode` 的实际使用**：样本仅 2 行（均 `FieldCopy`），其余 10 种无实测样本。**VACUUM**
9. **`DATA_MAPPING.mappingRule` 是否还有 `mappingType` 的其他版本**：本应用 6/6、全库 26/26 缺失；跨版本是否存在未验证。**UNVERIFIED**
10. **同名不同 id 微流程的 `state` 语义**：`state` 分布 {10: 289, 20: 4466}，同名的两行常呈现 10 vs 20。是草稿/发布态、还是租户内不同来源，**未反编译到 state 枚举 → UNVERIFIED**。这直接影响"每个逻辑微流程只算一次"时该取哪个版本，本切片不定义。
11. **state=10 是否应计入生产口径**：本应用 9 个映射节点中 **7 个宿主 state=10、仅 2 个 state=20**；全库对照（R3，131 个）**{20: 114, 10: 17}**，其中 state=10 占 17/131 = 13.0%（本应用 7/9 = 77.8%）。两口径比例差异极大（本应用 7:2 vs 全库 17:114），必须在使用前确认。
    **⚠️ 前版此处写「若业务只认已发布态，本应用实际应用面只有 2 个」——该推断已被 LIVE 数据否定，撤回。** 实测（2026-10-18）：
    ```
    state x publish_state 全库交叉：state=10 & publish=1 → 289（100%）
                                  state=20 & publish=1 → 4445
                                  state=20 & publish=0 → 21
    本应用 9 个映射节点宿主：6 行 state=10 全部 publish_state=1；2 行 state=20 亦 publish=1
    state=10 的 289 行 ⟨无一行⟩ publish_state=0；而 state=20 里存在 21 行未发布
    ```
    → **`state` 与 `publish_state` 是两个正交列：`publish_state` 才是发布标志（0/1），`state`（10/20）不是发布态。**
    → 因此「state=10 可能是草稿」这一前提**缺乏数据支持**；本应用 7 个 state=10 节点宿主**全部已发布**，不存在「只算已发布态就只剩 2 个」的情形。
    → **state 的真实语义仍未反编译 → UNVERIFIED**（列注释仅「数据状态」；10/20 与 type/trigger_type 均无稳定对应）。转入 B-7 专项。
    → **已于 B-7 解出（2026-10-18）**：`state=MicroFlowDataStateEnum{DRAFT=10, RELEASE=20}`；`CtpJobTask`/`selectEntity4Code` 硬过滤 `RELEASE.code()==20`，而 `selectFrontendEntity4Code` 不过滤（调用方：前端取流程定义链路 `getUsedEntityActionByAppId`→UI 拉取可运行流程列表，非代码生成链路；铁律 30）→ **type=0 的 state=10 不进代码生成**。见 `state-semantics.contract.md` §3.1/§3.3。

    **「不是版本草稿对」的正确证据（原表述有误，已更正）**：
    - 原写「289 行 state=10 无任何同名 state=20 兄弟行」——这句**只对一半**：全库按 `name` 跨应用分组，确有 **32 组**同名同时含 state=10 与 state=20（涉及 36 行 state=10）。
    - **但那 32 组是「同一租户、不同应用」的同名流程**（32/32 组内 `tenant_id` 相同、`app_id` 全部不同；19 组集中在 `3289082814923688017` 与 `6570299241515796755` 两个应用之间；`original_id` 32/32 为 None 且组内无交叉）——**不是同一逻辑流程的两个版本**。
    - **决定性证据（比"无兄弟行"更硬）**：按 `(app_id, name)` 分组，**多行组数 = 0**。即**每个应用内每个名字只有一行，数据库中根本不存在"同一流程的多个版本行"**。
    - → 既然不存在版本行，`state` 就不可能是「同一流程的版本/草稿状态」。这是**结构性结论**，不依赖任何统计相关性。
    - → 教训：跨应用同名 ≠ 同一流程。第 0 层（应用范围）不止用于计数，**也用于定义"什么算同一个东西"**。铁律 1 的扩展。
12. ~~`structure.dataType` 应用级差异~~ **【已撤销：假事实，见 §4.2 订正】**——本应用 6/6、全库 26/26 均为 `DTO`，无差异。原报的 `None` 是"路径不存在"的假 None。
12b. **UNVERIFIED-RISK｜`mappingRule.javaType` 缺键 3/6（全库同 3 个）**：`DataMappingActivity.java.ftl` 直接读该字段做 `fullNameTransformer.transform(...)`/`getDtoNameByFullName(...)`，缺键时生成代码拿 `null` 转换。**运行态是否真失败未验（0 次 /service）→ UNVERIFIED-RISK**。
13. **`theKey` 动态键（SelectParam 形态）在运行态如何求值**：本应用 1/2 个 MAP_OPERATION 是动态键。静态无法推出取哪个 key，**运行态行为 UNVERIFIED**（需 /service 实测，本切片 0 次）。
14. **`DATA_MAPPING_x8` 的 `mappingRows[0].mappingMode = None`**：单行缺 `mappingMode`，是"未配置"还是"默认引用"，**UNVERIFIED**（本应用仅 1 例；全库也仅 1 例）

---

## 8. SELF-CHECK 复现命令（须实跑通过）

```bash
# 前置：env loader
#   <HERMES_HOME>\skills\xiaozhua\01-platform\xiaozhua-low-code-environment\scripts\env.py
#   凭据只引用路径：<COLLAB_ROOT>\agent-collaboration\shared-credentials\test2-web-credential.json
```

```bash
# ⚠ 本文的 b6_*.py 已移入 `_attic_pending/legacy-audit/`（收容桶，不进分发）；命令路径已按现位置更新
# SELF-CHECK 1 【权威·D37 定稿】R1/R2/R3 三口径对照（本应用 vs 全库，LIVE，只读）
# 期望: 本应用 R1=9 / R2=10occ·9uniq / R3=9occ·9uniq  {DATA_MAPPING:6, MAP_OPERATION:2, CREATE_MAP:1}
#       全库   R1=42 / R2=244occ·139uniq / R3=131occ·131uniq {CREATE_MAP:30, MAP_OPERATION:75, DATA_MAPPING:26}
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_r3check.py

# SELF-CHECK 1b2 【D39 回应】auditor 决定性证据归属核实（LIVE，只读）
# 期望: MFSERVICERD1uB6 id=-9063453479472505266 app_id=3289082814923688017（非本应用）
#       全库 89 个内层节点按 app 分布：3289...017:25 / 5791...064:35 / 1656...084:2 / 2378...643:21 / 6570...755:5 / 7001...721:1
#       本应用 8704025620829192834: **0**
#       内层键数 {13:18,14:43,21:24,22:4}，3键壳 0
#       内层 runAfter：键存在 75/89、值非 None 0/89（input/name 也是 75/89）
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_auditor_claim.py

# SELF-CHECK 1b4 【全库 R3 全量对照】三节点字段分布（LIVE，只读，约 100s）
# 期望: DATA_MAPPING 26 / targetType {None:20, ENTITY:6} / node.structure.dataType {DTO:26} / mappingMode {REFERENCE:264,CONSTANT:1,None:1} 266行
#       CREATE_MAP 30 / entries 非空 22
#       MAP_OPERATION 75 / operationType {GET:40,PUT:24,KEY_SET:11} / output {STRING:39,None:24,DECIMAL:7,BIGINTEGER:2,ENUM:1,DATE:1,MAP:1}
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_alllib_r3.py

# SELF-CHECK 1b3 【口径分歧留痕】引用壳内部构成
# 期望: 引用位内命中 113，宿主键名 {nodeInfo:113}，壳键数 {3:89, 4:24}
#       孤儿（真映射节点 id 集判定）= 10 ；孤儿（真节点任意类型 id 集）= 10
#       旧 allids（含壳自身，错误口径）= 32928 → 恒 0 = 循环论证（本脚本已改为正确口径）
#       【订正】初版报「孤儿 0」是循环论证产物；auditor 报的 10 正确
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_refshell.py
# 独立复核（不依赖上面脚本的判定逻辑）
# 期望: 旧 allids=32928 / 真节点=18447 / 真映射节点=101 / 孤儿 10（两种正确口径均 10）
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_orphan_truth.py
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_refshell.py

# SELF-CHECK 1a 【对照】分母三层陷阱（本应用 vs 全库，LIVE，只读）
# 期望: 本应用 47 行 → A=9 {DATA_MAPPING:6, MAP_OPERATION:2, CREATE_MAP:1}，唯一 9，覆盖 6，state {10:7, 20:2}
#             B(任意深度)=10，差 1；同名组 0；按(name,nodeId)去重仍 9
#       全库 4755 行 → R1=42 {DATA_MAPPING:12, MAP_OPERATION:18, CREATE_MAP:12}（R1 已废弃，仅对照），唯一 42，覆盖 28，state {20:28, 10:14}
#             B=244，差 202；同名 848 名称/1811 行；按(name,nodeId)去重 37
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_scope.py

# SELF-CHECK 1b —— 本应用 9 个映射节点全景逐条（LIVE，只读）
# 期望: 9 条；CREATE_MAP 1 / MAP_OPERATION 2 / DATA_MAPPING 6
#       CREATE_MAP_n6a output=MAP key=String val=Object entries=len 1
#       2 个 MAP_OPERATION 均 GET，theKey 一为 "expText"(字面量) 一为 SelectParam(动态)
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_appnodes.py

# SELF-CHECK 1c —— 本应用字段定量（LIVE，只读）
# 期望: targetType ENTITY 6/6
#       【必修1订正】路径断言必须 OK：mappingRule 无 structure 键 6/6；顶层 node.structure 存在 6/6
#       node.structure.dataType = DTO 6/6（正确路径；原文档写 None 是查错路径的假事实）
#       mappingRule.javaType = {present:3, key_missing:3}，缺键: DATA_MAPPING_x8 / 8EZQEb / bbb222
#       mappingMode {REFERENCE:13, CONSTANT:1, None:1} 共 15 行
#       mappingType 存在于映射节点 0/9
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_appstats.py

# SELF-CHECK 1d —— 全库对照（仅作形态参考，非本应用事实）
# 期望: A=42、B=244、差=202
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_census.py

# SELF-CHECK 2 —— 字段语义定量（LIVE，只读）
# 期望(全库 R3): CREATE_MAP 30 / output.dataType=MAP 30/30 / keyType=String 30/30 / valueType=Object 30/30
#       entries: CREATE_MAP 有键12 非空7；DATA_MAPPING 有键0；MAP_OPERATION 有键0
#       DATA_MAPPING: node.structure.dataType=DTO 26/26, mappingRule.javaType 缺键 3/26,
#                     mappingRows.mappingMode {REFERENCE:264, CONSTANT:1, None:1} 共266行, mappingType 缺 26/26
#       MAP_OPERATION: operationType {GET:40, PUT:24, KEY_SET:11}（REMOVE 0）, selectMap.dataType=MAP 75/75
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_fields.py

# SELF-CHECK 3 —— mappingType 宿主否证（LIVE，只读）
# 期望: 映射类节点（R3 全库 131 / R1 顶层 42）中含 mappingType 的 0 个 —— 两口径均为 0
#       mappingType 取值 {attrs:3415, value:837, mapping:287, None:191}
#       宿主 actionType 为 CHANGE_VARIABLE/CREATE_VARIABLE/CALL_MICRO_FLOW/... 共 12 类
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_mt.py

# SELF-CHECK 4 —— entries 形态与条目统计（LIVE，只读）
# 期望: 含非空 entries 的节点 7 个、条目 40；key.type {Simple:40}；value.type {SelectParam:38, Simple:2}
#       CREATE_MAP 空值形态 = 空 list[] ×5（非 null）
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_sample.py

# SELF-CHECK 4b —— 同名不同 id 微流程核查（LIVE，只读）【分母第二层陷阱】
# 期望: udc_microflow_info 4755 行、唯一 id 4755、重复 id 0
#       同名多行：848 个名称 / 1811 行；state 分布 {10:289, 20:4466}
#       映射节点所在微流程 28 个 id，其中 8 个 id 属同名组
#       映射节点按宿主 state {20:28, 10:14}
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_dupnames.py
# 逐条核对（nodeId 重复明细）
# 期望: nodes 位置 42 条、唯一 (mf,nodeId) 42、重复键 []
#       CREATE_MAP 12 条逐条列出（R1 顶层口径；R3 全量为 30），其中 MFSERVICEvmSOMc/DVrcsWim 各 2 次
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_dups.py
# 表级核对
# 期望: 总行 4755 / 唯一 id 4755 / 重复 id 0；MFSERVICEvmSOMc 与 DVrcsWim 各 2 行（id 不同）
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_duprows.py

# SELF-CHECK 5 —— MapOperationTypeEnum 权威取值（STATIC_BYTECODE）
grep -A2 "public enum MapOperationTypeEnum" \
  <XIAOZHUA_AGENT_ROOT>/docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/enums/microflow/MapOperationTypeEnum.java
# 期望: GET(0), PUT(1), REMOVE(2), KEY_SET(3)

# SELF-CHECK 7 —— 全文数字自洽扫描（main D44 最后一道闸门，静态检查，秒级）
# 期望 A: 无未解释的硬禁表述（structure=None / None 6/6 / 孤儿 0 等）
#      期望 D: 42/244 全部位于对照/留痕语境
#      期望 E: CREATE_MAP/DATA_MAPPING/MAP_OPERATION 的旧值(R1 12/12/18)残留 0 处
#      期望 F: 「本应用 9 / 全库 131」口径已区分
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_selfcheck_numbers.py
# 期望: A ✅ / D ✅ / E 三项全 ✅ / F ✅

# SELF-CHECK 8 —— 孤儿引用三口径对照（澄清「全局 vs 微流程内」）
# 期望: A(含壳) 32928 → 孤儿 0（循环论证）; B(真节点全局) 18447 → 孤儿 10; C(同微流程) → 孤儿 10，涉 7 个微流程
#       B 与 C 同一集合（setB == setC 为 True）
python <XIAOZHUA_AGENT_ROOT>/_attic_pending/legacy-audit/b6_orphan_3ways.py

# SELF-CHECK 6 —— MappingMode 11 常量（STATIC_BYTECODE，注意目录是 cfr-r31 非 r31b）
grep "MAPPING_MODE_" <XIAOZHUA_AGENT_ROOT>/docs/audit/artifacts/scratch-migrated/cfr-r31/com/seeyon/udc/common/mappingmode/MappingMode.java
# 期望: FieldCopy/Formula/Sum/Average/Count/Max/Min/Splicing/FirstLine/LastLine/FixedValue
```

### 8.1 分母闸门

`tools/audit/b5_denom_gate.py` 为 B-5 前置资产，用于防止口径回退；B-6 若需同类闸门，按同样模式另建，不复用 B-5 的基线数字。

---

## 8.9 定向断言：state 分布三元组（本应用 / 全库 / 本应用9节点宿主）

```bash
# 三组 state 数字必须同时成立（B-6 D48 修正 L252 那个拆反的数字后新增）
mysql -N -e "
SELECT '本应用47行', state, COUNT(*) FROM udc_microflow_info
  WHERE app_id='8704025620829192834' GROUP BY state;
" 
# 期望 {10: 5, 20: 42}   ← 原写 {10: 45, 20: 2} 是拆反（auditor 20261017T210010 抓出，main 复核确认）
# 反例识别：若出现 45，说明把 42 与 5 对调了；45 在本应用不存在

SQL_ALL="SELECT state,COUNT(*) FROM udc_microflow_info GROUP BY state"
# 期望 全库 {10: 289, 20: 4466}

# 本应用 9 个映射节点宿主 state
# 期望 {10: 7, 20: 2}（口径=按节点数；按宿主行数是 {10:4, 20:2}，总行数 6——**三个数量必须分清**，铁律 17）
#   state=10 的 4 行宿主: xzhFinalAllNodes(3节点) / xzhStdReal31046(2) / xzhSvcDefK4Ge(1) / xzhSvcEvtBpDA(1) = 7
#   state=20 的 2 行宿主: xzhRestMf(1) / xzhSvcSchcHXa(1) = 2
# 注意：9 节点分布在 6 行宿主上，实测每行节点数直方图 = {1:4, 2:1, 3:1}（4×1+1×2+1×3=9）
#       原写「有 3 行各含 2 个节点」是错的（3×2+3×1=9 也加得通，但分布不同）——铁律 28
```

### 8.10 核心线索：映射节点在 state=10 微流程上的聚集 —— **本应用 16.8 倍是全库 3.16 倍的离群点；控 type 后不显著；效应仅在 trigger=2 子层成立（条件化，非方向翻转）**

L252 的数字拆反，**恰好把这条线索写反了**（原显示「95.7% 的行是 state=10」，掩盖了聚集）。修正后 L252 才显出真相。

**① 未分层的粗相关（raw，不是效应量）**
```
本应用 47 行微流程 state 分布：  state=10 → 5 行（10.6%）   state=20 → 42 行（89.4%）
本应用 9 个映射节点按宿主 state：state=10 → 7 个（77.8%）  state=20 → 2 个（22.2%）
宿主行「有没有映射节点」：
    state=10 的 5 行中，4 行带映射 = 80.0%
    state=20 的 42 行中，2 行带映射 =  4.8%
→ 粗倍数 = 80.0% / 4.8% = 16.8 倍
```

**② type 是混杂变量 —— 控制后净倍数降至 6.0 倍**
```
本应用 type × state（行数）：
  state=10: type=0 → 4 行     type=1 → 1 行
  state=20: type=0 → 6 行     type=1 → 26 行   type=3 → 10 行   ← type=3 全在 state=20
→ type=0 在 state=10 组占 80%（4/5），在 state=20 组只占 14.3%（6/42）→ 富集 5.6 倍

按 type 分层后「带映射 / 总数」：
  type=0  state=10 → 4/4 = 100.0%
  type=0  state=20 → 1/6 =  16.7%      → 层内净倍数 6.0 倍
  type=1  state=10 → 0/1 =   0.0%
  type=1  state=20 → 0/26 =  0.0%      → 层内均为 0，无可比效应
  type=3  state=20 → 1/10 = 10.0%      （state=10 无 type=3 样本）
→ 粗倍数 16.8 → 净倍数 6.0，**衰减约 64% 来自 type 构成差异**
```
→ **这是本切片最重要的一条：一个看起来 16.8 倍的强信号，控制 type 后只剩 6.0 倍。**

**③ 再控制 trigger_type 后，样本已不足以做统计**
```
双重分层（type × trigger_type）：
  type=0 trigger=0:  state=10 1/1=100%   vs  state=20 0/1=  0%    n=[1,1]
  type=0 trigger=2:  state=10 3/3=100%   vs  state=20 0/2=  0%    n=[3,2]
  （其余 7 个单元格只有单侧样本，无法对比）
```
→ **可分层的两个单元格样本量仅 1~3，效应方向仍是 100% vs 0%，但 n 小到不能做任何统计推断。**
→ 排除的字段：`creation_method` 全为 0、`group_type` 全为 0，无区分能力。

**④ 换数据源后：本应用 16.8 倍是极端局部值，全库只有 3.16 倍**
```
全库 4755 行（main 独立复算 tools/core/b7b_main_recheck.py，EXIT=0）：
  不控制        3.1% (  9/ 289)  vs  1.0% ( 44/4466)  = 3.16 倍
  控 type=0     5.9% (  9/ 152)  vs  3.4% ( 43/1249)  = 1.72 倍
  本应用        80.0% ( 4/   5)  vs  4.8% (  2/  42)  = 16.80 倍   ← 全库的 5.3 倍
→ **本应用是全库里的极端离群点，不是普遍规律。** 用本应用 16.8 倍谈「state 的效力」= 用 n=5 的样本外推。
```

**⑤ 再控 trigger_type：不是「方向翻转」，是「效应条件化」—— 看倍数会误判，必须看 Fisher**
```
全库 type=0 内按 trigger_type 分层（main 独立复算 tools/core/b7c_main_fisher_recheck.py，EXIT=0）：
  trigger=0   1.8% ( 1/ 56)  vs  2.6% ( 5/196)   0.70 倍   Fisher p=1.0000  无差异
  trigger=1   0.0% ( 0/ 31)  vs  1.0% ( 1/102)   0.00 倍   Fisher p=1.0000  无差异
  trigger=2  12.3% ( 8/ 65)  vs  3.9% (37/951)   3.16 倍   Fisher p=0.0059  **显著**
```
→ **关键判别：0.70 倍 / 0.00 倍的 p 值都是 1.0000。那是「无差异」，不是「方向相反」。**
→ 只看倍数会得出「方向翻转 / Simpson 交互」，那是**错的**——小样本下 0/31 与 1/102 的倍数可以是任意值，但没有统计含义。
→ 真实结构：**效应不是翻转，是被条件化** —— **仅 trigger=2 层内成立（3.16 倍, p=0.0059），其余两层无证据。**
→ **唯一可支持表述（D57 定稿）**：「合并层不显著（p=0.1668）；分层仅 tt=2 显著（p=0.0059），但层间异质性不显著（Woolf Q p=0.1191）且该显著性对单个应用敏感（剔除本应用后 p=0.1746）→ 整体 UNVERIFIED，无法定论。」
→ **错误表述（四个，均超出数据）**：「方向会翻转」「存在 Simpson 型交互」「state 无任何效力」「效应条件化于 trigger_type」。

**⑥ 结论：现象真实存在，但 state 不是解释变量**
```
能确定的：
  ① 本应用 state=10 的 5 行里 4 行带映射（80%），而 state=20 的 42 行只有 2 行（4.8%）—— 现象真实
  ② 该关联在本应用是 16.8 倍、全库仅 3.16 倍 —— **局部现象，不可外推**
  ③ 控 type 后全库 1.72 倍（p=0.1668，不显著）
  ④ **按 trigger_type 分层后，仅 trigger=2 层显著（3.16 倍, p=0.0059）；其余两层 p=1.0000 为无差异**
不能确定的：
  ① state 与映射之间是否存在直接因果（相关是条件化的，因果仍未证）
  ② 为何只在 trigger=2 成立 —— 是 state 在该类流程里真有语义，还是 trigger=2 的流程构造更易带映射（UNVERIFIED）
```

三种假设的状态（按实测更新，**与前一版结论不同**）：
1. `state=10` 标记「含数据加工/映射能力的流程类型」→ **否证**：全库 state=10 的 289 行里 280 行不含映射（96.9%）。但**不等于 state 与映射无关**——在 trigger=2 子层内仍显著（p=0.0059）
2. 含映射节点的流程在保存/发布时被置为 state=10 → **无代码路径**：`MicroFlowService.update` 分支只看 `type` 与 `state`，不看节点内容（implementer 字节码复核）
3. 两者都受第三字段决定 → **大部分成立**：`type` 解释 64% 粗效应，且映射结构上只可能出现在 SERVICE/CUSTOM（FRONTEND 2840 行零映射，DB 实测 type=1 全库 2840）；但 `type=0` 内部仍存在一个按 `trigger_type` 条件化的子层效应，未被完全解释；`creation_method`/`group_type` 无区分能力

→ **状态：现象 CONFIRMED（本应用）；关联在 `type=0 & trigger_type=2` 子层 CONFIRMED（p=0.0059）；合并层不显著；因果 UNVERIFIED（相关条件化，不能推因果，但也不能说无关）。**
→ **B-7 仍不必回答「state 是不是原因」——但理由不是「已否证」，而是「这是因果问题，DB 相关性回答不了」。**
→ **B-7 必须注意**：不可引用 16.8 倍作为效应量（粗相关 + 局部离群）；**也不可引用「方向一致」**（全库分层后翻转）。引用须四报「本应用粗 16.8 / 本应用净 6.0 / 全库粗 3.16 / 全库分层翻转 0.70–3.16」。

**⑦ 方法论价值（五条）**
- **数字方向错比数字错更危险**：拆反后「state=10 占 95.7%」，真相是占 10.6% 却承载 77.8% 映射节点。一个强信号被写成反向弱信号。（铁律 20）
- **粗相关不是效应量**：16.8 倍里 64% 是 type 构成差异。**任何"X 倍"必须先问「控制了什么」**。（铁律 26）
- **分层到样本不足时，正确结论是「无法定论」，不是「效应更强」**：本应用双重分层后是 100% vs 0%，看起来更强，但 n=1~3。（铁律 27）
- **样本不足时换数据源，不是换统计方法**：本应用 47 行怎么做分层都没样本；换到全库 4755 行才看出「本应用 16.8 倍是全库 3.16 倍里的离群点」。（**新铁律 29**）
- **和校验不保证分布**：「9 节点宿主只有 6 行（有 3 行各含 2 个）」加得通（3×2+3×1=9），实测分布是 `{1:4, 2:1, 3:1}`（4×1+1×2+1×3=9）。**「N 行各含 M 个」必须附实测直方图。**（铁律 28）

**⑧ GATE 化建议（GATE-STRICT）**
```
assert 本应用 47 行 state 分布 == {10:5, 20:42}      # 不符 sys.exit(1)
assert 10 not in {45}                                # 45 = 曾拆反的回归哨兵
assert 宿主行节点数分布 == {1:4, 2:1, 3:1}           # 不是「3 行各含 2 个」
assert type_分层 粗倍数/净倍数 双报                    # 16.8/6.0 必须同时出现
assert 全库 trigger 分层三值齐报 == [0.70, 0.00, 3.16]  # 少报一层即隐藏条件化
assert 各层 Fisher p == {0:1.0000, 1:1.0000, 2:0.0059}    # 只报倍数会误判「翻转」
assert 全库粗倍数 == 3.16 and 本应用粗倍数 == 16.80   # 局部/全库必须同现（铁律29）
```

## 9. 版本与状态锚点

> **纪律（B-6 强制）**：引用本文档任何行号前，先核对 HEAD 与该文件 `git status`（B-5 曾 3 次因核旧版误判）。

撰写时（B-6 订正版）：
- **HEAD commit：见 §9.2**（本文档经四轮 external 审：PARTIAL 必修 1/2/4、争议四项 D1-D4、D43/D44 已全部落实）
- 历史：3a220ed 主体 → 0d4c702 → 3ed57cf → f9a6acc（分母三层）→ e1f32f3（D36+D37）→ d0cfc3c（D39）→ 本轮（PARTIAL 修正）
- 引用本文任何行号前，请先 `git log --oneline -1` 核对；若已前进，行号可能位移
- `git status --short docs/operation-contracts/udc/microflow/ aud/b6_*.py` 应为空（干净）
- 反编译产物：`docs/audit/artifacts/scratch-migrated/cfr-r31b/`（MapOperationTypeEnum）、`docs/audit/artifacts/scratch-migrated/cfr-r31/`（MappingMode）——**两个目录并存，勿混**

### 9.1 本切片的口径演变（留痕，防"文档说 9 脚本跑 42"）

| commit | 那时的分母口径 | 状态 |
|---|---|---|
| `3a220ed` | 全库 42（**漏 app_id 过滤**） | ❌ 已废弃，仅作留痕 |
| `f9a6acc` | 本应用 9（app_id + `nodes[*]` 顶层 + (id,nodeId)） | ⚠ 顶层口径，本应用恰好无嵌套故数字仍对 |
| 本轮（D37 后） | 本应用 9（app_id + **递归跳 REF_SLOTS** + (id,nodeId)）；全库对照 131 | ✅ **唯一有效口径** |

> **B-5 教训在此重演了两次**：文档数字与脚本口径不同步是最难查的缺陷。
> 第一次是 42 vs 9（漏 app_id）；第二次是 R1 42 vs R3 131（漏 conditions 内嵌套）。
> 若有人引用 42 说成"本应用"，那是引用了 `3a220ed` 的废弃口径；引用 42 说成"全库"，那是 R1 废弃口径（正确全库对照是 131）。

---

## 10. 对下游（子流程切片）的交接要点

0. **先问三句，再报数字**：① 哪个 `app_id`？② 遍历哪个位置（`nodes[*]` vs 任意深度）？③ 用什么主键（`(id,nodeId)` vs `(name,nodeId)`）？
   —— 本切片初版就是漏了第 ①，把全库 42 当本应用 9 报了 4.7 倍。
1. **统计映射节点用 R3 口径**：递归 node 容器（含 `conditions` 内嵌套）但**跳过引用位** `{nodeInfo,selectParam,selectMap,selectEvent}`，主键 `(id,nodeId)`。只读 `nodes[*]` 顶层会漏分支内嵌套（全库漏 89 个）；任意深度会多算引用（42→244）
2. **`mappingType` 不是映射节点的字段**：它是变量/调用类节点的参数装配方式
3. **`mappingMode` 有两套**：微流程 `REFERENCE/CONSTANT` ≠ 数据流 `FieldCopy/Formula/...`
4. **`selectMap` 是引用不是定义**：带 `nodeInfo` 指回源节点，无 `entries`
5. **`generics` 双写**：节点级与 `output` 级各一份，内容需一致
6. **`entries` 是 CREATE_MAP 专属**：另两类节点根本没这个键
7. **大小写按原值**：`String`/`Object`（首字母大写）vs `MAP`（全大写），不可归一化
8. **`node.structure` ≠ `mappingRule.structure`**：`mappingRule` 根本没有 `structure` 键（0/6、0/26）；DTO 类型看 `node.structure.dataType`，但**模板真正读的是 `mappingRule.javaType`**（见 §4.2b）
9. **`mappingRule.javaType` 可能缺键**（本应用 3/6）：缺键则生成代码拿 `null` 做全名转换 → 生成器必须显式处理

---

## 11. 方法论（本切片产出，跨切片可复用）

### 11.1 链式 `.get()` 的 None 有两种含义 —— 必须先断言路径存在

```
node.get('mappingRule') or {}).get('structure') or {}).get('dataType')   →  None
```
这个 `None` 可能是：
- **A 字段存在但值为 null** → 业务含义：该字段未配置
- **B 路径根本不存在**（`mappingRule` 里没有 `structure` 键）→ 业务含义：**你查错了地方**

两者业务含义完全不同。**B 被当成 A 写进契约，就是假事实。**

**纪律**：任何链式取值前，先断言父键存在：
```python
assert 'structure' not in node['mappingRule']   # 显式声明它不该有
assert 'structure' in node                     # 显式声明正确路径在顶层
```
本切片 SELF-CHECK 1c 已内置该断言（输出 `[路径断言] ... -> OK/FAIL`）。

> **与 B-5 闸门 case7 同源**：那个盲区是「验证了三者一致，没验证等于权威值」——
> **验证了形式，没验证实体**。这里是「脚本 exit=0、输出有期望行，但取的是不存在的路径」，
> 同样是形式过了、实体没验。**SELF-CHECK 必须包含实体级断言，不能只验"能跑"和"有输出"。**

### 11.2 「保守地陈述一个假事实」仍然是假事实

我在 §4.2 原稿写「本应用 6/6 全 None」，并出于谨慎只陈述差异、不下成因（标 UNVERIFIED）。
方法论上"只报差异不下成因"是对的，**但我报的那个差异不存在**。
更糟的是我把结论标成「必读」「这条比数字本身重要」——
**一个假事实被标上"保守"和"重要"，比普通错误更难被发现，因为读者会降低警惕。**

**纪律**：写"差异/异常"之前，先验证**差异本身**是否存在，而不是急着推测成因。

### 11.3 判定"引用是否有效"时，参照集合不能包含被判定对象自己

我判"孤儿引用"时这样写：
```python
for o in everything:                      # 含引用壳
    if 'nodeId' in o: allids.add(o['nodeId'])   # ← 壳自己的 nodeId 也进了集合
...
if shell['nodeId'] not in allids: orphans += 1   # ← 恒为假
```
→ **orphans 永远是 0**。这不是"数据恰好没有孤儿"，是**判定逻辑自我满足**。

审计数字时，"得 0"和"得一个非 0 值"一样需要检查**参照集合的构成**：
- 参照集合里有没有混进被判定对象本身？
- 集合规模是否与预期量级相符？（我的 32928 vs 真节点 18447 vs 真映射节点 101 —— 三个数量级差 300 倍，本该一眼看出异常）

**纪律**：判定"X 是否存在于 Y"时，先打印 `len(Y)` 并问"这个规模合理吗"。
本次 32928 这个数字在第一次跑时就打印出来了，我没看。

### 11.4 同名字段有两种"不存在"：键不存在 vs 键存在但值为 None

本切片为此发生过一次三方互相指认对方算错（main D42 判 auditor 错 → D43 撤销并认错）：

| 说法 | 数值 | 口径 |
|---|---|---|
| 「内层节点有 runAfter」 | **75/89** | **按键**判定（`'runAfter' in node`） |
| 「内层节点没 runAfter」 | **0/89** | **按值**判定（`node['runAfter'] is not None`） |

**两个数都对**，但都只回答了一半问题：
- 按键 75/89 → 会让人以为"平台在用该字段定序"，实际值全是 None
- 按值 0/89 → 会让人以为"该字段完全不存在"，实际键位保留了

**纪律**：**统计任何可选字段，必须同时报「键命中数」和「非空值数」**。
只报一个，下一个人必然拿另一个数字来指认你算错。

> 这条与 §11.1（链式 `.get()` 的 None 有两种含义）是同一族：
> §11.1 说的是「None 可能来自路径不存在」，本条说的是「字段可能在但值为 None」。
> 合起来：**见 None 先问三句——路径在吗？键在吗？值是 None 还是真没有？**

### 11.5 验证否定结论时，必须先证明"我查的位置是对的"（auditor 20261017T205112）

**肯定结论可以从结果反推位置正确**（找到东西了，说明位置对）。
**否定结论不能** —— 查空既可能是「真没有」，也可能是「**查错地方**」，两者输出完全相同。

本切片实例（auditor 自己犯的，他主动记成纪律）：
```
git log --all -- "writechain-captures/*"                              → 空 → 误判"未提交"
git log --all -- "docs/audit/artifacts/udc-node-evidence/writechain-captures/*" → e1f32f3 命中
```
短路径相对仓库根，匹配不到任何 commit。**"查不到"和"查错地方"输出一模一样。**

**纪律**：报「没有 / 未提交 / 不存在」之前，先证明查的位置是对象真实所在位置
（用 `git ls-tree` / `find` / 绝对路径 交叉验一次），否则不许下否定结论。

> 与 §11.1 的关系：§11.1 说的是「**读到 None**」，本节说的是「**读不到任何东西**」——同一个方向的空结果版本。

### 11.5b 多口径给出不同结果时，先加口径交叉，不要先推定机制（main D46 提炼）

看到"A 口径得 0、B 口径得 10"时，我（main）**直接推定了机制**：「因为用了全局集合而非微流程内」。
这个推定是错的 —— 加第三种口径（真节点 · 全局）立刻得 10，说明真正的变量不是"全局 vs 局部"，
而是"参照集合里有没有混进被判定对象自身"。

**纪律**：两种口径结果不同时，不要先解释「为什么不同」，先加**第三种口径**做交叉。
新口径要与原两种**各自只差一个变量**，否则排除不了混淆。

本切片实测的四口径矩阵（main D46 复跑）：
| 口径 | 参照集合 | 孤儿 |
|---|---|---|
| A 全收（含壳自身） | 任意 dict 的 nodeId | 0（恒假） |
| Bm 全局 · 真映射节点 | 真映射节点 id | 10 |
| Ba 全局 · 真任意节点 | `type=ACTIVITY` 全部 | 10 |
| Cm 同流程 · 真映射节点 | 按流程分的真映射 id | 10 |
| Ca 同流程 · 真任意节点 | 按流程分的真节点 | 10 |

`setBm == setCm` 为 True，且 Ba/Ca 同为 10 → **节点类型与匹配范围都不是变量，唯一变量是"是否排除自身"**。

### 11.5c 报"某处没改"之前，先确认自己看的是最新版

本切片发生过多次「看到旧快照」：
- auditor 用 `git log --all -- "writechain-captures/*"`（短路径）判"未提交" → 实际已在 e1f32f3
- main D46 说 `b6_appstats.py` 仍无 `sys.exit` → 实际已在 f93533d（UTC 19:56:06），D46 在 UTC 20:56:40

**纪律**：要求对方修改前，先 `git log -1 -- <文件>` 确认自己读到的是最新版；
报"某处没改"时，同时贴出该文件的 `git log -1` 与自己读取的时间戳。

> 这是 §11.5（否定结论必须先证明查的位置对）在**版本维度**上的应用：
> 「查不到」可能不是不存在，而是你查的那个 commit / 那个工作区不是最新的。

### 11.6 任何"闸门/断言"必须能改变退出码（GATE-STRICT 第 5 条）

**只打印失败信息、但 `exit=0` 的检查，不是闸门，只是"更醒目的日志"。**

本切片在一天内犯了两次：
| 脚本 | 症状 |
|---|---|
| `_attic_pending/legacy-audit/b6_appstats.py`（**已移入 `_attic_pending/legacy-audit/b6_appstats.py`**，仓库内已无此路径） | 打印 6 条 `[断言失败]`，然后 `exit=0` |
| `_attic_pending/legacy-audit/b6_scan_v3.py`（**已移入 `_attic_pending/legacy-audit/b6_scan_v3.py`**，仓库内已无此路径） | 打印 `GATE FAIL`，然后 `exit=0` |

两处都已加 `sys.exit(1)` 并做负向注入验证（注入 → EXIT=1，还原 → EXIT=0）。

**检查任何"断言"的三问**：
1. 检查动作发生了吗？（调用了 `.get()` / 跑了 `git log` / 跑了断言）
2. 检查结果被读取了吗？（有人看这个返回值吗）
3. 结果能改变流程吗？（**退出码变了吗 / 后续步骤被阻断了吗**）

**第三问不过，就不是闸门。**

### 11.7 「保守地陈述假事实仍是假事实」的适用边界（auditor 补充）

§11.2 那句话只适用于**事实陈述**，不适用于**推断**：

| 类型 | 要求 |
|---|---|
| **可核的字段值 / 计数** | **必须给准确值**，「标保守」不能免责 |
| **不可核的机制 / 成因** | **必须标 UNVERIFIED**，这不算"保守陈述假事实" |

区分标准是「**这件事能不能核**」，不是「我有没有把握」。

### 11.8 自洽（加起来对）不等于正确

auditor 的 54+47+12=113 加得通、我的 3键+4键 也加得通，**两个都能自洽，但只有一个是真分布**。
他因此在 DIST 里写下"自洽不等于正确"，并紧接着自己也犯了一次。

**纪律**：自洽只排除"算术错误"，不排除"口径错误"。**必须做路径级抽查**（挑 2-3 个样本，把完整 JSON 路径打印出来看）。

### 11.9 口径纪律是切片相关的，不可跨切片机械复制

| 切片 | 节点位置 | 正确口径 |
|---|---|---|
| B-5（trigger 事件） | 固定位置 `data_schema.trigger` | **禁递归**任意深度（会多计 `nodeInfo` 里的引用碎片，254→255） |
| B-6（映射节点） | 嵌套分支 `nodes[i].conditions[j].nodes[k]` | **必须递归** node 容器，但跳过 `REF_SLOTS={nodeInfo,selectParam,selectMap,selectEvent}` 子树（否则 131→244） |

同一句"统计前先问 dict 在 JSON 树哪个位置"，在 B-5 导出"禁递归"、在 B-6 导出"必须递归"。
**结论不可复制，方法可复制。**
