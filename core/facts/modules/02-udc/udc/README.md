# 低代码平台（udc）

## 一句话

`com.seeyon.udc` 域的**可调用接口面**：18 个构件、3,345 个类、67 个 facade 接口 / 555 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `udc-biz` | biz | 1,855 |
| `udc-common` | common | 424 |
| `udc-plugin-api` | api | 307 |
| `udc-dataflow` | 其他 | 224 |
| `udc-extend` | 其他 | 82 |
| `udc-facade` | facade | 66 |
| `udc-cicd` | 其他 | 59 |
| `udc-portal` | 其他 | 58 |
| `udc-web` | web | 54 |
| `udc-cdpbi` | 其他 | 49 |
| `udc-bpm` | 其他 | 46 |
| `udc-upgrade` | 其他 | 44 |
| `udc-user` | 其他 | 37 |
| `udc-app-common` | common | 15 |
| `udc-m5` | 其他 | 11 |
| `udc-cip` | 其他 | 10 |
| `boot-starter-extmetadata` | 其他 | 3 |
| `udc-affair` | 其他 | 1 |
| **合计** | | **3,345** |

## 二、分层规律（写代码前必读）

`com.seeyon.udc` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

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

## facade 层：67 个接口 / 555 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.udc.api` | 63 | 497 |
| `com.seeyon.udc.common.api` | 1 | 1 |
| `com.seeyon.udc.log.api` | 1 | 3 |
| `com.seeyon.udc.upgrade.api` | 2 | 54 |
| **合计** | **67** | **555** |

### `com.seeyon.udc.api`

#### AppCollaborationAppService

`com.seeyon.udc.api.AppCollaborationAppService` · 构件 `udc-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectCollaborativeAppNames` | `—` | `ListResponse<String>` | 查询应用名称Collaborative |
| `selectCollaborativeGuid` | `—` | `ListResponse<Long>` | 查询CollaborativeGuid |
| `handoverApp` | `SingleRequest<AppHanoverDto> arg0` | `void` | 移交应用 |
| `batchHandoverApp` | `SingleRequest<AppBatchHandoverDto> arg0` | `void` | 移交应用 |
| `selectAppMemberInfoListByAppIdList` | `SingleRequest<List<Long>> arg0` | `ListResponse<AppMemberInfoDto>` | 列表查询应用成员按应用 |

#### ApplicationAppService

`com.seeyon.udc.api.ApplicationAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<ApplicationDto> arg0` | `SingleResponse<Long>` | 新建应用 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<ApplicationDto>` | 分页查询应用按条件 |
| `selectAppPageByConditions` | `PageRequest arg0` | `PageResponse<ApplicationDto>` | 分页查询应用按条件 |
| `selectAppPageByConditionsWithVersion` | `PageRequest arg0` | `PageResponse<ApplicationMultiVersionDto>` | 分页查询应用按条件版本 |
| `selectAppPageByGuid` | `PageRequest arg0` | `PageResponse<SingleAppVersionInfoDto>` | 分页查询应用按Guid |
| `selectTemplateAppPageByConditions` | `PageRequest arg0` | `PageResponse<ApplicationDto>` | 分页查询模板应用按条件 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<ApplicationDto>` | 查询应用按 id |
| `selectByGuid` | `SingleRequest<Long> arg0` | `ListResponse<ApplicationDto>` | 查询应用按Guid |
| `selectByIdUseAuth` | `SingleRequest<Long> arg0` | `SingleResponse<ApplicationDto>` | 查询应用按认证 |
| `selectDetailById` | `SingleRequest<Long> arg0` | `SingleResponse<ApplicationDto>` | 查询Detail按 id |
| `selectPlatformVersion` | `—` | `ListResponse<String>` | 查询版本Platform |
| `selectPlatformVersionMap` | `—` | `SingleResponse<Map>` | 查询版本PlatformMap |
| `selectHistoryById` | `SingleRequest<Long> arg0` | `ListResponse<ApplicationHistoryVersionDto>` | 查询History按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<ApplicationDto>` | 查询应用按 ids |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `deleteByGuid` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按Guid（SingleRequest） |
| `deleteFormAppByGuid` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除表单应用按Guid |
| `update` | `SingleRequest<ApplicationDto> arg0` | `SingleResponse<Integer>` | 修改应用 |
| `updateNoEvents` | `SingleRequest<ApplicationDto> arg0` | `SingleResponse<Integer>` | 修改NoEvents |
| `updateCaptionForAllVersion` | `SingleRequest<ApplicationDto> arg0` | `SingleResponse<Integer>` | 全部修改版本CaptionFor |
| `createDepApp` | `SingleRequest<DependentApplicationDto> arg0` | `SingleResponse<Long>` | 新建应用Dep |
| `createDepAppBatch` | `SingleRequest<List<DependentApplicationDto>> arg0` | `SingleResponse<Integer>` | 批量新建应用Dep |
| `updateDepApp` | `SingleRequest<DependentApplicationDto> arg0` | `SingleResponse<Integer>` | 修改应用Dep |
| `updateBatchDepAppVersion` | `SingleRequest<List<DependentUpdateDto>> arg0` | `SingleResponse<Integer>` | 批量修改应用版本Dep |
| `updateDepAppBatch` | `SingleRequest<List<DependentApplicationDto>> arg0` | `SingleResponse<Integer>` | 批量修改应用Dep |
| `deleteDepAppsByAppId` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除DepApps按应用 |
| `deleteDepAppById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除应用Dep按 id |
| `deleteDepAppsByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除DepApps按 ids |
| `selectDepAppListByAppId` | `SingleRequest<Long> arg0` | `ListResponse<DependentApplicationDto>` | 列表查询应用Dep按应用 |
| `selectDetectionListByAppId` | `SingleRequest<Long> arg0` | `ListResponse<ConsistenceDetectionDto>` | 列表查询检测按应用 |
| `selectSummaryDetectionByAppId` | `SingleRequest<Long> arg0` | `SingleResponse<DetectionMessageDto>` | 查询摘要检测按应用 |
| `detectionByAppId` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 检测按应用（SingleRequest） |
| `runDetectionState` | `SingleRequest<Long> arg0` | `SingleResponse<DetectionMessageDto>` | 运行检测State |
| `selectFrontDetectionByAppId` | `SingleRequest<Long> arg0` | `SingleResponse<DetectionMessageDto>` | 查询检测Front按应用 |
| `frontDetectionByAppId` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 检测按应用（SingleRequest） |
| `downloadApp` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | SPI 扩展点：应用（框架回调） |
| `selectByAppNames` | `SingleRequest<List<String>> arg0` | `ListResponse<ApplicationDto>` | 查询应用按应用名称 |
| `copyApp` | `SingleRequest<ApplicationCopyDto> arg0` | `SingleResponse<Long>` | 复制应用 |
| `saveAsTemplate` | `SingleRequest<ApplicationCopyDto> arg0` | `SingleResponse<Long>` | 保存模板As |
| `createFromTemplate` | `SingleRequest<TemplateApplicationDto> arg0` | `SingleResponse<Long>` | 新建模板From |
| `renewalAppEditingTime` | `Long arg0` | `SingleResponse<Boolean>` | 续期应用EditingTime |
| `isExclusive` | `Long arg0` | `SingleResponse<Boolean>` | 判断Exclusive |
| `selectDesignDataChange` | `List<Long> arg0` | `ListResponse<AppDesignDto>` | 查询数据DesignChange |
| `checkDesignModifiedAfterLastRelease` | `Long arg0` | `SingleResponse<AppDesignDto>` | 检查发布版本DesignModifiedAfterLast |
| `saveAsNewDesign` | `Long arg0` | `SingleResponse<Long>` | 保存AsNewDesign |
| `saveAsNormalNewDesign` | `ApplicationSaveAsDto arg0` | `SingleResponse<Long>` | 保存AsNormalNewDesign |
| `deployNormal` | `SingleRequest<DeployNormalDto> arg0` | `SingleResponse<DeployParamDto>` | 部署Normal |
| `deployForm` | `SingleRequest<DeployFormDto> arg0` | `SingleResponse<DeployResultDto>` | 部署表单 |
| `selectMultiVersion` | `SingleRequest<VersionSearchDto> arg0` | `ListResponse<MultiVersionDto>` | 查询版本Multi |
| `selectDepByCondition` | `ListRequest arg0` | `ListResponse<DependentApplicationDto>` | 查询Dep按条件 |
| `importAppZipIntoCurrentApp` | `Long arg0` | `SingleResponse<String>` | 导入应用当前ZipInto |
| `importAppOnlineIntoCurrentApp` | `Long arg0` | `SingleResponse<String>` | 导入应用在线当前Into |

#### ApplicationManagerAppService

`com.seeyon.udc.api.ApplicationManagerAppService` · 构件 `udc-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<ApplicationDto> arg0` | `SingleResponse<Long>` | 新建应用，返回 appId |
| `createOnlyPageApplication` | `SingleRequest<CreateOnlyPageApplicationDto> arg0` | `ListResponse<OnlyPageApplicationDto>` | 分页新建应用Only |
| `createNewLayoutAfterCall` | `SingleRequest<NewLayoutCreateAfterCallDto> arg0` | `SingleResponse<Void>` | 新建布局NewAfterCall |
| `copyOnlyPageApp` | `SingleRequest<ApplicationCopyDto> arg0` | `SingleResponse<OnlyPageApplicationDto>` | 分页复制应用Only |
| `upgradeOnlyPageApplication` | `SingleRequest<OnlyPageApplicationUpgradeDto> arg0` | `SingleResponse<OnlyPageApplicationUpgradeResultDto>` | 分页升级应用Only |
| `createIntegrationApplication` | `SingleRequest<IntegrationApplicationDto> arg0` | `SingleResponse<IntegrationApplicationDto>` | 新建应用Integration |
| `createLayoutApplication` | `SingleRequest<LayoutApplicationDto> arg0` | `SingleResponse<LayoutApplicationDto>` | 新建布局应用 |
| `copyLayoutApp` | `SingleRequest<ApplicationCopyDto> arg0` | `SingleResponse<LayoutApplicationDto>` | 复制布局应用 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<ApplicationDto>` | 查询应用按 id |
| `update` | `SingleRequest<ApplicationDto> arg0` | `SingleResponse<Integer>` | 修改应用 |
| `updateWithMember` | `SingleRequest<ApplicationWithMemberDto> arg0` | `SingleResponse<Integer>` | 修改成员With |
| `updateAppCategoryBatch` | `SingleRequest<AppCategoryDto> arg0` | `SingleResponse<Integer>` | 批量修改应用分类 |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `copyApp` | `SingleRequest<ApplicationCopyDto> arg0` | `SingleResponse<ApplicationDto>` | 复制应用（同步） |
| `copyAppAsync` | `SingleRequest<ApplicationCopyDto> arg0` | `SingleResponse<String>` | 复制应用（异步，返回任务 key） |
| `createMember` | `SingleRequest<MemberAddDto> arg0` | `SingleResponse<Integer>` | 新建成员 |
| `selectCollaborationRecordsByAppId` | `SingleRequest<Long> arg0` | `ListResponse<AppCollaborationDto>` | 查询CollaborationRecords按应用 |
| `deleteMemberById` | `SingleRequest<Long> arg0` | `SingleResponse<Void>` | 删除成员按 id |
| `handoverApp` | `SingleRequest<AppHanoverDto> arg0` | `SingleResponse<Integer>` | 移交应用（换负责人） |
| `createReturnDto` | `SingleRequest<ApplicationDto> arg0` | `SingleResponse<ApplicationDto>` | 新建ReturnDto |
| `deleteFormAppByGuid` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除表单应用按Guid |
| `deleteFormAppByName` | `SingleRequest<String> arg0` | `SingleResponse<Integer>` | 删除表单应用按名称 |
| `deployNormal` | `SingleRequest<DeployNormalDto> arg0` | `SingleResponse<DeployParamDto>` | ★部署（设计态→运行态，全量），入参 DeployNormalDto |
| `deployForm` | `SingleRequest<DeployFormDto> arg0` | `SingleResponse<DeployResultDto>` | ★部署表单类应用，入参 DeployFormDto |
| `selectLatestDesignAppByGuid` | `SingleRequest<Long> arg0` | `SingleResponse<ApplicationDto>` | 按 guid 取最新设计版本 |
| `selectLatestDesignAppWithMemberByGuid` | `SingleRequest<Long> arg0` | `SingleResponse<ApplicationWithMemberDto>` | 查询应用成员LatestDesignWith按Guid |
| `selectAppNameAndIdMapByAppNames` | `SingleRequest<List<String>> arg0` | `SingleResponse<Map<String, Long>>` | 查询应用名称AndMap按应用名称 |
| `selectDesignAppByGuid` | `SingleRequest<Long> arg0` | `ListResponse<ApplicationDto>` | 查询应用Design按Guid |
| `selectAppByUser` | `SingleRequest<ApplicationSearchDto> arg0` | `PageResponse<ApplicationDto>` | 查询应用按用户 |
| `selectAppByUserAndGuid` | `SingleRequest<ApplicationSearchDto> arg0` | `ListResponse<ApplicationDto>` | 查询应用按用户 |
| `selectAppByUserAndId` | `SingleRequest<ApplicationSearchDto> arg0` | `SingleResponse<ApplicationDto>` | 查询应用按用户 |
| `exportAppInfos` | `SingleRequest<AppInfoExportDto> arg0` | `ListResponse<ApplicationExportDto>` | 导出应用Infos |
| `selectAppDeployState` | `SingleRequest<QueryFormInfoDto> arg0` | `SingleResponse<AppVersionDto>` | 查应用部署状态 |
| `downloadApp` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 导出应用（同步） |
| `downloadAppAsync` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 导出应用（异步） |
| `downloadAppByHost` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | SPI 扩展点：应用（框架回调） |
| `importApp` | `SingleRequest<String> arg0` | `SingleResponse<Long>` | 导入应用，返回 appId |
| `importAppWithDto` | `SingleRequest<ApplicationImportDto> arg0` | `SingleResponse<Long>` | 导入应用WithDto |
| `batchDownloadAppAsync` | `SingleRequest<List<Long>> arg0` | `SingleResponse<String>` | 下载应用Async |
| `batchTransferAppAsync` | `SingleRequest<List<String>> arg0` | `SingleResponse<String>` | 转移应用Async |
| `importFormValidate` | `String arg0` | `ListResponse<ImportValidationInfo>` | 导入表单Validate |
| `importFormApp` | `String arg0` | `SingleResponse<String>` | 导入表单应用 |
| `transfer` | `SingleRequest<String> arg0` | `SingleResponse<Long>` | 转移（SingleRequest） |
| `transfer` | `SingleRequest<String> arg0` | `SingleResponse<Long>` | 转移（SingleRequest） |
| `getShelfDepend` | `SingleRequest<ShelfDependRequestDto> arg0` | `SingleResponse<ShelfDependResponseDto>` | 获取ShelfDepend |
| `getDependsByAppId` | `SingleRequest<Long> arg0` | `ListResponse<DependentApplicationDto>` | 查应用被谁依赖（删除/改动的风险面） |
| `getDependsLayoutAppInfo` | `SingleRequest<BaseApplicationSearchDto> arg0` | `ListResponse<DependentApplicationDto>` | 获取布局应用Depends |
| `shelfCompatibilityLock` | `SingleRequest<ShelfCompatibilityLockRequestDto> arg0` | `SingleResponse<ShelfCompatibilityLockResultDto>` | 加锁ShelfCompatibilityLock |
| `migrationApp` | `SingleRequest<DeployFerryDto> arg0` | `SingleResponse<Long>` | 应用迁移（另一个环境/租户） |
| `selectDeployRecordById` | `SingleRequest<Long> arg0` | `ListResponse<DeployRecordDto>` | 查部署记录 |
| `selectAppPageByConditions` | `PageRequest arg0` | `PageResponse<ApplicationDto>` | 分页查询应用按条件 |
| `createEntity` | `SingleRequest<EntityDto> arg0` | `SingleResponse<Long>` | 新建实体 |
| `operateBatch` | `SingleRequest<List<AttributeGroupDto>> arg0` | `ListResponse<AttributeGroupDto>` | 批量操作应用（上架/下架/删除等，按操作类型） |

#### ApplicationShelfService

`com.seeyon.udc.api.ApplicationShelfService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `module` | `—` | `String` | 应用上架：按模块维度上架 |
| `updateStateAfterAppShelf` | `ApplicationDto arg0` | `void` | 修改应用StateAfterShelf |

#### AsyncAppService

`com.seeyon.udc.api.AsyncAppService` · 构件 `udc-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createLayoutApplicationAsync` | `SingleRequest<LayoutApplicationDto> arg0` | `SingleResponse<String>` | 新建布局应用Async |
| `createOnlyPageApplicationAsync` | `SingleRequest<CreateOnlyPageApplicationDto> arg0` | `SingleResponse<String>` | 分页新建应用OnlyAsync |
| `upgradeOnlyPageApplicationAsync` | `SingleRequest<OnlyPageApplicationUpgradeDto> arg0` | `SingleResponse<String>` | 分页升级应用OnlyAsync |
| `copyLayoutAppAsync` | `SingleRequest<ApplicationCopyDto> arg0` | `SingleResponse<String>` | 复制布局应用Async |
| `copyOnlyPageAppAsync` | `SingleRequest<ApplicationCopyDto> arg0` | `SingleResponse<String>` | 分页复制应用OnlyAsync |
| `transferAsync` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<String>` | 转移Async |
| `getRequestStatus` | `SingleRequest<String> arg0` | `SingleResponse<RequestStatusDto>` | 获取RequestStatus |

#### AttributeAppService

`com.seeyon.udc.api.AttributeAppService` · 构件 `udc-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<AttributeDto> arg0` | `SingleResponse<Long>` | 新建字段 |
| `createBatch` | `SingleRequest<List<AttributeDto>> arg0` | `SingleResponse<Integer>` | 批量新建（SingleRequest） |
| `createBatch4System` | `SingleRequest<List<AttributeDto>> arg0` | `SingleResponse<Integer>` | 批量建系统内置字段（跳过用户字段校验） |
| `update` | `SingleRequest<AttributeDto> arg0` | `SingleResponse<Integer>` | 修改字段 |
| `updateBatch` | `SingleRequest<List<AttributeDto>> arg0` | `SingleResponse<Integer>` | 批量修改（SingleRequest） |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<AttributeDto>` | 查询字段按 id |
| `selectPageByCondition` | `PageRequest arg0` | `PageResponse<AttributeDto>` | 分页查询字段按条件 |
| `selectListByCondition` | `ListRequest arg0` | `ListResponse<AttributeDto>` | 列表查询字段按条件 |
| `selectListByTerm` | `SingleRequest<Long> arg0` | `ListResponse<AttributeDto>` | 列表查询字段按Term |
| `selectAllAttributeByEntityId` | `SingleRequest<Long> arg0` | `ListResponse<AttributeDto>` | 查实体下全部字段 |
| `selectEntityAttributeList` | `ListRequest arg0` | `ListResponse<AttributeDto>` | 列表查询实体字段 |
| `selectByAttributeSetId` | `SingleRequest<Long> arg0` | `ListResponse<AttributeDto>` | 查询字段按字段 |
| `selectParentEnumAttributes` | `ListRequest arg0` | `ListResponse<AttributeDto>` | 查询上级枚举Attributes |

#### AttributeGroupAppService

`com.seeyon.udc.api.AttributeGroupAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<AttributeGroupDto> arg0` | `SingleResponse<Long>` | 新建字段分组 |
| `update` | `SingleRequest<AttributeGroupDto> arg0` | `SingleResponse<Integer>` | 修改字段分组 |
| `cancel` | `SingleRequest<AttributeGroupDto> arg0` | `SingleResponse<Integer>` | 取消字段分组 |
| `remove` | `SingleRequest<AttributeGroupDto> arg0` | `SingleResponse<Integer>` | 移除字段分组 |
| `swap` | `SingleRequest<List<AttributeGroupDto>> arg0` | `SingleResponse<Void>` | 交换两个字段分组的顺序 |
| `operateBatch` | `SingleRequest<List<AttributeGroupDto>> arg0` | `ListResponse<AttributeGroupDto>` | 批量操作字段分组 |
| `selectListByEntityId` | `SingleRequest<Long> arg0` | `ListResponse<AttributeGroupDto>` | 列表查询字段分组按实体 |

#### AttributeSetAppService

`com.seeyon.udc.api.AttributeSetAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<AttributeSetDto> arg0` | `SingleResponse<Long>` | 新建字段 |
| `createBatch` | `SingleRequest<List<AttributeSetDto>> arg0` | `SingleResponse<Integer>` | 批量新建（SingleRequest） |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `update` | `SingleRequest<AttributeSetDto> arg0` | `SingleResponse<Integer>` | 修改字段 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<AttributeSetDto>` | 查询字段按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<AttributeSetDto>` | 查询字段按 ids |
| `selectByName` | `SingleRequest<Long> arg0` | `SingleResponse<AttributeSetDto>` | 查询字段按名称 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<AttributeSetDto>` | 列表查询字段按条件 |
| `selectListByAppId` | `SingleRequest<Long> arg0` | `ListResponse<AttributeSetDto>` | 列表查询字段按应用 |
| `selectListByNames` | `SingleRequest<Long> arg0` | `ListResponse<AttributeSetDto>` | 列表查询字段按名称 |
| `selectListByNamesWithAttributes` | `SingleRequest<Boolean> arg0` | `ListResponse<AttributeDto>` | 列表查询字段按名称 |
| `selectListByTerm` | `SingleRequest<Long> arg0` | `ListResponse<AttributeSetDto>` | 列表查询字段按Term |

#### ConsistenceDetectionAppService

`com.seeyon.udc.api.ConsistenceDetectionAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `updateDetection` | `SingleRequest<Class<? extends BaseEntity>> arg0` | `void` | 修改检测 |
| `updateDetection4Dto` | `SingleRequest<Class<? extends BaseEntity>> arg0` | `void` | 修改Detection4Dto |
| `selectDetectionListByAppId` | `SingleRequest<Long> arg0` | `ListResponse<ConsistenceDetectionDto>` | 列表查询检测按应用 |
| `deleteDetection` | `SingleRequest<Class<? extends BaseEntity>> arg0` | `void` | 删除检测 |

#### DataTransferObjectAppService

`com.seeyon.udc.api.DataTransferObjectAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<DataTransferObjectDto> arg0` | `SingleResponse<Long>` | 新建TransferObject |
| `createDtoWithAttrs` | `SingleRequest<DataTransferObjectDto> arg0` | `SingleResponse<Map<String, Object>>` | 新建自定义对象并同时建字段 |
| `update` | `SingleRequest<DataTransferObjectDto> arg0` | `SingleResponse<Integer>` | 修改TransferObject |
| `updateDtoWithAttrs` | `SingleRequest<DataTransferObjectDto> arg0` | `SingleResponse<Integer>` | 修改DtoWithAttrs |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<DataTransferObjectDto>` | 查询TransferObject按 id |
| `selectDtoWithAttrsById` | `SingleRequest<Long> arg0` | `SingleResponse<DataTransferObjectDto>` | 查询DtoWithAttrs按 id |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<DataTransferObjectDto>` | 分页查询TransferObject按条件 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<DataTransferObjectDto>` | 列表查询TransferObject按条件 |
| `createDtoWithAttrsAndRefDtos` | `SingleRequest<List<DataTransferObjectDto>> arg0` | `SingleResponse<Long>` | 新建 DTO 并建字段 + 引用关系 |
| `createDtoWithAttrs4EntityEvent` | `SingleRequest<EventAndDataDto> arg0` | `SingleResponse<Long>` | 新建实体DtoWithAttrs4Event |
| `updateDtoWithAttrs4EntityEvent` | `SingleRequest<EventAndDataDto> arg0` | `void` | 修改实体DtoWithAttrs4Event |
| `updateDtoWithAttrsAndRefDtos` | `SingleRequest<List<DataTransferObjectDto>> arg0` | `SingleResponse<Long>` | 修改DtoWithAttrsAndRefDtos |
| `selectDtoWithAttrsAndRefDtos` | `SingleRequest<Long> arg0` | `ListResponse<DataTransferObjectDto>` | 读 DTO 全量（含字段+引用） |
| `selectListBySourceId` | `SingleRequest<Long> arg0` | `ListResponse<DataTransferObjectDto>` | 列表查询TransferObject按SourceId |
| `selectMicroFlowCustomDtoByAppId` | `SingleRequest<Long> arg0` | `ListResponse<DataTransferObjectDto>` | 查询MicroFlowCustomDto按应用 |
| `selectAllByMicroFlowId` | `SingleRequest<Long> arg0` | `ListResponse<DataTransferObjectDto>` | 查某微流程用到的全部 DTO |
| `deleteDtoWithAttrsAndRefDtos` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除DtoWithAttrsAndRefDtos |
| `checkExists` | `SingleRequest<List<DataTransferObjectDto>> arg0` | `SingleResponse<Boolean>` | 检查Exists |
| `searchSelectableDtoList` | `SingleRequest<DataTransferObjectQueryDto> arg0` | `ListResponse<DataTransferObjectDto>` | 微流程搭节点时可选的自定义对象列表 |
| `searchPageMicroFlowDtos` | `PageRequest arg0` | `PageResponse<DataTransferObjectDto>` | 分页搜索MicroFlowDtos |
| `check` | `Long arg0` | `void` | 检查（Long） |

#### DataTypeAppService

`com.seeyon.udc.api.DataTypeAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getAll` | `—` | `ListResponse<DataTypeDto>` | 全部获取类型 |
| `selectBaseDataTypes` | `—` | `ListResponse<DataTypeDto>` | 查询数据Types |
| `selectParameterDataTypes` | `—` | `ListResponse<DataTypeDto>` | 查询参数数据Types |
| `selectDataTypeByName` | `SingleRequest<String> arg0` | `SingleResponse<DataTypeDto>` | 查询数据类型按名称 |
| `selectDataTypeByAppId` | `SingleRequest<Long> arg0` | `ListResponse<DataTypeDto>` | 查询数据类型按应用 |
| `selectDataTypeByParams` | `SingleRequest<DataTypeQueryParamDto> arg0` | `SingleResponse<Map<String, List<DataTypeDisplayDto>>>` | 查询数据类型按Params |
| `selectScalabilityDataType` | `SingleRequest<Long> arg0` | `ListResponse<DataTypeDto>` | 查询数据类型Scalability |

#### DeployBeforeService

`com.seeyon.udc.api.DeployBeforeService` · 构件 `udc-plugin-api` · extends `Condition`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `handle` | `AppContext arg0` | `boolean` | 部署前钩子（返回 false 中断部署） |

#### DeployFinishService

`com.seeyon.udc.api.DeployFinishService` · 构件 `udc-plugin-api` · extends `Condition`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `callback` | `DeployCallbackDto arg0` | `boolean` | 部署完成钩子（部署后回调） |

#### DesignMetadataQueryAppService

`com.seeyon.udc.api.DesignMetadataQueryAppService` · 构件 `udc-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectServiceMetadata` | `SingleRequest<SearchDesignMetadataDto> arg0` | `SingleResponse<ServiceMetadataDto>` | 查询扩展属性Service |
| `selectEntityMetadata` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<EntityMetadataDto>` | 查询实体扩展属性 |
| `selectEntityMetadataExcludeBoot` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<EntityMetadataDto>` | 查询实体扩展属性ExcludeBoot |
| `selectEntityMetadataByFullName` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `SingleResponse<EntityMetadataDto>` | 查询实体扩展属性按名称 |
| `selectEntityMetadataByFullNames` | `SingleRequest<SearchDesignMetadataByFullNamesDto> arg0` | `ListResponse<EntityMetadataDto>` | 查询实体扩展属性按名称 |
| `selectAggMetadata` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<AggMetadataDto>` | 查询扩展属性Agg |
| `selectAggMetadataExcludeBoot` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<AggMetadataDto>` | 查询扩展属性AggExcludeBoot |
| `selectAggMetadataByFullName` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `SingleResponse<AggMetadataDto>` | 查询扩展属性Agg按名称 |
| `selectAggMetadataByFullNames` | `SingleRequest<SearchDesignMetadataByFullNamesDto> arg0` | `ListResponse<AggMetadataDto>` | 查询扩展属性Agg按名称 |
| `selectEntityListByAgg` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `ListResponse<EntityMetadataDto>` | 列表查询实体按Agg |
| `selectRestApiMetadata` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<RestApiMetadataDto>` | 查询RESTAPI扩展属性 |
| `selectRestApiMetadataExcludeBoot` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<RestApiMetadataDto>` | 查询RESTAPI扩展属性ExcludeBoot |
| `selectRestApiMetadataByFullNames` | `SingleRequest<SearchDesignMetadataByFullNamesDto> arg0` | `ListResponse<RestApiMetadataDto>` | 查询RESTAPI扩展属性按名称 |
| `selectRestApiMetadataByFullName` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `SingleResponse<RestApiMetadataDto>` | 查询RESTAPI扩展属性按名称 |
| `selectDtoMetadata` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<DtoMetadataDto>` | 查询扩展属性Dto |
| `selectDtoMetadataExcludeBoot` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<DtoMetadataDto>` | 查询扩展属性DtoExcludeBoot |
| `selectDtoMetadataByFullNames` | `SingleRequest<SearchDesignMetadataByFullNamesDto> arg0` | `ListResponse<DtoMetadataDto>` | 查询扩展属性Dto按名称 |
| `selectDtoMetadataByFullName` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `SingleResponse<DtoMetadataDto>` | 查询扩展属性Dto按名称 |
| `selectEnumMetadata` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<EnumMetadataDto>` | 查询枚举扩展属性 |
| `selectEnumMetadataByFullNames` | `SingleRequest<SearchDesignMetadataByFullNamesDto> arg0` | `ListResponse<EnumMetadataDto>` | 查询枚举扩展属性按名称 |
| `selectEnumMetadataByFullName` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `SingleResponse<EnumMetadataDto>` | 查询枚举扩展属性按名称 |
| `selectAggEntityMetadata` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<AggEntityMetadataDto>` | 查询实体扩展属性Agg |
| `selectAggEntityMetadataByCondition` | `SingleRequest<UdcAppMetaDataQueryDto> arg0` | `ListResponse<AggEntityMetadataDto>` | 查询实体扩展属性Agg按条件 |
| `selectAggEntityMetadataExcludeBoot` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<AggEntityMetadataDto>` | 查询实体扩展属性AggExcludeBoot |
| `selectAggEntityMetadataByFullName` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `SingleResponse<AggEntityMetadataDto>` | 查询实体扩展属性Agg按名称 |
| `selectAggEntityMetadataByFullNames` | `SingleRequest<SearchDesignMetadataByFullNamesDto> arg0` | `ListResponse<AggEntityMetadataDto>` | 查询实体扩展属性Agg按名称 |
| `selectOpenApiMetadata` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<OpenApiMetadataDto>` | 查询API扩展属性Open |
| `selectOpenApiMetadataByFullNames` | `SingleRequest<SearchDesignMetadataByFullNamesDto> arg0` | `ListResponse<OpenApiMetadataDto>` | 查询API扩展属性Open按名称 |
| `selectOpenApiMetadataByFullName` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `SingleResponse<OpenApiMetadataDto>` | 查询API扩展属性Open按名称 |
| `selectAppServiceMetadata` | `SingleRequest<String> arg0` | `ListResponse<AppServiceMetadataDto>` | 查询应用扩展属性Service |
| `selectAppServiceMetadataExcludeBoot` | `SingleRequest<String> arg0` | `ListResponse<AppServiceMetadataDto>` | 查询应用扩展属性ServiceExcludeBoot |
| `selectAppServiceMetadataByFullNames` | `SingleRequest<SearchDesignMetadataByFullNamesDto> arg0` | `ListResponse<AppServiceMetadataDto>` | 查询应用扩展属性Service按名称 |
| `selectAppServiceMetadataByFullName` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `SingleResponse<AppServiceMetadataDto>` | 查询应用扩展属性Service按名称 |
| `selectMqMetadata` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<MqMetadataDto>` | 查询扩展属性Mq |
| `selectMqMetadataExcludeBoot` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<MqMetadataDto>` | 查询扩展属性MqExcludeBoot |
| `selectMqMetadataByFullNames` | `SingleRequest<SearchDesignMetadataByFullNamesDto> arg0` | `ListResponse<MqMetadataDto>` | 查询扩展属性Mq按名称 |
| `selectMqMetadataByFullName` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `SingleResponse<MqMetadataDto>` | 查询扩展属性Mq按名称 |
| `selectEntityRelationDtoMetadata` | `SingleRequest<String> arg0` | `ListResponse<DtoMetadataDto>` | 查询实体扩展属性RelationDto |
| `selectEntityRelationDtoMetadataExcludeBoot` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<DtoMetadataDto>` | 查询实体扩展属性RelationDtoExcludeBoot |
| `selectDtoMetadataByEntityFullNames` | `SingleRequest<SearchDesignMetadataByFullNamesDto> arg0` | `ListResponse<DtoMetadataDto>` | 查询扩展属性Dto按实体名称 |
| `selectDtoMetadataByEntityFullName` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `SingleResponse<DtoMetadataDto>` | 查询扩展属性Dto按实体名称 |
| `selectAppServiceMetadataByDto` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `SingleResponse<AppServiceMetadataDto>` | 查询应用扩展属性Service按Dto |
| `selectReferMetadataByEntity` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `ListResponse<ReferMetadataDto>` | 查询扩展属性Refer按实体 |
| `selectReferAndAppMetadataByEntity` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `SingleResponse<ReferAndAppMetadataDto>` | 查询应用扩展属性ReferAnd按实体 |
| `selectBasicDataEntityMetadata` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<EntityMetadataDto>` | 查询数据实体扩展属性Basic |
| `selectBasicDataEntityMetadataByFullName` | `SingleRequest<SearchDesignMetadataByFullNameDto> arg0` | `SingleResponse<EntityMetadataDto>` | 查询数据实体扩展属性Basic按名称 |
| `selectBasicDataEntityMetadataByFullNames` | `SingleRequest<SearchDesignMetadataByFullNamesDto> arg0` | `ListResponse<EntityMetadataDto>` | 查询数据实体扩展属性Basic按名称 |
| `selectPageMetadataList` | `SingleRequest<SearchDesignMetadataDto> arg0` | `ListResponse<PageMetadataDto>` | 分页列表查询扩展属性 |
| `selectEnumMetadataList` | `SingleRequest<List<Long>> arg0` | `ListResponse<EnumMetadataDto>` | 列表查询枚举扩展属性 |

#### DtoAttributeAppService

`com.seeyon.udc.api.DtoAttributeAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<DtoAttributeDto> arg0` | `SingleResponse<Long>` | 新建字段 |
| `createBatch` | `SingleRequest<List<DtoAttributeDto>> arg0` | `SingleResponse<Integer>` | 批量新建（SingleRequest） |
| `update` | `SingleRequest<DtoAttributeDto> arg0` | `SingleResponse<Integer>` | 修改字段 |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<DtoAttributeDto>` | 查询字段按 id |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<DtoAttributeDto>` | 分页查询字段按条件 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<DtoAttributeDto>` | 列表查询字段按条件 |

#### EntityAppService

`com.seeyon.udc.api.EntityAppService` · 构件 `udc-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<EntityDto> arg0` | `SingleResponse<Long>` | 新建实体（=一张物理表），返回 entityId |
| `update` | `SingleRequest<EntityDto> arg0` | `SingleResponse<Integer>` | 修改实体 |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<EntityDto>` | 查询实体按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<EntityDto>` | 查询实体按 ids |
| `selectByName` | `SingleRequest<Long> arg0` | `SingleResponse<EntityDto>` | 查询实体按名称 |
| `selectPageByCondition` | `PageRequest arg0` | `PageResponse<EntityDto>` | 分页查询实体按条件 |
| `selectListByConditions` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<EntityDto>` | 列表查询实体按条件 |
| `selectListByTerm` | `SingleRequest<Long> arg0` | `ListResponse<EntityDto>` | 列表查询实体按Term |
| `selectParentById` | `SingleRequest<Long> arg0` | `SingleResponse<EntityDto>` | 查询上级按 id |
| `selectEntitiesByAppId4Tree` | `SingleRequest<Long> arg0` | `ListResponse<EntityDto>` | 查询Entities按应用 |
| `selectAggregationEntitiesByAppId4Tree` | `SingleRequest<Long> arg0` | `ListResponse<EntityDto>` | 查询AggregationEntities按应用 |
| `selectChildrenByCondition` | `PageRequest arg0` | `PageResponse<EntityDto>` | 查询下级按条件 |
| `selectPrimaryEntityByAppId` | `SingleRequest<Long> arg0` | `ListResponse<EntityDto>` | 查询实体Primary按应用 |
| `selectByPrimaryEntityId` | `SingleRequest<Long> arg0` | `SingleResponse<EntityDto>` | 查询实体按实体 |
| `selectRootId` | `SingleRequest<Long> arg0` | `SingleResponse<Long>` | 查询根 |
| `selectEntityByIdsLoadAttribute` | `SingleRequest<List<Long>> arg0` | `ListResponse<EntityDto>` | 查询实体按字段 |

#### EntityGroupAppService

`com.seeyon.udc.api.EntityGroupAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<EntityGroupDto> arg0` | `SingleResponse<Long>` | 新建实体分组 |
| `update` | `SingleRequest<EntityGroupDto> arg0` | `SingleResponse<Integer>` | 修改实体分组 |
| `updateBatch` | `SingleRequest<List<EntityGroupDto>> arg0` | `SingleResponse<Integer>` | 批量修改（SingleRequest） |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<EntityGroupDto>` | 查询实体分组按 id |
| `selectByAppId` | `SingleRequest<Long> arg0` | `ListResponse<EntityGroupDto>` | 查询实体分组按应用 |

#### EntityOpenApiAppService

`com.seeyon.udc.api.EntityOpenApiAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectOpenApiData` | `SingleRequest<Void> arg0` | `ListResponse<EntityOpenApiDto>` | 查询API数据Open |

#### EntityPresetAppService

`com.seeyon.udc.api.EntityPresetAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectPresetByEntityId` | `SingleRequest<Long> arg0` | `SingleResponse<EntityPresetDto>` | 查询Preset按实体 |
| `uploadInItData` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 上传数据InIt |
| `create` | `SingleRequest<EntityPresetDto> arg0` | `SingleResponse<Long>` | 新建实体 |
| `update` | `SingleRequest<EntityPresetDto> arg0` | `SingleResponse<Integer>` | 修改实体 |
| `createDefaultExcelTemplate` | `SingleRequest<Long> arg0` | `SingleResponse<Long>` | 新建模板DefaultExcel |
| `selectListByAppId` | `SingleRequest<Long> arg0` | `ListResponse<EntityPresetDto>` | 列表查询实体按应用 |

#### EventAppService

`com.seeyon.udc.api.EventAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<EventDto> arg0` | `SingleResponse<Long>` | 新建Event |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<EventDto>` | 分页查询Event按条件 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<EventDto>` | 列表查询Event按条件 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<EventDto>` | 查询Event按 id |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `update` | `SingleRequest<EventDto> arg0` | `SingleResponse<Integer>` | 修改Event |
| `selectBusinessEvent` | `SingleRequest<EventQueryParamDto> arg0` | `ListResponse<EventQueryResultDto>` | 查询业务Event |
| `selectEvents` | `SingleRequest<EventQueryParamDto> arg0` | `ListResponse<EventQueryResultDto>` | 查询Events |

#### EventWithDataAppService

`com.seeyon.udc.api.EventWithDataAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createWithEventData` | `SingleRequest<EventAndDataDto> arg0` | `SingleResponse<Long>` | 新建数据WithEvent |
| `updateWithEventData` | `SingleRequest<EventAndDataDto> arg0` | `SingleResponse<Integer>` | 修改数据WithEvent |
| `selectWithEventData` | `SingleRequest<Long> arg0` | `SingleResponse<EventAndDataDto>` | 查询数据WithEvent |
| `selectListWithDataByConditions` | `ListRequest arg0` | `ListResponse<EventAndDataDto>` | 列表查询数据With按条件 |
| `selectListWithDataByTerm` | `SingleRequest<String> arg0` | `ListResponse<EventAndDataDto>` | 列表查询数据With按Term |

#### ExprConsistencyValidator

`com.seeyon.udc.api.ExprConsistencyValidator` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `validateConsistency` | `ConsistencyValidateConfig arg0` | `ConsistencyValidateResult` | 校验Consistency |

#### ExtendAppOperationAuthCheck

`com.seeyon.udc.api.ExtendAppOperationAuthCheck` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `hasRight` | `ExtendAppAuthCheckInfoDto arg0` | `boolean` | 判断有Right |

#### FeatureAppService

`com.seeyon.udc.api.FeatureAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `list` | `SingleRequest<String> arg0` | `ListResponse<FeatureBean>` | 列出FeatureBean |
| `listSystemAttributeNames` | `SingleRequest<String> arg0` | `ListResponse<String>` | 列出字段名称System |
| `upgrade` | `SingleRequest<String> arg0` | `Boolean` | 升级（SingleRequest） |

#### IndexAppService

`com.seeyon.udc.api.IndexAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<IndexDto> arg0` | `SingleResponse<Long>` | 新建Index |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `update` | `SingleRequest<IndexDto> arg0` | `SingleResponse<Integer>` | 修改Index |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<IndexDto>` | 查询Index按 id |
| `selectByEntityId` | `SingleRequest<Long> arg0` | `ListResponse<IndexDto>` | 查询Index按实体 |
| `selectMatchesAttributeByEntityId` | `SingleRequest<Long> arg0` | `ListResponse<AttributeDto>` | 查询字段Matches按实体 |

#### InnerEntityAppService

`com.seeyon.udc.api.InnerEntityAppService` · 构件 `udc-biz` · extends `EntityAppService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectEntitiesByEntityId4Tree` | `SingleRequest<Long> arg0` | `ListResponse<EntityDto>` | 查询Entities按实体 |
| `copyEntity` | `SingleRequest<EntityCopyDto> arg0` | `SingleResponse<Long>` | 复制实体 |
| `attributeTransfer` | `SingleRequest<AttributeTransferDto> arg0` | `ListResponse<Long>` | 转移字段 |
| `selectMasterEntityCount` | `SingleRequest<Long> arg0` | `SingleResponse<EntityCountDto>` | 查询实体MasterCount |

#### LastVersionMetadataManagerService

`com.seeyon.udc.api.LastVersionMetadataManagerService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `prepareLastVersionAfterDeployed` | `ApplicationDto arg0` | `List<LastVersionMetadataDto>` | 部署后准备「上一版本」元数据（用于版本对比/回滚） |
| `fetchLastVersionMetadataFromDbIfNotExist` | `LastVersionMetadataSearchDto arg0` | `LastVersionMetadataDto` | 拉取版本扩展属性LastFromDbIfNotExist |
| `getModule` | `—` | `LastVersionMetadataModuleEnum` | 获取Module |
| `getRelationModulePublishState` | `LastVersionMetadataSearchDto arg0` | `PublishStateEnum` | 获取RelationModulePublishState |
| `refreshLastVersionMetadata` | `ApplicationDto arg0` | `List<LastVersionMetadataDto>` | 刷新版本扩展属性Last |

#### LateralAuthChecker

`com.seeyon.udc.api.LateralAuthChecker` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `check` | `Supplier<Long> arg0` | `void` | 检查（Supplier） |
| `checkByAppName` | `Supplier<String> arg0` | `void` | 检查按应用名称（Supplier） |

#### MetadataHandleService

`com.seeyon.udc.api.MetadataHandleService` · 构件 `udc-plugin-api` · extends `Condition`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `handle` | `AppContext arg0` | `boolean` | 处理（AppContext） |

#### MicroFlowInfoAppService

`com.seeyon.udc.api.MicroFlowInfoAppService` · 构件 `udc-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `findCallConnectorAppService` | `SingleRequest<Long> arg0` | `SingleResponse<Map<String, List<String>>>` | 查找连接器应用CallService |
| `findCallIntegrationAppService` | `SingleRequest<Long> arg0` | `SingleResponse<MicroFlowIntegrationAppInfoDto>` | 查找应用CallIntegrationService |

#### MicroFlowUpgradeAppService

`com.seeyon.udc.api.MicroFlowUpgradeAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `upgradeThirdEntity` | `SingleRequest<String> arg0` | `SingleResponse<Integer>` | 升级第三方实体 |
| `upgradeThirdServiceByNames` | `SingleRequest<ThirdServiceQueryDto> arg0` | `SingleResponse<Integer>` | 升级第三方Service按名称 |
| `batchUpgradeThirdEntity` | `—` | `SingleResponse<Integer>` | 升级第三方实体 |
| `upgradeExtendFullNameByAppId` | `SingleRequest<String> arg0` | `SingleResponse<Integer>` | 升级扩展名称Full按应用 |
| `upgradeCallExtendAppService` | `SingleRequest<Long> arg0` | `SingleResponse<Map<String, Object>>` | 升级扩展应用CallService |
| `upgradeEntityEventFullName` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 升级实体名称EventFull |

#### PageMetadataQuery4SfAppService

`com.seeyon.udc.api.PageMetadataQuery4SfAppService` · 构件 `udc-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectAppMetaDataByAppName` | `SingleRequest<String> arg0` | `SingleResponse<UdcApplicationMetaData4SfDto>` | 查询应用数据Meta按应用名称 |

#### PageProcessEventAppService

`com.seeyon.udc.api.PageProcessEventAppService` · 构件 `udc-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectListByCondition` | `SingleRequest<PageProcessEventSearchDto> arg0` | `ListResponse<PageProcessEventDto>` | 列表查询页面流程按条件 |

#### ParameterAppService

`com.seeyon.udc.api.ParameterAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<UdcParameterDto> arg0` | `SingleResponse<Long>` | 新建参数 |
| `update` | `SingleRequest<UdcParameterDto> arg0` | `SingleResponse<Integer>` | 修改参数 |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<UdcParameterDto>` | 查询参数按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<UdcParameterDto>` | 查询参数按 ids |
| `selectPageByCondition` | `PageRequest arg0` | `PageResponse<UdcParameterDto>` | 分页查询参数按条件 |

#### PluginAttributeAppService

`com.seeyon.udc.api.PluginAttributeAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createBatch` | `SingleRequest<List<AttributeDto>> arg0` | `SingleResponse<Integer>` | 批量新建（SingleRequest） |

#### PluginEntityAppService

`com.seeyon.udc.api.PluginEntityAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<EntityDto> arg0` | `SingleResponse<Long>` | 新建实体 |
| `update` | `SingleRequest<EntityDto> arg0` | `SingleResponse<Integer>` | 修改实体 |

#### PluginPageInfoAppService

`com.seeyon.udc.api.PluginPageInfoAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createDefaultFilterPlanContentByEntityId` | `SingleRequest<Long> arg0` | `SingleResponse<FilterPlanContentDto>` | 新建内容DefaultFilterPlan按实体 |
| `createDefaultFilterPlanContentByEntity` | `SingleRequest<EntityDto> arg0` | `SingleResponse<FilterPlanContentDto>` | 新建内容DefaultFilterPlan按实体 |
| `parsePageResource` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<UdcResourceRegisterDto>` | 分页解析资源 |
| `getResourceByCondition` | `SingleRequest<UdcResourceRegisterDto> arg0` | `ListResponse<UdcResourceRegisterDto>` | 获取资源按条件 |
| `getResource4UserCenter` | `SingleRequest<Long> arg0` | `ListResponse<UdcResourceRegisterDto>` | 获取用户Resource4Center |

#### PluginReferConfigGroupAppService

`com.seeyon.udc.api.PluginReferConfigGroupAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createDefaultRefer` | `SingleRequest<Long> arg0` | `SingleResponse<Long>` | 新建DefaultRefer |
| `updateDefaultRefer` | `SingleRequest<Long> arg0` | `SingleResponse<Void>` | 修改DefaultRefer |
| `deleteDefaultRefer` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除DefaultRefer |

#### PreSetAttributeCapacityAppService

`com.seeyon.udc.api.PreSetAttributeCapacityAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getAllPreSetAttributeCapacity` | `SingleRequest<Long> arg0` | `ListResponse<PresetAttributeCapacityDto>` | 全部获取字段PreSetCapacity |
| `getPreSetAttributeCapacity` | `SingleRequest<String> arg0` | `SingleResponse<PresetAttributeCapacityDto>` | 获取字段PreSetCapacity |

#### PublishStateAppService

`com.seeyon.udc.api.PublishStateAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `updateState` | `SingleRequest<PublishStateUpdateDto> arg0` | `SingleResponse<Integer>` | 修改State |

#### ReferConfigAppService

`com.seeyon.udc.api.ReferConfigAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<ReferConfigDto> arg0` | `SingleResponse<Long>` | 新建配置 |
| `createOrUpdate` | `SingleRequest<ReferConfigDto> arg0` | `SingleResponse<Long>` | 新建OrUpdate |
| `update` | `SingleRequest<ReferConfigDto> arg0` | `SingleResponse<Integer>` | 修改配置 |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<ReferConfigDto>` | 查询配置按 id |
| `selectPageByCondition` | `PageRequest arg0` | `PageResponse<ReferConfigDto>` | 分页查询配置按条件 |
| `selectListByCondition` | `ListRequest arg0` | `ListResponse<ReferConfigDto>` | 列表查询配置按条件 |
| `convertToMobile` | `SingleRequest<Long> arg0` | `SingleResponse<Long>` | 转换ToMobile |

#### ReferConfigGroupAppService

`com.seeyon.udc.api.ReferConfigGroupAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createConfigInfo` | `SingleRequest<ReferConfigInfoDto> arg0` | `SingleResponse<Long>` | 新建配置 |
| `updateConfigInfo` | `SingleRequest<ReferConfigInfoDto> arg0` | `SingleResponse<Integer>` | 修改配置 |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<ReferConfigGroupDto>` | 列表查询配置分组按条件 |

#### ResourceAppService

`com.seeyon.udc.api.ResourceAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `registerRole` | `SingleRequest<UdcRoleRegisterDto> arg0` | `SingleResponse<Long>` | 注册角色 |
| `registerResourceBatch` | `SingleRequest<List<UdcResourceRegisterDto>> arg0` | `SingleResponse<Integer>` | 批量注册资源 |
| `registerResource` | `SingleRequest<UdcResourceRegisterDto> arg0` | `SingleResponse<Integer>` | 注册资源 |
| `deleteByRef` | `SingleRequest<UdcResourceDeleteDto> arg0` | `SingleResponse<Integer>` | 删除资源按Ref |
| `deleteByPage` | `SingleRequest<UdcResourceDeleteDto> arg0` | `SingleResponse<Integer>` | 删除资源按页面 |
| `deleteByApp` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按应用（SingleRequest） |

#### ScalabilityAppService

`com.seeyon.udc.api.ScalabilityAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<ScalabilityDto> arg0` | `SingleResponse<Long>` | 新建Scalability |
| `update` | `SingleRequest<ScalabilityDto> arg0` | `SingleResponse<Integer>` | 修改Scalability |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<ScalabilityDto>` | 查询Scalability按 id |
| `selectByOptionId` | `SingleRequest<Long> arg0` | `ListResponse<ScalabilityDto>` | 查询Scalability按OptionId |

#### ScalabilityOptionAppService

`com.seeyon.udc.api.ScalabilityOptionAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<ScalabilityOptionDto> arg0` | `SingleResponse<Long>` | 新建ScalabilityOption |
| `update` | `SingleRequest<ScalabilityOptionDto> arg0` | `SingleResponse<Integer>` | 修改ScalabilityOption |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<ScalabilityOptionDto>` | 查询ScalabilityOption按 id |
| `selectByAppId` | `SingleRequest<Long> arg0` | `ListResponse<ScalabilityOptionDto>` | 查询ScalabilityOption按应用 |
| `selectByAppIdWithDetail` | `SingleRequest<Long> arg0` | `ListResponse<ScalabilityOptionDto>` | 查询ScalabilityOption按应用 |
| `selectAllOptionName` | `—` | `ListResponse<ScalabilityOptionDto>` | 全部查询名称Option |

#### StereotypeAllAppService

`com.seeyon.udc.api.StereotypeAllAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getAll` | `—` | `List<Stereotype>` | 全部获取 |
| `get` | `String arg0` | `Stereotype` | 获取（String） |

#### StereotypeAppService

`com.seeyon.udc.api.StereotypeAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `list` | `SingleRequest<String> arg0` | `ListResponse<StereotypeBean>` | 列出StereotypeBean |
| `upgrade` | `SingleRequest<String> arg0` | `Boolean` | 升级（SingleRequest） |

#### UdcBpmAppService

`com.seeyon.udc.api.UdcBpmAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectDefaultLayoutAppName` | `—` | `SingleResponse<String>` | 取流程默认布局应用名（发起页渲染用） |

#### UdcCtpEnumAppService

`com.seeyon.udc.api.UdcCtpEnumAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectCategoryByAppGuid` | `SingleRequest<UdcCtpEnumBaseSearchDto> arg0` | `ListResponse<CtpEnumCategoryDto>` | 查询分类按应用 |
| `selectCategoryAndEnum` | `SingleRequest<UdcCtpEnumBaseSearchDto> arg0` | `SingleResponse<CtpEnumCategoryAndEnumDto>` | 查询分类枚举And |
| `selectCtpEnum` | `SingleRequest<UdcCtpEnumBaseSearchDto> arg0` | `ListResponse<CtpEnumDto>` | 查询枚举Ctp |
| `selectCtpEnumByIds` | `SingleRequest<UdcCtpEnumsSearchDto> arg0` | `ListResponse<CtpEnumDto>` | 查询枚举Ctp按 ids |
| `selectParentByCode` | `SingleRequest<UdcCtpEnumSearchDto> arg0` | `SingleResponse<CtpEnumDto>` | 查询上级按编码 |
| `selectListByConditionsNoLevel` | `SingleRequest<UdcCtpEnumSearchDto> arg0` | `ListResponse<CtpEnumDto>` | 列表查询枚举按条件职务级别 |
| `selectCtpEnumItemById` | `SingleRequest<UdcCtpEnumItemSearchDto> arg0` | `SingleResponse<CtpEnumItemDto>` | 查询枚举CtpItem按 id |
| `selectCtpEnumItemByAppInfo` | `SingleRequest<UdcCtpEnumBaseSearchDto> arg0` | `ListResponse<CtpEnumItemDto>` | 查询枚举CtpItem按应用 |
| `selectCtpEnumItemByEnumId` | `SingleRequest<UdcCtpEnumItemSearchDto> arg0` | `ListResponse<CtpEnumItemDto>` | 查询枚举CtpItem按枚举 |
| `selectCtpEnumItemByAppNameAndEnumCode` | `SingleRequest<UdcCtpEnumItemSearchDto> arg0` | `ListResponse<CtpEnumItemDto>` | 查询枚举CtpItem按应用名称枚举编码 |
| `selectCtpEnumItemSimpleByAppNameAndEnumCode` | `SingleRequest<UdcCtpEnumItemSearchDto> arg0` | `ListResponse<CtpEnumItemSimpleDto>` | 查询枚举简单CtpItem按应用名称枚举编码 |
| `selectCtpEnumItemSimpleByAppNameAndEnumCodes` | `SingleRequest<UdcCtpEnumItemSearchDto> arg0` | `ListResponse<CtpEnumItemSimpleDto>` | 查询枚举简单CtpItem按应用名称枚举编码 |
| `selectByEnumIds` | `SingleRequest<UdcCtpEnumItemSearchDto> arg0` | `ListResponse<CtpEnumItemDto>` | 查询枚举按枚举 |
| `selectEnumItemByConditions` | `SingleRequest<UdcCtpEnumItemSearchDto> arg0` | `ListResponse<CtpEnumItemDto>` | 查询枚举Item按条件 |
| `selectEnumItemCascadeTreeByEnumCode` | `SingleRequest<UdcCtpEnumItemSearchDto> arg0` | `ListResponse<CtpEnumItemDto>` | 级联树查询枚举Item按枚举编码 |
| `deleteCtpEnumByAppApprovalOrUdc` | `SingleRequest<UdcCtpEnumItemSearchDto> arg0` | `SingleResponse<Integer>` | 删除枚举Ctp按应用审批 |

#### UdcCtpEnumProxyAppService

`com.seeyon.udc.api.UdcCtpEnumProxyAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectOneByIdAndApp` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<CtpEnumItemDto>` | 查询One按应用 |
| `selectByEnumCodeAndAppGuid` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpEnumItemSimpleDto>` | 查询枚举简单按枚举编码应用 |
| `selectByEnumCodesAndAppGuid` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpEnumItemSimpleDto>` | 查询枚举简单按枚举编码应用 |
| `selectCascadeTreeByEnumCode` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpEnumItemDto>` | 级联树查询枚举按枚举编码 |
| `selectByEnumItemByDependentApp` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpEnumItemSimpleDto>` | 查询枚举简单按枚举应用 |
| `selectByEnumItemByDependentApp` | `DependentApplicationDto arg0` | `ListResponse<CtpEnumItemSimpleDto>` | 查询枚举简单按枚举应用 |

#### UdcDataBaseSqlGenerator

`com.seeyon.udc.api.UdcDataBaseSqlGenerator` · 构件 `udc-biz` · extends `Ordered`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getChangeList` | `ApplicationDto arg0` | `List<Change>` | 列表获取Change |
| `getDropChangeList` | `ApplicationDto arg0` | `List<Change>` | 列表获取DropChange |
| `getSchemaInfo` | `List<SchemaInfo> arg0` | `List<Object>` | 获取结构 |
| `filterSet` | `—` | `Set<String>` | 设置 |

#### UdcEnumAppService

`com.seeyon.udc.api.UdcEnumAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<UdcEnumDto> arg0` | `SingleResponse<Long>` | 新建枚举 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<UdcEnumDto>` | 分页查询枚举按条件 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<UdcEnumDto>` | 列表查询枚举按条件 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<UdcEnumDto>` | 查询枚举按 id |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `update` | `SingleRequest<UdcEnumDto> arg0` | `SingleResponse<Integer>` | 修改枚举 |
| `selectListByTerm` | `SingleRequest<Long> arg0` | `ListResponse<UdcEnumDto>` | 列表查询枚举按Term |

#### UdcEnumCategoryAppService

`com.seeyon.udc.api.UdcEnumCategoryAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<UdcEnumCategoryDto> arg0` | `SingleResponse<Long>` | 新建枚举分类 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<UdcEnumCategoryDto>` | 分页查询枚举分类按条件 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<UdcEnumCategoryDto>` | 列表查询枚举分类按条件 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<UdcEnumCategoryDto>` | 查询枚举分类按 id |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `update` | `SingleRequest<UdcEnumCategoryDto> arg0` | `SingleResponse<Integer>` | 修改枚举分类 |
| `selectCategoryAndEnum` | `SingleRequest<Long> arg0` | `SingleResponse<UdcEnumCategoryAndEnumDto>` | 查询分类枚举And |

#### UdcEnumItemAppService

`com.seeyon.udc.api.UdcEnumItemAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<UdcEnumItemDto> arg0` | `SingleResponse<Long>` | 新建枚举 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<UdcEnumItemDto>` | 分页查询枚举按条件 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<UdcEnumItemDto>` | 列表查询枚举按条件 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<UdcEnumItemDto>` | 查询枚举按 id |
| `selectByEnumId` | `SingleRequest<Long> arg0` | `ListResponse<UdcEnumItemDto>` | 查询枚举按枚举 |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `update` | `SingleRequest<UdcEnumItemDto> arg0` | `SingleResponse<Integer>` | 修改枚举 |
| `operateBatch` | `SingleRequest<List<UdcEnumItemDto>> arg0` | `SingleResponse<Integer>` | 批量操作枚举项（增删改排序） |
| `selectListByTerm` | `SingleRequest<Long> arg0` | `ListResponse<UdcEnumItemDto>` | 列表查询枚举按Term |
| `importExcel` | `SingleRequest<ExcelImportTransDto> arg0` | `ListResponse<ExcelImportResultDto>` | 导入Excel |

#### UdcFunctionAppService

`com.seeyon.udc.api.UdcFunctionAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createFunctionRefer` | `SingleRequest<Map<String, Object>> arg0` | `void` | 新建FunctionRefer |
| `deletePortalFunctionRefer` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 删除PortalFunctionRefer |
| `updateFunctionRefer` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 修改FunctionRefer |
| `findMenuDefaultPage` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Map<Long, Object>>` | 分页查找菜单Default |

#### UdcLateralAuthCheckAppService

`com.seeyon.udc.api.UdcLateralAuthCheckAppService` · 构件 `udc-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `check` | `SingleRequest<UdcLateralCheckDto> arg0` | `SingleResponse<Boolean>` | 检查LateralCheck |

#### UdcMetaDataAppService

`com.seeyon.udc.api.UdcMetaDataAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectAppMetaData4PageCode` | `SingleRequest<Long> arg0` | `SingleResponse<UdcApplicationMetaData4PageCode>` | ★读应用全量元数据（生成页面代码用） |
| `selectAvailableUpgradeAppMetadataById` | `SingleRequest<Long> arg0` | `ListResponse<UdcApplicationMetaDataDto>` | 查询升级应用扩展属性Available按 id |
| `selectPageAvailableAppMetaDataByCondition` | `PageRequest arg0` | `PageResponse<UdcApplicationMetaDataDto>` | 分页查询应用数据AvailableMeta按条件 |
| `selectPageAvailableAppMultiVersionMetaDataByCondition` | `PageRequest arg0` | `PageResponse<ApplicationMultiVersionDto>` | 分页查询应用版本数据AvailableMultiMeta按条件 |
| `selectReferMetaDataByEntity` | `SingleRequest<UdcReferMetaDataSearchDto> arg0` | `ListResponse<UdcReferMetaDataDto>` | 查询数据ReferMeta按实体 |
| `mergeReferMetaData` | `SingleRequest<UdcReferMetaDataSearch4PageDto> arg0` | `ListResponse<UdcReferMetaDataDto>` | 合并数据ReferMeta |
| `selectCustomReferMetaDataByPageId` | `SingleRequest<Long> arg0` | `ListResponse<UdcReferMetaDataDto>` | 查询数据CustomReferMeta按页面 |
| `selectReferAndAppMetadataByEntity` | `SingleRequest<UdcReferMetaDataSearchDto> arg0` | `SingleResponse<UdcReferAndAppMetaDataDto>` | 查询应用扩展属性ReferAnd按实体 |
| `selectEntityMetaData` | `SingleRequest<EntityMetaDataSearch4PageDto> arg0` | `SingleResponse<UdcEntityMetaDataDto>` | 读实体元数据（运行态快照） |
| `selectAggEntityIncludeAssociationByEntityId` | `SingleRequest<Long> arg0` | `ListResponse<UdcEntityMetaDataDto>` | 查询实体AggIncludeAssociation按实体 |
| `selectAggEntityIncludeAssociation` | `SingleRequest<EntityMetaDataSearch4PageDto> arg0` | `ListResponse<UdcEntityMetaDataDto>` | 查询实体AggIncludeAssociation |
| `selectAggEntity` | `SingleRequest<EntityMetaDataSearch4PageDto> arg0` | `ListResponse<UdcEntityMetaDataDto>` | 查询实体Agg |
| `selectEntitiesMetaDataByAppId` | `SingleRequest<Long> arg0` | `ListResponse<UdcEntityMetaDataDto>` | 查询数据EntitiesMeta按应用 |
| `selectSimpleAggEntityMetaDataByAppName` | `SingleRequest<UdcSimpleEntityMetaDataSearchDto> arg0` | `ListResponse<UdcAggMetadataDto>` | 查询简单实体数据AggMeta按应用名称 |
| `selectEnumMetaDataByAppId` | `SingleRequest<Long> arg0` | `ListResponse<CtpEnumDto>` | 读应用下全部枚举元数据 |
| `selectAppMetaListData` | `SingleRequest<UdcApplicationMetaDataSearchDto> arg0` | `ListResponse<UdcApplicationMetaDataDto>` | 列表查询应用数据Meta |
| `selectCtpEnumMetaDataListData` | `SingleRequest<UdcGeneralMetaDataSearchDto> arg0` | `SingleResponse<UdcApplicationMetaDataDto>` | 列表查询枚举数据CtpMeta |
| `selectParentEnumByCode` | `SingleRequest<UdcCtpEnumMetaDataSearchDto> arg0` | `SingleResponse<CtpEnumDto>` | 查询上级枚举按编码 |
| `selectCtpEnumMetaDataListData1` | `SingleRequest<UdcGeneralMetaDataSearchDto> arg0` | `SingleResponse<UdcApplicationCtpEnumDto>` | 列表查询枚举数据CtpMetaData1 |
| `selectCtpEnumAndApplicationMetaDataList` | `SingleRequest<Long> arg0` | `ListResponse<UdcApplicationCtpEnumDto>` | 列表查询枚举应用数据CtpAndMeta |
| `selectCtpEnumItemList` | `SingleRequest<UdcGeneralMetaDataSearchDto> arg0` | `ListResponse<CtpEnumItemDto>` | 列表查询枚举CtpItem |
| `selectPageMetaData` | `SingleRequest<PageMetaDataSearch4PageDto> arg0` | `SingleResponse<UdcPageMetadataV2Dto>` | 分页查询数据Meta |
| `selectPageInfoMetaData` | `SingleRequest<PagesMetaDataSearch4PageDto> arg0` | `ListResponse<UdcPageMetadataV2Dto>` | 分页查询数据Meta |
| `selectPageMetaDataByMasterApp` | `SingleRequest<PagesMetaDataSearch4PageDto> arg0` | `ListResponse<UdcApplicationMetaDataDto>` | 分页查询数据Meta按应用 |
| `selectAllLayoutMetaDataByAppIncludeHost` | `SingleRequest<PagesMetaDataSearch4PageDto> arg0` | `ListResponse<UdcApplicationMetaDataDto>` | 全部查询布局数据Meta按应用 |
| `selectPageLayoutInfoMetaData` | `SingleRequest<PageMetaDataSearch4PageDto> arg0` | `SingleResponse<UdcPageMetadataV2Dto>` | 分页查询布局数据Meta |
| `selectPageLayoutMetaData` | `SingleRequest<UdcPageLayoutSearchDto> arg0` | `SingleResponse<UdcPageMetadataV2Dto>` | 分页查询布局数据Meta |
| `selectAllPageLayoutMetaDataByApp` | `SingleRequest<List<UdcPageLayoutSearchDto>> arg0` | `ListResponse<UdcPageMetadataV2Dto>` | 全部分页查询布局数据Meta按应用 |
| `selectPageSchema4Bpm` | `SingleRequest<List<UdcPageInfoSearchV2Dto>> arg0` | `ListResponse<UdcPageMetadataV2Dto>` | 给流程用的页面 schema |
| `selectJavaEnumMetaDataList` | `SingleRequest<UdcJavaEnumMetaDataSearchDto> arg0` | `ListResponse<UdcJavaEnumCategoryAndItemDto>` | 列表查询枚举数据JavaMeta |
| `selectJavaEnumItemMetaDataList` | `SingleRequest<UdcJavaEnumMetaDataSearchDto> arg0` | `ListResponse<UdcJavaEnumItemMetaDataDto>` | 列表查询枚举数据JavaItemMeta |
| `selectEntitiesByEntityId4Tree` | `SingleRequest<Long> arg0` | `ListResponse<EntityDto>` | 查询Entities按实体 |
| `selectFunctionNodeWithPageInfoDtoTreeByApp` | `SingleRequest<PagesMetaDataSearch4PageDto> arg0` | `ListResponse<UdcApplicationMetaDataDto>` | 分页树查询FunctionWithDto按应用 |

#### UdcPageLayoutPluginAppService

`com.seeyon.udc.api.UdcPageLayoutPluginAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `filterDependentApplicationList` | `SingleRequest<List<UdcApplicationMetaDataDto>> arg0` | `ListResponse<UdcApplicationMetaDataDto>` | 过滤出依赖该布局插件的应用 |
| `allowDependentLayoutApplicationList` | `SingleRequest<ApplicationDto> arg0` | `ListResponse<String>` | 判断这些应用是否允许依赖该布局 |
| `filterApplicationFeature` | `SingleRequest<ApplicationDto> arg0` | `ListResponse<ApplicationFeatureEnum>` | 按特性过滤应用（插件启用范围） |

#### UdcPortalPortletAppService

`com.seeyon.udc.api.UdcPortalPortletAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createCategory` | `SingleRequest<UdcPortalPortletCategoryDto> arg0` | `SingleResponse<Long>` | 新建分类 |
| `updateCategory` | `SingleRequest<UdcPortalPortletCategoryDto> arg0` | `SingleResponse<Long>` | 修改分类 |
| `deleteCategoryByIds` | `SingleRequest<List<String>> arg0` | `SingleResponse<Integer>` | 删除分类按 ids |
| `createOrUpdatePortlet` | `SingleRequest<UdcPortalPortletDefinitionDto> arg0` | `SingleResponse<Long>` | 新建OrUpdatePortlet |
| `deletePortletByIds` | `SingleRequest<UdcPortletBatchOperateDto> arg0` | `SingleResponse<Integer>` | 删除Portlet按 ids |
| `updatePortletSortNos` | `SingleRequest<UdcPortalPortletSortNoParamDto> arg0` | `SingleResponse<Integer>` | 修改排序PortletNos |
| `updatePortletName` | `SingleRequest<UdcPortalPortletDefinitionDto> arg0` | `SingleResponse<Long>` | 修改名称Portlet |

#### UdcPortalSetAppService

`com.seeyon.udc.api.UdcPortalSetAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createPcTemplateData` | `SingleRequest<UdcPortalSetDesignerDto> arg0` | `SingleResponse<Long>` | 新建模板数据Pc |

#### UdcPortalSpaceAppService

`com.seeyon.udc.api.UdcPortalSpaceAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectDesignSpaceList` | `SingleRequest<List<Long>> arg0` | `ListResponse<UdcPortalSpaceDto>` | 列表查询DesignSpace |

#### UdcSandBoxAppService

`com.seeyon.udc.api.UdcSandBoxAppService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `search` | `PageDtoRequest<MicroFlowLogSearchDto> arg0` | `PageResponse<MicroFlowLogResultDto>` | 搜索日志 |
| `searchDetails` | `PageDtoRequest<MicroFlowLogDetailsSearchDto> arg0` | `PageResponse<MicroFlowLogDetailsResultDto>` | 搜索Details |
| `searchDetails4FlowLog` | `SingleRequest<MicroFlowLogDetailsSearchDto> arg0` | `SingleResponse<MicroFlowFlowLogResultDto>` | 搜索日志Details4Flow |
| `searchPageLog` | `PageDtoRequest<UdcRtPageLogSearchDto> arg0` | `PageResponse<UdcRtPageLogSearchResultDto>` | 分页搜索日志 |
| `searchPageLogNonMetadata` | `PageDtoRequest<UdcRtPageLogSearchDto> arg0` | `PageResponse<UdcRtPageLogSearchResultDto>` | 分页搜索日志扩展属性Non |
| `dataTransfer` | `SingleRequest<DataTransferRequest> arg0` | `SingleResponse<DataTransferResponse>` | 转移Transfer |

#### UdcSerialSchemeAppService

`com.seeyon.udc.api.UdcSerialSchemeAppService` · 构件 `udc-plugin-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectSerialScheme` | `SingleRequest<UdcSerialSchemeSearchDto> arg0` | `ListResponse<SerialSchemeDto>` | 查询SerialScheme |
| `selectSerialSchemeById` | `SingleRequest<UdcSerialSchemeSearchDto> arg0` | `SingleResponse<SerialSchemeDto>` | 查询SerialScheme按 id |
| `selectSerialRange` | `SingleRequest<UdcSerialRangeSearchDto> arg0` | `ListResponse<SerialRangeDto>` | 查询SerialRange |
| `createEasyScheme` | `SingleRequest<UdcSerialSchemeCreateDto> arg0` | `SingleResponse<Long>` | 新建EasyScheme |
| `selectDepAppSerialScheme` | `SingleRequest<List<DependentApplicationDto>> arg0` | `ListResponse<SerialSchemeDto>` | 查询应用DepSerialScheme |

### `com.seeyon.udc.common.api`

#### UdcTreeQueryService

`com.seeyon.udc.common.api.UdcTreeQueryService` · 构件 `udc-common`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectTreeData` | `SingleRequest<UdcTreeQueryDto> arg0` | `PageResponse` | 树查询数据 |

### `com.seeyon.udc.log.api`

#### UdcAuditLogService

`com.seeyon.udc.log.api.UdcAuditLogService` · 构件 `udc-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createLog4EntityDelete` | `List<EntityDto> arg0` | `void` | 新建实体Log4Delete |
| `createLog4AttributeDelete` | `List<AttributeDto> arg0` | `void` | 新建字段Log4Delete |
| `createLog4ApplicationDelete` | `ApplicationDto arg0` | `void` | 新建应用Log4Delete |

### `com.seeyon.udc.upgrade.api`

#### BusinessRuleUpgradeAppService

`com.seeyon.udc.upgrade.api.BusinessRuleUpgradeAppService` · 构件 `udc-upgrade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `upgradeDataFlowEntityMappingRelation` | `SingleRequest<EntityMappingRelationUpgradeParamDto> arg0` | `SingleResponse<Integer>` | 升级数据实体映射FlowRelation |
| `upgradeSearchConditionAndAlgorithmAddUuid` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 升级条件SearchAndAlgorithmAddUuid |
| `upgradeDataFlowPageParam` | `SingleRequest<EntityMappingRelationUpgradeParamDto> arg0` | `SingleResponse<Integer>` | 分页升级数据FlowParam |

#### UpgradeAppService

`com.seeyon.udc.upgrade.api.UpgradeAppService` · 构件 `udc-upgrade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `upgrade4OrgEntityModify` | `—` | `SingleResponse<Boolean>` | 升级：处理组织实体被修改的场景 |
| `upgradeDeleteVersionSuffix` | `—` | `SingleResponse<Boolean>` | 升级版本DeleteSuffix |
| `upgrade4AttributeSerialGuid` | `—` | `SingleResponse<Integer>` | 升级：字段流水号 guid 迁移 |
| `upgrade4pageId` | `SingleRequest<Boolean> arg0` | `SingleResponse<Integer>` | 升级：页面 id 迁移 |
| `upgradeBillEntity4AppId` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 升级应用BillEntity4 |
| `upgradeBillBefore1230` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 升级BillBefore1230 |
| `upgradeBill4DeductionAddField` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 升级字段Bill4DeductionAdd |
| `upgradeBasicDataReferName` | `—` | `SingleResponse<Boolean>` | 升级数据名称BasicRefer |
| `upgradeEntityTableName` | `—` | `SingleResponse<Boolean>` | 升级实体表名称 |
| `upgradeEntityTableName0831` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Boolean>` | 升级实体表Name0831 |
| `upgradeFilterPlanByAppId` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 升级FilterPlan按应用 |
| `upgradePrePageStorageKeyByAppId` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 分页升级存储键Pre按应用 |
| `upgradeFilterPlanFrame` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<String>` | 升级FilterPlanFrame |
| `upgradeReferBasicData` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<String>` | 升级数据ReferBasic |
| `upgradeReferConfig` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<String>` | 升级配置Refer |
| `updateState4Shelf` | `SingleRequest<ShelfCompatibilityLockRequestDto> arg0` | `SingleResponse<Void>` | 修改State4Shelf |
| `upgradeAttributeSetDefaultValueSystemVariable` | `SingleRequest<Long> arg0` | `SingleResponse<Void>` | 升级字段SetDefaultValueSystemVariable |
| `upgradeFilterPlanSearchReferByAppId` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 升级FilterPlanSearchRefer按应用 |
| `upgradeMultiVersionByAppId` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 升级版本Multi按应用 |
| `upgradeMultiVersion` | `—` | `SingleResponse<Boolean>` | 升级版本Multi |
| `upgradeAttribute4Widget` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 升级控件Attribute4 |
| `upgradeUnusedFilterPlan` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 升级UnusedFilterPlan |
| `updateDeductionInfo4Attribute` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 修改字段DeductionInfo4 |
| `upgradeReferCarry` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<String>` | 升级ReferCarry |
| `upgradePageSchema` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<String>` | 分页升级结构 |
| `upgradePageSchema` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<String>` | 分页升级结构 |
| `upgradePageComponentSourceType` | `—` | `SingleResponse<String>` | 分页升级组件类型Source |
| `upgradePageSchema` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<String>` | 分页升级结构 |
| `upgradeLatestDependentApplication` | `—` | `SingleResponse<String>` | 升级应用LatestDependent |
| `upgradeDependentApplicationPackage` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 升级应用DependentPackage |
| `refreshComponentNullSourceType` | `—` | `SingleResponse<String>` | 刷新组件类型NullSource |
| `upgradeGitRepo` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 升级GitRepo |
| `duplicateRepair` | `—` | `SingleResponse<Integer>` | 修复重复数据（升级遗留） |
| `upgradeCollaborationAppGuid` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 升级应用CollaborationGuid |
| `upgradePageTemplateForm` | `—` | `SingleResponse<String>` | 分页升级模板表单 |
| `deleteUnusedCyclicEnum` | `—` | `SingleResponse<String>` | 删除枚举UnusedCyclic |
| `updateApplicationPublishState` | `—` | `SingleResponse<Integer>` | 修改应用PublishState |
| `upgradeEdocComponentRepair` | `—` | `SingleResponse<String>` | 升级组件EdocRepair |
| `upgradeDefaultPageTemplateData` | `—` | `SingleResponse<String>` | 分页升级模板数据Default |
| `upgradeUpdaterAttributeExpression` | `—` | `SingleResponse<String>` | 升级字段UpdaterExpression |
| `upgradeAttachmentMultiDataTypeMaxLength` | `—` | `SingleResponse<String>` | 升级数据类型AttachmentMultiMaxLength |
| `upgradeAttachmentSingleDataTypeMaxLength` | `—` | `SingleResponse<String>` | 升级数据类型AttachmentSingleMaxLength |
| `upgradeAppVersion` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 升级应用版本 |
| `upgradeNormalAppCopVersion` | `String arg0` | `SingleResponse<String>` | 升级应用版本NormalCop |
| `upgradeComponentToAgg` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 升级组件ToAgg |
| `upgradeGitFrontRepo` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 升级GitFrontRepo |
| `upgradePageSchemaState` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 分页升级结构State |
| `upgradeTextOverflowAttribute` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 升级字段TextOverflow |
| `upgradeAttributeDefault` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 升级字段Default |
| `upgradeScalabilityAppId` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 升级应用Scalability |
| `upgradeAttribute52to53` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 升级Attribute52to53 |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 110 个领域服务，下表列**方法数最多的 40 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `MicroFlowService` | 126 | MicroFlow · 查询×30 / 获取×14 / 删除×11 |
| `MicroFlowMetaDataQueryService` | 122 | MicroFlowMetaQuery · 获取×23 / 构建×19 / 查询×17 |
| `AttributeService` | 99 | 字段 · 查询×26 / 检查×16 / 删除×9 |
| `PageInfoService` | 94 | 页面 · 查询×24 / 新建×10 / 获取×8 |
| `EntityService` | 91 | 实体 · 查询×36 / 删除×7 / 检查×7 |
| `ApplicationService` | 83 | 应用 · 查询×31 / 检查×10 / 修改×7 |
| `MicroFlowFrontEndService` | 79 | MicroFlowFrontEnd · 检查×27 / 获取×13 / 检测×12 |
| `FunctionNodeService` | 72 | FunctionNode · 查询×12 / 修改×9 / 删除×9 |
| `DeductionRuleService` | 61 | 规则 · 查询×11 / 检查×9 / 获取×6 |
| `DataFlowMappingDesignService` | 51 | 映射 · 查询×13 / 处理×4 / 修改×4 |
| `UdcRoleService` | 49 | 角色 · 查询×12 / 保存×8 / 获取×7 |
| `PageLayoutService` | 45 | 页面布局 · 查询×14 / 修改×5 / 删除×5 |
| `DeployRecordService` | 42 | 部署 · 查询×15 / 获取×8 / 修改×7 |
| `ReferConfigService` | 40 | 配置 · 删除×11 / 查询×9 / 新建×5 |
| `DependentApplicationService` | 39 | 应用 · 查询×10 / 获取×7 / 新建×7 |
| `CustomPageInfoService` | 39 | 页面 · 获取×13 / 办理×11 / 新建×3 |
| `AttributeGroupService` | 36 | 字段分组 · 查询×10 / 修改×4 / 删除×4 |
| `DataTransferObjectService` | 35 | TransferObject · 查询×15 / 删除×8 / 新建×2 |
| `UdcEnumItemService` | 34 | 枚举 · 查询×12 / 检查×4 / 删除×4 |
| `DeductionMapService` | 32 | DeductionMap · 检查×8 / 查询×7 / 修改×3 |
| `AppCollaborationService` | 31 | 应用 · 查询×17 / 新建×5 / 获取×3 |
| `EventService` | 31 | Event · 查询×17 / 删除×5 / 修改×2 |
| `IndexService` | 31 | Index · 查询×10 / 检查×7 / 删除×7 |
| `DataFlowDesignService` | 29 | FlowDesign · 查询×8 / 修改×7 / 删除×4 |
| `UdcResourceService` | 29 | 资源 · 删除×6 / 查询×6 / 获取×4 |
| `BaseDataService` | 28 | BaseData · 查询×13 / 获取×6 / 修改×4 |
| `AttributeSetService` | 26 | 字段 · 查询×11 / 新建×4 / 删除×4 |
| `Entity4RecordService` | 26 | Entity4Record · 处理×11 / 构建×9 / 获取×3 |
| `UdcEnumService` | 26 | 枚举 · 查询×10 / 删除×4 / 新建×2 |
| `MicroFlowGroupService` | 26 | 分组 · 查询×9 / 删除×7 / 新建×3 |
| `OperationLogService` | 25 | 日志 · 新建×4 / 记录×4 / 搜索×3 |
| `PageTemplateService` | 25 | 页面模板 · 查询×8 / 删除×4 / 新建×3 |
| `PortletService` | 25 | Portlet · 查询×6 / 新建×3 / 修改×3 |
| `ScalabilityService` | 24 | Scalability · 检查×8 / 删除×5 / 查询×3 |
| `UdcCtpEnumService` | 24 | 枚举 · 查询×16 / 修改×3 / 删除×1 |
| `MicroFlowFunctionalCheckService` | 23 | MicroFlowFunctionalCheck · 查找×6 / 解析×3 / 查询×3 |
| `DtoAttributeService` | 22 | 字段 · 查询×9 / 删除×6 / 新建×2 |
| `PageMetadataService` | 22 | 页面扩展属性 · 查询×13 / 构建×1 / 查找×1 |
| `SplitImportRecordService` | 21 | 拆分 · 查询×11 / 新建×4 / 删除×3 |
| `UdcCtpEnumItemProxyService` | 20 | 枚举 · 查询×8 / 获取×4 / 判断×2 |

## biz 层：事件与监听

事件 71 个 · 监听器 28 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
|  | `Event` |
| AbstractBatch | `AbstractBatchEvent` |
| After | `AfterCreateBatchEvent`, `AfterCreateEvent`, `AfterDeleteBatchEvent`, `AfterDeleteEvent`, `AfterUpdateBatchEvent`, `AfterUpdateEvent` |
| AfterBpmProcess | `AfterBpmProcessEvent` |
| AppVersion | `AppVersionEvent` |
| Application | `ApplicationCreateEvent`, `ApplicationDeleteEvent`, `ApplicationUpdateEvent` |
| ApplicationOnShelf | `ApplicationOnShelfEvent` |
| Attribute | `AttributeCreateEvent`, `AttributeDeleteEvent`, `AttributeUpdateEvent` |
| AttributeSet | `AttributeSetDeleteEvent`, `AttributeSetUpdateEvent` |
| Base | `BaseUpdateEvent` |
| Before | `BeforeCreateBatchEvent`, `BeforeCreateEvent`, `BeforeDeleteBatchEvent`, `BeforeDeleteEvent`, `BeforeUpdateBatchEvent`, `BeforeUpdateEvent` |
| CustomDataType | `CustomDataTypeDeleteEvent`, `CustomDataTypeUpdateEvent` |
| DataTransferObject | `DataTransferObjectDeleteEvent` |
| DeductionMap | `DeductionMapDeleteEvent` |
| DeductionRule | `DeductionRuleDeleteEvent` |
| Dependent | `DependentUpdateEvent` |
| DependentApplicationAdd | `DependentApplicationAddEvent` |
| DeployChange | `DeployChangeEvent` |
| DeployFinish | `DeployFinishEvent` |
| DeployStart | `DeployStartEvent` |
| DeployStop | `DeployStopEvent` |
| Entity | `EntityCreateEvent`, `EntityDeleteEvent`, `EntityUpdateEvent` |
| Event | `EventDeleteEvent` |
| FormLoadSuccess | `FormLoadSuccessEvent` |
| Function | `FunctionCreatePageSchemaEvent`, `FunctionDeletePageEvent`, `FunctionUpdatePageSchemaEvent` |
| FunctionNode | `FunctionNodeDeleteEvent` |
| FunctionNodeAdd | `FunctionNodeAddEvent` |
| MicroFlow | `MicroFlowDeleteEvent`, `MicroFlowUpdateEvent` |
| Page | `PageCreateEvent`, `PageDeleteEvent` |
| PageInfoSave | `PageInfoSaveEvent` |
| PageLayout | `PageLayoutDeleteEvent` |
| PageLayoutSave | `PageLayoutSaveEvent` |
| PageSchemaStateChange | `PageSchemaStateChangeEvent` |
| PartDetection | `PartDetectionCreateEvent`, `PartDetectionDeleteEvent`, `PartDetectionUpdateEvent` |
| ReferConfigGroup | `ReferConfigGroupDeleteEvent` |
| Select | `SelectEvent` |
| TransactionSuccess | `TransactionSuccessCreateBatchEvent`, `TransactionSuccessCreateEvent`, `TransactionSuccessDeleteBatchEvent`, `TransactionSuccessDeleteEvent`, `TransactionSuccessUpdateBatchEvent`, `TransactionSuccessUpdateEvent` |
| UdcEnum | `UdcEnumDeleteEvent` |
| UdcEnumCategory | `UdcEnumCategoryDeleteEvent` |
| UdcEnumItem | `UdcEnumItemCreateEvent`, `UdcEnumItemDeleteEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `AttributeEventListener` | 17 |
| `EntityEventListener` | 16 |
| `ApplicationEventListener` | 14 |
| `MicroFlowEventListener` | 12 |
| `DeployEventListener` | 7 |
| `FunctionNodeEventListener` | 6 |
| `PageEventListener` | 6 |
| `UdcPortalApplicationEventListener` | 6 |
| `SandboxEventListener` | 4 |
| `BasicDataEventListener` | 3 |
| `CtpEnumEventListener` | 3 |
| `CtpEnumItemEventListener` | 3 |
| `PartDetectionEventListener` | 3 |
| `DeductionEventListener` | 3 |
| `ExtendEventListener` | 3 |
| `UdcUserApplicationEventListener` | 3 |
| `CtpSerialSchemeEventListener` | 2 |
| `AttributeSetEventListener` | 2 |
| `UdcApplicationEventListener` | 2 |
| `DataFlowEventListener` | 2 |
| `CollaborationAppEventListener` | 1 |
| `DataTransferObjectEventListener` | 1 |
| `ReferConfigGroupEventListener` | 1 |
| `UdcEnumCategoryEventListener` | 1 |
| `UdcEnumEventListener` | 1 |
| `UdcEventEventListener` | 1 |
| `PageSchemaEventListener` | 1 |
| `UdcCdpApplicationEventListener` | 1 |

## web 层：Controller

共 62 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 推送/被引用（Refer*） | `ReferConfigController` | 12 |
| 核心实体 CRUD | `ApplicationController` | 74 |
| 核心实体 CRUD | `MicroFlowController` | 67 |
| 核心实体 CRUD | `UdcUpgradeController` | 64 |
| 核心实体 CRUD | `EntityController` | 55 |
| 核心实体 CRUD | `UdcDesignMetadataController` | 47 |
| 核心实体 CRUD | `MetaDataController` | 32 |
| 核心实体 CRUD | `PageInfoController` | 25 |
| 核心实体 CRUD | `DataFlowDesignController` | 24 |
| 核心实体 CRUD | `DataTransferObjectController` | 21 |
| 核心实体 CRUD | `FunctionNodeController` | 19 |
| 核心实体 CRUD | `PageLayoutController` | 18 |
| 核心实体 CRUD | `UdcRoleController` | 16 |
| 核心实体 CRUD | `DeductionRuleController` | 16 |
| 核心实体 CRUD | `PageTemplateController` | 14 |
| 核心实体 CRUD | `UdcManagerController` | 14 |
| 核心实体 CRUD | `EventController` | 13 |
| 核心实体 CRUD | `DeployController` | 12 |
| 核心实体 CRUD | `UdcEnumItemController` | 12 |
| 核心实体 CRUD | `AttributeSetController` | 10 |
| 核心实体 CRUD | `BackendComponentController` | 10 |
| 核心实体 CRUD | `MicroFlowFunctionalCheckController` | 9 |
| 核心实体 CRUD | `PageTemplatePublishedController` | 9 |
| 核心实体 CRUD | `UdcBasicDataController` | 8 |
| 核心实体 CRUD | `COLISplitController` | 8 |
| 核心实体 CRUD | `ScalabilityOptionController` | 8 |
| 核心实体 CRUD | `UdcEnumCategoryController` | 8 |
| 核心实体 CRUD | `UdcEnumController` | 8 |
| 核心实体 CRUD | `AttachmentTemplateController` | 7 |
| 核心实体 CRUD | `AttributeGroupController` | 7 |
| 核心实体 CRUD | `EntityGroupController` | 7 |
| 核心实体 CRUD | `IndexController` | 7 |
| 核心实体 CRUD | `MicroFlowGroupController` | 7 |
| 核心实体 CRUD | `PageTemplateClassController` | 7 |
| 核心实体 CRUD | `PortletController` | 7 |
| 核心实体 CRUD | `AppCollaborationController` | 6 |
| 核心实体 CRUD | `DataTypeController` | 6 |
| 核心实体 CRUD | `DeploymentController` | 6 |
| 核心实体 CRUD | `MicroFlowUpgradeController` | 6 |
| 核心实体 CRUD | `OperationLogController` | 6 |
| 核心实体 CRUD | `ParameterController` | 6 |
| 核心实体 CRUD | `ScalabilityController` | 6 |
| 核心实体 CRUD | `CtpApplicationCapabilityController` | 5 |
| 核心实体 CRUD | `MultiEditController` | 5 |
| 核心实体 CRUD | `SandboxController` | 5 |
| 核心实体 CRUD | `UdcCtpEnumController` | 5 |
| 核心实体 CRUD | `UdcSandBoxLogController` | 5 |
| 核心实体 CRUD | `UdcPortalSpaceController` | 4 |
| 核心实体 CRUD | `PortletGroupController` | 4 |
| 核心实体 CRUD | `MicroFlowRefactorController` | 3 |
| 核心实体 CRUD | `UdcReportController` | 2 |
| 核心实体 CRUD | `UdcPortalPortletController` | 2 |
| 核心实体 CRUD | `DependencyAnalysisController` | 2 |
| 核心实体 CRUD | `FeatureController` | 2 |
| 核心实体 CRUD | `MicroFlowMacroController` | 2 |
| 核心实体 CRUD | `UdcFileController` | 2 |
| 核心实体 CRUD | `UdcSerialController` | 1 |
| 核心实体 CRUD | `EntityOpenApiController` | 1 |
| 核心实体 CRUD | `PageRouteController` | 1 |
| 核心实体 CRUD | `PublishStateController` | 1 |
| 核心实体 CRUD | `StereotypeController` | 1 |
| 核心实体 CRUD | `TempPresetMicroFlowController` | 1 |

## 概念对照（udc 的名词）

| 平台术语 | 中文 | 关键 id |
|---|---|---|
| **application**（应用） | 一个低代码应用（含实体、页面、微流程） | `appId` |
| **guid** | 应用的稳定标识（跨版本不变，复制/迁移用） | `guid` |
| **entity**（实体） | 数据模型（对应一张物理表） | `entityId` |
| **attribute**（字段） | 实体字段 | `attributeId` |
| **dataTransferObject**（DTO） | 自定义对象（微流程出入参用，非实体） | `dtoId` |
| **enum / enumCategory / enumItem** | 枚举 / 枚举分类 / 枚举项 | `enumId` |
| **page** | 页面（表单/列表/流程页） | `pageId` |
| **layout** | 布局（页面外壳） | `layoutId` |
| **microflow** | 微流程（节点编排） | `microFlowId` |
| **dataflow** | 生单规则（数据流画布） | `dataFlowId` |
| **deploy** | 部署（设计态 → 运行态） | `deployRecordId` |

## 设计态与运行态是两套数据

```
设计态（MySQL）：udc_entity / udc_attribute / udc_application ...
                  ↑ ApplicationAppService / EntityAppService / AttributeAppService 写这里
                       ↓ deployNormal / deployForm 部署
运行态（Redis 180h → OSS）：metadata 快照
                  ↑ UdcMetaDataAppService 读这里（selectXxxMetaData*）
```

**⇒ 判据：**

- 要**改模型** → 调 `EntityAppService` / `AttributeAppService`（设计态）
- 要**读运行时结构**（页面渲染、微流程校验、流程取字段） → 调 `UdcMetaDataAppService`（运行态）

混用会拿到过期或空数据 —— 部署前的元数据在运行态里根本不存在。

## 建一个应用的完整链路（真实方法名）

```java
@Autowired private ApplicationManagerAppService appMgr;

// ① 建应用，返回 appId
SingleResponse<Long> appId = appMgr.create(SingleRequest.from(applicationDto));

// ② 建设计态应用（带成员/分类），或只用应用壳
appMgr.updateWithMember(SingleRequest.from(appWithMemberDto));

@Autowired private EntityAppService entitySvc;

// ③ 建实体（= 一张表），返回 entityId
SingleResponse<Long> entityId = entitySvc.create(SingleRequest.from(entityDto));

@Autowired private AttributeAppService attrSvc;

// ④ 建字段（可批量）
SingleResponse<Integer> n = attrSvc.createBatch(SingleRequest.from(List.of(attr1, attr2)));
// 系统内置字段用 createBatch4System（跳过用户字段校验）

// ⑤ 查实体下所有字段（建页面/生成代码前必做）
ListResponse<AttributeDto> attrs = attrSvc.selectAllAttributeByEntityId(SingleRequest.from(entityId));
```

## 部署（最容易出错的一步）

```java
@Autowired private ApplicationManagerAppService appMgr;

// 常规部署：入参 DeployNormalDto，返回 DeployParamDto
SingleResponse<DeployParamDto> r = appMgr.deployNormal(SingleRequest.from(deployNormalDto));

// 表单类应用部署
SingleResponse<DeployResultDto> r2 = appMgr.deployForm(SingleRequest.from(deployFormDto));
```

**REST 路径（此前实测可用，**`LIVE`** 级证据来自历史联调，不是本次会话重放）**：

```
POST /service/udc/runtime/deploy-normal
{
  "deployDto": {
    "appId": 8704025620829192834,
    "deployType": "TEST",
    "projectType": "ALL",
    "terminalType": "ALL"
  }
}
```

**两个部署钩子**（框架在部署前后回调，可用来做扩展）：

| 接口 | 方法 | 时机 |
|---|---|---|
| `DeployBeforeService` | `handle(AppContext)` → `boolean` | 部署前；返回 false 可中断 |
| `DeployFinishService` | `callback(DeployCallbackDto)` → `boolean` | 部署后 |

**⚠️ 部署后页面/微流程的改动要重新部署才生效** —— 只改设计态数据不部署，运行态看不到。

## 自定义对象（DTO）—— 微流程出入参就用它

```java
@Autowired private DataTransferObjectAppService dtoSvc;

// 建 DTO 并同时建它的字段，返回 id+字段
SingleResponse<Map<String,Object>> dto = dtoSvc.createDtoWithAttrs(SingleRequest.from(dtoDto));

// 带引用关系（DTO 套 DTO / 引实体）
SingleResponse<Long> withRef = dtoSvc.createDtoWithAttrsAndRefDtos(SingleRequest.from(List.of(dtoDto)));

// 读全量（含字段 + 引用）
ListResponse<DataTransferObjectDto> full = dtoSvc.selectDtoWithAttrsAndRefDtos(SingleRequest.from(dtoId));

// 微流程里可选的 DTO 列表（搭节点时选对象用）
ListResponse<DataTransferObjectDto> selectable = dtoSvc.searchSelectableDtoList(SingleRequest.from(queryDto));
ListResponse<DataTransferObjectDto> byFlow = dtoSvc.selectAllByMicroFlowId(SingleRequest.from(microFlowId));
```

**`*4EntityEvent` 后缀的方法**（`createDtoWithAttrs4EntityEvent`）是**实体事件触发时**的专用入口，
不要用它做常规建数据 —— 它带事件上下文参数。

## 读运行态元数据（生成代码/校验前必做）

```java
@Autowired private UdcMetaDataAppService meta;

// 应用全量元数据（生成页面代码用这个）
SingleResponse<UdcApplicationMetaData4PageCode> all = meta.selectAppMetaData4PageCode(SingleRequest.from(appId));

// 实体元数据（字段、类型、引用）
SingleResponse<UdcEntityMetaDataDto> e = meta.selectEntityMetaData(SingleRequest.from(searchDto));

// 聚合实体（含关联）
ListResponse<UdcEntityMetaDataDto> agg = meta.selectAggEntityIncludeAssociation(SingleRequest.from(searchDto));

// 页面元数据（取页面 schema，流程/微流程要字段时用）
SingleResponse<UdcPageMetadataV2Dto> page = meta.selectPageMetaData(SingleRequest.from(pageSearchDto));
ListResponse<UdcPageMetadataV2Dto> pagesForBpm = meta.selectPageSchema4Bpm(SingleRequest.from(list));

// 枚举元数据
ListResponse<CtpEnumDto> enums = meta.selectEnumMetaDataByAppId(SingleRequest.from(appId));
```

## UDC 与 bpm 的接缝

```java
// udc 侧：取流程默认布局应用名（发起页渲染用）
@Autowired private UdcBpmAppService udcBpm;
SingleResponse<String> layoutAppName = udcBpm.selectDefaultLayoutAppName();

// bpm 侧：从 UDC 发起流程 —— 用 BpmUdcApiService（见 bpm 模块）
//   sendForUdc / triggerFlowForUdc
```

**边界**：`udc` 管「应用/实体/页面/微流程」，`bpm` 管「流程实例」。
UDC 触发流程只调 `BpmUdcApiService`，不要调 `BpmAppService.send`。

## Agent 生成代码时的引用顺序（这是最常错的地方）

```
1. 先 assert 设计态存在        → EntityAppService.selectById / AttributeAppService.selectAllAttributeByEntityId
2. 再读运行态元数据            → UdcMetaDataAppService.selectAppMetaData4PageCode
3. 改完模型必须部署            → ApplicationManagerAppService.deployNormal
4. 部署后重新读运行态元数据     ← 不重读会用旧 schema 生成代码
```

**踩过两次的坑**：第 3 步没做就写第 4 步，拿到的还是旧字段列表；
第 1 步没做直接读运行态，实体刚建还没部署时返回空。

## 应用级操作速查

| 要做 | 方法 |
|---|---|
| 新建应用 | `ApplicationManagerAppService.create` |
| 复制应用 | `copyApp` / `copyAppAsync`（大批量用 async） |
| 移交应用（换负责人） | `handoverApp` |
| 导出应用 | `downloadApp` / `downloadAppAsync` |
| 导入应用 | `importApp` / `importAppWithDto` |
| 查依赖（被谁引用） | `getDependsByAppId` / `getShelfDepend` |
| 上架 | `ApplicationShelfService` |
| 查部署状态 | `selectAppDeployState` |
| 查部署记录 | `selectDeployRecordById` |
| 按 guid 取最新设计版本 | `selectLatestDesignAppByGuid` |

## 落表

> 证据等级：`VERIFIED_STATIC_BYTECODE`（表名出现在本模块 biz jar 的 class 常量池）
> ＋ `LIVE`（同名表已用 `information_schema` 在 `test2` 确认真实存在）。
> 粒度：**类级**。方法级落表未取证 —— 平台不用 MyBatis XML
> （21 个 biz 构件合计只有 9 个 mapper XML / 15 张表），SQL 内联在代码里，
> 方法→表要逐类反编译才能确认。

本模块代码中出现的真实表 **69** 张（来源构件：`udc-biz`）：

| 表名 | 注释 | 出现在几个类 |
|---|---|---:|
| `ctp_enum` | — | 22 |
| `ctp_parameter_definition` | — | 10 |
| `udc_enum_category` | — | 9 |
| `udc_enum` | — | 8 |
| `basic_data_attribute` | — | 6 |
| `basic_data_entity` | — | 6 |
| `ctp_enum_item` | — | 6 |
| `ctp_parameter` | — | 6 |
| `ctp_job_cron` | — | 5 |
| `ctp_job_info` | — | 5 |
| `ctp_job_simple` | — | 5 |
| `ctp_excel_export_template` | — | 4 |
| `ctp_enum_category` | — | 3 |
| `label_print_record` | — | 3 |
| `portal_space` | 空间 | 3 |
| `udc_app_collaboration` | — | 3 |
| `org_member_post` | 人员任职 | 2 |
| `udc_attribute` | — | 2 |
| `udc_enum_item` | — | 2 |
| `udc_index` | — | 2 |
| `ctp_serial_current` | — | 1 |
| `ctp_serial_range` | — | 1 |
| `ctp_serial_scheme` | — | 1 |
| `ctp_serial_section` | — | 1 |
| `org_job` | 职务 | 1 |
| `org_level` | 职级 | 1 |
| `org_member` | 人员 | 1 |
| `org_post` | 岗位 | 1 |
| `org_unit` | 组织信息 | 1 |
| `udc_app_custom_error` | — | 1 |
| `udc_app_version` | — | 1 |
| `udc_application` | — | 1 |
| `udc_attachment_template` | — | 1 |
| `udc_attribute_group` | — | 1 |
| `udc_attribute_set` | — | 1 |
| `udc_backend_component` | — | 1 |
| `udc_custom_data_type` | — | 1 |
| `udc_data_transfer_object` | — | 1 |
| `udc_dependent_application` | — | 1 |
| `udc_dto_attribute` | — | 1 |
| `udc_entity` | — | 1 |
| `udc_entity_group` | — | 1 |
| `udc_entity_preset` | — | 1 |
| `udc_event` | — | 1 |
| `udc_function_node` | — | 1 |
| `udc_last_version_metadata` | — | 1 |
| `udc_micro_flow_group` | — | 1 |
| `udc_microflow_info` | — | 1 |
| `udc_microflow_preset_template` | — | 1 |
| `udc_operation_log` | — | 1 |
| `udc_page_component` | — | 1 |
| `udc_page_component_category` | — | 1 |
| `udc_page_component_data_type` | — | 1 |
| `udc_page_data_source` | — | 1 |
| `udc_page_info` | — | 1 |
| `udc_page_layout` | — | 1 |
| `udc_page_schema` | — | 1 |
| `udc_page_template` | — | 1 |
| `udc_page_template_category` | — | 1 |
| `udc_page_template_published` | — | 1 |
| `udc_parameter` | — | 1 |
| `udc_portlet` | — | 1 |
| `udc_portlet_group` | — | 1 |
| `udc_push_association` | — | 1 |
| `udc_refer_config` | — | 1 |
| `udc_refer_config_group` | — | 1 |
| `udc_reference` | — | 1 |
| `udc_scalability` | — | 1 |
| `udc_scalability_option` | — | 1 |

### 接口 → 表（29 条）

> `implements` = 字节码声明实现了该接口；`implements+field` = 再经它持有的
> Manager/Dao 字段一跳；两者都是静态事实。`stem` 只是类名同源（弱证据，需实测）。
> 表名本身都 `VERIFIED`；**哪个方法写哪张表仍未取证**。

| facade 接口 | 承载类 | 表 | 依据 |
|---|---|---|---|
| `ApplicationManagerAppService` | `SchemaManager` | `basic_data_attribute`, `basic_data_entity`, `ctp_enum`, `ctp_enum_category`, `ctp_enum_item` | `implements+field` |
| `AsyncAppService` | `SchemaManager` | `basic_data_attribute`, `basic_data_entity`, `ctp_enum`, `ctp_enum_category`, `ctp_enum_item` | `implements+field` |
| `AttributeAppService` | `AttributeService` | `udc_attribute` | `implements+field` |
| `AttributeGroupAppService` | `AttributeGroup` | `udc_attribute_group` | `stem` |
| `AttributeSetAppService` | `AttributeSet` | `udc_attribute_set` | `stem` |
| `DataTransferObjectAppService` | `DataTransferObject` | `udc_data_transfer_object` | `stem` |
| `DeployBeforeService` | `UdcEnumService` | `udc_enum` | `implements+field` |
| `DtoAttributeAppService` | `DtoAttribute` | `udc_dto_attribute` | `stem` |
| `EntityAppService` | `Entity` | `udc_entity` | `stem` |
| `EntityGroupAppService` | `EntityGroup` | `udc_entity_group` | `stem` |
| `EntityPresetAppService` | `EntityPreset` | `udc_entity_preset` | `stem` |
| `EventAppService` | `Event` | `udc_event` | `stem` |
| `IndexAppService` | `IndexService` | `udc_index` | `implements+field` |
| `LastVersionMetadataManagerService` | `AttributeService` | `udc_attribute` | `implements+field` |
| `MicroFlowUpgradeAppService` | `UdcEnumService` | `udc_enum` | `implements+field` |
| `ParameterAppService` | `Parameter` | `udc_parameter` | `stem` |
| `PluginAttributeAppService` | `AttributeService` | `udc_attribute` | `implements+field` |
| `PluginEntityAppService` | `AttributeService` | `udc_attribute` | `implements+field` |
| `PluginPageInfoAppService` | `FunctionNodeService, ResoureParseService` | `portal_space` | `implements+field` |
| `ReferConfigAppService` | `ReferConfig` | `udc_refer_config` | `stem` |
| `ReferConfigGroupAppService` | `ReferConfigGroup` | `udc_refer_config_group` | `stem` |
| `ScalabilityAppService` | `Scalability` | `udc_scalability` | `stem` |
| `ScalabilityOptionAppService` | `ScalabilityOption` | `udc_scalability_option` | `stem` |
| `StereotypeAllAppService` | `AttributeService` | `udc_attribute` | `implements+field` |
| `UdcEnumAppService` | `UdcEnumService` | `udc_enum` | `implements+field` |
| `UdcEnumCategoryAppService` | `UdcEnumCategoryService` | `udc_enum`, `udc_enum_category` | `implements+field` |
| `UdcEnumItemAppService` | `UdcEnumService` | `udc_enum` | `implements+field` |
| `UdcFunctionAppService` | `FunctionNodeService` | `portal_space` | `implements+field` |
| `UdcMetaDataAppService` | `Application4PageMetaDataService` | `ctp_enum` | `implements+field` |

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

控制器 **54** 个、路由 **660** 条（来源：`udc-web`）。

> `{id}`、`ids` 这类方法级路径不带类级前缀，拼时必须补上。
> 完整清单（含 java 方法名）：`docs/audit/artifacts/rest/ROUTES-udc.md`

| Controller | 类级路径 | 路由 |
|---|---|---:|
| `ApplicationController` | `udc/application` | 72 |
| `MicroFlowController` | `udc/microflow` | 67 |
| `EntityController` | `udc/entity` | 54 |
| `UdcDesignMetadataController` | `udc/design-metadata` | 47 |
| `MetaDataController` | `udc/meta-data` | 32 |
| `PageInfoController` | `udc/page-info` | 25 |
| `DataFlowDesignController` | `udc/data-flow` | 23 |
| `DataTransferObjectController` | `udc/data-transfer-object` | 20 |
| `PageLayoutController` | `udc/page-layout` | 18 |
| `FunctionNodeController` | `udc/function` | 18 |
| `DeductionRuleController` | `udc/deduction` | 16 |
| `PageTemplateController` | `udc/page-template` | 14 |
| `UdcManagerController` | `udc/manager` | 13 |
| `ReferConfigController` | `udc/refer-config` | 12 |
| `EventController` | `udc/event` | 12 |
| `DeployController` | `udc/runtime` | 12 |
| `UdcEnumItemController` | `udc/udc-enum-item` | 11 |
| `BackendComponentController` | `udc/backend-component` | 10 |
| `AttributeSetController` | `udc/attributeSet` | 9 |
| `MicroFlowFunctionalCheckController` | `udc/micro-flow-functional-check` | 9 |
| `PageTemplatePublishedController` | `udc/page-template/published` | 9 |
| `COLISplitController` | `udc/app-split` | 8 |
| `ScalabilityOptionController` | `udc/scalability-option` | 7 |
| `UdcEnumCategoryController` | `udc/udc-enum-category` | 7 |
| `PageTemplateClassController` | `udc/page-template-class` | 7 |
| `AttachmentTemplateController` | `udc/attachment-template` | 7 |
| `UdcEnumController` | `udc/udc-enum` | 7 |
| `MicroFlowGroupController` | `udc/micro-flow-group` | 7 |
| `EntityGroupController` | `udc/entity-group` | 7 |
| `AttributeGroupController` | `udc/attribute-group` | 7 |
| `PortletController` | `udc/portlet` | 7 |
| `AppCollaborationController` | `udc/collaboration` | 6 |
| `DeploymentController` | `udc/deployment` | 6 |
| `IndexController` | `udc/index` | 6 |
| `DataTypeController` | `udc/data-type` | 6 |
| `MicroFlowUpgradeController` | `udc/micro-flow-upgrade` | 6 |
| `OperationLogController` | `udc/operation-log` | 6 |
| `UdcSandBoxLogController` | `udc/sandbox/logs` | 5 |
| `MultiEditController` | `udc/multi-edit` | 5 |
| `ScalabilityController` | `udc/scalability` | 5 |
| `SandboxController` | `udc/sandbox` | 5 |
| `UdcCtpEnumController` | `udc/udc-enum-item` | 5 |
| `ParameterController` | `—` | 5 |
| `PortletGroupController` | `udc/portlet-group` | 4 |
| `MicroFlowRefactorController` | `udc/microflow-refactor` | 3 |
| `UdcFileController` | `udc/runtime/file` | 2 |
| `FeatureController` | `udc/feature` | 2 |
| `DependencyAnalysisController` | `udc/dependency/analysis` | 2 |
| `MicroFlowMacroController` | `udc/micro-flow-macro` | 2 |
| `PublishStateController` | `udc/publish-state` | 1 |
| `EntityOpenApiController` | `udc/entity-open-api` | 1 |
| `TempPresetMicroFlowController` | `udc/preset/microflow` | 1 |
| `PageRouteController` | `udc/page-route` | 1 |
| `StereotypeController` | `udc/stereotype` | 1 |

前 15 条（其余见明细）：

| 方法 | 全路径 |
|---|---|
| `GetMapping` | `/service/udc/collaboration/{appId}` |
| `GetMapping` | `/service/udc/collaboration/members/{appGuid}` |
| `PostMapping` | `/service/udc/collaboration/create` |
| `PostMapping` | `/service/udc/collaboration/delete/{id}` |
| `PostMapping` | `/service/udc/collaboration/handover` |
| `PostMapping` | `/service/udc/collaboration/members` |
| `PostMapping` | `/service/udc/application/create-page-app` |
| `PostMapping` | `/service/udc/application/create-layout-app` |
| `PostMapping` | `/service/udc/application/delete-rename` |
| `PostMapping` | `/service/udc/application/delete` |
| `PostMapping` | `/service/udc/application/delete-by-guid` |
| `PostMapping` | `/service/udc/application/update` |
| `PostMapping` | `/service/udc/application/update-caption-for-all-version` |
| `GetMapping` | `/service/udc/application/version/platform` |
| `GetMapping` | `/service/udc/application/version/platform-service` |

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 67 接口 / 555 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 110 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 71 事件 / 28 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 62 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径（660 条） | Controller 字节码注解 | `VERIFIED_STATIC_BYTECODE` |
| REST 真机验证 | 374/374 条安全路由命中（100%） | `LIVE` |
| 落表（73 张表，类级） | class 常量池 + `information_schema` | `VERIFIED_STATIC_BYTECODE` + `LIVE` |
| 方法级落表 | 未取证（SQL 内联，需逐类反编译） | `UNVERIFIED` |
