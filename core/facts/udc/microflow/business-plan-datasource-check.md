# 业务方案：校验数据源是否有效

## 业务原话（用户）

> 校验数据迁移的数据源是不是有效。入参是数据源的 id，拿到 id 需要查里面的数据，
> 判断它是不是启用的；是的话，再判断查询其他的是不是有启用的，然后修改他们的启用状态为停用，
> 然后修改数据，再判断现在的 jdbc 包含的是不是 mysql，是的话出参 true 否则 false。

## 一、实体与字段（已活取，非猜测）

实体：**数据源配置信息**（`MigrationDatasourceDto`，relationEntityId `5738598551920790169`）
共 25 个字段，本业务用到的：

| 字段 | 类型 | 中文 | 用途 |
|---|---|---|---|
| `id` | BIGINTEGER | ID | 入参 + ID 查询 |
| `enabled` | BOOLEAN | **是否启用** | 判断启用状态 / 停用赋值 |
| `jdbcUrl` | STRING | **JDBC URL** | 判断是否含 mysql |
| `name` | STRING | 数据源名称 | 出参时便于识别 |
| `updateTime` | DATETIME | 更新时间 | 停用时一并更新（可选） |

## 二、节点分解（对着业务原话逐句）

原话有 6 个动作，但其中「再判断查询其他的是不是有启用的」有歧义——
我先按最合理的一种拆（B 方案），A/C 方案列在后面请你确认。

### 主链（5 个节点）

| # | 节点 | 为什么必须 |
|---|---|---|
| 1 | `RETRIEVE`（**ID 查询**，`fetchType=IDS`） | 「拿到数据源的 id 需要查里面的数据」→ 按入参 id 查出整条记录 |
| 2 | `BRANCH`（2 分支） | 「判断它是不是启用的」→ 是/否两条路 |
| 2.1 | 分支内 `RETRIEVE_ARRAY` | 「查询其他的是不是有启用的」→ 查全部 enabled=true 的数据源 |
| 2.2 | 分支内 `FOR_EACH` + `CHANGE_ENTITY` | 「修改他们的启用状态为停用」→ 逐条批量改 |
| 3 | `CREATE_VARIABLE`（BOOLEAN） | 「给出参 true 否则 false」→ 需要先算出布尔结果 |
| 4 | `END`（`paramType=BASIC`, `basic=BOOLEAN`） | 出参布尔 |

### 详细节点清单（9 个节点 + 结束节点）

```
[开始] 手动触发，入参 BASIC/BIGINTEGER: datasourceId
  │
  ├─ 1. RETRIEVE_1  「查询单条数据」
  │      fetchType = IDS
  │      structure = 数据源配置信息
  │      value     = 引用入参 datasourceId
  │      nullHandling = TERMINATION
  │      nullPromptMessage = "数据源不存在"
  │      出参: _RETRIEVE_xxxx
  │
  ├─ 2. BRANCH_1  「判断是否启用」
  │      conditions[0] ifBranch:
  │         expression = 查询单条数据(1).数据源配置信息_1.是否启用 == true
  │         resultTypeInfo = BOOLEAN
  │         ├─ 2.1 RETRIEVE_ARRAY_1 「查询其他启用的数据源」
  │         │      fetchType = CONDITION
  │         │      condition: 是否启用 EQ true
  │         │      出参: _RETRIEVE_ARRAY_xxxx (ARRAY)
  │         │
  │         ├─ 2.2 FOR_EACH_1 「列表循环」
  │         │      selectParam = 引用 RETRIEVE_ARRAY_1 (ARRAY, dtoType=MASTER_ENTITY)
  │         │      targetName = "数据源"
  │         │      ├─ CHANGE_ENTITY_1 「更新数据」
  │         │      │      entity = 数据源配置信息
  │         │      │      selectParam = 引用 FOR_EACH 当前项
  │         │      │      attrs[0]: 是否启用 → Simple(false)
  │         │      │      出参: _CHANGE_ENTITY_xxxx
  │         │
  │         └─ 2.3 CREATE_VARIABLE_1 「创建变量 vJdbc」
  │                paramType = BASIC, dataType = STRING
  │                value = 引用 查询单条数据(1).JDBC URL
  │                （把 jdbc 取到变量里，后面才能做包含判断）
  │      conditions[1] elseBranch:
  │         expression = null
  │         （未启用 → 直接给 false，走 3.2）
  │
  ├─ 3. BRANCH_2  「判断 jdbc 是否含 mysql」
  │      conditions[0] ifBranch:
  │         expression = 文本包含(vJdbc, "mysql")
  │         resultTypeInfo = BOOLEAN
  │         ├─ 3.1 CREATE_VARIABLE_2 「vResult = true」
  │      conditions[1] elseBranch:
  │         ├─ 3.2 CREATE_VARIABLE_2 「vResult = false」
  │                （★ 变量只能在 if 分支建一次，else 分支不能再建同名变量，
  │                  正确做法是 3.1 之前先建 vResult=false，if 分支里改成 true）
  │
  └─ 4. END  paramType=BASIC, basic=BOOLEAN
         value = 引用 vResult
```

### ★ 这里有个必须避开的坑

「是的话出参 true 否则 false」如果写成两个分支各建一个同名变量，第二条会报
`UDC_DTO_0001` / 变量重名。正确形态：

```
前置：CREATE_VARIABLE  vResult = false        （默认 false）
然后：BRANCH
        ifBranch(文本包含(vJdbc,"mysql")):
           CHANGE_VARIABLE  vResult = true   （只有这里改）
        elseBranch: （空）
END → 引用 vResult
```

这是 643 条真实流程里 `CREATE_VARIABLE → BRANCH → CHANGE_VARIABLE` 的常见形态。

## 三、还需要你拍板的 3 个歧义点

业务原话里这三处我不敢替你定，选错了做出来就是错的：

### 歧义 1：「查询其他的是不是有启用的」——「其他」指什么？

| 方案 | 含义 | SQL 等价 |
|---|---|---|
| **A** | 除了当前这条以外的所有数据源里，有没有启用的 | `enabled=1 AND id != 当前id` |
| **B** | 同类型/同角色的其他数据源（`datasourceRole` 相同） | `enabled=1 AND role = 当前role AND id != 当前id` |
| **C** | 全部启用的数据源（含当前这条） | `enabled=1` |

我倾向 **A**（「其他」字面就是排除自己），但如果你业务上是要防止「同角色多条启用」，
那就是 B。**这个选错的后果**：A 会把不该停用的也停用，B 会漏掉该停用的。

### 歧义 2：「修改他们的启用状态为停用，然后修改数据」——「修改数据」改什么？

- 只是改 `enabled=false`（同一次 CHANGE_ENTITY 完成）？
- 还是还要改 `updateTime`、`remarks`（写停用原因）？
- 「然后修改数据」指的是**改这些被停用的记录**，还是**改当前这条**？

### 歧义 3：「判断 jdbc 包含是不是 mysql」——查谁的 jdbc？

- 当前这条（入参 id 对应的）的 `jdbcUrl`？← 我按这个做的
- 还是查出来的「其他那些」的 jdbc？

另外 `jdbcUrl` 形如 `jdbc:mysql://host:3306/db`，判断「包含 mysql」是
`containsText(jdbcUrl, "mysql")`。要不要区分大小写 / 只认 `jdbc:mysql`？我按不区分做。

## 四、节点清单汇总（按你的验收口径）

| 类别 | 节点 | 数量 |
|---|---|---|
| 数据活动 | RETRIEVE（ID查）×1、RETRIEVE_ARRAY ×1、CHANGE_ENTITY ×1 | 3 |
| 逻辑活动 | BRANCH ×2、FOR_EACH ×1 | 3 |
| 变量活动 | CREATE_VARIABLE ×2（vJdbc、vResult）、CHANGE_VARIABLE ×1 | 3 |
| 结束 | END（BASIC/BOOLEAN 出参） | 1 |
| **合计** | | **10** |

**不需要的节点**（说明我为什么不用）：
- `SUB_MICROFLOW`：业务全在一条流程内，没有复用需求
- `CALL_APP_SERVICE`：判断启用状态和 jdbc 都在实体字段里，不用调服务
- `CUSTOM_ERROR`：未查到用 RETRIEVE 的 `nullHandling=TERMINATION` 即可，
  再套 CUSTOM_ERROR 是冗余
- `DATA_MAPPING` / `CONVERT_DATA`：没有异构数据转换
- `CREATE_ENTITY` / `DELETE_ENTITY`：只改状态不增删

## 五、形态风险（我已知的构造器缺口）

| 节点 | 形态 | 构造器状态 |
|---|---|---|
| RETRIEVE ID 查询 | `fetchType=IDS` + `value` | ✅ 本轮刚补（246 次真实用法） |
| RETRIEVE_ARRAY 条件查 | `condition[]` | ✅ 已有 |
| RETRIEVE_ARRAY 分页 | `pageSearch` | ⚠️ 有参但未验 |
| CHANGE_ENTITY | `attrs[].value=Simple(false)` | ✅ 已有 |
| BRANCH 2 分支 | `conditions[2]` | ✅ 已有（883/941 是 2 分支） |
| FOR_EACH | `selectParam+targetName` | ✅ 已有（384/384 同形） |
| CREATE_VARIABLE BOOLEAN | `paramType=BASIC` | ✅ 已有 |
| CHANGE_VARIABLE | 整体赋值 `value{}` | ✅ 已有（717 次） |
| END BASIC 出参 | `paramType=BASIC`+`basic=BOOLEAN` | ❌ **组装器只做了 MANUAL DTO 出参，没做 BASIC 布尔** |
| BRANCH 表达式 | `expression.schema` 走 transform | ⚠️ 需接表达式链路 |

**两个必须补的**：END 的 BASIC 布尔出参形态、BRANCH 条件表达式生成。
后者要走 `/expression/transform` 接口，不能手写 `executableExpr`。
