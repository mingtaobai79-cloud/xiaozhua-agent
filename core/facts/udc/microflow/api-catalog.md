# 微流程接口总清单（udc GraphQL）

全部 POST `/service/udc/graphql`，query string 带 operation 名（可 `&` 合并批量）。
命名规律：`udcMicroflow + 动词 + 对象 + Post/Get`；元数据类 `udcMetaDataSelect*`；通用 `appCommon*`。
凭证/来源：用户贴 body + CDP 抓包（fetch recorder + performance resource entries）。

## 一、选择类（节点下拉加载数据）

| 接口 | 触发操作 | 入参 | 返回关键字段 |
|---|---|---|---|
| udcMicroflowSearchAppsPost | 选应用 | appId, needBootStarter, needConnectorApp, needDependency | appId,name,caption,fullName,inApp,id,udcApp,appType,dynamicDependency |
| udcMicroflowSearchTreeEntityPost | 选实体(树形) | appId,appName,needChildren,needThirdEntity,serviceType | caption,fullName,dtoFullName,dtoType,udcApp,relationEntity,customs{entityCategory},methodLegal{available,complexCondition,seniorMethod,serviceType,interfaceClassFullName},children[递归] |
| udcMicroflowTreeEntityDtoPost | 选实体(树形DTO) | (同实体树) | 实体树 DTO |
| udcMetaDataSelectEntityByAppIdAppGet | 元数据选实体 | appId | 实体列表 |
| udcMicroflowFindCustomDtoPost | 选自定义对象/DTO | appId,appName,dtoFullName,needChildren | attributes,caption,fullName,type,relationEntityId,methodLegals,dtoType,udcApp,refApp,entity |
| udcMicroflowFindDtoByEntityPost | 实体→DTO | appId,appName,entityFullName | caption,entity,fullName,dtoType,udcApp,attributes,type |
| udcMicroflowSearchAppServiceByAppNamePost | 选服务 | appId,appName,needDynamicConnector | caption,fullName,description,methods{caption,description,dubbo,fullName,group,implClass,interfaceClass,appType} |
| udcMicroflowSearchMethodByNamePost | 选方法(加载出入参) | appId,appName,dtoFullName,methodFullName | caption,dubbo,dubboVersion,fullName,group,implClass,interfaceClass,md5,parameter/returnValue{type,item{enums,itemType,item{javaType,dataType,keyType}}} |
| udcMicroflowServiceListSubMfPost | 选子微流程 | appId | 子微流程列表(分组) |
| udcDataFlowListManuallyMappingPost | 选生单规则 | appId,sourceEntityId | appId,appUrl,caption,id,name,sourceEntityId |
| udcMicroFlowGroupSelectByTypePost | 分组选择 | (type) | 分组列表 |
| udcMicroflowSearchEnumByAppNamePost | 选选项集(枚举) | appId,appName | caption,customs,description,enums,fullName,id,md5 |
| udcMetaDataSelectJavaEnumItemPost | 选枚举项(选项值) | id(枚举id) | id,name,code,enumId,caption,fullName,enable |
| udcMicroflowSearchEventListPost | 选事件(应用内同步) | appId,appName | fullName,caption,source,dtoType,udcApp |
| udcMicroflowSearchSendMqListPost | 选事件(应用间异步/MQ) | appId,appName | fullName,md5,sort,caption,description,topic,contentDto{type},customs |
| udcDataTransferObjectSearchListPost | 数据转换对象搜索 | (appId,appName) | 转换对象列表 |
| udcEntityAssociationEntityAppGet | 实体关联实体 | (entityId) | 关联实体列表 |

## 二、校验 / 读写

| 接口 | 触发 | 说明 |
|---|---|---|
| udcMicroflowCheckSchemaUpdatePost | 保存前检查 | body 需 guid/publishState/groupType/openApi/versionCode 等；返回 content{check,errors,errorMessage[]} |
| udcConditionCheckPost | 条件校验 | params0=[条件组数组]；返回 content |
| udcMicroflowFindByIdGet | 读微流程详情 | 返回 dataSchema/节点 |
| udcMicroflowDisableNodePost | 禁用节点 | — |
| udcMultiEditLockPost | 编辑锁 | 多端编辑锁 |

## 三、表达式 / 通用

| 接口 | 触发 | 说明 |
|---|---|---|
| udcExpressionSchemaPost | 表达式编辑器 | 表达式可选范围(系统变量/函数) |
| appCommonIconNameListPost | 节点图标 | 图标名列表 |
| GET /service/app-common/expression/system/values/date | 表达式日期变量 | 日期系统变量值 |

## 四、关键链路（按节点）

- 自定义服务：选应用→选服务(SearchAppServiceByAppName)→选方法(SearchMethodByName 拿出入参+md5)→加载 DTO(FindCustomDto 拿 attributes)→填参→条件校验(udcConditionCheck)。
- 执行生单规则：选实体(MetaDataSelectEntityByAppIdAppGet)→实体→DTO(FindDtoByEntity)→选规则(DataFlowListManuallyMapping 按 sourceEntityId)。
- 事件投递：应用内→SearchEventListPost；应用间→SearchSendMqListPost(MQ 消息)。
- 选项集：选枚举(SearchEnumByAppName)→选枚举项(MetaDataSelectJavaEnumItemPost)。
- 查询条件：选实体(SearchTreeEntity 含 methodLegal 查询能力)→填条件→udcConditionCheckPost 校验。

## 五、机制（贯穿所有）

选什么 → 后端返回什么定义(字段/出入参/能力 md5) → 前端按定义渲染。生成器必须按链路顺序，
先走接口拿真实定义，再填下游字段，不能凭空写。

## 六、保存/更新核心接口（补：完整 body）

### udcMicroflowUpdatePost（保存/更新微流程，核心写接口）

body 与 checkSchema 几乎一致，但 **state 用 "DRAFT"**（草稿），checkSchema 用 "RELEASE"：

```json
{"query":"mutation graphqlLoader ($params0: udcMicroflowUpdatePostInputBody) {
  data0: udcMicroflowUpdatePost(body: $params0) { code data { content } message status } }",
 "variables":{"params0":{
   "appId":"9000000000000000001","businessEventCaption":"-",
   "caption":"最小编排验证-v1","description":"模板拼装验证",
   "guid":"-2841894774839228897","id":"-5386647105876167671",
   "name":"minV1","publishState":"UNPUBLISH","scheduleCaption":"-","sourceId":null,
   "type":"SERVICE","state":"DRAFT","triggerType":"MANUAL","groupType":"DEFAULT",
   "versionCode":0,"creationMethod":"MANUAL","serviceInterface":"CustomMicroFlowAppService",
   "openApi":"STOP","microFlowGroupId":"0","restApi":"DISABLED","restPath":"",
   "lastVersionMetadataState":"DISABLED","lastEnableTime":null,"lastEnableVersion":null,
   "sourceType":"PAGE","dataSchema":"<完整 dataSchema 字符串>"}}}
```

### udcMicroflowSearch（搜微流程列表，分页）

```json
{"pageInfo":{"needTotal":true,"pageNumber":1,"pageSize":999,"pages":0,"total":0},
 "params":{"appId":"9000000000000000001","IN_type":["SERVICE","CUSTOM"]},
 "sort":{"orders":[{"direction":"ASC","property":"caption"}]}}
```
返回 pageInfo{needTotal,pageNumber,pageSize,pages,total} + content{id,name,appId,versionCode,caption,type,triggerType,groupType,description,orderNum,state,publishState,createTime,updateTime,microFlowGroupId,creationMethod}

### udcMicroflowFindByIdGet（读详情，注意是 path 不是 body）

```json
{"query":"query graphqlLoader ($params0: udcMicroflowFindByIdGetInputPath) {
  data0: udcMicroflowFindByIdGet(path: $params0) { code data { content{...} } message status } }",
 "variables":{"params0":{"id":"-5386647105876167671"}}}
```
返回 content 含 **jsonSchema + dataSchema**（完整节点结构）+ name/state/publishState/type/triggerType/groupType/versionCode/serviceInterface/openApi/microFlowGroupId/restApi 等。

### udcMicroflowDisableNodePost（禁用节点）

```json
{"params0":{"appId":"9000000000000000001","nodeGroupEnum":"MICROFLOW"}}
```
返回 content{actionType}。

### udcMicroFlowGroupSelectByTypePost（分组选择，type 维度）

```json
{"params0":{"appId":"9000000000000000001","type":"BACKEND_SERVICE"}}
```
返回 content{appId,caption,guid,id,orderNo,preset,publishState,creationMethod}。

## 七、节点「确定保存」链路（用户口述）

每个节点点确定保存时：**校验通过 → udcMicroflowUpdatePost 保存 → 重新加载数据**。
重新加载会连发这几个接口：

1. udcMicroflowDisableNodePost（nodeGroupEnum=MICROFLOW，清理旧节点）
2. udcMicroflowFindCustomDtoPost ×N（重新加载相关 DTO，如入参 DTO/实体 DTO 的 attributes）
3. udcMicroflowFindByIdGet（重新读微流程 dataSchema）
4. udcMicroflowSearch（重新搜微流程列表，刷新左侧树）

所以「保存节点」不是单接口，是 UpdatePost + 一串重载接口的批量请求
（GraphQL 多 operation `&` 合并，如 `?udcMicroflowDisableNodePost&udcMicroflowFindCustomDtoPost&...`）。
生成器保存节点后必须用 FindByIdGet 读回 dataSchema 验证，而不是只看 UpdatePost 的返回。
