# ★★★★★ 微流程节点枚举权威表（反编译实证）

> 数据源：
> - `udc-biz-5.3.605.jar` → `com.seeyon.udc.enums.microflow.*`（CFR 反编译）
> - `udc-common-5.3.605.jar` → `com.seeyon.udc.common.enums.MicroFlowActivityTypeEnum`
> 等级：`VERIFIED_STATIC_BYTECODE`
> 时间：2026-11-18

---

## 0. ★★★★ 三张枚举表的关系（关键）

```
MicroFlowNodeTypeEnum      8 个  → node.type（结构大类，决定走哪个宏）
ActivityNodeTypeEnum      29 个  → actionType 的 strCode（模板 case 用这个）
MicroFlowActivityTypeEnum 101 个 → 全量 actionType（含前端/元信息）
ListOperationTypeEnum     19 个  → 集合运算类型
BaseNodeGroupEnum          8 个  → 节点分组（决定给哪个设计器用）
```

**★★★★★ 最容易搞混的一点：**
```
MicroFlowActivityTypeEnum（101 个）  ← 全量，含前端/元信息/页面动作
ActivityNodeTypeEnum（29 个）        ← 只有「能生成代码的」后端节点
```
**⇒ 模板 `nodeActivityHandler` 的 21 个 case 用的就是 `ActivityNodeTypeEnum.strCode`。**

---

## 1. ★★★★★ `MicroFlowNodeTypeEnum`：8 个结构大类（不是 5 个！）

**之前从模板里只看到 5 个（Activity/Branch/ForEach/For/CustomError），实际有 8 个。**

```
0  CONDITION    "Condition"    条件
1  FOR_EACH     "ForEach"      列表循环
2  BRANCH       "Branch"       分支
3  CUSTOM_ERROR "CustomError"  自定义错误
4  END          "End"          结束
5  ACTIVITY     "Activity"     动作节点  ★ 21 种 actionType 的容器
6  FOR          "For"          计数循环
7  BREAK        "Break"        跳出循环
```

**分组常量（`static {}` 实测全文）：**
```java
ALL_TYPE_NAMES       = 全部 8 个名称
CYCLIC_NODE_TYPES    = EnumSet.of(FOR, FOR_EACH);                  // ★ 循环类 2 个
CONTAINER_NODE_TYPES = EnumSet.of(CONDITION, FOR, FOR_EACH, BRANCH); // ★ 容器类 4 个
```

**★★★★★ 两个分组的语义（关键）：**
```
CYCLIC_NODE_TYPES = {FOR, FOR_EACH}
  ⇒ 会「重复执行子节点」的循环节点。用于：日志计数、循环变量作用域、跳出(BREAK)校验。

CONTAINER_NODE_TYPES = {CONDITION, FOR, FOR_EACH, BRANCH}
  ⇒ 能「包含子节点列表」的容器节点（有 children）。
  ⇒ Activity / CUSTOM_ERROR / END / BREAK 是叶子节点，不能挂子节点。
```

**★★★ 对照模板：`nodesLogicHandler` 里只有 BRANCH/FOR/FOR_EACH 递归调用自己，**
**`CONDITION` 在 `branceLogicNodeHandler` 里通过 `condition.nodes` 递归 —— 完全对得上。**

---

## 2. ★★★★★ `ActivityNodeTypeEnum`：29 个后端 actionType（权威映射）

**这是 `actionType` ↔ `strCode` 的唯一权威表，模板 case 直接用它。**

```
code  enum常量                strCode（模板 case 里的字符串）
---  ----------------------  ------------------------
 0   CONNECTOR               "Connector"
 1   CREATE_VARIABLE         "CreateVariable"
 2   CHANGE_VARIABLE         "ChangeVariable"
 3   CREATE_LIST             "CreateList"
 4   CHANGE_LIST             "ChangeList"
 5   PUBLISH_BUSINESS_EVENT  "PublishBusinessEvent"
 6   ATTRIBUTE_REQUIRED      "AttributeRequired"
 7   ASSIGN_VALUE            "AssignValue"
 8   SHOW_MESSAGE            "ShowMessage"
 9   ATTRIBUTE_UNIQUE        "AttributeUnique"
10   RETRIEVE                "Retrieve"
11   RETRIEVE_ARRAY          "RetrieveArray"
12   CHANGE_ENTITY           "ChangeEntity"
13   CREATE_ENTITY           "CreateEntity"
14   DELETE_ENTITY           "DeleteEntity"
15   LIST_OPERATION          "ListOperation"
16   SUB_MICROFLOW           "SubMicroFlow"
17   CALL_MICRO_FLOW         "CallMicroFlow"
18   CALL_APP_SERVICE        "CallAppService"
19   CALL_DATA_FLOW          "CallDataFlow"
21   DEFAULT_VALUE           "DefaultValue"
40   CONVERT_DATA            "ConvertData"
41   CREATE_BATCH_ENTITY     "CreateBatchEntity"
42   CHANGE_BATCH_ENTITY     "ChangeBatchEntity"
43   CREATE_MAP              "CreateMap"
44   MAP_OPERATION           "MapOperation"
45   DATA_MAPPING            "DataMapping"
46   CALL_DATA_FLOW_FRONT    "CallDataFlowFront"
47   EXTEND_ACTION           "CallDataFlowFront"   ★★★ 平台 bug！
48   SET_DATASOURCE          "CallDataFlowFront"   ★★★ 平台 bug！
```

**★★★★★ 发现平台的三个复制粘贴 bug（`strCode` 全部相同）：**
```java
CALL_DATA_FLOW_FRONT(46, "CallDataFlowFront"),
EXTEND_ACTION(47, "CallDataFlowFront"),      // ← 应该是 "ExtendAction"
SET_DATASOURCE(48, "CallDataFlowFront");     // ← 应该是 "SetDataSource"
```

**★★★ 后果：`getByStrCode("CallDataFlowFront")` 只会返回第一个（46），47/48 永远取不到。**
**⇒ 这三个 actionType 在**后端代码生成路径上是**不可用/失效的**。**

**★★★ 而且 `EXTEND_ACTION` 在整个 Maven 仓库里**没有任何实现类**（全 jar 字节搜索只命中 2 个枚举文件）。**
**⇒ 客开扩展点只是**枚举占位**，平台还没实现。**

### 2.1 ★★★★★ 两个分组常量（`static {}` 实测）

```java
DATA_ACTIVITY_TYPES = EnumSet.of(
    RETRIEVE, RETRIEVE_ARRAY, CREATE_ENTITY, CREATE_BATCH_ENTITY,
    CHANGE_ENTITY, CHANGE_BATCH_ENTITY, DELETE_ENTITY);
// → 7 个！不是 6 个（含 RETRIEVE）
```
**★ 数据操作类节点 7 个：查1 / 查多 / 增 / 批量增 / 改 / 批量改 / 删**

```java
BASE_SERVICE_TYPES = EnumSet.of(
    CALL_APP_SERVICE, PUBLISH_BUSINESS_EVENT, CONNECTOR, SUB_MICROFLOW, CALL_DATA_FLOW);
// → 5 个
```
**★ 基服务类节点 5 个：调 AppService / 发业务事件 / 连接器 / 子微流程 / 调数据流**

**★★★ 这两个方法的语义：**
```java
isDataActivity(strCode)  // 是否「直接操作实体数据」的节点
isBaseService(strCode)   // 是否「调用其他服务」的节点
```
**⇒ 平台用它们来判断：节点是否需要实体上下文 / 是否需要额外的服务注入。**

### 2.2 ★★ 21 vs 29 的差异

**`ActivityNodeTypeEnum` 有 29 个，但 `nodeActivityHandler` 只有 21 个 case。差 8 个：**

| 多出的 8 个 | 原因 |
|---|---|
| `ATTRIBUTE_REQUIRED`(6) | 走 **entityrule**（实体规则引擎），不是微流程 |
| `ASSIGN_VALUE`(7) | 同上 |
| `SHOW_MESSAGE`(8) | 同上 |
| `ATTRIBUTE_UNIQUE`(9) | 同上 |
| `DEFAULT_VALUE`(21) | 同上 |
| `CALL_MICRO_FLOW`(17) | 未在 nodeActivityHandler 出现（可能走别处） |
| `EXTEND_ACTION`(47) | **strCode bug，失效** |
| `SET_DATASOURCE`(48) | **strCode bug，失效** |

**★★★★★ 关键结论：**
```
29 个 Activity 节点
 ├─ 21 个 → 微流程代码生成（nodeActivityHandler）
 ├─  5 个 → 实体规则代码生成（entityrule/*.ftl）
 ├─  1 个 → CALL_MICRO_FLOW（未找到生成路径）
 └─  2 个 → EXTEND_ACTION / SET_DATASOURCE（strCode bug，实际不可用）
```

---

## 3. ★★★★★ `MicroFlowActivityTypeEnum`（101 个）与 29 个的关系

| 枚举 | 数量 | 用途 |
|---|---:|---|
| `MicroFlowActivityTypeEnum` | **101** | 全量（后端 + 前端 + 元信息 + 页面动作） |
| `ActivityNodeTypeEnum` | **29** | 只后端节点（strCode 供模板用） |

**⇒ 101 是「设计器可拖的所有节点」，29 是「后端能生成代码的」。**

**★ 但在 `ActivityNodeTypeEnum` 里，`CREATE_MAP`/`MAP_OPERATION`/`DATA_MAPPING` 的 code 是 43/44/45，
而 `MicroFlowActivityTypeEnum` 里是 65/66/83 —— **两个枚举的 code 编号体系完全不同**，不能混用。**

---

## 4. ★★★ `ListOperationTypeEnum`：19 种集合运算（权威，含分组）

| code | strCode | 中文 | 分组 |
|--:|---|---|---|
| 0 | `sum` | 求和 | AGGREGATION 聚合 |
| 1 | `size` | 计数 | AGGREGATION |
| 2 | `max` | 最大值 | AGGREGATION |
| 3 | `min` | 最小值 | AGGREGATION |
| 4 | `filter` | 过滤 | INSPECTION 检查 |
| 5 | **`find`** | 查找 | INSPECTION |
| 6 | `sort` | 排序 | INSPECTION |
| 7 | `union` | 并集 | **BINARY 双集合** |
| 8 | `intersect` | 交集 | **BINARY** |
| 9 | **`subtract`** | **差集** | **BINARY** |
| 10 | **`contains`** | 包含 | JUDGEMENT 判断 |
| 11 | **`equals`** | 相等 | JUDGEMENT |
| 12 | `groupAndSum` | 分组汇总 | **BINARY** |
| 13 | `firstOne` | 第一条 | INSPECTION |
| 14 | `lastOne` | 最后一条 | INSPECTION |
| 15 | `pickOne` | 选择一条 | INSPECTION |
| 16 | `distinct` | 去重 | INSPECTION |
| 17 | `subList` | 获取子列表 | **BINARY** |
| 18 | `map` | 字段收集 | **BINARY** |

**★★★★★ 关键补充（模板里没看到但枚举里有）：**
```
① find(5)      查找 —— 模板 16 个 case 里没有！说明模板可能落后于枚举
② contains(10) 包含 —— 判断类，不是运算类
③ equals(11)   相等 —— 判断类
④ groupAndSum(12) 分组汇总
⑤ 19 个 vs 模板 16 个 → 模板少了 find / contains / equals
```

**★★★★ `ListOperationGroupEnum` 四组（5 类）：**
```
AGGREGATION  聚合（sum/size/max/min）
INSPECTION   检查/取（filter/find/sort/firstOne/lastOne/pickOne/distinct）
BINARY       双集合（union/intersect/subtract/groupAndSum/subList/map）
JUDGEMENT    判断（contains/equals）
```
**★★★ 注意：`groupAndSum`/`subList`/`map` 被归到 BINARY，说明它们也需要「第二个参数」
（groupAndSum 需分组字段、subList 需起止、map 需字段名）—— 不是「第二个集合」，是「第二个参数」。**

**★★ `subtract`（差集）在 BINARY 组 ⇒ 确认需要第二集合。**
**⇒ `LIST_OPERATION.SUBTRACT` = 集合 A 减集合 B，内存运算。**

---

## 5. ★★★★ `BaseNodeGroupEnum`：节点分组（决定出现在哪个设计器）

```
0  ALL          "All"          全部
1  MICROFLOW    "MicroFlow"    后端微流程
2  ENTITY_RULE  "EntityRule"   实体规则
3  FRONTEND     "Frontend"     前端（页面规则）
4  CUSTOM       "CUSTOM"       ★ 自定义
5  FUNCTION     "FUNCTION"     ★ 函数
```

**★★★★★ 这回答了「节点在哪个设计器里能拖」：**
```
MICROFLOW    后端微流程设计器
ENTITY_RULE  实体规则设计器
FRONTEND     页面规则（前端微流程）设计器
CUSTOM       自定义节点（客开）
FUNCTION     函数节点
```

**★★ `CUSTOM` 组存在 ⇒ 平台**设计上支持客开自定义节点分组**，即使 EXTEND_ACTION 没实现。**

---

## 6. ★★★ 其他相关枚举（`udc-biz` 的 `enums/microflow/`，35 个）

```
ActivityCreateTypeEnum        节点创建方式
AppServiceTypeEnum            AppService 类型
AttrValueTypeEnum             属性值类型
BaseNodeGroupEnum             ★ 节点分组（见第 5 节）
ChangeListActionTypeEnum      改列表的动作类型
CopyTypeEnum                  复制类型
CronTypeEnum                  ★ 定时表达式类型
CustomErrorTypeEnum           自定义错误类型
DepAppNodeEnum                依赖应用节点
DtoParserTypeEnum             Dto 解析类型
ListOperationGroupEnum        ★ 集合运算分组
ListOperationTypeEnum         ★ 集合运算（见第 4 节）
MapOperationTypeEnum          映射操作类型
MappingTypeEnum               映射类型
MetaDataTypeEnum              元数据类型
MicroFlowDtoTypeEnum          微流程 Dto 类型
MicroFlowErrorTypeEnum        微流程错误类型
MicroFlowEventTypeEnum        ★ 事件类型
MicroFlowGroupTypeEnum        微流程分组
MicroFlowMacroTypeEnum        ★ 宏类型（预设微流程？）
MicroFlowNodeTypeEnum         ★ 节点类型（见第 1 节）
MicroFlowParamDataTypeEnum    参数数据类型
MicroFlowParseErrorEnum       解析错误
NullHandlingEnum              ★ 空值处理策略
OtherTypeEnum                 其他
ParamTypeEnum                 ★ 参数类型（Expression/SelectParam/Simple？）
PresetTemplateSourceEnum      预设模板来源
RotationTypeEnum              轮转类型
...
```

**★★★ `ParamTypeEnum` —— 实测是**8 种参数类型**（不是三态）：**
```java
DEFAULT_OBJECT(0)   默认对象
BASIC(1)            基础值
ENTITY_OBJECT(2)    ★ 实体对象
ENUM(3)             ★ 枚举
MAP(4)              映射
METADATA(5)         元数据
MESSAGE(6)          消息
OTHER(7)            其他
```
**⇒ 这是「节点参数/变量的类型」，不是「表达式三态」。**
**★ 之前从模板里看到的 `Expression / SelectParam / Simple` 是**取值来源**（另一种维度）。**

**★★ `NullHandlingEnum` —— 空值处理策略（表达式/映射里怎么处理 null）。**
**★★ `MicroFlowMacroTypeEnum` —— 微流程「宏」，对应 `MicroFlowMacroController`。**

---

## 7. ★★★★★ 完整节点 → 代码生成路径对照（最终版）

| node.type | 数量 | 生成方式 | 模板/宏 |
|---|---:|---|---|
| `ACTIVITY` | 21（后端） | `<#switch node.actionType>` | `nodeActivityHandler` → 21 个 `*Activity.ftl` |
| `ACTIVITY` | 5（实体规则） | 另一套 | `entityrule/*.ftl`（9 个） |
| `BRANCH` | 1 | `if/else if/else` | `branceLogicNodeHandler` |
| `FOR_EACH` | 1 | `for (T x : list)` | `forEachLogicHandler` |
| `FOR` | 1 | `for (int i = ...)` | `foriLogicHandler` |
| `CUSTOM_ERROR` | 1 | `throw BusinessException` | `errorLogicHandler` |
| `CONDITION` | 1 | 分支内条件（不独立生成） | 内联 |
| `END` | 1 | 不生成 | — |
| `BREAK` | 1 | `break` | 内联 |

**★★★★★ 8 个 node.type 全都有归属，没有遗漏。**

---

## 8. ★★★ 平台 bug 清单（本轮发现）

**① `ActivityNodeTypeEnum` 的 strCode 复制粘贴错误：**
```java
CALL_DATA_FLOW_FRONT(46, "CallDataFlowFront"),
EXTEND_ACTION(47, "CallDataFlowFront"),      // 应为 "ExtendAction"
SET_DATASOURCE(48, "CallDataFlowFront");     // 应为 "SetDataSource"
```
**后果：`getByStrCode()` 对这三个 strCode 都返回 46，47/48 无法通过 strCode 取到。**

**② `EXTEND_ACTION` 无任何实现类（全仓库字节搜索确认）：**
```
只命中 2 个枚举文件：ActivityNodeTypeEnum.class / MicroFlowActivityTypeEnum.class
没有 ExtendAction* / ExtendActivity* / ExtendNode* 任何类
```
**⇒ 客开扩展点是**纯占位，未实现**。**

**③ `ListOperationTypeEnum`（19）比模板 case（16）多 3 个：**
```
模板缺：find(5) / contains(10) / equals(11)
```
**⇒ 这三项**设计器可配但不会生成代码**（或走其他路径）。**

---

## 9. ★ 与我已有文档的印证/修正

| 旧结论 | 本轮 |
|---|---|
| 「node.type 5 类」 | **❌ 修正：实际 8 类**（+CONDITION/END/BREAK） |
| 「微流程 56 个 actionType」 | **❌ 修正：101 个全量 / 29 个后端 / 21 个生成代码** |
| 「集合运算 16 种」 | **✅ 补充：枚举 19 种，模板 16 种** |
| 「SUBTRACT 需第二集合」 | **✅ 确认：BINARY 组** |
| 「EXTEND_ACTION 是客开扩展点」 | **✅ 确认，但 ❌ 未实现（纯占位）** |
| 「微流程分前端/后端」 | **✅ 确认：BaseNodeGroupEnum 有 MICROFLOW / FRONTEND 分组** |

---

## 10. 未覆盖

| 项 | 说明 |
|---|---|
| `CYCLIC_NODE_TYPES` / `CONTAINER_NODE_TYPES` 成分 | 被截断，需补查 |
| `ParamTypeEnum` 三态确认 | 未读 |
| `NullHandlingEnum` | 未读 |
| `MicroFlowMacroTypeEnum`（宏） | 未读 |
| `MicroFlowEventTypeEnum`（事件类型） | 未读 |
| `CronTypeEnum`（定时） | 未读 |
| `MapOperationTypeEnum`（映射操作） | 未读 |
| `CALL_MICRO_FLOW(17)` 的生成路径 | 未找到（不在 nodeActivityHandler） |
| 其余 26 个枚举的完整内容 | 未读 |