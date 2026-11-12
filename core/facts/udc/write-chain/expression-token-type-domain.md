# 表达式 token 类型域与系统变量面（写链事实件）

> 证据阶梯：**VERIFIED_STATIC_BYTECODE**（CFR）+ **LIVE**（test2 真实运行）。
> 权威字节码：`boot-starter-formula-5.3.318.jar`（本仓反编译件 `docs/audit/artifacts/decompiled/r38_full`，202 个 `.java`）。
> LIVE 端点：`POST /service/udc/expression/check`（**纯校验，无落库副作用**）；
> `GET /service/udc/expression/system-variable/list`。
> LIVE 环境：test2，appId `8704025620829192834`。
> 日期：2026-10-16（第四十轮）。
>
> ★ 本件**同时登记两处对上一轮交接的证伪/更正**（§6、§7），不接受只有正例的结论。

## 1. token.type 值域（恰 5 值）

| 项 | 值 |
|---|---|
| CFR 权威 | `enums/TokenTypeEnum.java` = `CONSTANT / VARIABLE / SYSTEM / FUNCTION / OPERATOR` |
| CFR 佐证 | `common/constant/TokenTypeConstant.java` 同 5 个字面量 |
| ★ 不存在 | `SYSTEM_VARIABLE` —— 系统变量是 `type=SYSTEM` |
| 值域外后果 | LIVE：`SYSTEM_VARIABLE` / `BOGUS` / `""` ⇒ **`BOOT_3000`**（message 为 null）|

`parser/ast/Factor.parse:26-50` 只认 `VARIABLE` / `CONSTANT` / `SYSTEM` / `FUNCTION` 四类，
其余 `return null`。⇒ 值域外是**框架反序列化失败**，不是业务码。

## 2. SYSTEM token 的两条解析通路（互不等价）

| 通路 | token 形状 | CFR 路径 | 分析类型来源 |
|---|---|---|---|
| A 全名 | `{"type":"SYSTEM","value":"system.currentDateTime"}` | `SemanticAnalyzer.analyze:94` → `analyzeSystem:230-240` | `getSystemVariableItemsMap().get(value).getResultType()` |
| B 短名 | `{"type":"SYSTEM","value":"currentDateTime"}` | `ExpressionToken.currentIsCallFactor:122-124` → `Expr.f:64` → `CallExpr` → `analyzeCallExpr:145-157` | **函数返回类型** |

- `currentIsCallFactor` = `(currentIsFunction() \|\| currentIsSystemVariable()) && functionCacheMap.containsKey(value)`
  ⇒ 短名**只要同名于某个函数**就被当函数调用。
- 唯一 put 点：`ExpressionPresetRunner.loadSystemVariable:237`
  `ExpressionCache.getSystemVariableItemsMap().put(systemVariableItems.getName(), ...)`
  （扫 `classpath*:META-INF/system/**/*.json`；同处 `:234` 对 hidden 项/同名函数 hidden 的项 `setHidden(true)`）。
- LIVE 存在性判别：`{"type":"SYSTEM","value":"abs"}` 无 `subOps` ⇒ **BOOT_3000**；带 1/2 参 ⇒ **BOOT_0000**。

### 2.1 分析类型分裂（LIVE 实测，报文逼出）

报文形如 `Calculated result is of type <分析类型>, cannot be assigned to: <派生行键>`
（用 `resultTypeInfo=BOOLEAN` 或 `STRING` 逼出 `FORMULA_6901`）。

| 变量 | 短名（通路 B） | 全名（通路 A） | 分裂？ |
|---|---|---|---|
| `currentTime` | **STRING** | **TIME** | ★ 是 |
| `currentDateTime` | **DATE** | **DATETIME** | ★ 是 |
| `currentDate` | DATE | DATE | 否 |
| `currentUserId` | BIGINTEGER | BIGINTEGER | 否 |
| `currentTimestamp`（全名 hidden） | BIGINTEGER | BIGINTEGER | 否 |

⇒ **写链侧不得把短名与全名当同义词**：短名的分析类型来自函数表，可能与系统变量表不一致。

## 3. hidden 项：list 过滤 / check 不过滤

| 面 | CFR | 行为 |
|---|---|---|
| **列表** | `ExpressionService.getI18nSystemVariables:609` `if (item.isHidden()) continue;` | hidden 项**不出现**在前端选择器 |
| **校验** | `SemanticAnalyzer.analyzeSystem:230-240`（**无 hidden 判断**） | hidden 项**完全可用** |

LIVE 佐证：`system.currentTimestamp` 不在 list 里，但 `check` 在 `rt=BIGINTEGER`/`STRING` 下都 **BOOT_0000**。

## 4. 131 vs 132（双向闭合）

| 口径 | 值 | 来源 |
|---|---|---|
| LIVE list 回读 | **131**（4 组：organization 95 / date 33 / env 2 / plugin 1） | `GET /udc/expression/system-variable/list` |
| jar 静态计数 | **132**（date 34 / env 2 / plugin 1 / organization 95） | `META-INF/system/*.json` |
| 差额 | **恰 1** = `system.currentTimestamp`（`date.json` 唯一 `hidden:true` 项） | 双向闭合 |

⇒ 「list 过滤 hidden、check 不过滤」由**两条独立证据链**（LIVE 计数 + 静态逐件计数）同时支持。

## 5. 返回类型（resultTypeInfo）域

- CFR `enums/ExprDataTypeEnum.java`：枚举 **16 个常量**（`INTEGER/BIGINTEGER/BIGDECIMAL/STRING/`
  `MULTILINESTRING/ATTACHMENT/BOOLEAN/DATE/DATE_TIME/TIME/ENUM/CTP_ENUM/OBJECTS/ENTITY/ARRAY/CURRENCY`），
  静态块 `supportedResultType` 只 add **15 个** ⇒ **唯一被排除的是 `OBJECTS`**。
- CFR `ResultTypeDefinitionFilter.doFilter:33`：`supportedResultType.contains(resultTypeInfo)` 否则
  `throw RESULT_TYPE_ERROR` = **`FORMULA_6003`**。
- LIVE：`resultTypeInfo="OBJECT"` ⇒ `FORMULA_6003`；`"UDCENUM"`（无此 DataType）⇒ `FORMULA_6003`。
- `resultTypeInfo=ENUM && resultTypeFullName 为空` ⇒ **`FORMULA_6068`**（`ENUM_ASSIGN_ERROR`）。
- 其他静态集：`fixedBasicTypes` 14（无 ARRAY/OBJECTS）、`numberTypes` 4、`dateTypes` 2、`objectTypes` 1。

## 6. ★ 更正一：ENUM「表外 ⇒ 恒放行」是过强表述

上一轮交接写的「`ENUM` 在兼容表内无行 ⇒ 一条都不校验 ⇒ **恒放行**」
**只对兼容表这一门成立**；整条校验链**仍会**报错。

CFR `ExpressionValidator.resultTypeCompatibilityCheck:113-115` 顺序：
`checkUdcEnumCast` → `checkCtpEnumCast` → `checkEntityCast` → **然后**才是查表。

`checkUdcEnumCast:137-141`（**独立于兼容表**）判据：

```java
if (!( DataType.ENUM != expectedResultType
       || !analyzeExpressionDataType.isUdcEnum()
       || ( equals(analyze.genericType, resultTypeFullName)
            && analyze.isMultiSelect() == saveDto.getIsMultiSelect() ) ))
    throw new BusinessException("FORMULA_6071");
```

LIVE 反例（本轮复跑，`POST /udc/expression/check`）：

| token | rt | resultTypeFullName | isMultiSelect | 结果 |
|---|---|---|---|---|
| SYSTEM `system.currentUserId` | ENUM | `null` | false | **FORMULA_6071** |
| SYSTEM `system.currentUserId` | ENUM | `com.seeyon.organization.domain.core.entity.OrgMember` | false | **BOOT_0000** ← 填对就过 |
| SYSTEM `system.currentUserId` | ENUM | `"OrgMember"` | false | **FORMULA_6071** |
| SYSTEM `system.currentDate` | ENUM | `null` | false | **BOOT_0000** ← genericType 同为 null |
| CONSTANT `'x'` | ENUM | — | **true** | **FORMULA_6071**（multi 不匹配） |

⇒ 判据是 **`genericType == resultTypeFullName` 且 multi 一致**（**null == null 也算相等**）。

同族的另两门（也在查表之前）：
- `checkCtpEnumCast:159-180`：rt=CTPENUM 且分析结果是 entity/udcEnum ⇒ **`FORMULA_6169`**
  （LIVE：SYSTEM `system.currentUserId` ⇒ 6169，与 multi 无关）。
- `checkEntityCast:145-157`：rt=ENTITY 且分析结果是 ctpEnum/udcEnum ⇒ **`FORMULA_6170`**；
  ENTITY + fullName 不等 ⇒ 6170；期望单选而分析多选 ⇒ **`FORMULA_6172`**；CTPENUM 多选不匹配 ⇒ **`FORMULA_6171`**。

⇒ **「表外」只说明兼容表这一门不生效**，不等于「无其它门」。

## 7. ★ 更正二：判别器 J 的自变量不成立

上一轮交接写「判别器 J：`rt=CTPENUM + multi=True` ⇒ `BOOT_0000`，`multi=False` ⇒ `6901`」，
并把 token 记为 `SYSTEM system.currentDate`（分析类型 **DATE**）。
本轮复跑：该组合 **multi 真/假都是 `FORMULA_6901`**
（DATE 既不在 `BIGINTEGER` 行 `BE=(INTEGER,BIGINTEGER)`，也不在 `STRING` 行 `BE=(…,STRING,…)`）
⇒ 原表述的**自变量不成立**。

**正确的判别器**（本轮新证）：同一 token、**只翻 `isMultiSelect`**，让分析类型落进其中一个派生行：

| 自变量 | 派生行键 | 该行 BE | 结果 |
|---|---|---|---|
| token = `CONSTANT 'x'`（分析类型 **STRING**），rt=CTPENUM，multi=**false** | `BIGINTEGER` | `(INTEGER, BIGINTEGER)` 不含 STRING | **FORMULA_6901** |
| 同上，multi=**true** | `STRING` | 含 STRING | **BOOT_0000** |

⇒ 唯一自变量 `isMultiSelect`，结果翻转 ⇒ **行键确为 `getResultDataTypeBySaveDto` 的派生值**。

CFR 派生规则（两侧对称）：
- `getResultDataTypeBySaveDto:193-202`（行键）：CTPENUM/ENTITY 且 multi ⇒ `STRING`，否则 ⇒ `BIGINTEGER`；其余 ⇒ `resultTypeInfo`。
- `getExpectResultDataType:182-191`（被比较侧）：CTPENUM/ENTITY 且 multi ⇒ `STRING`，否则 ⇒ `BIGINTEGER`；其余 ⇒ `originDataType`。
- `terminalSupportType == null` 视为 `BACKEND`。

## 8. 兼容表（14 行，CFR 资源件逐字）

行键：`MULTILINESTRING / STRING / INTEGER / BIGINTEGER / DECIMAL / BOOLEAN / DATE / DATETIME /`
`TIME / ENTITY / ATTACHMENT / CURRENCY / CTPENUM / ARRAY`。
**无** `ENUM` / `UDCENUM` / `OBJECT` 行；`ENUM` 也不作为任何行的**值**出现。

## 9. 错误码

| 码 | 含义 |
|---|---|
| `BOOT_3000` | `tokens[].type` 越域；或枚举字段反序列化失败（message 为 null）|
| `FORMULA_6003` | `resultTypeInfo` 不在 15 值域（OBJECT/UDCENUM）|
| `FORMULA_6049` | 函数实参个数不符（LIVE：FUNCTION `abs` + `subOps=[]`）|
| `FORMULA_6058` | VARIABLE 名不在 schema/context |
| `FORMULA_6066` | 变量名以数字开头（`TokenLexerFilter.checkVariableName`）|
| `FORMULA_6068` | rt=ENUM 但 `resultTypeFullName` 为空 |
| `FORMULA_6069` | `controlData.data.fullName` 与 `resultTypeFullName` 不等 |
| `FORMULA_6071` | `checkUdcEnumCast` 判据不满足（§6）|
| `FORMULA_6169` / `6170` / `6171` / `6172` | CTPENUM/ENTITY 类型与多选匹配错误 |
| `FORMULA_6901` | 派生行键的兼容列表不含派生被比较类型 |

## 10. 边界（未取证，不得外推）

- 本件全部结论来自 `POST /udc/expression/check`（**校验面**），**未**验证落库后的运行期取值。
- `resultTypeInfo` 各类型的**实际可用组合**只做了抽查（ENUM/CTPENUM/OBJECT/UDCENUM/BOOLEAN/DATE/STRING/BIGINTEGER），
  未做 15×15 全矩阵。
- 短名通路 B 的**函数表全量**未枚举（只证了存在性与类型来源）。
- `FORMULA_6049`/`6066`/`6069` 由 CFR 定域，本轮**未逐条 LIVE 复现**（标 UNVERIFIED）。
