# 通用应用（app）

## 一句话

`com.seeyon.app` 域的**可调用接口面**：9 个构件、1,539 个类、22 个 facade 接口 / 119 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `app-common-biz` | biz | 628 |
| `app-doc-biz` | biz | 477 |
| `app-approval-biz` | biz | 232 |
| `app-common-facade` | facade | 103 |
| `app-common-web` | web | 39 |
| `app-approval-facade` | facade | 25 |
| `app-doc-web` | web | 22 |
| `app-approval-web` | web | 12 |
| `app-doc-facade` | facade | 1 |
| **合计** | | **1,539** |

## 二、分层规律（写代码前必读）

`com.seeyon.app` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

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

## facade 层：22 个接口 / 119 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.app.approval.api` | 3 | 24 |
| `com.seeyon.app.common.agent.api` | 2 | 19 |
| `com.seeyon.app.common.associate.api` | 1 | 3 |
| `com.seeyon.app.common.attention.api` | 1 | 9 |
| `com.seeyon.app.common.category.api` | 1 | 12 |
| `com.seeyon.app.common.image.api` | 3 | 12 |
| `com.seeyon.app.common.integral.api` | 1 | 4 |
| `com.seeyon.app.common.label.api` | 1 | 3 |
| `com.seeyon.app.common.mgn.api` | 1 | 4 |
| `com.seeyon.app.common.qrcode.api` | 1 | 2 |
| `com.seeyon.app.common.seal.api` | 1 | 3 |
| `com.seeyon.app.common.style.api` | 1 | 1 |
| `com.seeyon.app.common.system.api` | 1 | 4 |
| `com.seeyon.app.common.theme.api` | 1 | 4 |
| `com.seeyon.app.common.videomeeting.api` | 1 | 2 |
| `com.seeyon.app.common.watermark.api` | 1 | 1 |
| `com.seeyon.app.common.worktime.api` | 1 | 12 |
| **合计** | **22** | **119** |

### `com.seeyon.app.approval.api`

#### ApprovalAppService

`com.seeyon.app.approval.api.ApprovalAppService` · 构件 `app-approval-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getApprovalPageSchemaAndPermissionByAffairId` | `SingleRequest<Long> arg0` | `SingleResponse<ApprovalPageSchemaAndPermissionDto>` | 分页获取审批结构权限And按事项 |
| `getFormDataByGraphql` | `SingleRequest<ApprovalGraphqlRequestDto> arg0` | `SingleResponse<String>` | 获取表单数据按Graphql |
| `autoGenerateApplication` | `SingleRequest<AutoApplicationDto> arg0` | `SingleResponse<AutoGenerateResponseDto>` | 生成应用 |
| `deleteByAppIdList` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Void>` | 删除Void按应用 |

#### ApprovalFrameApiTransportAppService

`com.seeyon.app.approval.api.ApprovalFrameApiTransportAppService` · 构件 `app-approval-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `exportApprovalFrameInfo` | `SingleRequest<ApprovalFrameParamDto> arg0` | `SingleResponse<String>` | 导出审批Frame |

#### ApprovalInvokeAppService

`com.seeyon.app.approval.api.ApprovalInvokeAppService` · 构件 `app-approval-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `appOpsAuth` | `SingleRequest<ApprovalOpsAuthDto> arg0` | `SingleResponse<Void>` | 审批调用：应用运维授权校验 |
| `selectCurrentTenantFormApps` | `PageRequest arg0` | `PageResponse<SimpleAppInfoDto>` | 查询当前表单Apps |
| `selectByGuidAndVersion` | `SingleRequest<AppSearchByGuidDto> arg0` | `SingleResponse<ApplicationDto>` | 查询应用按版本 |
| `selectApplicationByGuid` | `SingleRequest<List<Long>> arg0` | `ListResponse<ApplicationDto>` | 查询应用按Guid |
| `selectApplicationByParams` | `SingleRequest<AppSearchByParamDto> arg0` | `ListResponse<ApplicationDto>` | 查询应用按Params |
| `selectApplicationByNames` | `SingleRequest<AppSearchByNameDto> arg0` | `ListResponse<ApplicationDto>` | 查询应用按名称 |
| `selectApplicationDmlFileById` | `SingleRequest<Long> arg0` | `SingleResponse<DmlFileDto>` | 查询应用文件Dml按 id |
| `createApplicationByMap` | `SingleRequest<Map<String, String>> arg0` | `SingleResponse<Void>` | 新建应用按Map |
| `updateApplicationOrgInfoByMap` | `SingleRequest<Map<String, String>> arg0` | `SingleResponse<Void>` | 修改应用组织按Map |
| `hasSuperFormAuth` | `SingleRequest<ApprovalOpsAuthDto> arg0` | `SingleResponse<Boolean>` | 判断有表单认证Super |
| `filterApplicationForTenant` | `SingleRequest<List<String>> arg0` | `ListResponse<SimpleAppInfoDto>` | 按租户过滤可访问应用 |
| `selectPermissionApprovalFrames` | `SingleRequest<ApprovalFrameSearchDto> arg0` | `ListResponse<ApprovalFrameDto>` | 查询权限审批Frames |
| `selectCurrentTenantFormAppGuids` | `SingleRequest<AppSearchByParamDto> arg0` | `ListResponse<Long>` | 查询当前表单应用Guids |
| `searchDeployFrameList` | `SingleRequest<String> arg0` | `ListResponse<ApprovalFrameDto>` | 列表搜索部署Frame |
| `getNormalApps` | `SingleRequest<ApplicationPageRequestDto> arg0` | `ListResponse<ApplicationDto>` | 获取NormalApps |
| `selectEditableAppIds` | `SingleRequest<ApplicationPageRequestDto> arg0` | `ListResponse<ApplicationDto>` | 查询应用EditableIds |
| `createOrUpdateTemporaryData` | `SingleRequest<AppDraftDto> arg0` | `SingleResponse<Integer>` | 新建数据OrUpdateTemporary |
| `deleteAllTemporaryData` | `SingleRequest<String> arg0` | `SingleResponse<Integer>` | 全部删除数据Temporary |
| `selectPublishedFormAppByOrgId` | `PageRequest arg0` | `PageResponse<SimpleAppInfoDto>` | 查询表单应用Published按组织 |

### `com.seeyon.app.common.agent.api`

#### AgentCommonAppService

`com.seeyon.app.common.agent.api.AgentCommonAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectByAgentUserId` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<AgentInfoDto>` | 查询Agent按用户 |
| `hasAgent` | `SingleRequest<AgentParamDto> arg0` | `SingleResponse<Map<String, Object>>` | 判断有Agent |
| `selectByUserIdAndTemplate` | `SingleRequest<AgentParamDto> arg0` | `ListResponse<AgentInfoDto>` | 查询Agent按用户模板 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<AgentInfoDto>` | 查询Agent按 id |
| `create` | `SingleRequest<AgentDto> arg0` | `SingleResponse<Long>` | 新建Agent |
| `update` | `SingleRequest<AgentDto> arg0` | `SingleResponse<Integer>` | 修改Agent |
| `deleteAgent` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 删除Agent |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<AgentDto>` | 列表查询Agent按条件 |
| `selectEffectiveAgentList` | `SingleRequest<AgentEffectiveRequestDto> arg0` | `ListResponse<AgentDto>` | 列表查询EffectiveAgent |

#### AgentCoreAppService

`com.seeyon.app.common.agent.api.AgentCoreAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<AgentInfoDto>` | 列表查询Agent按条件 |
| `create` | `SingleRequest<AgentDto> arg0` | `SingleResponse<Long>` | 新建Agent |
| `update` | `SingleRequest<AgentDto> arg0` | `SingleResponse<Integer>` | 修改Agent |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<AgentDto>` | 查询Agent按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<AgentDto>` | 查询Agent按 ids |
| `selectPageByCondition` | `PageRequest arg0` | `PageResponse<AgentDto>` | 分页查询Agent按条件 |
| `selectBizAgentPageByCondition` | `PageRequest arg0` | `PageResponse<AgentDto>` | 分页查询BizAgent按条件 |
| `cancelAgent` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 取消Agent |
| `batch` | `SingleRequest<List<AgentDto>> arg0` | `SingleResponse<Integer>` | Agent 核心：批量调用入口 |
| `getAgentProperties` | `—` | `SingleResponse<AgentPropertiesSetDto>` | 指定字段获取Agent |

### `com.seeyon.app.common.associate.api`

#### AssociateCommonAppService

`com.seeyon.app.common.associate.api.AssociateCommonAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectEntityConfigByConditions` | `ListRequest arg0` | `ListResponse<AssociateEntityReferDto>` | 查询实体配置按条件 |
| `selectAssociateCompleteByAppName` | `SingleRequest<String> arg0` | `ListResponse<AssociateCompleteDto>` | 查询AssociateComplete按应用名称 |
| `selectAssociateCompleteByControlCodes` | `ListRequest arg0` | `ListResponse<AssociateCompleteDto>` | 查询AssociateComplete按编码 |

### `com.seeyon.app.common.attention.api`

#### MyAttentionCommonAppService

`com.seeyon.app.common.attention.api.MyAttentionCommonAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<MyAttentionDto> arg0` | `SingleResponse<Long>` | 新建MyAttention |
| `createOrUpdateBatch` | `SingleRequest<List<MyAttentionDto>> arg0` | `SingleResponse<Integer>` | 批量新建OrUpdate |
| `deleteBatchByObjectIds` | `SingleRequest<MyAttentionBatchDeleteDto> arg0` | `SingleResponse<Integer>` | 批量删除MyAttentionDelete按ObjectIds |
| `deleteByObjectIdOrPageUrl` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 删除按页面（SingleRequest） |
| `isAttention` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Boolean>` | 判断Attention |
| `getAttentionByObjectIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<List<MyAttentionQueryDto>>` | 获取Attention按ObjectIds |
| `getAttentionUserIdsByObjectIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<Long>` | 获取用户AttentionIds按ObjectIds |
| `update` | `SingleRequest<MyAttentionDto> arg0` | `SingleResponse<Integer>` | 修改MyAttention |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<MyAttentionQueryDto>` | 分页查询MyAttentionQuery按条件 |

### `com.seeyon.app.common.category.api`

#### CategoryCommonAppService

`com.seeyon.app.common.category.api.CategoryCommonAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<CategoryDto> arg0` | `SingleResponse<Long>` | 新建分类 |
| `createBatch` | `SingleRequest<CategorySyncBatchDto> arg0` | `SingleResponse<Integer>` | 批量新建分类 |
| `update` | `SingleRequest<CategoryDto> arg0` | `SingleResponse<Integer>` | 修改分类 |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<CategoryDto>` | 查询分类按 id |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CategoryDto>` | 列表查询分类按条件 |
| `selectTreeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<CategoryTreeDto>` | 树查询分类按 ids |
| `selectChildrenById` | `SingleRequest<Long> arg0` | `ListResponse<Long>` | 查询下级按 id |
| `selectChildrenByCode` | `SingleRequest<String> arg0` | `ListResponse<Long>` | 查询下级按编码 |
| `checkCategoryBatch` | `SingleRequest<List<CategoryDto>> arg0` | `SingleResponse<List<CategoryRelationMapDto>>` | 批量检查分类 |
| `getCategoryDataInitResult` | `SingleRequest<String> arg0` | `SingleResponse<List<CategoryRelationMapDto>>` | 获取分类数据InitResult |
| `selectAllParentByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<CategoryDto>` | 全部查询上级按 ids |

### `com.seeyon.app.common.image.api`

#### ImageAppService

`com.seeyon.app.common.image.api.ImageAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<List<ImageDto>> arg0` | `SingleResponse<Boolean>` | 新建（SingleRequest） |
| `update` | `SingleRequest<List<ImageDto>> arg0` | `SingleResponse<Integer>` | 修改（SingleRequest） |
| `selectImage` | `PageRequest arg0` | `PageResponse<ImageDto>` | 查询Image |
| `deleteImage` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除Image |

#### ImageCategoryAppService

`com.seeyon.app.common.image.api.ImageCategoryAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `save` | `SingleRequest<ImageCategoryDto> arg0` | `SingleResponse<Long>` | 保存分类 |
| `selectImageCategory` | `SingleRequest<Long> arg0` | `ListResponse<ImageCategoryDto>` | 查询分类Image |
| `deleteCategory` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除分类 |
| `selectCountByCategoryId` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 查询Count按分类 |

#### ImageStoreAppService

`com.seeyon.app.common.image.api.ImageStoreAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `save` | `SingleRequest<ImageStoreDto> arg0` | `SingleResponse<Long>` | 保存ImageStore |
| `selectImageStore` | `—` | `ListResponse<ImageStoreDto>` | 查询ImageStore |
| `deleteStore` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除Store |
| `selectStoreAndCategory` | `—` | `ListResponse<ImageStoreAndCategoryDto>` | 查询分类StoreAnd |

### `com.seeyon.app.common.integral.api`

#### IntegralLedgerOprateAppService

`com.seeyon.app.common.integral.api.IntegralLedgerOprateAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<IntegralLedgerDto> arg0` | `SingleResponse<IntegralLedgerDto>` | 新建IntegralLedger |
| `createBatch` | `SingleRequest<List<IntegralLedgerDto>> arg0` | `SingleResponse<List<IntegralLedgerDto>>` | 批量新建（SingleRequest） |
| `selectPageByConditions` | `PageDtoRequest<IntegralLedgerDto> arg0` | `PageResponse<IntegralLedgerDto>` | 分页查询IntegralLedger按条件 |
| `selectRankById` | `SingleRequest<Long> arg0` | `SingleResponse<IntegralRankResultDto>` | 查询Rank按 id |

### `com.seeyon.app.common.label.api`

#### LabelAppService

`com.seeyon.app.common.label.api.LabelAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `updateReferenceCount` | `SingleRequest<LabelDepartmentDto> arg0` | `SingleResponse<Boolean>` | 修改ReferenceCount |
| `batchUpdateReferenceCount` | `SingleRequest<LabelUpdateCountDto> arg0` | `SingleResponse<Boolean>` | 修改ReferenceCount |
| `batchSelectLabelDtos` | `SingleRequest<List<Long>> arg0` | `ListResponse<LabelDto>` | 查询标签Dtos |

### `com.seeyon.app.common.mgn.api`

#### MgnAggDataInitAppService

`com.seeyon.app.common.mgn.api.MgnAggDataInitAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpMgnAggDataDto>` | 列表查询MgnAgg按条件 |
| `selectListByMap` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpMgnAggDataDto>` | 列表查询MgnAgg按Map |
| `create` | `SingleRequest<CtpMgnAggDataDto> arg0` | `SingleResponse<Long>` | 新建MgnAgg |
| `update` | `SingleRequest<CtpMgnAggDataDto> arg0` | `SingleResponse<Integer>` | 修改MgnAgg |

### `com.seeyon.app.common.qrcode.api`

#### QrCodeCommonAppService

`com.seeyon.app.common.qrcode.api.QrCodeCommonAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<QrCodeCreateDto> arg0` | `SingleResponse<QrCodeResultDto>` | 新建编码 |
| `selectByJson` | `SingleRequest<String> arg0` | `SingleResponse<QrCodeDto>` | 查询编码按Json |

### `com.seeyon.app.common.seal.api`

#### SealCommonAppService

`com.seeyon.app.common.seal.api.SealCommonAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectUsableList` | `ListRequest arg0` | `ListResponse<SealDto>` | 列表查询Usable |
| `checkSealPassword` | `SingleRequest<SealPasswordCheckDto> arg0` | `SingleResponse<Boolean>` | 检查密码Seal |
| `selectListByCondition` | `ListRequest arg0` | `ListResponse<SealDto>` | 列表查询Seal按条件 |

### `com.seeyon.app.common.style.api`

#### StyleFileAppService

`com.seeyon.app.common.style.api.StyleFileAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getCurrentTenantPortalFile` | `—` | `SingleResponse<StyleFileDto>` | 获取当前文件Portal |

### `com.seeyon.app.common.system.api`

#### SystemConfigCommonAppService

`com.seeyon.app.common.system.api.SystemConfigCommonAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getI18nConfig` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<I18nConfigDto>` | 获取配置I18n |
| `getSystemConfig` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<SystemConfigDto>` | 获取配置System |
| `saveSystemConfig` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 保存配置System |
| `getLocaleParameterByUserIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Map<Long, String>>` | 获取参数Locale按用户 |

### `com.seeyon.app.common.theme.api`

#### ThemeAppService

`com.seeyon.app.common.theme.api.ThemeAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<ThemeDto>` | 查询主题按 id |
| `create` | `SingleRequest<ThemeDto> arg0` | `SingleResponse<Long>` | 新建主题 |
| `selectPagePropertiesByConditions` | `PageRequest arg0` | `PageResponse<ThemeDto>` | 分页指定字段查询主题按条件 |
| `publishById` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 发布按 id（SingleRequest） |

### `com.seeyon.app.common.videomeeting.api`

#### VideoMeetingRoomCommonAppService

`com.seeyon.app.common.videomeeting.api.VideoMeetingRoomCommonAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<VideoMeetingRoomDto>` | 查询VideoMeetingRoom按 id |
| `selectAuthedVideoMeetingRoomList` | `—` | `ListResponse<VideoMeetingRoomDto>` | 列表查询AuthedVideoMeetingRoom |

### `com.seeyon.app.common.watermark.api`

#### WaterMarkCommonAppService

`com.seeyon.app.common.watermark.api.WaterMarkCommonAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getWaterMarkConfig` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<WaterMarkConfigDto>` | 获取配置WaterMark |

### `com.seeyon.app.common.worktime.api`

#### WorktimeAppService

`com.seeyon.app.common.worktime.api.WorktimeAppService` · 构件 `app-common-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectWorktimeByOrgIdAndYear` | `SingleRequest<WorktimeYearDto> arg0` | `SingleResponse<WorktimeDto>` | 查询Worktime按组织 |
| `selectByOrgIdAndYear` | `SingleRequest<WorktimeYearDto> arg0` | `SingleResponse<WorktimeSetDto>` | 查询WorktimeYear按组织 |
| `getByParentOrgIdAndYear` | `SingleRequest<WorktimeYearDto> arg0` | `SingleResponse<WorktimeSetDto>` | 获取WorktimeYear按上级组织 |
| `getWorkTimeByYear` | `SingleRequest<WorktimeYearDto> arg0` | `SingleResponse<WorktimeResDto>` | 获取WorkTime按Year |
| `getWorkTimeBetweenYear` | `SingleRequest<WorktimeBetweenYearDto> arg0` | `SingleResponse<WorktimeResDto>` | 获取WorkTimeBetweenYear |
| `getWorkTimeBetweenDate` | `SingleRequest<WorktimeDateTimeDto> arg0` | `SingleResponse<WorktimeResDto>` | 获取WorkTimeBetweenDate |
| `getWorkEndDate` | `SingleRequest<WorktimeAfterTimeDto> arg0` | `SingleResponse<Date>` | 获取WorkEndDate |
| `getWorkDayType` | `SingleRequest<WorktimeDateDto> arg0` | `SingleResponse<WorkDayTypeDto>` | 获取类型WorkDay |
| `getFestivalByYear` | `SingleRequest<Integer> arg0` | `ListResponse<WorktimeFestivalDto>` | 获取Festival按Year |
| `selectSpecifyWorkDay` | `SingleRequest<WorkDayRequestDto> arg0` | `SingleResponse<Date>` | 查询SpecifyWorkDay |
| `selectNonWorkDayList` | `SingleRequest<WorktimeDateTimeDto> arg0` | `ListResponse<String>` | 列表查询NonWorkDay |
| `syncWorktimeSpecialDay` | `SingleRequest<WorktimeSyncSpecialDayDto> arg0` | `SingleResponse<Integer>` | 同步WorktimeSpecialDay |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 190 个领域服务，下表列**方法数最多的 40 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `I18nManagerService` | 128 | 负责人 · 获取×25 / 查询×15 / 导出×7 |
| `KnowledgePediaService` | 61 | KnowledgePedia · 查询×22 / 检查×7 / 删除×6 |
| `ApplicationService` | 60 | 应用 · 查询×36 / 修改×5 / 获取×4 |
| `LocaleService` | 50 | Locale · 获取×10 / 查询×8 / 设置×2 |
| `AgentService` | 48 | Agent · 查询×12 / 检查×8 / 获取×4 |
| `DocKnowledgeClassService` | 47 | DocKnowledgeClass · 查询×23 / 新建×3 / 修改×3 |
| `DocKnowledgeAlbumService` | 46 | DocKnowledgeAlbum · 查询×19 / 保存×5 / 检查×5 |
| `KnowledgeMapService` | 45 | KnowledgeMap · 查询×18 / 保存×5 / 检查×5 |
| `WorktimeService` | 44 | Worktime · 获取×22 / 查询×8 / 删除×2 |
| `ThemeService` | 41 | 主题 · 查询×12 / 发布×8 / 新建×3 |
| `GraySwimlaneService` | 36 | GraySwimlane · 获取×9 / 查询×5 / 检查×3 |
| `SystemInspectService` | 36 | SystemInspect · 构建×16 / 获取×4 / 同步×3 |
| `CategoryService` | 31 | 分类 · 查询×12 / 获取×4 / 新建×2 |
| `ApprovalFrameService` | 29 | 审批 · 获取×5 / 查询×5 / 处理×4 |
| `WorktimeSpecialService` | 28 | WorktimeSpecial · 删除×6 / 获取×6 / 查询×4 |
| `DocDubboMemberService` | 28 | 成员 · 查询×25 |
| `GrayAppService` | 27 | 应用 · 获取×4 / 修改×3 / 查询×3 |
| `MyAttentionService` | 25 | MyAttention · 获取×6 / 新建×4 / 查询×3 |
| `WareHouseService` | 24 | WareHouse · 查询×7 / 设置×4 / 新建×3 |
| `DocAppSysConfigService` | 22 | 应用配置 · 新建×6 / 查询×3 / 同步×3 |
| `PhraseService` | 20 | Phrase · 查询×8 / 删除×4 / 修改×3 |
| `MgnConfigEnvService` | 19 | 配置 · 获取×4 / 判断×4 / 对比×1 |
| `IconService` | 19 | Icon · 获取×5 / 修改×3 / 查询×2 |
| `KnowledgeHomePageService` | 19 | 页面 · 查询×6 / 转换×3 / 检查×2 |
| `GrayCacheService` | 18 | GrayCache · 获取×6 / 运行×3 / 删除×3 |
| `LabelService` | 17 | 标签 · 查询×7 / 修改×4 / 检查×2 |
| `DocAlbumDirectoryService` | 17 | DocAlbumDirectory · 查询×7 / 保存×2 / 删除×1 |
| `DocIntegralOperationalService` | 17 | DocIntegralOperational · 获取×3 / 新建×3 / 发布×2 |
| `MapIndexService` | 17 | MapIndex · 新建×4 / 修改×3 / 删除×3 |
| `DocPediaDirectoryService` | 17 | DocPediaDirectory · 查询×4 / 保存×3 / 删除×2 |
| `PackageManagerService` | 16 | 负责人 · 修改×5 / 查询×4 / 转换×3 |
| `PullPackageManagerService` | 16 | 负责人 · 查询×5 / 转换×2 / 确认×1 |
| `AlbumCacheService` | 16 | AlbumCache · 查询×4 / 解析×3 |
| `DocAppSysPublishScopeService` | 16 | 应用范围 · 新建×6 / 修改×5 / 删除×4 |
| `MapCacheService` | 16 | MapCache · 查询×4 / 解析×3 |
| `PediaCacheService` | 16 | PediaCache · 查询×4 / 解析×3 |
| `PediaIndexService` | 16 | PediaIndex · 新建×4 / 修改×3 / 删除×3 |
| `FormQueryGroupService` | 15 | 分组 · 查询×4 / 获取×4 / 新建×2 |
| `ClassAuthorityService` | 15 | ClassAuthority · 查询×9 / 获取×2 / 发布×2 |
| `DocQuestionIndexService` | 15 | DocQuestionIndex · 新建×4 / 删除×3 / 保存×3 |

## biz 层：事件与监听

事件 7 个 · 监听器 8 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| ApplicationOnline | `ApplicationOnlineEvent` |
| KnowledgeAlbumAsync | `KnowledgeAlbumAsyncUpdateEvent` |
| KnowledgeMapAsync | `KnowledgeMapAsyncUpdateEvent` |
| KnowledgePediaAsync | `KnowledgePediaAsyncUpdateEvent` |
| KnowledgeToESOperate | `KnowledgeToESOperateEvent` |
| SyncWorkTimeSetToChildren | `SyncWorkTimeSetToChildrenEvent` |
| SyncWorkTimeSpecialToChildren | `SyncWorkTimeSpecialToChildrenEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `AfterTenantEventListener` | 3 |
| `KnowledgeAlbumEventListener` | 3 |
| `KnowledgeEventListener` | 3 |
| `KnowledgePediaEventListener` | 3 |
| `ReplyCommentEventListener` | 3 |
| `AgentEventListener` | 2 |
| `ExternalFileEventListener` | 1 |
| `ThemeFileAfterTenantEventListener` | 1 |

## web 层：Controller

共 73 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 核心实体 CRUD | `ApprovalApplicationController` | 48 |
| 核心实体 CRUD | `KnowledgePediaController` | 39 |
| 核心实体 CRUD | `KnowledgeAlbumController` | 37 |
| 核心实体 CRUD | `KnowledgeMapController` | 27 |
| 核心实体 CRUD | `AgentSetController` | 19 |
| 核心实体 CRUD | `GraySwimlaneController` | 19 |
| 核心实体 CRUD | `FormDataQueryController` | 18 |
| 核心实体 CRUD | `MyAttentionController` | 18 |
| 核心实体 CRUD | `I18nManagerController` | 18 |
| 核心实体 CRUD | `IntegralController` | 18 |
| 核心实体 CRUD | `SensitiveWordCommonController` | 17 |
| 核心实体 CRUD | `PackageInfoController` | 16 |
| 核心实体 CRUD | `PhraseController` | 16 |
| 核心实体 CRUD | `AssociateController` | 15 |
| 核心实体 CRUD | `ThemeController` | 15 |
| 核心实体 CRUD | `IconController` | 14 |
| 核心实体 CRUD | `ConfigMgnController` | 13 |
| 核心实体 CRUD | `GrayApplicationController` | 13 |
| 核心实体 CRUD | `ImageController` | 13 |
| 核心实体 CRUD | `LocaleController` | 13 |
| 核心实体 CRUD | `MngPushController` | 13 |
| 核心实体 CRUD | `WorktimeController` | 13 |
| 核心实体 CRUD | `WorktimeSpecialController` | 13 |
| 核心实体 CRUD | `QuestionInfoController` | 13 |
| 核心实体 CRUD | `MgnTenantController` | 11 |
| 核心实体 CRUD | `DemoController` | 10 |
| 核心实体 CRUD | `LabelController` | 10 |
| 核心实体 CRUD | `KnowledgeClassController` | 10 |
| 核心实体 CRUD | `ApprovalOutlineBorderController` | 9 |
| 核心实体 CRUD | `KnowledgeHomePageController` | 9 |
| 核心实体 CRUD | `ApprovalTransportController` | 8 |
| 核心实体 CRUD | `LabelCategoryController` | 8 |
| 核心实体 CRUD | `MngReceiveController` | 8 |
| 核心实体 CRUD | `SystemConfigController` | 8 |
| 核心实体 CRUD | `KnowledgeRoleController` | 8 |
| 核心实体 CRUD | `QuestionReplyController` | 8 |
| 核心实体 CRUD | `UserQuestionController` | 8 |
| 核心实体 CRUD | `CategoryController` | 7 |
| 核心实体 CRUD | `CustomizedDevelopmentController` | 7 |
| 核心实体 CRUD | `SealController` | 7 |
| 核心实体 CRUD | `TenantLocaleController` | 6 |
| 核心实体 CRUD | `SeeyonMonitorController` | 6 |
| 核心实体 CRUD | `OcrAuthorizationController` | 6 |
| 核心实体 CRUD | `SensitiveWordWhiteController` | 6 |
| 核心实体 CRUD | `SystemInspectController` | 6 |
| 核心实体 CRUD | `ApprovalProcessTeamController` | 5 |
| 核心实体 CRUD | `MyAttentionCategoryController` | 5 |
| 核心实体 CRUD | `ApprovalDepApplicationController` | 4 |
| 核心实体 CRUD | `CommonParameterConfigurationController` | 4 |
| 核心实体 CRUD | `WaterMarkController` | 4 |
| 核心实体 CRUD | `QuestionSystemController` | 4 |
| 核心实体 CRUD | `LabelCloudController` | 3 |
| 核心实体 CRUD | `VideoMeetingRoomController` | 3 |
| 核心实体 CRUD | `DocController` | 3 |
| 核心实体 CRUD | `DocAppSysConfigController` | 3 |
| 核心实体 CRUD | `QuestionSystemConfigController` | 3 |
| 核心实体 CRUD | `ApprovalBasicDataController` | 2 |
| 核心实体 CRUD | `ApprovalConfigController` | 2 |
| 核心实体 CRUD | `FormRefreshController` | 2 |
| 核心实体 CRUD | `QuestionAuditController` | 2 |
| 核心实体 CRUD | `WareHouseController` | 2 |
| 核心实体 CRUD | `AppApprovalUpgradeController` | 1 |
| 核心实体 CRUD | `ApprovalMenuController` | 1 |
| 核心实体 CRUD | `AppCommonAffairController` | 1 |
| 核心实体 CRUD | `AiConfigController` | 1 |
| 核心实体 CRUD | `SystemEnvironmentController` | 1 |
| 核心实体 CRUD | `AlbumSystemConfigController` | 1 |
| 核心实体 CRUD | `DocLibController` | 1 |
| 核心实体 CRUD | `DocShareController` | 1 |
| 核心实体 CRUD | `CopyStorageKeyController` | 1 |
| 核心实体 CRUD | `DocKnowledgeIntegralController` | 1 |
| 核心实体 CRUD | `MapSystemConfigController` | 1 |
| 核心实体 CRUD | `PediaSystemConfigController` | 1 |

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
| 22 接口 / 119 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 190 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 7 事件 / 8 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 73 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径 | 未取证 | `UNVERIFIED` |
| 落表 | 未取证 | `UNVERIFIED` |
