# 组织架构（organization）

## 一句话

`com.seeyon.organization` 域的**可调用接口面**：3 个构件、1,103 个类、55 个 facade 接口 / 421 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `organization-biz` | biz | 621 |
| `organization-facade` | facade | 414 |
| `organization-web` | web | 68 |
| **合计** | | **1,103** |

## 二、分层规律（写代码前必读）

`com.seeyon.organization` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

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

## facade 层：55 个接口 / 421 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.organization.api.app.affair` | 1 | 1 |
| `com.seeyon.organization.api.app.appcommon` | 1 | 2 |
| `com.seeyon.organization.api.app.authorization` | 1 | 1 |
| `com.seeyon.organization.api.app.edoc` | 1 | 1 |
| `com.seeyon.organization.api.app.m5` | 1 | 2 |
| `com.seeyon.organization.api.app.ocip` | 4 | 20 |
| `com.seeyon.organization.api.app.platform` | 1 | 1 |
| `com.seeyon.organization.api.app.portal` | 1 | 10 |
| `com.seeyon.organization.api.app.sync` | 11 | 47 |
| `com.seeyon.organization.api.app.third.zhonghe` | 1 | 14 |
| `com.seeyon.organization.api.app.workflow` | 1 | 37 |
| `com.seeyon.organization.api.common` | 1 | 45 |
| `com.seeyon.organization.api.core.business` | 2 | 12 |
| `com.seeyon.organization.api.core.institution` | 1 | 1 |
| `com.seeyon.organization.api.core.job` | 2 | 20 |
| `com.seeyon.organization.api.core.level` | 2 | 20 |
| `com.seeyon.organization.api.core.member` | 2 | 31 |
| `com.seeyon.organization.api.core.memberpost` | 2 | 18 |
| `com.seeyon.organization.api.core.memberrole` | 2 | 17 |
| `com.seeyon.organization.api.core.metadata` | 1 | 16 |
| `com.seeyon.organization.api.core.orgrole` | 2 | 17 |
| `com.seeyon.organization.api.core.post` | 2 | 20 |
| `com.seeyon.organization.api.core.systemteam` | 1 | 5 |
| `com.seeyon.organization.api.core.unit` | 2 | 33 |
| `com.seeyon.organization.api.core.unitteam` | 1 | 8 |
| `com.seeyon.organization.api.core.unitvertical` | 2 | 11 |
| `com.seeyon.organization.api.parameter` | 1 | 1 |
| `com.seeyon.organization.api.selectpeople.department` | 1 | 3 |
| `com.seeyon.organization.api.selectpeople.institution` | 1 | 2 |
| `com.seeyon.organization.api.selectpeople.member` | 1 | 2 |
| `com.seeyon.organization.api.tenant` | 1 | 1 |
| `com.seeyon.organization.appservice.api.app.workflow` | 1 | 2 |
| **合计** | **55** | **421** |

### `com.seeyon.organization.api.app.affair`

#### OrgAffairAppService

`com.seeyon.organization.api.app.affair.OrgAffairAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectByIdOrCode` | `SingleRequest<List<OrgEntityIdCodeDto>> arg0` | `ListResponse<OrgEntityIdCodeDto>` | 按 id 或 code 批量查实体（事项侧调用组织） |

### `com.seeyon.organization.api.app.appcommon`

#### OrgAppCommonAppService

`com.seeyon.organization.api.app.appcommon.OrgAppCommonAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectAccessViewMember` | `SingleRequest<List<Long>> arg0` | `ListResponse<Long>` | 过滤出有访问权限的人员 id |
| `selectAccessViewOrg` | `SingleRequest<List<Long>> arg0` | `ListResponse<Long>` | 过滤出有访问权限的组织 id |

### `com.seeyon.organization.api.app.authorization`

#### AuthorizationAppService

`com.seeyon.organization.api.app.authorization.AuthorizationAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `registerAppResourceAndPermission` | `SingleRequest<AuthorizationResourceAndPermissionDto> arg0` | `SingleResponse<String>` | 向组织注册应用资源与权限点，返回权限码 |

### `com.seeyon.organization.api.app.edoc`

#### OrgEdocAppService

`com.seeyon.organization.api.app.edoc.OrgEdocAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectSortByIds` | `SingleRequest<SearchSortDto> arg0` | `SingleResponse<List<Map<Long, Integer>>>` | 按 id 批量取排序号（公文侧） |

### `com.seeyon.organization.api.app.m5`

#### OrgMobileAppService

`com.seeyon.organization.api.app.m5.OrgMobileAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectPagePhoneNumber` | `PageRequest arg0` | `PageResponse<String>` | 移动端：分页取手机号 |
| `selectOfflineStorageKey` | `SingleRequest arg0` | `SingleResponse<String>` | 移动端：取离线存储 key |

### `com.seeyon.organization.api.app.ocip`

#### OcipLevelAppService

`com.seeyon.organization.api.app.ocip.OcipLevelAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `pushAll` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 全部推送（SingleRequest） |
| `pushAllByIncrement` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 全部推送按Increment（SingleRequest） |
| `pushBatch` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 批量推送（SingleRequest） |
| `pushLevelIncrement` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 增量推送职务级别 |

#### OcipMemberAppService

`com.seeyon.organization.api.app.ocip.OcipMemberAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `pushAll` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 全部推送（SingleRequest） |
| `pushAllByIncrement` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 全部推送按Increment（SingleRequest） |
| `pushBatch` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 批量推送（SingleRequest） |
| `pushMemberIncrement` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 增量推送成员 |

#### OcipPostAppService

`com.seeyon.organization.api.app.ocip.OcipPostAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `pushAll` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 全部推送（SingleRequest） |
| `pushAllByIncrement` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 全部推送按Increment（SingleRequest） |
| `pushBatch` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 批量推送（SingleRequest） |
| `pushPostIncrement` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 增量推送岗位 |

#### OcipUnitAppService

`com.seeyon.organization.api.app.ocip.OcipUnitAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `pushAccountAll` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 全部推送账户 |
| `pushAccountAllByIncrement` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 全部推送账户按Increment |
| `pushAccountBatch` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 批量推送账户 |
| `pushAccountIncrement` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 增量推送账户 |
| `pushDepartmentAll` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 全部推送部门 |
| `pushDepartmentAllByIncrement` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 全部推送部门按Increment |
| `pushDepartmentIncrement` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 增量推送部门 |
| `pushDepartmentBatch` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 批量推送部门 |

### `com.seeyon.organization.api.app.platform`

#### OrgPlatformAppService

`com.seeyon.organization.api.app.platform.OrgPlatformAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectWatermarkInfoByMemberId` | `SingleRequest<Long> arg0` | `SingleResponse<Map<String, Object>>` | 按人员 id 取水印信息（安全水印） |

### `com.seeyon.organization.api.app.portal`

#### OrgPortalAppService

`com.seeyon.organization.api.app.portal.OrgPortalAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectSwitchInstitution` | `PageRequest arg0` | `PageResponse<Map<String, Object>>` | 门户：可切换机构分页列表 |
| `selectSwitchInstitutions` | `SingleRequest arg0` | `ListResponse<Map<String, Object>>` | 查询切换Institutions |
| `selectSwitchInstitutionByMemberId` | `SingleRequest<Long> arg0` | `ListResponse<Map<String, Object>>` | 门户：某人员可切换的机构列表 |
| `selectLoginUserInfo` | `SingleRequest<Long> arg0` | `SingleResponse<Map<String, Object>>` | 门户：登录用户信息 |
| `selectCurrentLoginUserInfo` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Map<String, Object>>` | 查询当前登录用户 |
| `isOrgAdmin` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Boolean>` | 判断是否组织管理员 |
| `selectMainMemberPostByMemberId` | `SingleRequest<Long> arg0` | `SingleResponse<OrgMemberPostCoreDto>` | 取人员主岗 |
| `selectMainMemberPostByMemberIdsIgnoreTenant` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Map<Long, OrgMemberPostCoreDto>>` | 批量取主岗（跨租户） |
| `selectMainMemberPostByMemberIdsAllTenant` | `SingleRequest<List<Map<String, Object>>> arg0` | `SingleResponse<Map<Long, OrgMemberPostCoreDto>>` | 批量取主岗（全部租户） |
| `selectPeopleTabCustomSet` | `—` | `SingleResponse<Map<String, String>>` | 选人页签自定义配置 |

### `com.seeyon.organization.api.app.sync`

#### MultiOrgDepSyncService

`com.seeyon.organization.api.app.sync.MultiOrgDepSyncService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `multiOrgCreateBatch` | `SingleRequest<MultiOrgDepSyncBatchDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建组织 |
| `selectPageChildrenByCondition` | `PageDtoRequest<MultiOrgDepSyncSearchChildDto> arg0` | `PageResponse<MultiOrgDepSyncSearchResponse>` | 分页查询下级按条件 |

#### MultiOrgMemberSyncService

`com.seeyon.organization.api.app.sync.MultiOrgMemberSyncService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `MultiOrgMemberCreateBatch` | `SingleRequest<MultiOrgMemberSyncBatchDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 多组织架构下批量新建人员（多 org code 归属），返回同步结果 |
| `selectByCodes` | `PageDtoRequest<MultiOrgMemberSyncSearchByOrgCodeDto> arg0` | `PageResponse<MultiOrgMemberSyncSearchByOrgCodeResponse>` | 查询组织成员编码按编码 |

#### MultiOrgSyncService

`com.seeyon.organization.api.app.sync.MultiOrgSyncService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `multiOrgCreateBatch` | `SingleRequest<MultiOrgSyncBatchDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建组织 |
| `selectByCodes` | `SingleRequest<MultiOrgSyncSearchDto> arg0` | `ListResponse<MultiOrgSyncSearchResponse>` | 查询组织按编码 |

#### OrgJobSyncAppService

`com.seeyon.organization.api.app.sync.OrgJobSyncAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectByCodes` | `SingleRequest<SearchJobApiDto> arg0` | `ListResponse<OrgJobDataDto>` | 查询任务API按编码 |
| `createBatch` | `SingleRequest<OrgBatchJobDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建任务 |
| `selectPageByConditions` | `PageDtoRequest<SearchPostListApiDto> arg0` | `PageResponse<OrgJobDataDto>` | 分页查询岗位API按条件 |
| `selectByThirds` | `SingleRequest<SearchJobByThirdIdApiDto> arg0` | `ListResponse<OrgJobDataDto>` | 查询任务第三方API按第三方 |

#### OrgLevelSyncAppService

`com.seeyon.organization.api.app.sync.OrgLevelSyncAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectByCodes` | `SingleRequest<SearchLevelApiDto> arg0` | `ListResponse<OrgLevelDataDto>` | 查询职务级别API按编码 |
| `createBatch` | `SingleRequest<OrgBatchLevelDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建职务级别 |
| `selectPageByConditions` | `PageDtoRequest<SearchLevelListApiDto> arg0` | `PageResponse<OrgLevelDataDto>` | 分页查询职务级别API按条件 |
| `selectByThirdIds` | `SingleRequest<SearchLevelByThirdIdApiDto> arg0` | `ListResponse<OrgLevelDataDto>` | 查询职务级别第三方API按第三方 |

#### OrgMemberRoleSyncService

`com.seeyon.organization.api.app.sync.OrgMemberRoleSyncService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createBatch` | `SingleRequest<OrgBatchMemberRoleDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建成员角色 |

#### OrgMemberSyncAppService

`com.seeyon.organization.api.app.sync.OrgMemberSyncAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createBatch` | `SingleRequest<OrgBatchMemberDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建成员 |
| `selectByCodes` | `SingleRequest<SearchMemberConditionApiDto> arg0` | `ListResponse<OrgMemberDataDto>` | 查询成员条件API按编码 |
| `selectByThirdIds` | `SingleRequest<SearchMemberConditionApiDto> arg0` | `ListResponse<OrgMemberDataDto>` | 查询成员条件API按第三方 |
| `selectByCondition` | `PageDtoRequest<SearchMemberApiDto> arg0` | `PageResponse<OrgMemberDataDto>` | 查询成员API按条件 |
| `createBatchMemberPost` | `SingleRequest<OrgBatchMemberPostDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建成员岗位 |
| `createBatchMemberMetadata` | `SingleRequest<OrgBatchMetadataDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建成员扩展属性 |
| `fixCtpUserId` | `SingleRequest<OrgUserFixDto> arg0` | `SingleResponse<OrgUserFixDto>` | 修正用户Ctp |
| `disableMember` | `SingleRequest<String> arg0` | `SingleResponse<Integer>` | 停用成员 |
| `disableMemberByThirdIds` | `SingleRequest<String> arg0` | `SingleResponse<Integer>` | 停用成员按第三方 |
| `selectNaturalMemberByPhoneNumber` | `SingleRequest<String> arg0` | `SingleResponse<OrgNaturalMemberDataDto>` | 查询成员Natural按编号 |
| `selectNaturalMemberByCodes` | `SingleRequest<SearchMemberConditionApiDto> arg0` | `ListResponse<OrgNaturalMemberDataDto>` | 查询成员Natural按编码 |
| `selectNaturalMemberInfoPageListByCondition` | `PageDtoRequest<SearchMemberListApiDto> arg0` | `PageResponse<OrgNaturalMemberDataDto>` | 分页列表查询成员Natural按条件 |
| `selectOutSideInstitutionManagerPageByCondition` | `PageDtoRequest<SearchOutSideManagerApiDto> arg0` | `PageResponse<OrgOutsideUnitManagerDto>` | 分页查询机构负责人OutSide按条件 |
| `createBatchNaturalMember` | `SingleRequest<OrgBatchNaturalMemberDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建成员Natural |

#### OrgPostSyncAppService

`com.seeyon.organization.api.app.sync.OrgPostSyncAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createBatch` | `SingleRequest<OrgBatchPostDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建岗位 |
| `selectByCodes` | `SingleRequest<SearchPostApiDto> arg0` | `ListResponse<OrgPostDataDto>` | 查询岗位API按编码 |
| `selectPageByConditions` | `PageDtoRequest<SearchPostListApiDto> arg0` | `PageResponse<OrgPostDataDto>` | 分页查询岗位API按条件 |
| `selectByThirdIds` | `SingleRequest<SearchPostByThirdIdApiDto> arg0` | `ListResponse<OrgPostDataDto>` | 查询岗位第三方API按第三方 |

#### OrgRoleSyncService

`com.seeyon.organization.api.app.sync.OrgRoleSyncService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createBatch` | `SingleRequest<OrgBatchOrgRoleDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建组织角色 |
| `selectByCodes` | `SingleRequest<List<String>> arg0` | `ListResponse<OrgRoleDataDto>` | 查询角色按编码 |

#### OrgTeamSyncAppService

`com.seeyon.organization.api.app.sync.OrgTeamSyncAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectByCode` | `SingleRequest<String> arg0` | `SingleResponse<OrgTeamDataDto>` | 查询团队按编码 |
| `selectPageByConditions` | `PageDtoRequest<SearchTeamListApiDto> arg0` | `PageResponse<OrgTeamDataDto>` | 分页查询团队API按条件 |
| `create` | `SingleRequest<OrgTeamDataDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 新建团队 |
| `createBatch` | `SingleRequest<OrgBatchTeamDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建团队 |

#### OrgUnitSyncAppService

`com.seeyon.organization.api.app.sync.OrgUnitSyncAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createBatch` | `SingleRequest<OrgBatchUnitDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建单位 |
| `createBatchUnitMetadata` | `SingleRequest<OrgBatchMetadataDto> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建单位扩展属性 |
| `selectByCodes` | `SingleRequest<SearchUnitConditionApiDto> arg0` | `ListResponse<OrgUnitDataDto>` | 查询单位条件API按编码 |
| `selectByThirdIds` | `SingleRequest<SearchUnitConditionApiDto> arg0` | `ListResponse<OrgUnitDataDto>` | 查询单位条件API按第三方 |
| `selectChildrenByCondition` | `SingleRequest<SearchUnitApiDto> arg0` | `ListResponse<OrgUnitDataDto>` | 查询下级按条件 |
| `selectPageChildrenByCondition` | `PageDtoRequest<SearchUnitApiDto> arg0` | `PageResponse<OrgUnitDataDto>` | 分页查询下级按条件 |
| `disableOrganization` | `SingleRequest<OrgDisableUnitDto> arg0` | `SingleResponse<Integer>` | 停用Organization |
| `selectPageByConditions` | `PageDtoRequest<SearchUnitListApiDto> arg0` | `PageResponse<OrgUnitDataDto>` | 分页查询单位API按条件 |

### `com.seeyon.organization.api.app.third.zhonghe`

#### OrgZhongheService

`com.seeyon.organization.api.app.third.zhonghe.OrgZhongheService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectMemberByRole` | `SingleRequest<String> arg0` | `ListResponse<MemberRoleDto>` | 查询成员按角色 |
| `selectOrgByMetadataCustomizeZBBM` | `SingleRequest<SearchOrgDto> arg0` | `ListResponse<SearchOrgResultDto>` | 查询组织按扩展属性 |
| `selectOrgListByMetadata` | `SingleRequest<SearchOrgDto> arg0` | `ListResponse<SearchOrgResultDto>` | 列表查询组织按扩展属性 |
| `selectOrgTreeByMetadata` | `SingleRequest<SearchOrgDto> arg0` | `ListResponse<SearchOrgResultDto>` | 树查询组织按扩展属性 |
| `selectEnumItemValueById` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 查询枚举ItemValue按 id |
| `selectEnumItemValueByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Map<Long, String>>` | 查询枚举ItemValue按 ids |
| `selectLeadersBySecretary` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Map<Long, List<Long>>>` | 查询Leaders按Secretary |
| `selectSecretaryListByLeaderId` | `SingleRequest<Long> arg0` | `ListResponse<LeaderSecretaryDto>` | 列表查询Secretary按领导 |
| `selectLeaderListBySecretaryId` | `SingleRequest<Long> arg0` | `ListResponse<LeaderSecretaryDto>` | 列表查询领导按SecretaryId |
| `selectOrgTreeReceiveDept` | `SingleRequest<SearchOrgDto> arg0` | `ListResponse<SearchOrgResultDto>` | 树查询组织部门Receive |
| `selectRecOrgTree` | `SingleRequest<List<Long>> arg0` | `ListResponse<SearchOrgResultDto>` | 树查询组织Rec |
| `getCurrentSectorOrgList` | `SingleRequest<Long> arg0` | `ListResponse<SearchOrgResultDto>` | 列表获取当前组织Sector |
| `getOtherSectorOrgList` | `SingleRequest<Long> arg0` | `ListResponse<SearchOrgResultDto>` | 列表获取组织OtherSector |
| `getOrgUnitTeamOrgCount` | `SingleRequest<OrgUnitTeamSearchDto> arg0` | `SingleResponse<Integer>` | 获取组织单位团队Count |

### `com.seeyon.organization.api.app.workflow`

#### OrgWorkFlowAppService

`com.seeyon.organization.api.app.workflow.OrgWorkFlowAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectMemberPostBySelectPeople` | `SingleRequest<WorkFlowMatchRequestDto> arg0` | `SingleResponse<WorkFlowMatchResponseDto>` | 流程选人：按节点选人规则匹配出「人员+岗位」，入参含流程上下文 |
| `selectMemberPostBySelectPeoples` | `SingleRequest<Map<Long, List<WorkFlowMatchRequestDto>>> arg0` | `SingleResponse<Map<Long, List<WorkFlowMatchResponseDto>>>` | 流程选人：批量（多节点）匹配人员+岗位 |
| `selectMemberPostBySelectPeoplesReturnFile` | `SingleRequest<WorkFlowMatchRequestCustomModeDto> arg0` | `SingleResponse<WorkFlowMatchResponseToFileDto>` | 流程选人：结果落文件，返回文件 key（结果集大时用） |
| `selectReturnFileByKey` | `SingleRequest<WorkFlowSelectStorageKeyRequestDto> arg0` | `SingleResponse<Map<Long, WorkFlowMatchResponseFileKeyDto>>` | 按 key 取回上次落文件的结果 |
| `deleteReturnFileByKey` | `SingleRequest<WorkFlowSelectStorageKeyRequestDto> arg0` | `SingleResponse<Boolean>` | 删除上次落文件的结果 |
| `selectListByCondition` | `SingleRequest<WorkFlowConditionMatchRequestDto> arg0` | `ListResponse<Long>` | 流程选人：按条件匹配出人员 id 列表 |
| `selectListByMetaCondition` | `SingleRequest<List<WorkFlowConditionMetaMatchRequestDto>> arg0` | `SingleResponse<Map<String, List<Object>>>` | 流程选人：按扩展属性条件匹配 |
| `isOfUp` | `SingleRequest<SelectPeopleDataWfDto> arg0` | `SingleResponse<Boolean>` | 流程选人：判断是否「向上找」规则 |
| `selectOfUp` | `SingleRequest<SelectPeopleDataWfDto> arg0` | `SingleResponse<WorkFlowOfUpDto>` | 流程选人：按「向上找」规则解析 |
| `selectPreParameterKey` | `SingleRequest<List<SelectPeopleDataWfDto>> arg0` | `ListResponse<String>` | 流程选人：预取参数 key（提前准备上下文） |
| `selectMemberOfUnitMetadataOfMemberIds` | `SingleRequest<Map<String, SuperviseConditionDto>> arg0` | `SingleResponse<Map<String, List<Long>>>` | 流程选人：按单位扩展属性匹配人员 |
| `selectMemberOfMemberMetadataOfMemberIds` | `SingleRequest<Map<String, SuperviseConditionDto>> arg0` | `SingleResponse<Map<String, List<Long>>>` | 流程选人：按人员扩展属性匹配人员 |
| `selectMetadataListOfUnitMetadataOfMemberId` | `SingleRequest<SuperviseMetadataConditionDto> arg0` | `SingleResponse<List<String>>` | 流程选人：取单人单位扩展属性值列表 |
| `selectMetadataListOfMemberMetadataOfMemberId` | `SingleRequest<SuperviseMetadataConditionDto> arg0` | `SingleResponse<List<String>>` | 流程选人：取单人人员扩展属性值列表 |
| `funcMemberIn` | `SingleRequest<FunctionInDto> arg0` | `SingleResponse<Boolean>` | 流程函数「人员属于」判断 |
| `funcOrgIn` | `SingleRequest<FunctionInDto> arg0` | `SingleResponse<Boolean>` | 流程函数「组织属于」判断 |
| `funcMultMemberIn` | `SingleRequest<FunctionInDto> arg0` | `SingleResponse<Boolean>` | 流程函数「多人属于」判断 |
| `funcMultOrgIn` | `SingleRequest<FunctionInDto> arg0` | `SingleResponse<Boolean>` | 流程函数「多组织属于」判断 |
| `funcOrgRoleIn` | `SingleRequest<FunctionOrgRoleInDto> arg0` | `SingleResponse<Boolean>` | 流程函数「组织角色属于」判断 |
| `selectMemberPostById` | `SingleRequest<Long> arg0` | `ListResponse<OrgMemberPostWfDto>` | 按 id 查人员岗位关系（流程用 DTO） |
| `getSelectPeopleDataWfJson` | `SingleRequest<List<WorkFlowDataTestRequestDto>> arg0` | `SingleResponse<SelectPeopleDataDto>` | 流程选人：生成选人数据 JSON（调试/预览用） |
| `selectSplitUnitNodeInfo` | `SingleRequest<WorkFlowMatchRequestDto> arg0` | `SingleResponse<List<WorkFlowSplitUnitNodeResponseDto>>` | 流程选人：按单位拆分节点信息（分部门办理） |
| `selectSplitMemberNodeInfo` | `SingleRequest<WorkFlowSplitMemberNodeRequestDto> arg0` | `SingleResponse<List<WorkFlowSplitMemberNodeResponseDto>>` | 流程选人：按人员拆分节点信息（一人一节点） |
| `selectNodeName` | `SingleRequest<List<String>> arg0` | `SingleResponse<Map<String, String>>` | 按节点 code 批量取节点名 |
| `selectNamesByIds` | `SingleRequest<SearchNameDto> arg0` | `SingleResponse<Map<Long, String>>` | 按 id 批量取显示名 |
| `getEntityNameBySelectPeoples` | `SingleRequest<List<SelectPeopleDataDto>> arg0` | `SingleResponse<String>` | 把选人数据转成可读名称串（用于流程条件展示） |
| `selectPeopleCodeDataDto` | `SingleRequest<List<SelectPeopleDataDto>> arg0` | `SingleResponse<List<SelectPeopleCodeDataDto>>` | 选人数据 ↔ code 形式互转 |
| `selectPeopleDataDtoFromTransData` | `SingleRequest<SelectPeopleTransDataDto> arg0` | `SingleResponse<Map<Long, List<SelectPeopleDataDto>>>` | 从流程传输数据还原选人数据 |
| `selectPeopleIdsCodeData` | `SingleRequest<SelectPeopleIdsTransDataDto> arg0` | `SingleResponse<List<SelectPeopleCodeDataDto>>` | 选人数据转为 id+code 形式 |
| `selectPeopleIdsDataDtoFromTransData` | `SingleRequest<List<SelectPeopleCodeDataDto>> arg0` | `SingleResponse<SelectPeopleIdsTransNewMapDto>` | 选人 id+code 转回结构化数据 |
| `checkSelectPeopleData` | `SingleRequest<List<SelectPeopleDataDto>> arg0` | `SingleResponse<SelectPeopleDataValidDto>` | 校验选人数据合法性（流程保存前） |
| `selectSortField` | `SingleRequest<WorkFlowSortRequestDto> arg0` | `SingleResponse<String>` | 流程选人：取排序字段 |
| `selectMemberPostListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgMemberPostIdentityDto>` | 流程选人：按条件查人员岗位身份列表 |
| `selectOrgSameTypeChildList` | `SingleRequest<List<Long>> arg0` | `SingleResponse<List<OrgAboutIdDataDto>>` | 查同类下级组织（用于流程层级匹配） |
| `selectSupervisorMultipleData` | `SingleRequest<SupervisorMultipleParams> arg0` | `SingleResponse<SupervisorMultipleDataDto>` | 流程选人：监管关系多方数据 |
| `selectUserRoleAuthAndManageData` | `SingleRequest<Long> arg0` | `SingleResponse<UserRoleAuthAndManageDataDto>` | 查用户的角色权限与可管理数据（流程权限判断） |
| `selectFirstLevelDepartmentInfoByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Map<Long, Map<String, Object>>>` | 按 id 批量取一级部门信息 |

### `com.seeyon.organization.api.common`

#### OrgCommonAppService

`com.seeyon.organization.api.common.OrgCommonAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectMemberInfoById` | `SingleRequest<Long> arg0` | `SingleResponse<Map<String, Object>>` | 按人员 id 查人员基本信息（返回 Map） |
| `selectMemberDepartmentInfoById` | `SingleRequest<Long> arg0` | `SingleResponse<Map<Long, Map<String, List>>>` | 按人员 id 查其所属部门（部门 → 人员列表） |
| `selectMemberMultiDimOrgInfo` | `SingleRequest<Long> arg0` | `SingleResponse<Map<String, Object>>` | 按人员 id 查多维组织归属（主岗/兼岗/多单位） |
| `selectMemberInstitutionInfoById` | `SingleRequest<Long> arg0` | `SingleResponse<Map<Long, Map<String, List>>>` | 按人员 id 查其所属机构（机构 → 人员列表） |
| `selectMemberBySelectPeopleData` | `SingleRequest<List<SelectPeopleDataDto>> arg0` | `ListResponse<OrgMemberCoreDto>` | 按选人数据解析出人员列表（选人数据=部门/岗位/角色/人员/组的组合） |
| `selectPageMemberBySelectPeopleData` | `PageDtoRequest<List<SelectPeopleDataDto>> arg0` | `PageResponse<OrgMemberCoreDto>` | 按选人数据分页解析人员，返回人员对象 |
| `selectPageMemberBySelectPeopleIdData` | `PageDtoRequest<List<SelectPeopleDataDto>> arg0` | `PageResponse<Long>` | 按选人数据分页解析人员，只返回人员 id（更轻） |
| `selectMemberBySelectPeopleDatas` | `SingleRequest<List<List<SelectPeopleDataDto>>> arg0` | `ListResponse<List<OrgMemberCoreDto>>` | 多组选人数据分别解析，按组返回人员列表 |
| `selectMemberBySelectPeopleDataJson` | `SingleRequest<String> arg0` | `ListResponse<OrgMemberCoreDto>` | 同 selectMemberBySelectPeopleData，但入参是选人数据的 JSON 字符串 |
| `selectPageMemberBySelectPeopleDataJson` | `PageDtoRequest<String> arg0` | `PageResponse<OrgMemberCoreDto>` | 同分页版，入参为 JSON 字符串 |
| `selectPageMemberBySelectPeopleIdDataJson` | `PageDtoRequest<String> arg0` | `PageResponse<Long>` | 同分页只返 id 版，入参为 JSON 字符串 |
| `selectMemberBySelectPeopleDataJsons` | `SingleRequest<List<String>> arg0` | `ListResponse<List<OrgMemberCoreDto>>` | 多组 JSON 选人数据分别解析 |
| `isMemberInSelectPeopleDataJson` | `SingleRequest<MemberInSelectPeopleDataDto> arg0` | `SingleResponse<Boolean>` | 判断某人员是否落在选人数据范围内 |
| `selectMemberByOrgId` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<Long>` | 查某组织（部门）下的人员 id 列表 |
| `selectPageMemberByOrgId` | `PageRequest arg0` | `PageResponse<Long>` | 查某组织下人员，分页，只返 id |
| `selectMemberCountByOrgId` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 统计某组织下人员数量 |
| `selectMemberByPostId` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<Long>` | 查某岗位下的人员 id |
| `selectMemberByJobId` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<Long>` | 查某职务下的人员 id |
| `selectMemberByLevelId` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<Long>` | 查某职务级别下的人员 id |
| `selectMemberByUserId` | `SingleRequest<Long> arg0` | `SingleResponse<OrgMemberCoreDto>` | 按用户中心 userId 反查平台人员 |
| `selectChildrenOrgIdByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<Long>` | 按条件查下级组织 id（不含自身） |
| `selectChildrenOrgByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgUnitCoreDto>` | 按条件查下级组织对象 |
| `selectOrgMetadataColumnList` | `SingleRequest<SelectMetadataDto> arg0` | `ListResponse<OrgMetadataColumnCoreDto>` | 查组织扩展属性的列定义（字段元数据） |
| `selectParentIds` | `SingleRequest<Long> arg0` | `ListResponse<Long>` | 查某组织的全部上级 id（组织路径） |
| `selectRoot` | `—` | `SingleResponse<OrgUnitCoreDto>` | 查根组织（单位/集团根节点） |
| `selectOrgUnitTeamList` | `SingleRequest<SearchUnitTeamDto> arg0` | `ListResponse<OrgUnitTeamInfoDto>` | 查单位下的团队列表 |
| `isRole` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Boolean>` | 判断人员是否具备指定角色 |
| `selectMemberOfUnitMetadataOfMemberId` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<List<Long>>` | 按单位扩展属性的取值条件反查人员 |
| `selectManagerDepartmentByMemberId` | `SingleRequest<Long> arg0` | `ListResponse<Long>` | 查某人是「部门负责人」的那些部门 id |
| `selectLeaderDepartmentByMemberId` | `SingleRequest<Long> arg0` | `ListResponse<Long>` | 查某人是「部门领导」的那些部门 id |
| `selectAllDomainIdsByMemberId` | `SingleRequest<Long> arg0` | `SingleResponse<List<Long>>` | 查某人可见的全部组织域 id |
| `selectDomainIdsByMemberId` | `SingleRequest<OrgDomainIdDto> arg0` | `SingleResponse<List<Long>>` | 按域类型查某人可见的组织域 id |
| `selectDomainMapByMemberId` | `SingleRequest<OrgDomainIdDto> arg0` | `SingleResponse<Map<OrgDomainTypeEnum, Set<Long>>>` | 按域类型分组返回某人可见的组织域 id |
| `fillSelectPeopleData` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 补全选人数据（补 id/名称等），入出参均为 JSON |
| `canManage` | `SingleRequest<OrgMemberManagePermissionDto> arg0` | `SingleResponse<Boolean>` | 判断当前登录者能否管理目标人员 |
| `selectSecretMemberIds` | `SingleRequest<SelectSecretMemberDto> arg0` | `SingleResponse<List<Long>>` | 查涉密人员 id 列表 |
| `selectManageOrgByRole` | `SingleRequest<SelectManageOrgDto> arg0` | `ListResponse<OrgManageOrgDto>` | 按角色查当前人可管理的组织 |
| `selectInOrgScopeIds` | `SingleRequest<OrgInScopeDataDto> arg0` | `SingleResponse<List<Long>>` | 查落在指定组织范围内的人员/组织 id |
| `selectEntityIdByCode` | `SingleRequest<List<OrgEntitySearchDto>> arg0` | `SingleResponse<List<OrgEntitySearchResultDto>>` | 按 code 批量查实体 id（组织、人员通用） |
| `selectScopeTypeName` | `SingleRequest<List<SelectScopeTypeNameDto>> arg0` | `SingleResponse<List<ScopeTypeNameDto>>` | 查范围类型的显示名 |
| `selectSensitiveFieldInfo` | `SingleRequest<SelectSensitiveFieldPermissionDto> arg0` | `ListResponse<OrgSensitiveFieldPermissionDto>` | 查敏感字段的权限配置 |
| `selectSensitiveFieldMember` | `SingleRequest<SelectSensitiveFileMemberDto> arg0` | `ListResponse<OrgSensitiveFileMemberDto>` | 查敏感字段对应的人员 |
| `selectMemberExtendInfoById` | `SingleRequest<Long> arg0` | `SingleResponse<Map<String, Object>>` | 按 id 查人员扩展信息 |
| `selectNameBySelectPeopleData` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 按选人数据取显示名（用于展示） |
| `containsAny` | `SingleRequest<SelectPeopleContainsAnyDto> arg0` | `SingleResponse<Boolean>` | 判断两组选人数据是否有交集（用于权限判断） |

### `com.seeyon.organization.api.core.business`

#### OrgBusinessBaseAppService

`com.seeyon.organization.api.core.business.OrgBusinessBaseAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgBusinessDto>` | 查询业务按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgBusinessDto>` | 查询业务按 ids |
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgBusinessDto>` | 级联查询业务按 id |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgBusinessDto>` | 级联查询业务按 ids |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<OrgBusinessDto>` | 列表查询业务按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<OrgBusinessDto>` | 分页查询业务按条件 |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<OrgBusinessDto>` | 查询ProxyJoin |
| `dynamicCountJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `SingleResponse<Integer>` | 统计Select |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<OrgBusinessDto>` | 查询Proxy |
| `selectCascadeByConditions` | `SingleRequest<QueryConditionDto> arg0` | `SingleResponse<OrgBusinessDto>` | 级联查询条件按条件 |
| `selectCascadeListByConditions` | `SingleRequest<QueryConditionDto> arg0` | `ListResponse<OrgBusinessDto>` | 级联列表查询条件按条件 |

#### OrgBusinessCoreAppService

`com.seeyon.organization.api.core.business.OrgBusinessCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectBusinessListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgBusinessCoreDto>` | 列表查询业务按条件 |

### `com.seeyon.organization.api.core.institution`

#### OrgInstitutionExecutiveAppService

`com.seeyon.organization.api.core.institution.OrgInstitutionExecutiveAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `checkUserExecutiveHide` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Map<Long, Boolean>>` | 检查用户ExecutiveHide |

### `com.seeyon.organization.api.core.job`

#### OrgJobBaseAppService

`com.seeyon.organization.api.core.job.OrgJobBaseAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<OrgJobRequestDto> arg0` | `SingleResponse<Long>` | 新建任务 |
| `update` | `SingleRequest<OrgJobRequestDto> arg0` | `SingleResponse<Integer>` | 修改任务 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgJobDto>` | 查询任务按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgJobDto>` | 查询任务按 ids |
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgJobDto>` | 级联查询任务按 id |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgJobDto>` | 级联查询任务按 ids |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<OrgJobDto>` | 列表查询任务按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<OrgJobDto>` | 分页查询任务按条件 |
| `selectJobListPropertiesByJobIds` | `SingleRequest<SimpleConditionByIdsDto> arg0` | `ListResponse<Map<String, Object>>` | 列表指定字段查询任务按任务 |
| `selectJobPageListPropertiesByCondition` | `PageDtoRequest<SimpleConditionByParamsDto> arg0` | `PageResponse<Map<String, Object>>` | 分页列表指定字段查询任务按条件 |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<OrgJobDto>` | 查询ProxyJoin |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<OrgJobDto>` | 查询Proxy |
| `selectCascadeByConditions` | `SingleRequest<QueryConditionDto> arg0` | `SingleResponse<OrgJobDto>` | 级联查询条件按条件 |
| `selectCascadeListByConditions` | `SingleRequest<QueryConditionDto> arg0` | `ListResponse<OrgJobDto>` | 级联列表查询条件按条件 |

#### OrgJobCoreAppService

`com.seeyon.organization.api.core.job.OrgJobCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectJobById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgJobCoreDto>` | 查询任务按 id |
| `selectJobByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgJobCoreDto>` | 查询任务按 ids |
| `selectJobListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgJobCoreDto>` | 列表查询任务按条件 |
| `selectJobPageListByCondition` | `PageRequest arg0` | `PageResponse<OrgJobCoreDto>` | 分页列表查询任务按条件 |
| `selectJobListPropertiesByJobIds` | `SingleRequest<SimpleConditionByIdsDto> arg0` | `ListResponse<Map<String, Object>>` | 列表指定字段查询任务按任务 |
| `selectJobPageListPropertiesByCondition` | `PageDtoRequest<SimpleConditionByParamsDto> arg0` | `PageResponse<Map<String, Object>>` | 分页列表指定字段查询任务按条件 |

### `com.seeyon.organization.api.core.level`

#### OrgLevelBaseAppService

`com.seeyon.organization.api.core.level.OrgLevelBaseAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<OrgLevelRequestDto> arg0` | `SingleResponse<Long>` | 新建职务级别 |
| `update` | `SingleRequest<OrgLevelRequestDto> arg0` | `SingleResponse<Integer>` | 修改职务级别 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgLevelDto>` | 查询职务级别按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgLevelDto>` | 查询职务级别按 ids |
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgLevelDto>` | 级联查询职务级别按 id |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgLevelDto>` | 级联查询职务级别按 ids |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<OrgLevelDto>` | 列表查询职务级别按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<OrgLevelDto>` | 分页查询职务级别按条件 |
| `selectLevelListPropertiesByLevelIds` | `SingleRequest<SimpleConditionByIdsDto> arg0` | `ListResponse<Map<String, Object>>` | 列表指定字段查询职务级别按职务级别 |
| `selectLevelPageListPropertiesByCondition` | `PageDtoRequest<SimpleConditionByParamsDto> arg0` | `PageResponse<Map<String, Object>>` | 分页列表指定字段查询职务级别按条件 |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<OrgLevelDto>` | 查询ProxyJoin |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<OrgLevelDto>` | 查询Proxy |
| `selectCascadeByConditions` | `SingleRequest<QueryConditionDto> arg0` | `SingleResponse<OrgLevelDto>` | 级联查询条件按条件 |
| `selectCascadeListByConditions` | `SingleRequest<QueryConditionDto> arg0` | `ListResponse<OrgLevelDto>` | 级联列表查询条件按条件 |

#### OrgLevelCoreAppService

`com.seeyon.organization.api.core.level.OrgLevelCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectLevelById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgLevelCoreDto>` | 查询职务级别按 id |
| `selectLevelByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgLevelCoreDto>` | 查询职务级别按 ids |
| `selectLevelListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgLevelCoreDto>` | 列表查询职务级别按条件 |
| `selectLevelPageListByCondition` | `PageRequest arg0` | `PageResponse<OrgLevelCoreDto>` | 分页列表查询职务级别按条件 |
| `selectLevelListPropertiesByLevelIds` | `SingleRequest<SimpleConditionByIdsDto> arg0` | `ListResponse<Map<String, Object>>` | 列表指定字段查询职务级别按职务级别 |
| `selectLevelPageListPropertiesByCondition` | `PageDtoRequest<SimpleConditionByParamsDto> arg0` | `PageResponse<Map<String, Object>>` | 分页列表指定字段查询职务级别按条件 |

### `com.seeyon.organization.api.core.member`

#### OrgMemberBaseAppService

`com.seeyon.organization.api.core.member.OrgMemberBaseAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<OrgCreateMemberBaseDto> arg0` | `SingleResponse<Long>` | 新建人员，返回新人员主键 |
| `update` | `SingleRequest<OrgUpdateMemberBaseDto> arg0` | `SingleResponse<Integer>` | 修改人员，返回影响行数（0/1） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgMemberDto>` | 按主键查人员（完整 DTO） |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgMemberDto>` | 按主键批量查人员 |
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgMemberDto>` | 按主键查人员，级联带出关联对象 |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgMemberDto>` | 按主键批量查人员，级联带出关联对象 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<OrgMemberDto>` | 按 ListRequest 条件查人员列表（完整 DTO） |
| `selectMemberListByCondition` | `ListRequest arg0` | `ListResponse<OrgMemberCoreDto>` | 按 ListRequest 条件查人员列表（Core DTO，更轻） |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<OrgMemberDto>` | 按 PageRequest 条件分页查人员（完整 DTO） |
| `selectMemberPageListByCondition` | `PageRequest arg0` | `PageResponse<OrgMemberCoreDto>` | 按 PageRequest 条件分页查人员（Core DTO） |
| `selectMemberListPropertiesByMemberIds` | `SingleRequest<SimpleConditionByIdsDto> arg0` | `ListResponse<Map<String, Object>>` | 按 id 批量取人员指定字段（列裁剪） |
| `selectMemberPageListPropertiesByCondition` | `PageDtoRequest<SimpleConditionByParamsDto> arg0` | `PageResponse<Map<String, Object>>` | 按条件分页取人员指定字段 |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<OrgMemberDto>` | 关联多表动态查询人员（ProxyJoinParamDto 拼条件） |
| `dynamicCountJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `SingleResponse<Integer>` | 关联多表动态统计人员数 |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<OrgMemberDto>` | 单表动态条件查询人员 |
| `selectCascadeByConditions` | `SingleRequest<QueryConditionDto> arg0` | `SingleResponse<OrgMemberDto>` | 按 QueryConditionDto 查单条人员（级联） |
| `selectCascadeListByConditions` | `SingleRequest<QueryConditionDto> arg0` | `ListResponse<OrgMemberDto>` | 按 QueryConditionDto 查人员列表（级联） |
| `selectInfoListByExtendCode` | `SingleRequest<OrgMemberConditionDto> arg0` | `ListResponse<OrgMemberInfoDto>` | 按扩展编码查人员信息列表 |

#### OrgMemberCoreAppService

`com.seeyon.organization.api.core.member.OrgMemberCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectMemberById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgMemberCoreDto>` | 按 id 查人员（Core DTO，只读场景首选） |
| `selectMemberInfoById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgMemberInfoDto>` | 按 id 查人员信息（Info DTO，含更多字段） |
| `selectMemberByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgMemberCoreDto>` | 按 id 批量查人员（Core DTO） |
| `selectMemberByIdsIgnoreTenantId` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgMemberCoreDto>` | 按 id 批量查人员（跨租户，慎用） |
| `selectMemberInfoByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgMemberInfoDto>` | 按 id 批量查人员信息（Info DTO） |
| `selectMemberListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgMemberCoreDto>` | 列表查询成员按条件 |
| `selectMemberPageListByCondition` | `PageRequest arg0` | `PageResponse<OrgMemberCoreDto>` | 分页列表查询成员按条件 |
| `selectMemberInfoListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgMemberInfoDto>` | 按条件查人员信息列表（Info DTO） |
| `selectMemberInfoPageListByCondition` | `PageRequest arg0` | `PageResponse<OrgMemberInfoDto>` | 按条件分页查人员信息（Info DTO） |
| `selectMemberByCodeIgnoreTenant` | `SingleRequest<List<String>> arg0` | `ListResponse<Map<String, Object>>` | 按人员编码批量查（跨租户） |
| `modifyMemberInfoBySelf` | `SingleRequest<OrgModifyMemberInfoSelfDto> arg0` | `SingleResponse<Integer>` | 人员自助修改本人信息（受限字段） |
| `selectMemberListPropertiesByMemberIds` | `SingleRequest<SimpleConditionByIdsDto> arg0` | `ListResponse<Map<String, Object>>` | 列表指定字段查询成员按成员 |
| `selectMemberPageListPropertiesByCondition` | `PageDtoRequest<SimpleConditionByParamsDto> arg0` | `PageResponse<Map<String, Object>>` | 分页列表指定字段查询成员按条件 |

### `com.seeyon.organization.api.core.memberpost`

#### OrgMemberPostBaseAppService

`com.seeyon.organization.api.core.memberpost.OrgMemberPostBaseAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<OrgMemberPostDto> arg0` | `SingleResponse<Long>` | 新建人员岗位关系，返回主键 |
| `update` | `SingleRequest<OrgMemberPostDto> arg0` | `SingleResponse<Integer>` | 修改人员岗位关系，返回影响行数 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgMemberPostDto>` | 查询成员岗位按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgMemberPostDto>` | 查询成员岗位按 ids |
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgMemberPostDto>` | 级联查询成员岗位按 id |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgMemberPostDto>` | 级联查询成员岗位按 ids |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<OrgMemberPostDto>` | 列表查询成员岗位按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<OrgMemberPostDto>` | 分页查询成员岗位按条件 |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<OrgMemberPostDto>` | 查询ProxyJoin |
| `dynamicCountJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `SingleResponse<Integer>` | 统计Select |
| `selectMemberPostListPropertiesByMemberIds` | `SingleRequest<SimpleConditionByIdsDto> arg0` | `ListResponse<Map<String, Object>>` | 列表指定字段查询成员岗位按成员 |
| `selectMemberPostPageListPropertiesByCondition` | `PageDtoRequest<SimpleConditionByParamsDto> arg0` | `PageResponse<Map<String, Object>>` | 分页列表指定字段查询成员岗位按条件 |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<OrgMemberPostDto>` | 查询Proxy |

#### OrgMemberPostCoreAppService

`com.seeyon.organization.api.core.memberpost.OrgMemberPostCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectMemberPostListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgMemberPostCoreDto>` | 列表查询成员岗位按条件 |
| `selectMemberPostListByMemberIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgMemberPostCoreDto>` | 列表查询成员岗位按成员 |
| `selectMemberPostPageListByCondition` | `PageRequest arg0` | `PageResponse<OrgMemberPostCoreDto>` | 分页列表查询成员岗位按条件 |
| `selectMemberPostListPropertiesByMemberIds` | `SingleRequest<SimpleConditionByIdsDto> arg0` | `ListResponse<Map<String, Object>>` | 列表指定字段查询成员岗位按成员 |
| `selectMemberPostPageListPropertiesByCondition` | `PageDtoRequest<SimpleConditionByParamsDto> arg0` | `PageResponse<Map<String, Object>>` | 分页列表指定字段查询成员岗位按条件 |

### `com.seeyon.organization.api.core.memberrole`

#### OrgMemberRoleBaseAppService

`com.seeyon.organization.api.core.memberrole.OrgMemberRoleBaseAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgMemberRoleDto>` | 查询成员角色按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgMemberRoleDto>` | 查询成员角色按 ids |
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgMemberRoleDto>` | 级联查询成员角色按 id |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgMemberRoleDto>` | 级联查询成员角色按 ids |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<OrgMemberRoleDto>` | 列表查询成员角色按条件 |
| `selectListByCondition` | `SingleRequest<SearchOrgMemberRoleDto> arg0` | `ListResponse<OrgMemberRoleDto>` | 列表查询组织成员角色按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<OrgMemberRoleDto>` | 分页查询成员角色按条件 |
| `selectPageByConditions` | `PageDtoRequest<SearchOrgMemberRoleDto> arg0` | `PageResponse<OrgMemberRoleDto>` | 分页查询组织成员角色按条件 |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<OrgMemberRoleDto>` | 查询ProxyJoin |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<OrgMemberRoleDto>` | 查询Proxy |
| `selectCascadeByConditions` | `SingleRequest<QueryConditionDto> arg0` | `SingleResponse<OrgMemberRoleDto>` | 级联查询条件按条件 |
| `selectCascadeListByConditions` | `SingleRequest<QueryConditionDto> arg0` | `ListResponse<OrgMemberRoleDto>` | 级联列表查询条件按条件 |
| `createOrUpdateBatch` | `SingleRequest<List<OrgMemberRoleBaseDto>> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建或更新人员角色，返回同步结果 |

#### OrgMemberRoleCoreAppService

`com.seeyon.organization.api.core.memberrole.OrgMemberRoleCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgMemberRoleCoreDto>` | 查询成员角色按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgMemberRoleCoreDto>` | 查询成员角色按 ids |
| `selectListByConditions` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgMemberRoleCoreDto>` | 列表查询成员角色按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<OrgMemberRoleCoreDto>` | 分页查询成员角色按条件 |

### `com.seeyon.organization.api.core.metadata`

#### OrgMetadataCoreAppService

`com.seeyon.organization.api.core.metadata.OrgMetadataCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectOrgMetadataColumnListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgMetadataColumnCoreDto>` | 按条件查扩展属性列定义 |
| `selectMetadataColumnList` | `SingleRequest<SearchMetadataColumnDto> arg0` | `ListResponse<OrgMetadataColumnCoreDto>` | 列表查询扩展属性Column |
| `selectPageMetadataColumnList` | `PageRequest arg0` | `PageResponse<OrgMetadataColumnCoreDto>` | 分页列表查询扩展属性Column |
| `selectOrgByUnitMemberMetadata` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgUnitCoreDto>` | 按单位扩展属性条件查组织（含人员维度） |
| `selectMemberByUnitMetadata` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgMemberCoreDto>` | 按单位扩展属性条件查人员 |
| `selectMemberByUnitMemberMetadata` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgMemberCoreDto>` | 按单位+人员扩展属性联合条件查人员 |
| `selectMemberMetadataInfo` | `SingleRequest<SearchMemberMetadataDto> arg0` | `SingleResponse<Map<String, Object>>` | 查单个人员的扩展属性值 |
| `selectOrgMetadataInfo` | `SingleRequest<SearchUnitMetadataDto> arg0` | `SingleResponse<Map<String, Object>>` | 查单个组织的扩展属性值 |
| `selectOrgMetadataInfos` | `SingleRequest<SearchUnitMetadatasDto> arg0` | `SingleResponse<Map<Long, Map<String, Object>>>` | 批量查组织的扩展属性值 |
| `selectOrgRoleByMemberMetadata` | `SingleRequest<Long> arg0` | `SingleResponse<Map<String, Boolean>>` | 按人员扩展属性判断组织角色 |
| `selectOrgIdByMemberIdInInstitution` | `SingleRequest<SearchOrgIdMetadataInfoDto> arg0` | `SingleResponse<Map<String, List<Long>>>` | 在机构内按人员扩展属性查组织 id |
| `selectEntityIdByMetadataValue` | `SingleRequest<SearchEntityIdByMetadataValueDto> arg0` | `SingleResponse<List<Long>>` | 按扩展属性值反查实体 id |
| `selectEntityIdByMetadataValuePageList` | `PageRequest arg0` | `PageResponse<Long>` | 查询实体按扩展属性页面 |
| `selectEntityIdsByMetadataValue` | `SingleRequest<SearchEntityIdByMetadataValueDto> arg0` | `ListResponse<Long>` | 按扩展属性值批量反查实体 id |
| `selectUnitMetadataPageList` | `PageDtoRequest<OrgUnitMetadataRequestDto> arg0` | `PageResponse<OrgUnitMetadataValueDto>` | 单位扩展属性值分页列表 |
| `selectMemberMetadataPageList` | `PageDtoRequest<OrgMemberMetadataRequestDto> arg0` | `PageResponse<OrgMemberMetadataValueDto>` | 人员扩展属性值分页列表 |

### `com.seeyon.organization.api.core.orgrole`

#### OrgRoleBaseAppService

`com.seeyon.organization.api.core.orgrole.OrgRoleBaseAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgRoleDto>` | 查询角色按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgRoleDto>` | 查询角色按 ids |
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgRoleDto>` | 级联查询角色按 id |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgRoleDto>` | 级联查询角色按 ids |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<OrgRoleDto>` | 列表查询角色按条件 |
| `selectListByCondition` | `SingleRequest<SearchOrgRoleDto> arg0` | `ListResponse<OrgRoleDto>` | 列表查询组织角色按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<OrgRoleDto>` | 分页查询角色按条件 |
| `selectPageByConditions` | `PageDtoRequest<SearchOrgRoleDto> arg0` | `PageResponse<OrgRoleDto>` | 分页查询组织角色按条件 |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<OrgRoleDto>` | 查询ProxyJoin |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<OrgRoleDto>` | 查询Proxy |
| `selectCascadeByConditions` | `SingleRequest<QueryConditionDto> arg0` | `SingleResponse<OrgRoleDto>` | 级联查询条件按条件 |
| `selectCascadeListByConditions` | `SingleRequest<QueryConditionDto> arg0` | `ListResponse<OrgRoleDto>` | 级联列表查询条件按条件 |
| `createOrUpdateBatch` | `SingleRequest<List<OrgRoleBaseDto>> arg0` | `SingleResponse<OrgSyncInfoDto>` | 批量新建OrUpdate |

#### OrgRoleCoreAppService

`com.seeyon.organization.api.core.orgrole.OrgRoleCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgRoleCoreDto>` | 查询角色按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgRoleCoreDto>` | 查询角色按 ids |
| `selectListByConditions` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgRoleCoreDto>` | 列表查询角色按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<OrgRoleCoreDto>` | 分页查询角色按条件 |

### `com.seeyon.organization.api.core.post`

#### OrgPostBaseAppService

`com.seeyon.organization.api.core.post.OrgPostBaseAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<OrgPostRequestDto> arg0` | `SingleResponse<Long>` | 新建岗位 |
| `update` | `SingleRequest<OrgPostRequestDto> arg0` | `SingleResponse<Integer>` | 修改岗位 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgPostDto>` | 查询岗位按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgPostDto>` | 查询岗位按 ids |
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgPostDto>` | 级联查询岗位按 id |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgPostDto>` | 级联查询岗位按 ids |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<OrgPostDto>` | 列表查询岗位按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<OrgPostDto>` | 分页查询岗位按条件 |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<OrgPostDto>` | 查询Proxy |
| `selectPostListPropertiesByPostIds` | `SingleRequest<SimpleConditionByIdsDto> arg0` | `ListResponse<Map<String, Object>>` | 列表指定字段查询岗位按岗位 |
| `selectPostPageListPropertiesByCondition` | `PageDtoRequest<SimpleConditionByParamsDto> arg0` | `PageResponse<Map<String, Object>>` | 分页列表指定字段查询岗位按条件 |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<OrgPostDto>` | 查询ProxyJoin |
| `selectCascadeByConditions` | `SingleRequest<QueryConditionDto> arg0` | `SingleResponse<OrgPostDto>` | 级联查询条件按条件 |
| `selectCascadeListByConditions` | `SingleRequest<QueryConditionDto> arg0` | `ListResponse<OrgPostDto>` | 级联列表查询条件按条件 |

#### OrgPostCoreAppService

`com.seeyon.organization.api.core.post.OrgPostCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectPostById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgPostCoreDto>` | 查询岗位按 id |
| `selectPostByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgPostCoreDto>` | 查询岗位按 ids |
| `selectPostListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgPostCoreDto>` | 列表查询岗位按条件 |
| `selectPostPageListByCondition` | `PageRequest arg0` | `PageResponse<OrgPostCoreDto>` | 分页列表查询岗位按条件 |
| `selectPostListPropertiesByPostIds` | `SingleRequest<SimpleConditionByIdsDto> arg0` | `ListResponse<Map<String, Object>>` | 列表指定字段查询岗位按岗位 |
| `selectPostPageListPropertiesByCondition` | `PageDtoRequest<SimpleConditionByParamsDto> arg0` | `PageResponse<Map<String, Object>>` | 分页列表指定字段查询岗位按条件 |

### `com.seeyon.organization.api.core.systemteam`

#### OrgSystemTeamCoreAppService

`com.seeyon.organization.api.core.systemteam.OrgSystemTeamCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectTeamMemberByTeamId` | `SingleRequest<Long> arg0` | `ListResponse<OrgMemberCoreDto>` | 查询团队成员按团队 |
| `selectTeamMemberByTeamIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgMemberCoreDto>` | 查询团队成员按团队 |
| `selectTeamById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgTeamCoreDto>` | 查询团队按 id |
| `selectTeamByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgTeamCoreDto>` | 查询团队按 ids |
| `selectTeamByCondition` | `PageRequest arg0` | `PageResponse<OrgTeamCoreDto>` | 查询团队按条件 |

### `com.seeyon.organization.api.core.unit`

#### OrgUnitBaseAppService

`com.seeyon.organization.api.core.unit.OrgUnitBaseAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<OrgCreateUnitBaseDto> arg0` | `SingleResponse<Long>` | 新建单位/部门，返回新主键 |
| `update` | `SingleRequest<OrgUpdateUnitBaseDto> arg0` | `SingleResponse<Integer>` | 修改单位/部门，返回影响行数 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgUnitDto>` | 按主键查单位/部门（完整 DTO） |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgUnitDto>` | 按主键批量查单位/部门 |
| `selectOrgById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgUnitCoreDto>` | 按主键查组织（Core DTO，只读首选） |
| `selectOrgByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgUnitCoreDto>` | 按主键批量查组织（Core DTO） |
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgUnitDto>` | 级联查询单位按 id |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgUnitDto>` | 级联查询单位按 ids |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<OrgUnitDto>` | 列表查询单位按条件 |
| `selectOrgListByCondition` | `ListRequest arg0` | `ListResponse<OrgUnitCoreDto>` | 列表查询组织按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<OrgUnitDto>` | 分页查询单位按条件 |
| `selectOrgPageListByCondition` | `PageRequest arg0` | `PageResponse<OrgUnitCoreDto>` | 分页列表查询组织按条件 |
| `selectOrgListPropertiesByOrgIds` | `SingleRequest<SimpleConditionByIdsDto> arg0` | `ListResponse<Map<String, Object>>` | 列表指定字段查询组织按组织 |
| `selectOrgPageListPropertiesByCondition` | `PageDtoRequest<SimpleConditionByParamsDto> arg0` | `PageResponse<Map<String, Object>>` | 分页列表指定字段查询组织按条件 |
| `selectLegalByMemberId` | `SingleRequest<Long> arg0` | `ListResponse<OrgUnitDto>` | 查某人所属的法人单位 |
| `selectLegalIdByMemberId` | `SingleRequest<Long> arg0` | `ListResponse<Long>` | 查某人所属法人单位 id |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<OrgUnitDto>` | 查询ProxyJoin |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<OrgUnitDto>` | 查询Proxy |
| `selectCascadeByConditions` | `SingleRequest<QueryConditionDto> arg0` | `SingleResponse<OrgUnitDto>` | 级联查询条件按条件 |
| `selectCascadeListByConditions` | `SingleRequest<QueryConditionDto> arg0` | `ListResponse<OrgUnitDto>` | 级联列表查询条件按条件 |

#### OrgUnitCoreAppService

`com.seeyon.organization.api.core.unit.OrgUnitCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectOrgById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgUnitCoreDto>` | 查询组织按 id |
| `selectOrgInfoById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgUnitInfoDto>` | 按 id 查组织信息（Info DTO） |
| `selectOrgByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgUnitCoreDto>` | 查询组织按 ids |
| `selectOrgByIdsIgnoreTenantId` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgUnitCoreDto>` | 按 id 批量查组织（跨租户，慎用） |
| `selectOrgInfoByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgUnitInfoDto>` | 查询组织按 ids |
| `selectOrgListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgUnitCoreDto>` | 列表查询组织按条件 |
| `selectOrgPageListByCondition` | `PageRequest arg0` | `PageResponse<OrgUnitCoreDto>` | 分页列表查询组织按条件 |
| `selectOrgInfoListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgUnitInfoDto>` | 列表查询组织按条件 |
| `selectOrgInfoPageListByCondition` | `PageRequest arg0` | `PageResponse<OrgUnitInfoDto>` | 分页列表查询组织按条件 |
| `selectMetadataPropertiesByOrgIds` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<Map<String, Object>>` | 按组织 id 批量取扩展属性值 |
| `selectOrgListPropertiesByOrgIds` | `SingleRequest<SimpleConditionByIdsDto> arg0` | `ListResponse<Map<String, Object>>` | 列表指定字段查询组织按组织 |
| `selectOrgPageListPropertiesByCondition` | `PageDtoRequest<SimpleConditionByParamsDto> arg0` | `PageResponse<Map<String, Object>>` | 分页列表指定字段查询组织按条件 |
| `selectTraditionToSimpleNameByCondition` | `PageRequest arg0` | `PageResponse<Long>` | 传统部门名 → 简单名映射 |

### `com.seeyon.organization.api.core.unitteam`

#### OrgUnitTeamCoreAppService

`com.seeyon.organization.api.core.unitteam.OrgUnitTeamCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<OrgUnitTeamDto> arg0` | `SingleResponse<Long>` | 新建单位团队 |
| `delete` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除（SingleRequest） |
| `update` | `SingleRequest<OrgUnitTeamDto> arg0` | `SingleResponse<Integer>` | 修改单位团队 |
| `selectUnitTeamById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgUnitTeamInfoDto>` | 查询单位团队按 id |
| `selectUnitTeamByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgUnitTeamInfoDto>` | 查询单位团队按 ids |
| `selectUnitTeamListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgUnitTeamInfoDto>` | 列表查询单位团队按条件 |
| `selectUnitTeamPageListByCondition` | `PageRequest arg0` | `PageResponse<OrgUnitTeamInfoDto>` | 分页列表查询单位团队按条件 |
| `selectSortId` | `—` | `SingleResponse<Integer>` | 查询排序 |

### `com.seeyon.organization.api.core.unitvertical`

#### OrgUnitVerticalBaseAppService

`com.seeyon.organization.api.core.unitvertical.OrgUnitVerticalBaseAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgUnitVerticalDto>` | 查询单位按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgUnitVerticalDto>` | 查询单位按 ids |
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<OrgUnitVerticalDto>` | 级联查询单位按 id |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<OrgUnitVerticalDto>` | 级联查询单位按 ids |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<OrgUnitVerticalDto>` | 列表查询单位按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<OrgUnitVerticalDto>` | 分页查询单位按条件 |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<OrgUnitVerticalDto>` | 查询ProxyJoin |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<OrgUnitVerticalDto>` | 查询Proxy |
| `selectCascadeByConditions` | `SingleRequest<QueryConditionDto> arg0` | `SingleResponse<OrgUnitVerticalDto>` | 级联查询条件按条件 |
| `selectCascadeListByConditions` | `SingleRequest<QueryConditionDto> arg0` | `ListResponse<OrgUnitVerticalDto>` | 级联列表查询条件按条件 |

#### OrgUnitVerticalCoreAppService

`com.seeyon.organization.api.core.unitvertical.OrgUnitVerticalCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectUnitVerticalListByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<OrgUnitVerticalCoreDto>` | 列表查询单位Vertical按条件 |

### `com.seeyon.organization.api.parameter`

#### OrgParameterCoreAppService

`com.seeyon.organization.api.parameter.OrgParameterCoreAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectValueByParamsKey` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 查询Value按键 |

### `com.seeyon.organization.api.selectpeople.department`

#### OrgSelectPeopleForDeptAppService

`com.seeyon.organization.api.selectpeople.department.OrgSelectPeopleForDeptAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `departmentTree` | `SingleRequest<SearchDepartmentTree> arg0` | `SingleResponse<SelectPeopleUserDepartmentTreeListDto>` | 选人组件：部门树（懒加载） |
| `selectOrgPath` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 取部门完整路径（面包屑） |
| `departmentTreeExtensionList` | `SingleRequest<List<Long>> arg0` | `ListResponse<SelectPeopleUserDepartmentTreeExtensionDto>` | 部门树扩展（委托/兼职等） |

### `com.seeyon.organization.api.selectpeople.institution`

#### OrgSelectPeopleForInstAppService

`com.seeyon.organization.api.selectpeople.institution.OrgSelectPeopleForInstAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectFirstChildrenUnits` | `SingleRequest<SearchUnitDto> arg0` | `ListResponse<SelectPeopleUnitDto>` | 选人组件：机构下一级单位 |
| `searchInstitution` | `SingleRequest<SearchUnitByKeyDto> arg0` | `ListResponse<SelectPeopleUnitDto>` | 选人组件：按关键字搜机构 |

### `com.seeyon.organization.api.selectpeople.member`

#### OrgSelectPeopleForMemberAppService

`com.seeyon.organization.api.selectpeople.member.OrgSelectPeopleForMemberAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `searchMemberByGroup` | `SingleRequest<SearchByKeyDto> arg0` | `ListResponse<SelectPeopleMemberDto>` | 选人组件：按分组关键字搜人员 |
| `selectMembersByOrg` | `PageRequest arg0` | `PageResponse<SelectPeopleMemberDto>` | 选人组件：某组织下人员分页 |

### `com.seeyon.organization.api.tenant`

#### TenantManageAppService

`com.seeyon.organization.api.tenant.TenantManageAppService` · 构件 `organization-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectEnableUnitNumIgnoreTenant` | `—` | `ListResponse<HashMap<Long, Integer>>` | 查询单位EnableNum |

### `com.seeyon.organization.appservice.api.app.workflow`

#### WorkFlowMatchService

`com.seeyon.organization.appservice.api.app.workflow.WorkFlowMatchService` · 构件 `organization-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `type` | `—` | `String` | 返回该实现的类型标识（SPI/策略模式用于区分实现） |
| `selectMemberPostBySelectPeople` | `WorkFlowMatchRequestDto arg0` | `WorkFlowMatchResponseDto` | 查询成员岗位按SelectPeople |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 59 个领域服务，下表列**方法数最多的 40 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `OrgHelperService` | 95 | Helper · 判断×23 / 查询×22 / 获取×20 |
| `OrgUnitService` | 67 | 单位 · 查询×39 / 获取×7 / 修改×6 |
| `OrgMemberService` | 55 | 成员 · 查询×28 / 修改×12 / 新建×4 |
| `OrgMemberPostService` | 52 | 成员岗位 · 查询×29 / 新建×5 / 判断×3 |
| `OrgUnitMetadataService` | 48 | 单位扩展属性 · 查询×15 / 获取×9 / 修改×7 |
| `OrgUnitVerticalService` | 46 | 单位 · 查询×25 / 修改×5 / 新建×4 |
| `WorkFlowMatchEngineService` | 43 | WorkFlowMatchEngine · 查询×31 / 获取×8 / 判断×1 |
| `OrgBusinessService` | 31 | 业务 · 查询×21 / 修改×2 / 校验×2 |
| `SelectPeopleCacheService` | 31 | SelectPeopleCache · 查询×16 / 获取×5 / 修改×4 |
| `OrgPostService` | 28 | 岗位 · 查询×9 / 修改×5 / 同步×3 |
| `OrgBaseService` | 27 | OrgBase · 查询×20 / 获取×4 / 新建×2 |
| `OrgMemberMetadataService` | 25 | 成员扩展属性 · 查询×11 / 修改×4 / 获取×4 |
| `OrgJobService` | 20 | 任务 · 查询×7 / 修改×3 / 校验×3 |
| `OrgDepartmentVisitPermissionService` | 19 | 部门权限 · 查询×11 / 获取×4 / 新建×1 |
| `OrgMetaDataColumnService` | 19 | MetaColumn · 查询×12 / 初始化×2 / 获取×2 |
| `OrgRoleService` | 19 | 角色 · 查询×7 / 获取×4 / 校验×3 |
| `OrgMetaDataColumnSettingService` | 18 | 设置 · 查询×12 / 修改×2 / 删除×1 |
| `OrgUnitTeamService` | 18 | 单位团队 · 查询×6 / 获取×5 / 修改×2 |
| `OrgInstitutionVisitPermissionService` | 17 | 机构权限 · 查询×7 / 检查×4 / 判断×2 |
| `OrgLevelService` | 17 | 职务级别 · 查询×8 / 校验×4 / 新建×2 |
| `OrgTeamService` | 15 | 团队 · 查询×9 / 获取×2 / 新建×1 |
| `OrgUnitCacheService` | 14 | 单位 · 查询×9 / 获取×2 / 排序×1 |
| `OrgOutsidePermissionService` | 13 | 权限 · 查询×6 / 判断能否×2 / 新建×1 |
| `OrgExternalPartnerService` | 13 | 外部人员 · 查询×8 / 修改×2 / 新建×1 |
| `OrgPersonalTeamService` | 13 | 团队 · 查询×7 / 新建×2 / 修改×1 |
| `OrgTeamMemberDetailService` | 13 | 团队成员 · 查询×6 / 同步×3 / 删除×2 |
| `OrgMemberRoleService` | 12 | 成员角色 · 查询×4 / 修改×3 / 新建×2 |
| `OrgPostDimensionRelationService` | 12 | 岗位 · 查询×5 / 新建×1 / 修改×1 |
| `OrgAddressBookPermissionService` | 11 | 权限 · 查询×5 / 删除×2 / 新建×1 |
| `OrgParameterService` | 11 | 参数 · 查询×4 / 修改×1 / 办理×1 |
| `MemberSyncService` | 10 | 成员 · 新建×3 / 校验×3 / 获取×2 |
| `OrgExternalMemberService` | 10 | 外部人员成员 · 查询×6 / 新建×1 / 校验×1 |
| `OrgAddressBookFieldService` | 9 | 字段 · 查询×6 / 修改×1 / 校验×1 |
| `OrgLeaderSecretaryService` | 9 | 领导 · 查询×3 / 获取×2 / 新建×1 |
| `OrgPostDimensionService` | 9 | 岗位 · 查询×6 / 新建×1 / 修改×1 |
| `OrgUnitHorizontalService` | 9 | 单位 · 新建×2 / 修改×2 / 查询×2 |
| `OrgExternalMemberRelationshipService` | 9 | 外部人员成员 · 查询×5 / 新建×1 / 校验×1 |
| `OrgExternalPartnerMetadataService` | 9 | 外部人员扩展属性 · 获取×3 / 查询×2 / 新建×1 |
| `OrgScopeService` | 9 | 范围 · 查询×2 / 获取×2 |
| `OrgUnitTeamMemberService` | 9 | 单位团队成员 · 查询×3 / 新建×2 / 修改×1 |

## biz 层：事件与监听

事件 58 个 · 监听器 9 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| Business | `BusinessCreateEvent`, `BusinessUpdateEvent` |
| Job | `JobCreateBatchEvent`, `JobCreateEvent`, `JobUpdateBatchEvent`, `JobUpdateEvent` |
| Level | `LevelCreateBatchEvent`, `LevelCreateEvent`, `LevelUpdateBatchEvent`, `LevelUpdateEvent` |
| Member | `MemberCreateBatchEvent`, `MemberCreateEvent`, `MemberUpdateBatchEvent`, `MemberUpdateEvent` |
| MemberMetadata | `MemberMetadataCreateEvent`, `MemberMetadataUpdateEvent` |
| MemberPost | `MemberPostCreateEvent`, `MemberPostUpdateEvent` |
| MemberSecret | `MemberSecretUpdateBatchEvent` |
| MetadataColumn | `MetadataColumnCreateEvent`, `MetadataColumnUpdateEvent` |
| Org | `OrgCreateJobMessageEvent`, `OrgCreateLevelMessageEvent`, `OrgCreateMemberMessageEvent`, `OrgCreateMemberRoleMessageEvent`, `OrgCreatePostMessageEvent`, `OrgCreateRoleMessageEvent`, `OrgCreateUnitMessageEvent`, `OrgCreateUnitMetadataColumnMessageEvent`, `OrgDeleteMemberRoleMessageEvent`, `OrgDeleteRoleMessageEvent`, `OrgUpdateJobMessageEvent`, `OrgUpdateLevelMessageEvent`, `OrgUpdateMemberMessageEvent`, `OrgUpdateMemberRoleMessageEvent`, `OrgUpdatePostMessageEvent`, `OrgUpdateRoleMessageEvent`, `OrgUpdateUnitMessageEvent`, `OrgUpdateUnitMetadataColumnMessageEvent` |
| OrgBaseMessage | `OrgBaseMessageEvent` |
| OrgEnumMetadataMessage | `OrgEnumMetadataMessageEvent` |
| Post | `PostCreateBatchEvent`, `PostCreateEvent`, `PostUpdateBatchEvent`, `PostUpdateEvent` |
| PostDimension | `PostDimensionCreateEvent`, `PostDimensionUpdateEvent` |
| PostDimensionRelation | `PostDimensionRelationCreateEvent`, `PostDimensionRelationUpdateEvent` |
| Unit | `UnitCreateEvent`, `UnitUpdateBatchEvent`, `UnitUpdateEvent` |
| UnitHorizontal | `UnitHorizontalCreateEvent`, `UnitHorizontalUpdateEvent` |
| UnitMetadata | `UnitMetadataCreateEvent`, `UnitMetadataUpdateEvent` |
| UnitVertical | `UnitVerticalCreateEvent`, `UnitVerticalUpdateEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `UnitEventListener` | 17 |
| `MemberEventListener` | 12 |
| `MetadatacolumnEventListener` | 5 |
| `JobEventListener` | 4 |
| `LevelEventListener` | 4 |
| `PostEventListener` | 4 |
| `OrgUnitVerticalEventListener` | 3 |
| `MemberPostEventListener` | 2 |
| `OrgSpiProviderRegisterEventListener` | 1 |

## web 层：Controller

共 65 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 业务线（Business*） | `OrgBusinessUnitController` | 18 |
| 业务线（Business*） | `OrgBusinessLineController` | 14 |
| 业务线（Business*） | `OrgBusinessVerticalRelationController` | 6 |
| 业务线（Business*） | `OrgBusinessMemberController` | 5 |
| 业务线（Business*） | `OrgBusinessBaseController` | 4 |
| 业务线（Business*） | `OrgBusinessController` | 0 |
| 同步/初始化/迁移 | `OrgSyncController` | 30 |
| 同步/初始化/迁移 | `OrgInitController` | 21 |
| 同步/初始化/迁移 | `OrgTransferController` | 11 |
| 团队（*Team*） | `OrgUnitTeamController` | 11 |
| 团队（*Team*） | `OrgTeamController` | 7 |
| 团队（*Team*） | `OrgPersonalTeamController` | 5 |
| 团队（*Team*） | `OrgTeamBaseController` | 2 |
| 外部人员（External*） | `OrgExternalPartnerController` | 12 |
| 外部人员（External*） | `OrgExternalMemberController` | 11 |
| 外部人员（External*） | `OrgExternalMetadataController` | 5 |
| 外部人员（External*） | `OrgExternalMemberRelationshipController` | 4 |
| 外部人员（External*） | `OrgExternalUnitController` | 2 |
| 推送/被引用（Refer*） | `ReferOrgMemberController` | 11 |
| 推送/被引用（Refer*） | `ReferOrgBusinessController` | 9 |
| 推送/被引用（Refer*） | `ReferOrgJobController` | 9 |
| 推送/被引用（Refer*） | `ReferOrgLevelController` | 9 |
| 推送/被引用（Refer*） | `ReferOrgMemberPostController` | 9 |
| 推送/被引用（Refer*） | `ReferOrgPostController` | 9 |
| 推送/被引用（Refer*） | `ReferOrgRoleController` | 9 |
| 推送/被引用（Refer*） | `ReferOrgTeamController` | 9 |
| 推送/被引用（Refer*） | `ReferOrgUnitController` | 9 |
| 推送/被引用（Refer*） | `ReferOrgExternalMemberController` | 5 |
| 推送/被引用（Refer*） | `ReferOrgExternalPartnerController` | 5 |
| 核心实体 CRUD | `OrgAppController` | 53 |
| 核心实体 CRUD | `OrgUnitController` | 51 |
| 核心实体 CRUD | `OrgMemberController` | 37 |
| 核心实体 CRUD | `OrgAddressBookController` | 21 |
| 核心实体 CRUD | `OrgPostController` | 16 |
| 核心实体 CRUD | `OrgJobController` | 13 |
| 核心实体 CRUD | `OrgLevelController` | 12 |
| 核心实体 CRUD | `OrgRoleController` | 11 |
| 核心实体 CRUD | `OrgMemberRoleController` | 10 |
| 核心实体 CRUD | `OrgMemberPostController` | 8 |
| 核心实体 CRUD | `OrgNaturalMemberController` | 8 |
| 核心实体 CRUD | `OrgLeaderSecretaryController` | 6 |
| 核心实体 CRUD | `OrgMetaDataSettingController` | 6 |
| 核心实体 CRUD | `OrgPostDimensionController` | 6 |
| 核心实体 CRUD | `OrgLegalUnitController` | 6 |
| 核心实体 CRUD | `OrgOcipController` | 6 |
| 核心实体 CRUD | `OrgAddressBookFieldController` | 5 |
| 核心实体 CRUD | `OrgAddressBookPermissionController` | 5 |
| 核心实体 CRUD | `OrgAddressBookSetController` | 5 |
| 核心实体 CRUD | `OrgInstitutionExecutiveController` | 5 |
| 核心实体 CRUD | `OrgPostDimensionRelationController` | 5 |
| 核心实体 CRUD | `OrgParameterController` | 5 |
| 核心实体 CRUD | `ComponentFlatSelectPersonController` | 4 |
| 核心实体 CRUD | `OrgMetaDataController` | 4 |
| 核心实体 CRUD | `OrgOcipSelectPeopleController` | 4 |
| 核心实体 CRUD | `OrgOutsidePermissionController` | 3 |
| 核心实体 CRUD | `OrgScopeController` | 3 |
| 核心实体 CRUD | `OrgChangJiangController` | 3 |
| 核心实体 CRUD | `OrgSimulationController` | 1 |
| 核心实体 CRUD | `OrgOfflineInfoController` | 1 |
| 核心实体 CRUD | `OrgEnumController` | 1 |
| 访问权限 | `OrgDepartmentVisitPermissionController` | 5 |
| 访问权限 | `OrgLevelVisitPermissionController` | 4 |
| 访问权限 | `OrgInstitutionVisitPermissionController` | 3 |
| 选人组件（SelectPeople*） | `SelectPeopleController` | 62 |
| 选人组件（SelectPeople*） | `SelectPeopleListController` | 9 |

## 典型调用链（按真实签名拼，可直接抄）

### 链 1：给业务找人 —— 「某部门的负责人是谁」

```java
@Autowired
private com.seeyon.organization.api.common.OrgCommonAppService orgCommon;

// ① 按部门 id 找该部门下的人
SingleResponse<List<Long>> members = orgCommon.selectMemberByOrgId(
        SingleRequest.from(Map.of("orgId", deptId)));

// ② 过滤出「是本部门负责人」的那些部门
ListResponse<Long> managedDepts = orgCommon.selectManagerDepartmentByMemberId(
        SingleRequest.from(memberId));

// ③ 要拿去发起流程的，用选人数据解析（部门/岗位/角色/人员都能表达）
SingleResponse<OrgMemberCoreDto> ... = ...
ListResponse<OrgMemberCoreDto> resolved = orgCommon.selectMemberBySelectPeopleData(
        SingleRequest.from(selectPeopleDataList));
```

**关键点**：`selectMemberByOrgId` 的入参是 `Map<String,Object>`，键名不在字节码里
→ `UNVERIFIED`，第一次调用前要抓一次页面请求确认键名（通常是 `orgId` / `unitId`）。

### 链 2：人员主数据 —— 「按 id 拿人，要快」

```java
// 只读、字段精简 → Core（推荐）
@Autowired
private com.seeyon.organization.api.core.member.OrgMemberCoreAppService memberCore;

SingleResponse<OrgMemberCoreDto> one = memberCore.selectMemberById(SingleRequest.from(memberId));
ListResponse<OrgMemberCoreDto> many  = memberCore.selectMemberByIds(SingleRequest.from(ids));

// 要完整 DTO（含扩展属性、岗位等）→ Base
@Autowired
private com.seeyon.organization.api.core.member.OrgMemberBaseAppService memberBase;

SingleResponse<OrgMemberDto> full = memberBase.selectById(SingleRequest.from(memberId));
SingleResponse<OrgMemberDto> cascade = memberBase.selectCascadeById(SingleRequest.from(memberId));
```

**判据**：`Core` 返回 `OrgMemberCoreDto`（精简），`Base` 返回 `OrgMemberDto`（完整）。
跨租户场景才用 `selectMemberByIdsIgnoreTenantId`，默认不要用。

### 链 3：改人员 —— 「新建 + 立刻能查到」

```java
@Autowired
private com.seeyon.organization.api.core.member.OrgMemberBaseAppService memberBase;

// create 返回 SingleResponse<Long> = 新主键
SingleResponse<Long> created = memberBase.create(SingleRequest.from(createDto));

// update 返回 SingleResponse<Integer> = 影响行数（0 表示没匹配到）
SingleResponse<Integer> updated = memberBase.update(SingleRequest.from(updateDto));
```

**注意**：`create` / `update` 不在本地事务里包你 —— 它们是跨进程 AppService 调用。
如果你在自己的扩展里连着改多个实体，事务边界在你这边。

### 链 4：流程选人 —— 「按流程节点规则算办理人」

```java
@Autowired
private com.seeyon.organization.api.app.workflow.OrgWorkFlowAppService orgWorkFlow;

// 单个节点匹配（入参含流程上下文：流程 id、节点 id、选人规则）
SingleResponse<WorkFlowMatchResponseDto> match =
        orgWorkFlow.selectMemberPostBySelectPeople(
                SingleRequest.from(new WorkFlowMatchRequestDto()));

// 结果是「人员+岗位」对，不是纯人员 id —— 因为流程要按岗位定办理人
// 结果集很大时走文件：先 selectMemberPostBySelectPeoplesReturnFile 拿 key，
// 再用 selectReturnFileByKey 分页取，最后 deleteReturnFileByKey 清理
```

### 链 5：扩展属性反查 —— 「找出所有『职级= P7』的人」

```java
@Autowired
private com.seeyon.organization.api.core.metadata.OrgMetadataCoreAppService metaCore;

// ① 先取列定义，确认属性编码（这是查扩展属性的必要前置）
ListResponse<OrgMetadataColumnCoreDto> cols =
        metaCore.selectMetadataColumnList(SingleRequest.from(searchColDto));

// ② 按扩展属性值反查实体 id
SingleResponse<List<Long>> ids = metaCore.selectEntityIdByMetadataValue(
        SingleRequest.from(new SearchEntityIdByMetadataValueDto()));

// ③ 再按 id 批量取人员
ListResponse<OrgMemberCoreDto> people = memberCore.selectMemberByIds(SingleRequest.from(ids.getData()));
```

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
| 55 接口 / 421 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 59 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 58 事件 / 9 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 65 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径 | 未取证 | `UNVERIFIED` |
| 落表 | 未取证 | `UNVERIFIED` |
