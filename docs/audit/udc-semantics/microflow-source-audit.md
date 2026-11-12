# UDC 微流程解析、节点和页面规则源码审计

日期：2026-10-11
主线：`<XIAOZHUA_AGENT_ROOT>`
平台源码：`<PATH>
运行包补充：`<HERMES_HOME>/cache/scratch/md561/udc-biz-5.3.517.jar`，sha256 `8a1cda618cdc23d18d02e39f4f93d6fad4ff732c987fd47bbb28118dbf66ef25`
说明：源码树是静态版本证据，不能直接宣称当前 test2 行为；jar 模板是 5.3.517 静态证据。

## 1. dataSchema 是如何进入解析器

`MicroFlowParserUtils.parseToJsonNode` 先把字符串 JSON 转成 Jackson `JsonNode`，见：

```text
udc/udc-biz/src/main/java/com/seeyon/udc/microflow/util/MicroFlowParserUtils.java:84-110
```

然后 `parseNodes` 读取根 `nodes` 数组，逐个计算 `nodePath`，调用 `node(ObjectNode, ...)`，见 `322-355`。

节点类型先用 `MicroFlowNodeTypeEnum` 校验：

```text
CONDITION / FOR_EACH / BRANCH / CUSTOM_ERROR / END /
ACTIVITY / FOR / BREAK
```

见：

```text
udc/udc-biz/src/main/java/com/seeyon/udc/enums/microflow/MicroFlowNodeTypeEnum.java:17-50
```

`node()` 对容器节点递归解析：

- `CONDITION` → expression + 子 nodes。
- `BRANCH` → conditions + 每个 condition 的 nodes。
- `FOR_EACH` → selectParam + nodes。
- `FOR` → forStart/forEnd/operator/forStep/errorMsg + nodes。
- `CUSTOM_ERROR` → error。
- 其它默认作为 Activity 交给 Activity parser。

见 `MicroFlowParserUtils.java:371-428`、`435-462`。

所有节点最后由 `buildBaseNode` 补充 type、caption、description、nodeId 和 output；见 `468-485`。这说明节点 JSON 不是任意 key 集合，缺少 `type/caption/nodeId/output` 等字段会进入解析错误或节点语义不完整。

## 2. Activity 节点类型和语义分组

`ActivityNodeTypeEnum` 是后端活动节点的受控值域，见：

```text
udc/udc-biz/src/main/java/com/seeyon/udc/enums/microflow/ActivityNodeTypeEnum.java:17-131
```

### 数据活动

`isDataActivity()` 明确把以下类型分成数据活动：

```text
RETRIEVE
RETRIEVE_ARRAY
CREATE_ENTITY
CREATE_BATCH_ENTITY
CHANGE_ENTITY
CHANGE_BATCH_ENTITY
DELETE_ENTITY
```

见 `167-180`。

它们的语义是：

- `RETRIEVE` / `RETRIEVE_ARRAY`：按条件或 id 读取实体。
- `CREATE_ENTITY` / `CREATE_BATCH_ENTITY`：生单/创建实体记录。
- `CHANGE_ENTITY` / `CHANGE_BATCH_ENTITY`：修改实体记录。
- `DELETE_ENTITY`：删除实体记录。

这类节点直接改变或查询业务数据，必须有实体 DTO、字段/条件、输入输出和运行回读，不能用普通变量节点假装。

### 基础服务活动

`isBaseService()` 明确把以下类型分成基础服务：

```text
CALL_APP_SERVICE
PUBLISH_BUSINESS_EVENT
CONNECTOR
SUB_MICROFLOW
CALL_DATA_FLOW
```

见 `190-202`。

这说明：

- `CALL_DATA_FLOW` 是生单规则调用节点；模板已证实调用实体 `DataFlowRuntimeService` 并包装 `CallDataFlowResultDto`。它直接调用 Deduction 的结论没有证据。
- `PUBLISH_BUSINESS_EVENT` 是发布业务事件，不是事件监听动作本身。
- `SUB_MICROFLOW` 是子微流程调用。
- `CALL_APP_SERVICE` 是应用服务调用。
- `CONNECTOR` 是连接器调用。

### 变量/集合/转换活动

```text
CREATE_VARIABLE
CHANGE_VARIABLE
CREATE_LIST
CHANGE_LIST
LIST_OPERATION
CREATE_MAP
MAP_OPERATION
DATA_MAPPING
CONVERT_DATA
```

它们主要处理微流程上下文、列表、映射和数据转换，不等于实体持久化。

### 2.1 Activity 输入/输出矩阵（静态 parser 证据）

下面的“输入”是 Activity 类中由 `parseActivityNode` 读取/组装的字段；“输出”首先指节点 `output`/`NodeInfo` 变量槽位，不等同于已经验证的运行态返回值。类字段和方法位置来自旧源码树，模板路径另按 5.3.517 jar 单独标注。

| Activity | 前后端归属 | 主要输入结构 | 静态输出/作用 | 证据 |
|---|---|---|---|---|
| `RETRIEVE` | 后端数据活动 | `condition`, `sortParams`, `fetchType`, `nullHandling`, `value`, `mappingType` | 单实体/DTO 输出，要求 output/作用域 | `RetrieveEntityActivity.java:88-127` |
| `RETRIEVE_ARRAY` | 后端数据活动 | `pageSearch`, `pageInfo`, `size`, `condition`, `sortParams`, `fetchType`, 聚合字段 | 数组/分页结果输出 | `RetrieveEntityArrayActivity.java:95-146` |
| `CREATE_ENTITY` | 后端数据活动 | `mappingType`, `attrs`, `value` | 新实体结果/输出变量 | `CreateEntityActivity.java:68-87` |
| `CREATE_BATCH_ENTITY` | 后端数据活动 | 继承实体选择/结构输入，`isUdcApp` | 批量创建结果 | `CreateBatchEntityActivity.java:48-62` |
| `CHANGE_ENTITY` | 后端数据活动 | `attrs`, 实体选择/目标上下文，`isUdcApp` | 修改后的实体/输出变量 | `ChangeEntityActivity.java:57-72` |
| `CHANGE_BATCH_ENTITY` | 后端数据活动 | 批量目标/实体选择，`isUdcApp` | 批量修改结果 | `ChangeBatchEntityActivity.java:48-61` |
| `DELETE_ENTITY` | 后端数据活动 | `selectParam`, `condition`, `deleteType`, `value` | 删除副作用；通常无业务对象输出 | `DeleteEntityActivity.java:78-101` |
| `CREATE_VARIABLE` | 后端变量活动 | `paramType`, `javaType`, `attrs`, `value`, `selectParam`, metadata/sort | 创建变量并注册 output | `CreateVariableActivity.java:122-255` |
| `CHANGE_VARIABLE` | 后端变量活动 | `selectParam`, `selectMappingParam`, `attrs`, `value`, `mappingType` | 修改变量 | `ChangeVariableActivity.java:92-138` |
| `CREATE_LIST` | 后端集合活动 | `values` | 新列表变量 | `CreateListActivity.java:52-90` |
| `CHANGE_LIST` | 后端集合活动 | `action`, `dataSource`, `selectParam`, `countAttrs` | 列表修改/统计结果 | `ChangeListActivity.java:69-97` |
| `LIST_OPERATION` | 后端集合活动 | `selectParam`, `operationType`, group/count/sort/index/expression | 列表操作结果 | `ListOperationActivity.java:136-251` |
| `CREATE_MAP` | 后端映射活动 | `entries` | 新 Map 变量 | `CreateMapActivity.java:24-47` |
| `MAP_OPERATION` | 后端映射活动 | `selectMap`, `operationType`, `entries`, key/remove/null 策略 | Map 操作结果 | `MapOperationActivity.java:47-180` |
| `DATA_MAPPING` | 后端映射活动 | `dataSource`, `targetType`, `mappingRule` | 映射到目标对象/变量 | `DataMappingActivity.java:126-192` |
| `CONVERT_DATA` | 后端转换活动 | `selectParam`, `convertType`, `regex` | 类型转换结果 | `ConvertDataActivity.java:86-163` |
| `CALL_APP_SERVICE` | 后端基础服务 | `inApp`, `selectMethod`, `callMethodParam`, `callMethod`, `app` | 应用服务调用结果 | `CallAppServiceActivity.java:109-196` |
| `CALL_DATA_FLOW` | 后端基础服务 | `dataFlowMappingId`, `structure`, `dataSourceType`, `selectParam`, `condition` | DataFlow/生单规则调用结果 | `CallDataFlowActivity.java:86-111`；`MicroFlowTemplateConfig.java:11-19` |
| `SUB_MICROFLOW` | 后端基础服务 | `mfService`, `value`, `mappingType`, `attrs`, `pageInfo`, call 参数 | 子微流程调用结果 | `SubMicroflowActivity.java:84-140` |
| `CONNECTOR` | 后端基础服务 | `selectMethod`, `callMethodParam` | Connector 调用结果 | `ConnectorActivity.java:75-119` |
| `PUBLISH_BUSINESS_EVENT` | 后端事件活动 | `eventType`, `selectEvent`, app/MQ、`messageType`, `executeTime`, `attrs`, `eventId` | 发布事件副作用 | `BusinessEventActivity.java:112-205` |
| `ATTRIBUTE_REQUIRED` | 实体规则活动 | `params`, `follow`, `value` | 必填规则检测/错误结果 | `AttributeRequiredActivity.java:47-63` |
| `ATTRIBUTE_UNIQUE` | 实体规则活动 | `params`, `follow`, `value`, prerequisites | 唯一性规则检测/错误结果 | `AttributeUniqueActivity.java:61-73` |
| `ASSIGN_VALUE` | 实体规则活动 | rule `param`, `value` | 规则赋值副作用 | `AssignValueActivity.java:47-57` |
| `DEFAULT_VALUE` | 实体规则活动 | `entityAttrs` | 默认值规则赋值 | `DefaultValueActivity.java:46-56` |
| `SHOW_MESSAGE` | 规则/前端反馈活动 | rule `param`, `value`, `level`, `follow` | 消息反馈副作用 | `ShowMessageActivity.java:53-66` |
| `CALL_DATA_FLOW_FRONT` | 前端节点候选 | 枚举存在，但旧源码树未找到同名 Activity parser | 不能据此推后端生成 | `ActivityNodeTypeEnum.java:128-131` |

`ActivityNodeTypeEnum` 还列有 `ATTRIBUTE_REQUIRED`、`ASSIGN_VALUE`、`SHOW_MESSAGE`、`ATTRIBUTE_UNIQUE`、`DEFAULT_VALUE` 等规则活动；它们不能被简化成普通数据活动。`CALL_MICRO_FLOW` 在枚举中存在，但本源码树没有同名 `CallMicroFlowActivity.java`，实际后端子流程类是 `SubMicroflowActivity`；这是版本/命名差异，不能凭枚举名生成类。

以上是静态输入结构和 parser 入口矩阵，不是 test2 运行 PASS。每类要成为可交付节点，还必须追加：schema check 结果、发布态、模板映射、生成类和运行回读。

`ConvertDataActivity` 的真实合法转换值域，见：

```text
udc/udc-biz/src/main/java/com/seeyon/udc/microflow/domain/bo/flow/activity/ConvertDataActivity.java:35-50
```

包括：

```text
MultiAssociation2List
CtpEnumMultiAssociation2List
String2Integer
String2Decimal
String2Long
BasicData2String
List2multiAssociation
CtpEnumList2multiAssociation
GetEnumCode
GetEnumName
Split
```

解析和校验见 `86-125`；运行时类型推导见 `130-198`。因此“多选人员转列表”不是随便写 `ToList`：平台受控值是 `MultiAssociation2List`，且要满足 `selectParam` 是多选关联实体。前面临时脚本写 `ToList` 没有平台源码证据，应判为错误/未验证。

## 3. 微流程解析器和页面规则检查边界

`MicroFlowFrontEndService` 是前端微流程/页面规则检测服务，见：

```text
udc/udc-biz/src/main/java/com/seeyon/udc/microflow/domain/service/MicroFlowFrontEndService.java:108-159
```

它会区分：

- 普通页面 `sourceType` 为空或 `PAGE`：从 pageSchema/pageInfo 取页面上下文。
- 页面外框 `sourceType=PAGE_FRAME`：从 pageLayout schema 取外框上下文。

见 `159-211`。

它不是通用后端 Activity 解析器，而是把页面规则/前端微流程节点放回页面上下文中检查：

- 页面元素是否存在。
- selectParam 是否仍引用页面上的控件/数据源。
- 输出变量作用域是否存在。
- 数据源字段是否被隐藏或删除。
- 事件参数、布局事件和页面入参是否匹配。

节点递归检查见 `225-270`；输出变量见 `282-318`；页面 selectParam 和作用域检查见 `322-421`。

`PageRuleNodeUtil` 只负责从页面规则节点里提取微流程 id / dataflow id：

```text
udc/udc-biz/src/main/java/com/seeyon/udc/microflow/util/PageRuleNodeUtil.java:17-55
```

所以页面规则链是：

```text
页面事件/规则
  → FRONTEND 微流程 schema
  → MicroFlowFrontEndService 页面上下文检测
  → 节点中调用 microflow/dataflow
```

它不是 `udc_filter_plan` 查询方案，也不是普通 SERVICE 微流程。

## 4. 服务、事件监听、定时和页面规则的差异

前端创建类型映射已在 5.3.517 前端 bundle 发现：

```text
servicedefinition       → type=SERVICE, triggerType=MANUAL
customServicedefinition → type=CUSTOM, triggerType=MANUAL
eventmonitor            → type=SERVICE, triggerType=BUSINESS_EVENT
timingtask              → type=SERVICE, triggerType=SCHEDULE
frontend                → type=FRONTEND, triggerType=MANUAL
frontendparam           → type=FRONTEND_PARAM
frontendfunction        → type=FUNCTION, triggerType=MANUAL
entityrule              → type=ENTITYRULE, triggerType=MANUAL
customEventmonitor      → type=CUSTOM, triggerType=BUSINESS_EVENT
customTimingtask        → type=CUSTOM, triggerType=SCHEDULE
```

这些是前端创建模型的静态证据，当前版本来源是 `src_redux_store_ts.14dc061e.js` 中微流程创建类型映射模块；尚未形成主线仓库的可执行 parser。

后端服务通过 `MicroFlowService` 将数据库实体定义转成 `MicroFlowBo`。旧源码关键点：

```text
udc/udc-biz/src/main/java/com/seeyon/udc/microflow/domain/service/MicroFlowService.java:267-338
```

其中：

- `buildMicroFlowBo` / `getMicroFlowBo` 读取 dataSchema 并走 `MicroFlowParser.readWithInfo`。
- `buildMicroFlowBoWithoutNodes` 用于只读元信息。
- `getMicroFlowDefinition` 有老数据兼容：dataSchema 为空时回退 jsonSchema，见 `345-364`。

### 事件监听

事件监听的动作链不是把 action 写进 `udc_event`：

```text
事件定义/事件数据
  → 监听微流程 trigger=BUSINESS_EVENT
  → messageInfo / eventDataFullName / topic
  → BusinessEventListener 模板/运行订阅
```

5.3.517 jar 中有：

```text
autocode/JAVA/2.7/templates/microflow/BusinessEventActivity.java.ftl
autocode/JAVA/2.7/templates/microflow/event/BusinessEventListener.java.ftl
```

### 定时任务

定时任务由 `triggerType=SCHEDULE` 和 scheduleRule 组成，5.3.517 jar 有：

```text
autocode/JAVA/2.7/templates/microflow/schedule/MicroFlowSchedule.java.ftl
```

`MicroFlowParserUtils.clearScheduleRule` 会直接处理 trigger.scheduleRule 的 jobCaption/jobCode/id，见 `495-506`；说明 scheduleRule 是 dataSchema 的独立触发器配置，不是节点内容。

### 页面规则

页面规则是 `type=FRONTEND`，其 nodes 的检查依赖 pageSchema/pageInfo/pageLayout；不能用 SERVICE 微流程模板或普通 `udc_filter_plan` 替代。

## 5. checkSchema 的真实入口与边界

旧源码中的 Controller 入口是：

```text
udc/udc-web/src/main/java/com/seeyon/udc/controller/MicroFlowController.java:87-103
```

对应路径（类级前缀需从同一 Controller 的类级注解拼接）为：

```text
POST .../microflow/checkSchema
POST .../microflow/checkSchema/update
POST .../microflow/create
POST .../microflow/update
```

`checkSchema` 和 `checkSchema/update` 都接收 `MicroFlowDefinitionDto`；普通 `create/update` 在 Controller 注释中明确为“强制草稿态”。这证明校验、更新、草稿创建是不同动作，不能把 checkSchema 返回成功当成发布。

`MicroFlowService.checkSchema` 直接调用：

```text
MicroFlowService.java:571-576
MicroFlowParser.readWithInfo(determiner, buildApplicationDtoSupplier(microFlow))
```

`getMicroFlowBo` 的解析链是：

```text
MicroFlowService.java:267-338
  → getMicroFlowBo
  → MicroFlowParser.readWithInfo
  → buildMicroFlowBo
  → messages 为空才返回 MicroFlowBo，否则抛 schema parse error
```

页面规则的额外检查由 `MicroFlowFrontEndService` 完成，节点递归入口见：

```text
MicroFlowFrontEndService.java:200-216
MicroFlowFrontEndService.java:225-270
```

它还会针对 `FRONTEND` 类型检查 page/pageLayout 上的控件、selectParam、页面出入参和作用域；这不是所有 SERVICE 微流程都会执行的同一检查。

从平台源码可以确认：

- schema 先 parse 成 Jackson tree。
- 节点 type/actionType、必填字段、selectParam、output、表达式和页面作用域被检查。
- `MicroFlowFrontEndService.detection` 检查页面规则引用的页面控件/外框上下文。

但 `checkSchema` 通过只说明 schema 结构/检测规则通过，不能证明：

- 微流程已发布到 state=20。
- 构建器已经生成对应 Service.class。
- sandbox pipeline 成功。
- 运行态路由可调用。
- 业务数据、流程日志、意见列表返回正确。

这些必须单独回读：数据库微流程状态、deploy_record、jar class、运行接口和业务数据。

## 6. 生单与扣减边界

专门逐行报告和机器清单：`flow-excel-source-audit.md`、`flow-excel-contracts.json`。

`CALL_DATA_FLOW` 被 `ActivityNodeTypeEnum.isBaseService` 归为基础服务，但分类本身不证明它调用扣减。直接生成模板证据是：

```text
CallDataFlowActivity
 → DataFlowExecuteParamDto
 → <SourceEntity>DataFlowRuntimeService.<mappingMethod>
 → DataFlowResultDto
 → CallDataFlowResultDto(targetIds, updateIds)
```

旧源码 `CallDataFlowActivity.java:86-123` 要求映射 id、structure.entityId、来源数据/条件和 output，并在全局检测中检查映射存在。模板在本地 reference jar 的 `JAVA/2.9` 子目录已核验；源码及 jar 证据身份分开保留。

生单图、映射、ruleInfo 与 deduction 图/规则/算法/状态明细是不同对象。扣减由独立模板生成 BeforeCreate、BeforeUpdate、BeforeDelete 的同步监听器，使用 DeductionUpdateParamDto 执行 DO/UNDO 并更新来源 deductionInfo。

```text
微流程 CALL_DATA_FLOW → 生单规则 → 创建/更新目标数据
CREATE_ENTITY/CREATE_BATCH_ENTITY → 实体记录创建
CHANGE_ENTITY/CHANGE_BATCH_ENTITY → 实体修改
DeductionRule + Algorithm + Detail → 同步生命周期监听器 → DO/UNDO
```

只有当另有证据证明生单创建/修改触发了某条扣减监听器，才能建立两者间的具体运行联动。当前目标应用没有该运行回读证据，不画默认的 DataFlow→Deduction 直接调用边。

主线 graph validator、目标应用生成类/运行态数据、扣减事务/并发回读仍未实现或未验证。静态机制矩阵已补齐，不能称 live 生单/扣减通过。

## 7. 5.3.517 模板证据

从 `udc-biz-5.3.517.jar` 静态索引确认：

- jar sha256：`8a1cda618cdc23d18d02e39f4f93d6fad4ff732c987fd47bbb28118dbf66ef25`
- 微流程模板共 147 个文件。
- 核心 Activity/触发器相关模板 45 个，包含 Retrieve、ConvertData、Create/Change/Delete、CallAppService、SubMicroFlow、CallDataFlow、BusinessEventListener、MicroFlowSchedule 等。

这证明模板存在，不证明当前 test2 某个微流程已经用上模板；生成物检查仍是必要条件。

## 8. 当前 xiaozhua-agent 缺口

主线仓库现在没有：

1. `ActivityNodeTypeEnum`/`MicroFlowNodeTypeEnum` 对应的 Python 版本化枚举模型。
2. `dataSchema` JSON parser 和容器节点递归 graph model。
3. 节点输入输出/作用域/selectParam 页面引用 validator。
4. ActivityType → 5.3.517 模板清单的映射层。
5. SERVICE / BUSINESS_EVENT / SCHEDULE / FRONTEND / ENTITYRULE 分型 planner。
6. DataFlow/Deduction 独立 graph/model/validator。
7. state=20、deploy_record、生成 jar、运行态业务回读的验收器。

因此此前临时拼出的“订单人员查询”不能称为完整微流程；最多是 API schema 探针。
