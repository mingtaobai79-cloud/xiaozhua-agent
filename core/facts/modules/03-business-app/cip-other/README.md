# 集成周边（application·plug·basic·convert·openapi·custom）

## 一句话

`com.seeyon.cip` 域的**可调用接口面**：3 个构件、164 个类、23 个 facade 接口 / 94 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `cip-connector-biz` | biz | 89 |
| `cip-connector-facade` | facade | 71 |
| `cip-connector-web` | web | 4 |
| **合计** | | **164** |

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

## facade 层：23 个接口 / 94 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.cip.application.api` | 9 | 40 |
| `com.seeyon.cip.basic.api` | 3 | 19 |
| `com.seeyon.cip.convert.api` | 1 | 8 |
| `com.seeyon.cip.custom.api` | 2 | 3 |
| `com.seeyon.cip.openapi.operate.api` | 3 | 4 |
| `com.seeyon.cip.plug.api` | 5 | 20 |
| **合计** | **23** | **94** |

### `com.seeyon.cip.application.api`

#### ApplicationAffairAppService

`com.seeyon.cip.application.api.ApplicationAffairAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `addModifyPluginAffair` | `SingleRequest<PluginAffairBatchDto> arg0` | `SingleResponse<PluginAffairResultDto>` | 新增事项ModifyPlugin |
| `processRevoke` | `SingleRequest<PluginAffairGroupDto> arg0` | `SingleResponse<Void>` | 处理Revoke |
| `processTerminate` | `SingleRequest<PluginAffairGroupDto> arg0` | `SingleResponse<Void>` | 处理Terminate |
| `queryExternalIdByAffair` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 查询外部人员按事项 |
| `listExternalIdsByAffairIds` | `SingleRequest<AffairIdMappingQueryDto> arg0` | `ListResponse<AffairIdMappingResultDto>` | 列出外部人员Ids按事项 |
| `queryAffairByExternalId` | `SingleRequest<AffairQueryDto> arg0` | `SingleResponse<AffairDisplayDto>` | 查询事项按外部人员 |
| `retryPushAffair` | `SingleRequest<RetryPushAffairOpenApiDto> arg0` | `SingleResponse<Void>` | 重试推送事项 |
| `queryAffairListByExternalIdList` | `SingleRequest<AffairBatchQueryDto> arg0` | `ListResponse<AffairDisplayDto>` | 列表查询事项按外部人员 |

#### ApplicationMessageAppService

`com.seeyon.cip.application.api.ApplicationMessageAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `syncPluginMessage` | `SingleRequest<PluginMessageBatchDto> arg0` | `SingleResponse<PluginMessageResultDto>` | 同步消息Plugin |

#### ApplicationMobileAppService

`com.seeyon.cip.application.api.ApplicationMobileAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getAppUrl` | `SingleRequest<AppUrlRequestDto> arg0` | `SingleResponse<AppUrlResponseDto>` | 获取应用Url |
| `recallMessage` | `SingleRequest<RecallMsgDto> arg0` | `SingleResponse<RecallMsgResultDto>` | 移动应用：撤回已推送消息 |

#### ApplicationPluginStatusAppService

`com.seeyon.cip.application.api.ApplicationPluginStatusAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectStatusByPlugIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<PlugStatusDto>` | 查询Status按PlugIds |
| `selectStatusByLinkerIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<PlugStatusDto>` | 查询Status按LinkerIds |

#### MappingDetailAppService

`com.seeyon.cip.application.api.MappingDetailAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `addOrgMappingDetail` | `SingleRequest<OrgMappingDetailAddReqDto> arg0` | `SingleResponse<Long>` | 新增组织映射Detail |
| `modifyOrgMappingDetail` | `SingleRequest<OrgMappingDetailUpdateReqDto> arg0` | `SingleResponse<Void>` | 修改组织映射Detail |
| `addUserMappingDetail` | `SingleRequest<UserMappingDetailAddReqDto> arg0` | `SingleResponse<Long>` | 新增用户映射Detail |
| `modifyUserMappingDetail` | `SingleRequest<UserMappingDetailUpdateReqDto> arg0` | `SingleResponse<Void>` | 修改用户映射Detail |
| `queryUserMappingDetail` | `PageRequest arg0` | `PageResponse<UserMappingDetailResDto>` | 查询用户映射Detail |
| `queryOrgMappingDetail` | `PageRequest arg0` | `PageResponse<OrgMappingDetailResDto>` | 查询组织映射Detail |
| `deleteOrgMappingDetail` | `SingleRequest<OrgMappingDetailDeleteReqDto> arg0` | `SingleResponse<Void>` | 删除组织映射Detail |
| `deleteUserMappingDetail` | `SingleRequest<UserMappingDetailDeleteReqDto> arg0` | `SingleResponse<Void>` | 删除用户映射Detail |
| `getOrgInnerIdByOuterId` | `SingleRequest<OrgInnerIdReqDto> arg0` | `SingleResponse<OrgInnerIdResDto>` | 获取组织Inner按OuterId |
| `getOrgOuterIdByInnerId` | `SingleRequest<OrgOuterIdReqDto> arg0` | `SingleResponse<OrgOuterIdResDto>` | 获取组织Outer按InnerId |
| `getUserInnerIdByOuterId` | `SingleRequest<UserInnerIdReqDto> arg0` | `SingleResponse<UserInnerIdResDto>` | 获取用户Inner按OuterId |
| `getUserOuterIdByInnerId` | `SingleRequest<UserOuterIdReqDto> arg0` | `SingleResponse<UserOuterIdResDto>` | 获取用户Outer按InnerId |

#### MiddleTableAppService

`com.seeyon.cip.application.api.MiddleTableAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `saveUnit` | `SingleRequest<UnitInfoReqDto> arg0` | `SingleResponse<Void>` | 保存单位 |
| `saveLevel` | `SingleRequest<LevelInfoReqDto> arg0` | `SingleResponse<Void>` | 保存职务级别 |
| `savePost` | `SingleRequest<PostInfoReqDto> arg0` | `SingleResponse<Void>` | 保存岗位 |
| `saveDuty` | `SingleRequest<DutyInfoReqDto> arg0` | `SingleResponse<Void>` | 保存Duty |
| `saveMember` | `SingleRequest<MemberInfoReqDto> arg0` | `SingleResponse<Void>` | 保存成员 |
| `fullFinish` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 完成（SingleRequest） |
| `queryUnit` | `PageRequest arg0` | `PageResponse<UnitInfoDto>` | 查询单位 |
| `queryLevel` | `PageRequest arg0` | `PageResponse<LevelInfoDto>` | 查询职务级别 |
| `queryPost` | `PageRequest arg0` | `PageResponse<PostInfoDto>` | 查询岗位 |
| `queryMember` | `PageRequest arg0` | `PageResponse<MemberInfoDto>` | 查询成员 |
| `delete` | `SingleRequest<MiddleTableDeleteReqDto> arg0` | `SingleResponse<Void>` | 删除表 |
| `runningOrgSyncNowByLinkerCode` | `SingleRequest<RunningOrgSyncNowDto> arg0` | `SingleResponse<Void>` | 同步Now按编码 |

#### MobileAppService

`com.seeyon.cip.application.api.MobileAppService` · 构件 `cip-connector-facade`

（无方法）

#### WarningCallBackAppService

`com.seeyon.cip.application.api.WarningCallBackAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `redoWarning` | `SingleRequest<CipWarningInfoDto> arg0` | `SingleResponse<Void>` | 告警回调：重发告警 |

#### WarningManageAppService

`com.seeyon.cip.application.api.WarningManageAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `addWarningInfo` | `SingleRequest<CipWarningInfoDto> arg0` | `SingleResponse<Long>` | 新增Warning |
| `modifyWarningInfo` | `SingleRequest<CipWarningInfoDto> arg0` | `SingleResponse<Void>` | 修改Warning |

### `com.seeyon.cip.basic.api`

#### DefaultCardInfoService

`com.seeyon.cip.basic.api.DefaultCardInfoService` · 构件 `cip-manager-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getBeanName` | `—` | `String` | 获取名称Bean |
| `getName` | `—` | `String` | 获取名称 |
| `getTypeCaption` | `—` | `String` | 获取类型Caption |
| `buildCardInfo` | `String arg0` | `StaffCardDefaultRunDto` | 构建Card |

#### OrgIntegrationAppService

`com.seeyon.cip.basic.api.OrgIntegrationAppService` · 构件 `cip-manager-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `queryCardInfo` | `SingleRequest<QueryReqDto> arg0` | `SingleResponse<QueryResDto>` | 查询Card |
| `updateCardInfo` | `SingleRequest<UpdateReqDto> arg0` | `SingleResponse<Boolean>` | 修改Card |
| `queryServiceTypeInfo` | `—` | `SingleResponse<List<ServiceTypeDto>>` | 查询类型Service |
| `queryJsApiAddressByCode` | `String arg0` | `SingleResponse<List<Map<String, Object>>>` | 查询APIJsAddress按编码 |
| `queryCardRunInfo` | `SingleRequest<QueryRunReqDto> arg0` | `SingleResponse<Map<String, QueryRunResDto>>` | 查询CardRun |
| `queryCardShowInfo` | `—` | `SingleResponse<StaffCardShowTypeDto>` | 查询CardShow |
| `queryCardShowIsCustomAvatar` | `SingleRequest<Void> arg0` | `SingleResponse<Boolean>` | 查询CardShowIsCustomAvatar |
| `queryDefaultCardInfo` | `SingleRequest<QueryRunReqDto> arg0` | `SingleResponse<StaffCardDefaultResultDto>` | 查询DefaultCard |
| `queryDefaultCardCustomAvatar` | `SingleRequest<List<String>> arg0` | `SingleResponse<Map<String, Object>>` | 查询DefaultCardCustomAvatar |
| `queryThirdNativeCardInfo` | `SingleRequest<QueryThirdNativeCardReqDto> arg0` | `SingleResponse<StaffCardThirdNativeDto>` | 查询第三方NativeCard |

#### PersonnelCardService

`com.seeyon.cip.basic.api.PersonnelCardService` · 构件 `cip-manager-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getServiceCode` | `—` | `String` | 获取编码Service |
| `getServiceName` | `—` | `String` | 获取名称Service |
| `getServiceResParam` | `—` | `Map<String, Object[]>` | 获取ServiceResParam |
| `queryJsApiAddressParam` | `—` | `List<Map<String, Object>>` | 查询APIJsAddressParam |
| `result` | `Map<String, Object> arg0` | `Map<String, Object>` | 人员卡片：返回卡片渲染结果（SPI 回调） |

### `com.seeyon.cip.convert.api`

#### HtmlConvertAppService

`com.seeyon.cip.convert.api.HtmlConvertAppService` · 构件 `cip-convert-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `transfer` | `SingleRequest<TransferRequestDto> arg0` | `SingleResponse<FileConvertResultDto>` | 转移Transfer |
| `queryTransferInfo` | `SingleRequest<QueryTransferRequestDto> arg0` | `SingleResponse<FileConvertResultDto>` | 查询Transfer |
| `transferToZip` | `SingleRequest<MultipleTransferRequestDto> arg0` | `SingleResponse<FileConvertResultDto>` | 转移ToZip |
| `multiTabTransfer` | `SingleRequest<MultiTabTransferRequestDto> arg0` | `SingleResponse<MultiTabFileConvertResultDto>` | 转移MultiTabTransfer |
| `queryMultiTabTransferInfo` | `SingleRequest<MultiTabTransferRequestDto> arg0` | `SingleResponse<MultiTabFileConvertResultDto>` | 查询MultiTabTransfer |
| `getPageElementsByEvaluateFunction` | `SingleRequest<PageElementsRequestDto> arg0` | `SingleResponse<FileConvertResultDto>` | 分页获取Elements按EvaluateFunction |
| `batchDeleteByBusinessIds` | `SingleRequest<PageElementsDeleteRequestDto> arg0` | `SingleResponse<PageElementsDeleteResultDto>` | 删除页面按业务 |
| `getPicByFunction` | `SingleRequest<PicRequestDto> arg0` | `SingleResponse<FileConvertResultDto>` | 获取Pic按Function |

### `com.seeyon.cip.custom.api`

#### WarningCallBackAppService

`com.seeyon.cip.custom.api.WarningCallBackAppService` · 构件 `cip-manager-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `redoWarning` | `SingleRequest<CipWarningInfoDto> arg0` | `SingleResponse<Void>` | 告警回调：重发告警 |

#### WarningManageAppService

`com.seeyon.cip.custom.api.WarningManageAppService` · 构件 `cip-manager-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `addWarningInfo` | `SingleRequest<CipWarningInfoDto> arg0` | `SingleResponse<Long>` | 新增Warning |
| `modifyWarningInfo` | `SingleRequest<CipWarningInfoDto> arg0` | `SingleResponse<Void>` | 修改Warning |

### `com.seeyon.cip.openapi.operate.api`

#### CipFileAppService

`com.seeyon.cip.openapi.operate.api.CipFileAppService` · 构件 `cip-manager-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `uploadFiles` | `SingleRequest<Void> arg0` | `SingleResponse<Void>` | 上传Files |
| `deleteByStorageKeys` | `SingleRequest<FileDeleteDto> arg0` | `SingleResponse<Boolean>` | 删除文件按存储 |

#### CipMessageAppService

`com.seeyon.cip.openapi.operate.api.CipMessageAppService` · 构件 `cip-manager-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `deliveryMqMessage` | `SingleRequest<CipMessageDeliveryDto> arg0` | `SingleResponse<Boolean>` | 集成消息：投递 MQ 消息 |

#### OpenApiNotifyAppService

`com.seeyon.cip.openapi.operate.api.OpenApiNotifyAppService` · 构件 `cip-manager-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `batchSaveOpenApiNotify` | `SingleRequest<List<CipNotifyMessageDto>> arg0` | `SingleResponse<Void>` | 保存APIOpenNotify |

### `com.seeyon.cip.plug.api`

#### CipPlugCapabilityAppService

`com.seeyon.cip.plug.api.CipPlugCapabilityAppService` · 构件 `cip-connector-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getAndCheckCapability` | `SingleRequest<CapabilityInfoQueryDto> arg0` | `ListResponse<CipPluginCapabilityInfoDto>` | 获取集成能力AndCheck |

#### MiddleTableOperationAppService

`com.seeyon.cip.plug.api.MiddleTableOperationAppService` · 构件 `cip-manager-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `saveUnit` | `SingleRequest<UnitInfoReqDto> arg0` | `SingleResponse<Void>` | 保存单位 |
| `saveLevel` | `SingleRequest<LevelInfoReqDto> arg0` | `SingleResponse<Void>` | 保存职务级别 |
| `savePost` | `SingleRequest<PostInfoReqDto> arg0` | `SingleResponse<Void>` | 保存岗位 |
| `saveDuty` | `SingleRequest<DutyInfoReqDto> arg0` | `SingleResponse<Void>` | 保存Duty |
| `saveMember` | `SingleRequest<MemberInfoReqDto> arg0` | `SingleResponse<Void>` | 保存成员 |
| `fullFinish` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 完成（SingleRequest） |
| `queryUnit` | `PageRequest arg0` | `PageResponse<UnitInfoDto>` | 查询单位 |
| `queryLevel` | `PageRequest arg0` | `PageResponse<LevelInfoDto>` | 查询职务级别 |
| `queryPost` | `PageRequest arg0` | `PageResponse<PostInfoDto>` | 查询岗位 |
| `queryMember` | `PageRequest arg0` | `PageResponse<MemberInfoDto>` | 查询成员 |
| `delete` | `SingleRequest<MiddleTableDeleteReqDto> arg0` | `SingleResponse<Void>` | 删除表 |
| `runningOrgSyncNowByLinkerCode` | `SingleRequest<RunningOrgSyncNowDto> arg0` | `SingleResponse<Void>` | 同步Now按编码 |

#### PluginAffairAppService

`com.seeyon.cip.plug.api.PluginAffairAppService` · 构件 `cip-manager-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `addModifyPluginAffair` | `SingleRequest<PluginAffairBatchDto> arg0` | `SingleResponse<PluginAffairResultDto>` | 新增事项ModifyPlugin |
| `processRevoke` | `SingleRequest<PluginAffairGroupDto> arg0` | `SingleResponse<Void>` | 处理Revoke |
| `processTerminate` | `SingleRequest<PluginAffairGroupDto> arg0` | `SingleResponse<Void>` | 处理Terminate |
| `getExternalIdByAffairId` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 获取外部人员按事项 |

#### PluginMessageAppService

`com.seeyon.cip.plug.api.PluginMessageAppService` · 构件 `cip-manager-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `syncPluginMessage` | `SingleRequest<PluginMessageBatchDto> arg0` | `SingleResponse<PluginMessageResultDto>` | 同步消息Plugin |

#### PluginStatusAppService

`com.seeyon.cip.plug.api.PluginStatusAppService` · 构件 `cip-manager-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectStatusByPlugIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<PlugStatusDto>` | 查询Status按PlugIds |
| `selectStatusByLinkerIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<PlugStatusDto>` | 查询Status按LinkerIds |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 11 个领域服务，下表列**方法数最多的 11 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `UserMappingService` | 41 | 用户映射 · 获取×11 / 查询×8 / 删除×4 |
| `OrgMappingDetailService` | 29 | 映射 · 查询×8 / 获取×6 / 删除×4 |
| `UserMappingDetailService` | 28 | 用户映射 · 获取×10 / 查询×6 / 删除×5 |
| `MappingImpExpService` | 17 | 映射 · 查询×5 / 导入×3 / 新增×2 |
| `AppRegisterService` | 14 | 应用 · 查询×5 / 新增×2 / 检查×2 |
| `MappingConfigService` | 13 | 映射配置 · 查询×7 / 删除×2 / 新增×1 |
| `UserMappingColumnService` | 12 | 用户映射 · 获取×6 / 删除×2 / 新增×1 |
| `UserMappingValueService` | 12 | 用户映射 · 删除×4 / 查询×2 / 新建×1 |
| `CipMenuManageService` | 12 | 菜单管理 · 查询×4 / 修改×2 / 删除×2 |
| `CipTemplateService` | 12 | 模板 · 查询×4 / 删除×2 / 获取×2 |
| `CipTemplateSpiTestService` | 2 | 模板 · 查询×1 / 获取×1 |

## biz 层：事件与监听

事件 1 个 · 监听器 2 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| AppRegister | `AppRegisterEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `LinkerInfoEventListener` | 2 |
| `AppRegisterEventListener` | 1 |

## web 层：Controller

共 4 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 核心实体 CRUD | `LinkerUserMappingController` | 38 |
| 核心实体 CRUD | `AppRegisterController` | 12 |
| 核心实体 CRUD | `CipMenuManageController` | 6 |
| 核心实体 CRUD | `CipTemplateController` | 5 |

## 入参 DTO（字段级）

> 字段来自字节码 `fields`（含继承链，最多 3 层）；**字段名即 JSON 键名**（平台用 Jackson 默认命名，`shortName` 对应库列 `short_name`）。
> 包装类已揭开：`SingleRequest<T>` / `ListResponse<T>` 里看的是 `T` 的字段。
> 等级 `VERIFIED_STATIC_BYTECODE`。全量字段表：`docs/audit/artifacts/dto/DTO-cip-other.md`

本模块 **85** 个入参/返回 DTO，**85** 个能取到字段。Top 12（按出现次数）：

| DTO | 出现 | 字段数 | 关键字段 |
|---|---:|---:|---|
| `FileConvertResultDto` | 5 | 8 | `taskId`, `url`, `storageKey`, `fileName`, `targetFileFormat`, `status`, `errorMsg`, `validate` |
| `CipWarningInfoDto` | 3 | 16 | `id`, `serviceCaption`, `serviceName`, `actionId`, `serviceType`, `actionDesc`, `startTime`, `endTime` |
| `CipWarningInfoDto` | 3 | 16 | `id`, `serviceCaption`, `serviceName`, `actionId`, `serviceType`, `actionDesc`, `startTime`, `endTime` |
| `PluginAffairGroupDto` | 2 | 4 | `capabilityId`, `objectId`, `externalAffairId`, `validate` |
| `AffairDisplayDto` | 2 | 5 | `id`, `state`, `subState`, `receiveMemberId`, `validate` |
| `PlugStatusDto` | 2 | 6 | `plugId`, `plugStatus`, `connectorId`, `status`, `list`, `validate` |
| `QueryRunReqDto` | 2 | 2 | `userIds`, `validate` |
| `MultiTabTransferRequestDto` | 2 | 9 | `taskId`, `url`, `type`, `fileName`, `cookies`, `defaultDomain`, `async`, `fileNamePrefix` |
| `MultiTabFileConvertResultDto` | 2 | 8 | `taskId`, `url`, `storageKeyList`, `fileNameList`, `targetFileFormat`, `status`, `errorMsg`, `validate` |
| `PluginAffairGroupDto` | 2 | 4 | `capabilityId`, `objectId`, `externalAffairId`, `validate` |
| `PlugStatusDto` | 2 | 6 | `plugId`, `plugStatus`, `connectorId`, `status`, `list`, `validate` |
| `PluginAffairBatchDto` | 1 | 6 | `capabilityId`, `linkerCode`, `affairAction`, `idType`, `affairList`, `validate` |

## 落表

> 证据等级：`VERIFIED_STATIC_BYTECODE`（表名出现在本模块 biz jar 的 class 常量池）
> ＋ `LIVE`（同名表已用 `information_schema` 在 `test2` 确认真实存在）。
> 粒度：**类级**。方法级落表未取证 —— 平台不用 MyBatis XML
> （21 个 biz 构件合计只有 9 个 mapper XML / 15 张表），SQL 内联在代码里，
> 方法→表要逐类反编译才能确认。

本模块代码中出现的真实表 **39** 张（来源构件：`cip-convert-biz`、`cip-manager-biz`、`cip-openapi-gateway-biz`）：

| 表名 | 注释 | 出现在几个类 |
|---|---|---:|
| `cip_data_check_config` | 基础插件数据补偿配置 | 3 |
| `cip_ldap_info` | ldap信息 | 3 |
| `cip_org_running_config` | 组织结构同步运行态数据 | 3 |
| `cip_org_sync_config` | 组织同步插件能力的配置详情 | 3 |
| `cip_plugin_capability_info` | 插件能力基本信息表 | 3 |
| `cip_plugin_info` | 插件基本信息表 | 3 |
| `cip_plugin_param_mapping` | 插件参数映射表 | 3 |
| `cip_plugin_timer_job` | 插件定时任务信息表 | 3 |
| `cip_todo_config` | 待办/消息配置详情表 | 3 |
| `cip_applet_version` | 小程序版本管理表 | 2 |
| `cip_convert_transfer_record` | 转换文件记录表 | 2 |
| `cip_escape_rule` | 参数转义规则表 | 2 |
| `cip_event_notify_config` | 开放事件通知配置详情表 | 2 |
| `cip_mobile_plugin` | 移动插件表 | 2 |
| `cip_mobile_swtich_config` | 移动插件开关配置 | 2 |
| `cip_notify_message` | 异步通知消息信息表 | 2 |
| `cip_open_api` | 开放API信息表 | 2 |
| `cip_open_api_category` | 开放API分类表 | 2 |
| `cip_open_api_config` | 开放平台参数设置 | 2 |
| `cip_open_api_doc` | 开放API文档 | 2 |
| `cip_open_api_limit` | 开放API限量设置 | 2 |
| `cip_open_api_log` | 开放API调用日志表 | 2 |
| `cip_open_app` | APP基础信息表 | 2 |
| `cip_open_app_api` | APP的API列表信息 | 2 |
| `cip_open_app_event` | APP的事件订阅表 | 2 |
| `cip_open_app_url` | 应用安全设置，IP白名单 | 2 |
| `cip_open_category_status` | 开放API类目状态表 | 2 |
| `cip_open_dto` | 开放API的DTO信息 | 2 |
| `cip_open_event` | 开放事件信息表 | 2 |
| `cip_open_name_alias` | 开放API参数别名设置 | 2 |
| `cip_open_param_auth` | 开放参数授权配置信息 | 2 |
| `cip_plugin_org_sync_config` | 组织同步配置表（向外） | 2 |
| `cip_sync_data` | 待办/消息具体数据 | 2 |
| `cip_sync_data_detail` | 待办等的详情数据 | 2 |
| `cip_sync_message` | 插件能力已经同步的消息表 | 2 |
| `cip_org_sync_relation` | 三方平台组织id与系统内部组织id对应关系表 | 1 |
| `cip_personnel_card_config` | 人员卡片配置表 | 1 |
| `cip_third_page_component` | 第三方页面组件集成 | 1 |
| `cip_user_sync_relation` | 三方平台用户id与系统内部用户id对应关系表 | 1 |

## 方法级落表（写接口）

> **口径：触及表的上界，不是「只写这张表」。** 证据链是「方法体引用的实体/DAO → 实体类 `@TableName` 字面量」，
> 方法若再做条件分支，实际只写其中一部分。判断影响面用它，判断唯一落点还得看 SQL。
> 等级 `VERIFIED_STATIC_BYTECODE`（引用与表名都来自字节码），**上界推断**部分标 `STATIC_INFERENCE`。

本模块 31 个写方法中，**2** 个解析出触及表：

| 接口#方法 | 触及表 | 依据（引用链） |
|---|---|---|
| `HtmlConvertAppService#transfer` | `cip_convert_transfer_record` | `CipTransferRecordDao=>CipTransferRecord->cip_convert_transfer_record` |
| `HtmlConvertAppService#transferToZip` | `cip_convert_transfer_record` | `CipTransferRecordDao=>CipTransferRecord->cip_convert_transfer_record` |

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

控制器 **53** 个、路由 **467** 条（来源：`cip-convert-web`、`cip-manager-web`、`cip-openapi-gateway-web`）。

> `{id}`、`ids` 这类方法级路径不带类级前缀，拼时必须补上。
> 完整清单（含 java 方法名）：`docs/audit/artifacts/rest/ROUTES-cip-other.md`

| Controller | 类级路径 | 路由 |
|---|---|---:|
| `CapabilityManageController` | `cip-manager/manage` | 39 |
| `SignatureController` | `cip-manager/signature` | 37 |
| `OnlineDocController` | `cip-manager/doc` | 27 |
| `SmsManagerController` | `cip-manager` | 25 |
| `IntelligentMissiveController` | `cip-manager/missive` | 24 |
| `EnterpriseCreditController` | `cip-manager/enterpriseCredit` | 21 |
| `EmailController` | `cip-manager/email` | 20 |
| `VideoMeetingController` | `cip-manager` | 18 |
| `OpenEventController` | `cip-manager/openapi/app/event` | 18 |
| `OcrDataController` | `cip-manager/ocr` | 16 |
| `OpenApiController` | `cip-manager/openapi/api` | 15 |
| `BusinessTripController` | `cip-manager/trip` | 13 |
| `BankpayController` | `cip-manager/bank/pay` | 11 |
| `OpenAppApiController` | `cip-manager/openapi/app/api` | 10 |
| `OrgIntegrationController` | `cip-manager/org` | 10 |
| `PhysicalSealController` | `cip-manager/physicalseal` | 9 |
| `ParamEscapeController` | `cip-manager/data-escape` | 9 |
| `ApiCheckController` | `cip-manager/openapi/api` | 9 |
| `HtmlConvertController` | `cip-convert/html` | 8 |
| `PayController` | `cip-manager/pay` | 8 |
| `CapabiityAppChannelManagerController` | `cip-manager/app-manage` | 8 |
| `OpenAppController` | `cip-manager/openapi/app` | 8 |
| `OpenEventNotifyController` | `cip-manager/openapi/event/notify` | 8 |
| `ForwardLinkerController` | `cip-manager/connector-info` | 7 |
| `VoiceController` | `cip-manager/voice` | 7 |
| `InvoiceDataController` | `cip-manager/invoice` | 7 |
| `CapabilityEnumController` | `cip-manager/capability-enum` | 6 |
| `LocationController` | `cip-manager/location` | 6 |
| `OpenAppUrlController` | `cip-manager/openapi/app/url` | 6 |
| `MerchantController` | `cip-manager/pay` | 5 |
| `OfdController` | `cip-manager/ofd` | 5 |
| `FaceIdController` | `cip-manager/faceId` | 4 |
| `ScheduleController` | `cip-manager/schedule` | 4 |
| `OpenParamAuthController` | `cip-manager/openapi/param/auth` | 4 |
| `OfficeTransController` | `cip-convert/officetrans` | 3 |
| `SmsController` | `cip-manager/sms` | 3 |
| `ForwardMobilePluginApplicationController` | `cip-manager/mobile` | 3 |
| `ForwardMobilePluginAppletController` | `cip-manager/mobile` | 3 |
| `OpenApiLimitController` | `cip-manager/openapi/api/limit` | 3 |
| `AckController` | `healthCheck` | 3 |
| `ForwardLinkerSsoController` | `cip-manager/connector/sso` | 2 |
| `WeatherController` | `cip-manager/weather` | 2 |
| `InvoiceImageController` | `cip-manager/invoice` | 2 |
| `CapabilityAccessLogController` | `cip-manager/accessLog` | 2 |
| `ForwardLinkerEnumController` | `cip-manager/connector-enum` | 1 |
| `ForwardLinkerMetadataController` | `cip-manager/connector-metadata` | 1 |
| `GisController` | `cip-manager/gis` | 1 |
| `CloudConnectController` | `cip-manager/cloud-connect` | 1 |
| `SearchController` | `cip-manager/search` | 1 |
| `OfflineMessageController` | `cip-manager/offline-message` | 1 |
| `ResumeController` | `cip-manager/resume` | 1 |
| `CensorController` | `cip-manager/censor` | 1 |
| `SsoController` | `cip-manager/plug/sso` | 1 |

前 15 条（其余见明细）：

| 方法 | 全路径 |
|---|---|
| `PostMapping` | `/service/cip-manager/org/integration/card/info` |
| `PostMapping` | `/service/cip-manager/org/integration/card/update` |
| `PostMapping` | `/service/cip-manager/org/integration/card/service-type-info` |
| `GetMapping` | `/service/cip-manager/org/integration/card/js-address/{serviceCode}` |
| `PostMapping` | `/service/cip-manager/org/integration/card/show-info` |
| `PostMapping` | `/service/cip-manager/org/integration/default/card-info` |
| `PostMapping` | `/service/cip-manager/org/integration/card/run-info` |
| `PostMapping` | `/service/cip-manager/org/integration/card/tn-info` |
| `PostMapping` | `/service/cip-manager/org/integration/card/show-custom-avatar` |
| `PostMapping` | `/service/cip-manager/org/integration/default/card-custom-avatar-info` |
| `PostMapping` | `/service/cip-manager/app-manage/app-channel-manage/app-enable` |
| `PostMapping` | `/service/cip-manager/app-manage/app-channel-manage/query-app` |
| `PostMapping` | `/service/cip-manager/app-manage/app-channel-manage/create-app` |
| `PostMapping` | `/service/cip-manager/app-manage/app-channel-manage/delete-app/{id}` |
| `PostMapping` | `/service/cip-manager/app-manage/app-channel-manage/update-app` |

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 23 接口 / 94 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 11 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 1 事件 / 2 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 4 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径（467 条） | Controller 字节码注解 | `VERIFIED_STATIC_BYTECODE` |
| REST 真机验证 | 198/198 条安全路由命中（100%） | `LIVE` |
| 落表（42 张表，类级） | class 常量池 + `information_schema` | `VERIFIED_STATIC_BYTECODE` + `LIVE` |
| 方法级落表 | 未取证（SQL 内联，需逐类反编译） | `UNVERIFIED` |
