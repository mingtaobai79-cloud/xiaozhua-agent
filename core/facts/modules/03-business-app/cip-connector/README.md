# 连接器（connector）

## 一句话

`com.seeyon.cip` 域的**可调用接口面**：5 个构件、439 个类、25 个 facade 接口 / 124 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `cip-connector-biz` | biz | 273 |
| `cip-connector-api` | api | 114 |
| `cip-connector-facade` | facade | 40 |
| `cip-connector-web` | web | 8 |
| `cip-manager-web` | web | 4 |
| **合计** | | **439** |

## 二、分层规律（写代码前必读）

`com.seeyon.cip` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

| 接口族 | 包 | 能力 | 什么时候用 |
|---|---|---|---|
| `*BaseAppService` | `api.core.*` | **含写**：create / update / 全字段查询 / dynamic | 要改数据，或要完整 DTO |
| `*CoreAppService` | `api.core.*` | **只读**：select*，Core DTO 字段精简 | 只查不改，性能敏感 |
| `OrgCommonAppService` | `api.common` | **业务聚合**：按选人数据解析、权限、组织域、扩展属性反查 | 需要「按规则找人」而不是按 id 查 |

调用顺序建议：

```
知道 id       →  XxxCoreAppService.selectXxxById        （最轻）
知道业务规则   →  OrgCommonAppService.selectXxxBySelectPeopleData
要写          →  XxxBaseAppService.create / update
```

## facade 层：25 个接口 / 124 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.cip.connector.api.affair` | 1 | 1 |
| `com.seeyon.cip.connector.api.authentication` | 1 | 9 |
| `com.seeyon.cip.connector.api.callback` | 2 | 3 |
| `com.seeyon.cip.connector.api.core` | 5 | 29 |
| `com.seeyon.cip.connector.api.db` | 1 | 14 |
| `com.seeyon.cip.connector.api.midorgsync` | 2 | 3 |
| `com.seeyon.cip.connector.api.midorgsync.callback` | 3 | 7 |
| `com.seeyon.cip.connector.api.mobile` | 8 | 47 |
| `com.seeyon.cip.connector.api.sign` | 1 | 4 |
| `com.seeyon.cip.connector.api.sso` | 1 | 7 |
| **合计** | **25** | **124** |

### `com.seeyon.cip.connector.api.affair`

#### CipThirdAffairService

`com.seeyon.cip.connector.api.affair.CipThirdAffairService` · 构件 `cip-connector-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `queryThirdAffairFieldData` | `ThirdTemplateDataSpiReqDto arg0` | `List<ThirdTemplateDataSpiReturnDto>` | 查询第三方事项字段数据 |

### `com.seeyon.cip.connector.api.authentication`

#### LinkerSecurityService

`com.seeyon.cip.connector.api.authentication.LinkerSecurityService` · 构件 `cip-connector-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getName` | `—` | `String` | 获取名称 |
| `getTypeCaption` | `—` | `String` | 获取类型Caption |
| `getMode` | `—` | `AuthInfoModeEnum` | 获取Mode |
| `doAuthentication` | `AuthenticationDto arg0` | `Map<String, Object>` | SPI 扩展点：Authentication（框架回调） |
| `doDecode` | `String arg0` | `AuthEventDto` | SPI 扩展点：Decode（框架回调） |
| `getPageJson` | `—` | `String` | 分页获取Json |
| `getSortNo` | `—` | `Integer` | 获取排序No |
| `jsonCheck` | `String arg0` | `void` | 检查（String） |
| `doVerification` | `AuthenticationDto arg0` | `Boolean` | SPI 扩展点：Verification（框架回调） |

### `com.seeyon.cip.connector.api.callback`

#### ConnectorCallbackMessageSendService

`com.seeyon.cip.connector.api.callback.ConnectorCallbackMessageSendService` · 构件 `cip-connector-api` · extends `BaseDto>`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `sendMsgAsync` | `T arg0` | `void` | 发送MsgAsync |
| `sendMsgSync` | `T arg0` | `void` | 发送MsgSync |

#### ConnectorCallbackProviderService

`com.seeyon.cip.connector.api.callback.ConnectorCallbackProviderService` · 构件 `cip-connector-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `doCallback` | `ConnectorCallbackRequestDto arg0` | `Res` | SPI 扩展点：Callback（框架回调） |

### `com.seeyon.cip.connector.api.core`

#### BaseConfigAppService

`com.seeyon.cip.connector.api.core.BaseConfigAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createDatabase` | `SingleRequest<DatabaseInfoDto> arg0` | `SingleResponse<Long>` | 新建Database |
| `updateDatabase` | `SingleRequest<DatabaseInfoDto> arg0` | `SingleResponse<Integer>` | 修改Database |
| `deleteDatabaseById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除Database按 id |
| `selectDatabaseById` | `SingleRequest<Long> arg0` | `SingleResponse<DatabaseInfoDto>` | 查询Database按 id |
| `selectDatabaseByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<DatabaseInfoDto>` | 查询Database按 ids |
| `selectPageDatabaseByCondition` | `PageRequest arg0` | `PageResponse<DatabaseInfoDto>` | 分页查询Database按条件 |
| `connectorDatabase` | `SingleRequest<DatabaseInfoDto> arg0` | `SingleResponse<String>` | 连接器：配置数据库型数据源（建连接） |
| `selectAllDatabaseType` | `—` | `ListResponse<String>` | 全部查询类型Database |
| `selectAllTableInfo` | `SingleRequest<Long> arg0` | `SingleResponse<Map<String, List<TableInfoDto>>>` | 全部查询表 |
| `selectAllTableNameById` | `SingleRequest<Long> arg0` | `ListResponse<String>` | 全部查询表名称按 id |
| `selectTableInfo` | `SingleRequest<TableInfoDto> arg0` | `ListResponse<TableInfoDto>` | 查询表 |

#### LinkerAppService

`com.seeyon.cip.connector.api.core.LinkerAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectPageByCondition` | `PageRequest arg0` | `PageResponse<LinkerInfoDto>` | 分页查询Linker按条件 |
| `selectAll` | `—` | `ListResponse<LinkerInfoDto>` | 全部查询Linker |
| `selectDetailsByInfoId` | `SingleRequest<Long> arg0` | `ListResponse<LinkerDetailDto>` | 查询Details按InfoId |
| `selectLinkerDetailParameterDisplay` | `SingleRequest<Long> arg0` | `ListResponse<LinkerParameterDisplayDto>` | 查询参数LinkerDetailDisplay |
| `selectEventDetailsByInfoId` | `SingleRequest<Long> arg0` | `ListResponse<LinkerEventDetailDto>` | 查询EventDetails按InfoId |
| `selectEventDetailById` | `SingleRequest<Long> arg0` | `SingleResponse<LinkerEventDetailDto>` | 查询EventDetail按 id |
| `selectPageDetailByCondition` | `PageRequest arg0` | `PageResponse<LinkerDetailDto>` | 分页查询Detail按条件 |
| `selectPageEventDetailByCondition` | `PageRequest arg0` | `PageResponse<LinkerEventDetailDto>` | 分页查询EventDetail按条件 |
| `selectDetailById` | `SingleRequest<Long> arg0` | `SingleResponse<LinkerDetailDto>` | 查询Detail按 id |
| `execute` | `SingleRequest<ExecuteRequestDto> arg0` | `SingleResponse<ExecuteResponseDto>` | 执行Execute |
| `mqCustomSend` | `SingleRequest<MqCustomSendDto> arg0` | `SingleResponse<MqCustomSendResultDto>` | 发送MqCustomSend |
| `executeSql` | `SingleRequest<ExecuteSqlDto> arg0` | `SingleResponse<SqlResultDto>` | 执行Sql |

#### LinkerEnumAppService

`com.seeyon.cip.connector.api.core.LinkerEnumAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectItemList` | `ListRequest arg0` | `ListResponse<LinkerEnumItemDto>` | 列表查询Item |

#### LinkerMigrationAppService

`com.seeyon.cip.connector.api.core.LinkerMigrationAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `exportEntityTask` | `SingleRequest<LinkMigrationRequestDto> arg0` | `SingleResponse<String>` | 导出实体任务 |
| `initDataJsonByNames` | `SingleRequest<List<String>> arg0` | `SingleResponse<Map<String, String>>` | 初始化数据Json按名称 |
| `listConnectorData` | `SingleRequest<ConnectorMigrateRequestDto> arg0` | `ListResponse<ConnectorMigrateDto>` | 列出连接器数据 |
| `importConnectorData` | `SingleRequest<ConnectorMigrateImportResponseDto> arg0` | `SingleResponse<Void>` | 导入连接器数据 |

#### SsoExecutorAppService

`com.seeyon.cip.connector.api.core.SsoExecutorAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `ssoLongin` | `SingleRequest<SsoRequestDto> arg0` | `SingleResponse<String>` | 连接器：执行 SSO 登录（拼第三方登录请求） |

### `com.seeyon.cip.connector.api.db`

#### DataBaseExecutorService

`com.seeyon.cip.connector.api.db.DataBaseExecutorService` · 构件 `cip-connector-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getDbTypeEnum` | `—` | `DbTypeEnum` | 获取类型枚举Db |
| `getName` | `—` | `String` | 获取名称 |
| `executeDetail` | `DatabaseInfoApiDto arg0` | `ExecutorResultApiDto` | 执行Detail |
| `executeDetailForCount` | `DatabaseInfoApiDto arg0` | `Integer` | 执行DetailForCount |
| `transformByType` | `Object arg0` | `String` | 数据库执行器：按类型转换取回的值 |
| `getAllTableName` | `DatabaseInfoApiDto arg0` | `List<String>` | 全部获取表名称 |
| `getPageTableName` | `DatabaseInfoApiDto arg0` | `PageData<String>` | 分页获取表名称 |
| `getDriver` | `—` | `String` | 获取Driver |
| `getAllTableInfo` | `DatabaseInfoApiDto arg0` | `List<TableInfoApiDto>` | 全部获取表 |
| `generateSql` | `LinkerDetailApiDto arg0` | `String` | 生成Sql |
| `generateSql` | `LinkerDetailApiDto arg0` | `String` | 生成Sql |
| `getConnection` | `DatabaseInfoApiDto arg0` | `Connection` | 获取Connection |
| `getVersion` | `—` | `String` | 获取版本 |
| `executeSql` | `ExecuteSqlApiDto arg0` | `SqlResultApiDto` | 执行Sql |

### `com.seeyon.cip.connector.api.midorgsync`

#### MiddleTableOrgSyncSpiListenerService

`com.seeyon.cip.connector.api.midorgsync.MiddleTableOrgSyncSpiListenerService` · 构件 `cip-connector-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `dataGovernance` | `ConnectorCallbackRequestDto arg0` | `Object` | 中间表组织同步：数据治理（清洗/映射） |

#### MiddleTableOrgSyncSpiPullService

`com.seeyon.cip.connector.api.midorgsync.MiddleTableOrgSyncSpiPullService` · 构件 `cip-connector-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `pullAll` | `ConfigInfoApiDto arg0` | `void` | 中间表组织同步：全量拉取 |
| `pullIncrement` | `ConfigInfoApiDto arg0` | `void` | 中间表组织同步：增量拉取 |

### `com.seeyon.cip.connector.api.midorgsync.callback`

#### MiddleTableOrgSyncDataCallbackService

`com.seeyon.cip.connector.api.midorgsync.callback.MiddleTableOrgSyncDataCallbackService` · 构件 `cip-connector-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `batchSaveOrg` | `UnitInfoSpiReqDto arg0` | `Integer` | 保存组织 |
| `batchSavePosition` | `PostInfoSpiReqDto arg0` | `Integer` | 保存Position |
| `batchSaveDuty` | `DutyInfoSpiReqDto arg0` | `Integer` | 保存Duty |
| `batchSaveLevel` | `LevelInfoSpiReqDto arg0` | `Integer` | 保存职务级别 |
| `batchSaveMember` | `MemberInfoSpiReqDto arg0` | `Integer` | 保存成员 |

#### MiddleTableOrgSyncExecuteCallbackService

`com.seeyon.cip.connector.api.midorgsync.callback.MiddleTableOrgSyncExecuteCallbackService` · 构件 `cip-connector-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `executeSyncToOrgModel` | `String arg0` | `Boolean` | 执行组织SyncToModel |

#### MiddleTableOrgSyncMarkCallbackService

`com.seeyon.cip.connector.api.midorgsync.callback.MiddleTableOrgSyncMarkCallbackService` · 构件 `cip-connector-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `markComplete` | `String arg0` | `String` | 标记Complete |

### `com.seeyon.cip.connector.api.mobile`

#### MobileApplicationProviderService

`com.seeyon.cip.connector.api.mobile.MobileApplicationProviderService` · 构件 `cip-connector-api` · extends `MobileProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getMobileUrlDto` | `MobileUrlProviderDto arg0` | `MobileUrlDto` | 获取MobileUrlDto |
| `explainLinkInfo` | `—` | `String` | 移动应用提供方：解释/构造跳转链接 |
| `publishApp` | `MobilePublishAppRequestDto arg0` | `Long` | 发布应用 |
| `getSignature` | `MobilePlatformConfigDto arg0` | `MobilePlatformSignatureResultDto` | 获取Signature |
| `sendMessage` | `boolean arg0` | `void` | 发送消息 |
| `getMobileSsoUserDto` | `MobilePlatformConfigDto arg0` | `MobileSsoUserDto` | 获取用户MobileSsoDto |
| `interfaceStatus` | `MobilePlatformConfigDto arg0` | `MobileInterfaceStatusDto` | 移动应用提供方：查询接口可用状态 |
| `getOpenId` | `MobilePlatformConfigDto arg0` | `String` | 获取Open |
| `getLaunchCode` | `MobilePlatformConfigDto arg0` | `String` | 获取编码Launch |
| `recallMessage` | `MobilePlatformConfigDto arg0` | `RecallResultDto` | 移动应用提供方：撤回已发消息 |

#### MobileCallBackProviderService

`com.seeyon.cip.connector.api.mobile.MobileCallBackProviderService` · 构件 `cip-connector-api`

（无方法）

#### MobileConfigProviderService

`com.seeyon.cip.connector.api.mobile.MobileConfigProviderService` · 构件 `cip-connector-api` · extends `MobileProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `jsonCheck` | `String arg0` | `void` | 检查（String） |
| `getName` | `—` | `String` | 获取名称 |
| `getTypeCaption` | `—` | `String` | 获取类型Caption |
| `getSortNo` | `—` | `Integer` | 获取排序No |
| `getPageJson` | `—` | `String` | 分页获取Json |
| `getAppId` | `String arg0` | `String` | 获取应用 |
| `getAppSecret` | `String arg0` | `String` | 获取应用密钥 |
| `getAppName` | `String arg0` | `String` | 获取应用名称 |
| `getAdminUrl` | `—` | `String` | 获取AdminUrl |
| `getThirdApplicationDomain` | `MobilePlatformConfigDto arg0` | `String` | 获取第三方应用域 |
| `getThirdConfigCondition` | `String arg0` | `Map<String, Object>` | 获取第三方配置条件 |
| `getMobileCorpId` | `String arg0` | `String` | 获取MobileCorp |
| `isPrivateApp` | `—` | `boolean` | 判断应用Private |
| `isOnlyBaseInfo` | `—` | `Boolean` | 判断Only |

#### MobileOrgSyncBatchProviderService

`com.seeyon.cip.connector.api.mobile.MobileOrgSyncBatchProviderService` · 构件 `cip-connector-api` · extends `MobileProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `syncUnitBatch` | `MobileDepartmentBatchSyncDto arg0` | `String` | 批量同步单位 |
| `userSyncBatch` | `MobileUserBatchSyncDto arg0` | `String` | 批量同步（MobileUserBatchSyncDto） |
| `syncBatchResult` | `MobileBatchResultDto arg0` | `MobileContactBatchResultDto` | 批量同步Result |

#### MobileOrgSyncProviderService

`com.seeyon.cip.connector.api.mobile.MobileOrgSyncProviderService` · 构件 `cip-connector-api` · extends `MobileProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `syncUnit` | `MobileUnitRequestDto arg0` | `Long` | 同步单位 |
| `updateUnit` | `MobileUnitRequestDto arg0` | `void` | 修改单位 |
| `getUnit` | `MobileUnitRequestDto arg0` | `String` | 获取单位 |
| `removeUnit` | `MobileUnitRequestDto arg0` | `void` | 移除单位 |
| `syncUser` | `MobileUserRequestDto arg0` | `String` | 同步用户 |
| `updateUser` | `MobileUserRequestDto arg0` | `String` | 修改用户 |
| `getUser` | `MobileUserRequestDto arg0` | `MobileUserResponseDto` | 获取用户 |
| `removeUser` | `MobileUserRequestDto arg0` | `MobileUserResponseDto` | 移除用户 |
| `syncUnitNew` | `MobileUnitRequestDto arg0` | `MobileOrgDto` | 同步单位New |

#### MobileOrgSyncPullProviderService

`com.seeyon.cip.connector.api.mobile.MobileOrgSyncPullProviderService` · 构件 `cip-connector-api` · extends `MobileProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `listSyncOrg` | `MobilePlatformConfigDto arg0` | `List<MobileSyncPullOrgResponseDto>` | 列出组织Sync |
| `listSyncUser` | `MobilePlatformConfigDto arg0` | `List<MobileSyncPullUserResponseDto>` | 列出用户Sync |
| `listSyncPost` | `MobilePlatformConfigDto arg0` | `List<MobileSyncPullPostDto>` | 列出岗位Sync |
| `listSyncJob` | `MobilePlatformConfigDto arg0` | `List<MobileSyncPullJobDto>` | 列出任务Sync |
| `listSyncLevel` | `MobilePlatformConfigDto arg0` | `List<MobileSyncPullLevelDto>` | 列出职务级别Sync |

#### MobileProviderService

`com.seeyon.cip.connector.api.mobile.MobileProviderService` · 构件 `cip-connector-api`

（无方法）

#### MobileTodoProviderService

`com.seeyon.cip.connector.api.mobile.MobileTodoProviderService` · 构件 `cip-connector-api` · extends `MobileProviderService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createTodo` | `MobilePlatformConfigDto arg0` | `String` | 新建Todo |
| `updateTodo` | `MobilePlatformConfigDto arg0` | `void` | 修改Todo |
| `doneTodo` | `MobilePlatformConfigDto arg0` | `void` | SPI 扩展点：doneTodo（框架回调） |
| `deleteTodo` | `MobilePlatformConfigDto arg0` | `void` | 删除Todo |
| `doneTodo` | `MobilePlatformConfigDto arg0` | `String` | SPI 扩展点：doneTodo（框架回调） |
| `deleteTodo` | `MobilePlatformConfigDto arg0` | `String` | 删除Todo |

### `com.seeyon.cip.connector.api.sign`

#### LinkerSignService

`com.seeyon.cip.connector.api.sign.LinkerSignService` · 构件 `cip-connector-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getName` | `—` | `String` | 获取名称 |
| `getCaption` | `—` | `String` | 获取Caption |
| `doSign` | `LinkerSignDto arg0` | `RequestParamDto` | SPI 扩展点：Sign（框架回调） |
| `getSortNo` | `—` | `Integer` | 获取排序No |

### `com.seeyon.cip.connector.api.sso`

#### SsoService

`com.seeyon.cip.connector.api.sso.SsoService` · 构件 `cip-connector-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getName` | `—` | `String` | 获取名称 |
| `getTypeCaption` | `—` | `String` | 获取类型Caption |
| `login` | `String arg0` | `String` | SSO 登录入口（发起单点登录） |
| `check` | `String arg0` | `void` | 检查（String） |
| `getPageJson` | `—` | `String` | 分页获取Json |
| `getSortNo` | `—` | `Integer` | 获取排序No |
| `needUserBind` | `—` | `boolean` | 绑定 |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 23 个领域服务，下表列**方法数最多的 23 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `LinkerDetailService` | 31 | LinkerDetail · 查询×10 / 检查×5 / 新建×4 |
| `LinkerMqEventService` | 30 | LinkerMqEvent · 查询×11 / 检查×5 / 构建×3 |
| `LinkerInfoService` | 29 | Linker · 查询×11 / 修改×4 / 新建×3 |
| `LinkerEventDetailService` | 27 | LinkerEventDetail · 查询×12 / 检查×4 / 修改×3 |
| `LinkerEnumService` | 19 | 枚举 · 查询×4 / 新建×3 / 删除×3 |
| `LinkerBusinessService` | 18 | 业务 · 查询×4 / 导出×3 / 执行×2 |
| `LinkerDetailClassifyService` | 18 | LinkerDetailClassify · 查询×5 / 新建×3 / 检查×3 |
| `DatabaseInfoService` | 14 | Database · 查询×7 / 修改×2 / 新建×1 |
| `LinkerSpiJarRefService` | 13 | LinkerSpiJarRef · 获取×3 / 构建×2 / 修改×1 |
| `LinkerEnumItemService` | 12 | 枚举 · 删除×4 / 查询×3 / 新建×2 |
| `AuthExecutorService` | 11 | 认证 · 获取×3 / 检查×3 / 判断有×1 |
| `LinkerEventDetailPollService` | 11 | LinkerEventDetailPoll · 删除×4 / 查询×4 / 修改×2 |
| `AuthInfoService` | 9 | 认证 · 查询×3 / 新建×1 / 修改×1 |
| `LinkerClassifyService` | 8 | LinkerClassify · 查询×3 / 新建×1 / 修改×1 |
| `LinkerExecutorLogService` | 7 | 日志 · 查询×3 / 新建×2 / 删除×1 |
| `SignExecutorService` | 7 | SignExecutor · 获取×6 / 签署×1 |
| `SsoInfoService` | 7 | Sso · 查询×3 / 新建×1 / 删除×1 |
| `SsoManagerService` | 6 | 负责人 · 获取×2 / 加载×1 / 检查×1 |
| `LinkerSignInfoService` | 5 | LinkerSign · 查询×2 / 新建×1 / 获取×1 |
| `LinkerMetaDataService` | 3 | LinkerMeta · 新建×1 / 删除×1 / 查询×1 |
| `LinkerThirdAffairRouterService` | 1 | 第三方事项 · 获取×1 |
| `InitDataService` | 1 | Init · 初始化×1 |
| `SsoExecutorService` | 1 | SsoExecutor（无业务方法，可能为纯装配类） |

## biz 层：事件与监听

事件 3 个 · 监听器 2 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| Linker | `LinkerCreateEvent`, `LinkerDeleteEvent`, `LinkerUpdateEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `LinkerSpiEventListener` | 1 |
| `MqEventListener` | 1 |

## web 层：Controller

共 12 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 核心实体 CRUD | `LinkerController` | 68 |
| 核心实体 CRUD | `CipBaseConfigController` | 12 |
| 核心实体 CRUD | `LinkerClassifyController` | 9 |
| 核心实体 CRUD | `LinkerEnumController` | 9 |
| 核心实体 CRUD | `LinkerSsoController` | 8 |
| 核心实体 CRUD | `AuthController` | 7 |
| 核心实体 CRUD | `CallbackController` | 7 |
| 核心实体 CRUD | `ForwardLinkerController` | 7 |
| 核心实体 CRUD | `LinkerMetadataController` | 6 |
| 核心实体 CRUD | `ForwardLinkerMetadataController` | 2 |
| 核心实体 CRUD | `ForwardLinkerSsoController` | 2 |
| 核心实体 CRUD | `ForwardLinkerEnumController` | 1 |

## 落表

> 证据等级：`VERIFIED_STATIC_BYTECODE`（表名出现在本模块 biz jar 的 class 常量池）
> ＋ `LIVE`（同名表已用 `information_schema` 在 `test2` 确认真实存在）。
> 粒度：**类级**。方法级落表未取证 —— 平台不用 MyBatis XML
> （21 个 biz 构件合计只有 9 个 mapper XML / 15 张表），SQL 内联在代码里，
> 方法→表要逐类反编译才能确认。

本模块代码中出现的真实表 **84** 张（来源构件：`cip-connector-biz`）：

| 表名 | 注释 | 出现在几个类 |
|---|---|---:|
| `cip_mobile_corp` | 移动插件企业表 | 4 |
| `cip_sync_result` | 中间表同步日志表 | 4 |
| `cip_sync_duty` | 组织同步职务中间表 | 3 |
| `cip_sync_level` | 组织同步职级中间表 | 3 |
| `cip_sync_member` | 组织同步人员中间表 | 3 |
| `cip_sync_post` | 组织同步岗位中间表 | 3 |
| `cip_sync_unit` | 组织同步组织中间表 | 3 |
| `org_job` | 职务 | 3 |
| `org_level` | 职级 | 3 |
| `cip_custom_app` | 集成应用信息表 | 2 |
| `cip_database_info` | 数据库配置信息表 | 2 |
| `cip_download_log` | 文件下载历史表 | 2 |
| `cip_linker_auth_info` | 连接器认证信息表 | 2 |
| `cip_linker_classify_info` | 连接器分类表 | 2 |
| `cip_linker_detail` | 连接器动作详情表 | 2 |
| `cip_linker_detail_classify` | 连接器动作分类表 | 2 |
| `cip_linker_enum` | 连接器枚举类 | 2 |
| `cip_linker_enum_item` | 连接器枚举项类 | 2 |
| `cip_linker_event_detail` | 连接器事件详情表 | 2 |
| `cip_linker_event_detail_poll` | 连接器事件轮询表 | 2 |
| `cip_linker_executor_log` | 连接器执行日志表 | 2 |
| `cip_linker_info` | 连接器信息表 | 2 |
| `cip_linker_metadata_info` | 连接器元数据记录表 | 2 |
| `cip_linker_mq_event_detail` | 连接器mq事件信息表 | 2 |
| `cip_linker_sign_info` | 连接器签名信息表 | 2 |
| `cip_linker_spi_ref` | 连接器spi引用依赖表 | 2 |
| `cip_mapping_config` | 映射配置 | 2 |
| `cip_p_capability_info` | 插件能力基本信息表 | 2 |
| `cip_p_data_check_conf` | 基础插件数据补偿配置 | 2 |
| `cip_p_ldap_info` | ldap信息 | 2 |
| `cip_p_operate_log` | 插件操作日志表 | 2 |
| `cip_p_org_running_config` | 组织结构同步运行态数据 | 2 |
| `cip_p_org_sync_config` | 组织同步插件能力的配置详情 | 2 |
| `cip_p_param_mapping` | 插件参数映射表 | 2 |
| `cip_p_plugin_info` | 插件基本信息表 | 2 |
| `cip_p_running_detail` | 插件运行态详情表 | 2 |
| `cip_p_sync_affair` | 事项已同步数据 | 2 |
| `cip_p_sync_his` | 插件同步历史数据表 | 2 |
| `cip_p_sync_org` | 组织模型已同步数据表 | 2 |
| `cip_p_timer_job` | 插件定时任务信息表 | 2 |
| `cip_p_todo_config` | 待办/消息配置详情表 | 2 |
| `cip_sync_duty_view` | 组织同步职务中间表_查询 | 2 |
| `cip_sync_level_view` | 组织同步职级中间表_查询 | 2 |
| `cip_sync_member_view` | 组织同步人员中间表_查询 | 2 |
| `cip_sync_post_view` | 组织同步岗位中间表_查询 | 2 |
| `cip_sync_unit_view` | 组织同步组织中间表_查询 | 2 |
| `cip_user_mapping_column` | 用户映射的列信息 | 2 |
| `cip_user_mapping_detail` | 用户映射具体配置信息表 | 2 |
| `cip_user_mapping_value` | 用户映射的值信息 | 2 |
| `cip_warning_log` | 集成预警信息表 | 2 |
| `cip_ability_dingtalk_link` | 钉钉消息链接表 | 1 |
| `cip_app_param` | 应用参数 | 1 |
| `cip_app_param_detail` | 应用参数明细 | 1 |
| `cip_applet_version` | 小程序版本管理表 | 1 |
| `cip_data_check_config` | 基础插件数据补偿配置 | 1 |
| `cip_dingtalk_link` | 钉钉消息链接表 | 1 |
| `cip_ldap_info` | ldap信息 | 1 |
| `cip_mobile_app` | 移动插件表 | 1 |
| `cip_mobile_applet` | 小程序版本管理表 | 1 |
| `cip_mobile_config` | 第三方平台配置信息 | 1 |
| `cip_mobile_log` | 日志记录表 | 1 |
| `cip_mobile_msg_mapping` | 移动插件消息映射表 | 1 |
| `cip_mobile_plugin` | 移动插件表 | 1 |
| `cip_mobile_swtich` | 移动插件开关配置 | 1 |
| `cip_mobile_swtich_config` | 移动插件开关配置 | 1 |
| `cip_mobile_sync_config` | 组织同步配置表（向外） | 1 |
| `cip_mobile_todo_mapping` | 移动插件待办映射表 | 1 |
| `cip_mp_menu` | 微信公众号菜单表 | 1 |
| `cip_ocip_access_log` | ocip访问日志 | 1 |
| `cip_org_mapping_detail` | 用户映射具体配置信息表 | 1 |
| `cip_org_running_config` | 组织结构同步运行态数据 | 1 |
| `cip_org_sync_config` | 组织同步插件能力的配置详情 | 1 |
| `cip_plugin_capability_info` | 插件能力基本信息表 | 1 |
| `cip_plugin_info` | 插件基本信息表 | 1 |
| `cip_plugin_org_sync_config` | 组织同步配置表（向外） | 1 |
| `cip_plugin_param_mapping` | 插件参数映射表 | 1 |
| `cip_plugin_timer_job` | 插件定时任务信息表 | 1 |
| `cip_push_affair_log` | 外推待办日志表 | 1 |
| `cip_third_menu` | 应用菜单管理 | 1 |
| `cip_third_platform_config` | 第三方平台配置信息 | 1 |
| `cip_third_template` | 三方模板表 | 1 |
| `cip_todo_config` | 待办/消息配置详情表 | 1 |
| `cip_user_sso_info` | 单点登录信息 | 1 |
| `ctp_user` | 用户 | 1 |

### 接口 → 表（3 条）

> `implements` = 字节码声明实现了该接口；`implements+field` = 再经它持有的
> Manager/Dao 字段一跳；两者都是静态事实。`stem` 只是类名同源（弱证据，需实测）。
> 表名本身都 `VERIFIED`；**哪个方法写哪张表仍未取证**。

| facade 接口 | 承载类 | 表 | 依据 |
|---|---|---|---|
| `LinkerEnumAppService` | `LinkerEnum` | `cip_linker_enum` | `stem` |
| `MiddleTableOrgSyncDataCallbackService` | `MiddleTableService` | `cip_sync_duty`, `cip_sync_level`, `cip_sync_member`, `cip_sync_post`, `cip_sync_result`, `cip_sync_unit` | `implements+field` |
| `MiddleTableOrgSyncMarkCallbackService` | `MiddleTableService` | `cip_sync_duty`, `cip_sync_level`, `cip_sync_member`, `cip_sync_post`, `cip_sync_result`, `cip_sync_unit` | `implements+field` |

## REST 路由

> 证据：`javap -v` 读 Controller 字节码里的 `@RequestMapping`/`@PostMapping` 注解值。
> 等级 `VERIFIED_STATIC_BYTECODE`（注解值是常量，非推断）。

**拼法**（以 `organization` 为例，`:8080` 之类按环境）：

```
POST /service/{类级路径}/{方法级路径}
      ↑ 类级路径的第一段就是应用 code（organization / bpm / udc …），不要再加一层
  例：POST /service/udc/runtime/deploy-normal
      = DeployController 类级 `udc/runtime` + 方法级 `deploy-normal`（线上实测过）
```

控制器 **33** 个、路由 **368** 条（来源：`cip-connector-web`）。

> `{id}`、`ids` 这类方法级路径不带类级前缀，拼时必须补上。
> 完整清单（含 java 方法名）：`docs/audit/artifacts/rest/ROUTES-cip-connector.md`

| Controller | 类级路径 | 路由 |
|---|---|---:|
| `LinkerController` | `cip-connector/connector-info` | 67 |
| `LinkerUserMappingController` | `cip-connector/connector/mapping` | 38 |
| `PluginCapabilityController` | `cip-connector/plug/capability` | 28 |
| `MobileApplicationController` | `cip-connector/mobile` | 18 |
| `OrgSyncDesignController` | `cip-connector/plug/org-sync-design` | 16 |
| `CipApplicationController` | `cip-connector/custom-app` | 14 |
| `MobileController` | `cip-connector/mobile` | 14 |
| `PluginDataCheckController` | `cip-connector/plug/data-check` | 12 |
| `CipBaseConfigController` | `cip-connector/base-config` | 12 |
| `AppRegisterController` | `cip-connector/connector/appreg` | 12 |
| `MobileAppletController` | `cip-connector/mobile` | 11 |
| `CipConnectorApiController` | `cip-connector/apitest` | 11 |
| `MiddleTableViewController` | `cip-connector/plug/midview` | 9 |
| `MobileOrgSyncController` | `cip-connector/mobile` | 8 |
| `MiddleTableController` | `cip-connector/plug/middletable` | 8 |
| `LinkerClassifyController` | `cip-connector/connector-classify` | 8 |
| `LinkerSsoController` | `cip-connector/connector/sso` | 8 |
| `LinkerEnumController` | `cip-connector/connector-enum` | 8 |
| `OrgSyncRunningController` | `cip-connector/plug/org-sync-running` | 7 |
| `CipWarningController` | `cip-connector/warning` | 6 |
| `TodoRedirectController` | `cip-connector/plug/redirect-url` | 6 |
| `PluginInfoController` | `cip-connector/plug/basic` | 6 |
| `ConnectorCallbackController` | `cip-connector/base/callback` | 6 |
| `AuthController` | `cip-connector/connector-auth` | 6 |
| `LinkerMetadataController` | `cip-connector/connector-metadata` | 6 |
| `CipMenuManageController` | `cip-connector/application/menu` | 5 |
| `CipTemplateController` | `cip-connector/third/template` | 5 |
| `MobileTestController` | `cip-connector/mobile` | 4 |
| `MobileCallbackController` | `cip-connector/mobile/auth` | 2 |
| `FileApiController` | `cip-connector/apitest/file` | 2 |
| `CallbackController` | `cip-connector/call-back` | 2 |
| `CipMigrationController` | `cip-manager/migration` | 2 |
| `MobileUserMappingController` | `cip-connector/mobile/usermapping` | 1 |

前 15 条（其余见明细）：

| 方法 | 全路径 |
|---|---|
| `GetMapping` | `/service/cip-connector/apitest/callback/get-url` |
| `GetMapping` | `/service/cip-connector/apitest/ocip/ocipConfig` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/check` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/doc/async` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/doc/sync` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/user/sk` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/user/body` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/data/transfer` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/sk/delete` |
| `PostMapping` | `/service/cip-connector/apitest/ocip/log/list` |
| `PostMapping` | `/service/cip-connector/apitest/org-sync/middle-table/clear/test` |
| `PostMapping` | `/service/cip-connector/apitest/file/upload` |
| `PostMapping` | `/service/cip-connector/apitest/file/get` |
| `PostMapping` | `/service/cip-connector/connector/appreg/add` |
| `PostMapping` | `/service/cip-connector/connector/appreg/modify` |

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 25 接口 / 124 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 23 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 3 事件 / 2 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 12 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径（368 条） | Controller 字节码注解 | `VERIFIED_STATIC_BYTECODE` |
| REST 真机验证 | 171/172 条安全路由命中（99%） | `LIVE` |
| 落表（87 张表，类级） | class 常量池 + `information_schema` | `VERIFIED_STATIC_BYTECODE` + `LIVE` |
| 方法级落表 | 未取证（SQL 内联，需逐类反编译） | `UNVERIFIED` |
