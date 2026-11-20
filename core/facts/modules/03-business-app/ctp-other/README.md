# 应用管理/日志/媒体（application·manager·media·log·metadata）

## 一句话

`com.seeyon.ctp` 域的**可调用接口面**：3 个构件、146 个类、11 个 facade 接口 / 58 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `ctp-user-biz` | biz | 103 |
| `ctp-user-facade` | facade | 35 |
| `ctp-user-web` | web | 8 |
| **合计** | | **146** |

## 二、分层规律（写代码前必读）

`com.seeyon.ctp` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

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

## facade 层：11 个接口 / 58 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.ctp.application.api` | 1 | 6 |
| `com.seeyon.ctp.application.api.common` | 1 | 10 |
| `com.seeyon.ctp.application.api.core` | 4 | 12 |
| `com.seeyon.ctp.application.api.personalplan` | 1 | 4 |
| `com.seeyon.ctp.log.api` | 1 | 2 |
| `com.seeyon.ctp.manager.api` | 1 | 14 |
| `com.seeyon.ctp.media.api` | 1 | 8 |
| `com.seeyon.ctp.metadata.api` | 1 | 2 |
| **合计** | **11** | **58** |

### `com.seeyon.ctp.application.api`

#### CtpApplicationBaseAppService

`com.seeyon.ctp.application.api.CtpApplicationBaseAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<CtpApplicationAdminCreateDto> arg0` | `SingleResponse<Long>` | 新建应用 |
| `update` | `SingleRequest<CtpApplicationAdminCreateDto> arg0` | `SingleResponse<Integer>` | 修改应用 |
| `updateStatus` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 修改Status |
| `updateOnlineStatus` | `SingleRequest<String> arg0` | `SingleResponse<Integer>` | 修改在线Status |
| `simpleUpdate` | `SingleRequest<CtpApplicationAdminSimpleUpdateDto> arg0` | `SingleResponse<Integer>` | 修改应用简单 |
| `syncApplication` | `SingleRequest<CtpApplicationSyncDto> arg0` | `SingleResponse<Integer>` | 同步应用 |

### `com.seeyon.ctp.application.api.common`

#### CtpApplicationCommonAppService

`com.seeyon.ctp.application.api.common.CtpApplicationCommonAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectCategoryApplications` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpCategoryNameApplicationDto>` | 查询分类Applications |
| `selectCategorySetting` | `SingleRequest<ClientScopeEnum> arg0` | `SingleResponse<CtpCategorySettingDto>` | 查询分类设置 |
| `selectApplicationsByCategoryAndClientScope` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpApplicationDto>` | 查询Applications按分类客户端范围 |
| `selectAdminAppIdsByUserIdAndOrgId` | `ListRequest arg0` | `ListResponse<String>` | 查询应用AdminIds按用户组织 |
| `selectEnabledApplications` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Map<String, Boolean>>` | 查询EnabledApplications |
| `isEnabled` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Boolean>` | 判断Enabled |
| `selectUserMenuAndPortal` | `SingleRequest<SearchMenuAndPortalDto> arg0` | `SingleResponse<CtpMenuAndPortalDto>` | 查询用户菜单AndPortal |
| `selectEntityManageOrgIdByAppId` | `SingleRequest<SearchEntityManageOrgIdDto> arg0` | `SingleResponse<Long>` | 查询实体管理组织按应用 |
| `register` | `SingleRequest<CtpApplicationRegisterDto> arg0` | `SingleResponse<Integer>` | 注册应用 |
| `selectUserApplicationsByConditions` | `PageRequest arg0` | `PageResponse<CtpApplicationDto>` | 查询用户Applications按条件 |

### `com.seeyon.ctp.application.api.core`

#### CtpApplicationAuthCoreAppService

`com.seeyon.ctp.application.api.core.CtpApplicationAuthCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectApplicationAuthByAppId` | `SingleRequest<String> arg0` | `ListResponse<CtpApplicationAuthorizationDto>` | 查询应用认证按应用 |
| `selectAuthAppIdsByOrgId` | `SingleRequest<Long> arg0` | `ListResponse<String>` | 查询认证应用Ids按组织 |
| `selectAuthAppIds` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<String>` | 查询认证应用Ids |
| `selectWithOutAuthAllAppIdsByOrgId` | `SingleRequest<Long> arg0` | `ListResponse<String>` | 全部查询认证应用WithOutIds按组织 |
| `selectApplicationByAuthedOrg` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpApplicationDto>` | 查询应用按组织 |
| `selectPageApplicationByAuthedOrg` | `PageRequest arg0` | `PageResponse<CtpApplicationDto>` | 分页查询应用按组织 |

#### CtpApplicationCoreAppService

`com.seeyon.ctp.application.api.core.CtpApplicationCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpApplicationDto>` | 列表查询应用按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CtpApplicationDto>` | 分页查询应用按条件 |
| `selectAppStatusListIgnoreTenantId` | `—` | `ListResponse<CtpApplicationStatusDto>` | 列表查询应用Status |

#### CtpCapabilityCoreAppService

`com.seeyon.ctp.application.api.core.CtpCapabilityCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpCapabilityDto>` | 列表查询集成能力按条件 |

#### CtpCategoryCoreAppService

`com.seeyon.ctp.application.api.core.CtpCategoryCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpCategoryDto>` | 列表查询分类按条件 |
| `selectQuickListByConditions` | `ListRequest arg0` | `ListResponse<CtpWorkbenchItemDto>` | 列表查询Quick按条件 |

### `com.seeyon.ctp.application.api.personalplan`

#### CtpPersonalPlanCoreAppService

`com.seeyon.ctp.application.api.personalplan.CtpPersonalPlanCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createOrUpdateBatch` | `SingleRequest<CtpPersonalPlanPermissionDto> arg0` | `SingleResponse<Integer>` | 批量新建OrUpdate |
| `createRedirectBatch` | `SingleRequest<List<CtpPersonalPlanDto>> arg0` | `SingleResponse<List<Long>>` | 批量新建Redirect |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CtpPersonalPlanDto>` | 分页查询PersonalPlan按条件 |

### `com.seeyon.ctp.log.api`

#### CtpAccessLogService

`com.seeyon.ctp.log.api.CtpAccessLogService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectAccessLogPageByConditions` | `ListRequest arg0` | `ListResponse<CtpAccessLogDto>` | 分页查询可见日志按条件 |
| `selectAccessByConditions` | `PageRequest arg0` | `PageResponse<CtpAccessLogDto>` | 查询可见按条件 |

### `com.seeyon.ctp.manager.api`

#### CtpManagerTenantAppService

`com.seeyon.ctp.manager.api.CtpManagerTenantAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<CtpManagerTenantDto> arg0` | `SingleResponse<Long>` | 新建负责人租户 |
| `updateByUseTenantId` | `SingleRequest<CtpManagerTenantDto> arg0` | `SingleResponse<Integer>` | 修改负责人租户按租户 |
| `deleteByUseTenantId` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按租户（SingleRequest） |
| `updateStatusByUseTenantId` | `SingleRequest<CtpManagerTenantStatusDto> arg0` | `SingleResponse<Integer>` | 修改Status按租户 |
| `selectByUseTenantId` | `SingleRequest<Long> arg0` | `SingleResponse<CtpManagerTenantDto>` | 查询负责人租户按租户 |
| `selectByUseTenantCode` | `SingleRequest<String> arg0` | `SingleResponse<CtpManagerTenantDto>` | 查询负责人租户按租户编码 |
| `retryInit` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 重试Init |
| `selectStatusByUseTenantId` | `SingleRequest<Long> arg0` | `SingleResponse<CtpManagerTenantStatusDto>` | 查询Status按租户 |
| `selectInitStatus` | `SingleRequest<Long> arg0` | `ListResponse<CtpManagerTenantInitDto>` | 查询InitStatus |
| `applicationList` | `—` | `ListResponse<CtpManagerBaseAppDto>` | 列出负责人应用 |
| `replenishInit` | `SingleRequest<CtpManagerReplenishInitDto> arg0` | `SingleResponse<Boolean>` | 初始化负责人 |
| `activationLicence` | `SingleRequest<CtpLicenseInfoDto> arg0` | `SingleResponse<String>` | 租户管理：激活授权许可 |
| `bindingTenant` | `SingleRequest<CtpManagerBindingTenantDto> arg0` | `SingleResponse<Boolean>` | 租户管理：绑定租户 |
| `updateTenantAdmin` | `SingleRequest<CtpManagerTenantAdminUpdateDto> arg0` | `SingleResponse<Integer>` | 修改Admin |

### `com.seeyon.ctp.media.api`

#### MediaAppService

`com.seeyon.ctp.media.api.MediaAppService` · 构件 `ctp-media-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getPlayInfo` | `SingleRequest<PlayInfoRequestDto> arg0` | `SingleResponse<PlayInfoDto>` | 获取Play |
| `getPlayInfos` | `SingleRequest<List<PlayInfoRequestDto>> arg0` | `SingleResponse<Map<String, PlayInfoDto>>` | 获取PlayInfos |
| `asyncTrans` | `SingleRequest<TransRequestDto> arg0` | `SingleResponse<Boolean>` | 媒体：异步转码 |
| `getTaskDetailByStorageKey` | `SingleRequest<TaskDetailRequestDto> arg0` | `SingleResponse<String>` | 获取任务Detail按存储键 |
| `tsSign` | `SingleRequest<TsSignRequestDto> arg0` | `SingleResponse<String>` | 签署TsSign |
| `selectMediaInfo` | `SingleRequest<RequestParamDto> arg0` | `SingleResponse<MediaInfoDto>` | 查询Media |
| `asyncCutImg` | `SingleRequest<CutImgRequestDto> arg0` | `SingleResponse<String>` | 媒体：异步裁剪图片（缩略图） |
| `getCutImgTaskDetail` | `SingleRequest<String> arg0` | `SingleResponse<CutImgResponseDto>` | 获取任务CutImgDetail |

### `com.seeyon.ctp.metadata.api`

#### LoadJarResourceAppService

`com.seeyon.ctp.metadata.api.LoadJarResourceAppService` · 构件 `boot-starter-metadata`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getJsonMetadataData` | `SingleRequest<SearchJsonMetadataDto> arg0` | `SingleResponse<String>` | 获取扩展属性数据Json |
| `getRuntimeJsonData` | `SingleRequest<SearchJsonMetadataDto> arg0` | `SingleResponse<String>` | 获取数据RuntimeJson |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 11 个领域服务，下表列**方法数最多的 11 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `CtpApplicationService` | 94 | 应用 · 查询×46 / 修改×20 / 新建×5 |
| `CtpCategoryService` | 31 | 分类 · 查询×10 / 修改×5 / 删除×5 |
| `CtpApplicationAuthorizationService` | 30 | 应用 · 查询×20 / 新建×2 / 初始化×2 |
| `CtpPersonalPlanService` | 22 | PersonalPlan · 查询×7 / 获取×6 / 新建×2 |
| `CtpApplicationCapabilityService` | 12 | 应用集成能力 · 查询×3 / 删除×3 / 修改×1 |
| `CtpUserApplicationService` | 9 | 用户应用 · 删除×3 / 新建×3 / 查询×2 |
| `BaseService` | 8 | Base · 查询×5 / 新建×1 / 删除×1 |
| `CtpApplicationOfflineService` | 7 | 应用离线 · 查询×3 / 新建×1 / 修改×1 |
| `CtpApplicationDataInitExtService` | 6 | 应用扩展 · 获取×4 / 合并×1 |
| `CtpApplicationEntityManageService` | 5 | 应用实体管理 · 查询×2 / 获取×2 / 保存×1 |
| `CtpApplicationBasicService` | 2 | 应用 · 查询×1 |

## biz 层：事件与监听

事件 3 个 · 监听器 1 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| CtpApplicationEnableScope | `CtpApplicationEnableScopeEvent` |
| CtpCategoryReset | `CtpCategoryResetEvent` |
| CtpResourceRegister | `CtpResourceRegisterEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `CtpCategoryEventListener` | 3 |

## web 层：Controller

共 8 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 核心实体 CRUD | `CtpApplicationAdminController` | 18 |
| 核心实体 CRUD | `CtpApplicationController` | 15 |
| 核心实体 CRUD | `CtpApplicationCapabilityController` | 12 |
| 核心实体 CRUD | `CtpCategoryController` | 11 |
| 核心实体 CRUD | `CtpWorkbenchController` | 6 |
| 核心实体 CRUD | `CtpApplicationOfflineController` | 6 |
| 核心实体 CRUD | `CtpApplicationAuthorizationController` | 3 |
| 核心实体 CRUD | `CtpApplicationEntityManageController` | 3 |

## 落表

> 证据等级：`VERIFIED_STATIC_BYTECODE`（表名出现在本模块 biz jar 的 class 常量池）
> ＋ `LIVE`（同名表已用 `information_schema` 在 `test2` 确认真实存在）。
> 粒度：**类级**。方法级落表未取证 —— 平台不用 MyBatis XML
> （21 个 biz 构件合计只有 9 个 mapper XML / 15 张表），SQL 内联在代码里，
> 方法→表要逐类反编译才能确认。

本模块代码中出现的真实表 **1** 张（来源构件：`ctp-media-biz`）：

| 表名 | 注释 | 出现在几个类 |
|---|---|---:|
| `ctp_media` | — | 1 |

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 11 接口 / 58 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 11 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 3 事件 / 1 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 8 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径 | 未取证 | `UNVERIFIED` |
| 落表（1 张表，类级） | class 常量池 + `information_schema` | `VERIFIED_STATIC_BYTECODE` + `LIVE` |
| 方法级落表 | 未取证（SQL 内联，需逐类反编译） | `UNVERIFIED` |
