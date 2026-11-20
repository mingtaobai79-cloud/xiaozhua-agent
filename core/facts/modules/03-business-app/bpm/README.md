# 流程（bpm）

## 一句话

`com.seeyon.bpm` 域的**可调用接口面**：5 个构件、3,415 个类、39 个 facade 接口 / 278 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `bpm-biz` | biz | 2,728 |
| `bpm-facade` | facade | 533 |
| `bpm-web` | web | 65 |
| `bpm-org` | 其他 | 51 |
| `bpm-org-facade` | facade | 38 |
| **合计** | | **3,415** |

## 二、分层规律（写代码前必读）

`com.seeyon.bpm` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

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

## facade 层：39 个接口 / 278 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.bpm.api.common` | 26 | 207 |
| `com.seeyon.bpm.api.ext.activity` | 4 | 29 |
| `com.seeyon.bpm.api.udc` | 5 | 37 |
| `com.seeyon.bpm.api.upgrade` | 1 | 1 |
| `com.seeyon.bpm.appservice.autogenerate` | 1 | 1 |
| `com.seeyon.bpm.appservice.autogenerate.dispatcher` | 1 | 1 |
| `com.seeyon.bpm.simulation.api` | 1 | 2 |
| **合计** | **39** | **278** |

### `com.seeyon.bpm.api.common`

#### BpmActionAppService

`com.seeyon.bpm.api.common.BpmActionAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `activitySubmit` | `SingleRequest<BpmActivitySubmitDto> arg0` | `SingleResponse<BpmSubmitResultDto>` | 节点级提交（按 activitySubmitDto 精确到节点） |
| `activityStepBack` | `SingleRequest<BpmActivityTakeBackDto> arg0` | `SingleResponse<Void>` | 节点级回退 |

#### BpmActivityAppService

`com.seeyon.bpm.api.common.BpmActivityAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectAllByCaseId` | `SingleRequest<Long> arg0` | `ListResponse<BpmActivityRunDto>` | 查某实例的全部节点运行记录 |
| `selectBpmCaseActivityByCaseId` | `SingleRequest<BpmCaseActivitySearchDto> arg0` | `ListResponse<BpmCaseActivityDto>` | 查某实例的节点（含节点状态） |
| `create` | `SingleRequest<BpmActivityRunDto> arg0` | `SingleResponse<Integer>` | 新建ActivityRun |
| `createBatch` | `SingleRequest<List<BpmActivityRunDto>> arg0` | `SingleResponse<Integer>` | 批量新建（SingleRequest） |

#### BpmApiFormPermissionAppService

`com.seeyon.bpm.api.common.BpmApiFormPermissionAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<BpmFormPermissionDto> arg0` | `SingleResponse<Long>` | 新建权限 |
| `update` | `SingleRequest<BpmFormPermissionDto> arg0` | `SingleResponse<Void>` | 修改权限 |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Void>` | 删除Void按 id |
| `selectByTemplateId` | `SingleRequest<Long> arg0` | `ListResponse<BpmFormPermissionDto>` | ★查模板的表单权限（哪些字段可写/只读/隐藏） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<BpmFormPermissionDto>` | 查询权限按 id |
| `selectPermissionIncludeContentById` | `SingleRequest<Long> arg0` | `SingleResponse<BpmFormPermissionIncludeContentDto>` | 查表单权限（含字段内容明细） |
| `selectByApplicationName` | `SingleRequest<String> arg0` | `ListResponse<BpmFormPermissionDto>` | 查询权限按应用名称 |
| `selectThirdPermissionByTemplateId` | `SingleRequest<Long> arg0` | `SingleResponse<ThirdFormPermissionDto>` | 取第三方形式（第三方应用）的表单权限 |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<BpmFormPermissionDto>` | 查询权限按 ids |
| `selectFormDesensitizedList` | `SingleRequest<BpmFormDesensitizedQueryDto> arg0` | `ListResponse<BpmFormDesensitizedDto>` | 查表单脱敏字段列表 |
| `selectThirdFormPermissionById` | `SingleRequest<Long> arg0` | `SingleResponse<ThirdFormPermissionDto>` | 查询第三方表单权限按 id |
| `selectFormPermissionList` | `SingleRequest<BpmFormPermissionSearchRequestDto> arg0` | `ListResponse<BpmFormPermissionDto>` | 列表查询表单权限 |
| `deleteFormPermisionForceEntityDraft` | `SingleRequest<BpmFormPermissionDeleteRequestDto> arg0` | `SingleResponse<Void>` | 删除表单实体草稿PermisionForce |
| `selectFormPermissionIncludeContentList` | `SingleRequest<List<BpmFormPermissionSearchRequestDto>> arg0` | `ListResponse<BpmFormPermissionIncludeContentDto>` | 列表查询表单权限内容Include |
| `createOrUpdateBatch` | `SingleRequest<List<BpmFormPermissionDto>> arg0` | `SingleResponse<Void>` | 批量保存表单权限 |
| `createBatchOrUpdateContent` | `SingleRequest<List<BpmFormPermissionContentDto>> arg0` | `SingleResponse<Void>` | 批量新建内容OrUpdate |
| `selectContentListByPermissionIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<BpmFormPermissionContentSimpleDto>` | 列表查询内容按权限 |
| `checkFormPermissionBatch` | `SingleRequest<List<BpmFormPermissionDto>> arg0` | `ListResponse<CheckFormPermissionRespDto>` | 批量校验表单权限合法性 |

#### BpmApiNodePermissionAppService

`com.seeyon.bpm.api.common.BpmApiNodePermissionAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `bpmNodePermissionHandel` | `SingleRequest<BpmNodePermissionInitDto> arg0` | `SingleResponse<Void>` | 节点权限初始化处理 |
| `selectNodePermissionById` | `SingleRequest<BpmNodePermissionQueryDto> arg0` | `SingleResponse<BpmNodePermissionDetailDto>` | 查询权限按 id |
| `selectNodePermissionListByIds` | `SingleRequest<BpmNodePermissionQueryDto> arg0` | `ListResponse<BpmNodePermissionDetailDto>` | ★批量查节点权限 |
| `savePermission` | `SingleRequest<BpmNodePermissionAddDto> arg0` | `SingleResponse<Long>` | 保存节点权限，返回 id |
| `savePermissionList` | `SingleRequest<List<BpmNodePermissionAddDto>> arg0` | `ListResponse<Long>` | 批量保存节点权限 |
| `queryPermissionList` | `SingleRequest<BpmNodePermissionSearchRequestDto> arg0` | `ListResponse<BpmNodePermissionSearchResponseDto>` | 列表查询权限 |
| `configNodePermissionBind` | `SingleRequest<List<BpmNodePermissionBindDto>> arg0` | `SingleResponse<Void>` | 配置节点权限绑定（权限模板→节点） |
| `selectNodePermissionDetailListByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<BpmNodePermissionDetailDto>` | 列表查询权限Detail按 ids |
| `selectNodePermissionListByConditions` | `SingleRequest<BpmNodePermissionQueryConditionDto> arg0` | `ListResponse<BpmNodePermissionFullFieldDto>` | 列表查询权限按条件 |
| `createOrUpdateNodePermissionBatch` | `SingleRequest<List<BpmNodePermissionFullFieldDto>> arg0` | `SingleResponse<Void>` | 批量新建或更新节点权限 |
| `getMaxOrderNumber` | `SingleRequest<BpmNodePermissionMaxOrderNumQueryDto> arg0` | `SingleResponse<Integer>` | 获取编号MaxOrder |

#### BpmApiPermissionAppService

`com.seeyon.bpm.api.common.BpmApiPermissionAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `checkApplicationPermission` | `BpmAppInfoDto arg0` | `boolean` | 判断当前用户对应用有无流程权限 |
| `getCurrentOrgHierarchicalAppGuid` | `—` | `List<Long>` | 取当前组织层级下可用的应用 guid |
| `isProcessFragmentEnabled` | `—` | `boolean` | 流程片段功能是否开启 |

#### BpmApiProcessAppService

`com.seeyon.bpm.api.common.BpmApiProcessAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectDiagramDetailByTemplateCodeAndVersion` | `SingleRequest<BpmDiagramDetailRequestDto> arg0` | `ListResponse<BpmDiagramDetailInfoDto>` | 查询DiagramDetail按模板编码版本 |

#### BpmAppOrgReplaceService

`com.seeyon.bpm.api.common.BpmAppOrgReplaceService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `replace` | `SingleRequest<BpmAppOrgReplaceDto> arg0` | `SingleResponse<Void>` | 组织变更后替换流程中的组织/人员引用（架构调整时用） |

#### BpmAppService

`com.seeyon.bpm.api.common.BpmAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `send` | `SingleRequest<BpmSendDto> arg0` | `SingleResponse<BpmSendResultDto>` | ★发起流程（运行态入口，一次调用生成 case+witems） |
| `saveDraft` | `SingleRequest<BpmSaveDraftDto> arg0` | `SingleResponse<BpmSaveDraftResultDto>` | 保存待发（不产生 case，只存草稿） |
| `submit` | `SingleRequest<BpmSubmitDto> arg0` | `SingleResponse<BpmSubmitResultDto>` | ★提交当前节点（办理人同意/流转），入参含 caseId+activityId+意见 |
| `stepBack` | `SingleRequest<BpmStepBackDto> arg0` | `SingleResponse<CommonResultDto>` | 回退到上一节点（办理人操作） |
| `repeal` | `SingleRequest<BpmRepealDto> arg0` | `SingleResponse<CommonResultDto>` | 撤销（发起人收回已发出但未办理的流程） |
| `stop` | `SingleRequest<BpmStopDto> arg0` | `SingleResponse<CommonResultDto>` | 终止流程（不可再流转） |
| `takeBack` | `SingleRequest<BpmTakeBackDto> arg0` | `SingleResponse<CommonResultDto>` | 取回（办理人把自己已提交的节点收回） |
| `replace` | `SingleRequest<BpmReplaceDto> arg0` | `SingleResponse<CommonResultDto>` | 换人（把某节点的办理人换掉） |
| `consult` | `SingleRequest<BpmConsultDto> arg0` | `SingleResponse<CommonResultDto>` | 加签（临时加一个会签人） |
| `hasten` | `SingleRequest<BpmHastenDto> arg0` | `ListResponse<BpmHastenResponseDto>` | 催办（给当前办理人发催办） |
| `multipleReplace` | `SingleRequest<BpmMultipleReplaceDto> arg0` | `SingleResponse<CommonResultDto>` | 批量换人 |
| `pause` | `SingleRequest<BpmPauseDto> arg0` | `ListResponse<BpmPauseResponseDto>` | 暂停流程（挂起） |
| `cancelPause` | `SingleRequest<BpmPauseDto> arg0` | `ListResponse<BpmPauseResponseDto>` | 恢复暂停 |
| `superviseRelive` | `SingleRequest<BpmReliveDto> arg0` | `SingleResponse<CommonResultDto>` | 督办复活（把已终止的流程救活） |
| `superviseReliveFull` | `SingleRequest<BpmReliveFullDto> arg0` | `SingleResponse<CommonResultDto>` | 督办复活（全量重算节点） |
| `inform` | `SingleRequest<BpmInformDto> arg0` | `SingleResponse<CommonResultDto>` | 知会（不参与流转，只通知） |
| `addExecuteMember` | `SingleRequest<BpmAddExecuteUserDto> arg0` | `ListResponse<BpmItemInfoDto>` | 增加执行人（某节点追加办理人） |
| `cancelItems` | `SingleRequest<BpmCancelItemDto> arg0` | `SingleResponse<CommonResultDto>` | 取消待办项 |
| `batchDeal` | `SingleRequest<BpmBatchReqDto> arg0` | `ListResponse<BpmBatchResponseDto>` | 批量处理（多条待办一次提交） |
| `selectFullCaseInfo` | `SingleRequest<BpmCaseFullInfoSearch> arg0` | `SingleResponse<BpmCaseFullInfo>` | 查流程实例全量信息（含模板、节点、待办、表单） |
| `counterSignNode` | `SingleRequest<SimpleChangeProcessRequestDto> arg0` | `SingleResponse<ChangeNodeResponseDto>` | 会签节点（运行中把节点改成会签） |
| `addNode` | `SingleRequest<SimpleChangeProcessRequestDto> arg0` | `SingleResponse<ChangeNodeResponseDto>` | 运行中动态加节点 |
| `monitorNodeRun` | `SingleRequest<BpmMonitorRunDto> arg0` | `SingleResponse<BpmMonitorRunResultDto>` | 监控节点运行（看当前卡在哪个节点） |
| `check` | `SingleRequest<SecurityCheckDto> arg0` | `SingleResponse<Boolean>` | 流程操作安全检查（权限/数据范围） |
| `deleteDraft` | `SingleRequest<Long> arg0` | `SingleResponse<Void>` | 删除待发草稿（按草稿 id） |
| `deleteDraftAffair` | `SingleRequest<DeleteDraftReqDto> arg0` | `SingleResponse<Void>` | 删除待发草稿（连带删事项） |

#### BpmApplicationOperateLogAppService

`com.seeyon.bpm.api.common.BpmApplicationOperateLogAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `saveApplicationOperateLog` | `SingleRequest<BpmApplicationOperateLogInfoDto> arg0` | `SingleResponse<Void>` | 保存应用日志Operate |
| `selectNewestLogInfo` | `SingleRequest<AppOperateLogQueryDto> arg0` | `SingleResponse<BpmApplicationOperateLogInfoDto>` | 查询日志Newest |
| `updateAppLogs` | `SingleRequest<List<BpmApplicationOperateLogInfoDto>> arg0` | `SingleResponse<Void>` | 修改应用Logs |

#### BpmAutoApprovalAppService

`com.seeyon.bpm.api.common.BpmAutoApprovalAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `designerCreate` | `SingleRequest<BpmAutoApprovalCreateDto> arg0` | `SingleResponse<Long>` | 新建自动审批规则（设计态） |
| `designerUpdate` | `SingleRequest<BpmAutoApprovalUpdateDto> arg0` | `SingleResponse<Boolean>` | 改自动审批规则 |
| `designerDelete` | `SingleRequest<BpmAutoApprovalDeleteDto> arg0` | `SingleResponse<Boolean>` | 删自动审批规则 |
| `designerSelect` | `PageDtoRequest<BpmAutoApprovalSelectDto> arg0` | `PageResponse<BpmAutoApprovalDto>` | 查自动审批规则（分页） |

#### BpmCaseAppService

`com.seeyon.bpm.api.common.BpmCaseAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectCaseById` | `SingleRequest<Long> arg0` | `SingleResponse<BpmCaseDto>` | 按 caseId 查流程实例 |
| `selectMainCaseBySubCaseId` | `SingleRequest<Long> arg0` | `SingleResponse<Long>` | 由子流程 caseId 找主流程 caseId（子流程回查主流程） |
| `deleteCaseByIds` | `SingleRequest<BpmDeleteCaseDto> arg0` | `SingleResponse<String>` | 批量删除流程实例 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<BpmCaseDto>` | 按主键查流程实例（同 selectCaseById） |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<BpmCaseDto>` | 按主键批量查流程实例 |
| `selectBpmCaseByFormRecordId` | `SingleRequest<BpmCaseInfoSearchDto> arg0` | `SingleResponse<BpmCaseDto>` | ★按表单记录 id 反查流程实例（生单后回查流程） |
| `selectByPageCondition` | `PageRequest arg0` | `PageResponse<BpmCaseDto>` | 查询流程实例按页面条件 |
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<BpmCaseDto>` | 级联查询流程实例按 id |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<BpmCaseDto>` | 级联查询流程实例按 ids |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<BpmCaseDto>` | 查询Proxy |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<BpmCaseDto>` | 查询ProxyJoin |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<BpmCaseDto>` | 分页查询流程实例按条件 |
| `refreshCaseTitleById` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 刷新流程标题（表单标题变了后同步） |
| `selectCascadeByConditions` | `SingleRequest<QueryConditionDto> arg0` | `SingleResponse<BpmCaseDto>` | 级联查询条件按条件 |
| `selectCascadeListByConditions` | `SingleRequest<QueryConditionDto> arg0` | `ListResponse<BpmCaseDto>` | 级联列表查询条件按条件 |
| `getCascadeDefaultValue` | `SingleRequest<Void> arg0` | `SingleResponse<BpmCaseDto>` | 级联获取DefaultValue |
| `selectCaseAttachmentList` | `SingleRequest<Long> arg0` | `ListResponse<String>` | 查流程实例的附件列表 |
| `create` | `SingleRequest<BpmCaseDto> arg0` | `SingleResponse<Integer>` | 新建流程实例 |
| `createBatch` | `SingleRequest<List<BpmCaseDto>> arg0` | `SingleResponse<Integer>` | 批量新建（SingleRequest） |
| `selectByIdDisplayName` | `SingleRequest<Long> arg0` | `SingleResponse<BpmCaseDto>` | 按 id 查实例并带显示名（第二个参数指定要翻译的字段） |
| `selectByIdsDisplayName` | `SingleRequest<List<Long>> arg0` | `ListResponse<BpmCaseDto>` | 批量同上 |
| `updateCase` | `SingleRequest<BpmCaseDto> arg0` | `SingleResponse<Void>` | 更新流程实例（内部维护用） |
| `selectExpression` | `SingleRequest<Long> arg0` | `SingleResponse<BpmExpressionDto>` | 查流程实例的表单表达式（运行态取值） |

#### BpmCaseLogAppService

`com.seeyon.bpm.api.common.BpmCaseLogAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectByCaseId` | `SingleRequest<Long> arg0` | `ListResponse<BpmCaseLogDto>` | 查询流程实例日志按流程实例 |
| `selectByDto` | `SingleRequest<BpmCaseLogSelectDto> arg0` | `ListResponse<BpmCaseLogDto>` | 查询流程实例日志按Dto |

#### BpmCoMiAppService

`com.seeyon.bpm.api.common.BpmCoMiAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getDetailInfo` | `SingleRequest<Long> arg0` | `SingleResponse<CoMiDetailInfoDto>` | 获取Detail |

#### BpmDeployAppService

`com.seeyon.bpm.api.common.BpmDeployAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `upgradeBpmTemplateVersion` | `SingleRequest<String> arg0` | `SingleResponse<BpmExportInitDataDto>` | 升级模板版本 |
| `deployBpmTemplatesIndependent` | `SingleRequest<String> arg0` | `SingleResponse<BpmExportInitDataDto>` | 独立部署流程模板（应用初始化） |
| `afterFormAppDataInit` | `SingleRequest<BpmInitParamDto> arg0` | `SingleResponse<Void>` | 表单应用数据初始化后置处理 |
| `upgradeCommon` | `SingleRequest<UpgradeInfoDto> arg0` | `SingleResponse<String>` | 通用升级处理（版本迁移） |
| `autoDeployStartAndAuth` | `SingleRequest<BpmAppInfoDto> arg0` | `SingleResponse<String>` | 自动部署+启用+授权（一键） |
| `usedFrames` | `SingleRequest<BpmAppInfoDto> arg0` | `ListResponse<String>` | 取使用的框架 |

#### BpmDetailAppService

`com.seeyon.bpm.api.common.BpmDetailAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectDetail` | `SingleRequest<BpmEdocSummaryDetailParamDto> arg0` | `SingleResponse<BpmEdocDetailResponseDto>` | 查询Detail |

#### BpmNodeAppService

`com.seeyon.bpm.api.common.BpmNodeAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<BpmNodeDto>` | 分页查询Node按条件 |
| `selectByTemplateAndActivityType` | `SingleRequest<BpmNodeSearchDto> arg0` | `ListResponse<BpmNodeDto>` | 按模板+节点类型查节点 |
| `selectRunningProcessPreNode` | `SingleRequest<BpmPreNodeSearchDto> arg0` | `ListResponse<BpmNodeSimpleDto>` | 查运行中流程的前置节点 |
| `selectNodePolicy` | `SingleRequest<NodePolicySearchDto> arg0` | `ListResponse<NodeProperties>` | 查节点策略配置 |

#### BpmNodePermissionOperationAppService

`com.seeyon.bpm.api.common.BpmNodePermissionOperationAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getNodePermissionOperation` | `SingleRequest<BpmNodePermissionOperationRequestDto> arg0` | `SingleResponse<BpmNodePermissionFilterResponseDto>` | 获取权限Operation |
| `selectOperationSimpleByPermissionIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<BpmNodePermissionOperationSimpleDto>` | 查询简单Operation按权限 |

#### BpmNormalAppMultiVersionAppService

`com.seeyon.bpm.api.common.BpmNormalAppMultiVersionAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectCurrentHighestVersionBatch` | `SingleRequest<CurrentHighestVersionRequestDto> arg0` | `ListResponse<CurrentHighestVersionResponseDto>` | 批量查询当前版本Highest |
| `updateNormalApplicationToSpecifiedInstitution` | `SingleRequest<BpmUpdateApplicationToSpecifiedInstitutionDto> arg0` | `SingleResponse<Void>` | 修改应用机构NormalToSpecified |

#### BpmOpinionAppService

`com.seeyon.bpm.api.common.BpmOpinionAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectOpinionGroupByActivityNodeWithObjectId` | `PageDtoRequest<BpmOpinionRequestDto> arg0` | `ListResponse<BpmOpinionOpenApiNodeResponseDto>` | ★按对象 id 取各节点意见（流程详情页用） |
| `createBatch` | `SingleRequest<List<BpmInputOpinionDto>> arg0` | `SingleResponse<Integer>` | 批量写意见 |
| `create` | `SingleRequest<BpmOpinionDataDto> arg0` | `SingleResponse<Integer>` | 写一条意见（表单批注） |
| `createBatchOpinion` | `SingleRequest<List<BpmOpinionDataDto>> arg0` | `SingleResponse<Integer>` | 批量新建意见 |
| `deleteOpinion` | `SingleRequest<BpmDeleteOpinionDto> arg0` | `SingleResponse<Integer>` | 删意见 |
| `updateOpinion` | `SingleRequest<BpmOpinionUpdateDto> arg0` | `SingleResponse<Void>` | 改意见 |
| `adminDeleteOpinion` | `SingleRequest<Long> arg0` | `SingleResponse<Void>` | 管理员删意见 |

#### BpmProcessLogAppService

`com.seeyon.bpm.api.common.BpmProcessLogAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<BpmProcessLogDto> arg0` | `SingleResponse<Long>` | 新建流程日志 |
| `createBatch` | `SingleRequest<List<BpmProcessLogDto>> arg0` | `SingleResponse<Integer>` | 批量新建（SingleRequest） |
| `selectLogList` | `SingleRequest<Long> arg0` | `ListResponse<BpmProcessLogDto>` | 查某实例的流程日志 |
| `createBatchProcessLog` | `SingleRequest<List<BpmProcessLogDto>> arg0` | `SingleResponse<Integer>` | 批量新建流程日志 |
| `selectOriginalI18nLogList` | `SingleRequest<Long> arg0` | `ListResponse<BpmProcessLogDto>` | 查日志 i18n 原文 |
| `selectLogOriginalListByCaseIds` | `SingleRequest<SearchProcessLogInfoDto> arg0` | `ListResponse<BpmProcessLogDto>` | 批量查日志原文（未 i18n 转换） |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<BpmProcessLogDto>` | 分页查询流程日志按条件 |

#### BpmProcessTrackAppService

`com.seeyon.bpm.api.common.BpmProcessTrackAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectProcessTrackList` | `SingleRequest<BpmProcessTrackReqDto> arg0` | `PageResponse<BpmProcessTrackResDto>` | 列表查询流程Track |
| `countAttentionForBadge` | `SingleRequest<BpmProcessTrackReqDto> arg0` | `SingleResponse<Integer>` | 统计AttentionForBadge |

#### BpmSuperviseAppService

`com.seeyon.bpm.api.common.BpmSuperviseAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `search` | `ListRequest arg0` | `ListResponse<BpmVipSuperviseRunDto>` | 查督办列表 |
| `cancelFocus` | `SingleRequest<SuperviseCancelFocusDto> arg0` | `SingleResponse<Void>` | 取消关注 |
| `skip` | `SingleRequest<BpmSkipDto> arg0` | `SingleResponse<CommonResultDto>` | 跳过节点（督办特权） |

#### BpmTemplateAppService

`com.seeyon.bpm.api.common.BpmTemplateAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createOrUpdate` | `SingleRequest<BpmTemplateDto> arg0` | `SingleResponse<Long>` | 新建或保存流程模板（设计态），返回模板 id |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Void>` | 删除Void按 id |
| `updateCategoryByApplicationId` | `SingleRequest<BpmUpdateCategoryDto> arg0` | `SingleResponse<Void>` | 修改分类按应用 |
| `publishCheck` | `SingleRequest<String> arg0` | `SingleResponse<Void>` | 发布前检查（按应用名） |
| `publishCheckByAppInfo` | `SingleRequest<BpmAppInfoDto> arg0` | `SingleResponse<Void>` | 发布Check按应用 |
| `publishLock` | `SingleRequest<String> arg0` | `SingleResponse<Void>` | 发布加锁（防并发发布） |
| `publishLockByAppInfo` | `SingleRequest<BpmAppInfoDto> arg0` | `SingleResponse<Void>` | 按应用信息加发布锁（防并发发布） |
| `publishFinish` | `SingleRequest<BpmPublishResult> arg0` | `SingleResponse<Void>` | 发布完成（落发布结果） |
| `cleanCacheByApplicationName` | `SingleRequest<String> arg0` | `SingleResponse<Void>` | 清应用模板缓存（改完模板必须清） |
| `startCheck` | `SingleRequest<BpmStartTemplateDto> arg0` | `ListResponse<BpmTemplateDto>` | 启用前检查 |
| `start` | `SingleRequest<String> arg0` | `SingleResponse<Void>` | 启用模板（设计→可用） |
| `startByTemplateId` | `SingleRequest<BpmStartTemplateDto> arg0` | `ListResponse<BpmTemplateDto>` | 按模板 id 启用（含权限校验） |
| `startByTemplateIdWithoutAuth` | `SingleRequest<BpmStartTemplateDto> arg0` | `ListResponse<BpmTemplateDto>` | 按模板 id 启用（跳过权限，内部/初始化用） |
| `stop` | `SingleRequest<String> arg0` | `SingleResponse<Void>` | 停用模板（按应用名） |
| `stopByTemplateId` | `SingleRequest<Long> arg0` | `SingleResponse<Void>` | 停用模板（按 id） |
| `deleteByApps` | `SingleRequest<List<AppDeleteDto>> arg0` | `SingleResponse<Void>` | 按应用批量删模板 |
| `selectByApplicationName` | `SingleRequest<String> arg0` | `ListResponse<BpmTemplateDto>` | 按应用名查模板列表 |
| `updateEffectTimeByTemplateId` | `SingleRequest<BpmStartTemplateDto> arg0` | `ListResponse<BpmTemplateDto>` | 修改EffectTime按模板 |
| `updateEffectTime` | `SingleRequest<String> arg0` | `SingleResponse<Void>` | 改模板生效时间 |
| `updateAuthorized` | `SingleRequest<List<BpmTemplateAuthorizationDto>> arg0` | `SingleResponse<Void>` | 改模板授权 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<BpmTemplateDto>` | 查询模板按 id |
| `selectTemplateListByCondition` | `SingleRequest<BpmTemplateSearchConditionDto> arg0` | `ListResponse<BpmTemplateDto>` | 列表查询模板按条件 |
| `selectByTemplateUrlId` | `SingleRequest<Long> arg0` | `SingleResponse<BpmTemplateSimpleDto>` | 查询模板简单按模板 |
| `selectEffectedDiagramListByAppName` | `SingleRequest<BaseBpmHandlerParamDto> arg0` | `ListResponse<BpmAppTemplateDto>` | 取应用下生效的流程图列表 |
| `selectTemplateUserGuidInfo` | `SingleRequest<Long> arg0` | `ListResponse<BpmTemplateUserGuidInfo>` | 查询模板用户Guid |
| `selectTemplateById` | `SingleRequest<SeachTemplateInfoDto> arg0` | `SingleResponse<BpmTemplateInfoDto>` | 查询模板按 id |
| `selectPathTableCondition` | `SingleRequest<BpmPathTableDefineSearchDto> arg0` | `PageResponse<BpmPathTableDefineBaseDto>` | 查路径表定义（分页） |
| `selectTemplateIdsByName` | `SingleRequest<String> arg0` | `ListResponse<Long>` | 按模板名批量取 id |
| `selectTemplateByRootEntityId` | `SingleRequest<Long> arg0` | `ListResponse<BpmTemplateDto>` | 按根实体 id 查模板 |
| `selectTemplateByParams` | `SingleRequest<BpmTemplateParamDto> arg0` | `SingleResponse<BpmTemplateDto>` | 查询模板按Params |
| `selectTemplateByRootEntityName` | `SingleRequest<String> arg0` | `ListResponse<BpmTemplateDto>` | ★按根实体名查模板（生单/触发流程时定位模板） |
| `hasDesignTemplateByEntityName` | `SingleRequest<String> arg0` | `SingleResponse<Boolean>` | 判断某实体是否已设计流程模板 |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<BpmTemplateDto>` | 查询模板按 ids |
| `selectUserTemplatePageList` | `SingleRequest<UserTemplateListRequestDto> arg0` | `PageResponse<UserTemplateDto>` | 查用户可用模板（发起页用） |
| `selectTemplateGuidByCategoryCode` | `SingleRequest<String> arg0` | `ListResponse<Long>` | 查询模板Guid按分类编码 |
| `selectBpmTemplateOwnerPageList` | `SingleRequest<BpmTemplateOwnerSearchDto> arg0` | `PageResponse<BpmTemplateOwnerDto>` | 分页列表查询模板所有者Bpm |
| `filterEnableTemplateAppName` | `SingleRequest<List<String>> arg0` | `ListResponse<String>` | 过滤出已启用的应用名 |
| `selectCascadeById` | `SingleRequest<Long> arg0` | `SingleResponse<BpmTemplateDto>` | 级联查询模板按 id |
| `selectCascadeByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<BpmTemplateDto>` | 级联查询模板按 ids |
| `dynamicSelect` | `SingleRequest<ProxyParamDto> arg0` | `PageResponse<BpmTemplateDto>` | 查询Proxy |
| `updateByAppName` | `SingleRequest<BpmTemplateDto> arg0` | `SingleResponse<Integer>` | 修改模板按应用名称 |
| `dynamicJoinSelect` | `SingleRequest<ProxyJoinParamDto> arg0` | `PageResponse<BpmTemplateDto>` | 查询ProxyJoin |
| `selectCascadeByConditions` | `SingleRequest<QueryConditionDto> arg0` | `SingleResponse<BpmTemplateDto>` | 级联查询条件按条件 |
| `selectCascadeListByConditions` | `SingleRequest<QueryConditionDto> arg0` | `ListResponse<BpmTemplateDto>` | 级联列表查询条件按条件 |
| `selectTemplateIdListByGuid` | `SingleRequest<Long> arg0` | `ListResponse<Long>` | 列表查询模板按Guid |
| `selectNodeDetail` | `SingleRequest<BpmNodeDetailReqDto> arg0` | `SingleResponse<BpmNodeDetailDto>` | 查模板节点明细 |
| `selectByIdDisplayName` | `SingleRequest<Long> arg0` | `SingleResponse<BpmTemplateDto>` | 查询模板按名称 |
| `selectByIdsDisplayName` | `SingleRequest<List<Long>> arg0` | `ListResponse<BpmTemplateDto>` | 查询模板按名称 |
| `selectTemplateBySearchDto` | `SingleRequest<BpmTemplateAppSearchDto> arg0` | `ListResponse<Long>` | 查询模板按SearchDto |
| `selectTemplateByCategoryIds` | `SingleRequest<BpmTemplateCategorySearchDto> arg0` | `ListResponse<Long>` | 查询模板按分类 |
| `updateTemplateExtend` | `SingleRequest<BpmTemplateExtendUpdateDto> arg0` | `SingleResponse<Long>` | 修改模板扩展 |
| `selectNormalMultiVersionDraft` | `SingleRequest<BpmNormalMultiVersionSearchDto> arg0` | `ListResponse<BpmTemplateDto>` | 查询版本草稿NormalMulti |
| `getCascadeDefaultValue` | `SingleRequest<Void> arg0` | `SingleResponse<BpmTemplateDto>` | 级联获取DefaultValue |
| `getCascadeDefaultValue` | `—` | `SingleResponse<BpmTemplateDto>` | 级联获取DefaultValue |
| `selectLatestTemplateByGuids` | `SingleRequest<List<Long>> arg0` | `ListResponse<BpmTemplateDto>` | 查询模板Latest按Guids |

#### BpmTemplateManageAppService

`com.seeyon.bpm.api.common.BpmTemplateManageAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `grayAuthTemplate` | `SingleRequest<BpmGrayUpdateDto> arg0` | `SingleResponse<Void>` | 灰度授权（部分人先用新版） |
| `closeLowerVersionGrayAndStarted` | `SingleRequest<List<BpmAppInfoDto>> arg0` | `SingleResponse<Void>` | 关闭低版本灰度和已启用的模板 |
| `startByAppName` | `SingleRequest<BpmAppInfoDto> arg0` | `SingleResponse<Void>` | 按应用名启用全部模板 |
| `selectFormalAuthTemplateList` | `SingleRequest<Long> arg0` | `ListResponse<BpmTemplateDto>` | 查正式授权模板列表 |
| `selectFormalAuthTemplateListByQueryDto` | `SingleRequest<FormalAuthTemplateQueryDto> arg0` | `ListResponse<BpmTemplateDto>` | 列表查询认证模板Formal按QueryDto |
| `selectGrayAuthTemplateList` | `SingleRequest<String> arg0` | `ListResponse<BpmTemplateDto>` | 查灰度授权模板列表 |
| `updateAuth` | `SingleRequest<BpmBatchAuthDto> arg0` | `SingleResponse<Void>` | 批量改模板授权 |
| `invalidAppTemplatesByAppGuid` | `SingleRequest<Long> arg0` | `SingleResponse<Void>` | 按应用 guid 让模板全部失效 |
| `configNodePermissionScope` | `SingleRequest<BpmTemplateNodePerScopeDto> arg0` | `SingleResponse<Void>` | 配置节点权限范围 |
| `framePublish` | `SingleRequest<String> arg0` | `SingleResponse<Void>` | 发布框架（流程骨架） |
| `clearDefaultFrameCache` | `SingleRequest<String> arg0` | `SingleResponse<Void>` | 清默认框架缓存 |

#### BpmThirdTemplateSyncAppService

`com.seeyon.bpm.api.common.BpmThirdTemplateSyncAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createBatch` | `SingleRequest<List<BpmThirdTemplateCreateOrUpdateDto>> arg0` | `ListResponse<BpmThirdTemplateCreateOrUpdateDto>` | 批量新建第三方模板 |
| `updateBatch` | `SingleRequest<List<BpmThirdTemplateCreateOrUpdateDto>> arg0` | `SingleResponse<Void>` | 批量修改Void |
| `createActivityResponsibilities` | `SingleRequest<List<BpmActivityResponsibilityDto>> arg0` | `SingleResponse<Void>` | 新建ActivityResponsibilities |
| `createTemplateRecent` | `SingleRequest<BpmTemplateRecentDto> arg0` | `SingleResponse<Void>` | 新建模板Recent |

#### BpmWorkItemAppService

`com.seeyon.bpm.api.common.BpmWorkItemAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<BpmWorkItemDto> arg0` | `SingleResponse<Integer>` | 新建WorkItem |
| `createBatch` | `SingleRequest<List<BpmWorkItemDto>> arg0` | `SingleResponse<Integer>` | 批量新建（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<BpmWorkItemDto>` | 按 id 查待办项 |
| `selectByCaseId` | `SingleRequest<Long> arg0` | `ListResponse<BpmWorkItemDto>` | 查某实例的待办项 |

### `com.seeyon.bpm.api.ext.activity`

#### ActivityBehavior

`com.seeyon.bpm.api.ext.activity.ActivityBehavior` · 构件 `bpm-facade` · extends `Comparable`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `order` | `—` | `int` | 行为执行优先级（数值小的先执行） |
| `getConfigId` | `—` | `String` | 获取配置 |
| `preMatch` | `BpmSupportOperation arg0` | `boolean` | ★SPI 扩展点：判断本次流程是否走这个行为（返回 true 才执行） |
| `onActivityReady` | `BpmSupportOperation arg0` | `boolean` | ★SPI 扩展点：节点即将激活时回调，返回 false 可阻止激活 |
| `onActivityFinish` | `BpmSupportOperation arg0` | `boolean` | ★SPI 扩展点：节点完成时回调，返回 false 可阻止完成 |
| `onActivityCanceled` | `BpmSupportOperation arg0` | `boolean` | ★SPI 扩展点：节点被取消时回调 |
| `validateActivityAction` | `BpmSupportOperation arg0` | `boolean` | 校验ActivityAction |
| `compareTo` | `Object arg0` | `int` | 按 order 比较，用于排序 |

#### ActivityBehaviorChain

`com.seeyon.bpm.api.ext.activity.ActivityBehaviorChain` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `doBehaviorChain` | `BpmSupportOperation arg0` | `<T> T` | 按优先级依次执行行为链，任一返回 false 即中断 |
| `hasNext` | `—` | `boolean` | 判断有Next |

#### ActivityBehaviorFactory

`com.seeyon.bpm.api.ext.activity.ActivityBehaviorFactory` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getActivityBehaviors` | `String arg0` | `List<ActivityBehavior>` | 获取ActivityBehaviors |
| `getActivityConfiguration` | `String arg0` | `String` | 获取ActivityConfiguration |
| `supportActivities` | `—` | `Set<String>` | 声明该工厂支持哪些节点类型 code |

#### BpmSupportOperation

`com.seeyon.bpm.api.ext.activity.BpmSupportOperation` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getConfigId` | `—` | `String` | 获取配置 |
| `getParameters` | `—` | `Map<String, Object>` | 取全部流程参数 |
| `setParameter` | `String arg0` | `void` | 设置流程参数（传给后续节点） |
| `getConfigurationValue` | `String arg0` | `Object` | 取节点配置值 |
| `getAllConfigurationValues` | `—` | `Map<String, Object>` | 全部获取ConfigurationValues |
| `getCaseId` | `—` | `Long` | 取当前流程实例 id（在节点扩展代码里用） |
| `getActivityId` | `—` | `Long` | 取当前节点 id |
| `getActivityPolicyId` | `—` | `String` | 获取ActivityPolicy |
| `getAppName` | `—` | `String` | 获取应用名称 |
| `getTemplateId` | `—` | `Long` | 取当前流程模板 id |
| `getFormRecordId` | `—` | `String` | 取当前表单记录 id |
| `getRootEntityName` | `—` | `String` | 取根实体名 |
| `getApplicationName` | `—` | `String` | 取应用名 |
| `getSubject` | `—` | `String` | 取流程标题 |
| `getStartUserId` | `—` | `Long` | 取发起人 id |
| `getCurrentUserId` | `—` | `Long` | 取当前办理人 id |

### `com.seeyon.bpm.api.udc`

#### BpmApiDetectionService

`com.seeyon.bpm.api.udc.BpmApiDetectionService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `detectionForAttributeDelete` | `SingleRequest<DetectionAttrDeleteRequestDto> arg0` | `ListResponse<BpmConsistenceDetectionDto>` | 字段删除后的影响检测 |
| `detectionForAttributeUpdate` | `SingleRequest<DetectionAttrUpdateRequestDto> arg0` | `ListResponse<BpmConsistenceDetectionDto>` | 字段改名/改类型后的影响检测 |
| `detectionForCtpEnumDelete` | `SingleRequest<DetectionCtpEnumDeleteRequestDto> arg0` | `ListResponse<BpmConsistenceDetectionDto>` | 枚举删除后的影响检测 |
| `cascadeHandleAffectedForEntity` | `SingleRequest<BpmDetectionEntityDto> arg0` | `SingleResponse<Void>` | 实体变更的级联处理 |
| `cascadeHandleAffectedForAttr` | `SingleRequest<DetectionAttrUpdateDto> arg0` | `SingleResponse<Void>` | 字段变更的级联处理 |
| `detectionForEntityDelete` | `SingleRequest<DetectionEntityDeleteRequestDto> arg0` | `ListResponse<BpmConsistenceDetectionDto>` | 实体删除后的影响检测 |
| `detectionForPageDelete` | `SingleRequest<DetectionPageDeleteRequestDto> arg0` | `ListResponse<BpmConsistenceDetectionDto>` | 页面删除后的影响检测 |
| `detectionForPageUpdate` | `SingleRequest<DetectionPageUpdateRequestDto> arg0` | `ListResponse<BpmConsistenceDetectionDto>` | 页面变更后的影响检测 |
| `detection` | `SingleRequest<DetectionFullInfoRequestDto> arg0` | `ListResponse<BpmConsistenceDetectionDto>` | ★流程一致性检测（实体/字段/页面被删改后，流程是否还引用） |

#### BpmApiParamAppService

`com.seeyon.bpm.api.udc.BpmApiParamAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `saveParamSchema` | `SingleRequest<BpmParameterDefineDto> arg0` | `SingleResponse<Void>` | 保存流程参数模板（设计态） |
| `saveParamData` | `SingleRequest<BpmParameterDataDto> arg0` | `SingleResponse<Void>` | 保存流程参数值（运行态） |
| `loadParamSchema` | `SingleRequest<Long> arg0` | `ListResponse<BpmParameterSettingDto>` | 按模板 id 加载参数定义 |
| `loadParamTypes` | `SingleRequest<Void> arg0` | `ListResponse<BpmDataTypeDto>` | 取可用参数类型列表 |
| `loadParamSchemaByOrigin` | `SingleRequest<String> arg0` | `SingleResponse<BpmParameterSettingDto>` | 按来源加载参数定义 |
| `deleteSettingByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Void>` | 删除设置按 ids |
| `selectParameterUsedByTemplateId` | `SingleRequest<Long> arg0` | `ListResponse<BpmParameterSettingDto>` | 查模板用到的参数 |
| `selectUsedParameterPathName` | `SingleRequest<Long> arg0` | `ListResponse<String>` | 查询参数路径名称Used |

#### BpmApiSplitImportAppService

`com.seeyon.bpm.api.udc.BpmApiSplitImportAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectTemplateByAppName` | `SingleRequest<String> arg0` | `ListResponse<BpmTemplateBaseDto>` | 按应用名查可拆分导入的模板 |
| `prepareApp` | `SingleRequest<BpmSplitPrepareDto> arg0` | `SingleResponse<String>` | 拆分导入前的准备（建应用壳） |
| `splitImport` | `SingleRequest<String> arg0` | `SingleResponse<Void>` | 执行拆分导入 |

#### BpmApiTransportAppService

`com.seeyon.bpm.api.udc.BpmApiTransportAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `saveAs` | `SingleRequest<BpmSaveAsDto> arg0` | `SingleResponse<Void>` | 另存为 |
| `getApplicationInitData` | `SingleRequest<BpmInitParamDto> arg0` | `SingleResponse<BpmExportInitDataDto>` | 导出应用初始化数据（迁移/部署用） |
| `getApplicationInitDataAsync` | `SingleRequest<BpmInitParamDto> arg0` | `SingleResponse<String>` | 异步导出初始化数据 |
| `exportTemplateInfo` | `SingleRequest<BpmInitDataDto> arg0` | `SingleResponse<String>` | 导出模板信息 |
| `importTemplateInfo` | `SingleRequest<BpmImportDto> arg0` | `SingleResponse<Void>` | 导入模板信息 |
| `selectUsedConnectorByAppName` | `SingleRequest<String> arg0` | `ListResponse<String>` | 查应用用到的连接器 |
| `asyncTransportRequest` | `SingleRequest<BpmTransportRequestDto> arg0` | `SingleResponse<String>` | 异步传输请求 |

#### BpmUdcApiService

`com.seeyon.bpm.api.udc.BpmUdcApiService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `sendForUdc` | `SingleRequest<BpmSendUdcDto> arg0` | `SingleResponse<BpmApiSendApiResponseDto>` | ★★UDC 侧发起流程（扩展代码走这个，不是 BpmAppService.send） |
| `saveDraft` | `SingleRequest<BpmSaveDraftUdcDto> arg0` | `SingleResponse<BpmSaveDraftUdcResponseDto>` | UDC 侧保存待发 |
| `triggerFlowForUdc` | `SingleRequest<List<BpmTriggerFlowUdcRequestDto>> arg0` | `ListResponse<BpmTriggerFlowUdcResponseDto>` | ★★UDC 批量触发流程（微流程/数据流节点调用，一次多条） |
| `prefixForUdc` | `SingleRequest<BpmPrefixForUdcDto> arg0` | `SingleResponse<BpmPrefixForUdcResponseDto>` | 取流程标题前缀（发起前拼标题用） |
| `repealForUdc` | `SingleRequest<BpmOperationRepealUdcDto> arg0` | `SingleResponse<Void>` | UDC 侧撤销流程 |
| `stopForUdc` | `SingleRequest<BpmStopDto> arg0` | `SingleResponse<CommonResultDto>` | UDC 侧终止流程 |
| `deleteCaseByIdForUdc` | `SingleRequest<Long> arg0` | `SingleResponse<Void>` | UDC 侧删除流程实例（按 caseId+userId） |
| `getNodePermissionOperation` | `SingleRequest<BpmNodePermissionRequestDto> arg0` | `ListResponse<BpmNodePermissionResponseDto>` | 取节点可执行操作（提交/回退/加签…） |
| `getNodePermission` | `SingleRequest<BpmNodePermissionRequestDto> arg0` | `SingleResponse<BpmNodePermission4PageDto>` | 取节点权限（页面渲染用，按节点返回可编辑字段） |
| `asyncTriggerFlowForUdc` | `SingleRequest<BpmAsyncTriggerFlowUdcRequestDto> arg0` | `SingleResponse<Void>` | UDC 异步批量触发流程（大数据量用） |

### `com.seeyon.bpm.api.upgrade`

#### BpmUpgrade51To52AppService

`com.seeyon.bpm.api.upgrade.BpmUpgrade51To52AppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `upgradeExtensionPlan` | `SingleRequest<List<UdcExtensionPlanRequestDto>> arg0` | `SingleResponse<Void>` | 升级扩展方案（5.1→5.2 迁移） |

### `com.seeyon.bpm.appservice.autogenerate`

#### ApplicationAutoGenerateService

`com.seeyon.bpm.appservice.autogenerate.ApplicationAutoGenerateService` · 构件 `bpm-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `generate` | `SingleRequest<Map<String, Object>> arg0` | `void` | 触发应用自动生成（脚手架） |

### `com.seeyon.bpm.appservice.autogenerate.dispatcher`

#### DispatcherHandler

`com.seeyon.bpm.appservice.autogenerate.dispatcher.DispatcherHandler` · 构件 `bpm-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `handle` | `BpmDiagram arg0` | `BpmDiagram` | 自动生成的分发处理（按类型路由到具体生成器） |

### `com.seeyon.bpm.simulation.api`

#### BpmApiSimulationAppService

`com.seeyon.bpm.simulation.api.BpmApiSimulationAppService` · 构件 `bpm-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectProcessPredictionResult` | `SingleRequest<ProcessPredictionDto> arg0` | `SingleResponse<ProcessPredictionResultDto>` | 查询流程PredictionResult |
| `selectSimulationLinkByGuid` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 查询模拟Link按Guid |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 322 个领域服务，下表列**方法数最多的 40 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `BpmTemplateService` | 203 | 模板 · 查询×123 / 修改×17 / 获取×15 |
| `BpmProcessSuperviseService` | 149 | 流程监管 · 获取×45 / 查询×12 / 检查×8 |
| `BpmMqMessageService` | 113 | 消息 · 发送×57 / 修改×18 / 新建×16 |
| `BpmOperationService` | 112 | Operation · 获取×18 / 检查×8 / 保存×5 |
| `BpmNodePermissionService` | 108 | 权限 · 查询×38 / 获取×23 / 修改×4 |
| `BpmWorkItemService` | 104 | WorkItem · 查询×69 / 修改×6 / 获取×4 |
| `BpmProcessLogService` | 82 | 流程日志 · 查询×27 / 获取×14 / 新建×10 |
| `BpmFormPermissionService` | 78 | 权限 · 查询×42 / 获取×7 / 删除×5 |
| `BpmAbnormalReportService` | 64 | AbnormalReport · 获取×10 / 查询×8 / 修改×8 |
| `BpmProcessService` | 63 | 流程 · 查询×23 / 修改×9 / 新建×5 |
| `BpmService` | 63 | Bpm · 获取×9 / 检查×6 / 查询×6 |
| `BpmProcessSuperviseListService` | 62 | 流程监管 · 查询×12 / 校验×8 / 检查×8 |
| `BpmOpinionService` | 58 | 意见 · 查询×13 / 获取×12 / 新建×5 |
| `BpmMessageService` | 56 | 消息 · 发送×37 / 设置×6 / 构建×2 |
| `BpmPathTableService` | 56 | 路径表 · 查询×29 / 修改×6 / 检查×5 |
| `BpmCaseService` | 54 | 流程实例 · 查询×24 / 获取×7 / 修改×6 |
| `BpmParameterSettingService` | 52 | 参数设置 · 查询×30 / 修改×5 / 删除×3 |
| `BpmActivityRunService` | 48 | ActivityRun · 查询×25 / 修改×9 / 新建×7 |
| `BpmNodePermissionOperationService` | 47 | 权限 · 查询×20 / 获取×5 / 删除×3 |
| `BpmParameterService` | 47 | 参数 · 查询×19 / 获取×8 / 修改×4 |
| `BpmDetectionService` | 44 | 检测 · 检测×22 / 获取×15 / 处理×3 |
| `BpmTemplateCategoryService` | 44 | 模板分类 · 查询×14 / 获取×11 / 构建×4 |
| `BpmCaseRevisionService` | 44 | 流程实例 · 获取×7 / 判断有×5 / 判断×3 |
| `BpmVipSuperviseService` | 42 | 监管 · 查询×6 / 清理×5 / 审计×3 |
| `AffairConsultService` | 36 | 事项 · 获取×12 / 新建×10 / 发送×4 |
| `DispatcherService` | 34 | Dispatcher · 处理×6 / 取消×3 / 检查×2 |
| `BpmSystemSettingService` | 33 | 设置 · 查询×15 / 保存×4 / 获取×3 |
| `BpmSubProcessService` | 33 | 流程 · 查询×14 / 修改×4 / 处理×3 |
| `BpmParameterMapperService` | 32 | 参数 · 查询×16 / 删除×4 / 搜索×3 |
| `BpmUserTemplateService` | 32 | 用户模板 · 查询×15 / 获取×3 / 搜索×2 |
| `BpmUrlService` | 30 | Url · 获取×20 / 设置×5 / 判断×1 |
| `AbstractContentService` | 29 | 内容 · 修改×7 / 获取×6 / 新建×4 |
| `BpmExpressionService` | 27 | Expression · 查询×13 / 获取×6 / 新建×3 |
| `BpmNodeAssembleOperationService` | 27 | NodeAssembleOperation · 查询×17 / 新建×2 / 修改×2 |
| `BpmFormPermissionContentService` | 27 | 权限内容 · 查询×10 / 新建×4 / 修改×3 |
| `BpmActivityOverTimeService` | 27 | ActivityOverTime · 发送×7 / 新增×4 / 执行×2 |
| `BpmSummaryService` | 26 | 摘要 · 获取×9 / 判断×9 / 构建×1 |
| `ApprovalSecurityService` | 25 | 审批 · 判断×8 / 检查×6 / 判断能否×4 |
| `BpmThirdFormService` | 25 | 第三方 · 修改×7 / 获取×4 / 新建×3 |
| `BpmOpinionGroupService` | 25 | 意见分组 · 查询×5 / 获取×5 / 排序×1 |

## biz 层：事件与监听

事件 100 个 · 监听器 2 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
|  | `Event` |
| Abstract | `AbstractEvent` |
| AbstractBpm | `AbstractBpmEvent` |
| Affair | `AffairCreateMessageEvent` |
| Agent | `AgentUpdateEvent` |
| ApplicationIdNodePermission | `ApplicationIdNodePermissionUpdateEvent` |
| ApplicationPublish | `ApplicationPublishEvent` |
| AutoApprovalSetting | `AutoApprovalSettingUpdateEvent` |
| Bpm | `BpmDeleteEvent`, `BpmDeleteOpinionEvent`, `BpmUpdateFormDataEvent` |
| BpmAbnormalReport | `BpmAbnormalReportCreateEvent` |
| BpmActivityCancel | `BpmEventActivityCancelEvent` |
| BpmActivityFinish | `BpmActivityFinishEvent` |
| BpmActivityReady | `BpmEventActivityReadyEvent` |
| BpmAffairMessage | `BpmAffairMessageEvent` |
| BpmAfterTransaction | `BpmAfterTransactionEvent` |
| BpmAllActivityFinished | `BpmAllActivityFinishedEvent` |
| BpmAllEndFinished | `BpmAllEndFinishedEvent` |
| BpmAllTemplateStartOrStop | `BpmAllTemplateStartOrStopEvent` |
| BpmAutoActivityExecute | `BpmAutoActivityExecuteEvent` |
| BpmAutoStart | `BpmAutoStartEvent` |
| BpmBase | `BpmBaseEvent` |
| BpmBusinessReceive | `BpmBusinessReceiveEvent` |
| BpmBusinessSend | `BpmBusinessSendEvent` |
| BpmCancel | `BpmCancelEvent` |
| BpmCancelItemByActivityIds | `BpmCancelItemByActivityIdsEvent` |
| BpmCancelPause | `BpmCancelPauseEvent` |
| BpmCase | `BpmCaseDeleteEvent`, `BpmCaseUpdateTitleEvent` |
| BpmCaseCancelPause | `BpmCaseCancelPauseEvent` |
| BpmCaseFinish | `BpmCaseFinishEvent` |
| BpmCasePause | `BpmCasePauseEvent` |
| BpmCaseRevisionLog | `BpmCaseRevisionLogCreateEvent` |
| BpmChangeOpinion | `BpmChangeOpinionEvent` |
| BpmConsult | `BpmConsultEvent` |
| BpmCustomProperty | `BpmCustomPropertyUpdateEvent` |
| BpmDeploy | `BpmDeployEvent` |
| BpmExtendInfo | `BpmExtendInfoUpdateEvent` |
| BpmFinish | `BpmFinishEvent` |
| BpmFormPermission | `BpmFormPermissionUpdateEvent` |
| BpmFormPermissionContent | `BpmFormPermissionContentUpdateEvent` |
| BpmHasten | `BpmHastenEvent` |
| BpmLocalCache | `BpmLocalCacheEvent` |
| BpmMessageDeal | `BpmMessageDealEvent` |
| BpmMqMessage | `BpmMqMessageEvent` |
| BpmMultiWrite | `BpmMultiWriteEvent` |
| BpmNodePermission | `BpmNodePermissionUpdateEvent` |
| BpmNodePermissionOperation | `BpmNodePermissionOperationUpdateByIdAndCodeEvent`, `BpmNodePermissionOperationUpdateEvent` |
| BpmParameterExtend | `BpmParameterExtendUpdateEvent` |
| BpmPause | `BpmPauseEvent` |
| BpmProcess | `BpmProcessUpdateEvent` |
| BpmProcessCancelPause | `BpmProcessCancelPauseEvent` |
| BpmProcessDraft | `BpmProcessDraftEvent` |
| BpmProcessPause | `BpmProcessPauseEvent` |
| BpmProcessRelive | `BpmProcessReliveEvent` |
| BpmProcessRevisionRelease | `BpmProcessRevisionReleaseEvent` |
| BpmProcessStop | `BpmProcessStopEvent` |
| BpmRegisterAuth | `BpmRegisterAuthEvent` |
| BpmRetrieve | `BpmRetrieveEvent` |
| BpmRuntimeTemplate | `BpmRuntimeTemplateDeleteEvent` |
| BpmStart | `BpmStartEvent` |
| BpmStepback | `BpmStepbackEvent` |
| BpmStop | `BpmStopEvent` |
| BpmStopAchieve | `BpmStopAchieveEvent` |
| BpmSubmit | `BpmSubmitEvent` |
| BpmSuperviseChangeProcess | `BpmSuperviseChangeProcessEvent` |
| BpmSystemSetting | `BpmSystemSettingUpdateEvent` |
| BpmTemplate | `BpmTemplateCreateEvent`, `BpmTemplateUpdateEvent` |
| BpmTemplateAuth | `BpmTemplateAuthEvent` |
| BpmTemplateConfig | `BpmTemplateConfigUpdateEvent` |
| BpmTemplateFormPermissionList | `BpmTemplateFormPermissionListUpdateEvent` |
| BpmTemplateStartOrStop | `BpmTemplateStartOrStopEvent` |
| BpmTemporaryPending | `BpmTemporaryPendingEvent` |
| BpmTransfer | `BpmTransferEvent` |
| BpmWorkItemMerge | `BpmWorkItemMergeEvent` |
| BpmWorkItemMove | `BpmWorkItemMoveEvent` |
| Catch | `CatchEvent` |
| CreatePostOrDraft | `CreatePostOrDraftEvent` |
| DefaultFrame | `DefaultFrameUpdateEvent` |
| End | `EndEvent` |
| Evict | `EvictEvent` |
| FileUpload | `FileUploadEvent` |
| FreeFlowTemplate | `FreeFlowTemplateUpdateEvent` |
| MoveWorkItem | `MoveWorkItemEvent` |
| ProcessFlow | `ProcessFlowEvent` |
| ProcessTrack | `ProcessTrackEvent` |
| ReplaceIdRecordAdd | `ReplaceIdRecordAddEvent` |
| Start | `StartEvent` |
| TableChange | `TableChangeEvent` |
| TemplateProcessList | `TemplateProcessListUpdateEvent` |
| TemplateRecentList | `TemplateRecentListUpdateEvent` |
| Throw | `ThrowEvent` |
| Unit | `OrgUnitUpdateEvent` |
| UpdateUserAuthorizedTemplate | `UpdateUserAuthorizedTemplateEvent` |
| UserMemberPost | `UserMemberPostUpdateEvent` |
| WorkItemAssigned | `WorkItemAssignedEvent` |
| WorkItemFinished | `WorkItemFinishedEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `BpmCustomPropertyEventListener` | 3 |
| `BpmTemplateEventListener` | 2 |

## web 层：Controller

共 65 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 核心实体 CRUD | `BpmDemoController` | 145 |
| 核心实体 CRUD | `BpmController` | 81 |
| 核心实体 CRUD | `ProcessSuperviseController` | 63 |
| 核心实体 CRUD | `BpmTemplateController` | 45 |
| 核心实体 CRUD | `BpmUpgradeController` | 32 |
| 核心实体 CRUD | `BpmPathTableController` | 25 |
| 核心实体 CRUD | `BpmNodePermissionController` | 19 |
| 核心实体 CRUD | `BpmProcessController` | 19 |
| 核心实体 CRUD | `BpmParameterController` | 18 |
| 核心实体 CRUD | `BpmSummaryController` | 18 |
| 核心实体 CRUD | `BpmFormPermissionController` | 15 |
| 核心实体 CRUD | `BpmOpinionController` | 14 |
| 核心实体 CRUD | `BpmSystemSettingController` | 13 |
| 核心实体 CRUD | `BpmNodeActionController` | 12 |
| 核心实体 CRUD | `BpmSimulationController` | 12 |
| 核心实体 CRUD | `BpmNodePermissionOperationController` | 10 |
| 核心实体 CRUD | `BpmCaseDynamicReferController` | 8 |
| 核心实体 CRUD | `BpmTemplateDynamicReferController` | 8 |
| 核心实体 CRUD | `BpmProcessLogController` | 7 |
| 核心实体 CRUD | `BpmReplaceController` | 7 |
| 核心实体 CRUD | `BpmNormalAppMultiVersionController` | 6 |
| 核心实体 CRUD | `BpmNodePermissionV2Controller` | 5 |
| 核心实体 CRUD | `BpmPersonalTemplateController` | 5 |
| 核心实体 CRUD | `BpmTemplateDynamicController` | 5 |
| 核心实体 CRUD | `BpmTemplateTagController` | 5 |
| 核心实体 CRUD | `BpmThirdFormPermissionController` | 5 |
| 核心实体 CRUD | `BpmApplicationOperateLogController` | 4 |
| 核心实体 CRUD | `BpmAutoApprovalController` | 4 |
| 核心实体 CRUD | `BpmAutoNodeController` | 4 |
| 核心实体 CRUD | `BpmCaseDynamicController` | 4 |
| 核心实体 CRUD | `BpmListController` | 4 |
| 核心实体 CRUD | `BpmPluginController` | 4 |
| 核心实体 CRUD | `BpmProcessFeedbackController` | 4 |
| 核心实体 CRUD | `BpmProcessReplaceController` | 4 |
| 核心实体 CRUD | `BpmTemplateConfigController` | 4 |
| 核心实体 CRUD | `ShortMessageEmailController` | 4 |
| 核心实体 CRUD | `BpmApplicationController` | 3 |
| 核心实体 CRUD | `BpmConsultController` | 3 |
| 核心实体 CRUD | `BpmHierarchicalControlController` | 3 |
| 核心实体 CRUD | `BpmManagerLogController` | 3 |
| 核心实体 CRUD | `BpmMyProcessPermissionController` | 3 |
| 核心实体 CRUD | `BpmProcessTrackController` | 3 |
| 核心实体 CRUD | `BpmResponsibilityController` | 3 |
| 核心实体 CRUD | `BpmSubProcessController` | 3 |
| 核心实体 CRUD | `BpmBusinessRuleController` | 2 |
| 核心实体 CRUD | `BpmCaseController` | 2 |
| 核心实体 CRUD | `BpmControlledProcessController` | 2 |
| 核心实体 CRUD | `BpmCustomTabController` | 2 |
| 核心实体 CRUD | `BpmDesignController` | 2 |
| 核心实体 CRUD | `BpmDynamicTitleController` | 2 |
| 核心实体 CRUD | `BpmEditLockController` | 2 |
| 核心实体 CRUD | `BpmFormDataController` | 2 |
| 核心实体 CRUD | `BpmNodeForecastController` | 2 |
| 核心实体 CRUD | `BpmNodePermissionBindController` | 2 |
| 核心实体 CRUD | `BpmPlaceholderConfigController` | 2 |
| 核心实体 CRUD | `BpmTemplateEvaluationController` | 2 |
| 核心实体 CRUD | `AsyncOperationController` | 1 |
| 核心实体 CRUD | `BpmCaseRevisionController` | 1 |
| 核心实体 CRUD | `BpmEventNodeController` | 1 |
| 核心实体 CRUD | `BpmFormDataQueryController` | 1 |
| 核心实体 CRUD | `BpmMemberPostController` | 1 |
| 核心实体 CRUD | `BpmMessageNodeController` | 1 |
| 核心实体 CRUD | `BpmNodePropertyController` | 1 |
| 核心实体 CRUD | `BpmUserRoleController` | 1 |
| 核心实体 CRUD | `SandBoxApplicationDataCleanTestController` | 1 |

## 概念对照（bpm 的名词和中文业务词不是一一对应）

| 平台术语 | 中文业务含义 | 关键 id |
|---|---|---|
| **template**（模板） | 流程**设计态**：流程图、节点、权限配置 | `templateId` |
| **case**（案件） | 流程**实例**（一次发起 = 一个 case） | `caseId` |
| **activity**（节点实例） | case 里某个节点的一次运行记录 | `activityId` |
| **workItem**（待办项） | 某节点某人的一条待办 | `workItemId` |
| **opinion**（意见） | 办理意见 / 表单批注 | `opinionId` |
| **processLog** | 流程日志（流转轨迹） | — |
| **publish**（发布） | 把设计态模板推到运行态 | — |

**最容易搞混的两个**：
- `send`（发起，产生 case）vs `saveDraft`（存草稿，不产生 case）
- `repeal`（撤销，发起人收回）vs `takeBack`（取回，办理人收回自己刚提交的）

## 三条入口，选错就白改

```
我要从自己的扩展代码发起流程
  → BpmUdcApiService.sendForUdc / triggerFlowForUdc     ★ UDC 专用入口

我要从平台内部/初始化发起
  → BpmAppService.send

我只想知道某个表单记录对应哪个流程
  → BpmCaseAppService.selectBpmCaseByFormRecordId
```

**`BpmUdcApiService` 和 `BpmAppService` 的区别（这是关键）**：

| | `BpmAppService.send` | `BpmUdcApiService.sendForUdc` |
|---|---|---|
| 入参 | `BpmSendDto`（平台内部结构） | `BpmSendUdcDto`（UDC 结构，字段更少） |
| 返回值 | `BpmSendResultDto` | `BpmApiSendApiResponseDto` |
| 权限 | 走平台用户上下文 | 走 UDC 应用上下文 |
| 用途 | 标品内部发起 | **扩展代码 / 微流程节点 / 数据流生单** |

**UDC 生成的代码引用流程，只认后者。**

## 典型调用链

### 链 1：UDC 扩展发起一条流程

```java
@Autowired
private com.seeyon.bpm.api.udc.BpmUdcApiService bpmUdc;

// ① 拿到模板（按根实体名找，不要写死 templateId）
//    根实体名 = UDC 实体的全名
SingleResponse<BpmApiSendApiResponseDto> resp = bpmUdc.sendForUdc(
        SingleRequest.from(bpmSendUdcDto));

// ② dto 里必须有的（按 BpmSendUdcDto 字段）：模板、表单记录 id、标题、发起人
// ③ 返回里带 caseId —— 后续查流程状态全靠它
```

### 链 2：批量触发（数据流生单 / 微流程节点）

```java
// 列表入参：一次传多条，每条一个流程
ListResponse<BpmTriggerFlowUdcResponseDto> rs = bpmUdc.triggerFlowForUdc(
        SingleRequest.from(List.of(req1, req2, req3)));

// 数据量大（>1000）改异步，避免超时
bpmUdc.asyncTriggerFlowForUdc(SingleRequest.from(asyncReq));
```

### 链 3：办完流程后回写业务表

```java
@Autowired
private com.seeyon.bpm.api.common.BpmCaseAppService caseService;

// 已知表单记录 id → 找 caseId
SingleResponse<BpmCaseDto> c = caseService.selectBpmCaseByFormRecordId(
        SingleRequest.from(searchDto));

// 看流程跑到哪了
ListResponse<BpmActivityRunDto> acts = activityService.selectAllByCaseId(
        SingleRequest.from(c.getData().getId()));
```

### 链 4：在节点扩展里拿上下文

```java
// 节点扩展的入参里通常带 BpmSupportOperation
Long caseId     = op.getCaseId();
Long activityId = op.getActivityId();
Long templateId = op.getTemplateId();
String recordId = op.getFormRecordId();
String appName  = op.getApplicationName();
Long currentUser = op.getCurrentUserId();

// 往后续节点传值
op.setParameter("approveLevel", 3);
```

## UDC 和 bpm 的接口边界（谁能调谁）

```
UDC 扩展代码
  ├── 可调 BpmUdcApiService（★专用，10 个方法）
  ├── 可调 BpmCaseAppService（只读查实例）
  ├── 可调 BpmApiFormPermissionAppService / BpmApiNodePermissionAppService（读权限配置）
  └── 不应直接调 BpmAppService（那是标品内部入口，上下文不匹配）

bpm 内部
  └── 走 BpmAppService + BpmSupportOperation（节点上下文）
```

## 落表（流程侧）

流程数据落在 bpm 域自己的表，**不在 UDC 实体表里**。UDC 侧只需要保存 `caseId`。

⚠️ 具体表名 `UNVERIFIED`（字节码索引不含 SQL）。取证：反编译 `bpm-biz` 找 mapper，
或在 test2 库查 `information_schema.tables` 里 `%_bpm_%`。

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
| 39 接口 / 278 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 322 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 100 事件 / 2 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 65 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径 | 未取证 | `UNVERIFIED` |
| 落表 | 未取证 | `UNVERIFIED` |
