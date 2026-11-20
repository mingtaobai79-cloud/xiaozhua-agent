# udc-biz 5.3.517 → 5.3.605 差异分析（新增 PERSONSELECTOR 数据类型）

> 数据源对比：
> - 旧：`D:/repo/CHIT/com/seeyon/udc-biz/5.3.517/udc-biz-5.3.517.jar`（6,972,862 字节）
> - 新：`D:/repo/CHIT-extra/udc-biz/5.3.605/udc-biz-5.3.605.jar`（6,974,486 字节）
>
> 等级：`VERIFIED_STATIC_BYTECODE`（逐 class 文件 MD5 对比 + javap 常量级对比）
> 结论强度：**高**（字节级差异定位到具体类，常量级定位到具体枚举值）

---

## 0. ★★★ 一句话结论

**5.3.605 相对 5.3.517 的唯一实质性功能变更是：新增 `PERSONSELECTOR`（人员选择器）数据类型。**

**其余 2,287 个 class 文件字节完全相同。**

**⚠️ 但这个新功能是「半成品」：**
- ✅ 能建字段、能存值、能配列、能过滤
- ❌ **不能显示姓名、不能关联查询、不能树形搜、不能携带、不支持 IN**
- ⚠️ `BaseDataTypeEnum` 里 code 写错（**1**，与其他 10 个枚举的 **121** 不一致，与 `MULTILINESTRING` 冲突）

---

## 1. ★ 差异量化

| 指标 | 值 |
|---|---|
| class 文件总数（含内部类） | 旧 2,312 / 新 **2,312**（一致） |
| **字节完全相同** | **2,287**（98.9%） |
| **字节有变化** | **25**（1.1%） |
| 顶层类数（不含 `$`） | 1,856 / 1,856（一致） |
| 新增类 | **0** |
| 删除类 | **0** |
| md5（整包） | `9538447546…` → `96b5149237…`（不同） |
| 大小 | +1,624 字节 |

**⇒ 不是「大改版」，是「加一个数据类型 + 把它的支撑关系补齐」。**

---

## 2. ★★★ 发生变化的 25 个 class（全清单）

| # | 类 | 变化性质 |
|---|---|---|
| 1 | **`common.enums.BaseDataTypeEnum`** | **★ 加常量 `PERSONSELECTOR`** |
| 2 | **`common.enums.ReferConfigSearchSupportEnum`** | **★ +2 常量** |
| 3 | **`common.enums.ReferCarrySameLevelSupportEnum`** | **★ +3 常量** |
| 4 | **`common.enums.ReferCarryDataTypeConvertSupportEnum`** | **★ +1 常量** |
| 5 | **`common.enums.ReferConfigColumnsSupportEnum`** | **★ +3 常量** |
| 6 | **`common.enums.ReferConfigDisplayNameSupportEnum`** | **★ +2 常量** |
| 7 | **`common.enums.ReferConfigPullDisplayNameSupportEnum`** | **★ +2 常量** |
| 8 | **`common.enums.ReferConfigTreeSearchSupportEnum`** | **★ +2 常量** |
| 9 | **`common.enums.FilterPlanSearchSettingSupportEnum`** | **★ +2 常量** |
| 10 | **`common.enums.FilterPlanShowSettingSupportEnum`** | **★ +2 常量** |
| 11 | **`common.enums.DataTypeAndOperator4ConditionEnum`** | **★ +1 常量** |
| 12 | `datatype.domain.service.DataTypes` | 注册新类型（方法体变化） |
| 13 | `document.DataDictionaryGenerator` | 数据字典生成（+7 内部类） |
| 14 | `document.DataDictionaryGenerator$DataTypeTableColumn` | 内部类 |
| 15 | `document.DataDictionaryGenerator$DatabaseTypeTableColumn` | 内部类 |
| 16 | `document.DataDictionaryGenerator$EntityListSorter` | 内部类 |
| 17 | `document.DataDictionaryGenerator$*$1`（4 个匿名类） | 内部类 |
| 18 | `entity.util.DataTypeChangeUtil` | 类型转换（方法体变化） |
| 19 | `entity.domain.service.AttributeService` | **+私有常量 `CONTENT_DATA_TYPE`** |
| 20 | `auth.common.typechange.String2MultilineStringTypeUpdateChecker` | 方法体变化 |
| 21 | `autocode.db.resolver.String2MultiLineStringSqlResolver` | 方法体变化 |
| 22 | `autocode.task.PageControllerTask` | 方法体变化 |
| 23 | `autocode.v27.template.CustomMicroFlowTemplate` | 方法体变化 |

**⇒ 25 个里 11 个是 `common.enums.*` —— 全部围绕 `PERSONSELECTOR`。**

---

## 3. ★★★ PERSONSELECTOR 的支撑矩阵（**含 support 真实值**）

**⚠️ 重要更正：我上一版只看了「常量是否存在」，推断「功能都支持」—— 错。**
**实际每个常量第 5 个参数是 `support`（Boolean），只有 `support=true` 才在界面上真正可用。**

### 3.1 常量清单（存在的变体）

| 枚举 | 5.3.517 | 5.3.605 | 新增常量 |
|---|---:|---:|---|
| `BaseDataTypeEnum` | 25 | **26** | `PERSONSELECTOR` |
| `ReferConfigSearchSupportEnum` | 44 | **46** | `PERSONSELECTOR`, `ENTITY_PERSONSELECTOR` |
| `ReferCarrySameLevelSupportEnum` | 66 | **69** | `PERSONSELECTOR`, `ENTITY_PERSONSELECTOR`, `MULTI_ENTITY_PERSONSELECTOR` |
| `ReferCarryDataTypeConvertSupportEnum` | 18 | **19** | `PERSONSELECTOR` |
| `ReferConfigColumnsSupportEnum` | 66 | **69** | `PERSONSELECTOR`, `ENTITY_PERSONSELECTOR`, `MULTI_ENTITY_PERSONSELECTOR` |
| `ReferConfigDisplayNameSupportEnum` | 44 | **46** | `PERSONSELECTOR`, `ENTITY_PERSONSELECTOR` |
| `ReferConfigPullDisplayNameSupportEnum` | 44 | **46** | `PERSONSELECTOR`, `ENTITY_PERSONSELECTOR` |
| `ReferConfigTreeSearchSupportEnum` | 44 | **46** | `PERSONSELECTOR`, `ENTITY_PERSONSELECTOR` |
| `FilterPlanSearchSettingSupportEnum` | 44 | **46** | `PERSONSELECTOR`, `ENTITY_PERSONSELECTOR` |
| `FilterPlanShowSettingSupportEnum` | 44 | **46** | `PERSONSELECTOR`, `ENTITY_PERSONSELECTOR` |
| `DataTypeAndOperator4ConditionEnum` | 22 | **23** | `PERSONSELECTOR` |

### 3.2 ★★★ support 真实值（**这才是「能不能用」的判据**）

**枚举常量结构（CFR 反编译实证）：**
```java
// 3 布尔版
XxxEnum(int code, String dataType, Boolean entity, Boolean multi, Boolean support)
// 4 布尔版（多一个 entityMulti）
XxxEnum(int code, String dataType, Boolean entity, Boolean entityMulti, Boolean multi, Boolean support)
```

**`PERSONSELECTOR` 的实际配置：**

| 枚举（管什么） | 变体 | code | support | 结论 |
|---|---|---:|---|---|
| **列配置** `ReferConfigColumnsSupportEnum` | `PERSONSELECTOR` | 121 | **true** | ✅ **可配列** |
| 同上 | `ENTITY_PERSONSELECTOR` | 143 | **true** | ✅ **关联也可配列** |
| 同上 | `MULTI_ENTITY_PERSONSELECTOR` | 165 | false | ❌ 多层不支持 |
| **过滤-显示** `FilterPlanShowSettingSupportEnum` | `PERSONSELECTOR` | 121 | **true** | ✅ |
| 同上 | `ENTITY_PERSONSELECTOR` | 143 | **true** | ✅ |
| **过滤-搜索** `FilterPlanSearchSettingSupportEnum` | `PERSONSELECTOR` | 121 | **true** | ✅ |
| 同上 | `ENTITY_PERSONSELECTOR` | 143 | false | ❌ |
| 关联搜索 `ReferConfigSearchSupportEnum` | 两个变体 | 121/143 | **false** | ❌ **不能做关联搜索条件** |
| 显示名 `ReferConfigDisplayNameSupportEnum` | 两个变体 | 121/143 | **false** | ❌ **不支持显示名映射** |
| 拉取显示名 `ReferConfigPullDisplayNameSupportEnum` | 两个变体 | 121/143 | **false** | ❌ |
| 树形搜索 `ReferConfigTreeSearchSupportEnum` | 两个变体 | 121/143 | **false** | ❌ **不支持树形搜** |
| **携带（同层级）** `ReferCarrySameLevelSupportEnum` | 三个变体 | 121/143/165 | **全 false** | ❌ **不能携带** |
| 携带类型转换 `ReferCarryDataTypeConvertSupportEnum` | `PERSONSELECTOR` | 18 | **false** | ❌ |

### 3.3 ★★★ 结论：PERSONSELECTOR 是**半成品**

**当前真实可用范围只有 3 处：**
```
✅ 列配置（列，及关联列）
✅ 过滤方案 - 显示设置
✅ 过滤方案 - 搜索设置
```

**明确不支持（9 处）：**
```
❌ 关联搜索条件
❌ 显示名映射（不能把 ID 自动转人名）
❌ 拉取显示名
❌ 树形搜索
❌ 携带（同层级）
❌ 携带类型转换
```

**⇒ 业务含义：**
**人员选择器字段可以**存、可以列表显示、可以过滤**，但**不能显示成姓名、不能做关联查询条件、不能携带到下游单据**。**

**⇒ 这解释了为什么 `BaseDataTypeEnum` 里没有 `DEFAULT_PERSONSELECTOR_SUPPORT_DATA_TYPE` —— 支持关系还没铺开。**

### 3.4 ★★ code 编号采用「预留跳号」策略

**除 `BaseDataTypeEnum` 外，其余 10 个枚举都用统一的预留编码：**
```
PERSONSELECTOR               = 121
ENTITY_PERSONSELECTOR        = 143   (+22)
MULTI_ENTITY_PERSONSELECTOR  = 165   (+22)
```
**模式：每加一个数据类型，code 加 22（为该数据类型的 22 个变体预留空间）。**

**⇒ 印证了 `DataTypeAndOperator4ConditionEnum` 里 `PERSONSELECTOR` 复用 `MULTILINESTRING` 运算符集（含 LIKE/LLIKE/RLIKE）**
**⇒ 说明底层存储是**字符串类型的人员 ID**（所以能 LIKE 搜索）。**

### 3.5 ⚠️ `BaseDataTypeEnum` 的 code 缺陷（**真实 bug**）

```java
PERSONSELECTOR(1, "PERSONSELECTOR", false),     // ← code = 1
MULTILINESTRING(1, DataType.MULTILINESTRING.name(), false),   // ← code 也是 1
```

**⇒ 其他 10 个枚举都用 121（预留位），只有这里写了 1 —— 明显是笔误。**

**影响评估：**
```
✅ 不受影响：BaseDataTypeEnum.of(dataType, multi) 按 dataType 字符串匹配（未用 code）
✅ 不受影响：values() 遍历
⚠️ 潜在风险：任何按 code() 反查枚举的代码（如把 int code 从 DB/前端读回来反查）
             会得到 MULTILINESTRING（因为它在 PERSONSELECTOR 之前，先匹配到）
```

**⚠️ 我未验证是否有代码按 `code()` 反查 —— 只确认 `of()` 用的是 `dataType`。**
**⇒ 等级：`VERIFIED_STATIC_BYTECODE`（冲突事实确定）/ 影响面 `UNVERIFIED`。**

### 3.6 ★★★ 可用运算符（`DataTypeAndOperator4ConditionEnum` 实证）

**`PERSONSELECTOR` 的运算符集（复用 `MULTILINESTRING` 那套）：**
```
EQ / NEQ          等于 / 不等于
LIKE / NOTLIKE    模糊匹配
LLIKE / RLIKE     左模糊 / 右模糊
NULL / NOTNULL    空 / 非空
```

**对照 `STRING` 的运算符集：**
```
EQ / NEQ / LIKE / NOTLIKE / LLIKE / RLIKE / NULL / NOTNULL
+ IN / NOTIN      ← ★ STRING 有，PERSONSELECTOR 没有
```

**★★★ 两个结论：**

1. **`PERSONSELECTOR` 没有 `IN` / `NOTIN`**
   **⇒ 不能「查属于某几个人员」这种条件 —— 业务上很常见的需求（如「负责人 in [张三,李四]」）当前不支持。**
   **⚠️ 但可以用多个 `EQ` + OR 绕过。**

2. **`PERSONSELECTOR` 复用 `MULTILINESTRING` 的运算符（含 LIKE/LLIKE/RLIKE）**
   **⇒ 底层存的是**字符串类型的人员 ID**（不是 Long 数组）。**
   **⇒ 所以能对 ID 字符串做模糊匹配 —— 这其实语义上没意义（ID 不该 LIKE），但仍开放。**

**⚠️ `DataTypeAndOperator4ConditionEnum` 里 `PERSONSELECTOR` 的 `Pair` 第二个参数是 `BaseDataTypeEnum.DEFAULT_MULTILINESTRING_SUPPORT_DATA_TYPE`。**
**⇒ 这进一步印证：它被当成 `MULTILINESTRING` 处理，是**快速接入的简化做法**，不是完整设计。**

---

## 5. ★ 连带变化（非枚举类）

### 5.1 `AttributeService` —— 新增私有常量

```java
+ private static final String CONTENT_DATA_TYPE;
```

**★ `CONTENT` 是另一个独立数据类型（已在 5.3.517 存在）。**
**⇒ 这是**重构**：把硬编码的 `"CONTENT"` 提成常量。**
**⇒ 不影响功能，但说明代码在整理。**

### 5.2 `DataDictionaryGenerator` —— 7 个内部类变化

```
DataTypeTableColumn      + 内部类 $1
DatabaseTypeTableColumn  + 内部类 $1
EntityListSorter         （变化）
+ 4 个匿名类
```

**★ 数据字典生成器 —— 新增数据类型后，字典也要多一列/多一行。**
**⇒ 说明 `PERSONSELECTOR` 会体现在**数据字典文档**里。**

### 5.3 三个「方法体变化但签名不变」的类

| 类 | 推测变化 |
|---|---|
| `entity.util.DataTypeChangeUtil` | 类型变更时，`PERSONSELECTOR` 的转换规则 |
| `auth.common.typechange.String2MultilineStringTypeUpdateChecker` | **`String` → `MULTILINESTRING` 的检查器**（名称含 PERSONSELECTOR 但语义是另一码） |
| `autocode.db.resolver.String2MultiLineStringSqlResolver` | 同上，SQL 层 |
| `autocode.task.PageControllerTask` | 页面控制器任务 |
| `autocode.v27.template.CustomMicroFlowTemplate` | **自定义微流程模板 V27** |

**⚠️ 这些类名里没有 `PersonSelector`，但二进制里含 `PERSONSELECTOR` 字符串 —— 说明它们在**遍历所有数据类型**时被波及。**
**⇒ 具体逻辑变化未反编译验证（`UNVERIFIED`）。**

### 5.4 `datatype.domain.service.DataTypes` —— 注册表

**★ 这个类应该是数据类型注册中心（`DataTypes` 复数）。**
**⇒ 新类型要在注册表里登记，所以它必然变化。**

---

## 6. ★★★ 对「哪些结论受影响」的判定

| 我的旧结论 | 是否受影响 | 理由 |
|---|---|---|
| **微流程 56 种 actionType** | ❌ 不受影响 | 新增的是数据类型，不是节点类型 |
| **实体 CRUD / 主子表** | ❌ 不受影响 | 底层 DAO 未变 |
| **生单规则 / 扣减规则** | ❌ 不受影响 | 数据流未变 |
| **枚举/选项集** | ⚠️ 微影响 | 新数据类型会出现在枚举里 |
| **表达式** | ⚠️ 可能受影响 | `DataTypeAndOperator4ConditionEnum` 变了，**运算符可能新增** |
| **关联字段配置（页面向导）** | **✅ 受影响** | **6 个 Refer* 枚举都加了 PERSONSELECTOR → 关联配置界面会多一项** |
| **数据字典导出** | **✅ 受影响** | `DataDictionaryGenerator` 变了 |
| **过滤方案** | **✅ 受影响** | 2 个 FilterPlan 枚举变了 |

**★★ 最重要的业务影响（修正后）：**
```
✅ 界面上会多出「人员选择器」数据类型，可以：
   - 建字段、存值
   - 列表/表格显示（列配置）
   - 过滤方案里做搜索和显示

❌ 但以下都还不支持：
   - 关联搜索条件（不能拿人员字段做关联查询条件）
   - 显示名映射（列表里只能看到 ID，不会自动显示姓名）
   - 树形搜索（不能按组织树选人）
   - 携带（不能带到下游单据）
   - IN 查询（不能查「属于这几个人」）
```

**⇒ 一句话：能建能用能显示，但**联动能力一个都没有** —— 典型的新功能首版。**

---

## 7. ★ 与 `10-org-domain.md` 的关联（重要交叉验证）

**`PERSONSELECTOR` 是 UDC 层的数据类型，但它取的是**组织域的人员数据**。**

**⇒ 需要 organization 的什么能力？**
```
1. 按组织树取人员     → organization 的 OrgTree / DepartmentService
2. 人员 ID → 姓名     → AccountService / MemberService
3. 人员的多选         → MULTI_ENTITY_PERSONSELECTOR
```

**⚠️ 我这轮没验证 UDC 内部具体调哪个 org 接口。**
**⇒ `UNVERIFIED` —— 需读 `datatype.domain.service.DataTypes` 或相关 resolver 的方法体。**

---

## 8. ★ 版本策略启示

**⚠️ 需要注意：`CHIT` 和 `CHIT-extra` 的 udc-biz 是**两个不同版本**，但类完全一致。**

```
D:/repo/CHIT/com/seeyon/udc-biz/5.3.517/     6,972,862 字节  25 个类旧
D:/repo/CHIT-extra/udc-biz/5.3.605/          6,974,486 字节  25 个类新
```

**⇒ 建议：以后一律用 `CHIT-extra/udc-biz/5.3.605`（对齐官方清单）。**

**★ 同时说明：`udc-biz` 从 5.3.517 到 5.3.605 只加了一个数据类型。**
**⇒ 这反过来说明：我之前基于 5.3.517 的 UDC 结论**大部分仍然有效**（98.9% 字节相同）。**

---

## 9. 未覆盖

| 项 | 说明 |
|---|---|
| `DataTypeChangeUtil` 等 5 个类的方法体变化 | **未反编译对比**（已反编译 5.3.605 全量，但未与 5.3.517 逐行 diff） |
| `PERSONSELECTOR` 的 `code()` 值 | ✅ **已确认 = 1（与其他 10 个枚举的 121 不一致）** |
| `PERSONSELECTOR` 的 `dataType()` 字符串值 | ✅ **已确认 = `"PERSONSELECTOR"`** |
| 运算符集 | ✅ **已确认：EQ/NEQ/LIKE/NOTLIKE/LLIKE/RLIKE/NULL/NOTNULL（无 IN/NOTIN）** |
| **support 真实值** | ✅ **已确认：只有列配置 + 过滤显示/搜索支持** |
| UDC 调 organization 的哪个接口取人员 | **未验证** |
| `DEFAULT_PERSONSELECTOR_SUPPORT_DATA_TYPE` 缺失原因 | ✅ **已解释：support=false，支持关系未铺开** |
| 是否有代码按 `code()` 反查 BaseDataTypeEnum | **未验证**（只确认 `of()` 用 dataType） |
| 5.3.517 → 5.3.605 的方法体级 diff | 未做（只做了 class 字节哈希 + 常量级对比） |
| 前端（udc-web 5.3.517）是否已支持该类型渲染 | **❌ 未验证 —— 本机无前端资源**（`udc-web` 只有 Controller，66 条目里 0 个 js/vue；前端在独立 npm 构建包，不在 Java 仓库） |

---

## 10. ★★ 建议：这个功能现在**不能用于生产**

**判定依据：**
```
显示名不支持 → 列表显示一串人员ID，用户看不懂
关联搜索不支持 → 无法按人员做跨表查询
携带不支持 → 无法把人员带进下游单据（审批流里常见）
IN 不支持 → 无法按多人过滤
```

**⇒ 如果客开要用人员字段，当前仍应使用**既有方案**：**
```
方案A：STRING 字段存人员ID + 显示名映射（ReferConfigDisplayNameSupportEnum 对 STRING 是 true）
方案B：ENTITY 字段关联到人员实体
```
**⚠️ 这两个方案的具体配置细节需查既有实践，本轮未验证。**

---

## 11. ★★★ 决定性证据：`PERSONSELECTOR` 在 UDC 里没有业务实现

**全库 grep `PERSONSELECTOR`（udc-biz 5.3.605 反编译全量 1,856 类），命中 16 个文件，全部是枚举和工具类：**

```
common/enums/          11 个枚举（定义常量）
datatype/domain/service/DataTypes.java          ★ 数据类型的属性开关
entity/util/DataTypeChangeUtil.java             ★ 类型变更时的一个特殊处理
document/DataDictionaryGenerator.java           数据字典生成
auth/common/typechange/String2MultilineStringTypeUpdateChecker.java
autocode/db/resolver/String2MultiLineStringSqlResolver.java
```

**没有任何 `*Service` / `*Resolver` / `*Renderer` 为 PERSONSELECTOR 做业务处理。**

**⚠️ 复核澄清：grep 结果里有 1 个类名带 `Service`/`Resolver` —— `String2MultiLineStringSqlResolver`。**
**但它是「String → MULTILINESTRING」的 SQL 解析器，只是因为**遍历所有数据类型**时才顺带引用 `PERSONSELECTOR` 字符串，**
**⇒ **不是 PERSONSELECTOR 的专属实现**。**

**★ `DataTypes.java` 在 `datatype.domain.service` 包里，但它是**数据类型的属性开关配置表**（`dto.setEnableXxx`），**
**⇒ 不是「选人」的业务实现。**

### 11.1 `DataTypes.java` 里的全部配置（163-177 行）

```java
if ("Serial".equals(name) || "CONTENT".equals(name) || "DOCUMENTNUMBER".equals(name)
    || "OPINION".equals(name) || "PERSONSELECTOR".equals(name)) {
    dto.setEnablePattern(false);          // 不支持正则
    dto.setEnableDefaultValue(false);     // 不支持默认值
    dto.setEnableSensitive(false);        // 不支持脱敏
    dto.setEnableEncryption(false);       // 不支持加密
}
if ("CONTENT".equals(name) || "DOCUMENTNUMBER".equals(name)
    || "OPINION".equals(name) || "PERSONSELECTOR".equals(name)) {
    dto.setEnableUnique(false);           // 不支持唯一约束
}
```

### 11.2 `DataTypeChangeUtil.java` 里的唯一处理（32-34 行）

```java
if ("PERSONSELECTOR".equals(nowDataType)) {
    now.setDataI18n(false);               // 关闭 i18n
}
```

**★★★ 这就是 `PERSONSELECTOR` 在 UDC 里的**全部实现** —— 6 个 boolean 开关，没有别的。**

### 11.3 对照：`SelectPeopleDataParam` 存在但属于微流程

**UDC 里有选人相关的类，但都是**微流程**用的，不是数据类型：**
```
microflow/domain/bo/param/SelectPeopleDataParam.java
microflow/constant/MicroFlowComponentConstants.java
enums/microflow/AttrValueTypeEnum.java
```

**⇒ 微流程节点能选人是**节点参数级**的能力（`SelectPeopleDataParam`），**
**⇒ 与「实体字段是 PERSONSELECTOR 类型」是两回事。**

### 11.4 ★★★ 最终判定

| 层面 | 是否支持 PERSONSELECTOR |
|---|---|
| 枚举定义 | ✅ 有常量 |
| **存储** | ✅ 存字符串（复用 MULTILINESTRING 运算符，含 LIKE） |
| **列表显示** | ✅ 列配置支持 |
| **过滤** | ✅ 过滤方案支持 |
| **前端渲染器** | ❓ 未知（本机无前端资源） |
| **显示名映射（ID→人名）** | ❌ **无任何实现** |
| **选人弹窗（点字段能选人）** | ❌ **无任何实现** |
| **关联查询** | ❌ 不支持 |
| **携带到下游** | ❌ 不支持 |

**⇒ 结论：`PERSONSELECTOR` 在 5.3.605 里是**只有数据结构、没有交互实现**的半成品。**
**⇒ 建了字段也**没法选人**（没有选人弹窗），只能靠接口直接写 ID 字符串。**
**⇒ 生产不可用，客开仍应用 STRING 或 ENTITY 方案。**