# 用户中心（user）

## 一句话

`com.seeyon.ctp` 域的**可调用接口面**：6 个构件、1,069 个类、40 个 facade 接口 / 220 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `ctp-user-biz` | biz | 736 |
| `ctp-user-facade` | facade | 214 |
| `ctp-user-api` | api | 42 |
| `ctp-user-web` | web | 38 |
| `organization-biz` | biz | 34 |
| `organization-web` | web | 5 |
| **合计** | | **1,069** |

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

## facade 层：40 个接口 / 220 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.ctp.user.api` | 2 | 2 |
| `com.seeyon.ctp.user.api.avoidlogin` | 3 | 9 |
| `com.seeyon.ctp.user.api.bpm` | 1 | 1 |
| `com.seeyon.ctp.user.api.common` | 8 | 51 |
| `com.seeyon.ctp.user.api.core` | 15 | 102 |
| `com.seeyon.ctp.user.api.org` | 7 | 31 |
| `com.seeyon.ctp.user.api.passwordCheck` | 1 | 1 |
| `com.seeyon.ctp.user.api.sso` | 1 | 20 |
| `com.seeyon.ctp.user.api.udc` | 1 | 2 |
| `com.seeyon.ctp.user.api.user` | 1 | 1 |
| **合计** | **40** | **220** |

### `com.seeyon.ctp.user.api`

#### CtpSsoAvoidLoginBaseService

`com.seeyon.ctp.user.api.CtpSsoAvoidLoginBaseService` · 构件 `ctp-user-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getClientId` | `—` | `String` | 获取客户端 |

#### ThirdPermissionAppService

`com.seeyon.ctp.user.api.ThirdPermissionAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `checkPermissionByUser` | `SingleRequest<ThirdCheckResourcePermissionDto> arg0` | `SingleResponse<Map<String, Boolean>>` | 检查权限按用户 |

### `com.seeyon.ctp.user.api.avoidlogin`

#### CtpAvoidLoginBackendProviderService

`com.seeyon.ctp.user.api.avoidlogin.CtpAvoidLoginBackendProviderService` · 构件 `ctp-user-api` · extends `CtpSsoAvoidLoginBaseService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `doExecuteAvoidLoginBackend` | `HttpServletRequest arg0` | `Map<String, Object>` | SPI 扩展点：登录（框架回调） |
| `avoidLoginBackend` | `HttpServletRequest arg0` | `Object` | 免登后端跳转（SPI 提供方：给第三方免登回调地址） |

#### CtpAvoidLoginClientModeProviderService

`com.seeyon.ctp.user.api.avoidlogin.CtpAvoidLoginClientModeProviderService` · 构件 `ctp-user-api` · extends `CtpSsoAvoidLoginBaseService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `preCheck` | `CtpUserSpiAvoidLoginClientModeDto arg0` | `void` | 检查（CtpUserSpiAvoidLoginClientModeDto） |
| `getUserInfo` | `CtpUserSpiAvoidLoginClientModeDto arg0` | `CtpAvoidLoginUserInfoDto` | 获取用户 |

#### CtpAvoidLoginMiddlePageProviderService

`com.seeyon.ctp.user.api.avoidlogin.CtpAvoidLoginMiddlePageProviderService` · 构件 `ctp-user-api` · extends `CtpSsoAvoidLoginBaseService`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getUserInfo` | `String arg0` | `CtpAvoidLoginUserInfoDto` | 获取用户 |
| `getCtpUserInfo` | `String arg0` | `Object` | 获取用户Ctp |
| `isRefreshTokenCycle` | `—` | `Boolean` | 判断令牌RefreshCycle |
| `doRefreshToken` | `ThirdTokenDto arg0` | `CtpUserSpiThirdTokenDto` | SPI 扩展点：令牌（框架回调） |
| `getSpiWebAuthenticationDetailInfo` | `—` | `SpiWebAuthenticationDetailInfo` | 获取SpiWebAuthenticationDetail |

### `com.seeyon.ctp.user.api.bpm`

#### CtpUserBpmAppService

`com.seeyon.ctp.user.api.bpm.CtpUserBpmAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectUserResourceIgnoreTenant` | `PageInfo arg0` | `PageResponse<CtpUserBpmResourceDto>` | 查询用户资源 |

### `com.seeyon.ctp.user.api.common`

#### CtpDeviceBindCommonAppService

`com.seeyon.ctp.user.api.common.CtpDeviceBindCommonAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `bindDevice` | `SingleRequest<CtpDeviceBindDto> arg0` | `SingleResponse<Long>` | 绑定Device |
| `batchUnbindDevice` | `SingleRequest<CtpUnbindDeviceDto> arg0` | `SingleResponse<Integer>` | 解绑Device |
| `selectByConditions` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpDeviceBindDto>` | 查询DeviceBind按条件 |

#### CtpMenuCommonAppService

`com.seeyon.ctp.user.api.common.CtpMenuCommonAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectChildrenByCode` | `SingleRequest<String> arg0` | `ListResponse<CtpMenuDto>` | 查询下级按编码 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpMenuDto>` | 列表查询菜单按条件 |

#### CtpResourceCommonAppService

`com.seeyon.ctp.user.api.common.CtpResourceCommonAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectDesignResources` | `ListRequest arg0` | `ListResponse<CtpResourceDto>` | 查询DesignResources |
| `deleteDesignResources` | `SingleRequest<String> arg0` | `SingleResponse<Integer>` | 删除DesignResources |

#### CtpSecretCommonAppService

`com.seeyon.ctp.user.api.common.CtpSecretCommonAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectSecretEnable` | `—` | `SingleResponse<Boolean>` | 查询密钥Enable |
| `selectSecretLevelEnumItem` | `—` | `ListResponse<CtpSecretLevelEnumItemDto>` | 查询密钥职务级别枚举Item |
| `selectOrgSecretLevelEnumItem` | `—` | `ListResponse<CtpSecretLevelEnumItemDto>` | 查询组织密钥职务级别枚举Item |
| `selectSecretLevelEnumItemList` | `SingleRequest<Void> arg0` | `ListResponse<CtpSecretLevelEnumItemDto>` | 列表查询密钥职务级别枚举Item |
| `selectSecretLevelEnumItemByValue` | `SingleRequest<String> arg0` | `SingleResponse<CtpSecretLevelEnumItemDto>` | 查询密钥职务级别枚举Item按Value |
| `selectSecretLevelEnumItemByOrderNo` | `SingleRequest<Integer> arg0` | `SingleResponse<CtpSecretLevelEnumItemDto>` | 查询密钥职务级别枚举Item按OrderNo |
| `selectOrgSecretLevelEnumItemByOrderNo` | `SingleRequest<Integer> arg0` | `SingleResponse<CtpSecretLevelEnumItemDto>` | 查询组织密钥职务级别枚举Item按OrderNo |
| `selectSecretLevelOrderNoByValue` | `SingleRequest<String> arg0` | `SingleResponse<Integer>` | 查询密钥职务级别OrderNo按Value |
| `selectSecretLevelValueByOrderNo` | `SingleRequest<Integer> arg0` | `SingleResponse<String>` | 查询密钥职务级别Value按OrderNo |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpSecretLevelEnumItemDto>` | 列表查询密钥职务级别枚举按条件 |
| `selectOrgToSystemSecretMap` | `—` | `SingleResponse<Map<String, String>>` | 查询组织密钥ToSystemMap |
| `selectSystemToOrgSecretMap` | `—` | `SingleResponse<Map<String, String>>` | 查询组织密钥SystemToMap |
| `getAccessSecretEnumIds` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Map<String, List<Long>>>` | 获取可见密钥枚举Ids |

#### CtpUserCommonAppService

`com.seeyon.ctp.user.api.common.CtpUserCommonAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getUserInfo` | `SingleRequest<Long> arg0` | `SingleResponse<Map<String, Object>>` | 获取用户 |
| `selectUserByLoginName` | `SingleRequest<String> arg0` | `SingleResponse<CtpUserDto>` | 查询用户按登录名称 |
| `getLoginPageSetParameter` | `—` | `SingleResponse<Map<String, Object>>` | 分页获取登录参数Set |
| `getRecentUserId` | `Integer arg0` | `SingleResponse<Map<Long, Long>>` | 获取用户Recent |

#### CtpUserDefaultIdentityCommonAppService

`com.seeyon.ctp.user.api.common.CtpUserDefaultIdentityCommonAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectDefaultSwitchAdminOrg` | `SingleRequest<Long> arg0` | `SingleResponse<Long>` | 查询切换组织DefaultAdmin |
| `selectUDefaultseIdentityInfo` | `ListRequest arg0` | `SingleResponse<CtpUserDefaultIdentityDto>` | 查询UDefaultseIdentity |
| `selectFrontUserDefaultTenant` | `ListRequest arg0` | `SingleResponse<Long>` | 查询用户FrontDefault |

#### CtpUserPermissionCommonAppService

`com.seeyon.ctp.user.api.common.CtpUserPermissionCommonAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectUserResourceCode` | `SingleRequest<CtpUserResourceSearchDto> arg0` | `ListResponse<String>` | 查询用户资源编码 |
| `selectUserResourceCodesMap` | `SingleRequest<CtpUserResourceSearchMapDto> arg0` | `SingleResponse<Map<String, Set<String>>>` | 查询用户资源编码Map |
| `checkUserResourceCode` | `SingleRequest<CtpUserResourceSearchDto> arg0` | `SingleResponse<Boolean>` | 检查用户资源编码 |
| `selectUserResource` | `SingleRequest<CtpUserResourceSearchDto> arg0` | `ListResponse<CtpUserResourceDto>` | 查询用户资源 |
| `selectUserResourceProperties` | `SingleRequest<CtpUserResourceSearchDto> arg0` | `ListResponse<CtpUserResourceDto>` | 指定字段查询用户资源 |
| `selectUserResource` | `PageInfo arg0` | `PageResponse<CtpUserResourceDto>` | 查询用户资源 |
| `checkUserResource` | `SingleRequest<List<CheckResourcePermissionDto>> arg0` | `SingleResponse<Map<String, Boolean>>` | 检查用户资源 |
| `checkUserAppPermission` | `SingleRequest<CtpUserAppPermissionDto> arg0` | `SingleResponse<Boolean>` | 检查用户应用权限 |
| `selectControlMenus` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpResourceSecurityDto>` | 查询ControlMenus |
| `selectUserMenus` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpUserResourceSecurityDto>` | 查询用户Menus |
| `selectAdminMenus` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpResourceDto>` | 查询AdminMenus |
| `selectUserRoleCode` | `SingleRequest<Long> arg0` | `ListResponse<String>` | 查询用户角色编码 |
| `selectUserRoleCodeByOrg` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<String>` | 查询用户角色编码按组织 |
| `selectUserRole` | `SingleRequest<Long> arg0` | `ListResponse<CtpUserRoleDto>` | 查询用户角色 |
| `selectUserDataPermission` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpUserDataPermissionDto>` | 查询用户数据权限 |
| `hasAdminRole` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 判断有角色Admin |
| `selectAdminOrgIdList` | `SingleRequest<Long> arg0` | `ListResponse<Long>` | 列表查询组织Admin |
| `selectOrgAdminResourceAction` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Map<String, Object>>` | 查询组织资源AdminAction |
| `checkOrgAdminPermission` | `SingleRequest<CheckOrgAdminPermissionDto> arg0` | `SingleResponse<Boolean>` | 检查组织权限Admin |

#### CtpUserRoleCommonAppService

`com.seeyon.ctp.user.api.common.CtpUserRoleCommonAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectUserByRoleCode` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<Map<String, Object>>` | 查询用户按角色编码 |
| `selectPageUserByRoleCode` | `PageRequest arg0` | `PageResponse<Map<String, Object>>` | 分页查询用户按角色编码 |
| `selectUserByRoleCodeSearch` | `SingleRequest<CtpUserRoleSearchDto> arg0` | `ListResponse<CtpUserRoleViewDto>` | 查询用户按角色编码 |
| `selectUserIdByRoleCode` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<Long>` | 查询用户按角色编码 |
| `hasRoleByOrgCode` | `SingleRequest<HasRoleByOrgCodeSearchDto> arg0` | `SingleResponse<Boolean>` | 判断有角色按组织编码 |

### `com.seeyon.ctp.user.api.core`

#### CtpAuthCoreAppService

`com.seeyon.ctp.user.api.core.CtpAuthCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `authenticate` | `SingleRequest<CtpLoginDto> arg0` | `SingleResponse<Map<String, Object>>` | 认证（校验账号密码/令牌），成功返回会话 |
| `switchAdmin` | `SingleRequest<CtpSwitchIdentityDto> arg0` | `SingleResponse<Map<String, Object>>` | 切换管理员身份（超管切换到普通管理员视图） |
| `switchOrg` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Map<String, Object>>` | 切换当前组织（多组织用户换所属单位） |
| `switchUser` | `SingleRequest<CtpSwitchIdentityDto> arg0` | `SingleResponse<Map<String, Object>>` | 切换登录用户（代登录/超管代入） |
| `getLoginUserInfo` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Map<String, Object>>` | 获取登录用户 |
| `getPcUserInfo` | `SingleRequest<Long> arg0` | `SingleResponse<CtpLoginInfoDto>` | 获取用户Pc |
| `selectTenantList` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpManagerTenantViewDto>` | 列表查询负责人租户 |
| `switchTenant` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Map<String, Object>>` | 切换租户 |
| `refreshAccessToken` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 刷新可见令牌 |
| `getAccessToken` | `SingleRequest<AccessTokenRequestDto> arg0` | `SingleResponse<String>` | 获取可见令牌 |
| `selectTenantListByUserId` | `SingleRequest<Long> arg0` | `SingleResponse<Map<String, Object>>` | 列表查询按用户（SingleRequest） |
| `selectTicketByToken` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 查询Ticket按令牌 |
| `getTempAccessToken` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<String>` | 获取可见令牌Temp |

#### CtpDataAuditCoreAppService

`com.seeyon.ctp.user.api.core.CtpDataAuditCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<CtpDataAuditDto> arg0` | `SingleResponse<Long>` | 新建Audit |

#### CtpLoginLogCoreAppService

`com.seeyon.ctp.user.api.core.CtpLoginLogCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CtpLoginLogDto>` | 分页查询登录日志按条件 |

#### CtpLoginPreConfigAppService

`com.seeyon.ctp.user.api.core.CtpLoginPreConfigAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectByOrgId` | `SingleRequest<Long> arg0` | `SingleResponse<CtpLoginPreConfigDto>` | 查询登录配置按组织 |
| `createOrUpdate` | `SingleRequest<CtpLoginPreConfigDto> arg0` | `SingleResponse<Integer>` | 新建OrUpdate |
| `allowChildCustomDefine` | `—` | `SingleResponse<Boolean>` | 判断下级单位是否允许自定义登录配置 |
| `allowChildCustomDefine` | `SingleRequest<Boolean> arg0` | `SingleResponse<Boolean>` | 判断下级单位是否允许自定义登录配置 |
| `selectByUri` | `SingleRequest<String> arg0` | `SingleResponse<CtpLoginPreConfigDto>` | 查询登录配置按Uri |
| `hasRepeatName` | `SingleRequest<CtpLoginPreConfigDto> arg0` | `SingleResponse<Boolean>` | 判断有名称Repeat |

#### CtpResourceCoreAppService

`com.seeyon.ctp.user.api.core.CtpResourceCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `register` | `SingleRequest<CtpResourceDto> arg0` | `SingleResponse<Long>` | 注册资源 |
| `registerBatch` | `SingleRequest<CtpResourceSyncDto> arg0` | `SingleResponse<Integer>` | 批量注册资源 |
| `registerResourcePermissionBatch` | `SingleRequest<CtpResourcePermissionBatchRegisterDto> arg0` | `SingleResponse<CtpResourcePermissionBatchResultDto>` | 批量注册资源权限 |
| `updateByCode` | `SingleRequest<CtpResourceDto> arg0` | `SingleResponse<Integer>` | 修改资源按编码 |
| `deleteByConditions` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 删除按条件（SingleRequest） |
| `selectByCode` | `SingleRequest<String> arg0` | `SingleResponse<CtpResourceDto>` | 查询资源按编码 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpResourceDto>` | 列表查询资源按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CtpResourceDto>` | 分页查询资源按条件 |

#### CtpResourcePermissionCoreAppService

`com.seeyon.ctp.user.api.core.CtpResourcePermissionCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `register` | `SingleRequest<CtpResourcePermissionRegisterDto> arg0` | `SingleResponse<Integer>` | 注册资源权限 |
| `deleteByResourceCode` | `SingleRequest<String> arg0` | `SingleResponse<Integer>` | 删除按资源编码（SingleRequest） |
| `selectByResourceCode` | `SingleRequest<String> arg0` | `ListResponse<CtpResourcePermissionDto>` | 查询资源权限按资源编码 |
| `selectListByConditions` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpResourcePermissionDto>` | 列表查询资源权限按条件 |

#### CtpResourceTypeCoreAppService

`com.seeyon.ctp.user.api.core.CtpResourceTypeCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpResourceTypeDto>` | 列表查询资源类型按条件 |

#### CtpRoleCoreAppService

`com.seeyon.ctp.user.api.core.CtpRoleCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<CtpRoleDto> arg0` | `SingleResponse<Long>` | 新建角色 |
| `saveBatch` | `SingleRequest<CtpRoleSyncDto> arg0` | `SingleResponse<Integer>` | 批量保存角色 |
| `syncRoleResource` | `SingleRequest<CtpRoleResourceSyncDto> arg0` | `SingleResponse<Integer>` | 同步角色资源 |
| `update` | `SingleRequest<CtpRoleDto> arg0` | `SingleResponse<Integer>` | 修改角色 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<CtpRoleDto>` | 查询角色按 id |
| `selectByCode` | `SingleRequest<String> arg0` | `SingleResponse<CtpRoleDto>` | 查询角色按编码 |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<CtpRoleDto>` | 查询角色按 ids |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpRoleDto>` | 列表查询角色按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CtpRoleDto>` | 分页查询角色按条件 |
| `deleteByConditions` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 删除按条件（SingleRequest） |
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<CtpRoleDto>` | 级联查询角色按 id |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<CtpRoleDto>` | 级联查询角色按 ids |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<CtpRoleDto>` | 查询ProxyJoin |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<CtpRoleDto>` | 查询Proxy |

#### CtpRoleResourceCoreAppService

`com.seeyon.ctp.user.api.core.CtpRoleResourceCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectResourceActionByRoleCodes` | `SingleRequest<List<String>> arg0` | `SingleResponse<Map<String, List<CtpRoleResourceActionDto>>>` | 查询资源Action按角色编码 |

#### CtpThirdPlatformConfigCoreAppService

`com.seeyon.ctp.user.api.core.CtpThirdPlatformConfigCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<CtpThirdPlatformConfigDto> arg0` | `SingleResponse<Long>` | 新建第三方配置 |
| `update` | `SingleRequest<CtpThirdPlatformConfigDto> arg0` | `SingleResponse<Integer>` | 修改第三方配置 |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<CtpThirdPlatformConfigDto>` | 查询第三方配置按 id |
| `selectOneByConditions` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<CtpThirdPlatformConfigDto>` | 查询One按条件 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpThirdPlatformConfigDto>` | 列表查询第三方配置按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CtpThirdPlatformConfigDto>` | 分页查询第三方配置按条件 |

#### CtpUserBindMappingAppService

`com.seeyon.ctp.user.api.core.CtpUserBindMappingAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `saveUpdate` | `SingleRequest<CtpUserMappingSyncRequestDto> arg0` | `SingleResponse<Integer>` | 保存Update |
| `selectOneByCondition` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<CtpUserMappingResponseDto>` | 查询One按条件 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpUserMappingResponseDto>` | 列表查询用户映射按条件 |
| `pageUserMappingByUserIds` | `SingleRequest<CtpUserMappingQueryRequestDto> arg0` | `PageResponse<CtpUserMappingResponseDto>` | 按用户 id 分页查账号绑定关系（三方账号↔平台账号） |
| `listUserMappingByUserIds` | `SingleRequest<CtpUserMappingQueryRequestDto> arg0` | `ListResponse<CtpUserMappingResponseDto>` | 列出用户映射按用户 |
| `listUserMappingForPending` | `SingleRequest<CtpUserMappingQueryRequestDto> arg0` | `ListResponse<CtpUserMappingResponseDto>` | 列出用户映射待办For |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CtpUserMappingResponseDto>` | 分页查询用户映射按条件 |

#### CtpUserCoreAppService

`com.seeyon.ctp.user.api.core.CtpUserCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `beforeCreateCheck` | `SingleRequest<CtpUserDto> arg0` | `SingleResponse<Boolean>` | 新建Check |
| `create` | `SingleRequest<CtpUserDto> arg0` | `SingleResponse<Long>` | 新建用户 |
| `createBatch` | `SingleRequest<List<CtpUserDto>> arg0` | `SingleResponse<Integer>` | 批量新建（SingleRequest） |
| `beforeUpdateCheck` | `SingleRequest<CtpUserDto> arg0` | `SingleResponse<Boolean>` | 修改Check |
| `update` | `SingleRequest<CtpUserDto> arg0` | `SingleResponse<Integer>` | 修改用户 |
| `updateBatch` | `SingleRequest<List<CtpUserDto>> arg0` | `SingleResponse<Integer>` | 批量修改（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<CtpUserDto>` | 查询用户按 id |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<CtpUserDto>` | 查询用户按 ids |
| `selectSimpleByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<CtpUserSimpleDto>` | 查询简单按 ids |
| `selectOneByCondition` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<CtpUserDto>` | 查询One按条件 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpUserDto>` | 列表查询用户按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CtpUserDto>` | 分页查询用户按条件 |
| `selectUserIgnoreTenant` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<CtpUserDto>` | 查询用户 |
| `syncCreateBatch` | `SingleRequest<List<CtpUserDto>> arg0` | `ListResponse<SyncUserMessageDto>` | 批量同步Create |
| `syncUpdateBatch` | `SingleRequest<List<CtpUserDto>> arg0` | `ListResponse<SyncUserMessageDto>` | 批量同步Update |
| `syncCreateBatchCheck` | `SingleRequest<List<CtpUserDto>> arg0` | `ListResponse<SyncUserMessageDto>` | 批量同步CreateCheck |
| `syncUpdateBatchCheck` | `SingleRequest<List<CtpUserDto>> arg0` | `ListResponse<SyncUserMessageDto>` | 批量同步UpdateCheck |
| `selectUserTenantInfoByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Map<Long, List<UserTenantInfoDto>>>` | 查询用户按 ids |

#### CtpUserResourceCoreAppService

`com.seeyon.ctp.user.api.core.CtpUserResourceCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createBatch` | `SingleRequest<List<CtpUserResourceDto>> arg0` | `SingleResponse<Integer>` | 批量新建（SingleRequest） |
| `deleteByConditions` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 删除按条件（SingleRequest） |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpUserResourceDto>` | 列表查询用户资源按条件 |
| `selectPageListByConditions` | `PageRequest arg0` | `PageResponse<CtpUserResourceDto>` | 分页列表查询用户资源按条件 |

#### CtpUserRoleAppService

`com.seeyon.ctp.user.api.core.CtpUserRoleAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<CtpUserRoleDto>` | 级联查询用户角色按 id |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<CtpUserRoleDto>` | 级联查询用户角色按 ids |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<CtpUserRoleDto>` | 查询ProxyJoin |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<CtpUserRoleDto>` | 查询Proxy |

#### CtpUserRoleCoreAppService

`com.seeyon.ctp.user.api.core.CtpUserRoleCoreAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createBatch` | `SingleRequest<List<CtpUserRoleDto>> arg0` | `SingleResponse<Integer>` | 批量新建（SingleRequest） |
| `createUserRule` | `SingleRequest<CtpRuleRoleDto> arg0` | `SingleResponse<Long>` | 新建用户规则 |
| `createAuthorizationRule` | `SingleRequest<CtpAuthorizationDto> arg0` | `SingleResponse<Long>` | 新建规则Authorization |
| `createBatchAuthorizationRule` | `SingleRequest<CtpUserRoleSyncDto> arg0` | `SingleResponse<Integer>` | 批量新建规则Authorization |
| `deleteAuthorizationRuleById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除规则Authorization按 id |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `deleteByConditions` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 删除按条件（SingleRequest） |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<CtpUserRoleDto>` | 列表查询用户角色按条件 |
| `selectEntityRoleListByConditions` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpEntityRoleDto>` | 列表查询实体角色按条件 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CtpUserRoleDto>` | 分页查询用户角色按条件 |
| `authOrgAdmin` | `SingleRequest<CtpAuthOrgAdminDto> arg0` | `SingleResponse<Integer>` | 校验/授予组织管理员角色 |
| `roleAuthBatch` | `SingleRequest<CtpAuthorizationRuleSyncDto> arg0` | `SingleResponse<CtpAuthorizationRuleSyncResultDto>` | 批量给用户授角色 |
| `selectCtpEntityRolePageByConditions` | `PageRequest arg0` | `PageResponse<CtpEntityRoleDto>` | 分页查询实体角色Ctp按条件 |

### `com.seeyon.ctp.user.api.org`

#### CtpAuthorizationRuleOrgAppService

`com.seeyon.ctp.user.api.org.CtpAuthorizationRuleOrgAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<CtpAuthorizationRuleAllDto> arg0` | `SingleResponse<Long>` | 新建规则 |
| `update` | `SingleRequest<CtpAuthorizationRuleAllDto> arg0` | `SingleResponse<Integer>` | 修改规则 |
| `delete` | `SingleRequest<CtpAuthorizationRuleDeleteDto> arg0` | `SingleResponse<Integer>` | 删除规则 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CtpAuthorizationRuleDto>` | 分页查询规则按条件 |
| `selectAuthorizationObject` | `SingleRequest<CtpAuthorizationSearchDto> arg0` | `SingleResponse<CtpAuthorizationObjectDto>` | 查询AuthorizationObject |
| `selectAuthorizationEntity` | `SingleRequest<Long> arg0` | `SingleResponse<CtpAuthorizationEntityDto>` | 查询实体Authorization |
| `selectAuthorizationFuncList` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<CtpAuthorizationRuleFuncListDto>` | 列表查询AuthorizationFunc |
| `selectAuthorizationFuncListByRole` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<CtpAuthorizationRuleByRoleDto>` | 列表查询AuthorizationFunc按角色 |
| `selectDuplicateRolesRule` | `SingleRequest<CtpAuthorizationRuleCustomDto> arg0` | `SingleResponse<CtpAuthorizationRuleCustomDto>` | 查询角色规则Duplicate |

#### CtpOrgAdminOrgAppService

`com.seeyon.ctp.user.api.org.CtpOrgAdminOrgAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `configAdmin` | `SingleRequest<CtpOrgAdminConfigDto> arg0` | `SingleResponse<Integer>` | 配置组织管理员 |
| `selectByOrgId` | `SingleRequest<Long> arg0` | `SingleResponse<CtpOrgAdminConfigDto>` | 查询组织配置按组织 |
| `selectByOrgIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<CtpOrgAdminDto>` | 查询组织按组织 |
| `selectByUserId` | `SingleRequest<Long> arg0` | `ListResponse<CtpOrgAdminDto>` | 查询组织按用户 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CtpOrgAdminDto>` | 分页查询组织按条件 |
| `selectListByConditions` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpOrgAdminDto>` | 列表查询组织按条件 |
| `selectManageScopeByOrgAndUser` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<ManageScopeEnum>` | 查询管理范围按组织用户 |
| `selectTreeMembersAdminEnable` | `—` | `SingleResponse<Boolean>` | 树查询人员AdminEnable |
| `selectOrgAdminByOrgIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<CtpOrgAdminConfigDto>` | 查询组织Admin按组织 |
| `batchConfigOrgAdmin` | `SingleRequest<List<CtpOrgAdminConfigDto>> arg0` | `SingleResponse<Integer>` | 批量配置组织管理员 |
| `deleteOrgAdminByOrgId` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 删除组织Admin按组织 |
| `createAdmin` | `SingleRequest<CtpOrgAdminConfigDto> arg0` | `SingleResponse<Long>` | 新建Admin |
| `updateAdmin` | `SingleRequest<CtpOrgAdminConfigDto> arg0` | `SingleResponse<Integer>` | 修改Admin |

#### CtpOrgSelectPeopleAppService

`com.seeyon.ctp.user.api.org.CtpOrgSelectPeopleAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CtpRoleDto>` | 分页查询角色按条件 |

#### CtpOrgUpgradeAppService

`com.seeyon.ctp.user.api.org.CtpOrgUpgradeAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `updateBatchUserCode` | `SingleRequest<Map<Long, String>> arg0` | `SingleResponse<Integer>` | 批量修改用户编码 |

#### CtpPermissionApprovalOrgAppService

`com.seeyon.ctp.user.api.org.CtpPermissionApprovalOrgAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `update` | `SingleRequest<CtpPermissionApprovalDto> arg0` | `SingleResponse<Integer>` | 修改权限审批 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<CtpPermissionApprovalDto>` | 查询权限审批按 id |
| `batchKnow` | `—` | `SingleResponse<Integer>` | 批量知会权限审批人 |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<CtpPermissionApprovalDto>` | 分页查询权限审批按条件 |

#### CtpSecretApprovalOrgAppService

`com.seeyon.ctp.user.api.org.CtpSecretApprovalOrgAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<List<CtpSecretApprovalDto>> arg0` | `SingleResponse<Integer>` | 新建（SingleRequest） |
| `selectPendingInfo` | `SingleRequest<List<Long>> arg0` | `ListResponse<Map<String, Object>>` | 查询待办 |

#### SyncOrgRoleTempAppService

`com.seeyon.ctp.user.api.org.SyncOrgRoleTempAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `syncOrgRole` | `SingleRequest<Map<String, Set<Long>>> arg0` | `SingleResponse<Boolean>` | 同步组织角色 |

### `com.seeyon.ctp.user.api.passwordCheck`

#### PasswordCheckService

`com.seeyon.ctp.user.api.passwordCheck.PasswordCheckService` · 构件 `ctp-user-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `checkPasswordStrength` | `String arg0` | `Boolean` | 检查密码Strength |

### `com.seeyon.ctp.user.api.sso`

#### CtpUserSsoAuthProviderService

`com.seeyon.ctp.user.api.sso.CtpUserSsoAuthProviderService` · 构件 `ctp-user-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `setServerDomain` | `String arg0` | `void` | 设置域Server |
| `setServerEnv` | `CtpUserSpiServerEnvDto arg0` | `void` | 设置ServerEnv |
| `getRequestParaKey` | `—` | `String` | 获取键RequestPara |
| `getSsoLoginUrl` | `HttpServletRequest arg0` | `String` | 获取登录SsoUrl |
| `sendVerifyCode` | `String arg0` | `Boolean` | 发送编码Verify |
| `isRedirectShortLink` | `—` | `Boolean` | 判断RedirectShortLink |
| `shortLinkMode` | `—` | `ShortLinkModeEnum` | SSO 短链模式下的处理器（SPI） |
| `getUserLoginInfo` | `HttpServletRequest arg0` | `CtpUserSpiLoginUserInfoDto` | 获取用户登录 |
| `getEncodeLogoutRedirectUrl` | `—` | `String` | 获取EncodeLogoutRedirectUrl |
| `thirdSsoLogout` | `HttpServletRequest arg0` | `void` | 第三方 SSO 登出 |
| `getUserLoginInfoForMobile` | `String arg0` | `CtpUserSpiLoginUserInfoDto` | 获取用户登录ForMobile |
| `tokenExpiredSetNull` | `—` | `boolean` | 设置Null |
| `rebuildCtpUserDtoList` | `List<CtpUserSpiUserDto> arg0` | `Long` | 列表重建用户CtpDto |
| `refreshThirdToken` | `String arg0` | `CtpUserSpiThirdTokenDto` | 刷新第三方令牌 |
| `refreshThirdTokenByConfig` | `String arg0` | `CtpUserSpiThirdTokenDto` | 刷新第三方令牌按配置 |
| `get4aTokenKey` | `—` | `String` | 取 4A 认证 token 的键名 |
| `getTidCode` | `—` | `String` | 获取编码Tid |
| `mapSupportsAuthTokenEnum` | `—` | `Map<String, CtpUserSpiAuthTokenEnum[]>` | 声明支持哪些认证令牌类型（SPI 能力探测） |
| `getSuccessAuthTokenEnum` | `—` | `CtpUserSpiAuthTokenEnum` | 获取认证令牌枚举Success |
| `getThirdLogoutParams` | `Map<String, Object> arg0` | `CtpUserSpiThirdLogoutDto` | 获取第三方LogoutParams |

### `com.seeyon.ctp.user.api.udc`

#### CtpAuthorizationUdcAppService

`com.seeyon.ctp.user.api.udc.CtpAuthorizationUdcAppService` · 构件 `ctp-user-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `autoAuthAppRoles` | `SingleRequest<String> arg0` | `SingleResponse<Long>` | 自动给 UDC 应用授予角色（应用发布时） |
| `selectAppFirstLinks` | `SingleRequest<String> arg0` | `SingleResponse<CtpRoleLinkDto>` | 查询应用第一级Links |

### `com.seeyon.ctp.user.api.user`

#### CustomUserInfoService

`com.seeyon.ctp.user.api.user.CustomUserInfoService` · 构件 `ctp-user-api`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `filterCustomUserInfo` | `Map<String, Object> arg0` | `Map<String, Object>` | 过滤自定义用户信息（脱敏/裁剪字段） |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 70 个领域服务，下表列**方法数最多的 40 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `CtpMenuService` | 113 | 菜单 · 查询×50 / 获取×13 / 处理×11 |
| `CtpEntityResourceService` | 107 | 实体资源 · 查询×38 / 获取×18 / 新建×5 |
| `CtpUserService` | 96 | 用户 · 查询×34 / 修改×10 / 获取×9 |
| `CtpResourceService` | 78 | 资源 · 查询×28 / 获取×9 / 删除×6 |
| `CtpEntityRoleService` | 74 | 实体角色 · 查询×22 / 删除×12 / 处理×8 |
| `CtpAuthorizationRuleService` | 50 | 规则 · 查询×15 / 删除×12 / 新建×8 |
| `CtpRoleResourceService` | 50 | 角色资源 · 查询×24 / 修改×4 / 保存×4 |
| `CtpUserRoleService` | 47 | 用户角色 · 查询×20 / 删除×8 / 新建×5 |
| `CtpRoleService` | 37 | 角色 · 查询×16 / 删除×5 / 新建×3 |
| `CtpUserDefaultIdentityService` | 25 | 用户 · 查询×9 / 获取×8 / 新建×2 |
| `CtpLoginPreConfigService` | 22 | 登录配置 · 查询×13 / 判断有×2 / 新建×1 |
| `CtpOrgAdminService` | 18 | 组织 · 查询×12 / 删除×4 / 新建×2 |
| `CtpUserDomainCacheService` | 17 | 用户域 · 查询×14 / 获取×3 |
| `CtpUserParameterService` | 17 | 用户参数 · 获取×10 / 设置×3 / 判断×2 |
| `CtpRoleApplicationService` | 16 | 角色应用 · 查询×8 / 保存×4 / 删除×2 |
| `ThirdSsoAvoidConfigService` | 15 | 第三方配置 · 构建×8 / 获取×4 / 加载×1 |
| `CtpOrgRoleResourceService` | 14 | 组织角色资源 · 查询×9 / 新建×1 / 获取×1 |
| `CtpLoginDeviceService` | 13 | 登录 · 查询×6 / 检查×2 / 新建×1 |
| `CtpAuthorizationRuleFuncService` | 12 | 规则 · 查询×6 / 获取×3 / 初始化×1 |
| `CtpMenuCategoryService` | 12 | 菜单分类 · 查询×5 / 新建×3 / 删除×2 |
| `CtpLdapService` | 11 | Ldap · 查询×3 / 新建×2 / 校验×2 |
| `CtpDataPermissionService` | 10 | 权限 · 查询×4 / 新建×2 / 修改×2 |
| `CtpPermissionApprovalService` | 10 | 权限审批 · 查询×5 / 新建×2 / 审计×1 |
| `CtpResourcePermissionService` | 10 | 资源权限 · 查询×5 / 删除×3 / 新建×1 |
| `AuthConfigReloadService` | 10 | 认证配置 · 获取×6 / 刷新×1 / 重载×1 |
| `V5AvoidLoginProviderService` | 10 | 登录 · 获取×5 |
| `CtpUserDataPermissionService` | 9 | 用户权限 · 查询×5 / 新建×2 / 删除×2 |
| `CtpUserLogService` | 9 | 用户日志 · 移动×4 / 删除×4 / 记录×1 |
| `AuthConfigPersistenceService` | 9 | 认证配置 · 列出×4 / 获取×2 / 修改×2 |
| `CtpLogIndexService` | 9 | 日志 · 查询×2 / 获取×2 / 复制×2 |
| `CtpAuthorizationLogService` | 8 | 日志 · 查询×4 / 新建×2 / 获取×2 |
| `CtpLockedUserService` | 8 | 用户 · 删除×2 / 新建×1 / 修改×1 |
| `CtpUserFileCacheService` | 8 | 用户文件 · 删除×3 / 获取×2 |
| `CtpUserPasswordService` | 8 | 用户密码 · 新增×3 / 查询×2 / 检查×1 |
| `PersonalSettingService` | 8 | 设置 · 检查×2 / 获取×2 / 设置×2 |
| `CtpUserMappingService` | 7 | 用户映射 · 查询×3 / 列出×2 / 保存×1 |
| `CtpAuthConfigService` | 6 | 认证配置 · 查询×2 / 列出×1 / 处理×1 |
| `CtpAvoidLoginUserHasTenantService` | 6 | 登录用户租户 · 获取×5 / 列出×1 |
| `CtpAvoidLoginUserIgnoreTenantService` | 6 | 登录用户租户 · 获取×5 / 列出×1 |
| `CtpSyTokenAvoidLoginService` | 6 | 令牌登录 · 获取×2 / 校验×2 / 刷新×1 |

## biz 层：事件与监听

事件 18 个 · 监听器 13 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| CtpAuthorizationRule | `CtpAuthorizationRuleDeleteEvent` |
| CtpAuthorizationRuleNoPass | `CtpAuthorizationRuleNoPassEvent` |
| CtpAuthorizationRulePass | `CtpAuthorizationRulePassEvent` |
| CtpEntityRole | `CtpEntityRoleCreateEvent` |
| CtpLockedApproval | `CtpLockedApprovalEvent` |
| CtpMenu | `CtpMenuEvent` |
| CtpResourceChange | `CtpResourceChangeEvent` |
| CtpRoleApplication | `CtpRoleApplicationDeleteEvent` |
| CtpRoleApproval | `CtpRoleApprovalEvent` |
| CtpRoleDisabled | `CtpRoleDisabledEvent` |
| CtpRoleEnabled | `CtpRoleEnabledEvent` |
| CtpRoleFail | `CtpRoleFailEvent` |
| CtpRolePass | `CtpRolePassEvent` |
| CtpRoleResourceChange | `CtpRoleResourceChangeEvent` |
| CtpUserRole | `CtpUserRoleCreateEvent`, `CtpUserRoleDeleteEvent` |
| UserLoginFail | `UserLoginFailEvent` |
| UserLoginSuccess | `UserLoginSuccessEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `CtpRoleEventListener` | 23 |
| `AfterTenantEventListener` | 14 |
| `CtpUserLoginEventListener` | 9 |
| `CtpUserEnumItemEventListener` | 4 |
| `CtpAuthorizationEventListener` | 3 |
| `CtpEntityRoleEventListener` | 2 |
| `CtpApplicationEventListener` | 1 |
| `CtpDataEventListener` | 1 |
| `CtpLockedApprovalEventListener` | 1 |
| `CtpMenuEventListener` | 1 |
| `CtpResourceEventListener` | 1 |
| `SPIProviderRegisterEventListener` | 1 |
| `CtpUserRoleEventListener` | 0 |

## web 层：Controller

共 39 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 推送/被引用（Refer*） | `ReferCtpUserRoleController` | 7 |
| 核心实体 CRUD | `AuthController` | 96 |
| 核心实体 CRUD | `CtpMenuController` | 28 |
| 核心实体 CRUD | `CtpUserApiController` | 28 |
| 核心实体 CRUD | `CtpRolePermissionController` | 17 |
| 核心实体 CRUD | `CtpUserParameterController` | 17 |
| 核心实体 CRUD | `PersonalSettingController` | 14 |
| 核心实体 CRUD | `CtpOrgAdminController` | 13 |
| 核心实体 CRUD | `CtpUserController` | 13 |
| 核心实体 CRUD | `CtpLogController` | 12 |
| 核心实体 CRUD | `CtpSecretEnumController` | 12 |
| 核心实体 CRUD | `CtpUserTestController` | 12 |
| 核心实体 CRUD | `CtpAuthorizationRuleController` | 12 |
| 核心实体 CRUD | `CtpUserPermissionController` | 11 |
| 核心实体 CRUD | `CtpRoleController` | 9 |
| 核心实体 CRUD | `CtpLdapController` | 7 |
| 核心实体 CRUD | `CtpMenuCategoryController` | 7 |
| 核心实体 CRUD | `CtpUserRoleController` | 7 |
| 核心实体 CRUD | `SandboxAuthController` | 7 |
| 核心实体 CRUD | `CtpLoginDeviceController` | 6 |
| 核心实体 CRUD | `AuthConfigController` | 5 |
| 核心实体 CRUD | `CtpUserCustomizeController` | 5 |
| 核心实体 CRUD | `CtpOrgAdminOrgController` | 5 |
| 核心实体 CRUD | `CtpDataPermissionController` | 4 |
| 核心实体 CRUD | `CtpUserDefaultIdentityController` | 4 |
| 核心实体 CRUD | `CtpDataSignController` | 3 |
| 核心实体 CRUD | `CtpLockedUserController` | 3 |
| 核心实体 CRUD | `CtpUserTransferController` | 3 |
| 核心实体 CRUD | `CtpPermissionApprovalController` | 3 |
| 核心实体 CRUD | `CtpSecretApprovalController` | 3 |
| 核心实体 CRUD | `CtpIdentityVerifyController` | 2 |
| 核心实体 CRUD | `CtpLockedIpController` | 2 |
| 核心实体 CRUD | `CtpLoginPreConfigController` | 2 |
| 核心实体 CRUD | `CtpPublishController` | 2 |
| 核心实体 CRUD | `CtpUserSimpleController` | 2 |
| 核心实体 CRUD | `LevelProtectionController` | 2 |
| 核心实体 CRUD | `CtpAuthProviderController` | 1 |
| 核心实体 CRUD | `CtpResourceController` | 1 |
| 核心实体 CRUD | `CtpSecretController` | 1 |

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
| 40 接口 / 220 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 70 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 18 事件 / 13 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 39 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径 | 未取证 | `UNVERIFIED` |
| 落表 | 未取证 | `UNVERIFIED` |
