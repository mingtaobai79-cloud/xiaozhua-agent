# 组织域（organization-facade）能力清单

> 来源：`organization-facade-5.3.601.jar` CFR 反编译（414 类 / 54 接口）
> ✅ **版本核对（2026-11-18）**：官方清单 5.3.600，本机 5.3.601 —— **比官方新一个小版本，结论有效**。
> 等级：`VERIFIED_STATIC_SOURCE`

---

## 1. 规模与结构

```
414 个类 / 54 个接口（含 AppService）/ 6,409 个方法
包前缀：com.seeyon.organization
```

**接口分四层（按命名后缀）：**

| 后缀 | 含义 | 例子 |
|---|---|---|
| `*BaseAppService` | **基础 CRUD** | `OrgUnitBaseAppService` / `OrgMemberBaseAppService` |
| `*CoreAppService` | **核心查询**（含元数据维度） | `OrgMemberCoreAppService` / `OrgMetadataCoreAppService` |
| `*SyncAppService` | **同步/批量写入** | `OrgMemberSyncAppService` / `OrgUnitSyncAppService` |
| `Ocip*AppService` | **开放接口**（对外集成） | `OcipUnitAppService` / `OcipMemberAppService` |

**⇒ `OrgCommonAppService`（45 方法）是「综合查询」，最常用。**

---

## 2. 核心接口：`OrgCommonAppService`（45 方法）

**包：** `com.seeyon.organization.api.common`

### 2.1 人员查询（最常用）

```java
selectMemberInfoById(SingleRequest<Long>)                 : SingleResponse<Map<String,Object>>
selectMemberDepartmentInfoById(SingleRequest<Long>)       : SingleResponse<Map<Long,Map<String,List>>>
selectMemberMultiDimOrgInfo(SingleRequest<Long>)          : SingleResponse<Map<String,Object>>     ★ 多维组织
selectMemberInstitutionInfoById(SingleRequest<Long>)      : SingleResponse<Map<Long,Map<String,List>>>   ★ 单位信息
selectMemberExtendInfoById(SingleRequest<Long>)           : SingleResponse<Map<String,Object>>
```

**⇒ 注意：返回的是 `Map<String,Object>`，不是强类型 DTO。**
**⇒ 说明组织数据是「字段可配置」的（元数据驱动），不能假设固定字段。**

### 2.2 按选人数据查人员（`SelectPeopleData` 体系）

```java
selectMemberBySelectPeopleData(SingleRequest<List<SelectPeopleDataDto>>)        : ListResponse<OrgMemberCoreDto>
selectPageMemberBySelectPeopleData(PageDtoRequest<List<SelectPeopleDataDto>>)   : PageResponse<OrgMemberCoreDto>
selectPageMemberBySelectPeopleIdData(PageDtoRequest<List<SelectPeopleDataDto>>) : PageResponse<Long>
selectMemberBySelectPeopleDatas(SingleRequest<List<List<SelectPeopleDataDto>>>) : ListResponse<List<OrgMemberCoreDto>>
selectMemberBySelectPeopleDataJson(SingleRequest<String>)                       : ListResponse<OrgMemberCoreDto>
selectPageMemberBySelectPeopleDataJson(PageDtoRequest<String>)                  : PageResponse<OrgMemberCoreDto>
selectPageMemberBySelectPeopleIdDataJson(PageDtoRequest<String>)                : PageResponse<Long>
selectMemberBySelectPeopleDataJsons(SingleRequest<List<String>>)                : ListResponse<List<OrgMemberCoreDto>>
selectNameBySelectPeopleData(SingleRequest<String>)                             : SingleResponse<String>
containsAny(SingleRequest<SelectPeopleContainsAnyDto>)                          : SingleResponse<Boolean>
```

**⇒ `SelectPeopleData` 是平台的「选人条件」统一模型。**
**⇒ 每个方法都有 `Json` 变体（接收 `String`）—— 供前端直接传 JSON。**

### 2.3 按组织维度查人员 ID

```java
selectMemberByOrgId(...)          : ListResponse<Long>      ★ 按部门查人员
selectPageMemberByOrgId(...)      : PageResponse<Long>
selectMemberCountByOrgId(...)     : SingleResponse<Integer> ★ 部门人数
selectMemberByPostId(...)         : ListResponse<Long>      ★ 按岗位
selectMemberByJobId(...)          : ListResponse<Long>
selectMemberByLevelId(...)        : ListResponse<Long>      ★ 按职级
selectMemberByUserId(...)         : SingleResponse<OrgMemberCoreDto>  ★ 按 ctp userId
selectManagerDepartmentByMemberId : ListResponse<Long>      ★ 该人管理的部门
selectLeaderDepartmentByMemberId  : ListResponse<Long>      ★ 该人分管的部门
selectAllDomainIdsByMemberId      : SingleResponse<List<Long>>
```

**⇒ 这是「按部门/岗位/职级查人员」的标准入口，不要自己写 SQL。**

### 2.4 单位树查询

```java
selectChildrenOrgIdByCondition(...)  : ListResponse<Long>
selectChildrenOrgByCondition(...)    : ListResponse<OrgUnitCoreDto>
selectParentIds(SingleRequest<Long>) : ListResponse<Long>        ★ 所有父节点
selectRoot()                         : SingleResponse<OrgUnitCoreDto>
selectOrgUnitTeamList(...)           : ListResponse<OrgUnitTeamInfoDto>
```

### 2.5 元数据 / 权限

```java
selectOrgMetadataColumnList(...)     : ListResponse<OrgMetadataColumnCoreDto>
selectSensitiveFieldInfo(...)        : ListResponse<OrgSensitiveFieldPermissionDto>   ★ 敏感字段权限
selectSensitiveFieldMember(...)      : ListResponse<OrgSensitiveFileMemberDto>
selectScopeTypeName(...)             : SingleResponse<List<ScopeTypeNameDto>>
isRole(...)                          : SingleResponse<Boolean>
```

---

## 3. `OrgUnitBaseAppService`（20 方法）—— 单位/部门 CRUD

```java
create(SingleRequest<OrgCreateUnitBaseDto>)          : SingleResponse<Long>
update(SingleRequest<OrgUpdateUnitBaseDto>)          : SingleResponse<Void>
selectById(SingleRequest<Long>)                      : SingleResponse<...>
selectByIds(SingleRequest<List<Long>>)               : ListResponse<...>
selectOrgById / selectOrgByIds                        ← 含组织信息
selectCascadeById / selectCascadeByIds                ← ★ 级联（含子单位）
selectListByConditions(ListRequest)
selectOrgListByCondition(ListRequest)
selectPageByConditions(PageRequest)
selectOrgPageListByCondition(PageRequest)
```

**⇒ 与 UDC 实体的 CRUD 命名完全一致（`create`/`update`/`selectById`/`selectCascadeById`）。**
**⇒ 说明组织模块本身也是按 UDC 模式建的（`Org*` 是 UDC 生成的产物）。**

---

## 4. `OrgMemberBaseAppService`（18 方法）—— 人员 CRUD

```java
create(SingleRequest<OrgCreateMemberBaseDto>)
update(SingleRequest<OrgUpdateMemberBaseDto>)
selectById / selectByIds
selectCascadeById / selectCascadeByIds
selectListByConditions / selectMemberListByCondition
selectPageByConditions / selectMemberPageListByCondition
selectMemberListPropertiesByMemberIds          ← ★ 只查指定列
selectMemberPageListPropertiesByCondition      ← ★ 只查指定列 + 分页
```

**⇒ `selectMemberListPropertiesBy*` 是「列裁剪」版本，与 `AllInOneBaseDao.selectListProperties*` 同构。**

---

## 5. `OrgMemberSyncAppService`（14 方法）—— 批量同步

```java
createBatch(SingleRequest<OrgBatchMemberDto>)              : ★ 批量建人员
createBatchMemberPost(SingleRequest<OrgBatchMemberPostDto>)  ★ 批量建人员岗位关系
createBatchMemberMetadata(SingleRequest<OrgBatchMetadataDto>) ★ 批量写人员元数据
selectByCodes(SingleRequest<SearchMemberConditionApiDto>)    ★ 按编码查
selectByThirdIds(SingleRequest<SearchMemberConditionApiDto>) ★ 按三方 ID 查
selectByCondition(PageDtoRequest<SearchMemberApiDto>)
selectNaturalMemberByPhoneNumber(SingleRequest<String>)       ★ 按手机号查
fixCtpUserId(SingleRequest<OrgUserFixDto>)                    ★ 修复 ctp userId
disableMember(SingleRequest<String>)                          ★ 停用
disableMemberByThirdIds(SingleRequest<String>)
```

**⇒ 这是「组织数据同步」的主入口（与第三方 HR 系统对接用）。**
**⇒ `selectByThirdIds` 说明平台有「三方 ID」概念。**

---

## 6. `OrgWorkFlowAppService`（37 方法）—— 流程中的人员匹配

```java
selectMemberPostBySelectPeople(SingleRequest<WorkFlowMatchRequestDto>)
selectMemberPostBySelectPeoples(SingleRequest<Map<Long,List<WorkFlowMatchRequestDto>>>)
selectMemberPostBySelectPeoplesReturnFile(...)          ← ★ 结果写文件（大数据量）
selectReturnFileByKey / deleteReturnFileByKey            ← 文件回读/删除
selectListByCondition(WorkFlowConditionMatchRequestDto)
selectListByMetaCondition(...)
isOfUp(SelectPeopleDataWfDto)                            ★ 是否某人的上级
selectOfUp(SelectPeopleDataWfDto)                        ★ 取某人的上级
selectPreParameterKey(...)
```

**⇒ 这是「流程节点选人」的核心：按选人规则匹配人员。**
**⇒ `ReturnFile` 系列说明「选人结果可能很大，走文件而不是响应体」。**

---

## 7. `OrgMetadataCoreAppService`（16 方法）—— 元数据维度查询

```java
selectOrgMetadataColumnListByCondition(...)
selectMetadataColumnList(SearchMetadataColumnDto)
selectPageMetadataColumnList(PageRequest)
selectOrgByUnitMemberMetadata(...)               ★ 按单位/人员元数据查组织
selectMemberByUnitMetadata(...)                  ★ 按单位元数据查人员
selectMemberByUnitMemberMetadata(...)            ★ 按人员元数据查人员
selectMemberMetadataInfo(SearchMemberMetadataDto)
selectOrgMetadataInfo(SearchUnitMetadataDto)
selectOrgMetadataInfos(SearchUnitMetadatasDto)
selectOrgRoleByMemberMetadata(...)
selectOrgIdByMemberIdInInstitution(...)
selectEntityIdByMetadataValue(...)
```

**⇒ 「元数据」在组织域是**可配置的自定义字段**（与 UDC 的 `ext*` 扩展字段同源）。**
**⇒ `selectMemberByUnitMetadata` = 按部门的自定义字段值筛人。**

---

## 8. 接口全清单（54 个，按方法数排序）

| 接口 | 方法数 | 职责 |
|---|---|---|
| `OrgCommonAppService` | 45 | **综合查询（最常用）** |
| `OrgWorkFlowAppService` | 37 | 流程选人匹配 |
| `OrgUnitBaseAppService` | 20 | 单位/部门 CRUD |
| `OrgMemberBaseAppService` | 18 | 人员 CRUD |
| `OrgMetadataCoreAppService` | 16 | 元数据维度查询 |
| `OrgMemberSyncAppService` | 14 | 人员批量同步 |
| `OrgZhongheService` | 14 | 综合服务 |
| `OrgJobBaseAppService` | 14 | 职务 CRUD |
| `OrgLevelBaseAppService` | 14 | 职级 CRUD |
| `OrgPostBaseAppService` | 14 | 岗位 CRUD |
| `OrgMemberCoreAppService` | 13 | 人员核心查询 |
| `OrgMemberPostBaseAppService` | 13 | 人员-岗位关系 |
| `OrgMemberRoleBaseAppService` | 13 | 人员-角色关系 |
| `OrgRoleBaseAppService` | 13 | 角色 CRUD |
| `OrgUnitCoreAppService` | 13 | 单位核心查询 |
| `OrgBusinessBaseAppService` | 11 | 业务组织 |
| `OrgPortalAppService` | 10 | 门户相关 |
| `OrgUnitVerticalBaseAppService` | 10 | 垂直组织（上下级） |
| `OcipUnitAppService` | 8 | **开放接口：单位** |
| `OrgUnitSyncAppService` | 8 | 单位同步 |
| `OrgUnitTeamCoreAppService` | 8 | 组织团队 |
| `OrgJobCoreAppService` | 6 | 职务核心 |
| `OrgLevelCoreAppService` | 6 | 职级核心 |
| `OrgPostCoreAppService` | 6 | 岗位核心 |
| `OrgMemberPostCoreAppService` | 5 | 人员-岗位核心 |
| `OrgSystemTeamCoreAppService` | 5 | 系统团队 |
| `OcipLevelAppService` | 4 | 开放：职级 |
| `OcipMemberAppService` | 4 | 开放：人员 |
| `OcipPostAppService` | 4 | 开放：岗位 |
| `OrgJobSyncAppService` | 4 | 职务同步 |
| `OrgLevelSyncAppService` | 4 | 职级同步 |
| `OrgPostSyncAppService` | 4 | 岗位同步 |
| `OrgTeamSyncAppService` | 4 | 团队同步 |
| `OrgMemberRoleCoreAppService` | 4 | 人员-角色核心 |
| `OrgRoleCoreAppService` | 4 | 角色核心 |
| `OrgSelectPeopleForDeptAppService` | 3 | **选人：按部门** |
| `OrgSelectPeopleForInstAppService` | 2 | **选人：按单位** |
| `OrgSelectPeopleForMemberAppService` | 2 | **选人：按人员** |
| `OrgAppCommonAppService` | 2 | 应用通用 |
| `OrgMobileAppService` | 2 | 移动端 |
| `MultiOrgDepSyncService` | 2 | 多组织部门同步 |
| `MultiOrgMemberSyncService` | 2 | 多组织人员同步 |
| `MultiOrgSyncService` | 2 | 多组织同步 |
| `OrgRoleSyncService` | 2 | 角色同步 |
| `OrgMemberRoleSyncService` | 1 | 人员角色同步 |
| `OrgBusinessCoreAppService` | 1 | 业务组织核心 |
| `OrgAffairAppService` | 1 | 事项关联 |
| `OrgEdocAppService` | 1 | 公文关联 |
| `OrgPlatformAppService` | 1 | 平台 |
| `AuthorizationAppService` | 1 | 授权 |
| `TenantManageAppService` | 1 | 租户管理 |
| `OrgInstitutionExecutiveAppService` | 1 | 单位执行 |
| `OrgUnitVerticalCoreAppService` | 1 | 垂直组织核心 |
| `OrgParameterCoreAppService` | 1 | 组织参数 |
| `OrgWorkFlowUtil` | 12 | 流程工具 |

---

## 9. 开发要点（可直接用）

### 9.1 查人员的正确入口

```
按部门查人     → OrgCommonAppService.selectMemberByOrgId
按部门查人ID   → OrgCommonAppService.selectMemberByOrgId（返回 List<Long>）
部门人数       → OrgCommonAppService.selectMemberCountByOrgId
按岗位查人     → OrgCommonAppService.selectMemberByPostId
按职级查人     → OrgCommonAppService.selectMemberByLevelId
按 ctp userId  → OrgCommonAppService.selectMemberByUserId
单人详情       → OrgCommonAppService.selectMemberInfoById
多维组织       → OrgCommonAppService.selectMemberMultiDimOrgInfo
所在单位       → OrgCommonAppService.selectMemberInstitutionInfoById
此人管的部门   → selectManagerDepartmentByMemberId
此人分管的部门 → selectLeaderDepartmentByMemberId
```

### 9.2 返回值是 `Map`，不是强类型 DTO

```java
selectMemberInfoById(...) : SingleResponse<Map<String,Object>>
```

**⇒ 组织人员的字段是**元数据可配置**的。**
**⇒ 不能假设固定字段名，必须按元数据定义取。**

### 9.3 所有方法都包在 `Request/Response` 里

```java
SingleRequest<T>  → SingleResponse<R>
ListRequest       → ListResponse<R>
PageRequest       → PageResponse<R>
PageDtoRequest<T> → PageResponse<R>
```

**⇒ 这是 Dubbo 契约的统一封装，不是普通 Java 方法调用。**
**⇒ 调用时必须构造 Request 对象，不能直接传原始参数。**

### 9.4 `Json` 变体是给前端用的

```java
selectMemberBySelectPeopleData(SingleRequest<List<SelectPeopleDataDto>>)   ← 内部调用
selectMemberBySelectPeopleDataJson(SingleRequest<String>)                  ← 前端传 JSON 串
```

**⇒ 前端直接调时用 `Json` 版本，避免 DTO 序列化差异。**

### 9.5 大数据量走文件

```java
selectMemberPostBySelectPeoplesReturnFile(...)   ← 结果写文件
selectReturnFileByKey(...)                        ← 读回
deleteReturnFileByKey(...)                        ← 用完删
```

**⇒ 选人结果可能上万条，平台走「文件暂存 + 分次读」避免撑爆响应。**
**⇒ 用完后**必须** `deleteReturnFileByKey` 清理，否则存储泄漏。**

---

## 10. 与其他域的关系

```
organization（组织）
    ↑ 被依赖
    ├─ bpm（流程选人 → OrgWorkFlowAppService）
    ├─ affair（事项的发起人/办理人）
    ├─ file（附件权限 → 敏感字段）
    └─ udc（业务实体的创建人/部门字段）
```

**⇒ 组织域是**基础依赖**，几乎所有业务域都调它。**
