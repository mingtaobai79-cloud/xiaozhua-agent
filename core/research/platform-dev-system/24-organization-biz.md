# 组织域实现层（organization-biz 5.3.344，668 类）

> 数据源：`D:/repo/CHIT-extra/organization-biz/5.3.344/organization-biz-5.3.344.jar`（3.2 MB，668 类）
> 等级：`VERIFIED_STATIC_BYTECODE`（类清单 + javap 方法签名）
> ⚠️ **不在官方 102 清单** → 实现层
> ✅ **facade 版本对照**：`organization-facade` 官方 5.3.600，本机 5.3.601（NEWER，`10-org-domain.md` 用的就是这个）

---

## 0. ★★★ 核心结论

**`SelectPeopleAppService` 有 218 个方法 —— 这就是平台「选人」能力的全集。**
**上一轮 `PERSONSELECTOR` 数据类型的基础，就在这里。**

---

## 1. ★ 结构（668 类）

| 包 | 类数 | 是什么 |
|---|---:|---|
| `dto` | **248** | DTO（其中 `selectpeople` 96 = 最大子包） |
| **`domain`** | **207** | 领域实现（`domain.core` 133） |
| **`appservice`** | **122** | 对外服务 |
| `ctp.user` | 34 | 用户相关（personalsetting 18 / authorization 16） |
| `util` / `metadata` / `common` | 32 | |
| `mock` / `cache` / `upgrade` / `spi` / `job` / `config` / `track` / `mgn` | 20 | |

---

## 2. ★★★ 组织核心实体（`domain.core.entity`，22 个）

**这是组织架构的数据模型：**

| 实体 | 中文 | 关键 |
|---|---|---|
| **`OrgUnit`** | **单位/部门** | 树形（有 parent） |
| **`OrgMember`** | **人员** | |
| **`OrgPost`** | **岗位** | |
| **`OrgJob`** | **职务** | |
| **`OrgLevel`** | **层级** | |
| **`OrgRole`** | **角色** | |
| **`OrgMemberPost`** | **人员-岗位关系** | ★ 一个人可多岗 |
| **`OrgMemberRole`** | **人员-角色关系** | |
| **`OrgBusiness`** | **业务线** | ★ 业务归属 |
| **`OrgBusinessMember`** | 业务线人员 | |
| **`OrgUnitVertical`** | **单位纵向关系** | ★ 上下级 |
| **`OrgUnitHorizontal`** | **单位横向关系** | ★ 平级协作 |
| **`OrgUnitRelation`** | 单位关系 | |
| **`OrgPostDimension`** / `OrgPostDimensionRelation` | **岗位维度** | ★ 多维度岗位 |
| `OrgLeaderSecretary` | **领导秘书** | ★ 秘书代理领导 |
| `OrgDepartmentVisitPermission` | 部门访问权限 | |
| `OrgInstitutionVisitPermission` | 机构访问权限 | |
| `OrgOutsidePermission` | 外部权限 | |
| `OrgMemberMetadata` / `OrgUnitMetadata` | **元数据扩展** | ★ 组织可加自定义字段 |
| `OrgMetadataColumn` / `OrgMetaDataColumnSetting` | 元数据列配置 | |
| `OrgMemberBaseMetadata` / `OrgUnitBaseMetadata` | 基础元数据 | |
| `OrgMemberIdCodeResult` | ID 编码结果 | |

**★★★ 五个必须理解的设计：**

**① 岗位 vs 职务 vs 层级 vs 角色（四个概念，不是一回事）**
```
OrgPost    岗位  ← 具体职位（如「财务经理」）
OrgJob     职务  ← 职务序列（如「管理岗」）
OrgLevel   层级  ← 级别（如「M3」）
OrgRole    角色  ← 角色（如「审批人」）
```

**② 一个人可多岗（`OrgMemberPost` 是关系表）**
**⇒ 这就是「主岗/副岗」的实现。**

**③ 单位有纵向 + 横向双关系**
```
OrgUnitVertical    纵向（上下级）
OrgUnitHorizontal  横向（平级协作/虚拟组织）
```
**⇒ 支持矩阵式组织（一个人既在部门 A，也在项目组 B）。**

**④ `OrgLeaderSecretary` —— 领导-秘书关系**
**★ 这是「秘书代领导处理」的基础。**

**⑤ `OrgMemberMetadata` / `OrgUnitMetadata` —— 组织支持自定义字段**
**★ 与 UDC 元数据是两套（组织自己有一套元数据扩展）。**

---

## 3. ★★★ `SelectPeopleAppService`（218 方法）—— 选人能力全集

**这是平台「选人」的核心，按用法归类：**

### 3.1 选人（主入口）

```java
SingleResponse<SelectPeopleEntityDto> selectXxx(...)          // 选单个实体
PageResponse<SelectPeopleMemberDto>   selectMemberBy...(多版)  // ★ 分页选人员
ListResponse<SelectPeopleMemberDto>   searchMember(...)        // 搜索人员
ListResponse<SelectPeopleUnitDto>     selectFirstXxx(...)      // 首屏
ListResponse<SelectPeopleUnitDto>     searchUnit(...)          // 搜索单位
SingleResponse<CtpUserDto>            selectUserById(...)      // 按 ID 取用户
```

### 3.2 ★ 组织树

```java
SingleResponse<SelectPeopleUserDepartmentTreeListDto> getBusinessUnitTree(...)   // ★ 业务单位树
ListResponse<SelectPeopleUserDepartmentTree...>       getXxx(...)
ListResponse<SelectPeopleUnitDto>                     unitTree(...)
void getUnitTreeList(List<...>, ...)                                            // 递归建树
Boolean validateUnitTreePermission(PermissionEnum, ...)                          // ★ 树权限校验
```

### 3.3 ★ 按类型选（10 种被选对象）

```java
PageResponse<SelectPeopleMemberDto>        selectMemberBy...     人员
PageResponse<SelectPeopleUnitListDto>      selectUnit...         单位
PageResponse<SelectPeopleOrgTeamUnitDto>   selectOrgTeam...      单位团队
PageResponse<SelectPeoplePostDto>          selectPost...         ★ 岗位
PageResponse<SelectPeopleJobDto>           selectJob...          ★ 职务
PageResponse<SelectPeopleLevelDto>         selectLevel...        ★ 层级
PageResponse<SelectPeopleTeamDto>          selectTeam...         团队
PageResponse<SelectPeoplePersonalTeamDto>  selectPersonalTeam... ★ 个人组
PageResponse<SelectPeopleBusinessDto>      selectBusiness...     ★ 业务线（3 个重载）
ListResponse<SelectPeopleOutsideUnitDto>   selectOutsideUnit...  外部单位
ListResponse<SelectPeopleLocalUnitDto>     selectLocalUnit...    本单位
```

### 3.4 ★ 权限（`PermissionEnum`）

```java
PermissionEnum getPermission(SelectPeopleXxxDto)               // ★ 取当前用户对该选人场景的权限
Boolean validateUnitTreePermission(PermissionEnum, ...)        // 校验树权限
void processAuthorization(List<String>, List<SelectPeople...>) // ★ 处理授权
```

**★★ `PermissionEnum` —— 选人不是无脑全量，而是按「当前用户能看哪些组织」过滤。**
**⇒ 这就是「部门访问权限」（`OrgDepartmentVisitPermission`）的落点。**

### 3.5 外部单位

```java
ListResponse<SelectPeopleOutsideUnitDto> selectOutsideUnit(...)
ListResponse<SelectPeopleLocalUnitDto>   selectLocalUnit(...)
void filterAppointRootIds(List<Long>, Boolean)
```

**★ `filterAppointRootIds` —— 可以「指定根节点」限定选人范围。**

---

## 4. ★★ `OcipSelectPeopleAppService`（22 方法）—— 对外选人（泛化）

```java
SingleResponse<List<OcipUnitTreeDto>> selectXxx(...)       // 多种树查询
List<OcipUnitTreeDto> selectAllUnitList(String)
List<OcipUnitTreeDto> loadAllListByRootId(String, ...)     // ★ 按根节点全量
List<OcipUnitTreeDto> handleOcipReturnData(List, ...)      // 数据适配
void fillFullNameForDept(List, ...)                        // ★ 填全路径名
String getFullName(String, Map, ...)
List<OcipUnitTreeDto> getDepartments(String)
List<OcipUnitTreeDto> getLocalDepartments(String)
```

**★★ OCIP（开放接口平台）也有一套选人 —— 给外部系统调用的。**
**⇒ 与内部 `SelectPeopleAppService` 分离，说明**内外两套**。**

**★ `fillFullNameForDept` / `getFullName` —— 组织全路径名（如「集团/财务部/会计科」）是计算出来的。**

---

## 5. ★★ 组织核心服务（`domain.core.service`，40 个）

| 服务 | 方法数 | 管什么 |
|---|---:|---|
| **`OrgMemberService`** | **117** | **人员** |
| **`OrgUnitService`** | **109** | **单位/部门** |
| `OrgBaseService` | — | 基类 |
| `OrgHelperService` | — | 辅助 |
| `OrgJobService` | — | 职务 |
| `OrgLevelService` | — | 层级 |
| `OrgPostService` | — | 岗位 |
| `OrgPostDimensionService` / `...RelationService` | — | 岗位维度 |
| `OrgRoleService` | — | 角色 |
| `OrgMemberPostService` | — | 人员岗位 |
| `OrgMemberRoleService` | — | 人员角色 |
| `OrgMemberMetadataService` | — | 人员元数据 |
| `OrgUnitMetadataService` | — | 单位元数据 |
| `OrgUnitVerticalService` | — | 纵向关系 |
| `OrgUnitHorizontalService` | — | 横向关系 |
| `OrgMetaDataColumnService` / `...SettingService` | — | 元数据列 |
| `OrgMetadataCommonService` | — | 元数据公共 |
| `OrgBusinessService` / `...MemberService` / `...UnitService` | — | 业务线 |
| `OrgLeaderSecretaryService` | — | 领导秘书 |
| `OrgOutsidePermissionService` | — | 外部权限 |
| `OrgDepartmentVisitPermissionService` | — | 部门访问权限 |
| `OrgInstitutionVisitPermissionService` | — | 机构访问权限 |
| `CtpUserDubboCommonService` | — | **★ 用户 Dubbo 通用服务** |
| `cache.OrgMemberCacheService` | — | 人员缓存 |
| `cache.OrgUnitCacheService` | — | 单位缓存 |
| `sync.*`（5 个） | — | 同步 |

### 5.1 `OrgMemberService`（117 方法）关键方法

```java
Long    create(OrgMemberRequestDto)
Integer update(OrgMemberRequestDto)
void    createCheck(...) / validate(...)                    // 校验
OrgMemberResponseDto selectDtoById(Long, Boolean, ...)      // ★ 5 个重载（字段裁剪）
OrgMemberDto selectMemberById(Long, Boolean)
OrgMemberDto selectMemberFieldsById(Long, ...)
OrgMember   selectById(Long) / selectByIdFromCache(Long)    // ★ 缓存版本
List<OrgUnitResponseDto> selectInstitutionByMemberId(Long, ...)  // ★ 人员所属机构
OrgMemberPost findBestMatch(List<...>)                      // ★ 最佳匹配岗位
PageData<OrgMemberResponseDto> selectMemberBy...(...)       // 分页查
List<OrgMemberResponseDto> selectListMember(Map, ...)
Map<Long, OrgMember> selectMapByIds(List<Long>)             // ★ 批量（防 N+1）
void asyncLoadMemberCache(List<OrgMember>)                  // ★ 异步加载缓存
int  updateSort(...) / updateTopSortId(...)                 // 排序
```

**★★ 三个设计点：**
1. **`selectDtoById` 有 5 个重载**（`Boolean` 参数控制是否带某些数据/走缓存）—— 说明**性能敏感**
2. **`selectByIdFromCache`** —— 人员查询有缓存路径
3. **`selectMapByIds`** —— 批量查防 N+1

### 5.2 `OrgUnitService`（109 方法）关键方法

```java
Long init()                                        ★ 初始化
Long create(OrgUnitRequestDto)
Integer update(OrgUnitRequestDto)
Boolean valideLocalOrg(OrgUnit)
void clearLocalCache(Long, Set<String>, Boolean)   ★ 清缓存
void validateVerticalBusinessId(Long, List<...>)
void updateUnitVerticalRelation(OrgUnit, ...)      ★ 更新纵向关系
String getParentPath(Long)                         ★ 父路径
```

---

## 6. ★★ 组织同步（`appservice.api.sync`，12 个）

**这是「从外部系统同步组织架构」的入口：**

```
MultiOrgSyncServiceImpl          ★ 多组织总同步
MultiOrgDepSyncServiceImpl       ★ 部门同步
MultiOrgMemberSyncServiceImpl    ★ 人员同步（多个）
OrgJobSyncAppServiceImpl         职务同步
OrgLevelSyncAppServiceImpl       层级同步
OrgMemberSyncAppServiceImpl      人员同步
OrgPostSyncAppServiceImpl        岗位同步
OrgRoleSyncServiceImpl           角色同步
OrgTeamSyncAppServiceImpl        团队同步
OrgUnitSyncAppServiceImpl        单位同步
OrgMemberRoleSyncServiceImpl     人员角色同步
SyncModeEnum                     ★ 同步模式
MetadataUtil                     元数据工具
```

**★ 12 个 Sync 服务，覆盖 9 类组织对象。**
**⇒ 与连接器的「中间表模式」配合使用（`MiddleTableAppServiceImpl` 那套）。**

---

## 7. ★★ 组织 API 层（`appservice.api`，50 个）—— 按调用方分包

**这是最有价值的部分：按「谁在调」分包。**

### 7.1 `api.core.*`（16 个）—— 按对象
```
OrgUnitCoreAppServiceImpl          单位
OrgMemberCoreAppServiceImpl        人员
OrgMemberPostCoreAppServiceImpl    人员岗位
OrgMemberRoleCoreAppServiceImpl    人员角色
OrgPostCoreAppServiceImpl          岗位
OrgJobCoreAppServiceImpl           职务
OrgLevelCoreAppServiceImpl         层级
OrgRoleCoreAppServiceImpl          角色
OrgBusinessCoreAppServiceImpl      业务线
OrgUnitTeamCoreAppServiceImpl      单位团队
OrgUnitVerticalCoreAppServiceImpl  纵向关系
OrgSystemTeamCoreAppServiceImpl    系统团队
OrgMetadataCoreAppServiceImpl      元数据
OrgParameterCoreAppServiceImpl     参数
```

### 7.2 `api.app.*`（16 个）—— 按应用
```
OrgWorkFlowAppServiceImpl          ★ 流程用（最重要）
OrganizationMatchMemberAppServiceImpl  ★ 流程匹配人员
WorkFlowAppService / WorkFlowMatchService
condition.ConditionAppService       ★ 条件
condition.ConditionMetaAppService
formula.FormulaAppServiceImpl      ★ 公式
OrgAffairAppServiceImpl            事项
OrgAppCommonAppServiceImpl         应用公共
OrgEdocAppServiceImpl              公文
OrgMobileAppServiceImpl            移动
OrgPersonalInfoAppService          个人信息
OrgPlatformAppServiceImpl          平台
OrgPortalAppServiceImpl            门户
OrgToUserAppService                ★ 组织 → 用户
OrgUserResourceAppService          用户资源
```

**★★★ `api.app.workflow` 是 BPM 与组织域的桥梁：**
```
WorkFlowAppService                 流程用组织服务
WorkFlowMatchService               ★ 流程匹配人员
OrganizationMatchMemberAppServiceImpl  ★ 组织匹配人员
condition.ConditionAppService      流程条件
formula.FormulaAppServiceImpl      流程公式
OrgWorkFlowAppServiceImpl          流程组织服务主体
```

**⇒ 上一轮 BPM 的 `usedparam` 检测「流程用了哪些组织」（`bo/org/` 11 类），就是扫这些。**

### 7.3 `api.app.third.*`（3 个）—— 第三方定制
```
OrgChangJiangAppService            长江（客户定制）
OrgZhongheServiceImpl              中和（客户定制）
```

**⚠️ 这是客户定制代码混在标品 jar 里。**

### 7.4 `api.sync` / `api.tenant` / `api.common` / `api.enums`
```
TenantManageAppServiceImpl         ★ 租户管理
OrgCommonAppServiceImpl            公共
SystemVariableKeyEnum              ★ 系统变量 key
```

---

## 8. ★★ 权限体系（`ctp.user.authorization`，16 个 + `appservice` 8 个）

```
CtpAuthorizationAppService           ★ 授权
CtpAuthorizationRuleAppService       授权规则
CtpOrgAdminAppService                ★ 组织管理员
CtpOrgApplicationAppService          组织应用
CtpOrgPermissionApprovalAppService   ★ 权限审批
CtpUserPermissionCacheClearAppService 权限缓存清理
OrgMemberMessageAppService           人员消息
```

**★★ 三层权限：**
```
CtpAuthorization        授权（谁能操作什么）
CtpOrgAdmin             组织管理员（谁能管哪个组织）
CtpOrgPermissionApproval 权限审批（申请-审批流）
```

**★ `CtpUserPermissionCacheClearAppService` —— 权限有缓存，需要清理接口。**

---

## 9. ★ 其他子域

| 子域 | 类数 | 说明 |
|---|---|---|
| **`addressbook`** | 12 | **通讯录**（含字段/权限/设置四件套） |
| **`external`** | 18 | **外部单位/人员/合作伙伴** |
| **`team`** | 21+7 | **团队**（个人团队/单位团队/组织团队） |
| **`natural`** | — | **自然人员**（`OrgNaturalMemberAppService`） |
| **`ocip`** | 6 | 开放接口 |
| **`selectpeople`** | 7+96 dto | 选人 |
| **`transfer`** | — | 组织迁移 |
| **`temp`** | — | 临时（初始化用） |
| **`orgscope`** | — | 组织范围 |
| **`online`** | — | 在线人员 |
| **`init`** | 8 | **初始化**（DomainId / Tenant / Sandbox / License） |
| **`spi`** | 2 | **SPI 扩展点** |
| **`job`** | 2 | 定时任务 |
| **`metadata`** | 10 | 元数据 |

**★ `external`（18 类）—— 外部单位是独立体系（外部人员不是内部人员）。**
**★ `natural`（自然人员）—— 与「组织人员」区分，可能是「自然人」概念。**

---

## 10. ★★★ 回答上一轮的疑问：`PERSONSELECTOR` 的组织基础

**上一轮我写：`PERSONSELECTOR` 支持度是半成品（不能显示名、不能关联查询、不能携带）。**

**现在找到了它的组织侧基础：**
```
SelectPeopleAppService（218 方法）  ← 选人能力齐全（树/搜索/权限/多类型）
OcipSelectPeopleAppService（22）    ← 对外选人也齐
```

**⇒ 组织侧的选人能力是**完备的**。**
**⇒ 所以 `PERSONSELECTOR` 的限制**不在组织侧**，而在**UDC 侧**（元数据/关联配置还没接）。**

**⚠️ 但我仍未验证：UDC 的 `PERSONSELECTOR` 到底调哪个组织接口取人名。**
**⇒ 需要读 `udc-biz` 的数据类型解析器，本轮未做。**

---

## 11. 未覆盖

| 项 | 说明 |
|---|---|
| `SelectPeopleAppService` 218 方法中 184 个 | 只列了前 34 |
| `OrgMemberService` 117 方法中 83 个 | 只列了前 34 |
| `OrgUnitService` 109 方法中剩余 | 只列了前 13 |
| `dto.selectpeople` 96 个 DTO 的字段 | 未 dump |
| `PermissionEnum` 的取值 | 未读 |
| `SyncModeEnum` 的取值 | 未读 |
| `external` 18 类的结构 | 未看 |
| 组织元数据（`OrgMemberMetadata`）与 UDC 元数据的关系 | **未验证** |
| 各方法方法体 | 全部未反编译 |