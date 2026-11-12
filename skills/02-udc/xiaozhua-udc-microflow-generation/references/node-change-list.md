# CHANGE_LIST（修改列表）

> 语料：**317 条**样本（643 条 RELEASE 流程）

## 1. 四种动作（`action` 字段，不是 `operationType`）

| action | 样本 | 必填 | dataSource 形态 |
|---|---|---|---|
| ADD | 266 | selectParam + dataSource | 元素 OBJECT 125 / 列表 ARRAY 52 |
| REPLACE | 28 | selectParam + dataSource | 列表 ARRAY 25 / **元素 OBJECT 3** |
| CLEAR | 15 | **只有 selectParam** | **无 dataSource** |
| REMOVE | 8 | selectParam + dataSource + **countAttrs** | 列表 ARRAY 8 |

**枚举里没有 DELETE。** 节点没有出参（317/317 `output=null`）。

### ADD 的 dataSource 两种形态

```
元素形态（125 条）：type=OBJECT dataType=DTO dtoType=SUB_ENTITY position=parent
列表形态（ 52 条）：type=ARRAY  dataType=DTO/BIGINTEGER
```

元素形态来自 `CREATE_VARIABLE`（实体型变量）或 `LIST_OPERATION(FIRST_ONE)`；
列表形态是「批量追加另一个列表」。

### REMOVE 的 countAttrs

按字段匹配要删的元素，实测样本只有 1 个字段：

```json
{"id":"<dto>.id","fullName":"<dto>.id","name":"id",
 "javaType":"java.lang.Long","dataType":"BIGINTEGER","type":"OBJECT","dtoType":"CUSTOM"}
```

## 2. 构造器修正（2026-11-03）

| 问题 | 修正 |
|---|---|
| `action` 默认 ADD，无条件写 `dataSource`，还塞了语料里不存在的 `value` | 按动作分型；CLEAR 显式清掉模板自带的 dataSource/countAttrs |
| 文档写 ADD/REPLACE/**DELETE** | 真实枚举 ADD/REPLACE/CLEAR/REMOVE，传 DELETE 直接抛错 |
| REPLACE 的 dataSource 一律当列表处理 | 按**来源节点出参类型**选：OBJECT→元素引用、ARRAY→列表引用（REPLACE 两种都存在） |
| 契约表把 dataSource 列为全局必填 | 改为按动作，由 **G40** 把关 |

闸门 **G40**：action 必须在枚举内；CLEAR 不得有 dataSource；ADD/REPLACE 必须有；
REMOVE 还必须有非空 countAttrs。

## 3. 运行时验证（2026-11-03）

每种动作**一条独立流程**，结构统一：

```
1-查列表(taskId=M，3 条) → 2-SIZE → 3-写 BEFORE
→ <数据源> → 5-CHANGE_LIST(action) → 6-SIZE → 7-写 AFTER
```

读侧断言（同一次执行内前后两行）：

| 动作 | 数据源 | BEFORE | AFTER | 结论 |
|---|---|---|---|---|
| CLEAR | 无 | 3 | **0** | 清空生效 |
| ADD | CREATE_VARIABLE 实体变量（空 DTO 元素） | 3 | **4** | 追加一个元素 |
| ADD（列表形态） | 空实体列表 + 查询结果列表(3 条) | 0 | **3** | 批量追加，见 P6 闭环 |
| REPLACE | 另一组查询结果（1 条） | 3 | **1** | 整列表被替换 |
| REMOVE | 另一组查询结果（1 条，按 id 匹配） | 3 | **2** | 按 id 匹配移除 1 个 |

### 3.1 关键发现：CHANGE_LIST 直接作用于查询结果数组

CLEAR 的 selectParam 指向 `RETRIEVE_ARRAY` 出参，运行后 SIZE 从 3 变 0 ——
说明查询结果数组在流程内是**可变**的，不需要先 COPY 到变量再改。
这决定了后续所有列表动作都可以直接接查询节点。

### 3.2 四动作全部实测（不是互推）

四个动作各跑一条独立流程，各自有 BEFORE/AFTER 两行读侧数据：

```
CLEAR   00:29:00  BEFORE=3  AFTER=0
ADD     00:38:00  BEFORE=3  AFTER=4
REPLACE 00:55:00  BEFORE=3  AFTER=1
REMOVE  01:04:00  BEFORE=3  AFTER=2
```

REPLACE 与 REMOVE 用的是「另一组查询结果（sourceTable=S-A，1 条）」作 dataSource，
证明列表型 dataSource 语义正确；REMOVE 的 countAttrs（id）确实按 id 命中。
**没有用其中一种通过推导其余。**

### 3.3 形态与语料对齐

构造出来的节点键集与语料逐字一致：
CLEAR = `action,actionType,caption,description,input,isCompleted,name,nodeId,output,runAfter,selectParam,type`；
REMOVE 多 `countAttrs`、`dataSource`。

## 4. 补验（2026-11-03）：REPLACE 两种形态 + REMOVE 多字段

```
基线 4 行
REPLACE dataSource=单元素 OBJECT → 1   （用首元素整体替换，语料 3/28 是这种）
REPLACE dataSource=2 元素 ARRAY  → 2
REMOVE  countAttrs=[id, processedRows] → 2 （删 processedRows>2 的两行）
```

### ★ dataSource 形态不能按动作写死

早期构造器写成「REPLACE/REMOVE 一律 ARRAY」，结果 REPLACE 传单元素时 G31 报
`引用 type=ARRAY 与出参声明 OBJECT 不一致（List/单对象错接）`。

正确做法：按**来源节点出参类型**选 —— 出参 OBJECT 用元素引用，
ARRAY 用列表引用。REPLACE 两种在语料里都存在，写死任何一种都会错。

### REMOVE 的 countAttrs

按哪些字段匹配要删的元素。单字段（id）和多字段（id+业务字段）都可行，
多字段时平台按全部键匹配。
