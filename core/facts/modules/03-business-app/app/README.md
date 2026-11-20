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

## 入参 DTO（字段级）

> 字段来自字节码 `fields`（含继承链，最多 3 层）；**字段名即 JSON 键名**（平台用 Jackson 默认命名，`shortName` 对应库列 `short_name`）。
> 包装类已揭开：`SingleRequest<T>` / `ListResponse<T>` 里看的是 `T` 的字段。
> 等级 `VERIFIED_STATIC_BYTECODE`。全量字段表：`docs/audit/artifacts/dto/DTO-app.md`

本模块 **63** 个入参/返回 DTO，**62** 个能取到字段。Top 12（按出现次数）：

| DTO | 出现 | 字段数 | 关键字段 |
|---|---:|---:|---|
| `AgentDto` | 10 | 39 | `id`, `agentId`, `agentCode`, `agentName`, `agentToId`, `agentToCode`, `agentToName`, `cancelTime` |
| `ApplicationDto` | 6 | 32 | `effectTime`, `invalidTime`, `state`, `failReason`, `invalidReason`, `name`, `basePackage`, `caption` |
| `CategoryDto` | 5 | 11 | `id`, `originApp`, `name`, `code`, `orderNo`, `parentId`, `parentCode`, `categoryLevel` |
| `AgentInfoDto` | 4 | 27 | `id`, `agentId`, `agentName`, `agentToId`, `agentToName`, `startTime`, `endTime`, `templateIds` |
| `IntegralLedgerDto` | 4 | 28 | `operatorName`, `operatorUserName`, `operatorId`, `operatorDeptName`, `operatorDeptId`, `scorerName`, `scorerUserName`, `scorerId` |
| `CtpMgnAggDataDto` | 4 | 19 | `id`, `tenantId`, `dataType`, `contentField`, `mainEntity`, `mainEntityCh`, `orgField`, `appName` |
| `WorktimeYearDto` | 4 | 3 | `year`, `orgId`, `validate` |
| `SimpleAppInfoDto` | 3 | 5 | `name`, `caption`, `id`, `guid`, `validate` |
| `ThemeDto` | 3 | 14 | `id`, `name`, `description`, `status`, `primaryColor`, `globalStyleData`, `themeComponentData`, `publishStatus` |
| `WorktimeResDto` | 3 | 6 | `totalMins`, `years`, `days`, `hours`, `mins`, `validate` |
| `ApprovalOpsAuthDto` | 2 | 6 | `applicationName`, `designState`, `sourceType`, `currentUserId`, `loginOrgId`, `validate` |
| `AppSearchByParamDto` | 2 | 4 | `appGuids`, `appNames`, `orgId`, `validate` |

## 落表

> 证据等级：`VERIFIED_STATIC_BYTECODE`（表名出现在本模块 biz jar 的 class 常量池）
> ＋ `LIVE`（同名表已用 `information_schema` 在 `test2` 确认真实存在）。
> 粒度：**类级**。方法级落表未取证 —— 平台不用 MyBatis XML
> （21 个 biz 构件合计只有 9 个 mapper XML / 15 张表），SQL 内联在代码里，
> 方法→表要逐类反编译才能确认。

本模块代码中出现的真实表 **66** 张（来源构件：`app-common-biz`、`app-approval-biz`、`app-doc-biz`）：

| 表名 | 注释 | 出现在几个类 |
|---|---|---:|
| `sensitive_word` | — | 2 |
| `agent_detail` | — | 1 |
| `agent_scope` | — | 1 |
| `application_transport_record` | 跨环境推送记录表 | 1 |
| `approval_config` | 审批应用配置表 | 1 |
| `approval_form_app_depend` | 审批应用依赖管理 | 1 |
| `approval_frame` | 外框管理 | 1 |
| `approval_query_config` | 查询内容配置表 | 1 |
| `approval_query_group` | 查询分组配置表 | 1 |
| `associate_config` | — | 1 |
| `associate_entity_config` | — | 1 |
| `common_file_secret` | — | 1 |
| `common_parameter_configuration` | 系统参数表 | 1 |
| `common_service_metadata` | 元数据的应用列表 | 1 |
| `common_worktime_set` | — | 1 |
| `common_worktime_special` | — | 1 |
| `ctp_gray_app_swim` | — | 1 |
| `ctp_gray_application` | — | 1 |
| `ctp_gray_swim` | — | 1 |
| `ctp_gray_swim_org` | — | 1 |
| `ctp_gray_swim_tenant` | — | 1 |
| `ctp_gray_swim_user` | — | 1 |
| `ctp_locale` | — | 1 |
| `ctp_mgn_agg_data` | — | 1 |
| `ctp_mgn_main` | — | 1 |
| `ctp_mgn_main_relation` | — | 1 |
| `ctp_mgn_task` | — | 1 |
| `ctp_mgn_task_column_log` | — | 1 |
| `ctp_mgn_task_log` | — | 1 |
| `ctp_mgn_tenant_log` | — | 1 |
| `customized_development` | — | 1 |
| `customized_development_log` | — | 1 |
| `i18n_default_resource` | — | 1 |
| `i18n_resource` | — | 1 |
| `icon_category` | — | 1 |
| `icon_file` | — | 1 |
| `icon_relation` | — | 1 |
| `icon_tag` | — | 1 |
| `image_category` | — | 1 |
| `image_store` | — | 1 |
| `integral_expert_rank` | — | 1 |
| `integral_ledger` | — | 1 |
| `integral_medal` | — | 1 |
| `integral_medal_rule` | — | 1 |
| `integral_operation_rule` | — | 1 |
| `integral_rank` | — | 1 |
| `integral_rule` | — | 1 |
| `label_category` | 标签分类 | 1 |
| `label_cloud` | 标签云 | 1 |
| `label_department` | 标签部门使用情况 | 1 |
| `mgn_data_log` | 配置迁移数据日志表 | 1 |
| `mgn_entity_def` | 迁移实体定义 | 1 |
| `mgn_field_relation_def` | 字段关联定义 | 1 |
| `mgn_menu_def` | 配置项迁移菜单定义 | 1 |
| `mgn_package_info` | 迁移包信息 | 1 |
| `mgn_task_info` | 模块任务信息 | 1 |
| `my_attention` | — | 1 |
| `my_attention_category` | — | 1 |
| `ocr_authorization_object` | OCR授权对象表 | 1 |
| `ocr_authorization_rule` | OCR授权规则表 | 1 |
| `sensitive_word_white` | — | 1 |
| `system_inspect_record` | 巡检记录 | 1 |
| `theme_file` | 主题文件信息表 | 1 |
| `video_meeting_room` | 视频会议室 | 1 |
| `video_meeting_room_auth` | 视频会议室授权 | 1 |
| `video_meeting_room_auth_detail` | 视频会议室授权明细 | 1 |

### 接口 → 表（2 条）

> `implements` = 字节码声明实现了该接口；`implements+field` = 再经它持有的
> Manager/Dao 字段一跳；两者都是静态事实。`stem` 只是类名同源（弱证据，需实测）。
> 表名本身都 `VERIFIED`；**哪个方法写哪张表仍未取证**。

| facade 接口 | 承载类 | 表 | 依据 |
|---|---|---|---|
| `ImageCategoryAppService` | `ImageCategory` | `image_category` | `stem` |
| `ImageStoreAppService` | `ImageStore` | `image_store` | `stem` |

## 方法级落表（写接口）

> **口径：触及表的上界，不是「只写这张表」。** 证据链是「方法体引用的实体/DAO → 实体类 `@TableName` 字面量」，
> 方法若再做条件分支，实际只写其中一部分。判断影响面用它，判断唯一落点还得看 SQL。
> 等级 `VERIFIED_STATIC_BYTECODE`（引用与表名都来自字节码），**上界推断**部分标 `STATIC_INFERENCE`。

本模块 37 个写方法中，**14** 个解析出触及表：

| 接口#方法 | 触及表 | 依据（引用链） |
|---|---|---|
| `ImageCategoryAppService#deleteCategory` | `image_category` | `ImageCategoryDao=>ImageCategory->image_category` |
| `ImageCategoryAppService#save` | `image_category` | `ImageCategoryDao=>ImageCategory->image_category` |
| `ImageStoreAppService#deleteStore` | `image_store` | `ImageStoreDao=>ImageStore->image_store` |
| `ImageStoreAppService#save` | `image_store` | `ImageStoreDao=>ImageStore->image_store` |
| `IntegralLedgerOprateAppService#create` | `integral_ledger` | `IntegralLedgerDao=>IntegralLedger->integral_ledger` |
| `IntegralLedgerOprateAppService#createBatch` | `integral_ledger` | `IntegralLedgerDao=>IntegralLedger->integral_ledger` |
| `LabelAppService#updateReferenceCount` | `label_category`, `label_department` | `LabelCategoryDao=>LabelCategory->label_category; LabelDepartmentDao=>LabelDepartment->label_department` |
| `MgnAggDataInitAppService#create` | `ctp_mgn_agg_data` | `CtpMgnAggData->ctp_mgn_agg_data; CtpMgnAggDataDao=>CtpMgnAggData->ctp_mgn_agg_data` |
| `MgnAggDataInitAppService#update` | `ctp_mgn_agg_data` | `CtpMgnAggData->ctp_mgn_agg_data; CtpMgnAggDataDao=>CtpMgnAggData->ctp_mgn_agg_data` |
| `MyAttentionCommonAppService#create` | `my_attention` | `MyAttentionDao=>MyAttention->my_attention` |
| `MyAttentionCommonAppService#createOrUpdateBatch` | `my_attention` | `MyAttentionDao=>MyAttention->my_attention` |
| `MyAttentionCommonAppService#deleteBatchByObjectIds` | `my_attention` | `MyAttentionDao=>MyAttention->my_attention` |
| `MyAttentionCommonAppService#deleteByObjectIdOrPageUrl` | `my_attention` | `MyAttentionDao=>MyAttention->my_attention` |
| `MyAttentionCommonAppService#update` | `my_attention` | `MyAttentionDao=>MyAttention->my_attention` |

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

控制器 **73** 个、路由 **674** 条（来源：`app-common-web`、`app-approval-web`、`app-doc-web`）。

> `{id}`、`ids` 这类方法级路径不带类级前缀，拼时必须补上。
> 完整清单（含 java 方法名）：`docs/audit/artifacts/rest/ROUTES-app.md`

| Controller | 类级路径 | 路由 |
|---|---|---:|
| `ApprovalApplicationController` | `app-approval/application` | 48 |
| `KnowledgePediaController` | `app-doc/pedia` | 39 |
| `KnowledgeAlbumController` | `app-doc/album` | 37 |
| `KnowledgeMapController` | `app-doc/map` | 27 |
| `GraySwimlaneController` | `app-common/gray/swimlane` | 19 |
| `IntegralController` | `app-common/integral` | 18 |
| `MyAttentionController` | `app-common/attention` | 18 |
| `AgentSetController` | `app-common/agent` | 18 |
| `I18nManagerController` | `app-common/i18n` | 18 |
| `FormDataQueryController` | `app-approval/form-query` | 18 |
| `PackageInfoController` | `app-common/config-mgn/package` | 16 |
| `PhraseController` | `app-common/phrase` | 16 |
| `ThemeController` | `app-common/theme` | 15 |
| `AssociateController` | `app-common/associate` | 14 |
| `IconController` | `app-common/icon` | 14 |
| `GrayApplicationController` | `app-common/gray/application` | 13 |
| `LocaleController` | `app-common/locale` | 13 |
| `MngPushController` | `app-common/mgn/push` | 13 |
| `WorktimeController` | `app-common/worktime` | 13 |
| `WorktimeSpecialController` | `app-common/worktime-special` | 13 |
| `ConfigMgnController` | `app-common/config-mgn` | 13 |
| `ImageController` | `app-common/image` | 13 |
| `QuestionInfoController` | `app-doc/quiz/question-info` | 13 |
| `SensitiveWordCommonController` | `app-common/sensitive-word` | 12 |
| `MgnTenantController` | `app-common/mgn/tenant` | 11 |
| `LabelController` | `app-common/label` | 10 |
| `DemoController` | `app-approval/demo/` | 10 |
| `KnowledgeClassController` | `app-doc/manage/class` | 10 |
| `ApprovalOutlineBorderController` | `app-approval/outline-border` | 9 |
| `KnowledgeHomePageController` | `app-doc/knowledge/home-page` | 9 |
| `LabelCategoryController` | `app-common/label-category` | 8 |
| `MngReceiveController` | `app-common/mgn/receive` | 8 |
| `SystemConfigController` | `app-common/system-config` | 8 |
| `ApprovalTransportController` | `app-approval/transport` | 8 |
| `QuestionReplyController` | `app-doc/quiz/question-replay` | 8 |
| `UserQuestionController` | `app-doc/quiz/user` | 8 |
| `KnowledgeRoleController` | `app-doc/manage/role` | 8 |
| `CustomizedDevelopmentController` | `app-common/customized/development` | 7 |
| `CategoryController` | `app-common/category` | 7 |
| `SealController` | `app-common/seal` | 6 |
| `TenantLocaleController` | `app-common/tenant-locale` | 6 |
| `SensitiveWordWhiteController` | `app-common/sensitive-white` | 5 |
| `MyAttentionCategoryController` | `app-common/attention/category` | 5 |
| `SystemInspectController` | `app-common/system-inspect` | 5 |
| `OcrAuthorizationController` | `app-common/ocr/authorization` | 5 |
| `SeeyonMonitorController` | `app-common/system/monitor` | 5 |
| `ApprovalProcessTeamController` | `app-approval/process-team` | 5 |
| `CommonParameterConfigurationController` | `app-common/common-parameter-configuration` | 4 |
| `WaterMarkController` | `app-common/watermark` | 4 |
| `ApprovalDepApplicationController` | `app-approval/dependent-application` | 4 |
| `QuestionSystemController` | `app-doc/quiz/question-preset` | 4 |
| `LabelCloudController` | `app-common/label-cloud` | 3 |
| `VideoMeetingRoomController` | `app-common/videoMeetingRoom` | 3 |
| `DocController` | `app-doc/doc` | 3 |
| `QuestionSystemConfigController` | `app-doc/quiz/system-config` | 3 |
| `DocAppSysConfigController` | `app-doc/app/sys-config` | 3 |
| `FormRefreshController` | `/form` | 2 |
| `ApprovalBasicDataController` | `app-approval/basic-data-runtime` | 2 |
| `QuestionAuditController` | `app-doc/quiz/question-replay` | 2 |
| `WareHouseController` | `app-doc/warehouse` | 2 |
| `AiConfigController` | `app-common/ai` | 1 |
| `AppCommonAffairController` | `app-common/affair-center` | 1 |
| `SystemEnvironmentController` | `app-common/system-env` | 1 |
| `AppApprovalUpgradeController` | `app-approval/upgrade/` | 1 |
| `ApprovalMenuController` | `app-approval/menu` | 1 |
| `ApprovalConfigController` | `app-approval/config` | 1 |
| `AlbumSystemConfigController` | `app-doc/album/setting` | 1 |
| `MapSystemConfigController` | `app-doc/setting` | 1 |
| `DocLibController` | `app-doc/lib` | 1 |
| `DocShareController` | `app-doc/share` | 1 |
| `PediaSystemConfigController` | `app-doc/pedia/setting` | 1 |
| `DocKnowledgeIntegralController` | `app-doc/knowledge/integral` | 1 |
| `CopyStorageKeyController` | `app-doc/storageKey` | 1 |

前 15 条（其余见明细）：

| 方法 | 全路径 |
|---|---|
| `GetMapping` | `/service/app-doc/album/setting/permission` |
| `PostMapping` | `/service/app-doc/album/save-draft` |
| `PostMapping` | `/service/app-doc/album/publish-album` |
| `PostMapping` | `/service/app-doc/album/audit-album` |
| `PostMapping` | `/service/app-doc/album/essence-album` |
| `PostMapping` | `/service/app-doc/album/top-album` |
| `PostMapping` | `/service/app-doc/album/delete-album` |
| `PostMapping` | `/service/app-doc/album/batch-essence-album` |
| `PostMapping` | `/service/app-doc/album/batch-delete-album` |
| `PostMapping` | `/service/app-doc/album/select-audit-history` |
| `PostMapping` | `/service/app-doc/album/home-page-collection` |
| `PostMapping` | `/service/app-doc/album/search-my-album` |
| `PostMapping` | `/service/app-doc/album/home-page-my-album` |
| `PostMapping` | `/service/app-doc/album/search-un-audited` |
| `PostMapping` | `/service/app-doc/album/search-audited` |

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 22 接口 / 119 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 190 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 7 事件 / 8 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 73 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径（674 条） | Controller 字节码注解 | `VERIFIED_STATIC_BYTECODE` |
| REST 真机验证 | 182/182 条安全路由命中（100%） | `LIVE` |
| 落表（72 张表，类级） | class 常量池 + `information_schema` | `VERIFIED_STATIC_BYTECODE` + `LIVE` |
| 方法级落表 | 未取证（SQL 内联，需逐类反编译） | `UNVERIFIED` |
