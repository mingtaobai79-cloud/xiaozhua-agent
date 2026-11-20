# 47 · ★★★★★ 微流程代码生成体系（17 种节点 + 55 个模板）

**证据来源**：`autocode/JAVA/2.9/templates/microflow/*`（55 个 ftl）+ `MicroFlowDomainService.java.ftl`（768 行）
**证据等级**：VERIFIED_STATIC_BYTECODE / 资源原文

---

## 一、★★★★★ 核心结论：微流程**编译成真实 Java 代码**

```
设计态微流程（节点图）
   ↓ MicroFlowDomainService.java.ftl（768 行引擎）
   ↓ 每个节点 → 对应 *Activity.java.ftl
生成的 {microFlowName}Service.java（真实 Java 类）
   ↓
运行时直接执行 Java 代码
```

**⇒ 微流程不是解释执行，是**代码生成**。**
**⇒ 每个节点的执行逻辑在编译期就固化成了 Java 语句。**

---

## 二、★★★★★ 17 种 node.type（`nodesLogicHandler` 的 switch）

```freemarker
<#switch node.type>
    <#case "Activity">        <@nodeActivityHandler .../>       ← 通用活动（22 个子类型）
    <#case "Branch">          <@branceLogicNodeHandler .../>     ← 分支
    <#case "ForEach">         <@forEachLogicHandler .../>        ← 循环遍历
    <#case "For">             <@foriLogicHandler .../>           ← 计数循环
    <#case "CustomError">     <@errorLogicHandler .../>          ← 自定义错误
    <#case "Break">           break;                             ← 跳出
    <#case "CreateVariable">                                     ← 新建变量
    <#case "ChangeVariable">                                     ← 改变量
    <#case "CreateList">                                         ← 建列表
    <#case "ChangeList">                                         ← 改列表
    <#case "CreateMap">                                          ← 建 Map
    <#case "MapOperation">                                       ← Map 操作
    <#case "PublishBusinessEvent">                               ← 发业务事件
    <#case "ListOperation">                                      ← 列表操作
    <#case "SubMicroFlow">                                       ← 子微流程
    <#case "CallAppService">                                     ← 调 AppService
    <#case "CallDataFlow">                                       ← 调数据流
</#switch>
```

**★★★ 已修正（第 48 篇 LIVE 实测）：`actionType` 的真实取值是驼峰（`CreateEntity`），共 28 个，不是下表列的 19 个。完整清单见 48 篇。**

**★ 前 6 个是「控制流节点」，后 11 个是「数据/调用节点」。**

---

## 三、★★★★★ 19 种 `Activity` 活动模板（`nodeActivityHandler` 的二层分派）

| 模板文件 | 活动类型 | 说明 |
|---|---|---|
| `CreateEntityActivity.java.ftl` | 创建实体 | `service.create(SingleRequest.from(v))` |
| `CreateBatchEntityActivity.java.ftl` | 批量创建 | `createBatch` |
| `ChangeEntityActivity.java.ftl` | 修改实体 | `update` |
| `ChangeBatchEntityActivity.java.ftl` | 批量修改 | `updateBatch` |
| `DeleteEntityActivity.java.ftl` | 删除实体 | `deleteByIds` |
| `RetrieveActivity.java.ftl` | 查询单条/分页 | `selectPageByConditions` |
| `RetrieveArrayActivity.java.ftl` | 查询数组 | |
| `ListOperationActivity.java.ftl` | 列表操作 | ★ 含扣减 SUBTRACT |
| `MapOperationActivity.java.ftl` | Map 操作 | |
| `DataMappingActivity.java.ftl` | 数据映射 | |
| `ConvertDataActivity.java.ftl` | 数据转换 | |
| `CreateVariableActivity.java.ftl` | 建变量 | |
| `ChangeVariableActivity.java.ftl` | 改变量 | |
| `CreateList.java.ftl` | 建列表 | |
| `CreateMapActivity.java.ftl` | 建 Map | |
| `SubMicroFlowActivity.java.ftl` | 子微流程 | |
| `CallAppServiceActivity.java.ftl` | 调 AppService | |
| `ConnectorActivity.java.ftl` | 连接器 | |
| `BusinessEventActivity.java.ftl` | 业务事件 | |

**★★★ `plugin/calldataflow/CallDataFlowActivity*.ftl` —— 生单（CALL_DATA_FLOW）是插件式活动。**

---

## 四、★★★★★ 节点代码的真实产物（两个实例）

### 4.1 `CreateEntityActivity` —— 创建实体

```freemarker
<#if node.mappingType??>
    <#if "attrs" == node.mappingType>
        <#assign objectName = "v" + node.nodeId>
        ${node.structure.id} ${objectName} = new ${node.structure.id}();          ← new DTO
        <@buildActivityStartLog node microflowInfo deployType/>                    ← 开始日志

        <#if (node.attrs![])?size gt 0>
        ${MicroFlowCodeUtil.buildMicroFlowAssignValue2JavaBeanMethodName(node)}(
            ${MicroFlowCodeUtil.buildMicroFlowAssignValue2JavaBeanMethodParamList(
                fullNameTransformer, "", objectName, node.attrs, true)});          ← 逐字段赋值
        </#if>

        <@setCreateEntityActionType objectName node.structure.id node.structure/>  ← 设置操作类型
        <@buildActivityStartLog node microflowInfo deployType/>
        SingleResponse<${node.output.javaType}> resp${node.output.name} =
            ${node.service?replace(".", "")}.create(SingleRequest.from(v${node.nodeId}));   ← ★ 真实调用
        <@dealResp node/>                                                          ← 响应处理
        <@buildActivityEndLog node microflowInfo deployType/>                       ← 结束日志
    <#elseif "value" == node.mappingType>
        ...整体赋值分支...
```

**★★★★★ 生成的 Java 代码形如：**
```java
DemoOrderDto v123 = new DemoOrderDto();
UdcAppLogHelper.buildActivityStartLog(...);
setValueToJavaBean_v123("orderNo", ..., v123, ...);
setCreateEntityActionType(v123, "DemoOrderDto", structure);
UdcAppLogHelper.buildActivityStartLog(...);
SingleResponse<DemoOrderDto> respOut = demoOrderAppService.create(SingleRequest.from(v123));
if (!respOut.success()) { ... }
UdcAppLogHelper.buildActivityEndLog(...);
```

### 4.2 `RetrieveActivity` —— 查询

```freemarker
<#if node.fetchType == "CONDITION">
    pageInfo = new PageInfo();
    pageInfo.setPageSize(1);
    UdcAppLogHelper.buildActivityStartLog(...);
    <#assign isDynamicSelect = MicroFlowCodeUtil.isDynamicSelect(node.inApp, node.methodLegal!{}) />
    <@conditionDeal node isDynamicSelect />
    <@sortOrderList node/>
    <#if isDynamicSelect>
        ...dynamicJoinSelect（跨应用动态联查）...
    <#else>
        PageResponse<${node.structure.id}> resp${node.output.name} =
            ${node.service?replace(".", "")}.selectPageByConditions(
                PageRequest.from(pageInfo, selectMap, sort));        ← ★ 条件用 Map
    </#if>
    if (!resp.success()) { log.info(...); }
```

### ★★★★★ 三条关键事实

| # | 事实 |
|---|---|
| 1 | **查询节点复用 `selectPageByConditions`（Map DSL）** —— 与手写代码同一套 API |
| 2 | **跨应用查询走 `dynamicJoinSelect`**（`isDynamicSelect` 判定） |
| 3 | **每个节点都有 `buildActivityStartLog` / `buildActivityEndLog`**（可观测性内建） |

---

## 五、★★★★★ `MicroFlowDomainService.java.ftl` 的 12 个宏

```freemarker
buildMfService                           ← 服务主壳
buildFormulaPrivateMethod                ← 表达式私有方法
buildFilterListOperationFormulaMethod    ← 过滤列表操作表达式
buildConditionPrivateMethod              ← 条件私有方法
nodesLogicHandler                        ← ★ 节点分派器（17 种）
nodeActivityHandler                       ← ★ 活动分派器（19 种）
foriLogicHandler                         ← For 循环
forEachLogicHandler                      ← ForEach 循环
errorLogicHandler                         ← 自定义错误
buildErrorInfo                            ← 错误信息构建
branceLogicNodeHandler                    ← 分支
validateInputParamAttrRequired            ← 入参必填校验
```

### ★★★★ 生成的类结构

```java
public class ${className?cap_first}Service {
    // 表达式私有方法（buildFormulaPrivateMethod 生成）
    // 条件私有方法（buildConditionPrivateMethod 生成）
    // 入参必填校验（validateInputParamAttrRequired）
    public XxxResponse execute(XxxRequest request) {
        // nodesLogicHandler 展开所有节点
    }
}
```

---

## 六、★★★★ 微流程的支撑体系（`microflow/` 的 6 个子目录）

### 6.1 `customflow/` —— 自定义微流程（7 个模板）

```
CustomMicroFlowAppService.java.ftl          ← AppService 接口
CustomMicroFlowController.java.ftl          ← Controller
CustomMicroFlowService.java.ftl             ← Service
DefaultCustomMicroFlowAppServiceImpl.java.ftl
DefaultCustomMicroFlowBeanDefinitionRegistryPostProcessor.java.ftl   ← ★ Bean 注册后处理
DefaultCustomMicroFlowConfig.java.ftl
MicroFlowDubboExportBeanPostProcessor.java.ftl                       ← ★ Dubbo 导出
```

**★★★★★ 这是「自定义微流程」的关键：**
**⇒ 自定义微流程 = 开发者写 Java 实现，通过 `BeanDefinitionRegistryPostProcessor` 注册成 Bean。**
**⇒ 可以通过 `MicroFlowDubboExportBeanPostProcessor` **导出为 Dubbo 服务**。**

### 6.2 `event/` —— 事件监听（2 个）

```
BusinessEventListener.java.ftl
ConnectorBusinessEventListener.java.ftl
```

### 6.3 `schedule/` —— 定时调度

```
MicroFlowSchedule.java.ftl        ← 微流程可以作为定时任务
```

### 6.4 `web/` —— Web 暴露（5 个）

```
MicroFlowAppService.java.ftl
MicroFlowAppServiceImpl.java.ftl
MicroFlowController.java.ftl
CustomRestApiMicroFlowController.java.ftl     ← ★ 自定义 REST API
host/HostAppMicroFlowAppServiceImpl.java.ftl  ← 宿主应用
host/HostAppMicroFlowController.java.ftl
util/GraphQLControllerUtil.java.ftl            ← ★ GraphQL
```

**★★★ 微流程可暴露为 REST API，甚至 GraphQL。**

### 6.5 `common/` —— 8 个工具（代码生成用）

```
CallMethodUtil.java.ftl          调用方法
CommonUtil.java.ftl
GenericInvokeUtil.java.ftl       ★ 泛化调用
ListActivityUtil.java.ftl
LogUtil.java.ftl
MapUtil.java.ftl
SetActionTypeUtil.java.ftl
ValueUtil.java.ftl
```

**★ `GenericInvokeUtil` = 泛化调用工具（对应 Dubbo 泛化）。**

### 6.6 `plugin/calldataflow/` —— 生单插件（3 个）

```
CallDataFlowActivity.java.ftl
CallDataFlowActivityDI.ftl         ★ DI = 依赖注入配置
CallDataFlowActivityImport.ftl
```

**⇒ 生单规则（CALL_DATA_FLOW）是**插件式活动**，有独立的 DI 和 Import 模板。**

---

## 七、★★★★★ 微流程 vs 实体的代码生成对比

| 维度 | 实体代码生成 | 微流程代码生成 |
|---|---|---|
| 模板入口 | `entity/entity.java.ftl` 等 141 个 | `microflow/MicroFlowDomainService.java.ftl` 1 个主引擎 |
| 产物 | 每实体 10+ 个类 | 每微流程 1 个 Service + 可选 Controller |
| 节点机制 | 无（固定结构） | **17 种节点类型 + 19 种活动，模板分派** |
| 表达式 | `resolveDefaultValueExpression` | `buildFormulaPrivateMethod` 生成私有方法 |
| 可观测性 | 无内建 | **每节点自动 startLog/endLog** |
| 扩展点 | `joinSnippets` / `paster` | `plugin/` 目录（插件式活动） |

---

## 八、★★★★★ 对开发者的关键结论

| # | 结论 |
|---|---|
| 1 | **微流程是编译型，不是解释型** —— 生成的 Java 代码里能直接看到每个节点 |
| 2 | **微流程复用与手写代码同一套 AppService API**（`create`/`selectPageByConditions`/`updateBatch`） |
| 3 | **每个节点自动埋日志**（`buildActivityStartLog`/`EndLog`），这是平台可观测性的基础 |
| 4 | **跨应用查询自动走 `dynamicJoinSelect`**（勿在跨应用微流程里手写查询） |
| 5 | **自定义微流程走 Bean 注册**（`BeanDefinitionRegistryPostProcessor`），不是模板生成 |
| 6 | **自定义微流程可导出为 Dubbo 服务** |
| 7 | **微流程可暴露为 REST / GraphQL** |
| 8 | **生单（CALL_DATA_FLOW）是插件式活动**，有独立模板组 |
| 9 | **节点粒度是可变性边界**：想改行为改节点配置，改结构要重新生成代码 |

---

## 九、待验证

| 问题 | 状态 |
|---|---|
| `node.isShouldGenerateCode()` 的判定规则 | 待反编译（哪些节点不生成代码） |
| `MicroFlowCodeUtil` 的完整方法集 | 待反编译（模板重度依赖） |
| `dynamicJoinSelect` 的实现 | UNVERIFIED |
| `execute()` 方法签名（入参/出参结构） | 待渲染确认 |
| `microflow/common/*.ftl` 8 个工具的具体职责 | 待逐个读 |
| `customflow` 的 Bean 注册机制 | 待反编译 |