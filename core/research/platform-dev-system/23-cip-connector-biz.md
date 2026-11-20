# CIP 连接器实现层（cip-connector-biz 5.3.286，1,205 类）

> 数据源：`D:/repo/CHIT-extra/cip-connector-biz/5.3.286/cip-connector-biz-5.3.286.jar`（3.2 MB，1,205 类）
> 等级：`VERIFIED_STATIC_BYTECODE`（类清单 + javap 方法/字段/枚举实证）
> ⚠️ **不在官方 102 清单** → 实现层
> ⚠️ facade 版本：`cip-connector-facade` 官方 5.3.600（本机 5.3.286）

---

## 0. ★★★ 一句话：连接器 = Linker

**`Linker` 是整个连接器体系的核心抽象。一个 Linker = 一个对外系统的接入配置。**

**它支持 5 种执行类型（`LinkerExecutorTypeEnum`）：**
```
DETAIL      接口调用（同步）
EVENT       事件订阅（含轮询）
SSO         单点登录
MQ          消息消费
SEND_MQ     消息发送
```

---

## 1. ★★ 结构（1,205 类）

| 包 | 类数 | 是什么 |
|---|---:|---|
| **`mobile`** | **353** | **移动端接入（最大）** |
| **`plug`** | **315** | **插件式接入（含中间表组织同步）** |
| `connector` | 278 | **★ Linker 主体** |
| `application` | 89 | 连接器应用 + 映射 |
| `ocip` | 70 | 开放接口平台（泛化调用） |
| `component` | 49 | 组件 |
| `custom` | 27 | 客开 |
| `util` / `common` / `exception` / `migration` / `callback` / `upgrade` | 24 | 支撑 |

---

## 2. ★★★ Linker 的 14 个实体（配置模型）

| 实体 | 作用 | 关键字段 |
|---|---|---|
| **`LinkerInfo`** | **接入主体** | 见 §2.1 |
| **`LinkerDetail`** | **接口明细** | 见 §2.2 |
| **`LinkerEventDetail`** | **事件订阅** | 见 §2.3 |
| `LinkerEventDetailPoll` | 事件轮询状态 | eventId / subscribeParam / status |
| **`LinkerMqEventDetail`** | **MQ 订阅** | url / username / password / topic / consumerGroup / mqType / mode |
| `LinkerMetadataInfo` | 元数据映射 | linkerType(OperationTypeEnum) / fullName |
| **`LinkerSignInfo`** | **加签配置** | mode / signStatus / signLocation / signExpression / secret / signName / signType |
| `LinkerSpiRef` | **SPI 引用（插件）** | linkerCode / appId / routerCode / pluginType |
| `LinkerClassify` | 分类 | caption / preset |
| `LinkerEnum` | 枚举定义 | name / caption / enable / type(STRING/NUMBER) |
| `LinkerEnumItem` | 枚举项 | enumId / name / value |
| `LinkerExecutorLog` | 执行日志 | — |
| `LinkerClassify` / `LinkerDetailClassify` | 分类 | — |

### 2.1 ★★★ `LinkerInfo`（34 字段）—— 接入总配置

```java
// 基本信息
String caption / name / description / icon
Long   classifyId
String provider                    ← 厂商
SourceEnum source                  ← 来源
TypeEnum type                      ← 类型
Integer sortNo
String productVersion

// ★ 接口协议
String mainAddress                 ← 主地址
String consumes / produces         ← Content-Type
String requestQuery / requestHeader
String returnParam / returnValueName / returnValueDefine
String wsWsdlUrl                   ← ★ WebService WSDL

// ★ 认证与签名
String secret                      ← 密钥
String signName / signType / signLocation / signExpression
Boolean signStatus
Boolean openApiStatus              ← 开放 API 开关

// ★ 用户映射
UserMappingTypeEnum userMappingType  ← 人员映射方式
Long   databaseInfoId                ← 数据库连接
Long   configId / registerId
String appId
Boolean enableApp

// ★ 门户（移动/PC）
String manageHomePage / webHomePage / mobileHomePage
Boolean enableSsoLogin
```

**★★★ 从字段就能读出：**
```
mainAddress + wsWsdlUrl        → 支持 HTTP 和 WebService 两种协议
signType/signLocation/expr     → 支持请求加签
userMappingType                → 第三方账号↔平台人员映射
webHomePage/mobileHomePage     → 接入后有自己的门户入口
enableSsoLogin                 → 支持 SSO
```

### 2.2 ★★★ `LinkerDetail`（41 字段）—— 接口明细（**三种执行形态合一**）

```java
Long   infoId
String caption / description
Boolean isAuthAction               ← 是否需鉴权
String requestUrl / requestPath
RequestTypeEnum requestType        ← ★ 请求类型
String methodName                  ← ★ 方法名（WebService）
String targetNamespace             ← ★ 命名空间（WebService）
Boolean paramNeedNs
String consumes / produces
String requestQuery / requestHeader / requestBody / xmlParam

// ★★★ 数据库执行（DbStatementType）
DbStatementType dbStatementType    ← SELECT/INSERT/UPDATE/DELETE
String selectParam / formParam / whereParam
String groupByParam / orderByParam / havingParam
Boolean isDistinct / isPage
String pageParam / sqlParam
Long   dataSourceId

// 结果
String returnParam
Boolean status / authStatus / signStatus
Boolean enableEntity / enablePackageResult
Boolean enableAsync                ← ★ 支持异步
```

**★★★ 关键：一个 `LinkerDetail` 能是 HTTP 接口、WebService 方法、或 SQL 语句。**
**⇒ 用 `requestType` + `dbStatementType` 区分。**

### 2.3 ★★ `LinkerEventDetail` —— 事件订阅

```java
Long   infoId / classifyId / subscribeId
String caption / name / description
RequestTypeEnum requestType
String consumes / produces
Boolean openEncrypt                 ← ★ 事件加解密
String subscribeParam / expression  ← ★ 订阅参数/表达式
String requestEncryptParam / requestParam / returnParam
Boolean status
Long   pollingIntervalTime          ← ★ 轮询间隔
Date   pollingTime                  ← 上次轮询时间
```

**★★ 两种事件方式：**
```
推送（subscribeParam + expression）
轮询（pollingIntervalTime + pollingTime）
```
**⇒ 轮询型是给「对方不支持推送」的系统用的。**

### 2.4 ★★ `LinkerMqEventDetail` —— MQ 订阅

```java
String url / username / password
String topic / consumerGroup
MqTypeEnum  mqType      ← KAFKA / ROCKET / RABBIT
MqModeEnum  mode        ← SEND / RECEIVE
String expression       ← 消息过滤表达式
String parameters / messageParam
Long   dataSourceId
```

**★★ 支持 3 种 MQ：Kafka / RocketMQ / RabbitMQ。**

---

## 3. ★★★ `LinkerFactory`（46 方法）—— 执行引擎

**这是连接器的核心，负责「按配置调出去」：**

```java
// ★ 执行器创建
LinkerExecutorService createExecutor(String)

// ★ 执行（多入口）
Object doExecute(Long, Map<String,Object>)                       // 按 id + 参数
Object doExecute(Long, Map, Boolean)
BaseResponse doExecute(ExecuteRequestDto)                        // 按 DTO
BaseResponse syncExecute(ExecuteRequestDto, ...)                 // ★ 同步
BaseResponse asyncExecute(ExecuteRequestDto, ...)                // ★ 异步

// ★ 回调
EventDataDto callBackExecutor(EventCallBackDto)
EventDataDto getEventDataDto(EventCallBackDto)
EventDataDto callBackEvent(LinkerInfoDto, ...)

// ★ 事件执行
Boolean syncDoExecuteEvent(LinkerEventDetailDto)
String  doExecuteEvent(LinkerEventDetailDto)

// ★ MQ
MqSendResult doSendMqEvent(Long, Object)
MqCustomSendResultDto sendCustomMq(Long, Object)

// ★★★ 参数转义（与 boot-starter-cip 呼应）
void paramEscapeBeforeInvoke(LinkerDetailParamInfoDto, ...)
void paramEscapeAfterInvoke(LinkerDetailParamInfoDto, ...)
boolean hasParamEscape(List<ParamDefinitionDto>)

// 响应处理
BaseResponse getResponse(String, String, ...)
BaseResponse getPageResponse(Object, ...)

// 校验
void checkExecute(LinkerInfoDto, ...)

// 日志（6+ 个重载）
void recordLog(...) / recordErrorLog(...) 多个重载
```

**★★★ 三个关键发现：**

1. **`syncExecute` / `asyncExecute` 分离** —— 支持异步调用（对应 `LinkerDetail.enableAsync`）
2. **`paramEscapeBeforeInvoke` / `paramEscapeAfterInvoke`** —— **这就是 `boot-starter-cip` 的 `ParamEscapeAppService` 的调用点！**
   **⇒ 说明「参数转义」是连接器调用前后做的：请求前把平台类型转成对方要的格式，响应后转回来。**
3. **日志重载极多（6+ 个）** —— 每种执行类型（detail/event/mq/poll）都有自己的日志

---

## 4. ★★ `LinkerAppServiceImpl`（86 方法）—— 配置管理

```java
// 查询
PageResponse<LinkerInfoDto>        selectPageByConditions(...)
ListResponse<LinkerInfoDto>        selectAll()
PageResponse<LinkerDetailDto>      selectPageDetailBy...
PageResponse<LinkerEventDetailDto> selectPageEventDetailBy...
SingleResponse<LinkerInfoDto>      selectBasicInfoBy... / selectOneByAppId(...)
SingleResponse<LinkerStatusDto>    selectStatusBy...
SingleResponse<LinkerActionStatusDto> selectActionStatus...

// 创建/更新/删除
SingleResponse<Long>    createCustom(SingleRequest<...>)
SingleResponse<Integer> updateCustom(...)
SingleResponse<Void>    deleteCustomById(...)
SingleResponse<LinkerInfoDto> copyLinkerNew(...)         ★ 复制连接器

// ★ 接口操作
SingleResponse<Long>    createOperation(...)
SingleResponse<Integer> updateOperation(...)
SingleResponse<Void>    updateOperationWithFile(...)     ★ 带文件
// ★ 事件操作
SingleResponse<Long>    createEventDetail(...)
SingleResponse<Long>    createEventDetailPoll(...)       ★ 轮询型
SingleResponse<Integer> updateEventDetail(...)
SingleResponse<Integer> updateEventDetailPoll(...)

// ★ 内部保护（3 个）
void checkDetailIsInternal(Long)
void checkEventIsInternal(Long)
void checkLinkerIsInternal(Long)
```

**★ `checkXxxIsInternal` —— 3 个方法保护「内置连接器」不被改。**
**⇒ 说明平台自带一批预置连接器。**

---

## 5. ★★ `LinkerBusinessService`（23 方法）—— 导出/导入/部署

```java
// ★ 导出为 JSON
String exportLinkerInfoByJson(Long)
String exportLinkerInfoByJsonForPlugin(Long)
LinkerDto exportLinker(Long)

// ★ 导入
LinkerImportIdMapDto importLinkerInfoByJsonForPlugin(String, ...)
CipAppInfoDto getLinkerForImportZip(String)
String getLinkerJsonDownloadUrl(String, String)

// ★ 执行
SingleResponse<ExecuteResponseDto> execute(...)
PageResponse executePage(ExecuteRequestDto)

// ★ 参数展示（给前端配界面用）
List<LinkerParameterDisplayDto> selectLinkerEventParameterDisplay(...)
List<LinkerParameterDisplayDto> selectLinkerMqParameterDisplay(...)
List<LinkerParameterDisplayDto> generateParameterDisplay(...)
List<LinkerParameterDisplayDto> selectLinkerDetailParameterDisplay(...)
List<ParamDefinitionDto> findPageDataDefinition(...)     ★ 递归解析分页

// ★ 部署
SingleResponse<CipDeployResultDto> deployApp(...)
List<LinkerCheckResultDto> putway(...)                   ★ 落地检查
Boolean register(Long)
```

**★★★ 关键：`exportLinkerInfoByJson` / `importLinkerInfoByJsonForPlugin`**
**⇒ 连接器可以**导出成 JSON** 再导入 —— 这是跨环境搬运的方式（与 BPM 的导出-导入机制一致）。**

**★★ `generateParameterDisplay` —— 自动生成参数配置界面。**
**⇒ 说明「配置界面是运行时生成的」：拿到对方接口的返回值结构，自动生成参数表单。**

**★ `putway`（落地）—— 返回 `LinkerCheckResultDto` 列表，说明有**连通性/正确性检查**。**

---

## 6. ★★★ 认证体系（`connector.domain.service.auth`）

**10 种第三方认证实现（`SecurityServiceImpl`）：**

```
AccountSecurityServiceImpl          账号密码
AnonymousSecurityServiceImpl        匿名
CommonSecurityServiceImpl           通用
DingTalkSecurityServiceImpl         钉钉
FeishuSecurityServiceImpl           飞书
JiraSecurityServiceImpl             Jira
TokenSecurityServiceImpl            Token
TwiceRequestSecurityServiceImpl     二次请求
WojiacloudSecurityServiceImpl       我佳云
XdHrSecurityServiceImpl             夏谷 HR
YonYouSecurityServiceImpl           用友
```

**⇒ 11 种认证方式，覆盖主流第三方系统。**

**配套：**
```
AuthExecutorService        认证执行器
AuthInfoService            认证信息
CommonSecurityService      通用安全
```

---

## 7. ★★ 数据库执行器（`connector.domain.service.database`）

```java
GenerateSqlFactory          ★ SQL 生成工厂
GenerateSqlProcessor        ★ SQL 处理器
AbstractCommonExecutorServiceImpl   抽象基类
MySqlExecutorServiceImplAbstract
OracleExecutorServiceImplAbstract
PostgreSqlExecutorServiceImplAbstract
SqlServerExecutorServiceImplAbstract
DatabaseExecutorServiceImpl          ★ 执行入口
```

**★ 4 种数据库方言的执行器（MySQL / Oracle / PostgreSQL / SQL Server）。**

### 7.1 ★ SQL 构建的枚举（`DbStatementType` / `DbOperatorTypeEnum` / `DbJoinEnum`）

```
DbStatementType     SELECT / INSERT / UPDATE / DELETE
DbOperatorTypeEnum  EQ / NE / LT / LE / GT / GE / IN / NI / LIKE
DbJoinEnum          LEFT_JOIN / RIGHT_JOIN / INNER_JOIN / OUTER_JOIN
DatabaseUseRangeEnum ONLY_CURRENT / INCLUDE_SUBORDINATE   ★ 本单位 / 含下级
```

**★★ `DatabaseUseRangeEnum` —— 说明数据库执行时可选「只用当前组织数据」还是「含下级」。**

---

## 8. ★★ 组织同步（`plug` 315 类）—— 中间表模式

**`MiddleTableAppServiceImpl`（21 方法）：**

```java
// ★ 保存（分类型）
saveUnit(...)        单位
saveLevel(...)       层级
savePost(...)        岗位
saveDuty(...)        职务
saveMember(...)      人员

String fullFinish(...)                ★ 完成标记

// 查询
PageResponse<UnitInfoDto>   queryUnit(...)
PageResponse<LevelInfoDto>  queryLevel(...)
PageResponse<PostInfoDto>   queryPost(...)
PageResponse<MemberInfoDto> queryMember(...)

// 删除
SingleResponse<Void> delete(...) / del(...)

// ★ 同步触发
void runningOrgSyncNowByLinkerCode(...)

// ★ 更新规则
List<MiddleTableUpdateRuleDto> queryUpdateRule(...)
void saveUpdateRule(...)

// 模板导入导出
String importTemplate(...) / downTemplate(...)
void batchImport(...)
```

**★★★ 中间表模式的完整链路：**
```
第三方系统 → 写中间表（unit/level/post/duty/member 五类）
      ↓
平台 side：saveUnit/saveLevel/savePost/saveDuty/saveMember 读中间表
      ↓
fullFinish 标记「这批同步完成」
      ↓
写入组织架构
```

**★ `MiddleTableUpdateRuleDto` —— 有「更新规则」配置（如何处理变更）。**

**`OrgSyncRunningAppServiceImpl`（9 方法）：**
```java
listEnableOrgSyncCapability(...)     ★ 列出可用的同步能力
updateRunningConfig(...)             运行配置
updateRunningTime(...)               运行时间
runningOrgSyncNow(...)               ★ 立即同步
getOrgRunningConfig(...)
getLatestOrgSyncResult(...)          ★ 最新同步结果
queryMdTableLog(...) / queryMdTableLogDetail(...)   ★ 同步日志
```

---

## 9. ★★ 移动端接入（`mobile` 353 类 —— 最大子包）

**`MobileOrgSyncAppService`（9 方法）：**
```java
createOrgSyncConfig / updateOrgSyncConfig / deleteOrgSyncConfig   配置 CRUD
pageOrgSyncConfig / detailOrgSyncConfig
executeOrgSync(...)               ★ 执行同步
userExport(...)                   ★ 人员导出
getRecord(...)
```

**`mobile.appservice` 全家（13 个）：**
```
ApplicationMobileAppServiceImpl   移动应用
MobileAppletAppService            小程序
MobileApplicationAppService       移动应用
MobileConfigAppService            移动配置
MobileManagerAppService           移动管理
MobileOrgSyncAppService           ★ 组织同步
MobileUserMappingAppService       ★ 用户映射
process.MobileApplicationProcessAppService
process.MobileConfigProcessAppService
process.MobileSpecialProcessAppService
process.MobileTodoProcessAppService   ★ 待办处理
sso.MobileCorpPluginAppService
sso.MobileSsoAppService           ★ 移动 SSO
```

**★ `mobile.mq`（9 类）—— 移动端有自己的 MQ 通道。**

---

## 10. ★ OCIP（开放接口平台，70 类）

```
ocip.appservice.OcipGeneralizationAppService    ★ 泛化调用
ocip.domain / ocip.dto / ocip.util
```

**★ `OcipGeneralizationAppService` —— 泛化调用入口。**
**⇒ 与「标品走 Dubbo 泛化」的形态一致。**

---

## 11. ★★ 应用与映射（`application` 89 类）

**`application.appservice`：**
```
appparam.AppRegisterAppServiceImpl       ★ 应用注册
mapping.MappingConfigAppService          ★ 映射配置
mapping.MappingDetailAppServiceImpl      ★ 映射明细
mapping.UserMappingAppService            ★ 用户映射
menu.CipMenuManageAppService             ★ 菜单管理
template.CipTemplateAppServiceImpl        ★ 模板
```

**`application.domain.service.mapping` 专门做映射：**
```
MappingConfigService           映射配置
MappingImpExpService           ★ 映射导入导出
OrgMappingDetailService        组织映射
UserMappingColumnService       用户映射列
UserMappingDetailService       用户映射明细
UserMappingMemberProcessor     ★ 人员映射处理器
UserMappingService             用户映射
UserMappingValueService        映射值
```

**★★ 映射枚举：**
```
MappingTypeEnum         ORG / MEMBER           组织 / 人员
MappingConfigBindEnum   MOBILE_PLUG / THIRD_APP  移动插件 / 三方应用
```

**⇒ 第三方组织架构 ↔ 平台组织架构需要映射（不是自动对应）。**

---

## 12. ★★ 完整枚举清单（17 个）

| 枚举 | 值 |
|---|---|
| **`LinkerExecutorTypeEnum`** | **DETAIL / EVENT / SSO / MQ / SEND_MQ** |
| **`RequestTypeEnum`** | （HTTP/WS/SQL 等，未完整取到） |
| **`DbStatementType`** | **SELECT / INSERT / UPDATE / DELETE** |
| **`DbOperatorTypeEnum`** | **EQ / NE / LT / LE / GT / GE / IN / NI / LIKE** |
| **`DbJoinEnum`** | **LEFT_JOIN / RIGHT_JOIN / INNER_JOIN / OUTER_JOIN** |
| **`MqTypeEnum`** | **KAFKA / ROCKET / RABBIT** |
| **`MqModeEnum`** | **SEND / RECEIVE** |
| **`EncryptEnum`** | **MD5 / SHA1 / SHA256** |
| `ClassifyTypeEnum` | DETAIL / EVENT / MQ |
| `ConfigModeEnum` | DB / MQ |
| `ConvertTypeEnum` | REQUEST / RESPONSE |
| `DatabaseUseRangeEnum` | **ONLY_CURRENT / INCLUDE_SUBORDINATE** |
| `LinkerEnumTypeEnum` | STRING / NUMBER |
| `LinkerPluginTypeEnum` | AFFAIR |
| `MappingConfigBindEnum` | MOBILE_PLUG / THIRD_APP |
| `MappingTypeEnum` | ORG / MEMBER |
| `OperationTypeEnum` | **DTO / MQ / APP / ENUM / OPEN_API / MENU** |
| `PageTypeEnum` | PAGE / OFFSET |
| `ParamTypeEnum` | **HEADER / QUERY / PATH / BODY** |

---

## 13. ★★★ 连接器的完整能力画像

**一个 Linker 能做的事：**

```
① 调接口（DETAIL）
   ├─ HTTP（url/path/query/header/body）
   ├─ WebService（wsdl/namespace/methodName/xmlParam）
   └─ 数据库（SELECT/INSERT/UPDATE/DELETE + 条件 + 分页 + 多库方言）
   ★ 同步 or 异步（enableAsync）

② 收事件（EVENT）
   ├─ 推送（subscribeParam + expression）
   └─ 轮询（pollingIntervalTime）
   ★ 可加解密（openEncrypt）

③ 收发 MQ（MQ / SEND_MQ）
   ├─ Kafka / RocketMQ / RabbitMQ
   └─ 消费（带 expression 过滤）/ 发送

④ SSO
   └─ enableSsoLogin + MobileSsoAppService

⑤ 认证（11 种）
   账号/匿名/通用/钉钉/飞书/Jira/Token/二次请求/我佳云/夏谷HR/用友

⑥ 加签
   MD5/SHA1/SHA256 + signLocation + signExpression

⑦ 参数转义（paramEscapeBefore/AfterInvoke）
   平台类型 ↔ 对方格式

⑧ 用户/组织映射
   UserMappingType + MappingType(ORG/MEMBER)

⑨ 门户
   webHomePage / mobileHomePage / manageHomePage

⑩ 导出导入
   exportLinkerInfoByJson / importLinkerInfoByJsonForPlugin
```

---

## 14. ★ 与 `boot-starter-cip` 的连接（重要）

**我在 `00A` 里确认 `boot-starter-cip` 是「参数转义/开放API错误码/V5迁移/文档版本」。**

**现在找到了调用点：**
```
LinkerFactory.paramEscapeBeforeInvoke(LinkerDetailParamInfoDto, ...)
LinkerFactory.paramEscapeAfterInvoke(...)
LinkerFactory.hasParamEscape(List<ParamDefinitionDto>)
```
**⇒ 「参数转义」不是独立功能，而是**连接器调用前/后必走的一步**。**
**⇒ 这就是两块拼图对上的地方。**

---

## 15. 未覆盖

| 项 | 说明 |
|---|---|
| `RequestTypeEnum` 完整值 | 未完整取到（推测 HTTP/WS/SQL） |
| `LinkerFactory` 剩余 16 个方法 | 只见前 30 |
| `LinkerAppServiceImpl` 剩余 56 个方法 | 只见前 30 |
| 各方法的方法体 | **全部未反编译** |
| `OcipGeneralizationAppService` 的契约 | 未读 |
| `plug` 315 类中除中间表外的部分 | 只见 appservice，未看 domain |
| `mobile` 353 类 | 只见 appservice（13 个），未看 domain（192 个） |
| `cip-connector-biz` 5.3.286 vs facade 5.3.600 | **版本差异未评估** |