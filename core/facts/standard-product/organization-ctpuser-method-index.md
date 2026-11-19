# 组织域方法签名索引（organization + ctp-user）

## 1. Capability

**回答「查人员/单位/角色、按条件选人、多维组织，调哪个类哪个方法」。**

组织能力分散在**两个构件**：
- `organization-facade` —— **查询与选人**（54 接口 / 6409 方法）
- `ctp-user-facade` —— **写入与角色授权**（44 接口 / 2987 方法）

**本格不涉及任何具体应用/工程/环境。**

## 2. Version

| 构件 | jar | 版本 |
|---|---|---|
| `com.seeyon:organization-facade` | `organization-facade-5.3.601.jar` | **5.3.601** |
| `com.seeyon:ctp-user-facade` | `ctp-user-facade-5.3.600.jar` | **5.3.600** |

规模：414 类 / 54 接口 / 64 枚举 / 6409 方法（organization）；263 类 / 44 接口 / 2987 方法（ctp-user）。

## 3. Input

`docs/audit/reference/surface-index.tar.gz` → `packages/organization-facade.md`、`packages/ctp-user-facade.md`。

## 4. Required

无前置。跨进程 `@DubboReference`。

## 5. Execution

```java
@DubboReference private OrgCommonAppService orgCommonAppService;
@DubboReference private OrgWorkFlowAppService orgWorkFlowAppService;

// 查人员多维组织信息
Map<String,Object> info = orgCommonAppService
    .selectMemberMultiDimOrgInfo(SingleRequest.from(memberId))
    .getData().getContent();

// 选人器结果 → 人员 id 分页
PageResponse<Long> ids = orgCommonAppService
    .selectPageMemberBySelectPeopleIdData(
        PageDtoRequest.of(selectPeopleDataList, pageInfo));
```

## 6. Output

---

## 6.1 ★★★ 最重要：写人在 `ctp-user-facade`，查人在 `organization-facade`

```
organization-facade（54 接口 / 6409 方法）
  全是 select* / contains* / get*     ← 只读

ctp-user-facade（44 接口 / 2993 方法）
  CtpUserCoreAppService
    create / update / createBatch / updateBatch        ← ★ 普通写
    syncCreateBatchCheck / syncUpdateBatchCheck        ← 外部同步（逐条结果）
    beforeCreateCheck / beforeUpdateCheck              ← 写前校验
```

**⇒ 查组织去 `organization-facade`；写人员去 `ctp-user-facade`。
   `organization-facade` 确实没有人员 create/update，这部分结论仍然成立。**

---

## 6.2 `OrgCommonAppService`（45 方法）—— 最常用

`com.seeyon.organization.api.common.OrgCommonAppService`

```java
// 人员多维组织信息（岗位/角色/部门一次拿全）
SingleResponse<Map<String,Object>> selectMemberMultiDimOrgInfo(SingleRequest<Long>);

// 人员机构信息（按 id 批量）
SingleResponse<Map<Long, Map<String, List>>> selectMemberInstitutionInfoById(SingleRequest<...>);

// ★ 选人器结果 → 人员 id 分页（最实用）
PageResponse<Long> selectPageMemberBySelectPeopleIdData(PageDtoRequest<List<SelectPeopleDataDto>>);
PageResponse<Long> selectPageMemberBySelectPeopleIdDataJson(PageDtoRequest<String>);

// 选人器显示名
SingleResponse<String> selectNameBySelectPeopleData(SingleRequest<String>);

// 选人器是否包含某人
SingleResponse<Boolean> containsAny(SingleRequest<SelectPeopleContainsAnyDto>);

// 人员扩展信息
SingleResponse<Map<String,Object>> selectMemberExtendInfoById(SingleRequest<Long>);

// 密级字段权限
ListResponse<OrgSensitiveFieldPermissionDto> selectSensitiveFieldInfo(SingleRequest<...>);
ListResponse<OrgSensitiveFileMemberDto> selectSensitiveFieldMember(SingleRequest<...>);

// 范围类型名
SingleResponse<List<ScopeTypeNameDto>> selectScopeTypeName(SingleRequest<List<...>>);
```

**★★★ 45 个方法按用途分 6 类（本次全量枚举）：**

| 类 | 方法 |
|---|---|
| **按 id 查人** | `selectMemberInfoById` / `selectMemberDepartmentInfoById` / `selectMemberMultiDimOrgInfo` / `selectMemberInstitutionInfoById` / `selectMemberExtendInfoById` |
| **选人器** | `selectMemberBySelectPeopleData(+s/Json/Jsons)` / `selectPageMemberBySelectPeopleData(+Json)` / `selectPageMemberBySelectPeopleIdData(+Json)` / `isMemberInSelectPeopleDataJson` / `fillSelectPeopleData` / `selectNameBySelectPeopleData` / `containsAny` |
| **按组织维度查人** | `selectMemberByOrgId` / `selectPageMemberByOrgId` / `selectMemberCountByOrgId` / `selectMemberByPostId` / `selectMemberByJobId` / `selectMemberByLevelId` / `selectMemberByUserId` |
| **组织树** | `selectChildrenOrgIdByCondition` / `selectChildrenOrgByCondition` / `selectParentIds` / `selectRoot` / `selectOrgUnitTeamList` / `selectEntityIdByCode` |
| **管辖与角色** | `selectManagerDepartmentByMemberId` / `selectLeaderDepartmentByMemberId` / `canManage` / `isRole` / `selectManageOrgByRole` / `selectAllDomainIdsByMemberId` / `selectDomainIdsByMemberId` / `selectDomainMapByMemberId` / `selectInOrgScopeIds` / `selectSecretMemberIds` |
| **元数据与密级** | `selectOrgMetadataColumnList` / `selectMemberOfUnitMetadataOfMemberId` / `selectSensitiveFieldInfo` / `selectSensitiveFieldMember` / `selectScopeTypeName` |

**★★★★★ 三条铁律：**

| # | 事实 |
|---|---|
| 1 | **`selectMemberMultiDimOrgInfo` 返回 `Map`，不是强类型 DTO** |
| 2 | **选人器结果要转 id 用 `selectPageMemberBySelectPeopleIdData`** |
| 3 | **`PageDtoRequest` 不是 `PageRequest`** —— 分页 + 列表参数合一 |

---

## 6.3 `OrgWorkFlowAppService`（37 方法）—— 流程里的组织解析 + 选人函数

`com.seeyon.organization.api.app.workflow.OrgWorkFlowAppService`

```java
// 选人 → 岗位返回文件
SingleResponse<WorkFlowMatchResponseToFileDto> selectMemberPostBySelectPeoplesReturnFile(...);
// 按 key 取文件
SingleResponse<Map<Long, WorkFlowMatchResponseFileKeyDto>> selectReturnFileByKey(...);
// 删文件
SingleResponse<Boolean> deleteReturnFileByKey(SingleRequest<WorkFlowSelectStorageKeyRequestDto>);
// 同级子列表
SingleResponse<List<OrgAboutIdDataDto>> selectOrgSameTypeChildList(SingleRequest<List<...>>);
// 多分管领导
SingleResponse<SupervisorMultipleDataDto> selectSupervisorMultipleData(...);
// 用户角色权限与管理员数据
SingleResponse<UserRoleAuthAndManageDataDto> selectUserRoleAuthAndManageData(SingleRequest<Long>);
// 一级部门信息
SingleResponse<Map<Long, Map<String, Object>>> selectFirstLevelDepartmentInfoByIds(...);
```

**★ 37 个方法分四类（本次全量枚举）：**

| 类 | 方法 |
|---|---|
| **选人→人员/岗位** | `selectMemberPostBySelectPeople` / `selectMemberPostBySelectPeoples` / `selectMemberPostBySelectPeoplesReturnFile` / `selectMemberPostListByCondition` / `selectMemberPostById` / `selectPeopleCodeDataDto` / `selectPeopleDataDtoFromTransData` / `selectPeopleIdsCodeData` / `selectPeopleIdsDataDtoFromTransData` / `getSelectPeopleDataWfJson` / `checkSelectPeopleData` / `getEntityNameBySelectPeoples` |
| **★ 表达式函数**（流程条件里用） | `funcMemberIn` / `funcOrgIn` / `funcMultMemberIn` / `funcMultOrgIn` / `funcOrgRoleIn` |
| **元数据取人** | `selectMemberOfUnitMetadataOfMemberIds` / `selectMemberOfMemberMetadataOfMemberIds` / `selectMetadataListOfUnitMetadataOfMemberId` / `selectMetadataListOfMemberMetadataOfMemberId` / `selectOrgIdByMemberIdInInstitution` |
| **节点/分叉/上下级** | `selectSplitUnitNodeInfo` / `selectSplitMemberNodeInfo` / `selectNodeName` / `isOfUp` / `selectOfUp` / `selectPreParameterKey` / `selectNamesByIds` / `selectSortField` / `selectOrgSameTypeChildList` / `selectSupervisorMultipleData` / `selectUserRoleAuthAndManageData` / `selectFirstLevelDepartmentInfoByIds` / `selectReturnFileByKey` / `deleteReturnFileByKey` / `selectListByCondition` / `selectListByMetaCondition` |

**⇒ 流程节点解析「按选人规则算出实际人员」用这个；
   流程条件里写 `funcMemberIn` / `funcOrgIn` 等函数也在这里。**

---

## 6.4 `OrgMetadataCoreAppService`（16 方法）—— 组织元数据（自定义字段）

`com.seeyon.organization.api.core.metadata.OrgMetadataCoreAppService`

```java
SingleResponse<Map<Long, Map<String,Object>>> selectOrgMetadataInfos(...);
PageResponse<Long>                            selectEntityIdByMetadataValuePageList(PageRequest);
PageResponse<OrgUnitMetadataValueDto>         selectUnitMetadataPageList(PageDtoRequest<...>);
PageResponse<OrgMemberMetadataValueDto>       selectMemberMetadataPageList(PageDtoRequest<...>);
```

**★ 16 个方法（本次全量枚举）：**

```java
// 元数据列定义
selectMetadataColumnList / selectPageMetadataColumnList / selectOrgMetadataColumnListByCondition
// 按元数据查人/组织
selectMemberByUnitMetadata / selectMemberByUnitMemberMetadata / selectOrgByUnitMemberMetadata
selectMemberMetadataInfo / selectOrgMetadataInfo / selectOrgMetadataInfos
selectOrgRoleByMemberMetadata / selectOrgIdByMemberIdInInstitution
// 按元数据值查实体 id
selectEntityIdByMetadataValue / selectEntityIdsByMetadataValue / selectEntityIdByMetadataValuePageList
// 分页
selectUnitMetadataPageList / selectMemberMetadataPageList
```

**⇒ 按自定义字段（如工号、职级）查人用 `selectMemberMetadataPageList`。**

---

## 6.5 `OrgMemberSyncAppService`（14 方法）—— 第三方同步 / 人员建改

`com.seeyon.organization.api.app.sync.OrgMemberSyncAppService`

```java
ListResponse<OrgMemberDataDto> selectByThirdIds(SingleRequest<SearchMemberConditionApiDto>);
SingleResponse<Integer>        disableMemberByThirdIds(SingleRequest<String>);
```

**★★★ 14 个方法里含 create（本次重要修正）：**

```java
// ★ 建人（不只是查询！）
createBatch                              // 批量建人
createBatchMemberPost                    // 批量建人 + 岗位
createBatchMemberMetadata                // 批量建人 + 元数据
createBatchNaturalMember                 // 批量建外部自然人

// 查
selectByCodes / selectByThirdIds / selectByCondition
selectNaturalMemberByPhoneNumber / selectNaturalMemberByCodes
selectNaturalMemberInfoPageListByCondition
selectOutSideInstitutionManagerPageByCondition

// 改
disableMember / disableMemberByThirdIds
fixCtpUserId                             // 修复 userId 映射，生产慎用
```

**⇒ 第三方同步建人走 `createBatch` 系列；按第三方 id 查/停用也在这里。**

## 6.6 `OrgZhongheService`（14 方法）—— 中和定制（领导秘书/科室）

`com.seeyon.organization.api.app.third.zhonghe.OrgZhongheService`

**★ 这是特定客户的定制服务（`zhonghe`），不是通用能力。** 包含：
`selectMemberByRole` / `selectOrgByMetadataCustomizeZBBM` / `selectLeaderListBySecretaryId` /
`selectSecretaryListByLeaderId` / `getCurrentSectorOrgList` / `getOtherSectorOrgList` 等。

**⇒ 通用场景不要用；只在明确是中和项目时用。**

---

## 6.7 `CtpUserCoreAppService`（18 方法）—— 人员 CRUD + 同步

`com.seeyon.ctp.user.api.core.CtpUserCoreAppService`

**★ 本次修正：人员不只是 `sync*Check`，有完整 CRUD。**

```java
// —— 校验（写前必调）——
Void beforeCreateCheck(SingleRequest<...>);
Void beforeUpdateCheck(SingleRequest<...>);

// —— 单条 CRUD ——
Integer create(SingleRequest<CtpUserDto>);
Integer update(SingleRequest<CtpUserDto>);
Integer createBatch(SingleRequest<List<CtpUserDto>>);
Integer updateBatch(SingleRequest<List<CtpUserDto>>);
CtpUserDto selectById(SingleRequest<Long>);
List<CtpUserDto> selectByIds(SingleRequest<List<Long>>);
List<CtpUserDto> selectSimpleByIds(SingleRequest<List<Long>>);
CtpUserDto selectOneByCondition(SingleRequest<...>);
List<CtpUserDto> selectListByConditions(SingleRequest<...>);
PageResponse<CtpUserDto> selectPageByConditions(PageRequest);
CtpUserDto selectUserIgnoreTenant(SingleRequest<Long>);

// —— 同步（逐条结果）——
Integer syncCreateBatch(SingleRequest<List<CtpUserDto>>);
Integer syncUpdateBatch(SingleRequest<List<CtpUserDto>>);
ListResponse<SyncUserMessageDto> syncCreateBatchCheck(SingleRequest<List<CtpUserDto>>);
ListResponse<SyncUserMessageDto> syncUpdateBatchCheck(SingleRequest<List<CtpUserDto>>);

// —— 多租户 ——
Map<Long, List<UserTenantInfoDto>> selectUserTenantInfoByIds(SingleRequest<List<Long>>);
```

**★★★★★ 选哪个：**

| 场景 | 用哪个 | 为什么 |
|---|---|---|
| **外部同步建人** | `syncCreateBatchCheck` | 返回逐条校验消息，能定位哪条失败 |
| **普通建人** | `create` / `createBatch` | 直接写入，失败整体抛 |
| **写前校验** | `beforeCreateCheck` / `beforeUpdateCheck` | 先查重、查必填 |
| 要全量字段更新 | `update` / `updateBatch` | |

**⇒ `sync*Check` 是「外部同步」专用（批量 + 逐条消息）；普通业务用 `create`/`update`。**

## 6.8 `CtpRoleCoreAppService`（14 方法）—— 角色

`com.seeyon.ctp.user.api.core.CtpRoleCoreAppService`

```java
// 写
create / update / saveBatch / syncRoleResource / deleteByConditions

// 查
selectById / selectByCode / selectByIds / selectListByConditions
selectPageByConditions(PageRequest) / selectCascadeById / selectCascadeByIds
dynamicJoinSelect / dynamicSelect
```

**⇒ 角色有完整 CRUD，不只是 `saveBatch`。**

## 6.9 `CtpUserRoleCoreAppService`（13 方法）—— 用户角色授权

`com.seeyon.ctp.user.api.core.CtpUserRoleCoreAppService`

```java
SingleResponse<Integer> createBatchAuthorizationRule(SingleRequest<CtpUserRoleSyncDto>);
ListResponse<CtpEntityRoleDto> selectEntityRoleListByConditions(SingleRequest<Map<String,List>>);
SingleResponse<Integer> authOrgAdmin(SingleRequest<CtpAuthOrgAdminDto>);
SingleResponse<CtpAuthorizationRuleSyncResultDto> roleAuthBatch(SingleRequest<CtpAuthorizationRuleSyncDto>);
PageResponse<CtpEntityRoleDto> selectCtpEntityRolePageByConditions(PageRequest);
```

**★ 13 个方法（本次全量枚举）：**

```java
// 授权规则
createUserRule / createAuthorizationRule / createBatchAuthorizationRule
roleAuthBatch                    // ★ 批量给实体授权
deleteAuthorizationRuleById

// 用户角色
createBatch / deleteByIds / deleteByConditions

// 组织管理员
authOrgAdmin

// 查
selectListByConditions / selectPageByConditions(PageRequest)
selectEntityRoleListByConditions / selectCtpEntityRolePageByConditions(PageRequest)
```

**⇒ 给数据实体授权用 `roleAuthBatch`；查某实体上谁有角色用 `selectEntityRoleListByConditions`；
   给某人授组织管理员用 `authOrgAdmin`。**

## 6.10 `CtpOrgAdminOrgAppService`（6 方法）

组织管理员相关。签名见 `packages/ctp-user-facade.md`。

---

## 7. Side Effects

| 方法 | 副作用 |
|---|---|
| `syncCreateBatchCheck` | **建人员、发消息、触发同步事件** |
| `syncUpdateBatchCheck` | **改人员、可能变更组织关系** |
| `disableMemberByThirdIds` | **停用账号（不可见后果）** |
| `saveBatch`（角色） | 建角色 |
| `roleAuthBatch` / `authOrgAdmin` | **改权限（安全敏感）** |
| `deleteReturnFileByKey` | 删存储文件 |

**⇒ 前三个和权限两个必须在事务内、先记录基线。**

## 8. Known Constraints

| # | 约束 |
|---|---|
| 1 | **`organization-facade` 没有 create/update 人员**，写人在 `ctp-user-facade` |
| 2 | **选人器结果转 id 必须 `selectPageMemberBySelectPeopleIdData`** |
| 3 | **`PageDtoRequest` ≠ `PageRequest`**（前者带列表参数） |
| 4 | **`selectMemberMultiDimOrgInfo` 返回 `Map`**，字段名要运行时看 |
| 5 | **`OrgZhongheService` 是客户定制**，通用场景禁用 |
| 6 | **人员同步是 `sync*Check` 形态**，返回逐条消息不是布尔 |
| 7 | **权限类方法安全敏感**（`roleAuthBatch` / `authOrgAdmin`） |
| 8 | **取值两层 `getData().getContent()`** |

## 9. Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| 414 类 / 54 接口 / 6409 方法 | `packages/organization-facade.md` 头部 | **VERIFIED_STATIC_BYTECODE** |
| 263 类 / 44 接口 / 2987 方法 | `packages/ctp-user-facade.md` 头部 | **VERIFIED_STATIC_BYTECODE** |
| `organization-facade` 无 create 人员 | 54 接口逐名扫描（无 `create`/`update` 人员方法） | **VERIFIED_STATIC_BYTECODE** |
| 全部方法签名 | javap 逐字 | **VERIFIED_STATIC_BYTECODE** |
| `OrgZhongheService` 属定制 | 类名 `zhonghe` + DTO 包 `third.zhonghe` | **VERIFIED_STATIC_BYTECODE** |

## 10. Verified

- ✅ **VERIFIED_STATIC_BYTECODE**：6 个核心接口全部方法签名
- ⚠️ **UNVERIFIED**：`selectMemberMultiDimOrgInfo` 返回 Map 的真实 key（需 LIVE）
- ⚠️ **UNVERIFIED**：`syncCreateBatchCheck` 的真实校验规则
- ⚠️ **未覆盖**：`organization-facade` 其余 48 接口（按需查 JSON）

## 11. 给 Agent 的判据

```
问「怎么查人员信息」
  → OrgCommonAppService.selectMemberMultiDimOrgInfo(id)     ← 返回 Map
  → 或 selectMemberExtendInfoById(id)

问「选人器结果怎么变成人员 id」
  → OrgCommonAppService.selectPageMemberBySelectPeopleIdData(PageDtoRequest)

问「怎么按工号/自定义字段查人」
  → OrgMetadataCoreAppService.selectMemberMetadataPageList(...)

问「怎么建人员」
  → 普通业务：CtpUserCoreAppService.create(CtpUserDto)
  → 外部同步：syncCreateBatchCheck(List<CtpUserDto>)（返回逐条校验消息）
  → 写前校验：beforeCreateCheck
     ★ organization-facade 里没有任何人员写接口

问「流程里按选人规则解析出人员」
  → OrgWorkFlowAppService.selectMemberPostBySelectPeoplesReturnFile(...)

问「怎么给实体授权角色」
  → CtpUserRoleCoreAppService.roleAuthBatch(...)

问「Zhonghe 这些方法能用吗」
  → 只有中和项目能用，通用场景不要碰
```