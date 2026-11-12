# SLICE-B6｜实体字段类型矩阵第 5 类 DECIMAL —— STATIC / DB 前置腿

- 日期：2026-10-18（GMT+8）
- 环境：test2，库 `udc_test2`
- 应用：`datamigration9000000000000000001`
- HANDOFF：`20261018T050527Z`（B6 单一活动切片）
- 证据脚本（只读，可复跑）：
  - `docs/audit/artifacts/scratch-migrated/audit-slice-b6/b6_static.py` → `B6-static.json`
  - `docs/audit/artifacts/scratch-migrated/audit-slice-b6/b6_db.py` → `B6-db.json`
  - `tools/audit/gate_b6_decimal.py`（本切片闸门）
- 边界：**零页面、零 REST 业务请求、零库写**；DB 走内网直连（不耗 `/service` 配额）。

---

## 一、一句话结论

| 项 | 结论 | 等级 |
|---|---|---|
| **STATIC：DECIMAL vs Currency 键集** | `E[Decimal]` **17 键**，与 `E[Currency]` **集合完全相等**；`f[Decimal]` **7 键** vs `f[Currency]` **6 键**，差集仅 `{searchable}` | **STATIC** |
| **STATIC：精度标度键** | 全 14 表精度键名**唯一为 `decimalDigits`**（无 precision/scale）；仅 Currency/Decimal 携带；E/f 默认值均 **2** | **STATIC** |
| **STATIC：与 Integer/BigInteger 的关系** | E 层 D−I=`{decimalDigits}` / I−D=`{uniqueness}`；f 层差集更大（D 独有 `decimalDigits`+`searchable`，I 独有 `uniqueness`） | **STATIC** |
| **DB：DECIMAL 全库** | **4529** 行，全部 `is_system=0`（无系统字段）；min 非空 **6**、max 非空 **5** | **LIVE/DB** |
| **DB：值域真实样本** | 6 条中 **5 条 min=0/max=1**（税率统一调整 ×4 + 达成占比 ×1），1 条 min=0/max 空，全部 `decimal_digits=2` | **LIVE/DB** |
| **契约对照：batch DTO** | 两份 EVIDENCE 字段级 DTO 中 DECIMAL/CURRENCY 实例数 **0**；`decimalDigits` 在 DTO 层是**全员共有键** | **VACUUM** |
| **触发条件充分性** | Decimal 与 Currency 的 E 层键集恒等 ⇒ 键集无判别力 | **UNVERIFIED** |
| **页面可交互配值域** | 需页面腿，登录态冻结 | **BLOCKED** |

---

## 二、反解源锚（双 sha256）

```
bundle 整文件    2,530,724B   sha256 6051e1df6c574df74c842f9e4c0714fae5c7ff0df6e86e5ffa5b2d4f994f387d
SEG-E 段        4,666B        sha256 62869f1230be89074d5974a732eccc5edcb77044e7ea454118245628c589d645
SEG-E 内层      4,663B        sha256 b1e75e105c0dedefeaec5301fec38d22bbde71df864dc36f47188004b9f1e84f
                              ⇒ 与 auditor 已钉死锚逐字节相等（跨组互证）
SEG-F 段        1,454B        sha256 db90ee1f4d1f8c393de97533f8fdb0b478222e1d1501c0186b4aead08bf21221
SEG-T 段          298B        sha256 f5483b41efaf6b55546d7f2f3aefb7c8bdd17472791b670ae19ee8527688901e
```

三个段落均已在 B5 落地进仓库（`docs/audit/entity-field-matrix/assets/bundle-SEG-*.js.txt`），本片直接复用，不依赖 cache。
B5 已证：仓库内 bundle 副本与 cache 原件整文件差 1 字节（自偏移 2,349,062 位移），但 E 段字节完全相等 ⇒ **结论只依赖段落，不依赖整文件**。

---

## 三、DECIMAL 类型表反解（STATIC）

### 3.1 E[Decimal] 原文（17 键）

```
{dataType:"DECIMAL",notNull:!1,searchable:!1,defaultValue:0,expressionDesignData:"",
 expressionRuntimeData:"",auditLog:!1,decimalDigits:2,min:"",max:"",
 defaultValueSystemVariable:"",defaultValueExpressionDesignData:"",
 defaultValueExpressionRuntimeData:"",defaultValueIsChange:!0,calculate:"NORMAL",
 sourceType:"ENTITY",columnName:""}
```

键集（17）：
```
dataType, notNull, searchable, defaultValue, expressionDesignData, expressionRuntimeData,
auditLog, decimalDigits, min, max, defaultValueSystemVariable,
defaultValueExpressionDesignData, defaultValueExpressionRuntimeData,
defaultValueIsChange, calculate, sourceType, columnName
```

### 3.2 f[Decimal] 原文（**7 键**，比 Integer/BigInteger 多 1）

```
{decimalDigits:2,defaultValue:p,notNull:!1,min:void 0,max:void 0,auditLog:!1,searchable:!1}
```

### 3.3 集合差（本片核心）

```
E 层  vs Integer   ：set_equal = False
       只在 Decimal ：{decimalDigits}
       只在 Integer ：{uniqueness}

E 层  vs BigInteger：同上（BigInteger 与 Integer 的 E 层键集恒等）

★E 层  vs Currency ：set_equal = **True**   ← 完全相等，一个键都不差

f 层  vs Integer   ：set_equal = False
       只在 Decimal ：{decimalDigits, searchable}
       只在 Integer ：{uniqueness}

f 层  vs Currency  ：set_equal = False
       只在 Decimal ：{searchable}
       只在 Currency：{}
```

**结论三条**：
1. **DECIMAL 与 CURRENCY 在 E 层是不可区分的**（键集完全相等，连键序都一致）。⇒ 任何"看 E 层 DTO 键集判断是 Decimal 还是 Currency"的逻辑都必然失败。
2. 两者**唯一**的静态差异在 f 层：`f[Decimal]` 带 `searchable`，`f[Currency]` 不带。这是**表单层的可搜索开关**差异，不是数据模型差异。
3. DECIMAL 相对 Integer/BigInteger 的差异是 `decimalDigits`（有 vs 无）与 `uniqueness`（无 vs 有）——**双向差异**，与 B5 的 BigInteger（相对 Integer 只有值差异、键集恒等）性质不同。

### 3.4 精度／标度键：只有 `decimalDigits`，没有 precision/scale

对全部 14 张 E 表 + 16 张 f 表做键名正则扫描（`decimalDigits|precision|scale|decimalScale|decimalPrecision`）：

```
命中的键名集合 = ['decimalDigits']          ← 只有这一个
E 层含该键的类型 = ['Currency', 'Decimal']   ← 只有这两个
f 层含该键的类型 = ['Currency', 'Decimal']   ← 只有这两个
```

⇒ 平台**没有独立的 precision/scale 两键**，精度信息只由一个 `decimalDigits` 承载（语义上是小数位数）。
⇒ 该键默认值在 E 与 f 两层均为 `2`。
⇒ **`decimalDigits` 存在 ≠ Decimal 独有**：Currency 也有，所以它不能单独判别 Decimal。

### 3.5 min/max 归属与 WB 边界

```
min+max 同时出现的类型（E 层 7/14）：BigInteger, Currency, Date, DateTime, Decimal, Integer, Time
⇒ Decimal 在值域键组内（与 B5 的结论第①条一致）

WB 区间表：
  [a.Decimal]:{min:"-9007199254740991",max:"9007199254740991"}
  ⇒ 与 BigInteger / Currency 边界完全相同（±(2^53−1)，字符串形态）
  ⇒ 该边界无类型判别力（B5 已证，本片复核一致）
```

---

## 四、DB 回读（LIVE/DB）

### 4.1 存储字面量先证后查

bundle 侧已证 `E[Decimal].dataType = "DECIMAL"`；DB 侧全值枚举交叉验证：

```
SELECT data_type, COUNT(*) n FROM udc_attribute GROUP BY data_type ORDER BY n DESC;
  STRING 20496 / ENTITY 13468 / DATETIME 8522 / BOOLEAN 4953 / BIGINTEGER 4576 /
  DECIMAL 4529 / INTEGER 3539 / ENUM 2834 / CTPENUM 2133 / DATE 1364 /
  MULTILINESTRING 652 / ATTACHMENT 287 / Serial 213 / TIME 188 / CURRENCY 107 / CONTENT 3
```

⇒ 存储字面量确为 **`DECIMAL`**，与 bundle 枚举 `e.Decimal="DECIMAL"` 一致。**不是 `NUMERIC`，不是 `DEC`。**

查询时刻 `2026-10-18 13:xx`，全库 `udc_attribute` 总行数 **67864**。

### 4.2 四类型同表对照

```sql
SELECT data_type, COUNT(*) total,
       SUM(min IS NULL), SUM(min=''), SUM(min IS NOT NULL AND min<>''), ... (max 同)
FROM udc_attribute WHERE data_type IN ('DECIMAL','CURRENCY','INTEGER','BIGINTEGER')
GROUP BY data_type;
```

| data_type | total | min 三态（NULL / 空串 / 非空） | max 三态（NULL / 空串 / 非空） |
|---|---|---|---|
| **DECIMAL** | **4529** | 19 / 4504 / **6** | 19 / 4505 / **5** |
| **CURRENCY** | **107** | 0 / 107 / **0** | 0 / 107 / **0** |
| **INTEGER** | **3539** | 2829 / 709 / **1** | 2829 / 710 / **0** |
| **BIGINTEGER** | **4576** | 3628 / 948 / **0** | 3628 / 948 / **0** |

### 4.3 ★ 本片最重要的发现：DECIMAL 是唯一成规模配置值域的类型

> 口径更正（auditor 052240Z §二）：原写「全库唯一真正配过值域的类型」会被下游读成「其他类型全零」，**不成立**——INTEGER 有 1 条 min 非空孤例。
> 准确说法：**DECIMAL 是唯一成规模配置值域的类型**（min 非空 6/4529；占四类型全部 min 非空 7 条的 **85.7%**），其余仅 INTEGER 有 1 条业务字段孤例（`sys_1` 全 NULL），CURRENCY / BIGINTEGER 全零。

| data_type | is_system=1（系统） | is_system=0（业务） | 非空 min |
|---|---|---|---|
| DECIMAL | 0（**无系统字段**） | 4529 | **6** |
| CURRENCY | 0 | 107 | 0 |
| INTEGER | 2824 | 715 | 1 |
| BIGINTEGER | 3628 | 948 | 0 |

⇒ **DECIMAL 的 4529 个字段全部是业务字段，没有任何系统字段**。这与 INTEGER/BIGINTEGER（系统字段占 80%）形成鲜明对比。
⇒ 因此 B5 建立的「min NULL=系统字段 / 空串=业务字段」双路径规律**不适用于 DECIMAL**：DECIMAL 里 `NULL` 只有 19 条、`空串` 4504 条，19 条 NULL 需要单独解释（无系统字段可对应）。

### 4.4 6 条非空 min/max 的全部真实样本（不再只有"1 条"）

```sql
SELECT id,entity_id,name,caption,min,max,is_system,default_value,decimal_digits,
       value_scope_expression,update_time
FROM udc_attribute WHERE data_type='DECIMAL' AND (min NOT NULL AND min<>'' OR max NOT NULL AND max<>'');
```

| caption | min | max | decimal_digits | vse | update_time |
|---|---|---|---|---|---|
| 税率统一调整 | 0 | 1 | 2 | `{"min":"","max":""}` | 2026-04-22 |
| 达成占比 | 0 | 1 | 2 | `{"min":"","max":""}` | 2025-02-23 |
| 税率统一调整 | 0 | 1 | 2 | NULL | 2026-10-15 |
| 税率统一调整 | 0 | 1 | 2 | `{"min":"","max":""}` | 2026-10-14 |
| 税率统一调整 | 0 | 1 | 2 | `{"min":"","max":""}` | 2026-10-14 |
| 债权最高额限度（万元） | 0 | （空） | 2 | `{"min":"","max":""}` | 2025-02-23 |

**四条硬事实**：
1. 这 6 条**全部 is_system=0**（业务字段）。
2. **5 条是同一类业务模式**：`min=0, max=1`，其中 4 条 caption 为「税率统一调整」、1 条为「达成占比」——都是**比例/百分比**的典型值域（0～100%）。
3. 1 条 `min=0, max=''`（债权最高额限度，只有下界）。
4. **全部 `decimal_digits=2`**——与模板默认值 `2` 一致。
5. **vse 全部是空壳或 NULL**——说明值域是写进 `min`/`max` **两列**，而不是写进 `value_scope_expression`。这一条直接修正了 B2/B5 遗留的口径问题：**判"是否配过值域"要看 min/max 列，不能看 vse**。

⇒ 因此本片可以说：**在全库范围内，DECIMAL 是唯一有可证据化值域配置的类型**（6/4529 ≈ 0.13%）。
⇒ 但**不得**外推为"DECIMAL 普遍配值域"——配置率仍是极低的 0.13%。

### 4.5 vse 空壳（与 min/max 的关系被本片厘清）

```
DECIMAL  vse 非空 8 条，去重后仅 1 种值 {"min":"","max":""}（空壳）
CURRENCY vse 非空 0 条
```

**★ 比「两条独立通道」更强的实测事实（auditor 052240Z §三 指正，我复算成立）：**

逐条查那 6 条 min/max 有真值的行的 vse：

```
[1] 税率统一调整          min=0 max=1  vse={"min":"","max":""}   ← 空壳
[2] 达成占比             min=0 max=1  vse={"min":"","max":""}   ← 空壳
[3] 税率统一调整          min=0 max=1  vse=None                  ← NULL
[4] 税率统一调整          min=0 max=1  vse={"min":"","max":""}   ← 空壳
[5] 税率统一调整          min=0 max=1  vse={"min":"","max":""}   ← 空壳
[6] 债权最高额限度（万元）  min=0 max='' vse={"min":"","max":""}   ← 空壳
```

⇒ **5 条「min/max 有真值」的行，vse 同时是空壳**（第 6 条是 NULL）。
⇒ 不是"两条互斥通道"，而是 **同一行可以同时持有 min/max 真值 + vse 空壳，二者语义完全不重叠**。

**这个事实直接证伪了 B2/B5 的隐含方法。** B5 用「vse 非空 5 条全空壳」推「BigInteger 未配值域」——结论恰好对（BI min/max 确实全空），但**推理路径是错的**：vse 空壳根本不能推出"没配值域"，因为 DECIMAL 里 vse 空壳 + min/max 有真值同时成立。

**判「配没配值域」要看 min/max，不能看 vse —— 因为同一行可同时有 min/max 真值 + vse 空壳。**

### 4.6 decimal_digits 的真实取值分布

```
DECIMAL（10 种取值，共 4529 条）：
  4 位 2267 / 2 位 2130 / 6 位 51 / 10 位 49 / 8 位 18 /
  3 位 5 / 9 位 3 / 0 位 3 / 5 位 2 / 1 位 1

CURRENCY（2 种取值，共 107 条）：
  2 位 83 / 4 位 24
```

⇒ 模板默认 `decimalDigits: 2` **不是实际落库的默认值**：DECIMAL 里 4 位（2267）比 2 位（2130）还多。
⇒ 所以"模板默认 2" 是**前端表单初值**，与"创建时实际写入几"是两件事，不得混同（与 B5 的 defaultValue 结论同族）。
⇒ CURRENCY 只有 2/4 两位，取值域明显比 DECIMAL 窄。

### 4.7 本应用域

```
本应用类型分布：STRING 62 / ENTITY 35 / BIGINTEGER 27 / INTEGER 25 /
                DATETIME 22 / BOOLEAN 22 / CTPENUM 7 / MULTILINESTRING 3
| 本应用 DECIMAL 数 | **0** |
```

⇒ 本应用**一个 DECIMAL 字段都没有**。后续若要建 DECIMAL 字段做 LIVE 腿，属于**首次在该应用引入该类型**，需注意。

---

## 五、契约对照：batch DTO 中的 DECIMAL

### 5.1 结论：**VACUUM**

```
两份 EVIDENCE 的 DTO 层 dataType 取值集合：
  ev1: BOOLEAN, CTPENUM, DATETIME, ENTITY, INTEGER, STRING
  ev2: BOOLEAN, CTPENUM, DATETIME, ENTITY, INTEGER, STRING
  ⇒ DECIMAL 出现 0 次、CURRENCY 出现 0 次
```

⇒ 无任何字段级 DECIMAL 实例 ⇒ **VACUUM**，不升格、不外推。

### 5.2 必须区分的假阳性：`decimalDigits` 在 DTO 层是全员共有键

```
ev1 中 decimalDigits 出现 15 次；ev2 中 33 次
但 b2IntField（dataType=INTEGER）的 36 键请求 DTO 里：
  'decimalDigits' in dto  →  **False**（36 键不含它）
ev2 的 77 键响应 DTO 里：
  "dataType": "INTEGER", ..., "decimalDigits": 0, ...   ← 值为 0
```

⇒ `decimalDigits` 是**响应侧全员字段**（INTEGER 也有，值为 0），不是 Decimal 专属。
⇒ 用 `grep decimalDigits` 会得到"存在 DECIMAL 契约"的假阳性。**本片按字段级 DTO dataType 判定，结论 VACUUM。**
⇒ 这与 B5 §5.2 的 `grep BIGINTEGER` 假阳性是**同一类陷阱**，本片第二次遇到，已固化为检查项。

---

## 六、判定汇总与本切片不主张的事项

### 6.1 证据等级

| 结论 | 等级 | 依据 |
|---|---|---|
| E[Decimal] 17 键 / f[Decimal] 7 键 | **STATIC** | SEG-E、SEG-F 段落级反解 + 双 sha256 |
| E 层 Decimal 键集 == Currency（恒等） | **STATIC** | 集合比对 |
| f 层 Decimal vs Currency 差集 = {searchable} | **STATIC** | 集合比对 |
| 精度键唯一为 decimalDigits，仅 Decimal/Currency 携带 | **STATIC** | 14+16 表键名正则扫 |
| DECIMAL 全库 4529，全部业务字段 | **LIVE/DB** | §4.3 |
| min 非空 6 / max 非空 5（唯一成规模配置，占四类型 min 非空 7 条的 85.7%） | **LIVE/DB** | §4.4 |
| vse 与 min/max 语义不重叠（同一行可同时有 min/max 真值 + vse 空壳） | **LIVE/DB** | §4.5 |
| decimal_digits 实际分布 ≠ 模板默认 2 | **LIVE/DB** | §4.6 |
| 本应用 DECIMAL=0 | **LIVE/DB** | §4.7 |
| batch DTO 无 DECIMAL 实例 | **VACUUM** | §5.1 |
| Decimal 的请求 DTO 实际形态 | **UNVERIFIED** | 无实例；两批已捕获 DTO（1 实体/2 组/16 字段）内 DECIMAL 实例为 0，但全库 4529 条 DECIMAL 字段表明该类型真实存在，仅本抓包面未覆盖 |
| 页面可交互配值域 | **BLOCKED** | 登录态 |

### 6.2 明确**不**主张（防止后人误用）

1. **不得**说"DECIMAL 有值域配置能力就是 DECIMAL 特有"——min/max 键在 7/14 类型都有；真正配过的只有 DECIMAL 是**存量事实**，不是类型能力差异。
2. **不得**说"decimalDigits 能判别字段类型"——Currency 也有，且 DTO 响应侧 INTEGER 也带（值为 0）。
3. **不得**说"DECIMAL 的键集可判别它与 CURRENCY"——E 层**完全恒等**，一键不差。
4. **不得**把 6 条非空 min 当作"DECIMAL 普遍配值域"——配置率 6/4529 ≈ **0.13%**。
5. **不得**用 vse 判断是否配过值域——DECIMAL 的 6 条真实配置里 vse 全是空壳或 NULL，真实值在 `min`/`max` 列。

---

## 七、本切片边界执行情况

| 约束 | 执行 |
|---|---|
| 零页面操作 | ✅ 未开浏览器、未 attach、未导航 |
| 零 REST 业务请求 | ✅ 0 次 HTTP 到平台 |
| 零库写 | ✅ 全部 SELECT |
| 不跨组 | ✅ 未碰菜单/应用/其他组域 |
| 挂账清单零触及 | ✅ gate_b4_doc / gate_b2_docfix / B4-KEYCOUNT-ORIGIN / SLICE-B2-INTEGER-live 全未动 |
| commit 前缀 | ✅ `docs(entity-field-matrix)` |
| 只 add 本组文件 | ✅ 未 `git add -A` |

---

## 八、本切片遗留（供 main 派发）

1. **页面腿**：登录态恢复后，在本应用建一个 DECIMAL 字段 → 抓 batch DTO → 验证 `decimalDigits` 是否出现在请求、值是否等于表单所填；并尝试值域弹层设 min/max → 证"可交互配置"。
2. **DECIMAL 的 19 条 min=NULL 业务字段**：与"无系统字段"并存，本片不作解释；如需归因需按创建时间追溯（BIGINTEGER 侧这一数字恰等于系统字段数，DECIMAL 侧无对应物）。
3. **vse 真实配置样本**：全库 min/max 有 6 条真实配置但 vse 全空壳，**vse 到底在什么场景被写**仍未找到样本，需更大范围检索或页面腿取证。

### 8.1 闸门自证

沿用 B5 v3 标准 + main 051826Z 硬验收四条，逐条落实：

```
① §6.1 证据表整表逐行比对（不是抽样、不是只守标题段）—— F0 + F1-F12 共 13 条断言
② len(GRADE_ROWS) == §6.1 实际数据行数 —— F0 现算断言（防比对表截断）
③ 四码位 rc 全表（0/1/2/3 各贴该码位自身打印输出）—— D64
④ 内容破坏集 ≥ auditor 8 条 + 整表降格逐行 + 删段类
```

除此之外沿用 B5 的四条设计：
```
整行现算相等（非 has_num 存在即过）：§4.2/§4.3/§一/§6.1 的行全部由 B6-db.json 现算，
  改任一数字即整行失配。
等级 token 等价类：禁裸 LIVE / 纯 PASS（D3/D4 负向）。
注入矩阵 rc 与语义一致；锚点缺失 rc=3 独立，不计入被拦。
```

**① ② §6.1 整表逐行比对 + F0 长度断言（本片相对 B5 的结构性补强）**

B5 的缺口根因是 `GRADE_ROWS` 只写 7 条、§6.1 实际 12 数据行 ⇒ **比对表本身被截断**，5 行无覆盖，其中 3 行是 LIVE/DB ⇒ 降格 rc=0 静默放行。本片从第一版就按整表做：

```
GRADE_ROWS          12 条（= §6.1 全部数据行，逐行字面）
F0 长度断言          len(GRADE_ROWS) == 文档 §6.1 现算数据行数
F1-F12               逐行整行相等
F13 / F13b/c/d       等级分布计数五等级全覆盖：LIVE/DB 5、STATIC 4、VACUUM 1、UNVERIFIED 1、BLOCKED 1
F15 / F16            等级序关系绑定：文档等级 rank 不得高于/低于 baseline rank
F17 / F17b           ★等级-主张语义绑定（第三来源）+ 覆盖率断言
F18 / F18b/c/d/e     ★等级必须绑定基线 JSON 真实事实键，且由「来源类型」唯一决定等级
F19                  ★VACUUM 行的主张必须自带域限定（防小样本冒充平台级结论）
```

**★ F15/F16 是相对 B5 D4 的机制升级（auditor 052240Z §四-2 指正，采纳）：**

```
LEVEL_RANK = {UNVERIFIED:0, BLOCKED:0, STATIC:1, "STATIC-存在":1, VACUUM:1, LIVE/DB:2}
```

D4 是**白名单/黑名单**——只能禁"某几个 token"。B6 的 `**LIVE/DB**` 是主力等级 token（5 行），
白名单逻辑在这里正好失效：`STATIC → LIVE/DB` 完全合法，D4 不报错。
**这等于「静态推断冒充实测」这条最危险的方向完全敞开。**

F15/F16 改为**序关系**（rank 比较），表达"不许变高/不许变低"，而不是"不许出现某 token"。

**⚠️ 更正（auditor 053205Z §二 实测，我复算成立）：`BASELINE_RANK` 来自 `GRADE_ROWS`，不是"不读比对表"。**

```
BASELINE_RANK = [LEVEL_RANK[_LVL_RE.search(r).group(1)] for r in GRADE_ROWS]
```

⇒ 文档 + `GRADE_ROWS` **同步**改时，`BASELINE_RANK` 跟着变，**F15/F16 贡献为零**。
我上一版这里写"BASELINE_RANK 从闸门常量表现算，连共谋攻击也堵得住"——**这句话是错的，撤回**。
常数是 `LEVEL_RANK`，但每行的 baseline 值是从 `GRADE_ROWS` 的对应行取出来的，不是独立常量。

**共谋场景真正兜底的是 F13/F14 分布计数**（LIVE/DB=5 实得 4 被抓），不是 F15/F16。

**★ 且 F13/F14 对「跨级共谋」也无能为力（auditor 053205Z §四 提出，我实测证实）：**
把一条 `LIVE/DB` 行改成 `BLOCKED`、同时把 `BLOCKED` 行改成 `LIVE/DB`，
**五个等级的行数分布完全不变**（实测 `{'STATIC':4,'LIVE/DB':5,'VACUUM':1,'UNVERIFIED':1,'BLOCKED':1}` 前后相同），
分布计数天然看不出。仅扩成五等级计数（auditor 的建议）**仍不够**。

**⇒ 根治方案：F17 等级-主张语义绑定（第三来源）**

`F0`–`F12`、`F13/F13b–d`、`F15/F16` 全部挂在 `GRADE_ROWS` 上，共谋下一起失效。
`F17` 引入**与 `GRADE_ROWS` 无关的第三结构**：按「主张文本 → 该主张只能由哪类证据源验证」绑定。

```
CLAIM_LEVEL = [
  ("E[Decimal] 17 键 / f[Decimal] 7 键",  "STATIC"),    # 只能来自 bundle 反解
  ("E 层 Decimal 键集 == Currency",       "STATIC"),
  ("f 层 Decimal vs Currency 差集",       "STATIC"),
  ("精度键唯一为 decimalDigits",          "STATIC"),
  ("DECIMAL 全库 4529",                   "LIVE/DB"),   # 只能来自 DB 回读
  ("min 非空 6 / max 非空 5",             "LIVE/DB"),
  ("vse 与 min/max 语义不重叠",           "LIVE/DB"),
  ("decimal_digits 实际分布",             "LIVE/DB"),
  ("本应用 DECIMAL=0",                    "LIVE/DB"),
  ("batch DTO 无 DECIMAL 实例",           "VACUUM"),    # 域内零实例
  ("Decimal 的请求 DTO 实际形态",         "UNVERIFIED"),
  ("页面可交互配值域",                    "BLOCKED"),   # 登录态阻塞
]
```

理由是**证据源类型学**，不是"作者记得的数字"：一个只能靠 DB 回读得到的事实，
写成 `STATIC` 就是错的，与 `GRADE_ROWS` 怎么写无关。攻击者要绕过，必须连这张语义表一起改——
而改它等于承认自己在编造证据来源，比改数字更容易被审出来。

另有 `F17b`：`CLAIM_LEVEL` 必须覆盖 §6.1 全部行（防新增行未登记）。

**跨级共谋实测（`docs/audit/artifacts/scratch-migrated/audit-slice-b7/b7_f17_verify_v3.py`，沙箱 tempfile 零写盘）：**

```
步骤 0 三变体基线均 rc=0（完整 115 / 去F17 113 / 去F17+F15F16 111 PASS）
       F17 断言调用数：完整=2，去F17=0  ⇒ 删除确实生效（不是把脚本改坏）

攻击：文档 + GRADE_ROWS 同步互换 LIVE/DB ↔ BLOCKED
  改前/改后等级分布完全相同 {'STATIC':4,'LIVE/DB':5,'VACUUM':1,'UNVERIFIED':1,'BLOCKED':1}

  完整闸门          rc=1  触发 F17                          → 拦住
  去 F17            rc=0  无触发                            → ★★ 全漏
  去 F17+F15/F16    rc=0  无触发                            → ★★ 全漏
```

⇒ **F17 是本片唯一能拦跨级共谋的机制，不可替代。**
单边改 48/48 全拦（F0–F16 已足够），F17 专治共谋。

**★★ F17 的依赖边界（auditor 054702Z §四 实测，我独立复现，这条必须写进文档）**

F17 的 `CLAIM_LEVEL`、`F13b/c` 期望、`GRADE_ROWS` 都与文档在**同一个可写面**内。
我把它们**五处一起改**（即 071ee0a 那次操作），闸门看到「期望」与「实际」同时移位 ⇒ **rc=0 全绿放行**。

四条实测（`docs/audit/artifacts/scratch-migrated/audit-slice-b7/b7_f17_boundary_probe.py`，用 `git show` 取两个历史 blob）：

```
A  gate=574ad05  doc=574ad05   rc=0  115 PASS          ← 正常基线
B  gate=071ee0a  doc=071ee0a   rc=0  115 PASS  FAIL=0  ← ★ 改错方向也全绿
C  gate=071ee0a  doc=574ad05   rc=1  F16/F11/F17       ← 只改一处，拦住
D  gate=574ad05  doc=071ee0a   rc=1  F15/F11/F17       ← 只改一处，拦住（此为 574ad05 版闸门，尚无 F18d）
```

**而且这个漏洞是双向的**：我把 071ee0a 的 VACUUM 态**五处同步改回** UNVERIFIED，
同样 `rc=0 / 115 PASS / FAIL=0`。

⇒ 不是「改错方向」的单向漏洞，是 **F17 只能防住「忘改其中一处」**。
**「独立于 GRADE_ROWS」≠「独立于被测面」**——这是我上一版没写清的限定。

**★ 修补：F18 系列（等级从事实反推，不再靠常量表自证）**

```
F18    每条主张必须能绑定到基线 JSON 的真实事实键（不许凭空写数）
F18b   FACT_BIND 全部键可达（防写错路径后静默跳过）
F18c   ★ 等级由「来源类型」唯一决定：static→STATIC / db→LIVE/DB / vacuum→VACUUM
F18d   ★ 无事实键的行（显式登记于 NO_FACT_CLAIMS）等级只能是 UNVERIFIED/BLOCKED
F18e   NO_FACT_CLAIMS 全部能在 §6.1 找到对应行（防声明失效后静默跳过）
F19    VACUUM 行主张必须自带域限定（batch/这批/本次/已捕获/抓包/样本）
```

F18c 的理论依据是**证据类型学**，不是偏好：
- 只能由 bundle 反解得出的 → `STATIC`
- 只能由 DB 回读得出的 → `LIVE/DB`
- 域内穷尽且为空 → `VACUUM`
- **没有任何事实键可绑定的主张，三条路都走不通 ⇒ 只能是 `UNVERIFIED` 或 `BLOCKED`**

**五处同步改的三种攻击实测全部被 F18d 拦（`b7_f18_bypass_test.py`）：**

```
D66 负样本（单边改 → 必须拦）           rc=1  拦住[F1]          ← 先证明闸门有效
攻击 1 五处全同步改 VACUUM             rc=1  FAIL F18d         ← 复刻 071ee0a 手法
攻击 2 五处同步 + 加域限定骗 F19        rc=1  FAIL F18d
攻击 3 改成 STATIC（跨源伪造）          rc=1  FAIL F18d
```

⇒ **攻击者现在必须连「这行有没有事实支撑」一起伪造**，而那是编造取证产物，与改数字不是一个量级的成本。

**★★★ 闸门的固有边界（main 055409Z §4 实测 + 我独立复现，写进结论防止后人误读）**

**任何文档闸门都拦不住「gate 与 doc 完整自洽」的共谋。**

| 组 | 配置 | rc | 说明 |
|---|---|---|---|
| A | 574ad05 gate + 574ad05 doc | 0 | 正确基线 |
| B | 071ee0a gate + 071ee0a doc | **0** | ★ 旧违规态**用它自己的闸门**跑，全绿 |
| B' | HEAD gate + 071ee0a doc | 1 | 新闸门跑旧文档 → **F15/F11/F17/F18d 拦**（F18d 是 071ee0a 时不存在的层，对旧文档额外命中） |
| B'' | 071ee0a gate + HEAD doc | 1 | 旧闸门跑新文档 → F16/F11/F17 拦 |
| C | HEAD gate + HEAD doc | 0 | 当前终态 |

**B 组 rc=0 的正确解读（这条必须精确，否则会被误引）：**
- 它证明的不是「新闸门无效」，而是 **「闸门只能校验与自己配套的文档」**。
- 攻击者若把「文档 + GRADE_ROWS + CLAIM_LEVEL + F13 期望 + FACT_BIND 事实键」全改自洽，
  闸门看到的「预期」与「实际」同时移位，无法分辨改对还是改错。
- B'/B'' 说明：**跨版本混搭时闸门是有效的**（这是日常最可能出现的错误形态 —— 忘了同步改一处）。

**所以 F18/F19 的真实价值是：**
1. 把「忘改一处」的检出率从 F17 的水平再抬高一层（跨源伪造 STATIC 也被拦）；
2. 把共谋成本从「改 5 处数字」抬到「改 5 处 + 造 3 个 JSON 事实键 + 保证键值自洽」。

**但性质没变**：仍是同一攻击者可改全部。**单点从 F17 转移到了 F18/F19，没有消失。**

**这是自证体系的固有边界，不是缺陷。** 闸门能证明「文档与产物自洽」，**不能证明「产物为真」**。
后者只能靠：
- 闸门外的独立复算（auditor 每轮做的那种，读原始 bundle / 重连 DB）；
- 或不可写外部锚（签名 / 时间戳 / 第三方存证）。

**⇒ 停止在闸门内继续加层。** 往下的成本（bundle/DB 现场推导纳入闸门）远超收益，三方上轮已判不做。
后人不要把「F18 之后闸门全绿」读成「证据为真」。

F0 的 `_sec61_data_rows()` 同样从文档**现算**行数（排除表头与分隔行），不用闸门自身常量——否则又是「自己给自己出题」。

**整表降格 / 升格破坏实测（`docs/audit/artifacts/scratch-migrated/audit-slice-b6/b6_grade_reverse.py`，逐行单独施加，tempfile 副本零写盘）：**

```
| # | 原等级 | 方向 | rc |    | # | 原等级 | 方向 | rc |
|---|--------|------|----|    |---|--------|------|----|
| 1 | STATIC   | →LIVE/DB 升格 | 1 |    | 7 | LIVE/DB  | →BLOCKED 降格 | 1 |
| 1 | STATIC   | →BLOCKED 降格 | 1 |    | 8 | LIVE/DB  | →BLOCKED 降格 | 1 |
| 2 | STATIC   | →LIVE/DB 升格 | 1 |    | 9 | LIVE/DB  | →BLOCKED 降格 | 1 |
| 2 | STATIC   | →BLOCKED 降格 | 1 |    | 10| VACUUM   | →LIVE/DB 升格 | 1 |
| 3 | STATIC   | →LIVE/DB 升格 | 1 |    | 10| VACUUM   | →BLOCKED 降格 | 1 |
| 3 | STATIC   | →BLOCKED 降格 | 1 |    | 11| UNVERIFIED| →LIVE/DB 升格 | 1 |
| 4 | STATIC   | →LIVE/DB 升格 | 1 |    | 12| BLOCKED  | →LIVE/DB 升格 | 1 |
| 4 | STATIC   | →BLOCKED 降格 | 1 |    |   |          |               |   |
| 5 | LIVE/DB  | →BLOCKED 降格 | 1 |    |   |          |               |   |
| 6 | LIVE/DB  | →BLOCKED 降格 | 1 |    |   |          |               |   |

升格拦截 7/7   降格拦截 10/10   合计 17/17
共谋攻击（文档+GRADE_ROWS 同步单行降格）  rc=1  F13/F14 分布计数拦住（非 F15/F16）
跨级共谋（LIVE/DB↔BLOCKED 互换，分布不变）完整闸门 rc=1 / 去 F17 rc=0  ⇒ F17 必需
```

⇒ 降格模式（B5 三次复发的那条）与升格模式（B6 首次暴露的那条）在本片**双向全拦**，
由 F0（比对表截断）+ F13/F13b–d（五等级分布）+ F15/F16（序关系）+ **F17（等级-主张语义绑定）**
四层兜底。**其中 F17 是唯一能拦"分布不变型"跨级共谋的机制**——其余三层全部挂在 `GRADE_ROWS` 上，
共谋时一起失效（实测去 F17 后 rc=0 全漏）。

**四码位 rc 全表（D64 立法要求，各贴该码位自身的输出）**：
```
$ python tools/audit/gate_b6_decimal.py
  SUMMARY PASS=108 FAIL=0
  GATE PASS  (B6：DECIMAL STATIC 反解 + DB 回读 + 契约 VACUUM)         EXIT=0

$ python tools/audit/gate_b6_decimal.py --inject N1
  == 注入 N1: DECIMAL 总数 4529→4530 ==
  GATE BLOCKED 注入 N1（rc=1）                                        EXIT=1

$ python tools/audit/gate_b6_decimal.py --inject SELFCHECK
  == 注入 SELFCHECK: 等价改写（标题加尾随空格）——2 码位可达性 ==
  GATE LEAK —— 注入 SELFCHECK 未被拦截（rc=2）                         EXIT=2

$ python tools/audit/gate_b6_decimal.py --inject NOPE
  INJECT KEY NOT FOUND: NOPE（可用: N1,N10,...,SELFCHECK）             EXIT=3
```

**注入矩阵 14/14 全拦**（N1..N14 逐条 rc=1）：
```
DECIMAL 总数 4529→4530 / min 非空 6→7 / E 键数 17→16 / f 键数 7→6 /
结论表 STATIC→LIVE / decimalDigits 少 s / is_system 列换总数 / CURRENCY 107→108 /
禁令句式反转 / 集合相等→不等 / VACUUM→PASS / SEG-E sha256 被改 /
交叉表 min 6→7 / digits 2267→2268
```

**结构性删除防护**（沿用 B5 J 组思路）：
```
删「§6.2 明确不主张」整段   → rc=1 拦下
删「§5.2 grep 假阳性」整段  → rc=1 拦下
```

> 本片闸门首跑出现 6 条注入 rc=3（锚点未命中），即 B5 v1 的同族问题：注入没真正施加却出现在矩阵里。
> 已按文档真实文本（`vs` 而非「与」、交叉表列序、digits 行格式）逐条修正锚点，复跑 14/14 全 rc=1。
> **教训固化：注入锚点必须取自文档实际文本，不能用「我以为的格式」。**

---

## 九、A/B 对照：本片修正的错口径

> 本节引用错口径仅作对照，闸门负向断言作用域止于 §八，不含本节。

| # | 错口径 | 本片事实 |
|---|---|---|
| 1 | 「看 vse 判断配没配值域」 | DECIMAL 的 6 条真实配置行 vse 全是空壳/NULL，真值在 `min`/`max` 两列 ⇒ **同一行可同时持有 min/max 真值 + vse 空壳，二者语义不重叠**。B5 用「vse 全空壳」推「未配值域」结论对但路径错 |
| 2 | 「decimalDigits 默认 2 ⇒ 库里都是 2」 | 实际 4 位 2267 条 > 2 位 2130 条，模板默认 ≠ 落库实际 |
| 3 | 「decimalDigits 是 Decimal 专属」 | Currency 也有，DTO 响应侧 INTEGER 也带（值 0） |
| 4 | 「DECIMAL 与 CURRENCY 可用键集区分」 | E 层键集**完全恒等**，唯一差异在 f 层 `searchable` |
| 5 | 「min NULL=系统字段」规律普适 | DECIMAL **无系统字段**，4529 条全业务，该规律不适用 |
