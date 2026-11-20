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

## 落表

⚠️ **UNVERIFIED** —— 字节码索引不含 SQL/表名，本文件不写推测的表名。

取证路径（三条，任选其一，务必留证据）：

1. **jar 内 mapper**：`organization-biz` 里 `*.xml` / `*Mapper.java`
2. **库结构**：连 test2 的 MySQL 查 `information_schema.columns` 里 `tb_org_%`
3. **运行态**：开 SQL 日志跑一次写操作，看真实表名

在拿到上述证据前，本文件对「落哪张表」保持空。

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 23 接口 / 94 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 11 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 1 事件 / 2 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 4 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径 | 未取证 | `UNVERIFIED` |
| 落表 | 未取证 | `UNVERIFIED` |
