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