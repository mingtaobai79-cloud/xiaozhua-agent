# ★★★★★ 微流程代码生成：节点 → Java 类（实证）

> 数据源：`udc-biz-5.3.605.jar`
> - `autocode/JAVA/2.9/templates/microflow/MicroFlowDomainService.java.ftl`（41,740 字符 / 42 KB）
> - 66 个 microflow 模板（含 11 个子目录）
> 等级：`VERIFIED_STATIC_BYTECODE`（FTL 原文实测）
> 时间：2026-11-18

---

## 0. ★★★★ 一句话结论

**微流程「不是运行时解释执行」，而是把画布上的每个节点编译成 Java 语句，写进一个 `MicroFlowDomainService` 类的 `run` 方法里。**

```
微流程画布（节点树）
    ↓ MicroFlowDomainService.java.ftl
{MicroFlow}DomainService.java    ← 一个微流程 = 一个 Java 类
    ├─ run(...) 方法体
    │    ├─ node1 的 Java 语句
    │    ├─ for(...) { node2 ... }
    │    └─ if(...) { ... } else { ... }
    └─ 私有表达式方法 exp{雪花}(...)
```

---

## 1. ★★★★ 两种宏层级：Logic（结构）+ Activity（动作）

**`MicroFlowDomainService.java.ftl` 的 12 个宏：**

| 宏 | 类型 | 作用 |
|---|---|---|
| **`nodesLogicHandler`** | ★★★ **总分发** | 遍历节点列表，按 `node.type` 分派 |
| `nodeActivityHandler` | ★★★ **Activity 分发** | 按 `node.actionType` 分 21 个 case |
| **`branceLogicNodeHandler`** | 结构 | 分支 → `if / else if / else` |
| **`forEachLogicHandler`** | 结构 | 遍历 → `for (T x : list)` |
| **`foriLogicHandler`** | 结构 | 计数循环 → `for(int i=start; ...)` |
| **`errorLogicHandler`** | 结构 | 自定义错误 → 抛异常 |
| `buildErrorInfo` | 辅助 | 组装错误信息 |
| `buildMfService` | 辅助 | 类骨架 |
| `buildFormulaPrivateMethod` | 辅助 | 表达式私有方法 |
| `buildFilterListOperationFormulaMethod` | 辅助 | 集合过滤表达式方法 |
| `buildConditionPrivateMethod` | 辅助 | 条件私有方法 |
| `validateInputParamAttrRequired` | 辅助 | 入参必填校验 |

---

## 2. ★★★★★ `nodesLogicHandler`：5 类节点（第一层分发）

**原文：**
```freemarker
<#macro nodesLogicHandler nodes microflowInfo deployType microFlowInOutParamBo parentNode needDealLog>
    <#list nodes as node>
        <#-- 要调方法，有些方法会重写逻辑！ -->
        <#if !node.isShouldGenerateCode()><#continue></#if>
        <#switch node.type>
            <#case "Activity">
                <@nodeActivityHandler ... />
            <#case "Branch">
                <@branceLogicNodeHandler ... />
            <#case "ForEach">
                <@forEachLogicHandler ... />
            <#case "For">
                <@foriLogicHandler ... />
            <#case "CustomError">
                <@errorLogicHandler ... />
        </#switch>
    </#list>
</#macro>
```

**★★★★★ `node.type` 只有 5 种：**
```
Activity      动作节点  → 21 种 actionType（见第 3 节）
Branch        分支节点  → if / else if / else
ForEach       遍历节点  → for (T x : list)
For           计数循环  → for (int i = start; i < end; i++)
CustomError   自定义错误 → 抛异常
```

**★★★ 重要：`node.isShouldGenerateCode()` 过滤 —— 有些节点不生成代码（如纯注释、禁用节点、endNode）。**
**⇒ 这解释了「56 个 actionType」与「21 个生成模板」的差异：**设计器可配 56 种，但只有 21 种需要生成 Java 代码，其余是结构/控制/元信息节点。**

---

## 3. ★★★★★ `nodeActivityHandler`：21 个 actionType → 模板（完整实测）

| # | actionType | 生成模板 | 大小 |
|--:|---|---|---:|
| 1 | `CreateVariable` | CreateVariableActivity.java.ftl | 5.9 KB |
| 2 | `ChangeVariable` | ChangeVariableActivity.java.ftl | 7.0 KB |
| 3 | `CreateList` | CreateList.java.ftl | 2.6 KB |
| 4 | `ChangeList` | ChangeList.java.ftl | 7.7 KB |
| 5 | `CreateMap` | CreateMapActivity.java.ftl | 1.0 KB |
| 6 | `MapOperation` | MapOperationActivity.java.ftl | 1.9 KB |
| 7 | `PublishBusinessEvent` | BusinessEventActivity.java.ftl | 5.0 KB |
| 8 | `ListOperation` | ListOperationActivity.java.ftl | **42.9 KB** |
| 9 | `SubMicroFlow` | SubMicroFlowActivity.java.ftl | 4.7 KB |
| 10 | `CallAppService` | CallAppServiceActivity.java.ftl | 4.2 KB |
| 11 | **`CallDataFlow`** | **（无 include，走 paster 注入）** | — |
| 12 | `Connector` | ConnectorActivity.java.ftl | 0.8 KB |
| 13 | `Retrieve` | RetrieveActivity.java.ftl | 4.4 KB |
| 14 | `RetrieveArray` | RetrieveArrayActivity.java.ftl | 5.9 KB |
| 15 | `ChangeEntity` | ChangeEntityActivity.java.ftl | 1.3 KB |
| 16 | `CreateEntity` | CreateEntityActivity.java.ftl | 2.4 KB |
| 17 | `CreateBatchEntity` | CreateBatchEntityActivity.java.ftl | 0.8 KB |
| 18 | `ChangeBatchEntity` | ChangeBatchEntityActivity.java.ftl | 0.9 KB |
| 19 | `DeleteEntity` | DeleteEntityActivity.java.ftl | 3.2 KB |
| 20 | `ConvertData` | ConvertDataActivity.java.ftl | 3.3 KB |
| 21 | `DataMapping` | DataMappingActivity.java.ftl | **18.1 KB** |

**★★★ 三个异常点：**
```
① ListOperation 42.9 KB —— 最大，集合运算（含 SUBTRACT 扣减）
② DataMapping 18.1 KB   —— 次大，字段映射
③ CallDataFlow 无 include —— 走 <@paster name="call.data.flow.import[{entityId}]"/>
```

**★★★ `CallDataFlow` 为什么特殊？**
**因为它跨子域（microflow → dataflow），平台用 Paster 机制让 `udc-dataflow` 把自己的代码片段注入：**
```freemarker
<#list sourceEntityIdList as id>
    <@paster name="call.data.flow.import["+id+"]"></@paster>
</#list>
```
**⇒ 对应 `CallDataFlowActivityImport.ftl` / `CallDataFlowActivityDI.ftl` / `CallDataFlowActivity.java.ftl` 三个文件，由 `udc-dataflow` 的 PasterConfig 注册。**

---

## 3A. ★★★★★ `MicroFlowActivityTypeEnum` 全量：101 个 actionType（反编译实证）

**来源：`udc-common-5.3.605.jar` → `com.seeyon.udc.common.enums.MicroFlowActivityTypeEnum`（CFR 反编译）**

```
索引 0-102，枚举 101 个，缺失索引: [30, 85]（预留/废弃）
```

### 3A.1 ★★★ 四桶分类（21 / 11 / 6 / 63）

| 桶 | 数量 | 说明 |
|---|---:|---|
| **后端生成代码** | **21** | `nodeActivityHandler` 的 21 个 case |
| **结构节点** | **11** | `node.type` 5 类的来源 |
| **前端节点（`_FRONT`）** | **6** | 只在页面规则里跑 |
| **后端元信息 / 表单规则 / 页面动作** | **63** | 不生成微流程代码 |

### 3A.2 ★★★★★ 21 个后端生成代码的 actionType（枚举 ↔ 驼峰对照）

| 索引 | 枚举常量 | actionType（模板里的驼峰名） | 中文 |
|--:|---|---|---|
| 0 | `CONNECTOR` | `Connector` | 连接器 |
| 1 | `CREATE_VARIABLE` | `CreateVariable` | 创建变量 |
| 2 | `CHANGE_VARIABLE` | `ChangeVariable` | 修改变量 |
| 3 | `CREATE_LIST` | `CreateList` | 创建列表 |
| 4 | `CHANGE_LIST` | `ChangeList` | 修改列表 |
| 5 | `PUBLISH_BUSINESS_EVENT` | `PublishBusinessEvent` | 业务消息 |
| 10 | `RETRIEVE` | `Retrieve` | 查询单记录 |
| 11 | `RETRIEVE_ARRAY` | `RetrieveArray` | 查询多记录 |
| 12 | `CHANGE_ENTITY` | `ChangeEntity` | 更新数据 |
| 13 | `CREATE_ENTITY` | `CreateEntity` | 插入数据 |
| 14 | `DELETE_ENTITY` | `DeleteEntity` | 删除数据 |
| 15 | `LIST_OPERATION` | `ListOperation` | 列表操作 |
| 16 | `SUB_MICROFLOW` | `SubMicroFlow` | 子流程 |
| 18 | `CALL_APP_SERVICE` | `CallAppService` | 服务调用 |
| 19 | `CALL_DATA_FLOW` | `CallDataFlow` | 生单规则 |
| 40 | `CONVERT_DATA` | `ConvertData` | 类型转换 |
| 41 | `CREATE_BATCH_ENTITY` | `CreateBatchEntity` | 批量插入数据 |
| 42 | `CHANGE_BATCH_ENTITY` | `ChangeBatchEntity` | 批量修改数据 |
| 65 | `CREATE_MAP` | `CreateMap` | 创建映射 |
| 66 | `MAP_OPERATION` | `MapOperation` | 映射操作 |
| 83 | `DATA_MAPPING` | `DataMapping` | 数据转换 |

**★★★ 命名规律：枚举 `UPPER_SNAKE` → 模板 case `UpperCamel`（去下划线）。**

### 3A.3 ★★★ 11 个结构节点

```
43  START              开始
44  END                结束
45  BRANCH             分支        → branceLogicNodeHandler
46  FOR                计数循环    → foriLogicHandler
47  CONDITION          条件        → （分支内的条件）
48  FOR_EACH           列表循环    → forEachLogicHandler
49  CUSTOM_ERROR       自定义错误  → errorLogicHandler
50  OTHERS_CONTROL     其他事件
72  BREAK              跳出循环
76  END_NODE           结束
77  INPUT_NODE         入参
```

**★★★ 与 `node.type` 的 5 类（Activity/Branch/ForEach/For/CustomError）对照：**
```
node.type 是「大类」，actionType 是「具体类型」
Activity      → 21 个后端 actionType（+ 63 个元信息型 activityType）
Branch        → BRANCH(45)
For           → FOR(46)
ForEach       → FOR_EACH(48)
CustomError   → CUSTOM_ERROR(49)
```
**⇒ START / END / CONDITION / BREAK / END_NODE / INPUT_NODE 是**辅助结构**，不独立生成代码块。**

### 3A.4 ★★★ 6 个前端节点（`_FRONT` 后缀）

```
54  CREATE_VARIABLE_FRONT    创建变量
55  CHANGE_VARIABLE_FRONT     修改变量
56  CREATE_LIST_FRONT         创建列表
57  CHANGE_LIST_FRONT         修改列表
73  CONVERT_DATA_FRONT         类型转换
78  CALL_DATA_FLOW_FRONT       生单规则
```

**★★★★★ 关键：这 6 个是**后端 21 个的前端镜像** —— 同样的能力在页面规则（前端微流程）里也要有。**
**⇒ 印证了你记忆里的**「微流程分前端/后端两套」**：**
```
后端微流程（DomainService）  →  21 个后端 actionType → Java 代码
前端微流程（页面规则）      →  6 个 _FRONT + 63 个页面动作 → JS/前端执行
```

### 3A.5 ★★★★ 63 个「后端元信息 / 表单规则 / 页面动作」

**这些不生成微流程 Java 代码，但都是合法 actionType。按语义分 5 组：**

**① 实体规则（entityrule，走 9 个 `*Activity.ftl` 的另一套）**
```
6   ATTRIBUTE_REQUIRED   必填
7   ASSIGN_VALUE         设置值
8   SHOW_MESSAGE         提示信息
9   ATTRIBUTE_UNIQUE     唯一
21  DEFAULT_VALUE        默认值
```
**⇒ 对应 `entityrule/AttributeRequiredActivity.ftl` 等 5 个模板（见第 27 号文档）。**
**⚠️ 这 5 个虽然不生成微流程代码，但**会生成规则代码** —— 属于「实体规则引擎」而非「微流程引擎」。**

**② 表单/控件行为（页面规则专用，前端执行）**
```
20  VISIBLE              可见性
22  ATTR_VISIBLE        可见性
23  SET_VALUE           设置值
24  SET_REQUIRED        必填
25  ENABLE              启用禁用
26  READ_ONLY           只读
38  CLEAR_VALUE         清空值
67  CONTROL_ACTION      控件动作
75  VALUE_HANDLE        值操作
88  CONTROL_STATUS      控件状态
89  ADVANCED_PROPERTIES 高级属性
102 SET_DATASOURCE      SetDataSource
```
**⇒ 这是**表单交互**类节点，只在页面规则（前端微流程）里有效。**

**③ 页面/导航动作（前端执行）**
```
27  OPEN_PAGE           打开页面
28  CLOSE_PAGE          关闭页面
29  OPEN_URL            打开链接
34  MODAL               对话框
68  PAGE_LOADING        页面加载
69  OUT_PAGE_LOADING    退出页面加载
70  CONFIRM_CLOSE_PAGE  确认关闭页面
74  RELOAD_PAGE         刷新页面
```

**④ 实体数据操作（前端直连数据源，走后端的 DATA_SOURCE_* / ENTITY_* 两口）**
```
31  DATA_SOURCE_SAVE    保存
32  DATA_SOURCE_DELETE  删除
33  DATA_SOURCE_SEARCH  实体查询
58  ENTITY_SAVE         保存记录
59  ENTITY_SUBMIT       提交记录
60  ENTITY_EDIT         实体编辑
61  ENTITY_REFRESH      刷新记录
62  ENTITY_DELETE       实体删除
63  ENTITY_SAVE_DRAFT   存为草稿
64  ENTITY_WITHDRAW    撤回记录
96  ENTITY_COPY_DATA    实体一键复制
97  ENTITY_EXPORT       导出
98  ENTITY_IMPORT       导入
99  ENTITY_SAVE_NEW     保存并新增
100 ENTITY_SAVE_COPY    保存并复制
```
**★★★ 两套并存：`DATA_SOURCE_*`（3 个，早期/通用）和 `ENTITY_*`（12 个，新版细化）。**
**⇒ `ENTITY_*` 覆盖保存/提交/编辑/刷新/删除/草稿/撤回/复制/导入导出/保存并新增/保存并复制 —— 是完整的表单生命周期。**

**⑤ 消息 / 平台集成 / 其他**
```
17  CALL_MICRO_FLOW       后端微流程（注意：不是 SUB_MICROFLOW！）
35  MESSAGE_INFO          提示信息
36  CLEAR_MESSAGE_INFO    清空提示信息
37  SEND_MQ_MESSAGE       消息中心
39  CREATE_AFFAIR         待办中心
51  FED_LIST_OPERATION    列表操作（前端版）
52  CALL_FRONT_FLOW       页面规则
53  CALL_SERVICE          调用服务
71  FLOW_ACTION           流程动作
79  ATTACHMENT_DOWNLOAD   附件下载
80  OPEN_REPORT           打开报表
81  THROW_EVENT           子页面事件
82  FRONT_CUSTOM_ERROR    自定义错误（前端）
84  SCAN_CODE             扫码
86  ATTACHMENT_PREVIEW    附件预览
87  ATTACHMENT_UPLOAD     附件上传
90  PRINTPAGE             打印
91  LOCATION_CMP          锚点跳转
92  ATTENTION             关注/取消关注
93  LABEL_PRINT           标签打印
94  FORM_CONVERT          单据转文档
95  DOWNLOAD_ALL          下载全部
101 EXTEND_ACTION         ExtendAction（★ 扩展点）
```

**★★★ 三个值得注意的：**
```
① CALL_MICRO_FLOW(17) 和 SUB_MICROFLOW(16) 是两个不同的！
   SUB_MICROFLOW  = 子流程（内嵌，同一次执行上下文，可调标准或 CUSTOM）
   CALL_MICRO_FLOW = 后端微流程（独立调用，可能是异步/Dubbo）

② FED_LIST_OPERATION(51) 和 LIST_OPERATION(15) 也是两个
   LIST_OPERATION  = 后端集合运算（42.9 KB 模板，16 种 operationType）
   FED_LIST_OPERATION = 前端集合运算

③ EXTEND_ACTION(101) = 客开扩展点
   ★ 这是平台留给我自己的节点扩展入口！

④ CALL_SERVICE(53) vs CALL_APP_SERVICE(18)
   CALL_APP_SERVICE = 调 UDC AppService（生成代码）
   CALL_SERVICE     = 通用服务调用（前端/规则层）
```

---

## 4. ★★★★★ `Activity` 三种命名风格（实测差异）

**模板文件名不统一：**
```
*Activity.java.ftl       18 个（CreateVariable / ChangeVariable / CreateMap /
                          MapOperation / Retrieve / RetrieveArray / CreateEntity /
                          CreateBatchEntity / ChangeEntity / ChangeBatchEntity /
                          DeleteEntity / ConvertData / BusinessEvent / SubMicroFlow /
                          CallAppService / Connector / DataMapping / ListOperation）
*.java.ftl                2 个（CreateList / ChangeList）★ 无 Activity 后缀
```

**★ 说明 `CreateList` / `ChangeList` 是后加的，未遵循命名约定。**

---

## 5. ★★★★ `SubMicroFlowActivity`：同时支持标准与自定义微流程（实证）

**`SubMicroFlowActivity.java.ftl` 原文揭示：**

```freemarker
<#assign mfService = node.mfService>
<#assign calledMicroFlow4CodeDto = microFlow4CodeDtoMap[mfService.id]>

<#-- ★★★ 注入自定义微流程的 Bean 为 null 时，直接抛异常 -->
<#if "CUSTOM" == calledMicroFlow4CodeDto.type>
    if(${calledMicroFlow4CodeDto.uncapAppServiceName} == null){
        throw new BusinessException(MicroFlowErrorCode.UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED);
    }
</#if>
...
<#if "CUSTOM" == calledMicroFlow4CodeDto.type>
    <#assign callMethod = MicroFlowCodeUtil.buildCallMethodByMicroFlow4CodeDto(...)>
    ${callMethod.respOutputParam} ${respName} = ${callMethod.serviceName}.${callMethod.method}(${callMethod.inputParam!""});
    if(!${respName}.success()) {
        log.error("nodeId:【{}】 nodeCaption【{}】 variableKey【{}】 resp【{}】", ...);
```

**★★★★★ 三个关键结论：**
```
① 子微流程节点可以调「标准微流程」或「自定义微流程」（type == "CUSTOM"）
② 自定义微流程 = 一个 Spring Bean（{xxx}AppService），通过方法调用
③ Bean 为 null 就抛 UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED
   ⇒ 自定义微流程必须先实现接口并注册 Bean，否则运行期才报错
```

**★★★ 这印证了你记忆里的关键区分：**
```
「标准微流程」= 画布搭节点 → 生成 DomainService 类
「自定义微流程」= 写 Java 实现接口 → 注册为 AppService Bean
```

**★★ 注意命名约定：入参变量名为 `"v" + nodeId`（原文注释：「约定参数名为 "v" + nodeId」）。**

**★ 自定义微流程有 `hasPagination` / `pageInfo` —— 支持分页返回。**

---

## 5A. ★★★★ `CallDataFlow` 的 paster 三段（实测 paster 名）

**`MicroFlowDomainService.java.ftl` 里只有 3 个 paster 名（全部属于 CallDataFlow）：**

```
call.data.flow.di[      ← @Autowired 声明
call.data.flow.import[  ← import 语句
call.data.flow[         ← 节点调用体
```

**★★★ `paster` 名格式：`{prefix}[{动态key}]` —— 方括号部分是变量（这里是 sourceEntityId）。**
**⇒ 同一个微流程引用多个来源实体时，会生成多组 DI/import，用 entityId 区分。**

**★ 这也说明：**平台目前只有 CallDataFlow 一个跨子域 paster 节点**。**
**⇒ 若我要加自定义节点（EXTEND_ACTION），应该也走这个机制。**

---

## 6. ★★★★★ `ListOperationActivity`（42.9 KB）—— 集合运算核心

**最大模板（实测 40,568 字符）。**

**★★★★★ `operationType` 共 16 种（`<#switch>` 的 case 实测）：**

| operationType | 中文 | 说明 |
|---|---|---|
| `SUM` | 求和 | 分 INTEGER/BIGINTEGER/DECIMAL/CURRENCY/DTO 五路 |
| `MAX` | 最大值 | |
| `MIN` | 最小值 | |
| `SIZE` | 长度 | |
| `DISTINCT` | 去重 | |
| `FILTER` | 过滤 | |
| `SORT` | 排序 | |
| `MAP` | 映射 | |
| `SUB_LIST` | 取子集 | |
| `FIRST_ONE` | 取第一个 | |
| `LAST_ONE` | 取最后一个 | |
| `PICK_ONE` | 取指定一个 | |
| `UNION` | 并集 | ★ 需第二集合 |
| `INTERSECT` | 交集 | ★ 需第二集合 |
| **`SUBTRACT`** | **差集（扣减）** | ★ 需第二集合 |
| `GROUP_AND_SUM` | 分组求和 | |

**★★★★★ 三个关键机制：**

**① `requiredOperationParam(operationType)` —— 只有 3 个操作需要第二集合：**
```
UNION / INTERSECT / SUBTRACT
```
**⇒ 这三个是**双集合运算**，其余都是单集合运算。**

**② 每个双集合运算要生成 **4 个中间变量**（原文）：**
```freemarker
newSourceListName          = nodeId + "NewSourceList"            ← 过滤后源集合
newOperationParamListName  = nodeId + "NewOperationParamList"    ← 过滤后第二集合
deletedSourceListName      = nodeId + "DelSourceList"            ← 被删的源数据
deletedOperationParamListName = nodeId + "DelOperationParamList"  ← 被删的第二集合数据
```

**③ `SUM` 按数据类型分五路生成不同代码（原文）：**
```java
// INTEGER / BIGINTEGER
XxxType out = list.stream().filter(Objects::nonNull).reduce(XxxType::sum).orElse(XxxType.valueOf("0"));
// DECIMAL / CURRENCY
BigDecimal out = list.stream().filter(Objects::nonNull).reduce(BigDecimal.ZERO, BigDecimal::add);
// DTO（实体集合）
filterDeletedData(...);   // 先过滤掉 DELETE 的行，再对某属性求和
```

**★★★ `SUBTRACT`（扣减）的语义最终确认：**
```
集合A（源） - 集合B（第二集合） = 差集
在「内存 List<Dto> 上做差运算」
★ 不生成 SQL，不碰数据库
```
**⇒ 与「扣减规则 Deduction」（生成 SQL 直改数据库）是两个完全独立的东西。**

**★ `GROUP_AND_SUM` —— 分组求和，对应报表类需求。**

---

## 6. ★★★★ `foriLogicHandler`：三种循环起点（`forStart.type`）

```freemarker
<#if foriNode.forStart.type == "Expression">
    Integer forStart${output} = ${表达式生成的代码片段}
<#elseif foriNode.forStart.type == "SelectParam">
    Integer forStart${output} = <@convertSelectParamValue ... />
<#elseif foriNode.forStart.type == "Simple">
    Integer forStart${output} = <@convertSimpleValue ... />
```

**★★★ `For` 节点的起点有三种来源：**
```
Expression    表达式（可引用变量）
SelectParam   选择参数（引用上游节点输出）
Simple        恒定简单值
```

**⇒ 这套「Expression / SelectParam / Simple」三态是平台**所有节点参数**的统一形态。**
**★ 同样适用于 `forall` 的终点、条件判断等。**

---

## 7. ★★★★ `forEachLogicHandler`：遍历节点（含脏数据处理）

```freemarker
<#assign listDataType>
    <#if forEachNode.output.dataType?cap_first=="ENTITY">
        ${entityMap[forEachNode.output.id].capFirstName}       ← 实体类型
    <#else>
        ${fullNameTransformer.transform(forEachNode.output.javaType, VirtualFullNameType.DTO)}
    </#if>
</#assign>

if(${selectParam.outputName} != null){
    <#local newListName = nodeId + "FilterDelData">
    <#local sourceList = MicroFlowCodeUtil.getSelectParamValue(selectParam)>
    <#-- ★★★ 实体类型数据过滤 DELETE 的数据 -->
    ${MicroFlowCodeUtil.filterDeletedData(mfAppInfo, selectParam, listDataType, sourceList, newListName)}
    Integer ${nodeId}_forLogIndex = 0;
    for(${listDataType} ${output.name} : ${realListName}){
        ${nodeId}_forLogIndex ++;
        <@buildForStartLog ... />
```

**★★★★★ 关键机制：`filterDeletedData`**
```
遍历实体集合前，先过滤掉 ActionType == DELETE 的数据
```
**⇒ 这是主子表批量操作的必备逻辑：被删除的子表行不应该再参与遍历。**
**★★ 还带 `forLogIndex` 计数器 —— 每个循环迭代都记日志（运行态可看到第几次循环）。**

**★ 另外：`listDataType` 分两种情况**
```
dataType == "ENTITY"  →  用 entityMap 取实体类名
否则                  →  用 fullNameTransformer 转成 DTO 类型
```
**⇒ 遍历也能处理**连接器（Connector）返回的数据**，不限于实体。**

---

## 8. ★★★★ `branceLogicNodeHandler`：分支 → if/else 链

```freemarker
<#list branceNode.conditions as condition>
    <#if condition_index == 0>
        if(${condition.type?lower_case}${condition.nodeId?lower_case}(
            <@buildMicroFlowFormulaMethodParamList expression true />)){
        <@printConditionLog ... />
    <#elseif condition_index == (branceNode.conditions?size - 1)>
        else {                      ← ★ 最后一个默认是 else（无条件）
        <@printElseConditionLog ... />
    <#else>
        else if(${condition.type?lower_case}${condition.nodeId?lower_case}(...)){
        <@printConditionLog ... />
    </#if>
    <@nodesLogicHandler nodes=(condition.nodes!) ... parentNode=branceNode needDealLog=false/>
    }
</#list>
```

**★★★★★ 三个关键点：**
```
① 每个分支条件编译成独立私有方法：{type}{nodeId}(...)
② 最后一个条件 → 无条件 else（兜底分支）
③ needDealLog=false —— 分支内部不再记结束日志（由父节点负责）
```

**★★ 分支条件是**编译成方法**的，不是内联表达式 —— 便于复用和调试。**

---

## 9. ★★★★ `project/*` 模板：新建 UDC 应用生成什么（实测目录树）

**21 个模板渲染出完整 Maven 工程：**

```
backend/
├─ pom.xml                                    ← 父 POM（5.3 KB）
├─ .gitignore
├─ README.md
├─ {appName}-assemble/
│   ├─ pom.xml
│   └─ src/main/java/{appPath}/
│       └─ Application.java                    ← 启动类
│   └─ src/main/resources/
│       └─ application.y                       ← ★ 应用定义（202 B）
├─ {appName}-biz/
│   └─ pom.xml
├─ {appName}-facade/
│   └─ pom.xml
└─ {appName}-web/
    └─ pom.xml
```

**★★★★★ 这就是 `-assemble` / `-biz` / `-facade` / `-web` 四个模块的来源！**
**⇒ 仓库里那些 `{appId}-biz` / `{appId}-web` / `{appId}-facade` / `{appId}-assemble-resource` 是**这个脚手架生成的**。**

**★★ `application.y`（202 B）—— 极小的 YAML，是应用元信息。**

### 9.1 `project-for-deploy/*`（15 个）★ 部署工程

```
TestApplication.java fixture
PersonEntityRuleServiceTest.java     ← 自动生成的单元测试（4.7 KB）
FileHelper.java                      ← 文件助手
pom.xml
application-local.yaml
application.yaml
```

**★★★ 平台会**自动生成单元测试**（`PersonEntityRuleServiceTest`）。**

### 9.2 `project-ext/*`（11 个）★ 扩展工程

```
README.md
pom.xml
package-info.java                ← 空包定义
```

**★ `-ext` 模块 = 客开扩展层，只给 `package-info.java` 占位，代码要自己写。**

---

## 10. ★★★★ microflow 全套 66 个模板（按子目录）

### 10.1 根目录（21 个，Activity 模板 + 2 个核心）

```
ListOperationActivity.java.ftl      42.9 KB ★★★ 最大
MicroFlowDomainService.java.ftl     42.6 KB ★★★★★ 引擎
DataMappingActivity.java.ftl        18.1 KB
ChangeList.java.ftl                  7.7 KB
ChangeVariableActivity.java.ftl      7.0 KB
CreateVariableActivity.java.ftl      5.9 KB
RetrieveArrayActivity.java.ftl       5.9 KB
BusinessEventActivity.java.ftl       5.0 KB
SubMicroFlowActivity.java.ftl        4.7 KB
RetrieveActivity.java.ftl            4.4 KB
CallAppServiceActivity.java.ftl      4.2 KB
ConvertDataActivity.java.ftl         3.3 KB
DeleteEntityActivity.java.ftl        3.2 KB
CreateList.java.ftl                  2.6 KB
CreateEntityActivity.java.ftl        2.4 KB
MapOperationActivity.java.ftl        1.9 KB
ChangeEntityActivity.java.ftl        1.3 KB
CreateMapActivity.java.ftl           1.0 KB
ChangeBatchEntityActivity.java.ftl   0.9 KB
CreateBatchEntityActivity.java.ftl   0.8 KB
ConnectorActivity.java.ftl           0.8 KB
```

### 10.2 `common/`（8 个）★ 工具宏库

```
LogUtil.java.ftl                42.7 KB ★★★ 日志（很大！每个节点都有开始/结束日志）
ValueUtil.java.ftl              16.8 KB ★ 值转换
SetActionTypeUtil.java.ftl      13.5 KB ★ ActionType 设置
CommonUtil.java.ftl             12.3 KB ★ conditionDeal / convertSelectParamValue /
                                          convertSimpleValue（核心宏）
MapUtil.java.ftl                 8.7 KB
GenericInvokeUtil.java.ftl       6.3 KB
CallMethodUtil.java.ftl          3.4 KB
ListActivityUtil.java.ftl        0.6 KB
```

**★★★ `LogUtil` 42.7 KB —— 与引擎模板同样大，说明**日志是微流程的一等公民**。**
**⇒ 每个节点、每次循环、每个分支都记日志（开始/结束/耗时）。**

### 10.3 `customflow/`（7 个）★ 自定义微流程（写 Java 那种）

```
CustomMicroFlowController.java.ftl            9.1 KB
DefaultCustomMicroFlowAppServiceImpl.java.ftl 3.9 KB
DefaultCustomMicroFlowBeanDefinitionRegistryPostProcessor.java.ftl 2.6 KB
DefaultCustomMicroFlowConfig.java.ftl         2.3 KB
CustomMicroFlowService.java.ftl               1.3 KB
CustomMicroFlowAppService.java.ftl            1.0 KB
MicroFlowDubboExportBeanPostProcessor.java.ftl 0.6 KB
```

**★★★★★ 这印证了你记忆里的关键区分：**
```
「标准微流程」= 页面搭节点（走 nodeActivityHandler 的 21 个模板）
「自定义微流程」= 写 Java 扩展（走 customflow/ 模板，生成骨架 + 注册器）
```
**★★ `BeanDefinitionRegistryPostProcessor` —— 自定义微流程**通过 Spring 动态注册 Bean**。**
**★ `MicroFlowDubboExportBeanPostProcessor` —— 自定义微流程可导出为 Dubbo 服务。**
**★ `CustomMicroFlowController`（9.1 KB）—— 自定义微流程也能暴露 REST。**

### 10.4 `event/`（2 个）

```
BusinessEventListener.java.ftl          8.9 KB ★ 业务事件监听
ConnectorBusinessEventListener.java.ftl 6.4 KB ★ 连接器事件监听
```

**★★ 微流程可被**业务事件**和**连接器事件**触发（生成 Listener 类）。**

### 10.5 `plugin/calldataflow/`（3 个）★ 跨子域插件

```
CallDataFlowActivity.java.ftl       1.2 KB
CallDataFlowActivityDI.ftl          156 B   ← @Autowired 声明
CallDataFlowActivityImport.ftl      116 B   ← import 语句
```

**★★★★★ 这是一个**可插拔节点**的标准三段式：**
```
*Activity.java.ftl     节点逻辑
*ActivityDI.ftl        依赖注入（谁提供这个能力）
*ActivityImport.ftl    import 声明
```
**★★ 三段都需要，缺一个就编译不过。**
**⇒ 如果我要给微流程加自定义节点，必须提供这三个文件。**

### 10.6 `web/`（7 个）

```
MicroFlowController.java.ftl                   9.5 KB
MicroFlowAppServiceImpl.java.ftl               3.7 KB
CustomRestApiMicroFlowController.java.ftl      2.7 KB
MicroFlowAppService.java.ftl                   1.2 KB
GraphQLControllerUtil.java.ftl                 1.0 KB
host/HostAppMicroFlowAppServiceImpl.java.ftl   1.1 KB
host/HostAppMicroFlowController.java.ftl       3.0 KB
```

**★★ `host/` —— 微流程可被**宿主机应用**（host app）调用。**

### 10.7 `schedule/` `third/` `customerror/` `plugin/`

```
schedule/MicroFlowSchedule.java.ftl        2.2 KB  ★ 定时触发
third/dynamicSearch.java.ftl               4.3 KB  ★ 第三方动态查询
customerror/CustomError.java.ftl           426 B   ★ 自定义错误
customerror/CustomErrorI18nCN/EN/TW.ftl    121 B   ★ 三语错误消息
```

**★ 微流程的四种触发方式（从模板反推）：**
```
① 业务事件（event/BusinessEventListener）
② 连接器事件（event/ConnectorBusinessEventListener）
③ 定时调度（schedule/MicroFlowSchedule）
④ 宿主应用调用（web/host/HostAppMicroFlowController）
⑤ REST（web/MicroFlowController）
⑥ GraphQL（web/MicroFlowAppServiceImpl）
```

---

## 11. ★★★★★ 生成的 `MicroFlowDomainService` 结构（推理 + 模板证据）

```java
package {domainServicePackage};

@AppService(...)                       // 微流程也是一个 AppService
public class {MicroFlowName}DomainService {

    @Autowired private XxxService xxxService;
    @Autowired private XxxDataFlowRuntimeService xxxDataFlowRuntimeService;  // paster 注入

    public {ResultDto} run({Param}Dto input) {
        // 入参必填校验（validateInputParamAttrRequired）
        
        // ─── 节点代码，按 nodesLogicHandler 展开 ───
        log.info("nodeId:n1 caption:创建变量 start CreateVariable");
        ... CreateVariable 的代码 ...
        
        if(condition1(...)) {                    // Branch
            log.info("nodeId:n2 start forEach");
            for(XxxDto item : list){             // ForEach
                ... 
            }
        } else {
            throw new BusinessException(...);     // CustomError
        }
        
        return result;
    }

    // ─── 表达式私有方法 ───
    private Boolean condition1(Map<String,Object> map) { ... }
    private Integer exp123456(Map<String,Object> map) { ... }
}
```

**★★★ 一个微流程 = 一个 `DomainService` 类 + N 个私有表达式方法。**

---

## 12. ★★★ 与其他文档的印证/修正

| 旧结论 | 本轮 |
|---|---|
| 「微流程 56 个 actionType」 | **修正：设计器可配 56 种，但只有 21 种生成 Java 代码** |
| 「微流程是运行时解释」 | **❌ 修正：编译成 Java 类/方法，运行期直接跑** |
| 「标准微流程 vs 自定义微流程」 | **✅ 确认：`nodeActivityHandler` vs `customflow/*` 两套模板** |
| 「CALL_DATA_FLOW 节点调数据流」 | **✅ 确认，且走 Paster 三段式注入** |
| 「LIST_OPERATION.SUBTRACT 是集合扣减」 | **✅ 确认，42.9 KB 模板，内存运算** |
| 「微流程有 For/ForEach/Branch/Error」 | **✅ 确认，`node.type` 5 类** |

---

## 13. 未覆盖

| 项 | 说明 |
|---|---|
| `ListOperationActivity.java.ftl` 剩余部分 | 只看前 2.5 KB + case 名单 |
| `LogUtil.java.ftl`（42.7 KB）全文 | 未读（日志体系） |
| `CommonUtil.java.ftl` 的 `conditionDeal` / `convertSimpleValue` | 未读 |
| 真实生成的 `XxxDomainService.java` | **未验证**（需沙箱跑生成） |
| `SetActionTypeUtil.java.ftl`（13.5 KB） | 未读（ActionType 传播逻辑） |
| `ValueUtil.java.ftl`（16.8 KB） | 未读（值类型转换） |
| `EXTEND_ACTION(101)` 的具体扩展契约 | 未查（客开扩展点，**最值得挖**） |
| `CALL_MICRO_FLOW(17)` 与 SUB_MICROFLOW 的实现差异 | 只知枚举不同，模板未查 |
| `2.9` 与 `2.7/2.8` 的模板 diff | 未做 |