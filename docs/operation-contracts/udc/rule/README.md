# 规则生成契约层（`docs/operation-contracts/udc/rule/`）

> **契约层里的 rule 域**：2 份 / 11,546 B / 239 行。
> 上级入口：`docs/operation-contracts/udc/README.md`（14 子域总表）。
> **本目录此前零入口**（上级总表里 `rule/` 那一行标 ❌）。这是它的域入口。

---

## 一⚠️、先澄清一件事：**这里没有 `UdcOperationContract`**

上级总表把 `rule/` 列在"契约层"下，但它**不是端点契约域**。
本目录两份文件里 **0 条 `contracts[...]` 构造**，实测确认。

| | 其他 13 个子域 | 本域 |
|---|---|---|
| 描述对象 | **HTTP 端点**（method + path + DTO） | **规则节点 schema**（字段必填集 / 枚举值 / 空分支合法性） |
| 落库去向 | `registry.py` 的 `UdcOperationContract` | **落 constraints 不落 registry**，是生成器/校验器要实现的约束 |
| 证据形式 | `javap` + `jar_sha256` | **DB 只读复算**（结构性遍历 1,839 个 RETRIEVE 等） |

⇒ **别在本目录找 `registry-entries.md`，本域没有，也不该有。**
⇒ 判据：**"契约"在本仓库有两个意思** —— 端点契约（进 registry）和**数据/结构契约**（进 constraints）。
本域是后者。混为一谈会得出"rule 域 0 条落库 = 漏了"的错误结论。

---

## 二、`GENERATION-PLAN` 的状态是 **UNVERIFIED**，`RULE-GENERATION-CONTRACT` 是 LIVE

两份文件的头注等级**不同**，不能混用：

| 文件 | 等级 | 含义 |
|---|---|---|
| `RULE-GENERATION-CONTRACT-20261019.md` | **LIVE**（DB 只读复算）＋ **STATIC**（constraints） | 数字都是**本切片独立复算，非转抄** |
| `GENERATION-PLAN-20261019.md` | **UNVERIFIED**（③落库验证 **BLOCKED**，未解锁） | 只读比对的计划，未闭环 |

⇒ **引用数字前先看是哪一份。** 计划里的数不等于契约里的数。
⇒ 计划文件自己写着"③落库验证 BLOCKED，未解锁" —— 这是**诚实的未完成状态**，不是遗漏。

---

## 三、本域最值钱的东西：一份「照着做就不会出错」的字段规则

`RULE-GENERATION-CONTRACT` 把这些约束一条条钉死了。**这些都是实测/静态核对出来的，不是推测：**

### ① 必填字段（按节点类型分开）

| 节点 | 必填 | 注意 |
|---|---|---|
| `RETRIEVE` | `condition`(COND/COUNT/OTHERS) / `value`(IDS) / `nullPromptMessage`(仅 TERM) | **无 `size` / `aggFunction` 字段** |
| `RETRIEVE_ARRAY` | `fetchType` / `condition` / `value` / `size`(仅 COND) / `aggFunction`+`countAttrs`(仅 OTHERS) | 三者只属此节点 |
| `CALL_MICRO_FLOW` | `mfService` = 目标流程 id | 本 app 24/24 必带 |
| `END` | `output` **键必须在** | **有键无值是合法的**（null 34/46）→ **禁判「无 output」** |
| `DATA_MAPPING` | `mappingRule` 是 **dict 不是 JSON 串** | **勿 `json.loads`** |

### ② `pageSearch` 属于 `RETRIEVE_ARRAY`，不属于 `RETRIEVE`

> ★ `pageSearch` 是 `RETRIEVE_ARRAY` 的 shape，不是 `RETRIEVE` 的。
> `required_fields()` 对该节点只按 `fetchType` 过滤 `size`/`aggFunction`，**无 `pageSearch` 维度**
> → `fetchType=CONDITION` 且 `pageSearch=true` 时**不要补 `size`**（否则假失败）。

⇒ 这是"校验器会误报"的具体场景。**补了不该补的字段 = 假失败。**

### ③ `nullHandling` 的枚举是 `TERMINATION`，**不是 `STOP`**

```
结构式遍历全库 RETRIEVE = 1839（沿 nodes[] 与 conditions[].nodes[]）
  CONTINUE     1618 → nullPromptMessage 0 例带
  TERMINATION   219 → nullPromptMessage 219 例全带
  None            2 → 未配置，按 CONTINUE 处理（不补 prompt）
```

> ★ **枚举是 `TERMINATION` 不是 `STOP`**（源码 L35 注释写 STOP 是**注释错**）。

⇒ **源码注释写错了，实测才是对的。** 只读源码会写出 `STOP`，然后 219 个实例全部校验失败。

### ④ `fetchType` 的布尔串化，读前先归一

> ★ 三写法（布尔串化、大小写不一）**读前先归一**，否则 `'false'` 被当真值。

### ⑤ 空分支体**必须放行**

```
conditions[].nodes = []   → 合法，禁止报错、禁止修复
```

| 范围 | COND | 空 body | 占比 |
|---|---|---|---|
| 本 app 47 条 | 34 | **7** | 7/34 |
| 全库 type=2 | 67 | **30** | 30/67 |

⇒ **将近一半的空分支是合法的。** 一个"看到空就报错"的校验器会误报一半。

---

## 四、②的例子里藏着一个通用判据

本域反复出现的句型是"**别把 A 的字段要求套到 B 上**"：
- `pageSearch` 不是 `RETRIEVE` 的
- `size`/`aggFunction` 不是 `RETRIEVE` 的
- 空 body 不是错误

⇒ **判据：同一套 schema 里，字段约束是"按节点类型分表"的，不是全局的。**
⇒ 读这类契约时，先找"哪个字段属于哪个节点"那张表，再谈必填。

---

## 五、两份一览（按字节降序）

| 文件 | 字节 | 行 | 等级 | 性质 |
|---|---:|---:|---|---|
| `RULE-GENERATION-CONTRACT-20261019.md` | 6,123 | 132 | **LIVE + STATIC** | 四类可引用项 + 两条硬约束（生成器必须实现） |
| `GENERATION-PLAN-20261019.md` | 5,423 | 107 | **UNVERIFIED** | 契约四类清单 × 现网 47 条流程的只读比对 |

合计 **11,546 B / 239 行**（含本 README 时不适用——上表只算 2 份）。

日期都是 **2026-10-19**，源基线 `@12e5b70`（app-std `87240c7` / ctl `7b5f96b` / final `12e5b70`）。

---

## 六、⚠️ 环境标注里有保留段代号

两份文件都写的是保留段代号 `9000…001`/test2 ——
`9000000000…` 前缀是**保留段代号**（第 32/38 轮脱敏后的值），不是真实客户标识。

⇒ 本目录可直接读。但其中的统计数字来自**运行态 DB 只读复算**，
分发时仍须按分发清单判据过滤。

---

## 七、拿不到什么

- **③落库验证** —— `GENERATION-PLAN` 头注明写 **BLOCKED，未解锁**。
- **`mappingRule` 内部 8 键的全库核对** —— 明写"属 SUB_MICROFLOW 样本，**未在全库逐个核**"，
  只用 `targetType` / `mappingRows`。
- **`ACTIVITY_NODE_TYPES` 里那 2 种未收录类型**（`CHANGE_BATCH_ENTITY` / `CREATE_MAP`）—— 明写未收录、实例数未单列。
- **端点层面的东西** —— 本域没有，去 `microflow/` 或 `flow/`。

---

## 八、与事实层怎么分工

| 想知道 | 去 |
|---|---|
| 规则节点有哪些必填字段、枚举值是什么 | **本层**（`RULE-GENERATION-CONTRACT-20261019.md`） |
| 契约清单与现网 47 条流程的差距 | **本层**（`GENERATION-PLAN-20261019.md`，**UNVERIFIED**） |
| 微流程本身怎么生成 | `core/facts/udc/microflow/` + `docs/operation-contracts/udc/microflow/` |
| 校验器代码 | `components/udc/microflow_constraints.py` |
| 本层在 14 个子域里的位置 | `docs/operation-contracts/udc/README.md` |
