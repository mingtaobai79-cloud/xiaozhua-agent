# SLICE-B5｜实体字段类型矩阵第 4 类 BigInteger —— STATIC / DB 前置腿

- 日期：2026-10-18（GMT+8）
- 环境：test2，库 `udc_test2`
- 应用：`datamigration9000000000000000001`（数据迁移）
- HANDOFF：`20261018T044506Z-main-to-implementer-HANDOFF`（B5 单一活动切片）
- 证据脚本（只读，全部在仓库内可复跑）：
  - `docs/audit/artifacts/scratch-migrated/audit-slice-b5/b5_anchor_verify.py` —— 两份 bundle 的 E 表段字节比对
  - `docs/audit/artifacts/scratch-migrated/audit-slice-b5/b5_keyset_reverse_v2.py` —— 14 表键集反解
  - `docs/audit/artifacts/scratch-migrated/audit-slice-b5/b5_land_segments.py` —— 段落级落地 + 双 sha256
  - `docs/audit/artifacts/scratch-migrated/audit-slice-b5/b5_diff_keys.py` —— 逐键值差分
  - `docs/audit/artifacts/scratch-migrated/audit-slice-b5/b5_facts.py` —— DB 事实汇总（生成 `B5-DB-FACTS.json`）
  - `tools/audit/gate_b5_bigint_v2.py` —— 本切片闸门（104 断言全绿；14 条注入 14/14 拦截；退出码三档实测可达）
- 边界：**零页面操作、零 REST 业务请求、零库写**。DB 全程只读 SELECT；git 只读 + 本片 commit。

---

## 一、一句话结论

| 项 | 结论 | 等级 |
|---|---|---|
| **STATIC：BigInteger 类型表键集** | `E[BigInteger]` **17 键**、`f[BigInteger]` **6 键**，**键集与 Integer 完全相同**（集合级），仅 `dataType` 字面量与 `defaultValue` 默认值两处不同 | **STATIC** |
| **STATIC：min/max 归属** | `min`/`max` 同时出现在 **7/14** 张 E 表与 7/16 张 f 表，BigInteger **在组内**（与 Integer/Decimal/Currency/Date/Time/DateTime 同组） | **STATIC** |
| **STATIC：值域边界** | WB 区间表：BigInteger = **±9007199254740991（2^53−1，字符串形态）**；Integer = ±2147483648/2147483647（数值形态） | **STATIC** |
| **DB：BigInteger 全库** | **4576** 行；`min` 非空 **0**、`max` 非空 **0**；与 INTEGER **3539** 行 / min 非空 **1** / max 非空 **0** 同表对照 | **LIVE/DB** |
| **DB：vse 非空** | 5 条"非空"全是空壳 `{"min":"","max":""}`，去重后仅 1 种值 ⇒ **非空 ≠ 配过值域** | **LIVE/DB** |
| **契约对照：batch DTO** | 两份 EVIDENCE 中**无任何字段级 BIGINTEGER 实例**（DTO 的 dataType 仅见 STRING/INTEGER/CTPENUM/ENTITY/DATETIME/BOOLEAN） | **VACUUM** |
| **触发条件充分性** | BigInteger 与 Integer 键集相同 ⇒ 键集**无类型判别力**，无法由键集反推"当前是 BigInteger" | **UNVERIFIED** |
| **页面可交互配值域** | 需页面腿，登录态冻结 | **BLOCKED** |

> 本切片不含「页面新建 BigInteger 字段」的 LIVE 腿（HANDOFF 明示已单列待办）。

---

## 二、反解源锚（双 sha256）

### 2.1 一份重要事实：仓库内 bundle 副本与 cache 原件不是同一字节流

```
仓库副本 docs/audit/artifacts/udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js
  size    = 2,530,724
  sha256  = 6051e1df6c574df74c842f9e4c0714fae5c7ff0df6e86e5ffa5b2d4f994f387d

cache 原件 <HERMES_HOME>/cache/scratch/src_redux_store_ts.14dc061e.js
  size    = 2,530,725
  sha256  = dec48b500e2c655a1ca279b17d5f6128c8871c1d266f12e49cf0d2ff23345f94
```

`cmp -l` 显示两者自偏移 **2,349,062** 起整体位移 1 字节（尾部多/少 1 字节）。

**但 E 表段不受影响**（这是本片必须先钉死的前置）：

```
E 表段起点 = 1,588,313（两份相同）
段长       = 4,666
段 sha256  = 62869f1230be89074d5974a732eccc5edcb77044e7ea454118245628c589d645（两份相等）
段去 'E={' 与尾逗号后 = 4,663B
  sha256   = b1e75e105c0dedefeaec5301fec38d22bbde71df864dc36f47188004b9f1e84f
  ⇒ 与 auditor 已钉死锚 b1e75e10… 逐字节相等（跨组互证）
```

⇒ 反解源结论**只依赖段落，不依赖整文件**；两份 bundle 的整文件差异落在 2,349,062 之后，与 E 段无交集。

### 2.2 本片新落地的三个段落（仓库内，不依赖 cache）

| 段落 | 文件 | 字符偏移（非字节） | 长度 | 段 sha256 |
|---|---|---|---|---|
| SEG-E（E[type] 提交默认表，14 表） | `docs/audit/entity-field-matrix/assets/bundle-SEG-E_Etable.js.txt` | 1,521,061 | 4,666 | `62869f1230be89074d5974a732eccc5edcb77044e7ea454118245628c589d645` |
| SEG-T（WB 区间表，6 类型值域边界） | `docs/audit/entity-field-matrix/assets/bundle-SEG-T_WB_range.js.txt` | 1,525,727 | 298 | `f5483b41efaf6b55546d7f2f3aefb7c8bdd17472791b670ae19ee8527688901e` |
| SEG-F（f[type] 表单默认表，16 表） | `docs/audit/entity-field-matrix/assets/bundle-SEG-F_ftable.js.txt` | 1,519,607 | 1,454 | `db90ee1f4d1f8c393de97533f8fdb0b478222e1d1501c0186b4aead08bf21221` |

> **口径提醒（易踩坑）**：本表偏移是 **Python 字符串下标（字符偏移）**，因为反解在 `decode('utf-8')` 后的 str 上做。
> §2.1 的 `1,588,313` 是 **`bytes` 下标（字节偏移）**，因为段比对在 `read_bytes()` 上做。
> 两者差恒 **67,252** = 33,626 个三字节字符各自多出的 2 字节（`len(str)` 与 `len(bytes)` 的差），
> 三个段落起点实测 diff 全部为 67,252，各自成立、**互不矛盾**。
> 长度列同理：SEG-E 4666 是字符数，字节数更大。审计方第一轮也判过"自相矛盾"，逐字节取证后确认两者都对。

> SEG-E 与既有资产 `bundle-type-default-tables.js.txt`（7,687B，sha256 `1b7bffc7…`）中的 E 段逐字节一致，两处互为副本。

---

## 三、BigInteger 类型表键集（STATIC）

### 3.1 E[BigInteger] 原文（17 键）

```
{dataType:"BIGINTEGER",notNull:!1,searchable:!1,defaultValue:"",expressionDesignData:"",
 expressionRuntimeData:"",uniqueness:!1,auditLog:!1,min:"",max:"",
 defaultValueSystemVariable:"",defaultValueExpressionDesignData:"",
 defaultValueExpressionRuntimeData:"",defaultValueIsChange:!0,calculate:"NORMAL",
 sourceType:"ENTITY",columnName:""}
```

键集（17）：
```
dataType, notNull, searchable, defaultValue, expressionDesignData, expressionRuntimeData,
uniqueness, auditLog, min, max, defaultValueSystemVariable,
defaultValueExpressionDesignData, defaultValueExpressionRuntimeData,
defaultValueIsChange, calculate, sourceType, columnName
```

### 3.2 E[Integer] 原文（17 键）

```
{dataType:"INTEGER",notNull:!1,searchable:!1,defaultValue:0,defaultValueSystemVariable:"",
 defaultValueExpressionDesignData:"",defaultValueExpressionRuntimeData:"",
 expressionDesignData:"",expressionRuntimeData:"",uniqueness:!1,min:"",max:"",
 auditLog:!1,defaultValueIsChange:!0,calculate:"NORMAL",sourceType:"ENTITY",columnName:""}
```

### 3.3 差分结论（这是本片核心）

```
E 层：|keys(BigInteger)| = 17，|keys(Integer)| = 17
      set 相等 = True      键序相同 = False（第 5 个键起顺序不同）
      值相同键数 = 15 / 17
      值不同的键：只有 2 个
        dataType      : "BIGINTEGER"  vs  "INTEGER"
        defaultValue  : ""            vs  0

f 层：|keys| = 6 / 6，set 相等 = True，键序相同 = True，值相同键数 = 6/6
      （两者 defaultValue 都是占位 p，连默认值都不区分）
```

⇒ **BigInteger 与 Integer 在模板层面是「同形状、异字面量」**：键集完全相同，唯一实质差异是 `dataType` 字符串和提交默认表里 `defaultValue` 的初值形态（`""` vs `0`）。

⇒ 推论（重要，防止后人误用）：**不能由键集反推字段类型**。B4 已证 36 键精简 DTO 的接受集是 {Integer, BigInteger, Date, Time, DateTime} 5/14，本片进一步证明「连 BigInteger 与 Integer 之间都无法用键集区分」——两者键集是**恒等**，不是"接近"。

### 3.4 min/max 归属（对照 14 表结论第①条）

```
含 min 且含 max 的类型（E 层，7/14）：
  BigInteger, Currency, Date, DateTime, Decimal, Integer, Time
不含（7/14）：String, MultilineString, Boolean, Enum, CtpEnum, Entity, Attachment
f 层同样 7 张（f 表共 16 张，多出 PERSONSELECTOR / Serial 两张，均不含 min/max）
```

⇒ BigInteger **确在 7/14 值域键组内**，与 HANDOFF 引用的结论第①条一致。
⇒ 但「键存在 ≠ 有值 ≠ 可通过 UI 配」，三层不可混同（见 §五、§六）。

### 3.5 值域边界（WB 区间表，本片新增证据）

```
T={[a.String]:{min:0,max:4e3},
   [a.MultilineString]:{min:0,max:1e4},
   [a.Integer]:{min:-2147483648,max:2147483647},
   [a.BigInteger]:{min:"-9007199254740991",max:"9007199254740991"},
   [a.Decimal]:{min:"-9007199254740991",max:"9007199254740991"},
   [a.Currency]:{min:"-9007199254740991",max:"9007199254740991"}}
```

| 类型 | min | max | 形态 |
|---|---|---|---|
| Integer | `-2147483648` | `2147483647` | 数值字面量（±2^31） |
| BigInteger | `"-9007199254740991"` | `"9007199254740991"` | **字符串字面量**（±(2^53−1)） |

两点必须记账：
1. **BigInteger 与 Decimal/Currency 的边界完全相同**（都是 ±(2^53−1)），不是 BigInteger 专属。⇒ 该边界**无类型判别力**，只能否证"超出 2^53 的值"。
2. 形态不同（数值 vs 字符串）是**前端实现细节的静态事实**，本片**未证明**它是否在提交时被强制；不得据此推出"BigInteger 提交必传字符串"（batch EVIDENCE 中无 BigInteger 字段实例，无对照面，见 §六）。
3. `WB` 导出在 bundle 内**未找到任何调用点**（`grep '\.WB('` = 0 命中，全 chunk 仅 1 个文件，已穷举）。⇒ 该表**存在但未证被使用**，等级只能记 STATIC-存在，不能记 STATIC-生效。

---

## 四、DB 回读（LIVE/DB）

### 4.1 存储字面量确认（HANDOFF 要求"不要猜"）

先从 DB 全库 `data_type` 枚举取值，与 bundle 枚举交叉验证：

```
SELECT data_type, COUNT(*) n FROM udc_attribute GROUP BY data_type ORDER BY n DESC;

STRING           20496      BIGINTEGER        4576      DATE              1364
ENTITY           13468      DECIMAL           4529      MULTILINESTRING    652
DATETIME          8522      INTEGER           3539      ATTACHMENT         287
BOOLEAN           4953      ENUM              2834      Serial             213
                           CTPENUM           2133      TIME               188
                                                      CURRENCY           107
                                                      CONTENT              3
```

⇒ **存储字面量是 `BIGINTEGER`（全大写、无下划线），不是 `BIGINT`**，与 bundle 枚举 `e.BigInteger="BIGINTEGER"` 完全一致。
（`BIGINT` 是 MySQL 列类型 `bigint(20)` 的写法，与字段 data_type 无关——两者极易混淆，此处显式区分。）

### 4.2 BIGINTEGER vs INTEGER 同表对照

查询时刻 `2026-10-18 12:50:52`，全库 `udc_attribute` 总行数 **67864**（B2 时为 67862，期间他组有写入，与本源无关）。

```sql
SELECT data_type,
       COUNT(*) AS total,
       SUM(CASE WHEN min IS NULL THEN 1 ELSE 0 END)  AS min_null,
       SUM(CASE WHEN min='' THEN 1 ELSE 0 END)       AS min_empty,
       SUM(CASE WHEN min IS NOT NULL AND min<>'' THEN 1 ELSE 0 END) AS min_nonempty
FROM udc_attribute WHERE data_type IN ('BIGINTEGER','INTEGER')
GROUP BY data_type;
```

| data_type | total | min 三态（NULL / 空串 / 非空） | max 三态（NULL / 空串 / 非空） |
|---|---|---|---|
| **BIGINTEGER** | **4576** | 3628 / 948 / **0** | 3628 / 948 / **0** |
| **INTEGER** | **3539** | 2829 / 709 / **1** | 2829 / 710 / **0** |

### 4.3 ★ 关键结构发现：min 的 NULL 与空串精确对应「系统字段 / 业务字段」

```sql
SELECT is_system,
  SUM(min IS NULL) min_null, SUM(min='') min_empty, COUNT(*) total
FROM udc_attribute WHERE data_type='BIGINTEGER' GROUP BY is_system;
```

| data_type | is_system | total | min NULL | min 空串 | min 非空 |
|---|---|---|---|---|---|
| BIGINTEGER | 1（系统） | 3628 | **3628** | 0 | 0 |
| BIGINTEGER | 0（业务） | 948 | 0 | **948** | 0 |
| INTEGER | 1（系统） | 2824 | **2824** | 0 | 0 |
| INTEGER | 0（业务） | 715 | 5 | **709** | 1 |

⇒ 交叉表**完全解耦且零残差**：系统字段的 `min`/`max` 一律 **NULL**，业务字段一律**空串**。
⇒ 这解释了 4.2 表里 3628/948 的精确吻合不是巧合，而是**两条不同的写入路径**：
  - 系统字段（继承/平台预置）走**不给值域列赋值**（NULL）
  - 业务字段（设计器建/改）走**显式写空串**（`''`）
⇒ **这才是"键不适用 vs 键适用但未配置"的真实表达**：NULL 与 `''` 语义不同，不能合并统计。B2 的 INTEGER 基线（2829/709/1）同样是 2824+5 与 709 的组合 —— **本次把 B2 里"5 个 min=NULL 的业务 INTEGER"的来历查清了**（见 4.5）。

### 4.4 vse（value_scope_expression）非空 ≠ 配过值域

```sql
SELECT value_scope_expression vse, COUNT(*) n FROM udc_attribute
WHERE data_type='BIGINTEGER' AND value_scope_expression IS NOT NULL AND value_scope_expression<>''
GROUP BY vse;
```

```
{"min":"","max":""}    →  5 条
（去重后仅此 1 种值）
```

INTEGER 侧同口径 **1 条**，值同样是 `{"min":"","max":""}`。

⇒ **5 条"非空 vse"全是空壳**，其 `min`/`max` 两列本身也都是 `''`。
⇒ 所以 BIGINTEGER「可配值域」的**真实配置率 = 0**，不是 5。任何把"vse 非空"当"配过值域"的统计都是错的。

### 4.5 INTEGER 唯一的非空 min（B2 遗留个例已查明）

```sql
SELECT id,entity_id,name,caption,min,max,is_system,default_value,value_scope_expression,update_time
FROM udc_attribute WHERE data_type='INTEGER' AND min IS NOT NULL AND min<>'';
→ id=-3732152200587460387, name=gongGuanZhangHuID, caption=共管账户ID,
  min='0', max='', is_system=0, default_value='0',
  vse='{"min":"","max":""}', update_time=2025-02-23 11:34:41
```

⇒ 全库 3539 个 INTEGER 里**只有这 1 个** min 有值，值是 `'0'`，且它的 vse 仍是空壳、max 为空。
⇒ 这是一条**历史遗留的单点写入**（2025 年建），不构成"INTEGER 支持配值域"的证据。B2 §五 的"非空=1"口径正确。

另 5 个 `min IS NULL` 的 INTEGER 业务字段（B2 表里 715 的分子部分）：

```
caption=级次 ×4 (2026-03~04 建)  caption=实验数量 ×1 (2026-10-14 建)
```

⇒ 与本组探针字段（2026-10-18 建）**无关联**，不是本组写入残留。这批字段的 min 为 NULL 而非 `''`，说明"业务字段恒空串"在 INTEGER 侧**存在 5 个例外**（BIGINTEGER 侧是 0 例外）。此差异如实记录，**不作因果解释**（无证据）。

### 4.6 max_length 与默认值

```
BIGINTEGER 业务字段(948)：max_length 全部 = '20'
INTEGER   业务字段(715)：max_length 全部 = '10'
```

⇒ 与 WB 边界方向一致（2^53−1 需 16 位十进制，2^31−1 需 10 位），但**20/10 是设计器落库的固定字面量，不是由 WB 表推导**——两者只是数值上不矛盾，本片不主张因果。

default_value 非空分布：

```
BIGINTEGER：'0' → 5 条（业务字段）  其余 943 空串 / 3628 NULL
INTEGER   ：'0' → 3424 条，'1' → 12 条   其余 102 空串 / 1 NULL
```

⇒ INTEGER 业务字段几乎全部被显式写成 `0`（3424/715 口径外，即含系统外全员），而 BIGINTEGER 只有 5 条。**这与 §3.3 的模板默认值差异（`defaultValue:0` vs `""`）方向一致**，但本片**未证明**这是模板直接落库的结果——可能是设计器默认行为，需页面腿区分（BLOCKED）。

### 4.7 本应用域（app_id=8704025620829192834）

```
类型分布：STRING 62 / ENTITY 35 / BIGINTEGER 27 / INTEGER 25 /
          DATETIME 22 / BOOLEAN 22 / CTPENUM 7 / MULTILINESTRING 3

BIGINTEGER 27 = 系统 18 + 业务 9
  系统：name=id (caption=ID) / name=tenantId (caption=租户ID)，成对出现
  业务 9：processedRows / totalRows / duration / batchId / fileSize /
          targetDatasourceId / sourceDatasourceId …
          全部 min='' max='' defaultValue='' max_length='20'
```

⇒ 本应用**已有 9 个 BigInteger 业务字段**，但**全部未配值域**（min/max 空串）。这是本应用域的现状基线，供后续页面腿对照。

---

## 五、契约对照：batch DTO 中 BigInteger 的实例

### 5.1 结论：**VACUUM**（域内 0 条可证据化 BigInteger 字段实例）

两份 EVIDENCE（`EVIDENCE-batch-contract-live.json` / `EVIDENCE-batch-update-live.json`）中：

```
DTO 层 dataType 取值集合（正则 "dataType"\s*:\s*"([A-Z_]+)" 全量提取）：
  ev1: BOOLEAN, CTPENUM, DATETIME, ENTITY, INTEGER, STRING
  ev2: BOOLEAN, CTPENUM, DATETIME, ENTITY, INTEGER, STRING
  ⇒ 无 BIGINTEGER
```

所以**无法**从现有 batch 证据得出 BigInteger 字段的请求 DTO 长什么样。**不升格、不外推**。

### 5.2 必须区分的一处易混：「BIGINTEGER」在 EVIDENCE 里出现过，但不是字段类型

```
ev1: BIGINTEGER 字符串出现 4 次   ev2: 8 次
全部形态：
  "defaultValueSystemVariable": "{\"type\":\"SYSTEM_VARIABLE\",
      \"value\":\"currentUserId\",\"desc\":\"登录人员ID\",\"dataType\":\"BIGINTEGER\"}"
  （另有 currentInstitutionId / currentOrgId / currentPostId 三条同构）
```

⇒ 这是**系统变量自身的数据类型声明**（登录人员 ID 是长整型），出现在系统字段的 `defaultValueSystemVariable` 里，**不是被建字段的 dataType**。
⇒ 用 `grep BIGINTEGER` 会得到"存在 BigInteger 契约"的假阳性。**本片按字段级 DTO dataType 判定，结论 VACUUM。**

### 5.3 可用的唯一间接对照（不足以升格）

现有 INTEGER 字段 `b2IntField` 的 36 键请求 DTO 中 `defaultValue: 0`（数值），与 §3.3 的 `E[Integer].defaultValue:0` 一致。
BigInteger 的模板默认是 `""`（字符串），但**无 BigInteger 字段 DTO 实例**可验证该默认是否真的以 `""` 出现在请求里。
⇒ 记 **UNVERIFIED**：模板默认 ≠ 请求实际值，需页面腿建一个 BigInteger 字段抓包。

---

## 六、判定汇总与本切片不主张的事项

### 6.1 证据等级

| 结论 | 等级 | 依据 |
|---|---|---|
| E[BigInteger] 17 键 / f[BigInteger] 6 键 | **STATIC** | SEG-E、SEG-F 段落级反解 + 双 sha256 |
| BigInteger 与 Integer 键集恒等 | **STATIC** | 集合比对（不是比键数） |
| min/max 在 7/14 类型表内，BigInteger 在组内 | **STATIC** | 14 表逐表扫 |
| WB 边界 ±(2^53−1)，形态为字符串 | **STATIC-存在** | SEG-T 段落；**未找到调用点**，不主张生效 |
| BIGINTEGER 全库 4576，min/max 非空 0/0 | **LIVE/DB** | SELECT 原文见 §4.2 |
| min NULL=系统字段数、空串=业务字段数（零残差） | **LIVE/DB** | 交叉表 §4.3 |
| vse 非空 5 条全空壳 | **LIVE/DB** | 去重仅 1 值 §4.4 |
| 本应用 27 个 BIGINTEGER（18 系统 + 9 业务），全部未配值域 | **LIVE/DB** | §4.7 |
| batch DTO 无 BigInteger 字段实例 | **VACUUM** | §5.1 全量正则提取 |
| BigInteger 字段的请求 DTO 实际形态 | **UNVERIFIED** | 无实例，需页面腿 |
| 触发条件（何时走重建分支） | **UNVERIFIED** | 沿用 B4 结论，n=1 |
| 页面可交互配值域 | **BLOCKED** | 登录态冻结 |

### 6.2 明确**不**主张（防止后人误用）

1. **不得**说"BigInteger 支持值域配置"——只能说它**有 min/max 两个键**，且键存在 ≠ 可配（7 个类型都有，全库配置率 0）。
2. **不得**说"键数/键集能判别 BigInteger"——恰恰相反，BigInteger 与 Integer 键集恒等，B4 的 36 键接受集 5/14 里两者不可分。
3. **不得**说"WB 边界生效"——该表在 bundle 内**无调用点**，只证存在。
4. **不得**说"BigInteger 提交必传字符串"——无 BigInteger DTO 实例，形态差异只是模板事实。
5. **不得**把 vse 非空的 5 条当"已配值域"——全是空壳。
6. **不得**把系统字段的 `min IS NULL` 与业务字段的 `min=''` 合并成"3628+948 未配置"——两者语义不同（不适用 vs 适用未配）。

---

## 七、本切片边界执行情况

| 约束 | 执行 |
|---|---|
| 零页面操作 | ✅ 未开浏览器、未 attach、未导航（登录态冻结期） |
| 零 REST 业务请求 | ✅ 0 次 HTTP 到平台 |
| 零库写 | ✅ 全部 SELECT；无 INSERT/UPDATE/DELETE/DDL |
| DB 只读 | ✅ pymysql 只执行 SELECT |
| D56 git 实读 | ✅ 动手前 `git log` 实读 HEAD=0033a8f，收口后确认未被他组覆盖 |
| commit 前缀 | ✅ `docs(entity-field-matrix):` |
| 不扩范围 | ✅ 未动页面腿、未建字段、未碰另一分支的 aud/ 文件 |

**限流**：本片 DB 查询 6 批（每批 1 连接、多条 SELECT），全部走内网 MySQL 直连，**不经过平台 `/service`**，因此不消耗 `/service ≤3/30s` 配额、不触发共享账号互踢风险。

---

## 八、本切片遗留（不属本片范围，供 main 派发）

1. **页面腿（LIVE）**：登录态恢复后，在设计器建一个 BigInteger 字段 → 抓 batch 请求 → 验证 `defaultValue` 实际是 `""` 还是 `0`；并在值域弹层尝试设 min/max → 证"可交互配置"。
2. **WB 表调用点**：`WB`（导出名 `T`）在整 chunk 内无 `.WB(` 命中 ⇒ 该表可能是历史遗留或经其他 chunk 引用，需全前端 bundle 扫描（本片只有 1 个 chunk，已穷举本文件）。
3. **INTEGER 侧 5 个 `min IS NULL` 业务字段**：与"业务字段恒空串"不符，本片不作解释，如需归因需按创建时间/操作人追溯设计器版本。

### 8.1 闸门自证（含一次必须记账的自查事故）

**v1 事故**：首版闸门 75 断言全绿，但注入矩阵 12 条**只拦住 4 条**——N2/N3/N5/N8/N11 全部漏检（rc=2）。

根因：数字断言写成 `has_num(BODY, n)`（"正文里存在这个数"）。
- `3628` 在正文出现 4 次，改掉 1 处仍有 3 处蒙混 → N8 漏检；
- `**STATIC**` 出现在多行，改掉表格 1 处别处还在 → N5 漏检；
- `**17 键**` 出现在多处 → N3 漏检。

这是 B4 教训「单边断言等于给自己出简单题」的**第 3 次复发**（B2 一次、B4 一次）。

**v2 结构性修正**（不是补几条断言）：
1. **期望整行由基线现算**：§4.2 / §4.3 / §一 / §6.1 的行，全部按 `B5-DB-FACTS.json` 与 `B5-keysets.json` 现算成完整字面行，与文档做**整行相等**比对（不是"包含"）。改任一数字 → 整行失配。
2. **等级 token 等价类约束**：本片只允许 `STATIC` / `STATIC-存在` / `LIVE/DB` / `VACUUM` / `UNVERIFIED` / `BLOCKED`；
   其余两个常见等级 token（裸 LIVE 与纯 PASS）必须 0 出现（负向断言）→ 把 VACUUM 改成纯 PASS、STATIC 改成裸 LIVE 会立即破坏等价类。
3. **键数从反解源现算**：断言 `**{len(keys)} 键**`，不写死。

**v2 实测**：
```
正常跑                    EXIT=0   PASS=119  FAIL=0
注入 N1..N14              EXIT=1   14/14 全部拦截
--inject SELFCHECK        EXIT=2   ← 2 码位实测可达（等价改写已施加但零 FAIL）
--selfcheck               EXIT=0   等价改写放行（防假阳性）
--inject NOPE             EXIT=3   未知注入键 → 锚点缺失语义
```

**三档退出码 0/1/2/3 全部实测可达**（不是"代码里有"）。`2` 与 `3` 的区别是本片被反复点名的坑：
- `--selfcheck`（独立开关）走「等价改写应**放行**」语义 → rc=0，用于防假阳性；
- `--inject SELFCHECK`（注入键）走「注入已施加但闸门零 FAIL」语义 → **rc=2**，证明漏检码位可达。
  main 050012Z ③ 与 auditor 045650Z 都指过：v2 早期 `--inject SELFCHECK` 落进「未知键」分支返回 rc=3，
  等于「2 可达」仍只是代码里有。**把 SELFCHECK 正式登记进 INJ_TABLE 才真正打通。**

**环境失败反向验证**（`docs/audit/artifacts/scratch-migrated/audit-slice-b5/b5_env_failure_probe.py`）：
```
（无，全备）        rc=0   GATE PASS
bundle 原件缺失    rc=3   ANCHOR NOT FOUND: bundle
SEG-E/T/F 缺失     rc=3   ANCHOR NOT FOUND: asset_E / asset_T / asset_F
DB 基线缺失        rc=3   ANCHOR NOT FOUND: facts
keysets 缺失       rc=3   ANCHOR NOT FOUND: keysets
文档缺失           rc=3   ANCHOR NOT FOUND: doc
⇒ 7/7 场景均 rc=3，无假 PASS（rc=0）、无与被拦（rc=1）混淆
```

因此「2 可达」的准确表述是：**2 码位已实测可达**——由 `--inject SELFCHECK`（等价改写已施加、闸门零 FAIL）
直接打印 `GATE LEAK —— 注入 SELFCHECK 未被拦截（rc=2）` 并返回 2，这是该码位被打印出来的那次运行，
不是相邻码位的健康运行（D64 立法：写「实测可达」必须贴该码位自身的输出）。
另注：锚点缺失的 7/7 rc=3 证明的是**锚点缺失语义**正确，与 2 码位是两个独立命题，不互相证明。

**独立破坏测试 13/13 全拦**（脚本 `docs/audit/artifacts/scratch-migrated/audit-slice-b5/b5_auditor_breaktest.py` 与 `b5_v3_rc2_and_extra.py`，全部在内存副本上施加，零写盘）：
```
auditor 原 8 条：4576→4577 / 17键→16键 / VACUUM→PASS / 3628→3629 /
                键集相同→完全不同 / 27→28 / 948→949 / STATIC→LIVE     8/8 rc=1
auditor 另加 3 条：WB 上界+1 / 7-14→8-14 / f 6键→5键                 3/3 rc=1
本片补测 1 条：INTEGER 3539→3540                                     1/1 rc=1
auditor 判「残留漏拦」3 处，本轮全部闭合：
  ① §6.1 证据级 LIVE/DB→STATIC（降格）   → rc=1 ✅
  ② 删「§6.2 明确不主张」整段            → rc=1 ✅（J1/J2 六条禁令逐条守）
  ③ 删「§5.2 grep 假阳性」说明           → rc=1 ✅（J3/J4 三句逐句守）
```

> 审计方原判 ①②③ 非阻断挂账（理由：减少信息而非伪造信息）。
> 本片认为**整段删除是文档闸门最经典的绕过路径**（B4 的 M7 同类），且 ②③ 删掉的恰是本片最有价值的
> 诚实处理（假阳性陷阱、六条禁令），故未挂账而**直接补上 J 组结构性存在断言（+12 断言）**。

> v2 首跑曾抓出闸门自身 2 处生成器 bug（§4.3 表格列序错、WB 匹配式多了一对引号），
> 以及文档 1 处与加粗规则不符——三处都修正后才 119/0。**闸门先自证，再自证文档。**

> 注：§8.1 段最初把两个"禁止等级 token"的字面写进正文，立刻被自己的负向断言判 FAIL。
> 说明**作用域纪律有效**：正文只写正确口径，错口径对照一律放 §九。已按此改写。

---

## 九、A/B 对照：本片推翻/修正的三个常见错口径

> 本节引用错误口径仅作对照说明，闸门负向断言的作用域止于 §八，不含本节。

| # | 错口径 | 本片事实 |
|---|---|---|
| 1 | 「BigInteger 是 `BIGINT`」 | DB 存储字面量与 bundle 枚举均为 **`BIGINTEGER`**；`BIGINT` 是 MySQL 列类型 `bigint(20)`，混淆点在列类型 vs 字段类型 |
| 2 | 「vse 非空 5 条 ⇒ 5 个字段配了值域」 | 5 条全是 `{"min":"","max":""}` 空壳，真实配置数 **0** |
| 3 | 「BigInteger 边界 2^53−1 是 BigInteger 专属」 | Decimal / Currency 的 WB 边界**完全相同**，无判别力 |
