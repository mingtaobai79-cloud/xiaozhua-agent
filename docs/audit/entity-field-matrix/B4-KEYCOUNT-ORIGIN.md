# B4｜36 键精简 DTO 的来源与触发条件

> 切片：B4（main HANDOFF 20261018T035117Z）｜线：STATIC + DB 已有证据｜**零写入、零导航、零注入**
> 脚本：`tools/audit/b4_keycount_algebra.py`（34 断言，EXIT=0 才算通过）
> 上游证据：`EVIDENCE-batch-contract-live.json`（04:08:54 CREATE）、`EVIDENCE-batch-update-live.json`（04:52:05 UPDATE）、`assets/bundle-type-default-tables.js.txt`（STATIC bundle 关键段，已落地仓库）

---

## 〇、方向边界（先读这条，防越界引用）

本片的键集代数**只覆盖请求侧**。两侧必须分开陈述，各自标样本量：

| 方向 | 形态 | 样本量 | 本片是否做代数 |
|---|---|---|---|
| **请求侧**（`variables.params0[].attributeDtoList`） | **26**（ADD）/ **36**（UPDATE-精简）/ **76**（UPDATE-全量） | 30 条（2 批 × 15） | ✅ 本片全部结论在此 |
| **响应侧**（`data.data0.data.content[].attributeDtoList`） | **77**（batch 回写响应）/ **72**（另一响应形态，14 条） | 77×1 / 72×14 | ⚠️ 仅记录形态，不做代数 |

**响应侧两形态互不包含**（本片独立复现）：
```
72 ∩ 77 = 71 键
72 独有  = g_l_index（1 键）
77 独有  = attribute4DtoFullName, backupCode, originalId, ownerCode, uniqueKey, validate（6 键）
72 ⊂ 77 ? False     77 ⊂ 72 ? False
```
72 键样本取自 `docs/audit/artifacts/scratch-migrated/audit-slice-b1/audit_b1_read_1792265184189_anil5.json`，落在 `data.data0.data.content` ⇒ **是响应体，与 77 同方向**（此处更正一处早期误判：曾按文件名把它当作"读取方向"，文件名不是接口语义证据）。
72 键对应的接口，结构上高度指向 `udcEntityGet` 类（带 preset 展开），但**请求侧 URL↔body 未一一对应，接口名仍是推断，不当事实写**。

⇒ 因此本片**不能**表述为"全平台只有两档键数"。准确表述是：
**请求侧两档以上（26 / 36 / 76）；响应侧另有 77 与 72 两种互不包含的形态。**

---

## 一、一句话结论

**键数不是"档位"，也不是 dataType 的函数，而是「这条 DTO 从哪来」的函数。**

| 来源 | 键数 | 机制 | 证据级 |
|---|---|---|---|
| **读接口对象原样回传** | **76** | UX 读回的 77 键对象，删 5 个纯服务端键、加 4 个前端索引键，其余字段**一个不改**直传 | **LIVE 已证** |
| **按类型模板重建** | **36** | `core(19) ∪ E[dataType](17) ∪ 身份关系键(8)`，容斥后 0 残差 | **STATIC + LIVE 已证** |
| **新建（无 id）** | **26** | `core ∪ f[type] 表单默认表子集`，无任何身份键 | **STATIC + LIVE 已证** |

因此「什么条件下发 36」的**必要机制**已经查清（走重建分支 = 该字段本次被真实编辑/类型变更），但**充分条件仍 UNVERIFIED**——见 §五。
**判别力边界另有三条**（36 非 INTEGER 专属 / 必须比键集 / 值域 7-14 三层分开）——见 §4.3，须与结论同读。

---

## 二、样本轮廓（LIVE，30 条 DTO 全量）

| 批次 | 时间 | 14×76 UPDATE | 特例 |
|---|---|---|---|
| CREATE | 04:08:54 | 14 条 | `b2IntField` **ADD / 26 键** |
| UPDATE | 04:52:05 | 14 条 | `b2IntField` **UPDATE / 36 键** |

- 非 76 键的只有 2 条，且都是 `b2IntField`（唯一字段级变更对象）
- 28 条 76 键 DTO 的**键集完全一致**（frozenset 相同，0 差异）
- `26 ⊂ 76`、`36 ⊂ 76`、但 **`26 ⊄ 36`** —— ADD 与 UPDATE-精简**不同源**，不能用同一公式解释

---

## 三、76 键的来源：回显直传（LIVE，等式精确）

响应端 77 键与请求端 76 键做差：

```
响应独有 5 键（纯服务端）：attribute4DtoFullName, backupCode, originalId, ownerCode, validate
请求独有 4 键（前端索引）：g_l_index, index, key, parentKey

77 − 5 + 4 = 76   ✅ 等式精确成立
```

**交叉验证（比等式更强）**：14 个未编辑字段在 E1→E2 两批之间逐字段比对，**唯一的差异是 `updateTime`**（1792264333000 → 1792267734000）。字段值一字未动、键集一格未变 ⇒ 前端就是把读接口对象**原样塞回去**，不做任何重建。

> 这条同时解释了 `g_l_index`：它在 bundle 里是编辑器给表达式 token 编号用的内部字段（`decomposeEntities` 里显式 `delete n["g_l_index"]`），属前端私有，服务端不认识，故只出现在请求侧。

---

## 四、36 键的来源：按类型模板重建（STATIC + LIVE，代数 0 残差）

### 4.1 三条恒等式

```
core       = 30 条 DTO 的公共键                          = 19 键
E[Integer] = bundle 里 INTEGER 类型的提交默认表（模块 31623 导出 Uz） = 17 键
IDENT_REL  = guid/id/relationApp/relationCode/relationEntity/
             relationEntityCategory/relationEntityName/system = 8 键

`|core ∪ E[dataType] ∪ IDENT_REL| = 36（容斥：19 + 17 + 8 − 8 = 36）` —— 三集合非互斥，`core ∩ E[Integer] = 8 键`，故不是 19+17+8=44。与实测 36 键**逐键相等（0 残差）**。
```

分开看更清楚：

| 组成 | 键数 | 说明 |
|---|---|---|
| `core ∩ E[Integer]` | 8 | auditLog, columnName, dataType, defaultValue, defaultValueIsChange, notNull, searchable, uniqueness |
| `E[Integer] − core`（新增） | 9 | calculate, defaultValueSystemVariable, defaultValueExpressionDesignData/RuntimeData, expressionDesignData/RuntimeData, max, min, sourceType |
| `IDENT_REL`（新增） | 8 | ADD 时这些键**一个都没有**（记录尚不存在，无 id/guid） |

### 4.2 值的层面对证（不是只对齐键名）

| 项 | 36 键实测值 | `E[Integer]` 声明默认 | 命中 |
|---|---|---|---|
| `defaultValue` | `0` (int) | `0` | ✅ |
| `min` | `""` | `""` | ✅ |
| `max` | `""` | `""` | ✅ |
| `calculate` | `"NORMAL"` | `"NORMAL"` | ✅ |
| `sourceType` | `"ENTITY"` | `"ENTITY"` | ✅ |
| `maxLength`/`minLength` | **不存在该键** | INTEGER 模板里也没有 | ✅ |

ADD 的 26 键同理对上**表单默认表 `f[String]`**：`minLength:0` / `maxLength:50` 精确等于 `f[String]` 的 `minLength:0, maxLength:50`（不是巧合，STRING 表单默认就是 0/50）。

> ⇒ 结论：36 键与 26 键都是**"按当前 dataType 的模板重新拼一条 DTO"**，不是"从 76 里删几个"。
> 76 → 36 的 40 键差额只是这个构造方式的**副产品**，不是设计意图。

### 4.3 ★ 本结论的判别力边界（三条，必须与结论同读）

这三条是 main 12:06 采纳的验收口径，**不写就会把结论读歪**。

#### 4.3.1 `36 = core ∪ E[dataType] ∪ IDENT_REL` 不是 INTEGER 的特征

全 14 张类型表逐张验算（键集比对，不是比键数）：

| 类型 | `\|base ∪ E[t]\|` | `E[t] ⊆ k36` | `base∪E[t] == k36` |
|---|---|---|---|
| **Integer** / **BigInteger** / **Date** / **Time** / **DateTime** | 36 | True | **True ✅ 接受** |
| MultilineString | 36 | False | **False ← 陷阱，见 4.3.2** |
| Boolean | 34 | True | False |
| Decimal / Currency | 37 | False | False |
| Enum / CtpEnum / Entity | 33 | False | False |
| Attachment | 29 | False | False |
| String | 42 | False | False |

**接受集 = {Integer, BigInteger, Date, Time, DateTime}，5/14。**

⇒ `3.4` 那条恒等式**本身成立，但它没有类型判别力**：把 `Integer` 换成 BigInteger / Date / Time / DateTime **同样成立**。
⇒ **不得由 3.4 推出"36 键精简 DTO 是 INTEGER 专属形态"**。本片只能说：36 键 = 走重建分支时按**该字段当前 dataType** 的模板重拼，至于当前是这 5 个类型中的哪一个，键集层面无法区分。

#### 4.3.2 必须比"键集"不是比"键数"（MultilineString 是陷阱）

```
|base ∪ E[MultilineString]| = 36          ← 键数恰好也是 36
  base ∪ E[MultilineString] == k36 ? No   ← 但键集不等
  E[MultilineString] − k36 = {maxLength, minLength}
```
⇒ **只看键数会把 MultilineString 误判成"成立"**。任何据此判类型的逻辑都必须做集合相等，不能数字符个数。

#### 4.3.3 值域能力覆盖 7/14，且"有键 / 有值 / 可配"三层必须分开

| 层 | 事实 | 证据级 |
|---|---|---|
| **① 键存在** | `max` + `min` 出现在 **7/14** 张类型表（Integer, BigInteger, Decimal, Currency, Date, Time, DateTime）；String/MultilineString/Boolean/Enum/CtpEnum/Entity/Attachment 7 张没有 | **STATIC** |
| **② 有值** | INTEGER 域全库 3539 行：`min` 非空 **1**、`max` 非空 **0**、`vse` 非空 **1**；本片 36 键 DTO 的 `min`/`max` 均为空串 | **LIVE/DB** |
| **③ 可交互配置** | 需页面证据（弹层能否产生非空 min/max） | **BLOCKED（登录态）** |

⇒ **不得写"值域能力只有 INTEGER 具备"**——那样错两层：7 个类型都有这两个键；而且 INTEGER 自身也几乎没被写过。
⇒ 也不得由"`E[Integer]` 含 max/min"推出"INTEGER 可配值域"——**键存在 ≠ 有值 ≠ 可通过 UI 配**。

---

## 五、触发条件：必要机制已证，充分条件 UNVERIFIED

### 5.1 已反证的三个假设

| 假设 | 判定 | 反证 |
|---|---|---|
| 36 键 = INTEGER 类型的固定形状 | ❌ **反证** | 同批 `expNum`（dataType=INTEGER）发的是 **76 键**。同类型两档并存 ⇒ 键数不由 dataType 决定 |
| 36 键 = STRING 字段的固定形状 | ❌ **反证** | 同批 `expText` / `B1wenbenyanzheng`（STRING）发 76 键 |
| 40 键差额"全是跟类型走的派生键、类型一变全部失效" | ❌ **部分错**（round2 旧表述，本片更正） | 40 键实际只有 **8 键**属 `E[String]−E[Integer]`（maxLength/minLength/patternMessage/dataI18n/desensitization/enableDesensitization/enableEncryption/encryption）；另 18 键是**服务端只读回填**（orderNo/updateTime/attributeGroupId/sourceId/serialNumber*/parentEnumAttributeId/relationType...）、8 键是**前端索引**、1 键是 `valueScopeExpression`。**这些跟类型无关**，只是"重建时不带" |

### 5.2 为什么充分条件还不能下结论

本批 **n=1**：`b2IntField` 是唯一键集被重构的字段，同时它也是唯一 `dataType` 变化的字段（STRING→INTEGER），且是本批唯一被用户真实编辑的字段。三个因素**在这个样本上完全重合**，无法分离：

- 是"类型变了"触发重建？
- 还是"用户动了这个字段"触发重建（类型只是顺带）？

**判定：机制（重建分支）已证；触发器（哪个变量把它送进重建分支）UNVERIFIED。** 要分离，需要构造"只改类型不改别的"或"只改别的完全不动类型"的对照，属页面线动作 —— 当前 **BLOCKED-NEEDS_HUMAN（登录态）**，不在本片范围。

### 5.3 对下游的实际含义（可直接用）

- 写契约/校验时**不要**按"键数"判合法性。服务端按 `actionType` + 字段存在性收，36/26/76 都能落库（本批已 200 + 落库）。
- 断言应该做在**语义字段**上：`actionType`、`dataType`、`min/max/valueScopeExpression`、身份键四件套（`id/guid/entityId/appId`）。
- 若需要构造"改类型"请求，**最省事且已被 LIVE 证实可行**的路子是照 36 键形状发（core + 目标类型模板 + 身份键），比照 76 键更容易命中服务端重算分支。

---

## 六、证据分级

| 结论 | 级别 | 依据 |
|---|---|---|
| 76 = 读对象 77−5+4 直传 | **LIVE** | 等式精确 + 14 字段仅 updateTime 变 |
| 36 = core∪E[Integer]∪IDENT_REL | **LIVE + STATIC** | 键集 0 残差（LIVE）+ 模板表反解（STATIC） |
| 26 = core∪f[String] 子集，无身份键 | **LIVE + STATIC** | 键集 + minLength/maxLength 精确命中 |
| `E[type]` 是提交默认表、`f[type]` 是表单默认表 | **STATIC** | bundle 模块 31623：`E` 含 `dataType/columnName/sourceType`，`f` 含表单控件默认 |
| 触发条件充分条件 | **UNVERIFIED** | n=1，三因素重合，页面线 BLOCKED |

---

## 七、复现与注入验证

```bash
cd <SEEYON_AGENT_ROOT>
python tools/audit/b4_keycount_algebra.py          # EXIT=0 = 34 断言全过（取证闸门）
python tools/audit/gate_b4_doc.py                  # EXIT=0 = 41 断言全过（B4 文档闸门）
python tools/audit/gate_b2_docfix.py               # EXIT=0 = 74 断言全过（B2 文档闸门，round4 版）
python tools/audit/gate_b4_doc.py --inject M9      # 注入：rc=1 被拦 / 2 漏检 / 3 锚点缺失
python tools/audit/gate_b2_docfix.py --inject M2
```

**注入退出码已语义化**（main 12:11 要求）：`1`=被拦（好）、`2`=漏检（坏）、`3`=锚点缺失/未知注入名。

三码位**均已实测可达**（不是只写在代码里）：

| 码 | 含义 | 触发方式 | 实测 |
|---|---|---|---|
| 1 | 被拦（好） | `--inject M9` | ✅ |
| 2 | 漏检（坏） | `--inject SELFCHECK`（语义无害的等价改写，闸门应当放行） | ✅ |
| 3 | 锚点缺失 / 未知注入名 | `--inject NOPE` | ✅ |

> 修过一个真撞码 bug：`gate_b4_doc` 原用 `raise SystemExit("unknown injection: ...")`，
> **字符串参数使退出码=1**，与「被拦」撞码（main 12:26 指出）。已改 `sys.exit(3)`。
> 与 round2 的 `taskkill //F`（rc=1 空操作掩盖失败）同构：**退出码不承载语义 = 假信号源**。

**B4 闸门注入实测（9/9 命中，还原逐字节一致）**

| # | 注入 | 命中断言 |
|---|---|---|
| N1 | 充分条件 UNVERIFIED → 已证 | B5 |
| N2 | 77−5+4 → 77−6+4 | A1（负半边） |
| N3 | 8 键 → 13 键 | A5（负半边） |
| N4 | B2 恢复旧口径 | A9 + A10 |
| **M7** | **删掉触发条件节标题声明** | **B7e（结构性删除防护）** |
| **M9** | **加「36 键是 INTEGER 专属形态」** | **B7a（auditor 12:12 漏检点，已补）** |
| **M10** | **加「值域能力只有 INTEGER」** | **B7c（同上）** |
| M11 | 接受集 5/14 → 2/14 | A13 |
| M12 | MultilineString 陷阱改写成「键数不同故不成立」 | A15 + A15b |

**B2 闸门注入实测（round4，按 auditor/BASELINE-ROUND4-ACCEPTANCE.md 验收单，12/12 命中）**

| # | 验收项 | 注入 | 命中断言 |
|---|---|---|---|
| R1b | b) 不退步 | `**恒为 int**` → `**恒为 str**` | B1a-2 |
| R2 | b) 不退步 | `createTime`(29/30) → (30/30) | B1a-7 |
| R3 | b) 不退步 | 非空 vse 1 → 56 | B3f |
| R4 | b) 不退步 | 删「不能写任何值都不可用」 | B4f |
| **R1half** | **c) 必达** | **str 组追加 `createTime`，int 组保留** | **B1a-3（两组解析集合交集非空）** |
| **R4b** | **d) 必达** | **`type=3 → 实体 id（也用字段 id）`** | **B4d（分支绑定错挂）** |
| R5 | e) 新增式 | 加「恒为 int 是 STRING 专属形态」 | B1a-2 / B1a-5c |
| R6 | e) 新增式 | 段落前塞「任何值都不可用，一律按时间窗查」 | B4k |
| M1 | 自查 | 删 int 组 `updateTime` | B1a-5c |
| M2 | 自查 | 删 `type=1 → 字段 id` 声明句 | B4d |
| M3 | 自查 | domain_id 改「永不使用任何值」 | B4f |
| M4 | 自查 | createTime 挪进 int 段 | B1b |

> **c/d 两项（main 12:14 点名必达）已闭合；e 项（允许降级）未降级，R5/R6 均被抓。**
>
> **R1half 为什么旧版拦不住**：旧 B1a 判据是「`**恒为 int**` 在」+「`createTime`(29/30) 在」，两个条件在注入后**都仍成立**——因为 int 组那行原样保留。文档已经自相矛盾（同一键同时列在恒 str 与恒 int），闸门却无症状。
> 根因是**只在段内文本里找成员，不解析成集合算交集**。round4 改成：解析两行 → 得 `doc_str` / `doc_int` 两个集合 → 断言 `doc_str ∩ doc_int == ∅`，并各自与反解集合比对归属。
>
> **R4b 为什么旧版拦不住**：旧 B4e 只查 `"type=1" in seg and "type=3" in seg`（两字样都在），B4b/c/d 只查三个锚「共现」，**不校验谁配谁**。给 type=3 挂上"（也用字段 id）"后共现全部满足 → 漏检。
> round4 改成**分支绑定**校验：每个分支必须在自己的窗口里构成 `type=N … → want` 箭头，且窗口内不得出现未加否定的 `forbidden`。

> **闸门自身修正史（三轮假阳性 + 两轮漏检，全部记账）**
>
> 假阳性（把对的判成错）：
> ① 负向断言缺否定语境豁免——把「键数**不**由 dataType 决定」判违规；
> ② 未剥离引号/删除线——把「引用旧口径做对照」判违规；
> ③ 自测结果表里的字面错误值被负向断言自抓（B4 §七、B2 §10.2 两处同坑复发）。
>
> 漏检（把错的判成对）：
> ④ 单边正向断言抓不住数字篡改（N2/N3）→ 补**正负绑定**；
> ⑤ 只看「附近提及」不看**箭头句式**（M2 靠段内偶然出现的 `type=1` 蒙混）→ 改强制句式；
> ⑥ `--inject` 父进程恒 exit 0，`$?` 不承载语义 → 语义化为 1/2/3。
>
> 共同教训：**闸门必须能同时拒绝「对的被说错」与「错的被说对」**；任何单边断言（只有正向或只有负向）都会在一侧失守。
> 另：审计口径的 M7/M9/M10 证明**「数字被改」类注入全绿 ≠ 闸门有效**——还要测「新增错误断言」和「删除锚点」。

脚本纯只读：只读 EVIDENCE JSON + 仓库内 bundle 资产段，0 网络、0 浏览器、0 DB 写入。
bundle 源已落地 `assets/bundle-type-default-tables.js.txt`（7,687B，sha256 `1b7bffc7…9b9f39a`），**不再依赖 cache**；
已实测：把 cache 里原 bundle 移走后脚本仍 `EXIT=0`。若资产也被删，脚本以 `anchor not found` 显式退出，不会静默给假结论。

---

## 八、本片对既有文档的更正

| 位置 | 旧表述 | 更正 |
|---|---|---|
| §3.3 三档键集注 | "省略的 40 键**全是**跟着类型走的派生键，类型一变全部失效" | 只有 **8 键**是类型专属；18 键服务端只读、8 键前端索引、1 键 vse。真实原因是**按模板重建**，40 键差额是副产品 |
| §3.3 三档键集表"出现条件"列 | "类型变更时，派生键被前端省略" | 改为"该字段本次走重建分支（按当前 dataType 模板重拼 + 补身份键）"；触发变量 UNVERIFIED |
