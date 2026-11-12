# SLICE-B7 · B6 证据源级升级（VACUUM 独立重扫 + 反解/DB 重算比对）

- **切片**：B7（main HANDOFF `052638Z`，唯一活动切片）
- **前置**：B6 收口于 `5ac913c`（闸门 F15/F16 序关系 + 内容口径两处修正）
- **边界**：只读。零 /service 配额、零浏览器、零页面、零 DB 写、零 git 写（除本片 commit）。DB 走内网直连。
- **产出**：`docs/audit/artifacts/scratch-migrated/audit-slice-b7/{b7_vacuum_rescan.py, b7_recompute.py, B7-vacuum.json, B7-recompute.json, baseline-33e764b/}`

---

## 一、结论先行

| # | 事项 | 判定 | 依赖 |
|---|---|---|---|
| ① | VACUUM 独立重扫（DTO 层 DECIMAL/CURRENCY） | **样本内 VACUUM 成立**（48 实例 / DECIMAL 0 / CURRENCY 0）—— 但该结论**域限于已捕获的 2 批 DTO**，不足以支撑第 11 行「Decimal 请求形态」升 `VACUUM`（详见 §六） | 字段级 dataType 判定 |
| ② | 反解 + DB 重算 vs 基线 `B6-*.json` | **0 处偏差**（逐数相等） | bundle sha `6051e1df…` 未变 |
| ③ | 三态恒等式独立复核 | **72 格（4 类型 × 3 scope × 6 列）全部闭合**，其中**12 格平凡**（total=0）、有效 **60 格**。（48 格 = 4 列子集，8 平凡 / 40 有效；两套口径都对，主口径用 6 列全量）auditor 原报「26 组」经三方复核为心算混口径错数，已作废 | 见 §四 |
| ④ | §6.1 第 11 行等级 | **维持 `UNVERIFIED`**（我曾主张改判 VACUUM，main 053722Z 准予后于 054125Z 撤销，auditor 053941Z 反驳成立）。已按裁定补措辞，不改等级 | 见 §六 |

**没有一条把 STATIC 说成 LIVE。** 本片提升的是**证据来源等级**（从"作者自己的 JSON"升到"独立重算可复现"），不是证据类型等级。

---

## 二、① VACUUM 独立重扫

### 2.1 为什么不能用键名 grep

`decimalDigits` 在 DTO 层是**响应侧全员共有键**——B2 的 INTEGER 字段请求/响应 DTO 都是 77 键，里面就带 `decimalDigits: 0`。
所以「grep decimalDigits 命中」与「存在 DECIMAL 字段」**毫无关系**。这是 B5/B6 已记的第 2 次假阳性陷阱。

### 2.2 判定方法

递归遍历两份 EVIDENCE 原文里**每一个 dict**，若该 dict **自身含 `dataType` 键**，它就是一个「字段级 DTO」，取其 `dataType` 值。
拿到的是**实例**，不是字符串出现。

```
EVIDENCE-batch-contract-live.json   46,115B   DTO实例=16
    dataType={'DATETIME':3, 'ENTITY':6, 'STRING':4, 'CTPENUM':1, 'INTEGER':1, 'BOOLEAN':1}
EVIDENCE-batch-update-live.json    103,888B   DTO实例=32
    dataType={'INTEGER':6, 'DATETIME':6, 'ENTITY':12, 'STRING':4, 'CTPENUM':2, 'BOOLEAN':2}
```

### 2.3 结果

```
字段级 DTO 实例合计 = 48

  ENTITY            18
  DATETIME           9
  STRING             8
  INTEGER            7
  CTPENUM            3
  BOOLEAN            3

★ DECIMAL  实例 = 0
★ CURRENCY 实例 = 0
```

**假阳性缺口可量化：**

```
decimalDigits 键名出现 = 44 次
DECIMAL + CURRENCY 字段级实例 = 0
假阳性缺口 = 44
```

这 44 次键名命中**全部**来自其他类型的 DTO（全员共有键），无一条对应 DECIMAL/CURRENCY 实例。
**如果用键名 grep 判定，会得出完全相反的结论。**

### 2.4 防漏判：换键名也扫一遍

```
裸 token 字符串级出现次数：
  DECIMAL   0
  CURRENCY  0
  Decimal   0
  Currency  0
  Numeric   0
  Money     0
```

两份 EVIDENCE 原文里**连字符串形态都不存在** DECIMAL/CURRENCY 的任何变体。
⇒ 不是"字段级 DTO 恰好没命中"，是**整个 DTO 域内该类型完全缺席**。VACUUM 是完备负证据，不是抽样未命中。

### 2.5 前提与局限（不夸大证据强度）

VACUUM 成立的前提是：两份 EVIDENCE 里的 DTO 是**该批次请求/响应的完整原文**。
- `EVIDENCE-batch-update-live.json` 的 `_meta` 记 `requestBodyLen=30259 / responseBodyLen=31590 / httpStatus=200 / responseCode=BOOT_0000`，
  文件内 `request_full` / `response_full` 是解析后的结构，**不是纯文本全量**。
- 因此严格说：本片证明的是「**这两批已捕获的 DTO 中，DECIMAL/CURRENCY 实例为 0**」。
  它**不能**推出「平台上从未存在过 DECIMAL 字段的创建请求」——那需要更大的抓包面。
- 但对本片目标要分两行看，**不能合并**：
  · **第 10 行**（batch DTO 无 DECIMAL 实例）—— 该行主张自带域限定「batch DTO 这批」，
    所以「已捕获样本内 0 实例」对它是**完备负证据（VACUUM）**，成立。
  · **第 11 行**（Decimal 的请求 DTO 实际形态）—— 该行问的是**类型契约层**，域不是抓包域。
    16 字段的抓包对它**不构成完备负证据**，故维持 **UNVERIFIED**。
  ⇒ 同一份证据，两行等级不同，**因为两行问的域不同**。这是本片最容易被合并误读的一处。

**不主张：** 本片不主张「DTO 契约层在原理上不支持 DECIMAL」——只主张「已捕获样本内 0 实例」。

### 2.6 判定

但注意 B6 §6.1 表里第 10 行本来就写的是 `**VACUUM**`，第 11 行「Decimal 的请求 DTO 实际形态」写 `**UNVERIFIED**`。

★ **我一度主张第 11 行改判 `VACUUM`，这个主张错了，已撤回。** 撤回理由见 §六 —— 核心是：
48 个实例按 `(id,name,dataType)` 去重只有 **16 个独立字段**，且全属 **1 个实体 / 2 个属性组 / 2 次 batch 请求**；
而 B6 §4.3 已证 **全库 DECIMAL 4529 条**。用 16 字段的抓包说「Decimal 请求形态 VACUUM」，是被自己的 DB 数据否证。

---

## 三、② 反解 + DB 重算 vs 基线

### 3.1 为什么要独立写脚本，而不是重跑 `b6_static.py`

`b6_static.py` 的键集来自 `B5-keysets.json`（B5 阶段的预解析中间产物）。
重跑它只能证明"同一份中间产物还能读出同样的数"，**不能证明中间产物本身对**。
所以本片 `b7_recompute.py` **直接从 bundle 原文重新切段、重新解析**，不 import `b6_static.py`、不读 `B5-keysets.json`。

### 3.2 bundle 锚点（与基线一致）

```
size   = 2,530,724
sha256 = 6051e1df6c574df7…   ← 与 B6 §2.1 记录一致，文件未变

E 表切出 14 个类型：
Attachment, BigInteger, Boolean, CtpEnum, Currency, Date,
DateTime, Decimal, Entity, Enum, Integer, MultilineString, String, Time
```

### 3.3 独立重算键数

```
类型           E 键数   f 键数
Decimal        17       7
Integer        17       6
BigInteger     17       6
Currency       17       6
```

**E 层四类型全 17 键 ⇒ 键集对「Decimal vs Currency」无判别力**（B6 结论复现）。
**f 层 Decimal=7 而其余=6 ⇒ 唯一判别位在 f 层**（B6 结论复现）。

集合关系重算：

```
E 层 Decimal vs Currency : set_equal=True   only_in_Decimal=[]  only_in_other=[]
E 层 Decimal vs Integer  : only_in_Decimal=['decimalDigits']  only_in_other=['uniqueness']
f 层 Decimal vs Currency : set_equal=False  only_in_Decimal=['searchable']  only_in_other=[]
```

精度键扫描（全 14 E 表 + 14 f 表）：命中键名集合 **唯一为 `decimalDigits`**，无 precision / scale / decimalScale / decimalPrecision。

### 3.4 DB 重算

```
queried_at           2026-10-18 13:29:16
db_max_update_time   2026-10-18 04:52:05   ← 与基线相同，DB 自 04:52:05 起零写入
total_all_types      67864

DECIMAL     n=4529   min[19/4504/6]   max[19/4505/5]
CURRENCY    n=107    min[0/107/0]     max[0/107/0]
INTEGER     n=3539   min[2829/709/1]  max[2829/710/0]
BIGINTEGER  n=4576   min[3628/948/0]  max[3628/948/0]
```

三态写法为 `[null/empty/nonempty]`。

### 3.5 逐数比对结果

比对项共 **70+ 组**（bundle size/sha + 2 资产 size/sha + 4 类型 × (E_n/f_n/E_keys/f_keys) + 3 类型 × 6 组集合差 + 3 组精度键扫描 + DB total/max_update + 4 类型计数 + 48 组三态 + digits 分布 + 本应用 3 项 + min/max 非空行数）。

```
★★ 0 处偏差（全部逐数相等）
```

**这个 0 偏差是有意义的**，因为：
1. 键集是从 bundle 原文**重新解析**的，不是复用中间产物；
2. DB 是**重新连库重新发 SQL** 的，不是读旧 JSON；
3. `db_max_update_time` 未变（04:52:05）证明两次查询落在**同一个 DB 快照**上，排除"数据变了但结论碰巧一致"。

### 3.6 一处口径澄清：基线 `keysets` 6 类型 ≠ 精度扫描 6 类型（我一度误判，已自纠）

```
基线 B6-static.json  res["keysets"]      6 个类型（TYPES 列表：Decimal/Integer/BigInteger/Currency/String/MultilineString）
基线 b6_static.py    精度扫描域           KEYS5["ALL_E_keysets"] 14 个 / ALL_f_keysets 16 个
```

★ **我第一版写这条时说「B6 §三『全 14 E 表 + 16 f 表正则扫』在 `B6-static.json` 里没有对应实现，属 D64 同族」——这个指控是错的，撤回。**

查证过程：`b6_static.py` L96-L102 的精度扫描用的是 `KEYS5["ALL_E_keysets"]` / `ALL_f_keysets`，
实测这两个字典分别是 **14 / 16** 个类型，**与 B6 声明的"全 14 表 + 16 f 表"完全一致**。
我误把 `res["keysets"]`（只装 6 个目标类型）当成了扫描域——**这是看代码只看一半**。

**B6 的措辞是准确的，我的指控不成立。** 已在本片报告中撤回，不进入任何结论。

（本片仍保留全量重算这一动作：独立重跑得的 E 14 / f 16 类型与基线扫描域一致，
精度键扫描结果 `{decimalDigits}`、携带类型 `{Currency, Decimal}` 也一致 ⇒ 0 偏差。）

---

## 四、③ 三态恒等式独立复核 —— 恒等式成立，但"26 组"这个数是错的

### 4.1 我算出的数

我用 `null + empty + nonempty == total` 作为恒等式，逐格验证：

```
口径 A：4 类型 × 3 scope(all/sys_0/sys_1) × 4 列(min/max/vse/decimal_digits) = 48 格
        闭合 48 / 失衡 0

口径 B：仅 min/max 列 = 4 类型 × 3 scope × 2 列 = 24 格
        其中 total>0 的 = 20 格

口径 C：仅 min/max 且仅 sys_0/sys_1（不含 all）= 4 × 2 × 2 = 16 格

口径 D（本片最终采用，全列）：4 类型 × 3 scope × 6 列 = 72 格
        闭合 72 / 失衡 0 / 平凡 12 / 有效 60
```

**auditor 说的"26 组"，我三种口径都复现不出来。** 这不是 auditor 算错——是"组"这个词没有绑定口径（4 类型？含不含 all？只 min/max 还是含 vse？）。按 auditor 自己刚立的纪律「报行数必须带口径前缀」，这里应写成：

> 恒等式在 **4 类型 × 3 scope × 4 列 = 48 格全部闭合（0 失衡）**，其中 min/max 子集 24 格、非平凡（total>0）20 格。

### 4.2 ★ 一个 auditor 没提、我认为更要紧的事实：8 格是平凡闭合

```
total=0 的格（恒等式必然成立，等于没验）：
  DECIMAL  sys_1  min / max / value_scope_expression / decimal_digits    ← 4 格
  CURRENCY sys_1  min / max / value_scope_expression / decimal_digits    ← 4 格
```

原因：**DECIMAL 和 CURRENCY 的 `is_system` 全部为 0，没有系统字段**（B6 已记）。
所以 `sys_1` 这 8 格的 `total` 本身就是 0，`0+0+0==0` 恒成立——**这 8 格不构成任何证据。**

auditor 说「26 组全 0 失衡 ⇒ 说明提取脚本没失真，这是 baseline 可信的强证据」。
**方向对，但强度要打折**：48 格里有 8 格（17%）是空集自证。

真正有判别力的是 **40 格**（total>0）。40 格仍全闭合，**结论不变**，但"强证据"的强度描述应基于 40 而非 48 或 26。

### 4.3 为什么"空集自证"要单独记账

这是 D64 同族病的又一形态：**数字对得上，但它证明的东西比看上去少。**
- D64：贴"可达"不贴"那次运行" → 数字无来源
- 本片：贴"48 格全闭合"不贴"其中 8 格 total=0" → 数字有来源但**部分无内容**

**记法**：凡是"全部 X 都满足 P"的断言，必须同时报 **X 里有多少个是平凡满足**（空集、零值、默认值）。否则"全部"这个词在做虚功。

---

## 五、承接：判「配没配值域」必须看 min/max，不能看 vse

main HANDOFF `052638Z` §6 要求本报告承接 auditor `052240Z` §四 的方法修正。**我复核成立，且这条比 B6 原文写得更强。**

逐条查 DECIMAL 那 6 条 min/max 有真值行的 `value_scope_expression`：

```
[1] 税率统一调整          min=0  max=1   vse={"min":"","max":""}   空壳
[2] 达成占比             min=0  max=1   vse={"min":"","max":""}   空壳
[3] 税率统一调整          min=0  max=1   vse=None                  NULL
[4] 税率统一调整          min=0  max=1   vse={"min":"","max":""}   空壳
[5] 税率统一调整          min=0  max=1   vse={"min":"","max":""}   空壳
[6] 债权最高额限度（万元）  min=0  max=''  vse={"min":"","max":""}   空壳
```

**5 条「min/max 有真值」的行，vse 同时是空壳**（第 6 条是 NULL）。

⇒ 不是"两条互斥通道"，是 **同一行可同时持有 min/max 真值 + vse 空壳，二者语义完全不重叠**。

**这直接证伪 B2/B5 的隐含推理路径：**

| 切片 | 原文推理 | 结论 | 路径 |
|---|---|---|---|
| B5 | 「BigInteger vse 非空 5 条全是空壳」→「BI 未配值域」 | 对（BI min/max 确实 0/0） | ✗ **作废** |
| B2 | 同族（vse 导向） | 需回查，本片不重开 | ✗ 存疑 |

B5 的结论恰好对，是因为 BigInteger 的 min/max 本来就是空的——**不是 vse 空壳推出来的**。
用同一条推理去看 DECIMAL 会得出"DECIMAL 也没配值域"，而事实是 **DECIMAL 有 6 条真实配置**。

**判定基线（已入 ROUTE）：判「配没配值域」看 `min`/`max` 两列，不看 `value_scope_expression`。**

---

## 六、④ 第 11 行等级：我主张改判 VACUUM → **错，已撤回**

### 6.1 撤回经过（完整留痕，不删）

```
B7 首版     我判定：48 实例 0 命中 + 裸 token 全 0 ⇒ 第11行应改判 VACUUM
main 053722Z §4   准予改判
我 071ee0a       执行改判（§6.1 表 + GRADE_ROWS + F13b/c 期望 + CLAIM_LEVEL 四处同步）
auditor 053941Z  驳回，判「维持 UNVERIFIED，不准改」
main 054125Z §1  撤销准予，采纳 auditor 反驳
我 本 commit     回滚等级，保留措辞补充
```

### 6.2 auditor 的反驳我逐条复核，全部成立

**① 证据域被我高估了：48 实例 ≠ 48 个独立事实**

```
按 (id, name, dataType) 去重：48 → 16 个独立字段
出现次数分布：3 次×14 / 2 次×1 / 4 次×1
（同一字段在 request / response 里各算一次，14 个字段出现 3 次）
```

且这 16 个字段全部属于：
```
实体 474806313816300867 · 2 个属性组(params0[0] 7 字段 / params0[1] 8 字段) · 2 次 batch 请求
```

**这不是"平台"，不是"本应用"，甚至不是"该实体的全部字段"。**

**② VACUUM 的定义要求「在该域内穷尽且为空」，而这个域太小**

`VACUUM` 与 `UNVERIFIED` 的区别是：前者是**完备负证据**（查遍了，确实没有），后者是**未查/未取到**。
16 个字段的两次抓包，够不上"对 Decimal 类型请求契约穷尽"。

**③ 第 11 行问的域与抓包域不是同一个域**

第 11 行问「**Decimal 的请求 DTO 实际形态**」——这是**类型契约层**的问题：若有 Decimal 字段，它的 DTO 长什么样。
16 个字段里没有 DECIMAL，**推不出**「Decimal 的 DTO 形态不存在」。域不同，结论不传递。

**④ ★ 最硬的反驳：被 B6 自己的 DB 数据否证**

**B6 §4.3 已证：DECIMAL 全库 4529 条。**
⇒ 平台上 DECIMAL 字段**大量存在**，只是这两批抓包没覆盖到。
用「16 个字段的抓包里 0 实例」去说「Decimal 请求形态 VACUUM」，等于说一个库里有 4529 行的类型"不存在契约形态"。

**⑤ 而且我的报告本来就写对了，紧接着又跳回去**

§2.5 我写：
> 本片证明的是「这两批已捕获的 DTO 中，DECIMAL/CURRENCY 实例为 0」。
> 它**不能**推出「平台上从未存在过 DECIMAL 字段的创建请求」——那需要更大的抓包面。

**下一段我却写「在该证据域内是完备负证据（VACUUM）」——把"证据域"偷换成"这两批 DTO"，自相矛盾。**
正确写法应该是：那句§2.5 的限定就是结论本身，不能在同一段里再升格为 VACUUM。

### 6.3 最终处置：不改等级，只补措辞

```
| Decimal 的请求 DTO 实际形态 | **UNVERIFIED** | 无实例；两批已捕获 DTO（1 实体/2 组/16 字段）
                                                 内 DECIMAL 实例为 0，但全库 4529 条 DECIMAL 字段
                                                 表明该类型真实存在，仅本抓包面未覆盖 |
```

**核心：把「域内 0 实例」和「该类型真实存在」两句并列写出**，读者才不会误读成"不存在"。

### 6.4 回滚后的可回退检测（证明回滚态本身是被守住的）

`docs/audit/artifacts/scratch-migrated/audit-slice-b7/b7_line11_rollback_verify.py`，D65 三联判据：

```
测试 1 单边把第11行改成 VACUUM（不该改却改）
  完整闸门 rc=1  F15 升格 [(11, 0, 'VACUUM')] + F11 整行不一致
  去F17    rc=1  F15 + F11

测试 2 共谋（文档 + GRADE_ROWS 同步改成 VACUUM）
  完整闸门 rc=1  F13b(VACUUM应1实2) + F13c(UNVERIFIED应1实0) + F17
  去F17    rc=1  F13b + F13c
```

⇒ 回滚态稳：往 VACUUM 方向改，无论单边还是共谋都被拦。

### 6.5 ★ 跨级互换共谋：F17 是单点（我独立复现 auditor 054238Z §三）

`docs/audit/artifacts/scratch-migrated/audit-slice-b7/b7_crosslevel_conspiracy_v2.py`：

```
攻击：L10(VACUUM) ↔ L11(UNVERIFIED) 互换，文档 + GRADE_ROWS 同步改
改前/改后等级分布完全相同 {'STATIC':4,'LIVE/DB':5,'VACUUM':1,'UNVERIFIED':1,'BLOCKED':1}
⇒ 计数层（F13/F13b/c/d）天然看不出

步骤 0 基线（原文档 + 未共谋闸门变体）：四变体全 rc=0
攻击结果：
  完整闸门      rc=1  FAIL=2  触发 F17            → 拦住
  去 F17       rc=0  FAIL=0                     → ★★ 全漏
  去 F13 系     rc=1  FAIL=2  触发 F17            → 拦住（F13 系在这组无用）
  去 F13+F17   rc=0  FAIL=0                     → ★★ 全漏
```

**⇒ 跨级互换（分布守恒）场景下，F17 是唯一有效层，属单点防护。**

不必恐慌，但**收口声明必须写准**：

```
单边攻击           → F0–F16 多层冗余
共谋降格/升格       → F13 系 + F17 双保险
跨级互换(分布守恒)   → 仅 F17 单点
```

**不写「三重防护无缺陷」。** F17 的常量表是语义表，编造它等于编造证据来源，比改数字更易被审出；且 F17b 有覆盖率断言兜底 —— 但单点性质没消失，只是从 F13 转移到了 F17。

### 6.6 探针事故三（本轮，我自己的）

`b7_crosslevel_conspiracy.py` v1 我把「步骤 0 基线」写成「原文档 + **共谋**闸门」，
必然 rc=1，脚本自己打印「★ 作废」退出。修正为「基线 = 原文档 + 未共谋闸门 / 攻击 = 共谋文档 + 共谋闸门」。

**这是 D65 想防的那类错误的第三次形态**：不是把崩溃当拦截，而是把测试装置搭错导致自我否定。
**教训：共谋类测试必须把"基线组"和"攻击组"分开构造，不能共用一套改了常量的闸门。**

### 6.7 「源级」覆盖范围（原为限定，已补齐全列 —— 说明变更原因）

auditor 053526Z §三-② 指出：B6 基线 `states` 有 **6 列**，我只重算 4 列 ⇒ 另 **24 格**（`default_value` / `max_length` × 4 类型 × 3 scope）仍是产物级，应按「源级到顶」打折。

**我采纳这条，且直接把缺的两列补上**（加两次 SQL，成本远低于挂账）：

```
COLS6 = (min, max, value_scope_expression, decimal_digits, default_value, max_length)

4 类型 × 3 scope × 6 列 = 72 格
  闭合 72 / 失衡 0
  其中 total=0 平凡格 12 个
  有效格 60 个
  与基线逐数比对：0 偏差
```

**⇒ 覆盖范围已从 48 格扩到 72 格，B6 的 `states` 六个 DB 列全部独立重算。**

**但仍必须说明「源级」的边界（不夸大）：**

| 维度 | 等级 | 依据 |
|---|---|---|
| 键集（E/f 键数+键集） | 源级 | bundle 原文重新切段解析 |
| 集合差 / 精度键 | 源级 | 全 14 E / 16 f 表扫描，结果已落盘 JSON |
| DB 六列三态（min/max/vse/digits/default_value/max_length） | 源级 | 重连库重发 SQL，72 格 0 偏差 |
| VACUUM 判定 | 源级 | 48 实例 + 裸 token + 换名三扫 |
| ★ 页面可交互形态 | **BLOCKED** | 登录态冻结，本轮无法触及 |

**「源级到顶」只适用于 STATIC/DB 两腿。页面 LIVE 腿仍是 BLOCKED，不是本片能升的。**

### 6.8 ★ 一处「宣称 > 实际」我自己承认（auditor 053526Z §三-①）

`B7-recompute.json` 的 `compare.static.checked` 写了「+ 精度键扫描」，但 **JSON 里没有 `precision_keys` / `diffs` 字段**。
这些结果我算了、打印在 stdout 了，但**没落盘** ⇒ 该声明不可复核。

**D64 同族：声称做了，但没贴产物。** 已在本 commit 补写入 JSON（见 §九 附注），不靠 stdout 存活。

| 行 | 原等级 | 处置 | 依据 |
|---|---|---|---|
| 10 · batch DTO 无 DECIMAL 实例 | `VACUUM` | **维持 `VACUUM`** | §二：48 实例 0 命中 + 裸 token 全 0 |
| 11 · Decimal 的请求 DTO 实际形态 | `UNVERIFIED` | **维持 `UNVERIFIED`**（我曾主张改判 VACUUM，经 auditor 053941Z 反驳、main 054125Z 撤销准予，已回滚） | 抓包域仅 1 实体/2 组/16 字段，且全库 DECIMAL 4529 条 ⇒ 域不足以支撑完备负证据；属「未取到」而非「域内穷尽为空」 |
| 其余 10 行 | 不变 | **不变** | §三 重算 0 偏差 |

⚠️ **这张表在 `071ee0a` 曾被写成「已改判 VACUUM」，后被 auditor 053941Z 驳回、main 054125Z 撤销准予、
`ca4403c` 回滚。现为回滚后终态。** 改判经过与五条驳回理由见 §6.1–6.2，此处不重复叙述
（同一主张多处出现正是本次残文的成因，见 §6.9）。

---

### 6.9 ★ 残文事故：同一主张写多处，改一处必留残（D67 候选）

本轮 `ca4403c` 回滚只改了 `SLICE-B6` 文档与闸门，**`SLICE-B7` 这份报告漏改 5 处**，
造成同一份文档里「第 11 行已改判 VACUUM」与「第 11 行维持 UNVERIFIED」并存。

**最要命的是摘要表相邻两行直接打架：**

```
| ① VACUUM 独立重扫 | VACUUM 成立，UNVERIFIED 可清零为 VACUUM   |   ← 旧残文
| ④ §6.1 第 11 行   | 维持 UNVERIFIED（…反驳成立）              |   ← 已修
```

读者读到相邻两行会以为是两件事，其实说的是同一件事。

**闸门为什么抓不到：**

```
gate 输入 = SLICE-B6-DECIMAL-static.md / B6-static.json / B6-db.json / B7-vacuum.json
gate 是否引用 SLICE-B7 报告 : False
```

⇒ **B7 报告不是闸门输入，这 5 处残文永远不会被任何断言发现。**
「闸门全绿」对闸门不读的文件没有任何保证力。

**成因不是偷懒，是「同一主张在文档里出现多处」**：
§一 摘要表、§六 6.1 时间线、§6.8 处置表、§七 证据分级表，四处都在讲第 11 行该是什么等级。
改的时候改了「新写的那处」，漏了「早就存在的那处」。

**规则（D67 候选）：**

> 文档内同一主张只写一处，其余处**引用**该处，不重复陈述结论。
> 若必须重复（如摘要表），则重复处只写「见 §X」，不写独立结论。

本报告已按此处理：§6.8 的处置表不再重复改判理由，只写终态 + 指向 §6.1–6.2。

---

## 七、证据分级（本片产出）

| 事实 | 等级 | 依据 |
|---|---|---|
| DTO 层无 DECIMAL/CURRENCY 实例 | **VACUUM** | 字段级 dataType 递归，48 实例 0 命中 + 裸 token 全 0 |
| `decimalDigits` 是全员共有键（假阳性） | **LIVE** 级产物证据 | EVIDENCE 原文 44 次键名命中、0 字段级实例 |
| E 17/f 7 键集 | **STATIC（源级可复现）** | bundle sha `6051e1df…` + 独立重新切段解析 |
| E 层 Decimal ≡ Currency | **STATIC（源级可复现）** | 集合比对 |
| DECIMAL 4529 / min 6 / max 5 | **LIVE/DB（源级可复现）** | 13:29:16 重连库重算，db_max_update 未变 |
| 三态恒等式 72 格全闭合 | **LIVE/DB** | 60 格非平凡 + 12 格平凡（48 格为 4 列子集；6 列全量多 2 列 × 2 个空 scope = +4 平凡格） |
| min/max 是唯一值域配置通道 | **LIVE/DB** | 6 行逐条 vse 实测 |

**没有一处把 STATIC 写成 LIVE。** 本片所有"升级"都在**同一等级内提升可复现性**，不跨级。

---

## 八、边界自证

- 零 `/service` 请求（DB 内网直连，不经 web 层）
- 零浏览器 / 零页面 / 零登录态依赖
- 零 DB 写（全部 SELECT）
- 0 kill / 0 启动 / 0 新建 profile
- 未改 B6 已收口文件（`5ac913c` 的 gate/doc 零触及）
- 未重开 B5/B6 闸门线
- 基线副本 `docs/audit/artifacts/scratch-migrated/audit-slice-b7/baseline-33e764b/` sha256 与 `HEAD` blob 逐字节一致（`b551947…` / `d6c79d5…`）

---

## 九、残余边界：闸门能证「自洽」，不能证「为真」

本节为 **main 055848Z §3 明令写入**。不修代码，但必须把边界说清，
否则下一个读到这里的人会以为「F18 之后闸门能证明证据为真」。

### 9.1 四层防护的真实强度

| 攻击形态 | 5ac913c 时 | F17 后 | F18/F19 后 |
|---|---|---|---|
| 单边改（只改文档） | 拦 | 拦 | 拦 |
| 共谋降格/升格（文档 + GRADE_ROWS） | **rc=0 漏** | F13/F14 或 F17 拦 | 拦 |
| 跨级互换（分布守恒） | rc=0 漏 | **仅 F17 拦（单点）** | 拦 |
| 五处同步改（含 CLAIM_LEVEL + F13b/c 期望） | rc=0 漏 | **rc=0 漏** | **F18d 拦** ✅ |
| 六处同步改（攻击 6：NO_FACT 移出 + FACT_BIND 插真键，见 9.2） | rc=0 漏 | rc=0 漏 | **rc=0 仍漏**（伪造 JSON 与否无差别） |

**F18/F19 的真实价值**：把「**照指令同步改动**」这类**无心之失**从放过变成拦住。
071ee0a 正是无心之失 —— 我当时按 main「同步四处」的指令做，根本没意识到那是攻击。

### 9.2 攻击 6：**连 JSON 都不用动**（auditor 060003Z §二，我独立复现）

**上一版这里我写错了方向**：我原写「攻击者若连事实源一起伪造仍属可能」，
暗示攻击成本包含「伪造 JSON」。**实际不用 —— F18d 判「有无事实」根本不读 JSON。**

**关键源码：**

```python
_BOUND_CLAIMS = [c for c, _s, _p, _w in FACT_BIND]   # ← 闸门内常量表，不读 JSON
bound = any(b in r for b in _BOUND_CLAIMS)           # ← 纯文本子串匹配
```

**攻击只需两步（不碰任何 JSON）：**

```
① 把「Decimal 的请求 DTO 实际形态」从 NO_FACT_CLAIMS 删掉
② 往 FACT_BIND 加一条指向**任意真实存在键**的绑定：
   ("Decimal 的请求 DTO 实际形态", "vacuum", ("verdict","DECIMAL_instances"), 0)
   ← 这就是 batch 那行自己的真键，复制粘贴即可
```

**于是 F18（取值对）、F18b（键可达）、F18c（等级==来源映射）、F18d（已登记）四层全部通过。**

**分解验证（`docs/audit/artifacts/scratch-migrated/audit-slice-b7/b7_attack6_jsonfree.py`，我独立复现）：**

```
步骤 0  基线                       rc=0  121 PASS
        ② 五处同步（仍在 NO_FACT）  rc=1  120 PASS  触发 [F18d]   ← D66 负样本成立
        ③ 六处（不伪造 JSON）       rc=0  121 PASS  触发 无         ★ 全漏
        ④ 六处 + 伪造 B7-vacuum.json rc=0  121 PASS  触发 无         ★ 同样全漏
```

**⇒ ③ 与 ④ 结果完全相同。伪造 JSON 那一步对「是否被拦」毫无影响。**

**这是本轮最需要写清的一条**：
- 我原以为边界是「JSON 可伪造」——那至少要求攻击者理解数据语义；
- **实际边界是「FACT_BIND 表里插一行复用真键」——成本比改 5 处还低，且不需要理解任何数据。**

**根因（比上版更精确）：**

```python
is_declared_no_fact = any(c in r for c in NO_FACT_CLAIMS)   # 变量 A（闸门内常量）
bound = any(b in r for b in _BOUND_CLAIMS)                  # 变量 B（闸门内常量）
if is_declared_no_fact: ...    # 只查 A
elif not bound: ...            # 只查 B
```

**A 与 B 都取自闸门内常量表，与文档同处一个可写面；且两者无交叉校验。**
攻击者同时「从 A 删掉 + 往 B 加一条」，两个动作语义相反但分处两个变量 ⇒ 都通过。

而 `F18c` 只验「等级 == 来源映射」，**不验「该主张本应属于哪类来源」**。
登记 `vacuum` 源 → `SRC_TO_LEVEL["vacuum"] = "VACUUM"`，文档也写 `VACUUM` ⇒ F18c 一致通过。

**「同一主张既声明无事实、又声明有事实」这个语义矛盾，闸门没有任何一处检查。**

**成本量化**：只需复制粘贴一条相邻行的真键（`("verdict","DECIMAL_instances"), 0`），
**比 071ee0a 的「改 5 处」还低，且完全不需理解任何数据语义。**
（上一版我写的「需伪造 JSON」高估了攻击成本 —— JSON 那一步根本不影响是否被拦。）

### 9.3 为什么不在本轮修（main 055848Z §2 + auditor 055655Z §六 共同判断）

1. **堵不完**：加 F18f（两名单交叉校验）只需 3 行，但下一层是「换 FACT_BIND 里的 key 路径指向另一个真键」，
   再下一层才是「改 JSON」。**每堵一层只需多改一处，永无终点。**
   **这不只是「门槛抬高」的问题 —— 它说明「用常量表自证」这条路本身有天花板。**
2. **性质不同**：攻击 6 需要**刻意**「先把某行从无事实名单挪到有事实名单」，属主动伪造取证。
   F18 拦住的是无心之失（071ee0a 正是：我按指令同步改，没意识到是攻击），
   没拦住的是蓄意伪造。**一个闸门的实际价值 = 拦住真实发生过的那类错误。**
3. **真正缺口在页面线**：登录态仍 BLOCKED，继续加层的边际收益远低于恢复页面腿。

⇒ **F17c（CLAIM_LEVEL 从 JSON 现算）与 F18f（两名单交叉校验）只入待办，不做。**

### 9.4 ★ 自证体系的固有边界（结论，防止后人误读）

> **闸门能证明「文档与产物自洽」，不能证明「产物为真」。**

后者只能靠：
- **闸门外的独立复算**（auditor 每轮做的那种：读原始 bundle / 重连 DB / git show 取 blob）；
- 或**不可写外部锚**（签名 / 时间戳 / 第三方存证）。

**「F18 之后闸门全绿」不等于「证据为真」。** 任何把这两者划等号的说法都是误读。

### 9.5 D65 规范的两处补充（本轮实测挖出来的，非空想）

**① 「PASS 数下降」检测不到中性化**（我 055919Z 实测，main 060055Z §2 确认并修正 D65）

```
方式                    rc  PASS数  该断言标签是否仍在 PASS 行
基线                    0   121     是
完整块删除式            0   120     否      ← PASS 掉 1，可检出
中性化 ok(True, ...)    0   121     是      ← PASS 不变，检不出
```

⇒ **判断言是否真被禁用，必须看「该断言的标签是否仍出现在 PASS/FAIL 行」，不能只看 PASS 总数。**

**② 中性化最危险的失败是「改错位置」**（auditor 060247Z §四 补）

`ok(x, "A")` 若被改成 `ok(True or y, "A")`，**标签还在、PASS 数不变，但已短路到无关条件上** ⇒ 两层检查都过。

**⇒ 中性化之后必须另加一步：构造必然违反该断言的最小输入，看它是否仍 PASS。**
若仍 PASS 说明真的被短路了；若 FAIL 说明中性化没生效（改错位置）。

**完整判据（删除式 + 中性化共用）：**

| 方式 | 必须验 |
|---|---|
| 完整块删除 | rc=0 且 PASS 数按预期下降 且 标签消失 且 stderr 空 |
| 中性化 | rc=0 且 PASS 数不变（正常）且 标签仍在 且 **构造必违反输入后仍 PASS** |

---

### 9.6 子串匹配隐患（auditor 060247Z §六 提醒）

`_BOUND_CLAIMS` 与 `NO_FACT_CLAIMS` 的判定用的是：

```python
any(b in r for b in _BOUND_CLAIMS)      # 子串匹配
```

**隐患**：若两条主张文本互为子串（如 `"DECIMAL 全库 4529"` 与 `"DECIMAL 全库 4529，全部业务字段"`），
`in` 会双向命中。

**当前 12 行经核对没有互为子串的情况，所以现在不出错。但新增行时必须注意。**
（这是我 §9.5 那个「范围默认」病的另一种表现：默认「现在没冲突，以后也不会有」。）

---

### 9.7 我的验证范围事故（main 055848Z §5 点名，记在这里）

auditor 055655Z §五 指出：**我在 F18 里防的正是「同一主张多处出现、改一处漏一处」，
而我的 B7 报告里第 11 行主张出现在 §4 摘要表 L14、§六 6.3、§6.8 L435 三处，我只改了 6.3。**

**「自己防的病，在自己报告里犯了。」**

根因与 §五② 的自纠同族 —— **不是疏漏，是默认「我改的那份就是全部」**：

| 位置 | 表现 | 共同根因 |
|---|---|---|
| `has_num`（B5 v1） | 用「存在」推断「成立」 | 用间接信号代替直接判据 |
| F18d v1 | 用「未登记」推断「无事实」 | 同上（缺席→不存在） |
| 本轮残文 | 用「我改的这份」推断「全部改完」 | 同上（局部→全部） |

**三次都是「范围默认」**：把一个局部的、间接的信号当成全局的、直接的结论。

**修的规则**：交付前必须 `grep` 同一主张的所有出现位置逐行核对，不能凭"我改过了"记忆。
**已按此执行**：本次修完 5 处残文后，用
`grep -n "请求 DTO 实际形态" SLICE-B7-*.md` 逐行核对（见 §十）。

★ **而且这个 grep 真的又抓出一处（L91）** —— 它不在 auditor 报的 3 处里，是我机械核对时发现的。
如果只按「auditor 列了几处就改几处」，这处会一直留着。
**这是「机械核对」优于「照清单改」的实证：清单是别人视角的抽样，grep 是全量。**

---

## 十、本报告与 SLICE-B6 doc 的一致性检查（main 055848Z §5 要求）

**检查方法**（下次可复算）：

```bash
grep -n "请求 DTO 实际形态" docs/audit/entity-field-matrix/SLICE-B7-SOURCE-LEVEL-UPGRADE.md
grep -n "VACUUM" docs/audit/entity-field-matrix/SLICE-B7-SOURCE-LEVEL-UPGRADE.md
```

**当前全部命中位置逐行核对结果：**

| 位置 | 内容 | 判定 |
|---|---|---|
| L97 | 「第 11 行写 `**UNVERIFIED**`」 | ✅ 与 B6 doc 一致 |
| L283 | 「main 053722Z §4 准予改判」（§6.1 撤回经过时间线） | ✅ **历史记录，保留**（main 055848Z §4 明令不改） |
| L91 | 原写「对判定第 10/11 行已足够…是完备负证据（VACUUM）」 | ★ **本轮 grep 新发现并修正** —— 它把两行合并判定，实际第 10 行成立、第 11 行不成立（域不同）。已拆成两行分别说明 |
| L314 | 「第 11 行问类型契约层的问题」 | ✅ 说明性文字 |
| L335 | 表内第 11 行 = `**UNVERIFIED**` | ✅ 一致 |
| L435 | 处置表第 11 行 = 「维持 `UNVERIFIED`」 | ✅ 已修正 |
| L438 | 「该表在 071ee0a 曾被写成已改判…现为回滚后终态」 | ✅ 撤回记录，非现行结论 |

**唯一允许保留的"VACUUM"邻接表述**：§二 讲「样本内 VACUUM 成立」时明确写了**域限于已捕获 2 批 DTO**，
不构成对第 11 行等级的暗示。

---

## 十一、本片终态声明

```
B7 = PASS
  STATIC/DB 两腿源级：键集 / 集合差 / 精度键 / DB 六列 72 格 / VACUUM 判定
  页面 LIVE 腿 = BLOCKED（登录态），不在本片范围
B6 = PASS
  含「跨级共谋依赖 F17 单点」结构事实
  F15/F16 在共谋下零贡献（结构事实，已登记）
  F17 自身「与文档同可写面」边界已由 F18/F19 补强，但攻击 4 仍可漏（§9.2）
```

**不再在闸门内加层。** 本节即闸门线的收口依据。
